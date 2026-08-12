"""Bridge governed PPTX Studio plans to the portable physical OPC assembler.

The public catalog deliberately contains no commercial-template paths.  This
adapter is the only boundary allowed to resolve a selected package hash to a
private source file, turn approved region bindings into native shape slots,
and invoke the existing cross-package importer.  It never searches a client
folder for templates and it never accepts model-authored geometry or OOXML.
"""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from window_pptx.page_template_library import (
    PageTemplate,
    SlotRecord,
    _compile_governed_content_inventory,
    _discover_slots,
)
from window_pptx.physical_assembly import (
    AssemblyImportContext,
    AssemblyPlan,
    AssemblyTargetSlide,
    AssetBindingSpec,
    AuthorityLock,
    PhysicalAssemblyReport,
    TextBindingSpec,
    assemble_physical_deck,
)

from .adaptation import adaptation_request_sha256, compile_adaptation, serialize_adaptation_plan
from .composition import composition_plan_sha256
from .qa import run_studio_qa


class PhysicalAdapterError(ValueError):
    """A selected catalog page cannot safely be materialized."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _write_json(path: Path, value: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _canonical_json(value)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return _sha256_bytes(raw)


def _safe_private_root(value: Path | str) -> Path:
    root = Path(value).expanduser().resolve(strict=False)
    if root.is_symlink() or not root.is_dir():
        raise PhysicalAdapterError("PRIVATE_SOURCE_ROOT_INVALID")
    return root


def resolve_catalog_sources(
    catalog: Mapping[str, Any], *, private_source_root: Path | str,
) -> dict[str, Path]:
    """Resolve the catalog's immutable package hashes below one private root.

    The traversal is deliberately limited to the catalog's active categories.
    This makes template discovery impossible in a clean client requirement
    directory and makes duplicate package hashes fail instead of being chosen
    opportunistically.
    """

    root = _safe_private_root(private_source_root)
    active = catalog.get("active_categories")
    pages = catalog.get("pages")
    if not isinstance(active, list) or not active or not isinstance(pages, list):
        raise PhysicalAdapterError("CATALOG_SCHEMA_INVALID")
    wanted = {
        str(page.get("package_sha256"))
        for page in pages
        if isinstance(page, Mapping)
        and isinstance(page.get("package_sha256"), str)
        and len(str(page["package_sha256"])) == 64
    }
    if not wanted:
        raise PhysicalAdapterError("CATALOG_PACKAGES_EMPTY")
    found: dict[str, Path] = {}
    for category in active:
        if not isinstance(category, str) or not category:
            raise PhysicalAdapterError("CATALOG_CATEGORY_INVALID")
        directory = root / category
        if directory.is_symlink() or not directory.is_dir():
            raise PhysicalAdapterError("PRIVATE_CATEGORY_MISSING")
        for package in sorted(directory.rglob("*.pptx"), key=lambda item: item.as_posix()):
            if package.is_symlink() or not package.is_file():
                raise PhysicalAdapterError("PRIVATE_SOURCE_PATH_INVALID")
            digest = _sha256_file(package)
            if digest not in wanted:
                continue
            previous = found.get(digest)
            if previous is not None and previous != package:
                raise PhysicalAdapterError("PRIVATE_PACKAGE_HASH_AMBIGUOUS")
            found[digest] = package.resolve(strict=True)
    missing = sorted(wanted - set(found))
    if missing:
        raise PhysicalAdapterError("PRIVATE_PACKAGE_MISSING")
    return found


def _slot_graph(slots: Sequence[SlotRecord]) -> dict[str, Any]:
    records = []
    for item in slots:
        records.append({
            "slot_id": item.slot_id,
            "shape_id": item.shape_id,
            "kind": item.kind,
            "semantic_role": item.semantic_role,
            "region": item.region,
            "reading_order": item.reading_order,
            "bbox": dict(item.bbox),
            "max_chars": item.max_chars,
            "source_text": item.text,
            "source_text_sha256": _sha256_bytes(item.text.encode("utf-8")),
            "source_char_count": item.source_char_count,
            "source_line_count": item.source_line_count,
            "source_run_count": item.source_run_count,
            "group_id": item.group_id,
            "group_order": item.group_order,
            "font_size_pt": item.font_size_pt,
            "allowed_binding_modes": list(item.allowed_binding_modes),
        })
    return {
        "text_slot_ids": [item.slot_id for item in slots],
        "text_slot_count": len(slots),
        "reading_order": [item.slot_id for item in slots],
        "fragment_groups": [],
        "slots": records,
    }


def _fact_id(prefix: str, value: str) -> str:
    return f"{prefix}-{_sha256_bytes(value.encode('utf-8'))[:24]}"


def _source_fact(value: str) -> tuple[str, dict[str, Any]]:
    identifier = _fact_id("source", value)
    return identifier, {
        "id": identifier,
        "kind": "label",
        "text": value,
        "allowed_renderings": [value],
        "language": "und",
        "source_id": "template-source",
        "locator": "private-template",
        "required": False,
    }


def _request_facts(request: Mapping[str, Any]) -> dict[str, str]:
    raw = request.get("facts")
    if not isinstance(raw, list):
        raise PhysicalAdapterError("ADAPTATION_REQUEST_INVALID")
    result: dict[str, str] = {}
    for item in raw:
        if not isinstance(item, Mapping) or not isinstance(item.get("fact_id"), str) or not isinstance(item.get("value"), str):
            raise PhysicalAdapterError("ADAPTATION_REQUEST_INVALID")
        result[str(item["fact_id"])] = str(item["value"])
    return result


def _page_lookup(catalog: Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    pages = catalog.get("pages")
    regions = catalog.get("regions")
    if not isinstance(pages, list) or not isinstance(regions, list):
        raise PhysicalAdapterError("CATALOG_SCHEMA_INVALID")
    page_by_id = {
        str(item.get("page_id")): item for item in pages
        if isinstance(item, Mapping) and isinstance(item.get("page_id"), str)
    }
    region_by_id = {
        str(item.get("region_id")): item for item in regions
        if isinstance(item, Mapping) and isinstance(item.get("region_id"), str)
    }
    if not page_by_id:
        raise PhysicalAdapterError("CATALOG_PAGES_EMPTY")
    return page_by_id, region_by_id


def _asset_manifest(
    request: Mapping[str, Any], asset_paths: Mapping[str, Path | str], workspace: Path,
) -> tuple[Path, str]:
    assets = request.get("assets")
    if not isinstance(assets, list):
        raise PhysicalAdapterError("ADAPTATION_REQUEST_INVALID")
    bindings: dict[str, Any] = {}
    for item in assets:
        if not isinstance(item, Mapping) or not isinstance(item.get("asset_id"), str) or not isinstance(item.get("sha256"), str):
            raise PhysicalAdapterError("ADAPTATION_REQUEST_INVALID")
        asset_id, expected = str(item["asset_id"]), str(item["sha256"])
        raw_path = asset_paths.get(asset_id)
        if raw_path is None:
            continue
        path = Path(raw_path).expanduser().resolve(strict=False)
        if path.is_symlink() or not path.is_file() or _sha256_file(path) != expected:
            raise PhysicalAdapterError("CLIENT_ASSET_DRIFT")
        try:
            from PIL import Image
            with Image.open(path) as image:
                width, height = image.size
        except Exception as exc:  # Pillow's concrete exceptions are optional.
            raise PhysicalAdapterError("CLIENT_ASSET_IMAGE_UNREADABLE") from exc
        bindings[asset_id] = {
            "path": str(path),
            "sha256": expected,
            "record": {
                "id": asset_id,
                "kind": "image",
                "quality": 1.0,
                "source": "client-provided",
                "license": "client-provided",
                "retrieved_at": "local",
                "width_px": width,
                "height_px": height,
            },
        }
    manifest = workspace / "asset-manifest.v1.json"
    return manifest, _write_json(manifest, {"schema_version": "1.0", "bindings": bindings})


@dataclass(frozen=True)
class PhysicalAdapterResult:
    plan: AssemblyPlan
    library_index_sha256: str
    fact_store_path: Path
    fact_store_sha256: str
    asset_manifest_path: Path
    asset_manifest_sha256: str
    connective_copy_path: Path
    connective_copy_sha256: str
    lineage: Mapping[str, Any]


def compile_physical_adapter(
    composition_plan: Mapping[str, Any],
    adaptation_plan: Mapping[str, Any],
    adaptation_request: Mapping[str, Any],
    *,
    catalog: Mapping[str, Any],
    private_source_root: Path | str,
    workspace: Path | str,
    asset_paths: Mapping[str, Path | str] | None = None,
) -> PhysicalAdapterResult:
    """Compile one locked composition/adaptation pair to an OPC AssemblyPlan."""

    if composition_plan.get("schema_version") != "1.0" or composition_plan.get("status") != "PASS":
        raise PhysicalAdapterError("COMPOSITION_PLAN_INVALID")
    if adaptation_plan.get("schema_version") != "1.0" or adaptation_plan.get("status") != "PASS":
        raise PhysicalAdapterError("ADAPTATION_PLAN_INVALID")
    if adaptation_plan.get("composition_plan_sha256") != composition_plan_sha256(composition_plan):
        raise PhysicalAdapterError("ADAPTATION_PLAN_DRIFT")
    if adaptation_plan.get("adaptation_request_sha256") != adaptation_request_sha256(adaptation_request):
        raise PhysicalAdapterError("ADAPTATION_REQUEST_DRIFT")
    # Recompilation proves the values have not been decoupled from the ID-only plan.
    expected_adaptation = compile_adaptation(composition_plan, catalog=catalog, request=adaptation_request)
    if serialize_adaptation_plan(expected_adaptation) != serialize_adaptation_plan(adaptation_plan):
        raise PhysicalAdapterError("ADAPTATION_REQUEST_DRIFT")

    stage = Path(workspace).expanduser().resolve(strict=False)
    if stage.is_symlink():
        raise PhysicalAdapterError("WORKSPACE_INVALID")
    stage.mkdir(parents=True, exist_ok=True)
    page_by_id, region_by_id = _page_lookup(catalog)
    source_paths = resolve_catalog_sources(catalog, private_source_root=private_source_root)
    request_facts = _request_facts(adaptation_request)
    operations_by_slide: dict[str, list[Mapping[str, Any]]] = {}
    for operation in adaptation_plan.get("operations", []):
        if not isinstance(operation, Mapping) or not isinstance(operation.get("slide_id"), str):
            raise PhysicalAdapterError("ADAPTATION_PLAN_INVALID")
        operations_by_slide.setdefault(str(operation["slide_id"]), []).append(operation)

    context = AssemblyImportContext()
    fact_records: dict[str, dict[str, Any]] = {}
    targets: list[AssemblyTargetSlide] = []
    lineage_slides: list[dict[str, Any]] = []
    for ordinal, selected in enumerate(composition_plan.get("slides", []), start=1):
        if not isinstance(selected, Mapping):
            raise PhysicalAdapterError("COMPOSITION_PLAN_INVALID")
        slide_id = selected.get("slide_id")
        source = selected.get("source")
        if not isinstance(slide_id, str) or not isinstance(source, Mapping):
            raise PhysicalAdapterError("COMPOSITION_PLAN_INVALID")
        page_id = source.get("page_id")
        page = page_by_id.get(str(page_id))
        if page is None:
            raise PhysicalAdapterError("CATALOG_PAGE_MISSING")
        package_sha = str(source.get("package_sha256", ""))
        slide_number = source.get("slide_number")
        if package_sha != page.get("package_sha256") or slide_number != page.get("slide_number") or package_sha not in source_paths:
            raise PhysicalAdapterError("CATALOG_SOURCE_DRIFT")
        source_path = source_paths[package_sha]
        _, graph = context.graph_for(source_path, package_sha, int(slide_number))
        slots = _discover_slots(graph.slide_xml.decode("utf-8", errors="replace"))
        if not slots:
            raise PhysicalAdapterError("SOURCE_PAGE_HAS_NO_EDITABLE_TEXT")
        slots_by_id = {slot.slot_id: slot for slot in slots}
        legacy_page_id = f"{package_sha}:{int(slide_number):03d}"
        try:
            with zipfile.ZipFile(source_path, "r") as archive:
                governed_content_inventory = _compile_governed_content_inventory(
                    archive, int(slide_number),
                )
        except (OSError, zipfile.BadZipFile) as exc:
            raise PhysicalAdapterError("SOURCE_PACKAGE_UNREADABLE") from exc
        if not governed_content_inventory.get("complete"):
            raise PhysicalAdapterError("SOURCE_CONTENT_INVENTORY_INCOMPLETE")
        template = PageTemplate(
            schema_version="1.0",
            page_id=legacy_page_id,
            package_sha256=package_sha,
            slide_number=int(slide_number),
            source_path=str(source_path),
            source_sha256=package_sha,
            source_slide_sha256=graph.slide_sha,
            page_role=str(selected.get("role", "content")),
            category_names=(str(page.get("category", "unknown")),),
            # Phase 51 has already admitted this page to the locked art-direction
            # family.  The physical importer uses this canonical family ID only
            # for cohesion verification; it must not re-derive a visual choice.
            style_cluster_id=str(composition_plan.get("art_direction", {}).get("anchor_style_signature", "pptx-studio")),
            deck_family_id=str(page.get("deck_id", "unknown")),
            theme_palette=tuple(str(item) for item in page.get("style", {}).get("palette", []) if isinstance(item, str)),
            capacity={"max_text_chars": sum(slot.max_chars for slot in slots), "max_text_runs": len(slots)},
            editability="native_editable",
            certification="certified",
            visual_quality=float(page.get("render", {}).get("visual_quality", 1.0)),
            structure={"catalog_page_id": str(page_id)},
            slot_graph=_slot_graph(slots),
            requires_customer_asset=False,
            media_retention_policy="preserve",
            pool="direct-use",
            decision="certified",
            direct_use=True,
            eligibility_known=True,
            governed_content_inventory=governed_content_inventory,
        )
        bindings: dict[str, str] = {}
        specs: dict[str, TextBindingSpec] = {}
        for slot in slots:
            fact_id, record = _source_fact(slot.text)
            fact_records.setdefault(fact_id, record)
            bindings[slot.slot_id] = slot.text
            specs[slot.slot_id] = TextBindingSpec(slot.text, (fact_id,), "auto")

        slide_lineage: dict[str, Any] = {
            "slide_id": slide_id,
            "ordinal": ordinal,
            "catalog_page_id": page_id,
            "source": {"package_sha256": package_sha, "slide_number": int(slide_number), "source_slide_sha256": graph.slide_sha},
            "text_bindings": [],
            "asset_bindings": [],
        }
        asset_specs: dict[str, AssetBindingSpec] = {}
        for operation in operations_by_slide.get(slide_id, []):
            operation_kind = operation.get("operation")
            if operation_kind == "replace_text":
                region = region_by_id.get(str(operation.get("region_id")))
                fact_ref = operation.get("fact_id")
                if region is None or region.get("page_id") != page_id or not isinstance(fact_ref, str) or fact_ref not in request_facts:
                    raise PhysicalAdapterError("TEXT_OPERATION_DRIFT")
                value = request_facts[fact_ref]
                physical_fact_id, record = _source_fact(value)
                fact_records.setdefault(physical_fact_id, record)
                raw_shape_ids = region.get("editable_shape_ids")
                if not isinstance(raw_shape_ids, list) or not raw_shape_ids:
                    raise PhysicalAdapterError("TEXT_REGION_EMPTY")
                for raw_shape_id in raw_shape_ids:
                    slot_id = f"shape_{raw_shape_id}"
                    slot = slots_by_id.get(slot_id)
                    requested_chars = len("".join(value.split()))
                    if slot is None:
                        raise PhysicalAdapterError(
                            "TEXT_SLOT_UNRESOLVED"
                            f":slide_id={slide_id}:region_id={region['region_id']}"
                            f":shape_id={slot_id}:fact_id={fact_ref}"
                        )
                    if requested_chars > slot.max_chars:
                        # Catalog capacity is deliberately a fast conservative
                        # retrieval signal. The source slide is authoritative at
                        # assembly time, so report the exact non-secret binding
                        # identifier and native capacity rather than forcing an
                        # agent to guess which value must be shortened/split.
                        raise PhysicalAdapterError(
                            "TEXT_SLOT_CAPACITY_EXCEEDED"
                            f":slide_id={slide_id}:region_id={region['region_id']}"
                            f":shape_id={slot_id}:fact_id={fact_ref}"
                            f":requested_chars={requested_chars}:native_capacity={slot.max_chars}"
                        )
                    bindings[slot_id] = value
                    specs[slot_id] = TextBindingSpec(value, (physical_fact_id,), "auto", "shrink-to-fit")
                    slide_lineage["text_bindings"].append({"region_id": region["region_id"], "shape_id": slot_id, "fact_id": fact_ref, "replacement_sha256": _sha256_bytes(value.encode("utf-8"))})
            elif operation_kind == "replace_asset":
                raw_shape_id = operation.get("shape_id")
                asset_id = operation.get("asset_id")
                slot_id = f"shape_{raw_shape_id}"
                if not isinstance(raw_shape_id, str) or not isinstance(asset_id, str):
                    raise PhysicalAdapterError("ASSET_OPERATION_DRIFT")
                asset_specs[slot_id] = AssetBindingSpec(asset_id, "cover")
                slide_lineage["asset_bindings"].append({"shape_id": slot_id, "asset_id": asset_id, "asset_sha256": operation.get("asset_sha256")})
            else:
                raise PhysicalAdapterError("ADAPTATION_OPERATION_UNKNOWN")
        targets.append(AssemblyTargetSlide(
            ordinal=ordinal,
            page_template=template,
            bindings=bindings,
            narrative_role=str(selected.get("role", "content")),
            title="",
            headline="",
            text_binding_specs=specs,
            asset_binding_specs=asset_specs,
        ))
        lineage_slides.append(slide_lineage)

    fact_store = {
        "schema_version": "1.0",
        "project": {"title": "PPTX Studio assembly", "objective": "physical assembly", "audience": "internal", "language": "und"},
        "sources": [{"id": "template-source", "kind": "manual", "locator": "private-template", "sha256": None}],
        "facts": [fact_records[key] for key in sorted(fact_records)],
    }
    fact_path = stage / "fact-store.v1.json"
    fact_sha = _write_json(fact_path, fact_store)
    asset_path, asset_sha = _asset_manifest(adaptation_request, asset_paths or {}, stage)
    connective_path = stage / "connective-copy.v1.json"
    connective_sha = _write_json(connective_path, {"schema_version": "1.0", "entries": []})
    fingerprint = _sha256_bytes(_canonical_json({"catalog_id": catalog.get("catalog_id"), "composition": composition_plan_sha256(composition_plan), "adaptation": adaptation_plan.get("composition_plan_sha256")}))
    plan = AssemblyPlan(
        schema_version="1.0",
        plan_id=f"pptx-studio-{fingerprint[:16]}",
        scenario_id="pptx-studio",
        dominant_style_cluster_id=str(composition_plan.get("art_direction", {}).get("anchor_style_signature", "pptx-studio")),
        created_at="2026-08-12T00:00:00Z",
        target_slide_count=len(targets),
        target_slides=tuple(targets),
        library_index_sha256=fingerprint,
        authority=AuthorityLock(str(fact_path), fact_sha, str(asset_path), asset_sha, str(connective_path), connective_sha),
    )
    lineage = {
        "schema_version": "1.0",
        "status": "PASS",
        "composition_plan_sha256": composition_plan_sha256(composition_plan),
        "adaptation_plan_sha256": _sha256_bytes(serialize_adaptation_plan(adaptation_plan).encode("utf-8")),
        "slides": lineage_slides,
    }
    return PhysicalAdapterResult(plan, fingerprint, fact_path, fact_sha, asset_path, asset_sha, connective_path, connective_sha, lineage)


def assemble_from_plans(
    composition_plan: Mapping[str, Any],
    adaptation_plan: Mapping[str, Any],
    adaptation_request: Mapping[str, Any],
    *,
    catalog: Mapping[str, Any],
    private_source_root: Path | str,
    workspace: Path | str,
    output_path: Path | str,
    asset_paths: Mapping[str, Path | str] | None = None,
) -> tuple[PhysicalAssemblyReport, dict[str, Any]]:
    """Materialize a new editable PPTX and return evidence without client text."""

    compiled = compile_physical_adapter(
        composition_plan, adaptation_plan, adaptation_request,
        catalog=catalog, private_source_root=private_source_root, workspace=workspace,
        asset_paths=asset_paths,
    )
    report = assemble_physical_deck(
        compiled.plan, output_path,
        library_index_sha256=compiled.library_index_sha256,
        fact_store_path=compiled.fact_store_path,
        fact_store_sha256=compiled.fact_store_sha256,
        asset_manifest_path=compiled.asset_manifest_path,
        asset_manifest_sha256=compiled.asset_manifest_sha256,
        connective_copy_path=compiled.connective_copy_path,
        connective_copy_sha256=compiled.connective_copy_sha256,
        require_locked_authority=True,
        # LibreOffice is a portable opening/rendering check, not a Windows COM
        # dependency.  The legacy verifier requires these release checks when
        # a plan carries locked authority.
        require_libreoffice=True,
        max_output_size_bytes=33_941_179,
    )
    lineage = dict(compiled.lineage)
    lineage["output_sha256"] = _sha256_file(Path(output_path))
    lineage["physical_report_status"] = report.status
    qa = run_studio_qa(
        output_path, plan=compiled.plan, physical_report=report, lineage=lineage,
    )
    lineage["qa"] = qa.to_dict()
    return report, lineage
