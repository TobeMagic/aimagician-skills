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
_FACT_FIELDS = frozenset({"value", "semantic_role", "component_key", "component_group", "component_field"})
_LOCKED_FACT_FIELDS = frozenset({"fact_id", "semantic_role", "component_key", "component_group", "component_field"})
_SEMANTIC_ROLES = frozenset({"title", "label", "metric", "body", "any"})
# A long, source-grounded conclusion is frequently supplied by an agent as a
# ``label`` because it names a visual value (for example ``总支出…万元``).
# It is not a card-caption once it exceeds this threshold. Permit it to use a
# certified body surface only after all fitting label surfaces are exhausted;
# short labels still cannot steal narrative space.
_LONG_LABEL_TO_BODY_MIN_CHARS = 12
_MIN_VISUAL_SURFACE_COVERAGE = 0.50


def _is_semantic_fragment(text: str) -> bool:
    """Reject a visually useless fragment before it can enter an outline.

    A source locator proves provenance but not that an agent selected a
    meaningful unit of language.  In particular, weak agents sometimes split
    a normal Chinese word (``建设``) into two title facts solely to fill a
    repeated native component.  Such a deck is mechanically editable yet
    plainly unprofessional.  A one-character CJK token is therefore not a
    reusable fact.  Measurements and symbols remain valid: they use digits
    or non-CJK characters after punctuation/space normalisation.
    """

    compact = re.sub(r"[\s\W_]", "", text, flags=re.UNICODE)
    return not (len(compact) == 1 and "\u3400" <= compact <= "\u9fff")


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
        # Rich specialist pages deliberately expose more editable labels than
        # their client narrative should populate: timeline ticks, process
        # connectors, map callouts and team ornaments are part of the native
        # visual grammar, not a request to invent filler.  Generic card pages
        # keep the coverage guard below.  Older/pre-v7 preflight evidence has
        # no role and therefore retains the conservative historic behaviour.
        declared_role = slide.get("role")
        if declared_role in {
            "timeline", "roadmap", "process", "flow", "team", "map",
            "business-model", "product", "quote", "partners", "case-study",
            "clinical-network",
        }:
            return {}
        governed = slide.get("governed_content_contract")
        if isinstance(governed, Mapping) and governed.get("requires_structured_data") is True:
            return {}
        contract = slide.get("content_contract")
        if not isinstance(contract, Mapping):
            return {}
        # Some certified section dividers are a single editorial word; others
        # visibly reserve a subtitle/statement panel.  The latter looks
        # broken when template-copy cleanup leaves the panel empty.  Require a
        # factual body only when the native page actually publishes a body
        # surface, preserving intentionally sparse one-word dividers.
        if declared_role == "section" and type(contract.get("body")) is int and contract["body"] > 0:
            return {"body": 1}
        # A certified native component group is a stronger density signal than
        # the raw count of text boxes.  A dashboard/page can contain many
        # auxiliary numbers, units and decorative labels; requiring 65% of
        # *all* of them coerces the model to invent client facts merely to
        # clear a density floor.  Group completeness below already guarantees
        # that every selected visual unit is filled as designed.  Keep the
        # generic density gate for ungrouped pages, where no such grammar is
        # available.
        if isinstance(slide.get("component_groups"), list) and slide["component_groups"]:
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
        declared_role = slide.get("role")
        if declared_role is not None and not isinstance(declared_role, str):
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
                "component_key": region.get("component_key"),
                "component_binding": region.get("component_binding"),
                "declared_role": declared_role,
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
        kind = item.get("kind")
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
            # Narrative planning permits up to 24 delivery beats.  Fact
            # ownership must not silently cap a legitimate no-count client
            # narrative at the historical 15-slide reference length.
            or re.fullmatch(r"s(?:0[1-9]|1[0-9]|2[0-4])", item["recommended_beat"]) is None
            or identifier in values
            or (kind is not None and (not isinstance(kind, str) or not kind))
        ):
            raise BriefBindingError("FACT_STORE_SCHEMA_INVALID")
        if not _is_semantic_fragment(text):
            raise BriefBindingError(
                f"FACT_STORE_SEMANTIC_FRAGMENT_INVALID:fact_id={identifier}"
            )
        values[identifier] = item
    if not values:
        raise BriefBindingError("FACT_STORE_SCHEMA_INVALID")
    return values


