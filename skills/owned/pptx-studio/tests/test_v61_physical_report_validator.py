"""Focused tests for the independent v6.1 physical-report validator."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import jsonschema
import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
SCHEMA_PATH = SKILL_ROOT / "schemas" / "physical-assembly-report.v1.schema.json"
sys.path.insert(0, str(SCRIPTS_ROOT))

from validate_window_pptx_v61_physical_report import (  # noqa: E402
    PHASE49_GOVERNED_INVENTORY_SHA256,
    _governed_inventory_identity_sha256,
    _independent_style_clone_scope_sha256,
    _independent_style_clone_target_guard_sha256,
    _read_slide_shape_text,
    _read_slide_shape_text_variants,
    main,
    validate_physical_report,
)


PACKAGE_RELATIONSHIP_NS = (
    "http://schemas.openxmlformats.org/package/2006/relationships"
)
RELATIONSHIP_TAG = f"{{{PACKAGE_RELATIONSHIP_NS}}}Relationship"
OFFICE_RELATIONSHIP_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)


def test_shape_text_reader_joins_runs_within_paragraphs_only() -> None:
    slide = (
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<p:cSld><p:spTree><p:sp><p:nvSpPr><p:cNvPr id="7" name="metric"/>'
        '</p:nvSpPr><p:txBody><a:bodyPr/><a:p><a:r><a:t>44.6</a:t></a:r>'
        '<a:r><a:t>%</a:t></a:r></a:p><a:p><a:r><a:t>同比</a:t></a:r>'
        '<a:r><a:t>增长</a:t></a:r></a:p></p:txBody></p:sp>'
        '</p:spTree></p:cSld></p:sld>'
    ).encode()

    assert _read_slide_shape_text(slide, 7) == "44.6%\n同比增长"
    assert _read_slide_shape_text_variants(slide, 7) == (
        "44.6%\n同比增长",
        "44.6%同比增长",
        "44.6\n%\n同比\n增长",
    )


def test_independent_style_clone_hashes_exclude_text_geometry_and_relationships() -> None:
    slide = (
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<p:cSld><p:spTree><p:sp><p:nvSpPr><p:cNvPr id="7" name="metric"/>'
        '</p:nvSpPr><p:spPr><a:xfrm><a:off x="1" y="2"/></a:xfrm>'
        '<a:solidFill><a:schemeClr val="accent1"/></a:solidFill></p:spPr>'
        '<p:txBody><a:bodyPr><a:noAutofit/></a:bodyPr><a:p><a:r>'
        '<a:rPr sz="2400"><a:solidFill><a:schemeClr val="accent1"/>'
        '</a:solidFill></a:rPr><a:t>44.6%</a:t></a:r></a:p></p:txBody>'
        '</p:sp></p:spTree></p:cSld></p:sld>'
    ).encode()

    assert len(_independent_style_clone_scope_sha256(slide, 7, "shape-fill")) == 64
    guard = _independent_style_clone_target_guard_sha256(slide, 7, "shape-fill")
    changed_text = slide.replace(b"44.6%", b"49.1%")
    changed_geometry = slide.replace(b'x="1"', b'x="99"')

    assert _independent_style_clone_target_guard_sha256(
        changed_text, 7, "shape-fill"
    ) == guard
    assert _independent_style_clone_target_guard_sha256(
        changed_geometry, 7, "shape-fill"
    ) != guard


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_deck(path: Path, slide_count: int) -> dict[int, str]:
    slide_hashes: dict[int, str] = {}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/ppt/presentation.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
                + "".join(
                    '<Override '
                    f'PartName="/ppt/slides/slide{ordinal}.xml" '
                    'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
                    for ordinal in range(1, slide_count + 1)
                )
                + "</Types>"
            ).encode(),
        )
        archive.writestr(
            "_rels/.rels",
            (
                f'<Relationships xmlns="{PACKAGE_RELATIONSHIP_NS}">'
                f'<Relationship Id="rId1" Type="{OFFICE_RELATIONSHIP_NS}/officeDocument" '
                'Target="ppt/presentation.xml"/>'
                "</Relationships>"
            ).encode(),
        )
        archive.writestr(
            "ppt/presentation.xml",
            (
                '<p:presentation xmlns:p="http://schemas.openxmlformats.org/'
                'presentationml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/'
                '2006/relationships">'
                '<p:sldIdLst>'
                + "".join(
                    f'<p:sldId id="{255 + ordinal}" r:id="rId{ordinal}"/>'
                    for ordinal in range(1, slide_count + 1)
                )
                + '</p:sldIdLst><p:sldSz cx="12192000" cy="6858000" '
                'type="screen16x9"/><p:notesSz cx="6858000" cy="9144000"/>'
                '</p:presentation>'
            ).encode(),
        )
        slide_relationships = "".join(
            (
                f'<Relationship Id="rId{ordinal}" '
                f'Type="{OFFICE_RELATIONSHIP_NS}/slide" '
                f'Target="slides/slide{ordinal}.xml"/>'
            )
            for ordinal in range(1, slide_count + 1)
        )
        archive.writestr(
            "ppt/_rels/presentation.xml.rels",
            (
                f'<Relationships xmlns="{PACKAGE_RELATIONSHIP_NS}">'
                f"{slide_relationships}</Relationships>"
            ).encode(),
        )
        for ordinal in range(1, slide_count + 1):
            payload = _text_slide_xml(f"Slide {ordinal}")
            name = f"ppt/slides/slide{ordinal}.xml"
            archive.writestr(name, payload)
            slide_hashes[ordinal] = hashlib.sha256(payload).hexdigest()
    return slide_hashes


def _relationship_counts(path: Path) -> tuple[int, int, int]:
    total = 0
    internal = 0
    external = 0
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith(".rels"):
                continue
            root = ET.fromstring(archive.read(name))
            for relation in list(root):
                if relation.tag != RELATIONSHIP_TAG:
                    continue
                total += 1
                if relation.attrib.get("TargetMode", "").lower() == "external":
                    external += 1
                else:
                    internal += 1
    return total, internal, external


def _rewrite_deck(
    path: Path,
    updates: dict[str, bytes],
    *,
    remove: set[str] | None = None,
) -> None:
    with zipfile.ZipFile(path) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    for name in remove or set():
        parts.pop(name, None)
    parts.update(updates)
    temporary = path.with_name(f".{path.name}.rewrite")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload)
    temporary.replace(path)


def _refresh_output_bindings(
    report: dict[str, Any],
    output: Path,
    *,
    sync_relationship_counts: bool = True,
) -> None:
    with zipfile.ZipFile(output) as archive:
        names = sorted(archive.namelist())
    output_size = output.stat().st_size
    report["output_sha256"] = _sha(output)
    report["opc_integrity"]["package_entry_count"] = len(names)
    report["opc_integrity"]["media_count"] = sum(
        1 for name in names if "media/" in name
    )
    if sync_relationship_counts:
        total, internal, external = _relationship_counts(output)
        report["opc_integrity"]["total_relationship_count"] = total
        report["opc_integrity"]["internal_relationship_count"] = internal
        report["opc_integrity"]["external_relationship_count"] = external
    report["assembly_metrics"]["output_size_bytes"] = output_size
    report["assembly_metrics"]["source_size_bytes"] = output_size
    report["assembly_metrics"]["imported_part_count"] = len(names)
    report["assembly_metrics"]["imported_parts"] = names
    report["assembly_metrics"]["unique_dependency_part_count"] = max(
        0,
        len(names) - report["target_slide_count"],
    )
    report["assembly_metrics"]["amplification_ratio"] = 1
    report["size_check"]["output_size_bytes"] = output_size
    report["size_check"]["max_output_size_bytes"] = output_size + 1024
    with zipfile.ZipFile(output) as archive:
        for record in report.get("lineage_records", []):
            ordinal = record.get("ordinal")
            slide_name = f"ppt/slides/slide{ordinal}.xml"
            if type(ordinal) is int and slide_name in archive.namelist():
                record["target_slide_sha256"] = hashlib.sha256(
                    archive.read(slide_name)
                ).hexdigest()


def _write_authority(project: Path, name: str, payload: bytes) -> tuple[str, str]:
    path = project / name
    path.write_bytes(payload)
    return str(path.resolve()), _sha(path)


def _authority_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _minimal_fact_store() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "project": {"title": "Validator fixture", "language": "en-US"},
        "sources": [
            {"id": "fixture-source", "kind": "manual", "locator": "fixture"}
        ],
        "facts": [
            {
                "id": "fixture-fact",
                "kind": "metric",
                "text": "42",
                "allowed_renderings": ["42 units"],
                "language": "en-US",
                "source_id": "fixture-source",
                "locator": "fixture#42",
                "required": False,
                "value": 42,
                "unit": " units",
                "status": "active",
            }
        ],
    }


def _minimal_asset_manifest() -> dict[str, Any]:
    return {"schema_version": "1.0", "bindings": {}}


def _minimal_connective_copy() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "entries": [{"id": "connective-clear", "text": ""}],
    }


def _replace_authority_payload(
    report: dict[str, Any],
    authority_name: str,
    payload: Any,
) -> None:
    path = Path(report["authority"][f"{authority_name}_path"])
    data = payload if isinstance(payload, bytes) else _authority_bytes(payload)
    path.write_bytes(data)
    report["authority"][f"{authority_name}_sha256"] = _sha(path)


def _text_slide_xml(text: str, *, shape_id: int = 2) -> bytes:
    return (
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<p:cSld><p:spTree><p:sp><p:nvSpPr>'
        f'<p:cNvPr id="{shape_id}" name="Text {shape_id}"/>'
        '<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
        f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>{text}</a:t>'
        '</a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>'
    ).encode()


def _text_binding_evidence(
    replacement: str,
    *,
    fact_refs: list[str] | None = None,
    connective_ref: str = "",
    fit_policy: str = "preserve",
) -> dict[str, Any]:
    return {
        "ordinal": 1,
        "page_id": f"{'a' * 64}:001",
        "slot_id": "shape_2",
        "shape_id": 2,
        "binding_kind": "text",
        "mode": "exact" if fact_refs else "connective",
        "fit_policy": fit_policy,
        "source_sha256": "f" * 64,
        "replacement_sha256": hashlib.sha256(replacement.encode()).hexdigest(),
        "fact_refs": fact_refs or [],
        "asset_refs": [],
        "connective_ref": connective_ref,
        "relationship_id": "",
        "target_part": "",
        "capacity": {
            "chars": {"used": len(replacement), "limit": max(1, len(replacement))},
            "items": {"used": 1, "limit": 1},
            "images": {"used": 0, "limit": 0},
        },
        "status": "pass",
    }


def _picture_slide_xml(*, shape_id: int = 2, relationship_id: str = "rImage") -> bytes:
    return (
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<p:cSld><p:spTree><p:pic><p:nvPicPr>'
        f'<p:cNvPr id="{shape_id}" name="Picture {shape_id}"/>'
        '<p:cNvPicPr/><p:nvPr/></p:nvPicPr><p:blipFill>'
        f'<a:blip r:embed="{relationship_id}"/><a:stretch><a:fillRect/>'
        '</a:stretch></p:blipFill><p:spPr/></p:pic></p:spTree></p:cSld></p:sld>'
    ).encode()


def _table_slide_xml(first: str, second: str, *, shape_id: int = 2) -> bytes:
    return (
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<p:cSld><p:spTree><p:graphicFrame><p:nvGraphicFramePr>'
        f'<p:cNvPr id="{shape_id}" name="Table {shape_id}"/>'
        '<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>'
        '<a:graphic><a:graphicData><a:tbl><a:tr>'
        f'<a:tc><a:txBody><a:p><a:r><a:t>{first}</a:t></a:r></a:p></a:txBody></a:tc>'
        f'<a:tc><a:txBody><a:p><a:r><a:t>{second}</a:t></a:r></a:p></a:txBody></a:tc>'
        '</a:tr></a:tbl></a:graphicData></a:graphic>'
        '</p:graphicFrame></p:spTree></p:cSld></p:sld>'
    ).encode()


def _chart_slide_xml(*, shape_id: int = 2, relationship_id: str = "rChart") -> bytes:
    return (
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<p:cSld><p:spTree><p:graphicFrame><p:nvGraphicFramePr>'
        f'<p:cNvPr id="{shape_id}" name="Chart {shape_id}"/>'
        '<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>'
        '<a:graphic><a:graphicData>'
        f'<c:chart r:id="{relationship_id}"/>'
        '</a:graphicData></a:graphic>'
        '</p:graphicFrame></p:spTree></p:cSld></p:sld>'
    ).encode()


def _chart_xml(package_relationship_id: str) -> bytes:
    return (
        '<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<c:chart/><c:externalData '
        f'r:id="{package_relationship_id}"/>'
        '</c:chartSpace>'
    ).encode()


def _xlsx_with_value(value: str) -> bytes:
    xlsxwriter = pytest.importorskip("xlsxwriter")
    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
    worksheet = workbook.add_worksheet("Sheet1")
    worksheet.write_string("A1", value)
    workbook.close()
    return buffer.getvalue()


def _xlsx_with_forbidden_vba(value: str) -> bytes:
    source = _xlsx_with_value(value)
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(source)) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    parts["xl/vbaProject.bin"] = b"forbidden"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload)
    return output.getvalue()


def _embedded_binding_evidence(
    slot_id: str,
    replacement: str,
    *,
    fact_ref: str = "fixture-fact",
) -> dict[str, Any]:
    return {
        **_text_binding_evidence(replacement, fact_refs=[fact_ref]),
        "slot_id": slot_id,
        "binding_kind": "embedded",
        "mode": "source-fact",
    }


def _valid_report(
    project: Path,
    *,
    slide_count: int = 1,
    phase49: bool = False,
) -> tuple[dict[str, Any], Path]:
    project.mkdir(parents=True, exist_ok=True)
    output = project / "output.pptx"
    slide_hashes = _write_deck(output, slide_count)
    fact_path, fact_sha = _write_authority(
        project,
        "fact-store.json",
        _authority_bytes(_minimal_fact_store()),
    )
    asset_path, asset_sha = _write_authority(
        project,
        "asset-manifest.json",
        _authority_bytes(_minimal_asset_manifest()),
    )
    copy_path, copy_sha = _write_authority(
        project,
        "connective-copy.json",
        _authority_bytes(_minimal_connective_copy()),
    )
    query_path, query_sha = _write_authority(project, "query-bundle.json", b"query")
    with zipfile.ZipFile(output) as archive:
        names = sorted(archive.namelist())
    relationship_total, relationship_internal, relationship_external = (
        _relationship_counts(output)
    )
    lineage = [
        {
            "ordinal": ordinal,
            "page_id": f"{'a' * 64}:{ordinal:03d}",
            "package_sha256": "a" * 64,
            "slide_number": ordinal,
            "source_sha256": "a" * 64,
            "source_slide_sha256": "b" * 64,
            "target_slide_sha256": slide_hashes[ordinal],
            "source_package_verified": True,
            "source_slide_verified": True,
            "structure_signature_source": "c" * 64,
            "structure_signature_target": "c" * 64,
            "structure_match": True,
            "imported_part_map_sha256": "d" * 64,
            "imported_part_count": 1,
            "narrative_role": "content",
            "title": f"Slide {ordinal}",
            "status": "pass",
            "binding_count": 0,
            "byte_match_score": 0.9,
        }
        for ordinal in range(1, slide_count + 1)
    ]
    selection = (
        {
            "mode": "locked",
            "query_bundle_path": query_path,
            "query_bundle_sha256": query_sha,
            "library_index_sha256": "e" * 64,
            "query_count": slide_count,
            "selected_count": slide_count,
            "distinct_query_id_count": slide_count,
            "distinct_page_id_count": slide_count,
            "status": "pass",
        }
        if phase49
        else {
            "mode": "not_required",
            "query_bundle_path": "",
            "query_bundle_sha256": "",
            "library_index_sha256": "e" * 64,
            "query_count": 0,
            "selected_count": 0,
            "distinct_query_id_count": 0,
            "distinct_page_id_count": 0,
            "status": "not_required",
        }
    )
    output_size = output.stat().st_size
    report = {
        "schema_version": "1.0",
        "report_id": "report-1",
        "plan_id": "plan-1",
        "output_path": str(output.resolve()),
        "output_sha256": _sha(output),
        "acceptance_profile": (
            "phase49-work-report-15" if phase49 else "standard"
        ),
        "expected_slide_count": 15 if phase49 else None,
        "status": "pass",
        "target_slide_count": slide_count,
        "distinct_page_id_count": slide_count,
        "duplicate_page_records": [],
        "lineage_records": lineage,
        "opc_integrity": {
            "zip_open": True,
            "content_types_parsed": True,
            "slide_rels_resolved": True,
            "package_entry_count": len(names),
            "media_count": 0,
            "total_relationship_count": relationship_total,
            "internal_relationship_count": relationship_internal,
            "external_relationship_count": relationship_external,
            "unresolved_internal_relationship_count": 0,
            "unresolved_internal_relationships": [],
            "unsafe_relationship_count": 0,
            "unsafe_relationships": [],
            "status": "pass",
            "details": "",
        },
        "editability": {
            "native_editable": True,
            "python_pptx_open": True,
            "slide_count": slide_count,
            "text_run_count": slide_count,
            "shape_count": slide_count,
            "native_object_count": slide_count,
            "picture_count": 0,
            "native_editable_slide_count": slide_count,
            "full_slide_raster_count": 0,
            "raster_dominant_slide_count": 0,
            "native_editable_coverage": 1,
            "status": "pass",
        },
        "style_cluster_adherence": {
            "dominant_style_cluster_id": "reference-work-summary",
            "matches": slide_count,
            "total": slide_count,
            "status": "pass",
        },
        "assembly_metrics": {
            "output_size_bytes": output_size,
            "source_size_bytes": output_size,
            "unique_source_package_count": 1,
            "imported_part_count": len(names),
            "imported_parts": names,
            "unique_dependency_part_count": max(0, len(names) - slide_count),
            "same_source_reuse_count": 0,
            "same_source_reuse_bytes": 0,
            "cross_source_safe_dedup_count": 0,
            "cross_source_safe_dedup_bytes": 0,
            "deduplicated_part_count": 0,
            "deduplicated_bytes": 0,
            "static_duplicate_bytes": 0,
            "unresolved_internal_relationship_count": 0,
            "amplification_ratio": 1,
            "parts_by_kind": {"slide": slide_count},
        },
        "authority": {
            "mode": "locked",
            "fact_store_path": fact_path,
            "fact_store_sha256": fact_sha,
            "asset_manifest_path": asset_path,
            "asset_manifest_sha256": asset_sha,
            "connective_copy_path": copy_path,
            "connective_copy_sha256": copy_sha,
            "status": "pass",
        },
        "selection_authority": selection,
        "binding_evidence": [],
        "source_residue": {
            "governed_content_slot_count": 0,
            "governed_content_binding_count": 0,
            "verified_governed_content_count": 0,
            "governed_content_mismatch_count": 0,
            "peer_group_mismatch_count": 0,
            "mutation_manifest_sha256": hashlib.sha256(b"[]").hexdigest(),
            "governed_mutations": [],
            "unauthorized_content_count": 0,
            "tag_part_count": 0,
            "tag_relationship_count": 0,
            "layout_master_cached_field_count": 0,
            "certified_media_count": 0,
            "media_hash_mismatch_count": 0,
            "replacement_asset_count": 0,
            "replacement_asset_hash_mismatch_count": 0,
            "asset_slot_mismatch_count": 0,
            "orphan_media_count": 0,
            "status": "pass",
        },
        "libreoffice": {
            "available": True,
            "executable": "/usr/bin/libreoffice",
            "open_result": "pass",
            "render_result": "pass",
            "status": "pass",
            "details": "",
        },
        "size_check": {
            "output_size_bytes": output_size,
            "max_output_size_bytes": output_size + 1024,
            "status": "pass",
        },
    }
    if phase49:
        profile_path = (
            SKILL_ROOT
            / "registries"
            / "v61-binding-profiles"
            / "phase49-work-report-15.binding-profile.v1.json"
        )
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        style_clones = [
            (slide, clone)
            for slide in profile["slides"]
            for clone in slide.get("style_clones", ())
        ]
        report["binding_profile_authority"] = {
            "profile_id": profile["profile_id"],
            "profile_sha256": _sha(profile_path),
            "acceptance_profile": profile["acceptance_profile"],
            "style_clone_count": len(style_clones),
            "status": "pass",
        }
        report["style_clone_evidence"] = [
            {
                "ordinal": slide["ordinal"],
                "page_id": slide["page_id"],
                "source_shape_id": clone["source_shape_id"],
                "target_shape_id": clone["target_shape_id"],
                "scope": clone["scope"],
                "expected_style_sha256": clone["source_style_sha256"],
                "actual_source_style_sha256": clone["source_style_sha256"],
                "actual_target_style_sha256": clone["source_style_sha256"],
                "actual_target_guard_sha256": clone["target_guard_sha256"],
                "status": "pass",
            }
            for slide, clone in style_clones
        ]
    report_path = project / "physical-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return report, report_path


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


def _schema_errors(report: dict[str, Any]) -> list[jsonschema.ValidationError]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return list(jsonschema.Draft202012Validator(schema).iter_errors(report))


def test_valid_report_is_hash_size_and_path_bound_with_machine_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "project"
    _, report_path = _valid_report(project)

    result = validate_physical_report(report_path, project)
    exit_code = main(["--project-root", str(project), "--report", report_path.name])
    emitted = json.loads(capsys.readouterr().out)

    assert result["status"] == "pass"
    assert result["issue_count"] == 0
    assert result["observed"]["output_sha256"] == _sha(project / "output.pptx")
    assert result["observed"]["output_size_bytes"] == (project / "output.pptx").stat().st_size
    assert exit_code == 0
    assert emitted["status"] == "pass"
    assert emitted["validator_id"] == "pptx-studio-v61-physical-report-validator"


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("lineage_records", 0, "status"), "fail"),
        (("lineage_records", 0, "source_package_verified"), False),
        (("lineage_records", 0, "source_slide_verified"), False),
        (("lineage_records", 0, "structure_match"), False),
        (("opc_integrity", "zip_open"), False),
        (("opc_integrity", "unresolved_internal_relationship_count"), 1),
        (("editability", "native_editable"), False),
        (("editability", "python_pptx_open"), False),
        (("editability", "native_editable_coverage"), 0.5),
        (("editability", "raster_dominant_slide_count"), 1),
        (("libreoffice", "open_result"), "fail"),
        (("libreoffice", "render_result"), "not_run"),
        (("size_check", "status"), "not_run"),
        (("authority", "fact_store_path"), ""),
        (("authority", "fact_store_sha256"), ""),
        (("source_residue", "governed_content_mismatch_count"), 1),
        (("source_residue", "peer_group_mismatch_count"), 1),
        (("source_residue", "tag_relationship_count"), 1),
        (("source_residue", "replacement_asset_hash_mismatch_count"), 1),
        (("source_residue", "asset_slot_mismatch_count"), 1),
        (("source_residue", "orphan_media_count"), 1),
    ],
)
def test_schema_rejects_contradictory_pass_states(
    tmp_path: Path,
    path: tuple[Any, ...],
    value: Any,
) -> None:
    report, _ = _valid_report(tmp_path / "project")
    cursor: Any = report
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = value

    assert _schema_errors(report)


def test_schema_rejects_empty_locked_selection_identity(tmp_path: Path) -> None:
    report, _ = _valid_report(
        tmp_path / "project",
        slide_count=15,
        phase49=True,
    )
    report["selection_authority"]["query_bundle_path"] = ""
    report["selection_authority"]["query_bundle_sha256"] = ""

    assert _schema_errors(report)


def test_output_drift_fails_and_cli_returns_nonzero_machine_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "project"
    _, report_path = _valid_report(project)
    with (project / "output.pptx").open("ab") as stream:
        stream.write(b"drift")

    result = validate_physical_report(report_path, project)
    exit_code = main(["--project-root", str(project), "--report", report_path.name])
    emitted = json.loads(capsys.readouterr().out)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "OUTPUT_SHA256_MISMATCH" in codes
    assert "ASSEMBLY_OUTPUT_SIZE_MISMATCH" in codes
    assert "SIZE_CHECK_OUTPUT_MISMATCH" in codes
    assert exit_code == 1
    assert emitted["status"] == "fail"
    assert emitted["issue_count"] > 0


def test_phase49_validator_rejects_duplicate_page_ids_and_ordinals(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project, slide_count=15, phase49=True)
    assert not _schema_errors(report)

    duplicate_page = copy.deepcopy(report)
    duplicate_page["lineage_records"][14]["page_id"] = duplicate_page[
        "lineage_records"
    ][0]["page_id"]
    _write_report(report_path, duplicate_page)
    page_result = validate_physical_report(report_path, project)
    page_codes = {issue["code"] for issue in page_result["issues"]}

    duplicate_ordinal = copy.deepcopy(report)
    duplicate_ordinal["lineage_records"][14]["ordinal"] = 1
    _write_report(report_path, duplicate_ordinal)
    ordinal_result = validate_physical_report(report_path, project)
    ordinal_codes = {issue["code"] for issue in ordinal_result["issues"]}

    assert "PHASE49_PAGE_IDS_NOT_UNIQUE" in page_codes
    assert "DISTINCT_PAGE_COUNT_MISMATCH" in page_codes
    assert "PHASE49_ORDINALS_MISMATCH" in ordinal_codes
    assert "LINEAGE_ORDINAL_SET_MISMATCH" in ordinal_codes


def test_validator_rejects_cross_field_lies_and_paths_outside_project(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    outside = tmp_path / "outside.pptx"
    outside.write_bytes((project / "output.pptx").read_bytes())
    report["output_path"] = str(outside.resolve())
    report["distinct_page_id_count"] = 2
    report["style_cluster_adherence"]["matches"] = 0
    report["source_residue"]["verified_governed_content_count"] = 1
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "BOUND_PATH_OUTSIDE_PROJECT" in codes
    assert "DISTINCT_PAGE_COUNT_MISMATCH" in codes
    assert "STYLE_MATCH_COUNT_MISMATCH" in codes
    assert "GOVERNED_VERIFIED_COUNT_MISMATCH" in codes


def test_namespace_aware_parser_accepts_prefixes_and_single_quotes(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(
        output,
        {
            "_rels/.rels": (
                f"<pr:Relationships xmlns:pr='{PACKAGE_RELATIONSHIP_NS}'>"
                f"<pr:Relationship Id='rId1' Type='{OFFICE_RELATIONSHIP_NS}/officeDocument' "
                "Target='ppt/presentation.xml'/></pr:Relationships>"
            ).encode(),
            "ppt/_rels/presentation.xml.rels": (
                f"<pr:Relationships xmlns:pr='{PACKAGE_RELATIONSHIP_NS}'>"
                f"<pr:Relationship Id='rId1' Type='{OFFICE_RELATIONSHIP_NS}/slide' "
                "Target='slides/slide1.xml'/></pr:Relationships>"
            ).encode(),
        },
    )
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)

    assert result["status"] == "pass"
    assert result["issue_count"] == 0
    assert result["observed"]["opc_reachable_part_count"] == 2


def test_validator_accepts_safe_https_external_relationship(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    with zipfile.ZipFile(output) as archive:
        presentation_rels = archive.read("ppt/_rels/presentation.xml.rels")
    safe_relationship = (
        f"<Relationship Id='rSafe' Type='{OFFICE_RELATIONSHIP_NS}/hyperlink' "
        "Target='https://example.com/report' TargetMode='External'/>"
    ).encode()
    _rewrite_deck(
        output,
        {
            "ppt/_rels/presentation.xml.rels": presentation_rels.replace(
                b"</Relationships>",
                safe_relationship + b"</Relationships>",
            )
        },
    )
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)

    assert result["status"] == "pass"
    assert result["observed"]["opc_external_relationship_count"] == 1


@pytest.mark.parametrize(
    ("relationship", "extra_parts"),
    [
        (
            (
                f"<Relationship Id='rUnsafe' Type='{OFFICE_RELATIONSHIP_NS}/hyperlink' "
                "Target='file:///tmp/private.txt' TargetMode='External'/>"
            ),
            {},
        ),
        (
            (
                f"<Relationship Id='rUnsafe' Type='{OFFICE_RELATIONSHIP_NS}/activeXControl' "
                "Target='activeX/activeX1.xml'/>"
            ),
            {"ppt/activeX/activeX1.xml": b"<activeX/>"},
        ),
        (
            (
                f"<Relationship Id='rUnsafe' Type='{OFFICE_RELATIONSHIP_NS}/image' "
                "Target='media/payload.exe'/>"
            ),
            {"ppt/media/payload.exe": b"MZ"},
        ),
        (
            (
                f"<Relationship Id='rUnsafe' Type='{OFFICE_RELATIONSHIP_NS}/macroLink' "
                "Target='macros/item.xml'/>"
            ),
            {"ppt/macros/item.xml": b"<macro/>"},
        ),
        (
            (
                f"<Relationship Id='rUnsafe' Type='{OFFICE_RELATIONSHIP_NS}/script' "
                "Target='scripts/item.xml'/>"
            ),
            {"ppt/scripts/item.xml": b"<script/>"},
        ),
        (
            (
                f"<Relationship Id='rUnsafe' Type='{OFFICE_RELATIONSHIP_NS}/image' "
                "Target='media/payload.py'/>"
            ),
            {"ppt/media/payload.py": b"print('owned')"},
        ),
    ],
    ids=(
        "file-uri",
        "activex",
        "executable",
        "macro-link",
        "script-type",
        "python-payload",
    ),
)
def test_validator_rejects_unsafe_relationships(
    tmp_path: Path,
    relationship: str,
    extra_parts: dict[str, bytes],
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    with zipfile.ZipFile(output) as archive:
        presentation_rels = archive.read("ppt/_rels/presentation.xml.rels")
    updated_rels = presentation_rels.replace(
        b"</Relationships>",
        relationship.encode() + b"</Relationships>",
    )
    _rewrite_deck(
        output,
        {
            "ppt/_rels/presentation.xml.rels": updated_rels,
            **extra_parts,
        },
    )
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "OPC_UNSAFE_RELATIONSHIP" in codes
    assert "OPC_UNSAFE_COUNT_ACTUAL_MISMATCH" in codes


def test_validator_rejects_malformed_relationship_xml(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(
        output,
        {"ppt/_rels/presentation.xml.rels": b"<Relationships"},
    )
    _refresh_output_bindings(
        report,
        output,
        sync_relationship_counts=False,
    )
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "OPC_RELATIONSHIP_XML_MALFORMED" in codes


def test_validator_requires_root_relationship_closure(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(output, {}, remove={"_rels/.rels"})
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "OPC_ROOT_RELATIONSHIPS_MISSING" in codes
    assert "OPC_SLIDE_NOT_ROOT_REACHABLE" in codes


def test_validator_rejects_missing_internal_relationship_target(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    with zipfile.ZipFile(output) as archive:
        presentation_rels = archive.read("ppt/_rels/presentation.xml.rels")
    missing_relationship = (
        f"<Relationship Id='rMissing' Type='{OFFICE_RELATIONSHIP_NS}/slide' "
        "Target='slides/missing.xml'/>"
    ).encode()
    _rewrite_deck(
        output,
        {
            "ppt/_rels/presentation.xml.rels": presentation_rels.replace(
                b"</Relationships>",
                missing_relationship + b"</Relationships>",
            )
        },
    )
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "OPC_INTERNAL_TARGET_MISSING" in codes
    assert "OPC_UNRESOLVED_COUNT_ACTUAL_MISMATCH" in codes
    assert "ASSEMBLY_OPC_UNRESOLVED_ACTUAL_MISMATCH" in codes


def test_unreachable_relationship_cannot_mask_orphan_media(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(
        output,
        {
            "ppt/orphan/ghost.xml": b"<ghost/>",
            "ppt/orphan/_rels/ghost.xml.rels": (
                f"<Relationships xmlns='{PACKAGE_RELATIONSHIP_NS}'>"
                f"<Relationship Id='rId1' Type='{OFFICE_RELATIONSHIP_NS}/image' "
                "Target='../media/orphan.png'/></Relationships>"
            ).encode(),
            "ppt/media/orphan.png": b"not-a-real-png",
        },
    )
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "ORPHAN_MEDIA_COUNT_MISMATCH" in codes
    assert result["observed"]["opc_reachable_part_count"] == 2


def test_reported_relationship_counts_are_checked_against_package(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    report["opc_integrity"]["total_relationship_count"] += 1
    report["opc_integrity"]["internal_relationship_count"] += 1
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "OPC_TOTAL_RELATIONSHIP_COUNT_ACTUAL_MISMATCH" in codes
    assert "OPC_INTERNAL_RELATIONSHIP_COUNT_ACTUAL_MISMATCH" in codes


@pytest.mark.parametrize(
    ("authority_name", "payload", "expected_code"),
    [
        ("fact_store", b"not-json", "FACT_STORE_JSON_INVALID"),
        (
            "asset_manifest",
            {"schema_version": "1.0", "bindings": []},
            "ASSET_MANIFEST_SCHEMA_INVALID",
        ),
        (
            "connective_copy",
            {
                "schema_version": "1.0",
                "entries": [
                    {"id": "duplicate", "text": "A"},
                    {"id": "duplicate", "text": "B"},
                ],
            },
            "CONNECTIVE_COPY_ID_DUPLICATE",
        ),
    ],
)
def test_locked_authority_is_parsed_and_semantically_validated_after_hash_binding(
    tmp_path: Path,
    authority_name: str,
    payload: Any,
    expected_code: str,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    _replace_authority_payload(report, authority_name, payload)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert expected_code in codes


def test_fact_store_semantic_cross_references_are_revalidated(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    facts = _minimal_fact_store()
    facts["facts"][0]["source_id"] = "missing-source"
    _replace_authority_payload(report, "fact_store", facts)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "FACT_STORE_SOURCE_REF_UNKNOWN" in codes


def test_text_binding_value_must_be_present_in_and_authorized_by_output_and_fact_store(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(output, {"ppt/slides/slide1.xml": _text_slide_xml("hacked")})
    report["binding_evidence"] = [
        _text_binding_evidence("hacked", fact_refs=["fixture-fact"])
    ]
    report["lineage_records"][0]["binding_count"] = 1
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "BINDING_VALUE_NOT_FACT_AUTHORIZED" in codes


def test_text_binding_authorized_fact_rendering_passes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(output, {"ppt/slides/slide1.xml": _text_slide_xml("42 units")})
    report["binding_evidence"] = [
        _text_binding_evidence("42 units", fact_refs=["fixture-fact"])
    ]
    report["lineage_records"][0]["binding_count"] = 1
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)

    assert result["status"] == "pass"
    assert result["issue_count"] == 0


def test_no_autofit_evidence_is_recomputed_from_output_xml(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(output, {"ppt/slides/slide1.xml": _text_slide_xml("42 units")})
    report["binding_evidence"] = [
        _text_binding_evidence(
            "42 units",
            fact_refs=["fixture-fact"],
            fit_policy="no-autofit",
        )
    ]
    report["lineage_records"][0]["binding_count"] = 1
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "BINDING_FIT_POLICY_MISMATCH" in codes


def test_shrink_to_fit_evidence_is_recomputed_from_output_xml(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(output, {"ppt/slides/slide1.xml": _text_slide_xml("42 units")})
    report["binding_evidence"] = [
        _text_binding_evidence(
            "42 units",
            fact_refs=["fixture-fact"],
            fit_policy="shrink-to-fit",
        )
    ]
    report["lineage_records"][0]["binding_count"] = 1
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "BINDING_FIT_POLICY_MISMATCH" in codes


def test_connective_binding_hash_must_match_registered_connective_text(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    connective = {
        "schema_version": "1.0",
        "entries": [{"id": "approved-label", "text": "Approved"}],
    }
    _replace_authority_payload(report, "connective_copy", connective)
    _rewrite_deck(output, {"ppt/slides/slide1.xml": _text_slide_xml("Unapproved")})
    report["binding_evidence"] = [
        _text_binding_evidence("Unapproved", connective_ref="approved-label")
    ]
    report["lineage_records"][0]["binding_count"] = 1
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "BINDING_VALUE_NOT_CONNECTIVE_AUTHORIZED" in codes


def test_asset_binding_hash_must_be_authorized_by_manifest(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    report["binding_evidence"] = [
        {
            **_text_binding_evidence(""),
            "binding_kind": "asset",
            "mode": "cover",
            "fact_refs": [],
            "asset_refs": ["unregistered-asset"],
            "connective_ref": "",
            "relationship_id": "rImage",
            "target_part": "ppt/media/image.png",
            "replacement_sha256": "1" * 64,
            "capacity": {
                "chars": {"used": 0, "limit": 0},
                "items": {"used": 0, "limit": 0},
                "images": {"used": 1, "limit": 1},
            },
        }
    ]
    report["lineage_records"][0]["binding_count"] = 1
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "AUTHORITY_ASSET_REF_UNKNOWN" in codes


@pytest.mark.parametrize(
    ("updates", "remove", "expected_code"),
    [
        ({}, {"[Content_Types].xml"}, "OPC_CONTENT_TYPES_MISSING"),
        (
            {"[Content_Types].xml": b"<Types"},
            set(),
            "OPC_CONTENT_TYPES_MALFORMED",
        ),
        (
            {
                "[Content_Types].xml": (
                    f'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                    '<Default Extension="xml" ContentType="application/xml"/>'
                    '<Override PartName="/ppt/presentation.xml" '
                    'ContentType="application/vnd.ms-powerpoint.presentation.macroEnabled.main+xml"/>'
                    '<Override PartName="/ppt/slides/slide1.xml" '
                    'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
                    '</Types>'
                ).encode()
            },
            set(),
            "OPC_PRESENTATION_CONTENT_TYPE_INVALID",
        ),
    ],
    ids=("missing", "malformed", "macro-enabled-presentation"),
)
def test_content_types_are_independently_required_and_revalidated(
    tmp_path: Path,
    updates: dict[str, bytes],
    remove: set[str],
    expected_code: str,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(output, updates, remove=remove)
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert expected_code in codes


def test_unreachable_arbitrary_part_is_rejected_even_when_report_hash_is_refreshed(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(output, {"ppt/customXml/secret.xml": b"<secret>hidden</secret>"})
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "OPC_PART_NOT_ROOT_REACHABLE" in codes


def test_native_editability_is_recomputed_from_slide_xml(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(
        output,
        {
            "ppt/slides/slide1.xml": (
                '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                '<p:cSld/></p:sld>'
            ).encode()
        },
    )
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "EDITABILITY_EMPTY_SLIDE" in codes
    assert "EDITABILITY_ACTUAL_NATIVE_SLIDE_COUNT_MISMATCH" in codes


def test_swapped_media_cannot_be_authorized_by_refreshing_report_and_evidence_hashes(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    assets = project / "assets"
    assets.mkdir()
    approved = b"\x89PNG\r\n\x1a\nAPPROVED"
    swapped = b"\x89PNG\r\n\x1a\nSWAPPED"
    approved_path = assets / "approved.png"
    approved_path.write_bytes(approved)
    approved_sha = hashlib.sha256(approved).hexdigest()
    manifest = {
        "schema_version": "1.0",
        "bindings": {
            "approved-image": {
                "path": "assets/approved.png",
                "sha256": approved_sha,
                "record": {
                    "id": "approved-image",
                    "kind": "image",
                    "quality": 1,
                    "source": "fixture",
                    "license": "fixture",
                    "retrieved_at": "2026-08-09T00:00:00Z",
                    "width_px": 1,
                    "height_px": 1,
                },
            }
        },
    }
    _replace_authority_payload(report, "asset_manifest", manifest)
    with zipfile.ZipFile(output) as archive:
        content_types = archive.read("[Content_Types].xml")
    content_types = content_types.replace(
        b"</Types>",
        b'<Default Extension="png" ContentType="image/png"/></Types>',
    )
    _rewrite_deck(
        output,
        {
            "[Content_Types].xml": content_types,
            "ppt/slides/slide1.xml": _picture_slide_xml(),
            "ppt/slides/_rels/slide1.xml.rels": (
                f'<Relationships xmlns="{PACKAGE_RELATIONSHIP_NS}">'
                f'<Relationship Id="rImage" Type="{OFFICE_RELATIONSHIP_NS}/image" '
                'Target="../media/image.png"/></Relationships>'
            ).encode(),
            "ppt/media/image.png": swapped,
        },
    )
    swapped_sha = hashlib.sha256(swapped).hexdigest()
    report["binding_evidence"] = [
        {
            **_text_binding_evidence(""),
            "binding_kind": "asset",
            "mode": "cover",
            "asset_refs": ["approved-image"],
            "connective_ref": "",
            "relationship_id": "rImage",
            "target_part": "ppt/media/image.png",
            "replacement_sha256": swapped_sha,
            "capacity": {
                "chars": {"used": 0, "limit": 0},
                "items": {"used": 0, "limit": 0},
                "images": {"used": 1, "limit": 1},
            },
        }
    ]
    report["lineage_records"][0]["binding_count"] = 1
    report["editability"]["native_editable_slide_count"] = 0
    report["editability"]["native_editable_coverage"] = 0
    report["editability"]["native_object_count"] = 0
    report["editability"]["picture_count"] = 1
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "AUTHORITY_ASSET_SHA256_MISMATCH" in codes


def test_governed_peer_equality_and_cardinality_are_recomputed_from_output(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    facts = _minimal_fact_store()
    facts["facts"][0]["allowed_renderings"].append("99")
    _replace_authority_payload(report, "fact_store", facts)
    _rewrite_deck(output, {"ppt/slides/slide1.xml": _table_slide_xml("42", "99")})
    locators = [
        "graphicFrame[id=2]/table[1]/row[1]/cell[1]",
        "graphicFrame[id=2]/table[1]/row[1]/cell[2]",
    ]
    values = ["42", "99"]
    with zipfile.ZipFile(output) as archive:
        slide_part_sha256 = hashlib.sha256(
            archive.read("ppt/slides/slide1.xml")
        ).hexdigest()
    report["binding_evidence"] = [
        _embedded_binding_evidence(f"slot-{index}", value)
        for index, value in enumerate(values, start=1)
    ]
    report["lineage_records"][0]["binding_count"] = 2
    mutations = [
        {
            "ordinal": 1,
            "page_id": f"{'a' * 64}:001",
            "slot_id": f"slot-{index}",
            "kind": "table-cell",
            "source_part": "ppt/slides/slide1.xml",
            "slide_part": "ppt/slides/slide1.xml",
            "shape_id": 2,
            "slide_relationship_id": "",
            "chart_part": "",
            "chart_relationship_id": "",
            "target_part": "ppt/slides/slide1.xml",
            "target_part_sha256": slide_part_sha256,
            "locator": locator,
            "actual_sha256": hashlib.sha256(value.encode()).hexdigest(),
            "peer_group_id": "peer-one",
        }
        for index, (locator, value) in enumerate(zip(locators, values), start=1)
    ]
    report["source_residue"].update(
        {
            "governed_content_slot_count": 2,
            "governed_content_binding_count": 2,
            "verified_governed_content_count": 2,
            "governed_mutations": mutations,
            "mutation_manifest_sha256": hashlib.sha256(
                json.dumps(
                    mutations,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest(),
        }
    )
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "GOVERNED_PEER_GROUP_ACTUAL_MISMATCH" in codes


def test_governed_workbook_target_must_follow_actual_chart_relationship_chain(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    expected_workbook = _xlsx_with_value("42")
    redirected_workbook = _xlsx_with_value("99")
    with zipfile.ZipFile(output) as archive:
        content_types = archive.read("[Content_Types].xml")
    content_types = content_types.replace(
        b"</Types>",
        (
            b'<Default Extension="xlsx" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/>'
            b'<Override PartName="/ppt/charts/chart1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>'
            b'<Override PartName="/ppt/charts/chart2.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>'
            b"</Types>"
        ),
    )
    _rewrite_deck(
        output,
        {
            "[Content_Types].xml": content_types,
            "ppt/slides/slide1.xml": _chart_slide_xml(),
            "ppt/slides/_rels/slide1.xml.rels": (
                f'<Relationships xmlns="{PACKAGE_RELATIONSHIP_NS}">'
                f'<Relationship Id="rChart" Type="{OFFICE_RELATIONSHIP_NS}/chart" '
                'Target="../charts/chart1.xml"/>'
                f'<Relationship Id="rUnusedChart" Type="{OFFICE_RELATIONSHIP_NS}/chart" '
                'Target="../charts/chart2.xml"/></Relationships>'
            ).encode(),
            "ppt/charts/chart1.xml": _chart_xml("rPackage"),
            "ppt/charts/_rels/chart1.xml.rels": (
                f'<Relationships xmlns="{PACKAGE_RELATIONSHIP_NS}">'
                f'<Relationship Id="rPackage" Type="{OFFICE_RELATIONSHIP_NS}/package" '
                'Target="../embeddings/redirected.xlsx"/></Relationships>'
            ).encode(),
            "ppt/charts/chart2.xml": _chart_xml("rPackage"),
            "ppt/charts/_rels/chart2.xml.rels": (
                f'<Relationships xmlns="{PACKAGE_RELATIONSHIP_NS}">'
                f'<Relationship Id="rPackage" Type="{OFFICE_RELATIONSHIP_NS}/package" '
                'Target="../embeddings/expected.xlsx"/></Relationships>'
            ).encode(),
            "ppt/embeddings/expected.xlsx": expected_workbook,
            "ppt/embeddings/redirected.xlsx": redirected_workbook,
        },
    )
    replacement = "42"
    report["binding_evidence"] = [
        {
            **_embedded_binding_evidence("workbook-slot", replacement),
            "shape_id": 2,
        }
    ]
    report["lineage_records"][0]["binding_count"] = 1
    mutation = {
        "ordinal": 1,
        "page_id": f"{'a' * 64}:001",
        "slot_id": "workbook-slot",
        "kind": "workbook-cell",
        "source_part": "ppt/embeddings/expected.xlsx",
        "slide_part": "ppt/slides/slide1.xml",
        "shape_id": 2,
        "slide_relationship_id": "rUnusedChart",
        "chart_part": "ppt/charts/chart2.xml",
        "chart_relationship_id": "rPackage",
        "target_part": "ppt/embeddings/expected.xlsx",
        "target_part_sha256": hashlib.sha256(expected_workbook).hexdigest(),
        "locator": "chartFrame[id=2]/xl/worksheets/sheet1.xml!A1",
        "actual_sha256": hashlib.sha256(replacement.encode()).hexdigest(),
        "peer_group_id": "",
    }
    report["source_residue"].update(
        {
            "governed_content_slot_count": 1,
            "governed_content_binding_count": 1,
            "verified_governed_content_count": 1,
            "governed_mutations": [mutation],
            "mutation_manifest_sha256": hashlib.sha256(
                json.dumps(
                    [mutation],
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest(),
        }
    )
    report["editability"].update(
        {
            "text_run_count": 0,
            "shape_count": 1,
            "native_object_count": 1,
            "picture_count": 0,
            "native_editable_slide_count": 1,
            "native_editable_coverage": 1,
        }
    )
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "GOVERNED_ACTUAL_TARGET_MISMATCH" in codes


def test_every_reachable_nested_workbook_is_security_audited(tmp_path: Path) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    with zipfile.ZipFile(output) as archive:
        content_types = archive.read("[Content_Types].xml")
    content_types = content_types.replace(
        b"</Types>",
        b'<Default Extension="xlsx" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/></Types>',
    )
    _rewrite_deck(
        output,
        {
            "[Content_Types].xml": content_types,
            "ppt/slides/_rels/slide1.xml.rels": (
                f'<Relationships xmlns="{PACKAGE_RELATIONSHIP_NS}">'
                f'<Relationship Id="rWorkbook" Type="{OFFICE_RELATIONSHIP_NS}/package" '
                'Target="../embeddings/evil.xlsx"/></Relationships>'
            ).encode(),
            "ppt/embeddings/evil.xlsx": _xlsx_with_forbidden_vba("42"),
        },
    )
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "NESTED_WORKBOOK_SECURITY_FAILED" in codes


def test_duplicate_governed_evidence_and_mutation_keys_fail_closed(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project)
    output = project / "output.pptx"
    _rewrite_deck(output, {"ppt/slides/slide1.xml": _table_slide_xml("42", "42")})
    with zipfile.ZipFile(output) as archive:
        slide_sha = hashlib.sha256(
            archive.read("ppt/slides/slide1.xml")
        ).hexdigest()
    evidence = _embedded_binding_evidence("duplicate-slot", "42")
    mutation = {
        "ordinal": 1,
        "page_id": f"{'a' * 64}:001",
        "slot_id": "duplicate-slot",
        "kind": "table-cell",
        "source_part": "ppt/slides/slide1.xml",
        "slide_part": "ppt/slides/slide1.xml",
        "shape_id": 2,
        "slide_relationship_id": "",
        "chart_part": "",
        "chart_relationship_id": "",
        "target_part": "ppt/slides/slide1.xml",
        "target_part_sha256": slide_sha,
        "locator": "graphicFrame[id=2]/table[1]/row[1]/cell[1]",
        "actual_sha256": hashlib.sha256(b"42").hexdigest(),
        "peer_group_id": "",
    }
    mutations = [copy.deepcopy(mutation), copy.deepcopy(mutation)]
    report["binding_evidence"] = [copy.deepcopy(evidence), copy.deepcopy(evidence)]
    report["lineage_records"][0]["binding_count"] = 2
    report["source_residue"].update(
        {
            "governed_content_slot_count": 2,
            "governed_content_binding_count": 2,
            "verified_governed_content_count": 2,
            "governed_mutations": mutations,
            "mutation_manifest_sha256": hashlib.sha256(
                json.dumps(
                    mutations,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest(),
        }
    )
    _refresh_output_bindings(report, output)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "BINDING_EVIDENCE_KEY_DUPLICATE" in codes
    assert "GOVERNED_MUTATION_KEY_DUPLICATE" in codes
    assert "GOVERNED_MUTATION_LOCATOR_DUPLICATE" in codes


def test_phase49_inventory_identity_is_immutable_and_registered(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, report_path = _valid_report(project, slide_count=15, phase49=True)
    _write_report(report_path, report)

    result = validate_physical_report(report_path, project)
    codes = {issue["code"] for issue in result["issues"]}

    assert result["status"] == "fail"
    assert "PHASE49_LIBRARY_INDEX_SHA256_MISMATCH" in codes
    assert "PHASE49_GOVERNED_INVENTORY_SHA256_MISMATCH" in codes
    assert len(PHASE49_GOVERNED_INVENTORY_SHA256) == 64
    identity = {
        "ordinal": 5,
        "page_id": f"{'a' * 64}:005",
        "slot_id": "slot-one",
        "kind": "chart-value",
        "source_part": "ppt/charts/chart1.xml",
        "locator": "graphicFrame[id=2]/chartSpace[1]",
        "peer_group_id": "peer-one",
    }
    changed = {**identity, "kind": "workbook-cell"}
    assert _governed_inventory_identity_sha256([identity]) != (
        _governed_inventory_identity_sha256([changed])
    )


def test_mutation_schema_enforces_kind_specific_lineage_and_chart_text(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, _ = _valid_report(project)
    base = {
        "ordinal": 1,
        "page_id": f"{'a' * 64}:001",
        "slot_id": "slot-one",
        "kind": "chart-text",
        "source_part": "ppt/charts/chart1.xml",
        "slide_part": "ppt/slides/slide1.xml",
        "shape_id": 2,
        "slide_relationship_id": "rChart",
        "chart_part": "ppt/charts/chart1.xml",
        "chart_relationship_id": "",
        "target_part": "ppt/charts/chart1.xml",
        "target_part_sha256": "a" * 64,
        "locator": "graphicFrame[id=2]/chartSpace[1]/chart[1]/title[1]",
        "actual_sha256": "b" * 64,
        "peer_group_id": "",
    }
    report["source_residue"]["governed_mutations"] = [base]
    assert not _schema_errors(report)

    contradictory = copy.deepcopy(base)
    contradictory.update(
        {
            "kind": "table-cell",
            "source_part": "ppt/slides/slide1.xml",
            "slide_relationship_id": "rChart",
        }
    )
    report["source_residue"]["governed_mutations"] = [contradictory]
    assert _schema_errors(report)


def test_mutation_schema_accepts_only_canonical_importer_namespaced_targets(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report, _ = _valid_report(project)
    namespace = "v61_59b104d31bf3"
    chart_mutation = {
        "ordinal": 1,
        "page_id": f"{'a' * 64}:001",
        "slot_id": "chart-slot",
        "kind": "chart-value",
        "source_part": "ppt/charts/chart1.xml",
        "slide_part": "ppt/slides/slide1.xml",
        "shape_id": 2,
        "slide_relationship_id": "rChart",
        "chart_part": "ppt/charts/chart1.xml",
        "chart_relationship_id": "",
        "target_part": "ppt/charts/chart1.xml",
        "target_part_sha256": "a" * 64,
        "locator": "graphicFrame[id=2]/chartSpace[1]/chart[1]/value[1]",
        "actual_sha256": "b" * 64,
        "peer_group_id": "",
    }
    workbook_mutation = {
        **chart_mutation,
        "slot_id": "workbook-slot",
        "kind": "workbook-cell",
        "source_part": "ppt/embeddings/Microsoft_Excel_Worksheet.xlsx",
        "chart_part": "ppt/charts/chart1.xml",
        "chart_relationship_id": "rWorkbook",
        "target_part": "ppt/embeddings/Microsoft_Excel_Worksheet.xlsx",
        "locator": "xl/worksheets/sheet1.xml/A1",
    }

    for mutation in (chart_mutation, workbook_mutation):
        report["source_residue"]["governed_mutations"] = [mutation]
        assert not _schema_errors(report)

    namespaced_chart = copy.deepcopy(chart_mutation)
    namespaced_chart["chart_part"] = (
        f"ppt/{namespace}/charts/chart1_slide_005.xml"
    )
    namespaced_chart["target_part"] = namespaced_chart["chart_part"]
    report["source_residue"]["governed_mutations"] = [namespaced_chart]
    assert not _schema_errors(report)

    namespaced_workbook = copy.deepcopy(workbook_mutation)
    namespaced_workbook["chart_part"] = (
        f"ppt/{namespace}/charts/chart1_slide_005.xml"
    )
    namespaced_workbook["target_part"] = (
        f"ppt/{namespace}/embeddings/Microsoft_Excel_Worksheet_slide_005.xlsx"
    )
    report["source_residue"]["governed_mutations"] = [namespaced_workbook]
    assert not _schema_errors(report)

    invalid_targets = (
        (namespaced_chart, "chart_part", f"ppt/{namespace}/charts/nested/chart1.xml"),
        (namespaced_chart, "target_part", f"ppt/{namespace}/charts/../chart1.xml"),
        (namespaced_chart, "chart_part", f"ppt/{namespace}/charts\\chart1.xml"),
        (namespaced_chart, "target_part", "ppt/v61_59b104d31bf/charts/chart1.xml"),
        (namespaced_chart, "target_part", "ppt/v61_59B104D31BF3/charts/chart1.xml"),
        (namespaced_chart, "target_part", "ppt/v61_59b104d31bfg/charts/chart1.xml"),
        (
            namespaced_workbook,
            "target_part",
            f"ppt/{namespace}/embeddings/nested/workbook.xlsx",
        ),
        (
            namespaced_workbook,
            "target_part",
            f"ppt/{namespace}/embeddings/../workbook.xlsx",
        ),
    )
    for valid_mutation, field, invalid_path in invalid_targets:
        invalid_mutation = copy.deepcopy(valid_mutation)
        invalid_mutation[field] = invalid_path
        report["source_residue"]["governed_mutations"] = [invalid_mutation]
        assert _schema_errors(report), f"{field} unexpectedly accepted {invalid_path}"
