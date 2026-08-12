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

from .curation import ACTIVE_GAOJIE_CATEGORIES


class CatalogError(ValueError):
    """Raised when catalog evidence is incomplete or unsafe."""


_SLIDE_RE = re.compile(r"^ppt/slides/slide([1-9][0-9]*)\.xml$")
_EMU_PER_SLIDE_WIDTH = 12192000
_EMU_PER_SLIDE_HEIGHT = 6858000
_SRGB_RE = re.compile(r'(?:val|lastClr)="([A-Fa-f0-9]{6})"')


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise CatalogError("SLIDE_XML_INVALID") from exc
    tree = _child(root, "spTree")
    if tree is None:
        raise CatalogError("SLIDE_SHAPETREE_MISSING")
    shapes: list[dict[str, Any]] = []
    for order, node in enumerate(list(tree), start=1):
        record = _shape_record(node, width=width, height=height, order=order)
        if record is not None:
            shapes.append(record)
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


def _materialization_record(archive: zipfile.ZipFile, *, slide_number: int) -> dict[str, Any]:
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
    return {
        "status": "eligible" if complete else "blocked",
        "governed_content_slot_count": len(slots),
        "blocker_codes": sorted(set(errors)),
    }


def compile_catalog(
    source_root: Path | str,
    *,
    render_index: Mapping[str, Mapping[str, Any]],
    active_categories: Sequence[str] = ACTIVE_GAOJIE_CATEGORIES,
) -> dict[str, Any]:
    """Compile exactly the declared active source scope, with no file discovery later."""

    root = _safe_source_root(source_root, active_categories)
    decks: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    for category in active_categories:
        for path in sorted((root / category).rglob("*.pptx"), key=lambda item: item.as_posix()):
            if path.is_symlink() or not path.is_file():
                raise CatalogError("SOURCE_PATH_INVALID")
            package_sha = _sha256_file(path)
            try:
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
                        shapes, palette = _slide_record(
                            archive.read(name), width=width, height=height,
                        )
                        text_shapes = [shape for shape in shapes if shape["kind"] == "text" and shape["text"]]
                        editability = "native_editable" if text_shapes else "image_only"
                        pages.append({
                            "page_id": f"page_{package_sha[:24]}_{slide_number:03d}",
                            "deck_id": deck_id,
                            "package_sha256": package_sha,
                            "slide_number": slide_number,
                            "category": category,
                            "render": _render_record(render_index, package_sha, slide_number),
                            "style": {"palette": list(palette), "tone": "unknown"},
                            "editability": editability,
                            "component_eligible": bool(text_shapes),
                            "materialization": _materialization_record(
                                archive, slide_number=slide_number,
                            ),
                            "shapes": shapes,
                        })
            except zipfile.BadZipFile as exc:
                raise CatalogError("PPTX_INVALID") from exc
    pages.sort(key=lambda item: item["page_id"])
    decks.sort(key=lambda item: item["deck_id"])
    if len({item["page_id"] for item in pages}) != len(pages):
        raise CatalogError("PAGE_ID_DUPLICATE")
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
        "category_index": dict(sorted(Counter(item["category"] for item in pages).items())),
        "decks": decks,
        "pages": pages,
        "region_count": len(regions),
        "regions": regions,
    }


def serialize_catalog(catalog: Mapping[str, Any]) -> str:
    """Serialize deterministically for digesting and repeated-query evidence."""

    return json.dumps(catalog, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