def _require_complete_component_groups(
    preflight_slide: Mapping[str, Any], prepared: list[Mapping[str, Any]],
) -> None:
    """Reject a partially populated certified visual component.

    Native PPTX group membership is intentionally published as opaque component
    keys.  A weak model can otherwise put a new metric into a dashboard card
    while leaving its label (or its paired unit/action) as stale template copy.
    That is mechanically valid OOXML but visually and semantically broken.
    """

    groups = preflight_slide.get("component_groups")
    if groups is None:
        return
    if not isinstance(groups, list):
        raise BriefBindingError("OUTLINE_COMPONENT_GROUP_INVALID")
    published = preflight_slide.get("component_contract")
    published_keys = {
        item.get("component_key")
        for item in published
        if isinstance(item, Mapping) and isinstance(item.get("component_key"), str)
    } if isinstance(published, list) else set()
    # A component is an explicit authoring decision only when the outline
    # names its group or its exact key.  Automatic ordinary-slot allocation
    # may land a cover caption on a member of a decorative, non-required
    # group; that must not silently turn one ordinary fact into a demand to
    # invent the other members of that component.  Explicit group/key use
    # still has the original all-or-nothing semantics below.
    explicitly_requested_groups = {
        item.get("component_group")
        for item in prepared
        if isinstance(item.get("component_group"), str)
    }
    explicitly_requested_keys = {
        item.get("component_key")
        for item in prepared
        if isinstance(item.get("component_key"), str)
        and isinstance(item.get("component_target"), str)
    }
    selected = {
        item.get("component_key")
        for item in prepared
        if isinstance(item.get("component_key"), str)
    }
    for group in groups:
        if not isinstance(group, Mapping):
            raise BriefBindingError("OUTLINE_COMPONENT_GROUP_INVALID")
        group_id = group.get("component_group")
        keys = group.get("component_keys")
        if (
            not isinstance(group_id, str)
            or not group_id
            or not isinstance(keys, list)
            or len(keys) < 2
            or any(not isinstance(key, str) or not key for key in keys)
            or len(set(keys)) != len(keys)
            or (published_keys and not set(keys).issubset(published_keys))
        ):
            raise BriefBindingError("OUTLINE_COMPONENT_GROUP_INVALID")
        chosen = [key for key in keys if key in selected]
        explicitly_selected = (
            # Before allocation, group-targeted facts have no native key yet;
            # after allocation they retain the group alias and gain one.  Do
            # not reject that legitimate intermediate state.
            (group_id in explicitly_requested_groups and bool(chosen))
            or bool(set(keys).intersection(explicitly_requested_keys))
        )
        # A wholly absent required group has its own actionable diagnostic in
        # ``_require_component_group_coverage``.  This check owns only a group
        # that the outline has started to populate and must therefore finish.
        if (
            (explicitly_selected or (group.get("required") is True and bool(chosen)))
            and len(chosen) != len(keys)
        ):
            missing = [key for key in keys if key not in selected]
            raise BriefBindingError(
                "OUTLINE_COMPONENT_GROUP_INCOMPLETE"
                f":slide_id={preflight_slide.get('slide_id')}:group={group_id}"
                f":provided={','.join(chosen)}:required={','.join(keys)}"
                f":missing={','.join(missing)}"
            )


