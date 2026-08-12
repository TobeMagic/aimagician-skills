"""Compile a semantic client-content outline into safe native-slot bindings.

The model supplies only the ordered facts it wants on each selected slide.  It
never needs to see or choose region IDs, shape IDs, geometry or OOXML.  Native
capacity and semantic role information from ``preflight`` are the sole source
of binding authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class BriefBindingError(ValueError):
    """The semantic outline cannot be safely represented by certified slots."""


_OUTLINE_FIELDS = frozenset({"schema_version", "slides"})
_SLIDE_FIELDS = frozenset({"slide_id", "facts"})
_FACT_FIELDS = frozenset({"value", "semantic_role"})
_SEMANTIC_ROLES = frozenset({"title", "label", "metric", "body", "any"})


def _compact_len(value: str) -> int:
    # PowerPoint stores whitespace in the text run.  Capacity decisions must
    # use the same raw character measure as adaptation and the physical
    # importer; removing spaces here made a fact appear to fit during binding
    # and fail later in a different compiler stage.
    return len(value)


def _preflight_regions(preflight: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if preflight.get("status") != "PASS" or not isinstance(preflight.get("slides"), list):
        raise BriefBindingError("PREFLIGHT_INVALID")
    result: dict[str, list[dict[str, Any]]] = {}
    for slide in preflight["slides"]:
        if not isinstance(slide, Mapping) or not isinstance(slide.get("slide_id"), str) or not isinstance(slide.get("regions"), list):
            raise BriefBindingError("PREFLIGHT_SCHEMA_INVALID")
        regions: list[dict[str, Any]] = []
        for region in slide["regions"]:
            if not isinstance(region, Mapping) or not isinstance(region.get("region_id"), str) or type(region.get("native_capacity")) is not int or not isinstance(region.get("shape_slots"), list):
                raise BriefBindingError("PREFLIGHT_REGION_INVALID")
            slot_roles = {
                str(slot.get("binding_role", slot.get("semantic_role", "body")))
                for slot in region["shape_slots"]
                if isinstance(slot, Mapping)
            }
            if not slot_roles:
                raise BriefBindingError("PREFLIGHT_REGION_INVALID")
            regions.append({
                "region_id": region["region_id"],
                "capacity": region["native_capacity"],
                "semantic_roles": slot_roles,
            })
        result[slide["slide_id"]] = regions
    return result


def _remaining_capacity_summary(regions: list[dict[str, Any]]) -> str:
    """Return a compact public repair hint without leaking template copy.

    A weak model cannot reliably infer why a fact failed from its ordinal
    alone.  Report only certified role/capacity aggregates, never source text,
    shape IDs, geometry or private paths.  This is sufficient for it to remove
    a low-priority fact, shorten an approved label, or split the narrative.
    """

    buckets: dict[tuple[str, int], int] = {}
    for region in regions:
        capacity = int(region["capacity"])
        for role in sorted(str(item) for item in region["semantic_roles"]):
            buckets[(role, capacity)] = buckets.get((role, capacity), 0) + 1
    return ",".join(
        f"{role}:{capacity}x{count}"
        for (role, capacity), count in sorted(buckets.items())
    ) or "none"


def compile_outline_bindings(outline: Mapping[str, Any], *, preflight: Mapping[str, Any]) -> dict[str, Any]:
    """Return a strict v1 adaptation request from a semantic outline.

    Facts are allocated greedily to the smallest fitting unused region.  An
    explicit semantic role is preferred; the allocator safely falls back to a
    certified ``body``/other region only when no exact visual role fits.  It
    fails rather than truncating, duplicating, or inventing client content.
    """

    if set(outline) != _OUTLINE_FIELDS or outline.get("schema_version") != "1.0" or not isinstance(outline.get("slides"), list):
        raise BriefBindingError("OUTLINE_SCHEMA_INVALID")
    regions_by_slide = _preflight_regions(preflight)
    facts: list[dict[str, str]] = []
    bindings: list[dict[str, Any]] = []
    seen_slides: set[str] = set()
    for slide in outline["slides"]:
        if not isinstance(slide, Mapping) or set(slide) != _SLIDE_FIELDS or not isinstance(slide.get("slide_id"), str) or not isinstance(slide.get("facts"), list):
            raise BriefBindingError("OUTLINE_SLIDE_INVALID")
        slide_id = slide["slide_id"]
        if slide_id in seen_slides or slide_id not in regions_by_slide:
            raise BriefBindingError("OUTLINE_SLIDE_UNKNOWN")
        seen_slides.add(slide_id)
        available = list(regions_by_slide[slide_id])
        prepared: list[dict[str, Any]] = []
        for ordinal, item in enumerate(slide["facts"], start=1):
            if not isinstance(item, Mapping) or set(item) != _FACT_FIELDS or not isinstance(item.get("value"), str) or not isinstance(item.get("semantic_role"), str):
                raise BriefBindingError("OUTLINE_FACT_INVALID")
            value, requested_role = item["value"], item["semantic_role"]
            if not value or requested_role not in _SEMANTIC_ROLES:
                raise BriefBindingError("OUTLINE_FACT_INVALID")
            prepared.append({
                "ordinal": ordinal,
                "value": value,
                "requested_role": requested_role,
                "required": _compact_len(value),
            })

        # Allocate scarce long-capacity regions first. A presentation outline
        # is naturally written title → metric → body; consuming a 31-character
        # body slot for an early five-character label can make a later source
        # grounded conclusion falsely appear impossible. Allocation order is
        # internal only: stable fact IDs and output order remain the model's
        # original narrative order.
        allocated: dict[int, dict[str, Any]] = {}
        for item in sorted(prepared, key=lambda record: (-record["required"], record["ordinal"])):
            ordinal = int(item["ordinal"])
            value = str(item["value"])
            requested_role = str(item["requested_role"])
            required = int(item["required"])
            fitting = [region for region in available if region["capacity"] >= required]
            if requested_role != "any":
                exact = [region for region in fitting if requested_role in region["semantic_roles"]]
                if exact:
                    fitting = exact
            if not fitting:
                raise BriefBindingError(
                    "OUTLINE_FACT_NO_FITTING_SLOT"
                    f":slide_id={slide_id}:ordinal={ordinal}:requested_chars={required}"
                    f":remaining_slots={_remaining_capacity_summary(available)}"
                )
            chosen = min(fitting, key=lambda region: (region["capacity"], region["region_id"]))
            available.remove(chosen)
            allocated[ordinal] = {"value": value, "region_id": chosen["region_id"]}

        for item in prepared:
            ordinal = int(item["ordinal"])
            binding = allocated[ordinal]
            fact_id = f"{slide_id}-f{ordinal:02d}"
            facts.append({"fact_id": fact_id, "value": binding["value"]})
            bindings.append({
                "slide_id": slide_id,
                "operation": "replace_text",
                "region_id": binding["region_id"],
                "shape_id": None,
                "fact_id": fact_id,
                "asset_id": None,
            })
    # Structured data is deliberately a distinct semantic payload.  Normal
    # text-only decks still carry the empty field so every downstream stage
    # sees one strict adaptation-request schema.
    return {
        "schema_version": "1.0",
        "facts": facts,
        "assets": [],
        "bindings": bindings,
        "structured_data": [],
    }
