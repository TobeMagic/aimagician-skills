"""Compile a semantic client-content outline into safe native-slot bindings.

The model supplies only the ordered facts it wants on each selected slide.  It
never needs to see or choose region IDs, shape IDs, geometry or OOXML.  Native
capacity and semantic role information from ``preflight`` are the sole source
of binding authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from math import ceil
import re
from typing import Any


class BriefBindingError(ValueError):
    """The semantic outline cannot be safely represented by certified slots."""


_OUTLINE_FIELDS = frozenset({"schema_version", "slides"})
_SLIDE_FIELDS = frozenset({"slide_id", "facts"})
_FACT_FIELDS = frozenset({"value", "semantic_role"})
_LOCKED_FACT_FIELDS = frozenset({"fact_id", "semantic_role"})
_SEMANTIC_ROLES = frozenset({"title", "label", "metric", "body", "any"})
# A long, source-grounded conclusion is frequently supplied by an agent as a
# ``label`` because it names a visual value (for example ``总支出…万元``).
# It is not a card-caption once it exceeds this threshold. Permit it to use a
# certified body surface only after all fitting label surfaces are exhausted;
# short labels still cannot steal narrative space.
_LONG_LABEL_TO_BODY_MIN_CHARS = 12


def _structural_coverage_requirements(
    preflight: Mapping[str, Any], *, slide_id: str,
) -> dict[str, int]:
    """Return the non-negotiable content density for a rich native page.

    A template may expose many independent label/metric surfaces (cards,
    timeline stops, department chips).  Satisfying a generic role floor with a
    handful of facts leaves an otherwise beautiful page visibly empty after
    source copy is safely cleared.  Dense *text-only* templates therefore
    require a meaningful portion of their certified visual surface to be
    populated.  Governed chart/table pages are excluded: their published data
    contract, rather than ordinary outline facts, owns those visible values.
    """

    slides = preflight.get("slides")
    if not isinstance(slides, list):
        raise BriefBindingError("PREFLIGHT_SCHEMA_INVALID")
    for slide in slides:
        if not isinstance(slide, Mapping) or slide.get("slide_id") != slide_id:
            continue
        governed = slide.get("governed_content_contract")
        if isinstance(governed, Mapping) and governed.get("requires_structured_data") is True:
            return {}
        contract = slide.get("content_contract")
        if not isinstance(contract, Mapping):
            return {}
        required: dict[str, int] = {}
        for role in ("label", "metric"):
            surface_count = contract.get(role, 0)
            if type(surface_count) is not int or surface_count < 0:
                raise BriefBindingError("PREFLIGHT_SCHEMA_INVALID")
            # Small pages are already covered by the role-specific fact floor.
            # Eight or more repeated surfaces are a deliberate structural
            # pattern, so require 65% coverage rather than releasing a sparse
            # shell with only the title changed.
            if surface_count >= 8:
                required[role] = ceil(surface_count * 0.65)
        return required
    raise BriefBindingError("OUTLINE_SLIDE_UNKNOWN")


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
            if not isinstance(region, Mapping) or not isinstance(region.get("region_id"), str) or type(region.get("native_capacity")) is not int:
                raise BriefBindingError("PREFLIGHT_REGION_INVALID")
            raw_slots = region.get("shape_slots")
            raw_roles = region.get("semantic_roles")
            if isinstance(raw_slots, list):
                slot_roles = {
                    str(slot.get("binding_role", slot.get("semantic_role", "body")))
                    for slot in raw_slots
                    if isinstance(slot, Mapping)
                }
            elif isinstance(raw_roles, list):
                slot_roles = {str(role) for role in raw_roles if isinstance(role, str)}
            else:
                raise BriefBindingError("PREFLIGHT_REGION_INVALID")
            if not slot_roles:
                raise BriefBindingError("PREFLIGHT_REGION_INVALID")
            regions.append({
                "region_id": region["region_id"],
                "capacity": region["native_capacity"],
                "semantic_roles": slot_roles,
                "fragment_group": region.get("fragment_group") is True,
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


def _locked_fact_values(fact_store: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    """Return the active immutable client-copy ledger for a governed run."""

    facts = fact_store.get("facts")
    project = fact_store.get("project")
    sources = fact_store.get("sources")
    if (
        fact_store.get("schema_version") != "1.0"
        or not isinstance(project, Mapping)
        or not isinstance(project.get("title"), str)
        or not isinstance(project.get("language"), str)
        or not isinstance(sources, list)
        or not sources
        or not isinstance(facts, list)
    ):
        raise BriefBindingError("FACT_STORE_SCHEMA_INVALID")
    source_ids = {
        item.get("id") for item in sources
        if isinstance(item, Mapping) and isinstance(item.get("id"), str) and item.get("id")
    }
    if len(source_ids) != len(sources):
        raise BriefBindingError("FACT_STORE_SCHEMA_INVALID")
    values: dict[str, Mapping[str, Any]] = {}
    for item in facts:
        if not isinstance(item, Mapping):
            raise BriefBindingError("FACT_STORE_SCHEMA_INVALID")
        identifier, text = item.get("id"), item.get("text")
        if (
            not isinstance(identifier, str)
            or not identifier
            or not isinstance(text, str)
            or not text
            or item.get("status") != "active"
            or item.get("source_id") not in source_ids
            or not isinstance(item.get("locator"), str)
            or not item.get("locator")
            or not isinstance(item.get("recommended_beat"), str)
            or re.fullmatch(r"s(?:0[1-9]|1[0-5])", item["recommended_beat"]) is None
            or identifier in values
        ):
            raise BriefBindingError("FACT_STORE_SCHEMA_INVALID")
        values[identifier] = item
    if not values:
        raise BriefBindingError("FACT_STORE_SCHEMA_INVALID")
    return values


def compile_outline_bindings(
    outline: Mapping[str, Any], *, preflight: Mapping[str, Any],
    fact_store: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a strict v1 adaptation request from a semantic outline.

    Facts are allocated greedily to the smallest fitting unused region.  An
    explicit semantic role is an authority boundary, not a visual preference:
    a body cannot consume a title or metric surface merely because it is long.
    Only ``any`` is permitted to use a role-agnostic surface.  The compiler
    fails rather than truncating, duplicating, inventing client content, or
    corrupting a page's visual hierarchy.
    """

    if set(outline) != _OUTLINE_FIELDS or outline.get("schema_version") != "1.0" or not isinstance(outline.get("slides"), list):
        raise BriefBindingError("OUTLINE_SCHEMA_INVALID")
    regions_by_slide = _preflight_regions(preflight)
    locked_facts = _locked_fact_values(fact_store) if fact_store is not None else None
    facts: list[dict[str, str]] = []
    bindings: list[dict[str, Any]] = []
    seen_slides: set[str] = set()
    seen_locked_fact_ids: set[str] = set()
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
            if not isinstance(item, Mapping) or not isinstance(item.get("semantic_role"), str):
                raise BriefBindingError("OUTLINE_FACT_INVALID")
            if locked_facts is None:
                if set(item) != _FACT_FIELDS or not isinstance(item.get("value"), str):
                    raise BriefBindingError("OUTLINE_FACT_INVALID")
                value = item["value"]
                output_fact_id = f"{slide_id}-f{ordinal:02d}"
            else:
                if set(item) != _LOCKED_FACT_FIELDS or not isinstance(item.get("fact_id"), str):
                    raise BriefBindingError("LOCKED_FACT_REFERENCE_REQUIRED")
                output_fact_id = item["fact_id"]
                locked_fact = locked_facts.get(output_fact_id)
                if locked_fact is None:
                    raise BriefBindingError(f"LOCKED_FACT_UNKNOWN:fact_id={output_fact_id}")
                recommended_beat = locked_fact.get("recommended_beat")
                if recommended_beat is not None and recommended_beat != slide_id:
                    raise BriefBindingError(
                        "LOCKED_FACT_BEAT_MISMATCH"
                        f":fact_id={output_fact_id}:slide_id={slide_id}"
                    )
                value = locked_fact["text"]
                if output_fact_id in seen_locked_fact_ids:
                    raise BriefBindingError(f"LOCKED_FACT_REUSED:fact_id={output_fact_id}")
                seen_locked_fact_ids.add(output_fact_id)
            requested_role = item["semantic_role"]
            if not value or requested_role not in _SEMANTIC_ROLES:
                raise BriefBindingError("OUTLINE_FACT_INVALID")
            prepared.append({
                "ordinal": ordinal,
                "value": value,
                "requested_role": requested_role,
                "source_fact_id": output_fact_id,
                "required": _compact_len(value),
            })

        coverage = _structural_coverage_requirements(preflight, slide_id=slide_id)
        for role, required_count in coverage.items():
            provided_count = sum(
                1 for item in prepared if item["requested_role"] == role
            )
            if provided_count < required_count:
                raise BriefBindingError(
                    "OUTLINE_STRUCTURAL_COVERAGE_INSUFFICIENT"
                    f":slide_id={slide_id}:role={role}"
                    f":provided={provided_count}:required={required_count}"
                )

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
                # A title/body/metric's semantic role is derived from the
                # certified source page.  Falling back across roles looked
                # superficially helpful but lets a long body replace a
                # headline, particularly on chart-led editorial pages.
                strict_fitting = [
                    region for region in fitting
                    if requested_role in region["semantic_roles"]
                ]
                # A conclusion-length label is semantically safer in a body
                # line than in a small card caption. This is deliberately a
                # narrow one-way fallback: never use it for a short label,
                # title, metric or body fact, and never take a label surface
                # when one fits.
                if (
                    not strict_fitting
                    and requested_role == "label"
                    and required >= _LONG_LABEL_TO_BODY_MIN_CHARS
                ):
                    strict_fitting = [
                        region for region in fitting
                        if "body" in region["semantic_roles"]
                    ]
                fitting = strict_fitting
            if not fitting:
                raise BriefBindingError(
                    "OUTLINE_FACT_NO_FITTING_SLOT"
                    f":slide_id={slide_id}:ordinal={ordinal}:requested_chars={required}"
                    f":remaining_slots={_remaining_capacity_summary(available)}"
                )
            chosen = min(fitting, key=lambda region: (region["capacity"], region["region_id"]))
            available.remove(chosen)
            allocated[ordinal] = {
                "value": value,
                "source_fact_id": item["source_fact_id"],
                "region_id": chosen["region_id"],
                "operation": (
                    "replace_fragment_text" if chosen["fragment_group"]
                    else "replace_text"
                ),
            }

        for item in prepared:
            ordinal = int(item["ordinal"])
            binding = allocated[ordinal]
            fact_id = str(binding["source_fact_id"])
            facts.append({"fact_id": fact_id, "value": binding["value"]})
            bindings.append({
                "slide_id": slide_id,
                "operation": binding["operation"],
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