def _require_visual_surface_coverage(
    preflight_slide: Mapping[str, Any], prepared: list[Mapping[str, Any]],
) -> None:
    """Reject a source page whose visible text skeleton would remain empty.

    Clearing sample copy is necessary but not sufficient: its surrounding
    cards, frames and diagram units remain visible.  Requiring a bounded share
    of published native surfaces prevents a two-fact section from releasing a
    thirteen-unit template shell.  This is a re-selection signal, never a cue
    to invent filler.
    """

    contract = preflight_slide.get("component_contract")
    if not isinstance(contract, list) or not contract:
        return
    published_keys = {
        item.get("component_key")
        for item in contract
        if isinstance(item, Mapping) and isinstance(item.get("component_key"), str)
    }
    if not published_keys:
        return
    # A high-end cover can intentionally expose a single editorial title
    # while retaining decorative metadata surfaces that must remain empty.
    # The role floor still requires that one customer fact, and physical QA
    # validates the populated composition. Requiring a percentage of every
    # source text box here would force author/presenter/date facts into the
    # cover, a common cause of collisions and visual noise.
    if preflight_slide.get("role") == "cover":
        return
    coverage = _MIN_VISUAL_SURFACE_COVERAGE
    required = ceil(len(published_keys) * coverage)
    if len(prepared) < required:
        raise BriefBindingError(
            "OUTLINE_VISUAL_SURFACE_COVERAGE_INSUFFICIENT"
            f":slide_id={preflight_slide.get('slide_id')}"
            f":provided={len(prepared)}:required={required}"
            f":published={len(published_keys)}"
        )


def _published_component_groups(preflight_slide: Mapping[str, Any]) -> dict[str, set[str]]:
    """Return a validated opaque-group → published-component map."""

    groups = preflight_slide.get("component_groups")
    if groups is None:
        return {}
    if not isinstance(groups, list):
        raise BriefBindingError("OUTLINE_COMPONENT_GROUP_INVALID")
    result: dict[str, set[str]] = {}
    for group in groups:
        if not isinstance(group, Mapping):
            raise BriefBindingError("OUTLINE_COMPONENT_GROUP_INVALID")
        group_id, keys = group.get("component_group"), group.get("component_keys")
        fields = group.get("component_fields")
        if (
            not isinstance(group_id, str) or not group_id
            or not isinstance(keys, list) or len(keys) < 2
            or any(not isinstance(key, str) or not key for key in keys)
            or len(set(keys)) != len(keys) or group_id in result
            or (fields is not None and (
                not isinstance(fields, list)
                or len(fields) != len(keys)
                or any(not isinstance(field, str) or not field for field in fields)
                or len(set(fields)) != len(fields)
            ))
        ):
            raise BriefBindingError("OUTLINE_COMPONENT_GROUP_INVALID")
        result[group_id] = set(keys)
    return result


def _assign_sequence_groups_automatically(
    preflight_slide: Mapping[str, Any], prepared: list[dict[str, Any]],
) -> None:
    """Bind ordered timeline date/action facts to published milestone groups.

    Timeline component groups are compiler-discovered from a certified native
    page.  Requiring a weak model to name opaque ``timeline-step.03`` keys
    would turn ordinary fact binding into a private-slot guessing exercise.
    A strict alternating label/body sequence is therefore assigned to the
    published group order. Other page types and any explicit component choice
    retain the ordinary, fully explicit component contract.
    """

    if preflight_slide.get("role") not in {"timeline", "roadmap"}:
        return
    if any(item.get("component_key") is not None or item.get("component_group") is not None for item in prepared):
        return
    raw_groups = preflight_slide.get("component_groups")
    if not isinstance(raw_groups, list):
        return
    groups = [
        group for group in raw_groups
        if isinstance(group, Mapping)
        and group.get("component_intent") == "timeline-milestone"
        and isinstance(group.get("component_group"), str)
        and isinstance(group.get("component_keys"), list)
        and group.get("component_fields") == ["date", "action"]
        and len(group["component_keys"]) == 2
    ]
    groups.sort(key=lambda group: str(group["component_group"]))
    sequence_items = [
        item for item in prepared
        if item.get("requested_role") in {"label", "body"}
    ]
    if not sequence_items or len(sequence_items) % 2 or len(sequence_items) > len(groups) * 2:
        return
    pairs = list(zip(sequence_items[::2], sequence_items[1::2], strict=True))
    if any(
        first.get("requested_role") != "label" or second.get("requested_role") != "body"
        for first, second in pairs
    ):
        return
    for (label, body), group in zip(pairs, groups, strict=False):
        group_id = str(group["component_group"])
        label["component_group"] = group_id
        label["component_field"] = "date"
        body["component_group"] = group_id
        body["component_field"] = "action"


