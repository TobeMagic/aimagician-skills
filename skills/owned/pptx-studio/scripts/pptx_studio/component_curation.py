"""Operator-only compiler for hash-bound native PPTX component profiles.

The production agent only receives opaque component and host-anchor IDs.  This
module is deliberately on the other side of that boundary: a curator supplies
an explicitly reviewed page/shape closure declaration and this compiler reads
the authorized source package to calculate every physical fingerprint.  It
does not discover components, infer geometry, or make a visual decision.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping

from window_pptx.page_template_library import _discover_slots
from window_pptx.physical_assembly import (
    _COMPONENT_SHAPE_TAGS,
    _component_nodes_bbox,
    _component_nodes_sha256,
    _component_relationship_ids,
    _component_root_nodes,
    _shape_non_visual_ids,
    _slide_shape_tree,
)

from .component_profiles import catalog_sha256, component_profile_sha256
from .query import _SUITABILITY_PROFILES


class ComponentCurationError(ValueError):
    """A private component curation declaration is unsafe or incomplete."""


_REQUEST_VERSIONS = frozenset({
    "pptx-studio-component-curation-request.v1",
    "pptx-studio-component-curation-request.v2",
    "pptx-studio-component-curation-request.v3",
})
_REQUEST_FIELDS_V1 = frozenset({"schema_version", "profile_id", "components", "host_anchors"})
_REQUEST_FIELDS_V2 = _REQUEST_FIELDS_V1 | {"canvas_anchors"}
_REQUEST_FIELDS_V3 = _REQUEST_FIELDS_V2
_COMPONENT_FIELDS = frozenset({
    "component_key", "source_page_id", "shape_ids", "fields", "semantic_intent",
    "allowed_roles", "host_anchor_keys",
})
_COMPONENT_FIELDS_V3 = _COMPONENT_FIELDS | {"visual_certification"}
_FIELD_FIELDS = frozenset({"field_id", "shape_id", "semantic_role"})
_ANCHOR_FIELDS = frozenset({
    "anchor_key", "source_page_id", "shape_ids", "removable_shape_ids",
    "compatible_component_keys",
})
_CANVAS_ANCHOR_FIELDS = frozenset({
    "anchor_key", "host_page_id", "canvas_source_page_id", "canvas_shape_ids",
    "safe_underlay_shape_ids", "compatible_component_keys",
})
_SOURCE_FIELDS = frozenset({"page_id", "package_sha256", "slide_number", "slide_sha256"})
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMPONENT_ROLES = frozenset({"title", "label", "metric", "body"})
_STYLE_PROFILE_FIELDS = frozenset({"archetype", "tone", "color_family"})
_STYLE_ARCHETYPES = frozenset({
    "academic", "corporate", "editorial", "festive", "general",
    "infographic", "minimal", "technology",
})
_STYLE_TONES = frozenset({"light", "balanced", "dark"})
_STYLE_COLORS = frozenset({"cool", "green", "mixed", "neutral", "warm"})
_REVIEW_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _opaque_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def _positive_ids(value: Any, *, code: str) -> list[int]:
    if (
        not isinstance(value, list)
        or not value
        or any(type(item) is not int or item < 1 for item in value)
        or len(set(value)) != len(value)
    ):
        raise ComponentCurationError(code)
    return list(value)


def _string_list(value: Any, *, code: str) -> list[str]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
    ):
        raise ComponentCurationError(code)
    return list(value)


def _catalog_pages(catalog: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    pages = catalog.get("pages")
    if not isinstance(pages, list):
        raise ComponentCurationError("COMPONENT_CURATION_CATALOG_INVALID")
    result: dict[str, Mapping[str, Any]] = {}
    for page in pages:
        if not isinstance(page, Mapping) or not isinstance(page.get("page_id"), str):
            raise ComponentCurationError("COMPONENT_CURATION_CATALOG_INVALID")
        page_id = str(page["page_id"])
        if page_id in result:
            raise ComponentCurationError("COMPONENT_CURATION_CATALOG_INVALID")
        result[page_id] = page
    return result


def _asset_paths(
    asset_index: Mapping[str, Any], *, private_root: Path,
    private_source_root: Path | None,
) -> dict[str, Path]:
    packages = asset_index.get("packages")
    if not isinstance(packages, list):
        raise ComponentCurationError("COMPONENT_CURATION_ASSET_INDEX_INVALID")
    result: dict[str, Path] = {}
    root = private_root.resolve()
    for package in packages:
        if not isinstance(package, Mapping):
            continue
        digest, relative = package.get("package_sha256"), package.get("private_path")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None or not isinstance(relative, str):
            continue
        candidate = (root / relative).resolve()
        if root not in candidate.parents or not candidate.is_file():
            continue
        if digest in result and result[digest] != candidate:
            raise ComponentCurationError("COMPONENT_CURATION_ASSET_INDEX_AMBIGUOUS")
        result[digest] = candidate
    # The operator may retain a certified reference work in the declared
    # source tree even when it was intentionally omitted from an older asset
    # index snapshot. This recovery is curation-only: it is bounded to the
    # explicit private source root and never exists on the client runtime path.
    if private_source_root is not None:
        source_root = private_source_root.resolve()
        if not source_root.is_dir():
            raise ComponentCurationError("COMPONENT_CURATION_SOURCE_ROOT_UNAVAILABLE")
        for candidate in source_root.rglob("*.pptx"):
            resolved = candidate.resolve()
            if source_root not in resolved.parents:
                continue
            digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
            if digest in result and result[digest] != resolved:
                raise ComponentCurationError("COMPONENT_CURATION_ASSET_INDEX_AMBIGUOUS")
            result.setdefault(digest, resolved)
    return result


def _source_graph(
    page: Mapping[str, Any], *, asset_paths: Mapping[str, Path],
) -> tuple[dict[str, Any], ET.Element, tuple[Any, ...]]:
    package_sha = page.get("package_sha256")
    slide_number = page.get("slide_number")
    page_id = page.get("page_id")
    if not isinstance(package_sha, str) or type(slide_number) is not int or not isinstance(page_id, str):
        raise ComponentCurationError("COMPONENT_CURATION_CATALOG_INVALID")
    package_path = asset_paths.get(package_sha)
    if package_path is None:
        raise ComponentCurationError("COMPONENT_CURATION_SOURCE_UNAVAILABLE")
    if hashlib.sha256(package_path.read_bytes()).hexdigest() != package_sha:
        raise ComponentCurationError("COMPONENT_CURATION_PACKAGE_SHA_MISMATCH")
    slide_name = f"ppt/slides/slide{slide_number}.xml"
    try:
        with zipfile.ZipFile(package_path) as archive:
            slide_xml = archive.read(slide_name)
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise ComponentCurationError("COMPONENT_CURATION_SOURCE_UNAVAILABLE") from exc
    try:
        root = ET.fromstring(slide_xml)
    except ET.ParseError as exc:
        raise ComponentCurationError("COMPONENT_CURATION_SLIDE_XML_INVALID") from exc
    try:
        slots = tuple(_discover_slots(slide_xml.decode("utf-8", errors="strict")))
    except (UnicodeError, ValueError) as exc:
        raise ComponentCurationError("COMPONENT_CURATION_SLOT_DISCOVERY_FAILED") from exc
    source = {
        "page_id": page_id,
        "package_sha256": package_sha,
        "slide_number": slide_number,
        "slide_sha256": hashlib.sha256(slide_xml).hexdigest(),
    }
    assert set(source) == _SOURCE_FIELDS
    return source, root, slots


def _nodes_for(root: ET.Element, shape_ids: list[int], *, label: str) -> tuple[Any, ...]:
    try:
        return _component_root_nodes(root, shape_ids=shape_ids, label=label)
    except ValueError as exc:
        raise ComponentCurationError(f"COMPONENT_CURATION_{label}_CLOSURE_INVALID") from exc


def _request_mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ComponentCurationError("COMPONENT_CURATION_REQUEST_INVALID")
    version = value.get("schema_version")
    expected_fields = (
        _REQUEST_FIELDS_V3 if version == "pptx-studio-component-curation-request.v3"
        else _REQUEST_FIELDS_V2 if version == "pptx-studio-component-curation-request.v2"
        else _REQUEST_FIELDS_V1
    )
    if version not in _REQUEST_VERSIONS or set(value) != expected_fields:
        raise ComponentCurationError("COMPONENT_CURATION_REQUEST_INVALID")
    if not isinstance(value.get("profile_id"), str) or not str(value["profile_id"]).strip():
        raise ComponentCurationError("COMPONENT_CURATION_REQUEST_INVALID")
    return value


def _visual_certification(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {
        "review_id", "review_sha256", "style_profile", "suitability",
    }:
        raise ComponentCurationError("COMPONENT_CURATION_VISUAL_CERTIFICATION_INVALID")
    review_id, review_sha, profile, suitability = (
        value.get("review_id"), value.get("review_sha256"),
        value.get("style_profile"), value.get("suitability"),
    )
    if (
        not isinstance(review_id, str) or _REVIEW_ID_RE.fullmatch(review_id) is None
        or not isinstance(review_sha, str) or _SHA256_RE.fullmatch(review_sha) is None
        or not isinstance(profile, Mapping) or set(profile) != _STYLE_PROFILE_FIELDS
        or profile.get("archetype") not in _STYLE_ARCHETYPES
        or profile.get("tone") not in _STYLE_TONES
        or profile.get("color_family") not in _STYLE_COLORS
    ):
        raise ComponentCurationError("COMPONENT_CURATION_VISUAL_CERTIFICATION_INVALID")
    suitability_values = _string_list(
        suitability, code="COMPONENT_CURATION_VISUAL_CERTIFICATION_INVALID",
    )
    if any(item not in _SUITABILITY_PROFILES for item in suitability_values):
        raise ComponentCurationError("COMPONENT_CURATION_VISUAL_CERTIFICATION_INVALID")
    return {
        "review_id": review_id,
        "review_sha256": review_sha,
        "style_profile": {key: str(profile[key]) for key in sorted(_STYLE_PROFILE_FIELDS)},
        "suitability": suitability_values,
    }


def _bbox_tuple(nodes: tuple[Any, ...], *, code: str) -> tuple[int, int, int, int]:
    bbox = _component_nodes_bbox(nodes)
    if bbox is None:
        raise ComponentCurationError(code)
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        raise ComponentCurationError(code)
    return x0, y0, x1 - x0, y1 - y0


def _boxes_overlap(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> bool:
    return not (
        left[0] + left[2] <= right[0]
        or right[0] + right[2] <= left[0]
        or left[1] + left[3] <= right[1]
        or right[1] + right[3] <= left[1]
    )


def _validate_canvas_is_empty(
    host_root: ET.Element, *, canvas_bbox: tuple[int, int, int, int],
    safe_underlay_shape_ids: set[int],
) -> None:
    """Prove a fixed insertion zone is blank except for declared underlays."""

    for child in list(_slide_shape_tree(host_root)):
        if child.tag not in _COMPONENT_SHAPE_TAGS:
            continue
        shape_ids = set(_shape_non_visual_ids(child))
        if not shape_ids:
            continue
        if shape_ids.issubset(safe_underlay_shape_ids):
            continue
        bbox = _component_nodes_bbox((child,))
        if bbox is None:
            # Unknown geometry cannot be asserted not to overlap a canvas.
            raise ComponentCurationError("COMPONENT_CURATION_CANVAS_GEOMETRY_UNAVAILABLE")
        x0, y0, x1, y1 = bbox
        if _boxes_overlap(canvas_bbox, (x0, y0, x1 - x0, y1 - y0)):
            raise ComponentCurationError("COMPONENT_CURATION_CANVAS_NOT_EMPTY")


def compile_component_profile(
    *, catalog: Mapping[str, Any], asset_index: Mapping[str, Any], private_root: Path | str,
    request: Mapping[str, Any], private_source_root: Path | str | None = None,
) -> dict[str, Any]:
    """Compile a hash-bound component authority from explicit curation input.

    The input can name shape IDs because it is an operator-only source review
    artefact. All IDs, XML closures, text capacities, relationship references,
    package fingerprints and source-slide hashes in the output are derived
    from the certified source; callers cannot provide any of those values.
    """

    request = _request_mapping(request)
    pages = _catalog_pages(catalog)
    asset_paths = _asset_paths(
        asset_index, private_root=Path(private_root),
        private_source_root=Path(private_source_root) if private_source_root is not None else None,
    )
    raw_components = request.get("components")
    raw_anchors = request.get("host_anchors")
    raw_canvas_anchors = request.get("canvas_anchors", [])
    if (
        not isinstance(raw_components, list) or not raw_components
        or not isinstance(raw_anchors, list)
        or not isinstance(raw_canvas_anchors, list)
        or not raw_anchors and not raw_canvas_anchors
    ):
        raise ComponentCurationError("COMPONENT_CURATION_REQUEST_INVALID")

    source_cache: dict[str, tuple[dict[str, Any], ET.Element, tuple[Any, ...]]] = {}

    def source_for(page_id: Any) -> tuple[dict[str, Any], ET.Element, tuple[Any, ...]]:
        if not isinstance(page_id, str) or page_id not in pages:
            raise ComponentCurationError("COMPONENT_CURATION_PAGE_UNKNOWN")
        if page_id not in source_cache:
            source_cache[page_id] = _source_graph(pages[page_id], asset_paths=asset_paths)
        return source_cache[page_id]

    anchors_by_key: dict[str, dict[str, Any]] = {}
    anchor_nodes: dict[str, tuple[Any, ...]] = {}
    canvas_bboxes: dict[str, tuple[int, int, int, int]] = {}
    anchor_claims: dict[str, set[int]] = {}
    for raw in raw_anchors:
        if not isinstance(raw, Mapping) or set(raw) != _ANCHOR_FIELDS:
            raise ComponentCurationError("COMPONENT_CURATION_ANCHOR_INVALID")
        key = raw.get("anchor_key")
        if not isinstance(key, str) or not key or key in anchors_by_key:
            raise ComponentCurationError("COMPONENT_CURATION_ANCHOR_INVALID")
        source, root, _slots = source_for(raw.get("source_page_id"))
        shape_ids = _positive_ids(raw.get("shape_ids"), code="COMPONENT_CURATION_ANCHOR_INVALID")
        nodes = _nodes_for(root, shape_ids, label="HOST_ANCHOR")
        removable = raw.get("removable_shape_ids")
        if removable is None:
            removable_ids: list[int] = []
        elif isinstance(removable, list) and not removable:
            removable_ids = []
        else:
            removable_ids = _positive_ids(removable, code="COMPONENT_CURATION_ANCHOR_INVALID")
        if set(shape_ids).intersection(removable_ids):
            raise ComponentCurationError("COMPONENT_CURATION_ANCHOR_OVERLAP")
        _nodes_for(root, removable_ids, label="HOST_CLEANUP") if removable_ids else ()
        claimed = anchor_claims.setdefault(str(raw["source_page_id"]), set())
        # Host reservations must be disjoint. Cleanup declarations are a
        # separate, conditional fallback contract: several anchors may name
        # the same certified unused variant and the runtime deduplicates that
        # exact closure when it is actually selected.
        if claimed.intersection(shape_ids):
            raise ComponentCurationError("COMPONENT_CURATION_ANCHOR_OVERLAP")
        claimed.update(shape_ids)
        anchor_id = _opaque_id("anchor", str(request["profile_id"]), key, source["page_id"], ",".join(map(str, shape_ids)))
        anchors_by_key[key] = {
            "host_anchor_id": anchor_id,
            "source": source,
            "shape_ids": shape_ids,
            "host_anchor_sha256": _component_nodes_sha256(nodes),
            "compatible_component_ids": [],
            "removable_shape_ids": removable_ids,
            "removable_shape_sha256": _component_nodes_sha256(_nodes_for(root, removable_ids, label="HOST_CLEANUP")) if removable_ids else None,
            "_compatible_keys": _string_list(raw.get("compatible_component_keys"), code="COMPONENT_CURATION_ANCHOR_INVALID"),
        }
        anchor_nodes[key] = nodes

    for raw in raw_canvas_anchors:
        if not isinstance(raw, Mapping) or set(raw) != _CANVAS_ANCHOR_FIELDS:
            raise ComponentCurationError("COMPONENT_CURATION_CANVAS_ANCHOR_INVALID")
        key = raw.get("anchor_key")
        if not isinstance(key, str) or not key or key in anchors_by_key:
            raise ComponentCurationError("COMPONENT_CURATION_CANVAS_ANCHOR_INVALID")
        host_source, host_root, _host_slots = source_for(raw.get("host_page_id"))
        canvas_source, canvas_root, _canvas_slots = source_for(raw.get("canvas_source_page_id"))
        canvas_shape_ids = _positive_ids(
            raw.get("canvas_shape_ids"), code="COMPONENT_CURATION_CANVAS_ANCHOR_INVALID",
        )
        canvas_nodes = _nodes_for(canvas_root, canvas_shape_ids, label="CANVAS")
        canvas_bbox = _bbox_tuple(
            canvas_nodes, code="COMPONENT_CURATION_CANVAS_GEOMETRY_UNAVAILABLE",
        )
        safe_underlays = raw.get("safe_underlay_shape_ids")
        if safe_underlays is None:
            safe_underlay_ids: list[int] = []
        elif isinstance(safe_underlays, list) and not safe_underlays:
            safe_underlay_ids = []
        else:
            safe_underlay_ids = _positive_ids(
                safe_underlays, code="COMPONENT_CURATION_CANVAS_ANCHOR_INVALID",
            )
        if safe_underlay_ids:
            _nodes_for(host_root, safe_underlay_ids, label="CANVAS_UNDERLAY")
        _validate_canvas_is_empty(
            host_root, canvas_bbox=canvas_bbox,
            safe_underlay_shape_ids=set(safe_underlay_ids),
        )
        anchor_id = _opaque_id(
            "anchor", str(request["profile_id"]), key, host_source["page_id"],
            canvas_source["page_id"], ",".join(map(str, canvas_shape_ids)),
        )
        anchors_by_key[key] = {
            "host_anchor_id": anchor_id,
            "anchor_mode": "canvas",
            "source": host_source,
            "canvas_source": canvas_source,
            "canvas_shape_ids": canvas_shape_ids,
            "canvas_sha256": _component_nodes_sha256(canvas_nodes),
            "canvas_bbox": list(canvas_bbox),
            "compatible_component_ids": [],
            "_compatible_keys": _string_list(
                raw.get("compatible_component_keys"),
                code="COMPONENT_CURATION_CANVAS_ANCHOR_INVALID",
            ),
        }
        canvas_bboxes[key] = canvas_bbox

    components_by_key: dict[str, dict[str, Any]] = {}
    component_nodes: dict[str, tuple[Any, ...]] = {}
    for raw in raw_components:
        component_fields = (
            _COMPONENT_FIELDS_V3
            if request.get("schema_version") == "pptx-studio-component-curation-request.v3"
            else _COMPONENT_FIELDS
        )
        if not isinstance(raw, Mapping) or set(raw) != component_fields:
            raise ComponentCurationError("COMPONENT_CURATION_COMPONENT_INVALID")
        key = raw.get("component_key")
        if not isinstance(key, str) or not key or key in components_by_key:
            raise ComponentCurationError("COMPONENT_CURATION_COMPONENT_INVALID")
        source, root, slots = source_for(raw.get("source_page_id"))
        shape_ids = _positive_ids(raw.get("shape_ids"), code="COMPONENT_CURATION_COMPONENT_INVALID")
        nodes = _nodes_for(root, shape_ids, label="SOURCE")
        fields = raw.get("fields")
        if not isinstance(fields, list) or not fields:
            raise ComponentCurationError("COMPONENT_CURATION_COMPONENT_INVALID")
        slots_by_shape = {str(slot.slot_id): slot for slot in slots}
        output_fields: list[dict[str, Any]] = []
        field_ids: set[str] = set()
        field_shapes: set[int] = set()
        for field in fields:
            if not isinstance(field, Mapping) or set(field) != _FIELD_FIELDS:
                raise ComponentCurationError("COMPONENT_CURATION_FIELD_INVALID")
            field_id, shape_id, role = field.get("field_id"), field.get("shape_id"), field.get("semantic_role")
            if (
                not isinstance(field_id, str) or not field_id or field_id in field_ids
                or type(shape_id) is not int or shape_id not in shape_ids or shape_id in field_shapes
                or role not in _COMPONENT_ROLES
            ):
                raise ComponentCurationError("COMPONENT_CURATION_FIELD_INVALID")
            slot = slots_by_shape.get(f"shape_{shape_id}")
            if slot is None or type(slot.max_chars) is not int or slot.max_chars < 1:
                raise ComponentCurationError("COMPONENT_CURATION_FIELD_SLOT_INVALID")
            field_ids.add(field_id)
            field_shapes.add(shape_id)
            output_fields.append({"field_id": field_id, "shape_id": shape_id, "semantic_role": role, "max_chars": slot.max_chars})
        allowed_roles = _string_list(raw.get("allowed_roles"), code="COMPONENT_CURATION_COMPONENT_INVALID")
        anchor_keys = _string_list(raw.get("host_anchor_keys"), code="COMPONENT_CURATION_COMPONENT_INVALID")
        if any(anchor_key not in anchors_by_key for anchor_key in anchor_keys):
            raise ComponentCurationError("COMPONENT_CURATION_ANCHOR_UNKNOWN")
        if not isinstance(raw.get("semantic_intent"), str) or not str(raw["semantic_intent"]).strip():
            raise ComponentCurationError("COMPONENT_CURATION_COMPONENT_INVALID")
        component_id = _opaque_id("component", str(request["profile_id"]), key, source["page_id"], ",".join(map(str, shape_ids)))
        components_by_key[key] = {
            "component_id": component_id,
            "source": source,
            "shape_ids": shape_ids,
            "component_sha256": _component_nodes_sha256(nodes),
            "relationship_ids": list(_component_relationship_ids(nodes)),
            "semantic_intent": raw["semantic_intent"],
            "allowed_roles": allowed_roles,
            "fields": output_fields,
            "allowed_host_anchor_ids": [anchors_by_key[anchor_key]["host_anchor_id"] for anchor_key in anchor_keys],
            **({
                "visual_certification": _visual_certification(raw.get("visual_certification")),
            } if request.get("schema_version") == "pptx-studio-component-curation-request.v3" else {}),
        }
        component_nodes[key] = nodes

    for anchor_key, anchor in anchors_by_key.items():
        component_keys = anchor.pop("_compatible_keys")
        if any(key not in components_by_key for key in component_keys):
            raise ComponentCurationError("COMPONENT_CURATION_COMPONENT_UNKNOWN")
        for component_key in component_keys:
            component = components_by_key[component_key]
            if anchor["host_anchor_id"] not in component["allowed_host_anchor_ids"]:
                raise ComponentCurationError("COMPONENT_CURATION_COMPATIBILITY_ASYMMETRIC")
            component_bbox = _bbox_tuple(
                component_nodes[component_key],
                code="COMPONENT_CURATION_ANCHOR_BOUNDS_MISMATCH",
            )
            anchor_bbox = (
                canvas_bboxes[anchor_key]
                if anchor_key in canvas_bboxes
                else _bbox_tuple(
                    anchor_nodes[anchor_key],
                    code="COMPONENT_CURATION_ANCHOR_BOUNDS_MISMATCH",
                )
            )
            if component_bbox[2:] != anchor_bbox[2:]:
                raise ComponentCurationError("COMPONENT_CURATION_ANCHOR_BOUNDS_MISMATCH")
        anchor["compatible_component_ids"] = [components_by_key[key]["component_id"] for key in component_keys]

    profile: dict[str, Any] = {
        "schema_version": (
            "pptx-studio-component-profile.v4"
            if request.get("schema_version") == "pptx-studio-component-curation-request.v3"
            else "pptx-studio-component-profile.v3"
            if raw_canvas_anchors else "pptx-studio-component-profile.v2"
        ),
        "status": "COMPLETE",
        "profile_id": request["profile_id"],
        "profile_sha256": "",
        "catalog_sha256": catalog_sha256(catalog),
        "components": list(components_by_key.values()),
        "host_anchors": list(anchors_by_key.values()),
    }
    profile["profile_sha256"] = component_profile_sha256(profile)
    return profile


__all__ = ["ComponentCurationError", "compile_component_profile"]
