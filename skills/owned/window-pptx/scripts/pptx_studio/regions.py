"""Conservative reusable region extraction from catalogued native text shapes."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping


def _region_id(page_id: str, kind: str, shape_ids: list[str]) -> str:
    digest = hashlib.sha256(f"{page_id}|{kind}|{'|'.join(shape_ids)}".encode("utf-8")).hexdigest()[:20]
    return f"region_{digest}"


def _capacity(shapes: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "max_text_chars": sum(max(0, int(shape.get("max_chars", 0))) for shape in shapes),
        "text_shape_count": len(shapes),
    }


def _record(page: Mapping[str, Any], kind: str, shapes: list[Mapping[str, Any]], hierarchy: str) -> dict[str, Any]:
    shape_ids = [str(shape["shape_id"]) for shape in shapes]
    x = min(int(shape["bbox"]["x"]) for shape in shapes)
    y = min(int(shape["bbox"]["y"]) for shape in shapes)
    right = max(int(shape["bbox"]["x"]) + int(shape["bbox"]["w"]) for shape in shapes)
    bottom = max(int(shape["bbox"]["y"]) + int(shape["bbox"]["h"]) for shape in shapes)
    return {
        "region_id": _region_id(str(page["page_id"]), kind, shape_ids),
        "page_id": page["page_id"],
        "region_kind": kind,
        "hierarchy": hierarchy,
        "editable_shape_ids": shape_ids,
        "bbox": {"x": x, "y": y, "w": right - x, "h": bottom - y},
        "capacity": _capacity(shapes),
        "prohibited_adaptations": ["raw_geometry", "raw_style", "source_mutation"],
    }


def extract_regions(page: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return non-overlapping highest-value text regions, or none if unsafe."""

    if page.get("editability") != "native_editable" or page.get("component_eligible") is not True:
        return []
    text_shapes = [
        shape for shape in page.get("shapes", [])
        if isinstance(shape, Mapping)
        and shape.get("kind") == "text"
        and isinstance(shape.get("shape_id"), str)
        and isinstance(shape.get("text"), str)
        and shape["text"].strip()
        and isinstance(shape.get("bbox"), Mapping)
        and int(shape["bbox"].get("w", 0)) > 0
        and int(shape["bbox"].get("h", 0)) > 0
    ]
    if not text_shapes:
        return []
    text_shapes.sort(key=lambda shape: (int(shape["bbox"]["y"]), int(shape["bbox"]["x"]), str(shape["shape_id"])))
    title = text_shapes[0]
    records = [_record(page, "title", [title], "primary")]
    rest = text_shapes[1:]
    if rest:
        records.append(_record(page, "content-block", rest, "supporting"))
    return records