def _require_component_group_coverage(
    preflight_slide: Mapping[str, Any], prepared: list[Mapping[str, Any]],
) -> None:
    """Keep card-led pages from becoming a mostly empty template shell.

    Complete group membership prevents a broken half-card.  It does not by
    itself stop an agent from filling only two cards in a certified KPI grid
    and leaving the rest blank.  Dense dashboard and multi-item pages need a
    modest visual-group floor; specialised relationship pages are deliberately
    excluded because their groups can represent ornamental network nodes.
    """

    group_map = _published_component_groups(preflight_slide)
    if not group_map:
        return
    selected_keys = {
        item.get("component_key")
        for item in prepared
        if isinstance(item.get("component_key"), str)
    }
    selected_groups = [
        group_id for group_id, keys in group_map.items()
        if keys.intersection(selected_keys)
    ]
    raw_groups = preflight_slide.get("component_groups")
    required_groups = {
        str(group.get("component_group"))
        for group in (raw_groups if isinstance(raw_groups, list) else [])
        if isinstance(group, Mapping)
        and group.get("required") is True
    }
    missing_required = sorted(required_groups.difference(selected_groups))
    if missing_required:
        raise BriefBindingError(
            "OUTLINE_REQUIRED_COMPONENT_GROUP_MISSING"
            f":slide_id={preflight_slide.get('slide_id')}"
            f":groups={','.join(missing_required)}"
        )
    if preflight_slide.get("role") in {"cover", "contents", "section", "closing", "data", "table"}:
        return
    # A compact relationship page with only two or three declared visual
    # units has no spare card: leaving one empty is conspicuous. Larger
    # dashboards can retain deliberate breathing room, but must still express
    # at least half of their certified units with client-grounded content.
    required = len(group_map) if len(group_map) <= 3 else ceil(len(group_map) * 0.5)
    if len(selected_groups) < required:
        raise BriefBindingError(
            "OUTLINE_COMPONENT_GROUP_COVERAGE_INSUFFICIENT"
            f":slide_id={preflight_slide.get('slide_id')}"
            f":provided={len(selected_groups)}:required={required}"
        )


