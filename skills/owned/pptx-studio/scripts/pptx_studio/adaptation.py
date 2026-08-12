"""Fact/asset-ID-only adaptation-plan compiler for later physical assembly."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from .composition import composition_plan_sha256


class AdaptationError(ValueError):
    """Raised when a binding requests undeclared visual implementation authority."""


_REQUEST_FIELDS = frozenset({"schema_version", "facts", "assets", "bindings"})
_FACT_FIELDS = frozenset({"fact_id", "value"})
_ASSET_FIELDS = frozenset({"asset_id", "sha256"})
_BINDING_FIELDS = frozenset({"slide_id", "operation", "region_id", "shape_id", "fact_id", "asset_id"})
_FORBIDDEN = frozenset({"text", "x", "y", "w", "h", "color", "font", "size", "style", "xml", "ooxml", "path", "locator"})


def serialize_adaptation_plan(plan: Mapping[str, Any]) -> str:
    return json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def adaptation_request_sha256(request: Mapping[str, Any]) -> str:
    """Bind the ID-only plan to the immutable value registry without exposing it."""

    return __import__("hashlib").sha256(
        json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _registry(request: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str], list[Mapping[str, Any]]]:
    if set(request) != _REQUEST_FIELDS or request.get("schema_version") != "1.0":
        raise AdaptationError("REQUEST_SCHEMA_INVALID")
    facts_raw, assets_raw, bindings = request.get("facts"), request.get("assets"), request.get("bindings")
    if not isinstance(facts_raw, list) or not isinstance(assets_raw, list) or not isinstance(bindings, list):
        raise AdaptationError("REGISTRY_SCHEMA_INVALID")
    facts: dict[str, str] = {}
    for item in facts_raw:
        if not isinstance(item, Mapping) or set(item) != _FACT_FIELDS or not isinstance(item.get("fact_id"), str) or not item["fact_id"] or not isinstance(item.get("value"), str):
            raise AdaptationError("FACT_INVALID")
        if item["fact_id"] in facts:
            raise AdaptationError("FACT_DUPLICATE")
        facts[item["fact_id"]] = item["value"]
    assets: dict[str, str] = {}
    for item in assets_raw:
        if not isinstance(item, Mapping) or set(item) != _ASSET_FIELDS or not isinstance(item.get("asset_id"), str) or not item["asset_id"] or not isinstance(item.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise AdaptationError("ASSET_INVALID")
        if item["asset_id"] in assets:
            raise AdaptationError("ASSET_DUPLICATE")
        assets[item["asset_id"]] = item["sha256"]
    return facts, assets, bindings


def compile_adaptation(
    composition_plan: Mapping[str, Any],
    *,
    catalog: Mapping[str, Any],
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Compile only safe, value-free references for a later materializer."""

    if composition_plan.get("schema_version") != "1.0" or composition_plan.get("status") != "PASS":
        raise AdaptationError("COMPOSITION_PLAN_INVALID")
    facts, assets, bindings = _registry(request)
    pages = {str(page.get("page_id")): page for page in catalog.get("pages", []) if isinstance(page, Mapping)}
    regions = {str(region.get("region_id")): region for region in catalog.get("regions", []) if isinstance(region, Mapping)}
    selected = {str(item.get("slide_id")): item for item in composition_plan.get("slides", []) if isinstance(item, Mapping)}
    operations: list[dict[str, Any]] = []
    targets: set[tuple[str, str]] = set()
    for binding in bindings:
        if not isinstance(binding, Mapping) or set(binding) != _BINDING_FIELDS or any(key in binding for key in _FORBIDDEN):
            raise AdaptationError("BINDING_SCHEMA_INVALID")
        slide_id, operation = binding.get("slide_id"), binding.get("operation")
        if not isinstance(slide_id, str) or slide_id not in selected or operation not in {"replace_text", "replace_asset"}:
            raise AdaptationError("BINDING_TARGET_INVALID")
        source = selected[slide_id].get("source")
        if not isinstance(source, Mapping) or not isinstance(source.get("page_id"), str):
            raise AdaptationError("PLAN_SOURCE_INVALID")
        page = pages.get(source["page_id"])
        if page is None or page.get("package_sha256") != source.get("package_sha256"):
            raise AdaptationError("SOURCE_DRIFT")
        if operation == "replace_text":
            region_id, fact_id = binding.get("region_id"), binding.get("fact_id")
            if not isinstance(region_id, str) or not isinstance(fact_id, str) or fact_id not in facts:
                raise AdaptationError("TEXT_BINDING_INVALID")
            region = regions.get(region_id)
            if region is None or region.get("page_id") != page.get("page_id") or region_id not in source.get("region_ids", []):
                raise AdaptationError("REGION_NOT_SELECTED")
            capacity = region.get("capacity", {}).get("max_text_chars", 0) if isinstance(region.get("capacity"), Mapping) else 0
            if type(capacity) is not int or len(facts[fact_id]) > capacity:
                raise AdaptationError("TEXT_CAPACITY_EXCEEDED")
            target = (slide_id, region_id)
            if target in targets:
                raise AdaptationError("BINDING_TARGET_DUPLICATE")
            targets.add(target)
            operations.append({"slide_id": slide_id, "operation": operation, "region_id": region_id, "fact_id": fact_id, "capacity": capacity})
        else:
            shape_id, asset_id = binding.get("shape_id"), binding.get("asset_id")
            if not isinstance(shape_id, str) or not isinstance(asset_id, str) or asset_id not in assets:
                raise AdaptationError("ASSET_BINDING_INVALID")
            image_ids = {str(shape.get("shape_id")) for shape in page.get("shapes", []) if isinstance(shape, Mapping) and shape.get("kind") == "image"}
            if shape_id not in image_ids:
                raise AdaptationError("ASSET_TARGET_INVALID")
            target = (slide_id, shape_id)
            if target in targets:
                raise AdaptationError("BINDING_TARGET_DUPLICATE")
            targets.add(target)
            operations.append({"slide_id": slide_id, "operation": operation, "shape_id": shape_id, "asset_id": asset_id, "asset_sha256": assets[asset_id]})
    return {
        "schema_version": "1.0",
        "status": "PASS",
        "composition_plan_sha256": composition_plan_sha256(composition_plan),
        "adaptation_request_sha256": adaptation_request_sha256(request),
        "operations": operations,
    }
