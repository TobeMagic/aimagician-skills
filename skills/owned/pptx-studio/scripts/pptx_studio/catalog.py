"""Deterministic, private-only deck/page catalog compilation."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence
from xml.etree import ElementTree as ET

from .curation import ACTIVE_GAOJIE_CATEGORIES, COMPONENT_ONLY_GAOJIE_CATEGORIES


class CatalogError(ValueError):
    """Raised when catalog evidence is incomplete or unsafe."""


_SLIDE_RE = re.compile(r"^ppt/slides/slide([1-9][0-9]*)\.xml$")
_EMU_PER_SLIDE_WIDTH = 12192000
_EMU_PER_SLIDE_HEIGHT = 6858000
_SRGB_RE = re.compile(r'(?:val|lastClr)="([A-Fa-f0-9]{6})"')
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_CERTIFICATION_OVERLAY_SCHEMA = "pptx-studio-certification-overlay.v1"
_CERTIFICATION_DENY_BLOCKER = "visual-certification-denied"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def certification_evidence_sha256(value: Mapping[str, Any]) -> str:
    """Digest certification semantics independently of JSON whitespace."""

    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _certification_denials(
    evidence: Mapping[str, Any] | None,
) -> tuple[dict[tuple[str, int], dict[str, str]], dict[str, Any]]:
    """Validate the curated deny partition and return exact source identities.

    The commercial curation ledger uses a full package SHA plus a one-based
    slide number.  The public page ID is intentionally shorter, so compilation
    must never trust that truncated identifier by itself.
    """

    if evidence is None:
        return {}, {
            "schema_version": _CERTIFICATION_OVERLAY_SCHEMA,
            "status": "NOT_APPLIED",
            "source_schema_version": None,
            "source_sha256": None,
            "source_entry_count": 0,
            "denied_page_count": 0,
            "applied_denied_page_count": 0,
            "out_of_scope_denied_page_count": 0,
        }
    if evidence.get("schema_version") != "gaojie-certified-core.v2":
        raise CatalogError("CERTIFICATION_EVIDENCE_SCHEMA_INVALID")
    denied = evidence.get("denied_pages")
    declared_count = evidence.get("denied_page_count")
    if (
        not isinstance(denied, list)
        or type(declared_count) is not int
        or declared_count != len(denied)
    ):
        raise CatalogError("CERTIFICATION_EVIDENCE_INVALID")
    result: dict[tuple[str, int], dict[str, str]] = {}
    seen: set[tuple[str, int]] = set()
    for entry in denied:
        if not isinstance(entry, Mapping):
            raise CatalogError("CERTIFICATION_EVIDENCE_INVALID")
        package_sha = entry.get("package_sha256")
        slide_number = entry.get("slide_number")
        legacy_page_id = entry.get("page_id")
        visual_sha = entry.get("visual_sha256")
        reason_code = entry.get("reason_code")
        disposition = entry.get("visual_disposition")
        if (
            not isinstance(package_sha, str)
            or _SHA256_RE.fullmatch(package_sha) is None
            or type(slide_number) is not int
            or slide_number < 1
            or legacy_page_id != f"{package_sha}:{slide_number:03d}"
            or not isinstance(visual_sha, str)
            or _SHA256_RE.fullmatch(visual_sha) is None
            or not isinstance(reason_code, str)
            or not reason_code
            or disposition not in {"deny", "keep", "reroute"}
        ):
            raise CatalogError("CERTIFICATION_EVIDENCE_INVALID")
        key = (package_sha, slide_number)
        if key in seen:
            raise CatalogError("CERTIFICATION_EVIDENCE_DUPLICATE")
        seen.add(key)
        if disposition == "deny":
            result[key] = {
                "visual_sha256": visual_sha,
                "reason_code": reason_code,
            }
    return result, {
        "schema_version": _CERTIFICATION_OVERLAY_SCHEMA,
        "status": "PASS",
        "source_schema_version": str(evidence["schema_version"]),
        "source_sha256": certification_evidence_sha256(evidence),
        "source_entry_count": len(denied),
        "denied_page_count": len(result),
        # The active catalog intentionally excludes archived categories. These
        # two counts are finalized after source compilation.
        "applied_denied_page_count": 0,
        "out_of_scope_denied_page_count": 0,
    }


def _safe_source_root(value: Path | str, active_categories: Sequence[str]) -> Path:
    root = Path(value).expanduser().resolve(strict=False)
    if root.is_symlink() or not root.is_dir():
        raise CatalogError("SOURCE_ROOT_INVALID")
    found = {path.name for path in root.iterdir() if path.is_dir() and not path.is_symlink()}
    expected = set(active_categories)
    if found != expected:
        raise CatalogError("SOURCE_SCOPE_INVALID")
    return root


def _local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _child(node: ET.Element, name: str) -> ET.Element | None:
    return next((item for item in node.iter() if _local_name(item) == name), None)


def _int_attribute(element: ET.Element | None, key: str) -> int:
    if element is None:
        return 0
    try:
        return int(element.attrib.get(key, "0"))
    except ValueError:
        return 0


def _text(node: ET.Element) -> str:
    return "".join((item.text or "") for item in node.iter() if _local_name(item) == "t").strip()


def _slide_size(archive: zipfile.ZipFile) -> tuple[int, int]:
    try:
        root = ET.fromstring(archive.read("ppt/presentation.xml"))
    except (KeyError, ET.ParseError):
        return _EMU_PER_SLIDE_WIDTH, _EMU_PER_SLIDE_HEIGHT
    node = _child(root, "sldSz")
    width = _int_attribute(node, "cx") or _EMU_PER_SLIDE_WIDTH
    height = _int_attribute(node, "cy") or _EMU_PER_SLIDE_HEIGHT
    return width, height


def _bbox(node: ET.Element, *, width: int, height: int) -> dict[str, int]:
    transform = _child(node, "xfrm")
    offset = _child(transform, "off") if transform is not None else None
    extent = _child(transform, "ext") if transform is not None else None
    x, y = _int_attribute(offset, "x"), _int_attribute(offset, "y")
    w, h = _int_attribute(extent, "cx"), _int_attribute(extent, "cy")
    return {
        "x": max(0, min(1000, round(x * 1000 / width))),
        "y": max(0, min(1000, round(y * 1000 / height))),
        "w": max(0, min(1000, round(w * 1000 / width))),
        "h": max(0, min(1000, round(h * 1000 / height))),
    }


def _shape_record(node: ET.Element, *, width: int, height: int, order: int) -> dict[str, Any] | None:
    kind_by_xml = {"sp": "text", "pic": "image", "graphicFrame": "graphic", "grpSp": "group"}
    xml_kind = _local_name(node)
    kind = kind_by_xml.get(xml_kind)
    if kind is None:
        return None
    c_nv_pr = _child(node, "cNvPr")
    shape_id = str(_int_attribute(c_nv_pr, "id"))
    if shape_id == "0":
        return None
    value = _text(node) if kind in {"text", "group", "graphic"} else ""
    bbox = _bbox(node, width=width, height=height)
    # A model may not use arbitrary new geometry. The catalog is conservative:
    # a text region is only editable if it has a positive native rectangle.
    max_chars = max(0, int((bbox["w"] * bbox["h"]) / 180)) if value else 0
    return {
        "shape_id": shape_id,
        "name": str(c_nv_pr.attrib.get("name", "")) if c_nv_pr is not None else "",
        "kind": kind,
        "text": value,
        "bbox": bbox,
        "max_chars": max(max_chars, len(value)) if value else 0,
        "z_order": order,
    }


def _slide_record(
    payload: bytes,
    *,
    width: int,
    height: int,
) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    # The historical lightweight scanner only walked direct children of
    # ``p:spTree``. Commercial PPTX authors routinely put metric labels inside
    # nested ``p:grpSp`` diagrams; treating the group as a single shape made a
    # data page appear to have just one editable heading even though its labels
    # and values are ordinary native text. Reuse the physical importer's slot
    # discovery here so catalog capacity, preflight and actual replacement all
    # agree on the same recursive, shape-ID-addressable text surface.
    from window_pptx.page_template_library import PageTemplateError, _discover_slots

    try:
        slots = _discover_slots(
            payload.decode("utf-8", errors="strict"),
            slide_width=width,
            slide_height=height,
        )
    except (UnicodeDecodeError, PageTemplateError) as exc:
        raise CatalogError("SLIDE_XML_INVALID") from exc
    shapes = [
        {
            "shape_id": str(slot.shape_id),
            "name": "",
            "kind": "text",
            "text": slot.text,
            "bbox": dict(slot.bbox),
            "max_chars": slot.max_chars,
            "semantic_role": slot.semantic_role,
            "z_order": slot.reading_order,
        }
        for slot in slots
    ]
    palette = tuple(sorted(set(f"#{item.upper()}" for item in _SRGB_RE.findall(payload.decode("utf-8", errors="ignore")))))
    return shapes, palette[:6]


def _render_record(render_index: Mapping[str, Mapping[str, Any]], package_sha: str, slide_number: int) -> dict[str, Any]:
    key = f"{package_sha}:{slide_number:03d}"
    value = render_index.get(key)
    if not isinstance(value, Mapping):
        raise CatalogError("RENDER_EVIDENCE_MISSING")
    image_sha = value.get("image_sha256")
    if not isinstance(image_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", image_sha):
        raise CatalogError("RENDER_EVIDENCE_INVALID")
    width, height = value.get("width"), value.get("height")
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise CatalogError("RENDER_EVIDENCE_INVALID")
    quality = value.get("visual_quality", 0.0)
    if not isinstance(quality, (int, float)) or not 0 <= float(quality) <= 1:
        raise CatalogError("RENDER_EVIDENCE_INVALID")
    return {"image_sha256": image_sha, "width": width, "height": height, "visual_quality": round(float(quality), 8)}


def _materialization_record(
    archive: zipfile.ZipFile,
    *,
    slide_number: int,
    dependency_bytes: int | None,
    fragment_slot_count: int,
    visual_text_unit_count: int,
    dependency_blocker: str | None = None,
) -> dict[str, Any]:
    """Publish whether a page can be physically assembled without source residue.

    A native chart is not automatically safe to reuse.  The physical assembler
    must either be able to enumerate and govern every chart/table/workbook
    value or reject the page; otherwise a new client deck could retain stale
    commercial sample data.  Compute that fact while compiling the private
    catalog, rather than making an agent discover it after it has committed a
    whole narrative to a page choice.  Deliberately expose only count and
    stable error codes -- never source content or paths.
    """

    # The conservative content scanner is shared with the stable physical
    # importer.  Keeping one implementation avoids a catalog claiming a page
    # is safe which the assembler later refuses for a different interpretation
    # of chart/workbook closure.
    from window_pptx.page_template_library import _compile_governed_content_inventory

    inventory = _compile_governed_content_inventory(archive, slide_number)
    errors = inventory.get("scan_errors", [])
    if not isinstance(errors, list) or any(not isinstance(item, str) for item in errors):
        raise CatalogError("MATERIALIZATION_INVENTORY_INVALID")
    complete = inventory.get("complete") is True
    slots = inventory.get("slots", [])
    if not isinstance(slots, list):
        raise CatalogError("MATERIALIZATION_INVENTORY_INVALID")
    if dependency_bytes is not None and (type(dependency_bytes) is not int or dependency_bytes < 1):
        raise CatalogError("MATERIALIZATION_DEPENDENCY_SIZE_INVALID")
    if dependency_blocker is not None and dependency_blocker != "dependency-closure-unsafe":
        raise CatalogError("MATERIALIZATION_DEPENDENCY_BLOCKER_INVALID")
    if type(fragment_slot_count) is not int or fragment_slot_count < 0:
        raise CatalogError("MATERIALIZATION_FRAGMENT_PROFILE_INVALID")
    if type(visual_text_unit_count) is not int or visual_text_unit_count < 0:
        raise CatalogError("MATERIALIZATION_VISUAL_SKELETON_INVALID")
    blocker_codes = sorted(set(errors) | ({dependency_blocker} if dependency_blocker else set()))
    return {
        "status": "eligible" if complete and dependency_blocker is None else "blocked",
        "governed_content_slot_count": len(slots),
        "blocker_codes": blocker_codes,
        # This is a private-library planning signal, not a delivery-file
        # promise. It counts the source slide's recursive OPC closure before
        # cross-page byte deduplication, so a bounded planner can avoid
        # needlessly importing several photographic masters for a short deck.
        # The final physical size gate remains authoritative.
        "dependency_bytes": dependency_bytes or 0,
        # Fragment slots accept exactly one source character. They are often
        # visual ornaments (outlined numerals, letter-spacing effects) rather
        # than a client-fact surface. The planner consumes this count for
        # grammars such as business models where treating several of them as
        # mandatory metrics would coerce semantic fragmentation.
        "fragment_slot_count": fragment_slot_count,
        # A value-free count of native visible text units.  It is not the
        # number of facts a client must provide; it prevents a three-item
        # narrative from selecting a dense editorial/dashboard skeleton whose
        # many visible units would otherwise render as conspicuous blanks.
        "visual_text_unit_count": visual_text_unit_count,
    }


def compile_catalog(
    source_root: Path | str,
    *,
    render_index: Mapping[str, Mapping[str, Any]],
    certification_evidence: Mapping[str, Any] | None = None,
    active_categories: Sequence[str] = ACTIVE_GAOJIE_CATEGORIES,
) -> dict[str, Any]:
    """Compile exactly the declared active source scope, with no file discovery later."""

    root = _safe_source_root(source_root, active_categories)
    certification_denials, certification_overlay = _certification_denials(
        certification_evidence,
    )
    applied_denials: set[tuple[str, int]] = set()
    decks: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    for category in active_categories:
        for path in sorted((root / category).rglob("*.pptx"), key=lambda item: item.as_posix()):
            if path.is_symlink() or not path.is_file():
                raise CatalogError("SOURCE_PATH_INVALID")
            package_sha = _sha256_file(path)
            source_context = None
            try:
                # Reuse the production importer’s exact dependency traversal
                # rather than estimating a slide from package byte size. A
                # multi-page 25 MB deck can still contain a 200 KB reusable
                # component page, while a one-page deck can carry a large
                # photographic master. This maintenance-time metadata lets
                # the agent select for visual quality *and* delivery cost
                # without inspecting private files at client runtime.
                from window_pptx.physical_assembly import (
                    _SourcePackageContext,
                    _build_source_graph_from_context,
                )

                try:
                    source_context = _SourcePackageContext.open(path, package_sha)
                except (KeyError, zipfile.BadZipFile):
                    # Minimal catalog fixtures predating physical import do
                    # not contain an OPC content-type table. They cannot
                    # certify a real import closure, but remain useful for
                    # deterministic metadata tests; estimate only their
                    # slide XML rather than weakening the production importer.
                    source_context = None
                with zipfile.ZipFile(path) as archive:
                    width, height = _slide_size(archive)
                    slide_names = sorted(
                        (name for name in archive.namelist() if _SLIDE_RE.fullmatch(name)),
                        key=lambda name: int(_SLIDE_RE.fullmatch(name).group(1)),
                    )
                    if not slide_names:
                        raise CatalogError("PPTX_SLIDES_MISSING")
                    deck_id = f"deck_{package_sha[:24]}"
                    decks.append({
                        "deck_id": deck_id,
                        "package_sha256": package_sha,
                        "category": category,
                        "page_count": len(slide_names),
                    })
                    for name in slide_names:
                        slide_number = int(_SLIDE_RE.fullmatch(name).group(1))
                        dependency_blocker = None
                        if source_context is None:
                            dependency_bytes = len(archive.read(name))
                        else:
                            try:
                                graph = _build_source_graph_from_context(
                                    source_context, slide_number,
                                )
                                dependency_bytes = sum(
                                    len(payload)
                                    for payload in (
                                        graph.slide_xml,
                                        *graph.rels.values(),
                                        *graph.extra_parts.values(),
                                    )
                                )
                            except Exception as exc:
                                # The importer is the final authority on OPC
                                # safety. Do not leak an unsafe target or a
                                # private path into the catalog: record only
                                # that this page cannot be physically reused.
                                from window_pptx.physical_assembly import PhysicalAssemblyError

                                if not isinstance(exc, PhysicalAssemblyError):
                                    raise
                                dependency_bytes = None
                                dependency_blocker = "dependency-closure-unsafe"
                        shapes, palette = _slide_record(
                            archive.read(name), width=width, height=height,
                        )
                        text_shapes = [shape for shape in shapes if shape["kind"] == "text" and shape["text"]]
                        editability = "native_editable" if text_shapes else "image_only"
                        render = _render_record(render_index, package_sha, slide_number)
                        materialization = _materialization_record(
                            archive,
                            slide_number=slide_number,
                            dependency_bytes=dependency_bytes,
                            fragment_slot_count=sum(
                                shape.get("semantic_role") in {"title_fragment", "label_fragment"}
                                for shape in shapes
                            ),
                            visual_text_unit_count=sum(
                                shape.get("semantic_role") not in {"title_fragment", "label_fragment"}
                                for shape in text_shapes
                            ),
                            dependency_blocker=dependency_blocker,
                        )
                        certification: dict[str, str] | None = None
                        denial_key = (package_sha, slide_number)
                        denial = certification_denials.get(denial_key)
                        if denial is not None:
                            if denial["visual_sha256"] != render["image_sha256"]:
                                raise CatalogError("CERTIFICATION_VISUAL_EVIDENCE_DRIFT")
                            applied_denials.add(denial_key)
                            materialization["status"] = "blocked"
                            materialization["blocker_codes"] = sorted(set(
                                [*materialization["blocker_codes"], _CERTIFICATION_DENY_BLOCKER]
                            ))
                            certification = {
                                "visual_disposition": "deny",
                                "reason_code": denial["reason_code"],
                                "visual_sha256": denial["visual_sha256"],
                            }
                        pages.append({
                            "page_id": f"page_{package_sha[:24]}_{slide_number:03d}",
                            "deck_id": deck_id,
                            "package_sha256": package_sha,
                            "slide_number": slide_number,
                            "category": category,
                            "component_only": category in COMPONENT_ONLY_GAOJIE_CATEGORIES,
                            "render": render,
                            "style": {"palette": list(palette), "tone": "unknown"},
                            "editability": editability,
                            "component_eligible": bool(text_shapes),
                            "materialization": materialization,
                            **({"certification": certification} if certification is not None else {}),
                            "shapes": shapes,
                        })
            except zipfile.BadZipFile as exc:
                raise CatalogError("PPTX_INVALID") from exc
            finally:
                if source_context is not None:
                    source_context.close()
    pages.sort(key=lambda item: item["page_id"])
    decks.sort(key=lambda item: item["deck_id"])
    if len({item["page_id"] for item in pages}) != len(pages):
        raise CatalogError("PAGE_ID_DUPLICATE")
    active_package_hashes = {str(item["package_sha256"]) for item in decks}
    unmatched_denials = set(certification_denials) - applied_denials
    if any(package_sha in active_package_hashes for package_sha, _ in unmatched_denials):
        raise CatalogError("CERTIFICATION_SOURCE_SCOPE_DRIFT")
    if certification_overlay["status"] == "PASS":
        certification_overlay["applied_denied_page_count"] = len(applied_denials)
        certification_overlay["out_of_scope_denied_page_count"] = len(unmatched_denials)
    # Import here to keep the compiler's OOXML parser independent while making
    # its returned object conform to the published catalog contract.
    from .regions import extract_regions

    regions = [region for page in pages for region in extract_regions(page)]
    return {
        "schema_version": "1.0",
        "catalog_id": "pptx-studio-gaojie-active-v1",
        "source_kind": "gaojie",
        "active_categories": list(active_categories),
        "deck_count": len(decks),
        "page_count": len(pages),
        "certification_overlay": certification_overlay,
        "category_index": dict(sorted(Counter(item["category"] for item in pages).items())),
        "decks": decks,
        "pages": pages,
        "region_count": len(regions),
        "regions": regions,
    }


def serialize_catalog(catalog: Mapping[str, Any]) -> str:
    """Serialize deterministically for digesting and repeated-query evidence."""

    return json.dumps(catalog, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