def validate_fact_store(fact_store: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a locked client ledger before any template retrieval.

    This makes the brief-freeze boundary an explicit CLI gate rather than an
    error discovered only after a weak model has spent time composing pages.
    The return deliberately exposes only counts and approved beat IDs; client
    values and private source content stay in the local fact-store file.
    """

    facts = _locked_fact_values(fact_store)
    beats = sorted({str(record["recommended_beat"]) for record in facts.values()})
    return {
        "schema_version": "1.0",
        "status": "PASS",
        "fact_count": len(facts),
        "approved_beats": beats,
    }


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
            component_key = item.get("component_key")
            component_group = item.get("component_group")
            component_field = item.get("component_field")
            if component_key is not None and not isinstance(component_key, str):
                raise BriefBindingError("OUTLINE_COMPONENT_INVALID")
            if component_group is not None and not isinstance(component_group, str):
                raise BriefBindingError("OUTLINE_COMPONENT_INVALID")
            if component_field is not None and not isinstance(component_field, str):
                raise BriefBindingError("OUTLINE_COMPONENT_INVALID")
            if component_key is not None and component_group is not None:
                raise BriefBindingError("OUTLINE_COMPONENT_TARGET_AMBIGUOUS")
            if component_field is not None and component_group is None:
                raise BriefBindingError("OUTLINE_COMPONENT_FIELD_REQUIRES_GROUP")
            if locked_facts is None:
                if (
                    not {"value", "semantic_role"}.issubset(item)
                    or not set(item).issubset(_FACT_FIELDS)
                    or not isinstance(item.get("value"), str)
                ):
                    raise BriefBindingError("OUTLINE_FACT_INVALID")
                value = item["value"]
                output_fact_id = f"{slide_id}-f{ordinal:02d}"
            else:
                if (
                    not {"fact_id", "semantic_role"}.issubset(item)
                    or not set(item).issubset(_LOCKED_FACT_FIELDS)
                    or not isinstance(item.get("fact_id"), str)
                ):
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
                "component_key": component_key,
                "component_target": component_key,
                "component_group": component_group,
                "component_field": component_field,
            })

        preflight_slide = next(
            item for item in preflight["slides"]
            if isinstance(item, Mapping) and item.get("slide_id") == slide_id
        )
        # ``component_contract`` is a deterministic layout API, not a burden
        # for the authoring agent. A direct component key remains useful when
        # a client explicitly needs a particular surface, but ordinary facts
        # can safely omit it: the binder selects the smallest fitting unused
        # native surface by role and capacity. Requiring opaque ordinals such
        # as ``metric.07`` made a valid outline turn into slot-guessing.
        component_groups = _published_component_groups(preflight_slide)
        # A group alias is the author-facing API for a linked visual unit.
        # Once a complete group is requested, its facts must resolve to the
        # published member order.  Capacity-first allocation can otherwise
        # distribute same-role facts across cards and leave every card
        # formally complete but visually cross-wired.  The outline supplies
        # facts in this public component order; it never needs to know a
        # shape identifier or coordinate.
        raw_component_groups = preflight_slide.get("component_groups")
        ordered_component_groups = {
            str(group["component_group"]): {
                "keys": list(group["component_keys"]),
                "fields": list(group["component_fields"])
                if isinstance(group.get("component_fields"), list) else None,
            }
            for group in (raw_component_groups if isinstance(raw_component_groups, list) else [])
            if isinstance(group, Mapping)
            and isinstance(group.get("component_group"), str)
            and isinstance(group.get("component_keys"), list)
        }
        for item in prepared:
            group = item["component_group"]
            if group is not None and group not in component_groups:
                raise BriefBindingError(
                    f"OUTLINE_COMPONENT_GROUP_UNKNOWN:slide_id={slide_id}:group={group}"
                )
        _assign_sequence_groups_automatically(preflight_slide, prepared)
        _require_complete_component_groups(preflight_slide, prepared)
        for group_id, group_contract in ordered_component_groups.items():
            keys = group_contract["keys"]
            fields = group_contract["fields"]
            group_items = [item for item in prepared if item["component_group"] == group_id]
            if not group_items:
                continue
            if len(group_items) != len(keys):
                raise BriefBindingError(
                    "OUTLINE_COMPONENT_GROUP_MEMBER_COUNT_INVALID"
                    f":slide_id={slide_id}:group={group_id}"
                )
            if fields is None:
                # Legacy annotations did not have named fields. Retain their
                # published visual sequence for backwards compatibility.
                for group_item, component_key in zip(group_items, keys):
                    group_item["resolved_group_component_key"] = component_key
            else:
                field_to_key = dict(zip(fields, keys, strict=True))
                supplied_fields = [item.get("component_field") for item in group_items]
                if any(not isinstance(field, str) or not field for field in supplied_fields):
                    raise BriefBindingError(
                        "OUTLINE_COMPONENT_FIELD_REQUIRED"
                        f":slide_id={slide_id}:group={group_id}"
                    )
                if set(supplied_fields) != set(fields) or len(set(supplied_fields)) != len(supplied_fields):
                    raise BriefBindingError(
                        "OUTLINE_COMPONENT_FIELD_COVERAGE_INVALID"
                        f":slide_id={slide_id}:group={group_id}"
                    )
                for group_item in group_items:
                    group_item["resolved_group_component_key"] = field_to_key[
                        str(group_item["component_field"])
                    ]
        coverage = _structural_coverage_requirements(preflight, slide_id=slide_id)
        # A visible, certified title surface is a mandatory part of the page
        # grammar.  Without this gate a weak agent can label its headline as
        # a generic metric/body fact, leaving the true headline blank and
        # placing the narrative into a data card.  A title *fact* remains
        # subject to native capacity, so the model must condense it or select
        # another certified page instead of overflowing the art direction.
        content_contract = preflight_slide.get("content_contract")
        if (
            isinstance(content_contract, Mapping)
            and isinstance(content_contract.get("title"), int)
            and content_contract["title"] > 0
        ):
            coverage["title"] = max(1, coverage.get("title", 0))
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
            component_key = item.get("component_key")
            component_group = item.get("component_group")
            if component_key is not None:
                # Component keys are published by the local preflight only.
                # They identify a role-ordered native surface, never a shape
                # or a coordinate.  A typo must fail rather than silently
                # spilling the fact into an arbitrary card.
                fitting = [
                    region for region in fitting
                    if region.get("component_key") == component_key
                ]
            elif component_group is not None:
                # The weak-model interface targets a deliberate visual unit,
                # not one fragile internal key.  Select the only fitting
                # native member for this fact's declared role; all members
                # are still checked as a complete group after allocation.
                resolved_component_key = item.get("resolved_group_component_key")
                fitting = [
                    region for region in fitting
                    if region.get("component_key") == resolved_component_key
                ]
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
                # A native timeline often renders both a milestone date and
                # its action in compact label surfaces.  The narrative still
                # retains the action as a semantic body fact, but forcing it
                # into a non-existent generic body slot would reject a
                # physically sound, certified timeline.  This is intentionally
                # one-way and page-role-limited: no ordinary body prose may
                # occupy a label/title/metric surface.
                if (
                    not strict_fitting
                    and requested_role == "body"
                    and all(region.get("declared_role") in {"timeline", "roadmap"} for region in fitting)
                ):
                    strict_fitting = [
                        region for region in fitting
                        if "label" in region["semantic_roles"]
                    ]
                fitting = strict_fitting
            if not fitting:
                raise BriefBindingError(
                    ("OUTLINE_COMPONENT_NO_FITTING_SLOT" if component_key is not None or component_group is not None else "OUTLINE_FACT_NO_FITTING_SLOT")
                    +
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
                "component_key": chosen.get("component_key"),
                "component_group": component_group,
                "component_binding": chosen.get("component_binding"),
            }

        # A group-targeting outline does not expose its native component key.
        # Reconstruct the selected keys from the deterministic allocation and
        # apply the same full-card guard used by the precise-key interface.
        resolved_group_prepared = [
            item | {"component_key": allocated[int(item["ordinal"])]["component_key"]}
            for item in prepared
        ]
        _require_complete_component_groups(preflight_slide, resolved_group_prepared)
        _require_component_group_coverage(preflight_slide, resolved_group_prepared)
        _require_visual_surface_coverage(preflight_slide, resolved_group_prepared)

        for item in prepared:
            ordinal = int(item["ordinal"])
            binding = allocated[ordinal]
            fact_id = str(binding["source_fact_id"])
            facts.append({"fact_id": fact_id, "value": binding["value"]})
            output_binding = {
                "slide_id": slide_id,
                "operation": binding["operation"],
                "region_id": binding["region_id"],
                "shape_id": None,
                "fact_id": fact_id,
                "asset_id": None,
            }
            resolved_component_key = binding["component_key"]
            if resolved_component_key is None:
                resolved_component_key = next(
                    item["component_key"]
                    for item in resolved_group_prepared
                    if int(item["ordinal"]) == ordinal
                )
            if resolved_component_key is not None:
                output_binding["component_key"] = resolved_component_key
            bindings.append(output_binding)
    if locked_facts is not None:
        # The fact store is the locked customer-content ledger. A valid
        # outline may not simply omit an inconvenient conclusion or metric to
        # satisfy an attractive template: each active, source-located fact
        # must have exactly one native binding by the end of compilation.
        unbound_fact_ids = sorted(set(locked_facts).difference(seen_locked_fact_ids))
        if unbound_fact_ids:
            raise BriefBindingError(
                "LOCKED_FACT_UNBOUND:fact_ids=" + ",".join(unbound_fact_ids)
            )
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
