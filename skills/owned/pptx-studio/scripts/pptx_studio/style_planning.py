"""Deterministic, privacy-safe style-cluster planning for mixed PPTX decks.

The catalog can expose a handful of excellent candidates for a role, but a
language model should not have to solve a constrained combinatorial search:
the best-looking cover may leave no safe, high-quality compatible page for a
later role.  This module resolves that *before* an author writes a composition
request.  It returns only public IDs and aggregate evidence; it never exposes
template paths, source copy, shape geometry, preview bytes or media.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from itertools import combinations
from typing import Any

from .composition import _style_profiles_compatible
from .query import (
    _CATEGORY_ROLES,
    _SUITABILITY_PROFILES,
    _observation_for,
    _capacity,
    governed_content_slot_count,
    _suitability_safe,
    materialization_eligible,
    role_matches_page,
    style_profile_from_observation,
    style_signature_from_observation,
)
from .role_policy import minimum_distinct_client_facts
from .surface_semantics import classify_text_surface, is_sequence_date_source


class StylePlanningError(ValueError):
    """Raised when the bounded style-planning contract is malformed."""


_REQUEST_VERSION = "pptx-studio-style-cluster-request.v1"
_REQUEST_REQUIRED_FIELDS = frozenset({"schema_version", "suitability", "slides"})
_REQUEST_OPTIONAL_FIELDS = frozenset({"locked_anchor_page_id"})
_SLIDE_REQUIRED_FIELDS = frozenset({"beat_id", "role", "minimum_capacity"})
_SLIDE_OPTIONAL_FIELDS = frozenset({"content_requirements", "minimum_role_capacities", "sequence_index"})
_CONTENT_REQUIREMENT_FIELDS = frozenset({"title", "label", "metric", "body"})
_MAX_SLIDES = 24
_MAX_ANCHORS = 48
# A production deck has one anchor direction and, at most, three catalog-
# certified companion signatures. A light agenda, balanced evidence card and
# dark cadence page can all belong to one proven cool-professional system;
# colour-family, archetype and quality checks below still reject a collage.
_MAX_COMPANION_SIGNATURES = 3
_MAX_COMPANION_SIGNATURE_POOL = 6
_MAX_CANDIDATES_PER_BEAT = 48
_BEAM_WIDTH = 256
_CROSS_PACKAGE_QUALITY_FLOOR = 0.80
_STRUCTURED_DATA_ROLES = frozenset({"data", "dashboard", "table"})
# A business-model page must expose meaningful named capability/value units.
# Three or more source-character-only fragments indicate decorative numbering
# or a fragmented title lockup, not three client metrics. Selecting one would
# force a weak author either to invent one-glyph values or split a Chinese
# phrase; both are rejected later by fact binding. Keep this value-free native
# profile check in planning so the agent receives a feasible page instead.
_FRAGMENT_INTENSIVE_ROLE_BLOCKLIST = frozenset({
    "business-model", "process", "three-item", "multi-item",
})
# Upper bounds for value-free visible text skeletons.  These reject a page
# whose native composition is materially denser than the selected narrative
# role, rather than letting a weak model leave large certified visual units
# empty.  Structural pages remain unconstrained because their decorative text
# lockups are intentionally sparse and role-specific.
_MAX_VISUAL_TEXT_UNITS_BY_ROLE = {
    "one-item": 7, "two-item": 9, "three-item": 12, "four-item": 15,
    "five-item": 18, "six-item": 21, "multi-item": 28,
    "process": 16, "timeline": 18, "roadmap": 18, "comparison": 12,
    "team": 16, "business-model": 16, "case-study": 16, "risk": 16,
}
_MIN_MIXED_SOURCE_PACKAGES = 6
_MIN_MIXED_SOURCE_CATEGORIES = 5
_MAX_MIXED_PAGES_PER_SOURCE = 4
# The actual assembler checks the finished ZIP at 32 MiB. A page's recursive
# dependency closure is not the final archive: the assembled OPC package also
# needs slide records, relationship parts and package-level registrations.
# Reserve a real margin rather than allowing a 40 MiB closure to reach a
# predictable late release failure. This remains a planning ceiling; the
# final physical ZIP gate is authoritative.
_MAX_ESTIMATED_DEPENDENCY_BYTES = 32 * 1024 * 1024
_REUSABLE_PAGE_ROLES = frozenset({
    "one-item", "two-item", "three-item", "four-item", "five-item",
    "six-item", "multi-item", "comparison", "case-study", "process", "risk",
})
_MAX_CONTENT_REUSE_PER_PAGE = 2
_CARD_LAYOUT_ROLES = frozenset({"three-item", "risk"})
_MAX_SHARED_CARD_LAYOUT_INSTANCES = 3
_MAX_SECTION_REUSE_PER_PAGE = 4
_MAX_REUSE_PER_PAGE = max(_MAX_CONTENT_REUSE_PER_PAGE, _MAX_SECTION_REUSE_PER_PAGE)
_STRUCTURAL_QUALITY_FLOOR = 0.78


def _max_reused_page_instances(slide_count: int) -> int:
    """Bound repetition to a rare, deliberate fallback in substantive decks."""

    return 0 if slide_count < 10 else max(1, slide_count // 20)


def _shared_card_layout(roles: set[str]) -> bool:
    """Allow a bounded third use of one complete three-card grammar.

    A solution, benefit and risk page can all truthfully require the same
    title + three label/body-card grammar. Reusing one high-quality native
    page on those non-adjacent beats is preferable to admitting an unrelated
    low-quality page solely to manufacture variety. The binder still requires
    every label/body surface to be client-grounded.
    """

    return bool(roles) and roles.issubset(_CARD_LAYOUT_ROLES)


def _validate_request(request: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]], str | None]:
    if (
        not _REQUEST_REQUIRED_FIELDS.issubset(request)
        or not set(request).issubset(_REQUEST_REQUIRED_FIELDS | _REQUEST_OPTIONAL_FIELDS)
        or request.get("schema_version") != _REQUEST_VERSION
    ):
        raise StylePlanningError("STYLE_CLUSTER_REQUEST_INVALID")
    suitability = request.get("suitability")
    if suitability not in _SUITABILITY_PROFILES:
        raise StylePlanningError("SUITABILITY_INVALID")
    slides = request.get("slides")
    if not isinstance(slides, list) or not 1 <= len(slides) <= _MAX_SLIDES:
        raise StylePlanningError("STYLE_CLUSTER_SLIDES_INVALID")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    seen_sequence_indices: set[int] = set()
    for item in slides:
        if (
            not isinstance(item, Mapping)
            or not _SLIDE_REQUIRED_FIELDS.issubset(item)
            or not set(item).issubset(_SLIDE_REQUIRED_FIELDS | _SLIDE_OPTIONAL_FIELDS)
        ):
            raise StylePlanningError("STYLE_CLUSTER_SLIDE_INVALID")
        beat_id, role, minimum_capacity = item.get("beat_id"), item.get("role"), item.get("minimum_capacity")
        if not isinstance(beat_id, str) or not beat_id or beat_id in seen:
            raise StylePlanningError("STYLE_CLUSTER_BEAT_INVALID")
        if not isinstance(role, str) or not role:
            raise StylePlanningError("STYLE_CLUSTER_ROLE_INVALID")
        # v1 describes a fact/text-backed selection only. A true trend,
        # dashboard or table must be selected by the later structured-data
        # contract, which declares every native chart/table value. Requiring
        # the author to reframe here is safer than allowing a few headline
        # figures to masquerade as a governed dataset.
        if role in _STRUCTURED_DATA_ROLES:
            raise StylePlanningError("STYLE_CLUSTER_STRUCTURED_DATA_ROLE_REQUIRES_CONTRACT")
        if type(minimum_capacity) is not int or minimum_capacity < 0:
            raise StylePlanningError("STYLE_CLUSTER_CAPACITY_INVALID")
        sequence_index = item.get("sequence_index", len(result))
        if (
            type(sequence_index) is not int
            or sequence_index < 0
            or sequence_index in seen_sequence_indices
            or (result and sequence_index <= result[-1]["sequence_index"])
        ):
            raise StylePlanningError("STYLE_CLUSTER_SEQUENCE_INDEX_INVALID")
        content_requirements = item.get("content_requirements")
        if content_requirements is None:
            normalized_requirements: dict[str, int] = {}
        elif (
            not isinstance(content_requirements, Mapping)
            or not set(content_requirements).issubset(_CONTENT_REQUIREMENT_FIELDS)
            or not content_requirements
            or any(type(value) is not int or value < 0 for value in content_requirements.values())
        ):
            raise StylePlanningError("STYLE_CLUSTER_CONTENT_REQUIREMENTS_INVALID")
        else:
            normalized_requirements = {
                str(name): int(value)
                for name, value in content_requirements.items()
                if int(value) > 0
            }
        role_capacities = item.get("minimum_role_capacities")
        if role_capacities is None:
            normalized_role_capacities: dict[str, int] = {}
        elif (
            not isinstance(role_capacities, Mapping)
            or not set(role_capacities).issubset(_CONTENT_REQUIREMENT_FIELDS)
            or not role_capacities
            or any(type(value) is not int or value < 1 for value in role_capacities.values())
        ):
            raise StylePlanningError("STYLE_CLUSTER_ROLE_CAPACITIES_INVALID")
        else:
            normalized_role_capacities = {
                str(name): int(value) for name, value in role_capacities.items()
            }
        # Ordered pages have a stronger contract than a generic card count.
        # ``minimum_capacity`` is the title plus the number of complete
        # source-grounded units.  Letting an author state ``timeline: 4`` for
        # four date/action pairs used to make the candidate matcher search for
        # a three-step source page (it subtracts the title internally).  The
        # resulting NO_MATCH looked like a library gap even though the request
        # itself was semantically inconsistent.  Make the relationship
        # executable before catalog selection, where a weaker model receives a
        # direct repair code rather than a misleading retrieval failure.
        if role in {"timeline", "roadmap", "process"} and content_requirements is not None:
            label_count = normalized_requirements.get("label", 0)
            body_count = normalized_requirements.get("body", 0)
            title_count = normalized_requirements.get("title", 0)
            if label_count < 1 or body_count < 1 or label_count != body_count:
                raise StylePlanningError("STYLE_CLUSTER_SEQUENCE_PAIR_REQUIREMENTS_INVALID")
            if title_count != 1:
                raise StylePlanningError("STYLE_CLUSTER_SEQUENCE_TITLE_REQUIREMENT_INVALID")
            expected_capacity = label_count + 1
            if minimum_capacity != expected_capacity:
                raise StylePlanningError(
                    "STYLE_CLUSTER_SEQUENCE_CAPACITY_INVALID"
                    f":expected={expected_capacity}:actual={minimum_capacity}"
                )
        seen.add(beat_id)
        seen_sequence_indices.add(sequence_index)
        result.append({
            "beat_id": beat_id, "role": role, "minimum_capacity": minimum_capacity,
            "content_requirements": normalized_requirements,
            "minimum_role_capacities": normalized_role_capacities,
            "sequence_index": sequence_index,
        })
    if result[0]["role"] != "cover":
        raise StylePlanningError("STYLE_CLUSTER_COVER_FIRST_REQUIRED")
    locked_anchor_page_id = request.get("locked_anchor_page_id")
    if locked_anchor_page_id is not None and (not isinstance(locked_anchor_page_id, str) or not locked_anchor_page_id):
        raise StylePlanningError("STYLE_CLUSTER_LOCKED_ANCHOR_INVALID")
    return str(suitability), result, locked_anchor_page_id


def _public_candidate(page: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    render = page.get("render")
    quality = render.get("visual_quality") if isinstance(render, Mapping) else 0.0
    materialization = page.get("materialization")
    dependency_bytes = (
        materialization.get("dependency_bytes", 0)
        if isinstance(materialization, Mapping) else 0
    )
    if type(dependency_bytes) is not int or dependency_bytes < 0:
        raise StylePlanningError("STYLE_CLUSTER_DEPENDENCY_BUDGET_INVALID")
    fragment_slot_count = (
        materialization.get("fragment_slot_count", 0)
        if isinstance(materialization, Mapping) else 0
    )
    if type(fragment_slot_count) is not int or fragment_slot_count < 0:
        raise StylePlanningError("STYLE_CLUSTER_FRAGMENT_PROFILE_INVALID")
    visual_text_unit_count = (
        materialization.get("visual_text_unit_count", 0)
        if isinstance(materialization, Mapping) else 0
    )
    if type(visual_text_unit_count) is not int or visual_text_unit_count < 0:
        raise StylePlanningError("STYLE_CLUSTER_VISUAL_SKELETON_INVALID")
    return {
        "page_id": str(page.get("page_id")),
        "deck_id": str(page.get("deck_id")),
        "package_sha256": str(page.get("package_sha256")),
        "category": str(page.get("category")),
        "style_signature": style_signature_from_observation(observation),
        "style_profile": style_profile_from_observation(observation),
        "page_visual_quality": float(quality) if isinstance(quality, (int, float)) else 0.0,
        "capacity": _capacity(page, None),
        "dependency_bytes": dependency_bytes,
        "fragment_slot_count": fragment_slot_count,
        "visual_text_unit_count": visual_text_unit_count,
    }


def _binding_surface_profile(page: Mapping[str, Any], *, role: str) -> dict[str, Any]:
    """Compile the preflight-compatible surface facts needed before selection."""

    counts = {name: 0 for name in ("title", "label", "metric", "body")}
    maximum_capacities = {name: 0 for name in counts}
    maximum_title_capacity = 0
    maximum_statement_capacity = 0
    sequence_date_count = 0
    for shape in page.get("shapes", []):
        if (
            not isinstance(shape, Mapping)
            or shape.get("kind") != "text"
            or not isinstance(shape.get("text"), str)
            or not shape["text"].strip()
        ):
            continue
        semantic_role = shape.get("semantic_role")
        # Fragment lockups are grouped into opaque title regions by physical
        # preflight. Counting each character here would overstate the number
        # of independently bindable client surfaces.
        if semantic_role in {"title_fragment", "label_fragment"}:
            continue
        binding_role = classify_text_surface(
            text=shape["text"],
            semantic_role=str(semantic_role) if isinstance(semantic_role, str) else None,
            bbox=shape.get("bbox") if isinstance(shape.get("bbox"), Mapping) else {},
            declared_role=role,
        )
        if binding_role in counts:
            counts[binding_role] += 1
            maximum_capacities[binding_role] = max(
                maximum_capacities[binding_role],
                int(shape.get("max_chars", 0)) if type(shape.get("max_chars")) is int else 0,
            )
            if binding_role in {"title", "label", "body"}:
                maximum_statement_capacity = max(
                    maximum_statement_capacity,
                    int(shape.get("max_chars", 0)) if type(shape.get("max_chars")) is int else 0,
                )
            if binding_role == "title":
                maximum_title_capacity = max(
                    maximum_title_capacity,
                    int(shape.get("max_chars", 0)) if type(shape.get("max_chars")) is int else 0,
                )
        if role in {"timeline", "roadmap"} and is_sequence_date_source(shape["text"]):
            sequence_date_count += 1
    return {
        "binding_role_counts": counts,
        "binding_role_maximum_capacities": maximum_capacities,
        "published_surface_count": sum(counts.values()),
        "maximum_title_capacity": maximum_title_capacity,
        "maximum_statement_capacity": maximum_statement_capacity,
        "sequence_milestone_count": sequence_date_count,
    }


def _surface_contract_safe(
    candidate: Mapping[str, Any], *, role: str, minimum_capacity: int,
    content_requirements: Mapping[str, int] | None = None,
    minimum_role_capacities: Mapping[str, int] | None = None,
) -> bool:
    profile = candidate["surface_profile"]
    counts = profile["binding_role_counts"]
    published = int(profile["published_surface_count"])

    # Synthetic/legacy catalogs without native text records retain their
    # historical deterministic behavior. Production catalogs always publish
    # shape text, so they cannot bypass the surface contract this way.
    if published == 0:
        return True

    # A cardinality adaptation is not a generic surface-count escape hatch.
    # It is an opaque page/role/capacity entitlement created only by the
    # private, hash-bound physical adapter. The later native preflight and
    # disposable physical probe still prove the effective groups and client
    # copy. Here it prevents the solver from judging a certified four-node
    # adaptation by its unadapted five-node source profile.
    if candidate.get("certified_sequence_cardinality_adaptation") is True:
        return (
            role in {"timeline", "roadmap"}
            and int(counts["title"]) >= 1
            and int(profile["maximum_title_capacity"]) >= minimum_capacity
            and int(candidate["capacity"]) >= minimum_capacity
        )

    # Optional fact-derived surface minima move a late binding failure into
    # candidate selection. The planner still sees only role counts, never
    # customer copy, coordinates or source text. A requirement for five bodies
    # therefore rules out a visually attractive four-card page before an
    # ordinary model can attempt to squeeze a conclusion into a caption.
    for surface_role, required_count in (content_requirements or {}).items():
        if int(counts.get(surface_role, 0)) < required_count:
            return False
    maximum_capacities = profile["binding_role_maximum_capacities"]
    for surface_role, required_capacity in (minimum_role_capacities or {}).items():
        if int(maximum_capacities.get(surface_role, 0)) < required_capacity:
            return False

    # Cover capacity is a title-character contract, not a fact-count budget.
    if role == "cover":
        return True
    # A structural divider owns one source-grounded heading. Selecting a
    # content-heavy page and moving evidence into it destroys both the chapter
    # rhythm and fact ownership, even if the binder could technically fill it.
    if role == "section":
        return (
            int(counts["title"]) >= 1
            and int(profile["maximum_title_capacity"]) >= minimum_capacity
            and published <= 2
        )
    # A closing owns one complete, source-grounded approval request or final
    # takeaway. It must fit one native title surface: facts are atomic and may
    # not be split over decorative title/label lockups just to make a narrow
    # template appear usable. Like sections, its request capacity is an actual
    # character contract, not a count of one fact.
    if role == "closing":
        # ``role_matches_page`` permits a quote page here only after an
        # independent quote observation. Its hero statement is often
        # classified as a label by spatial semantics, so the complete CTA may
        # occupy that one long certified statement surface. A dedicated
        # closing page remains title-only and cannot use this exception.
        if candidate.get("category") == "053-金句模板":
            return (
                int(profile["maximum_statement_capacity"]) >= minimum_capacity
                and published <= 2
            )
        return (
            int(counts["title"]) >= 1
            and int(profile["maximum_title_capacity"]) >= minimum_capacity
            and published <= 2
        )

    # Binding requires at least half of published text surfaces to be grounded.
    # The style request's capacity is the number of truthful content units; the
    # role floor accounts for mandatory titles and paired fields where needed.
    available_fact_floor = max(minimum_distinct_client_facts(role), minimum_capacity)
    if published > 2 * available_fact_floor:
        return False

    if role in {"timeline", "roadmap"}:
        # The deterministic role ladder defines capacity as one page title plus
        # N source-dated milestones. Physical preflight publishes every native
        # milestone as one required date/action group, so the counts must match
        # exactly rather than inviting a fabricated fifth milestone.
        expected = max(0, minimum_capacity - 1)
        return int(profile["sequence_milestone_count"]) == expected
    if role == "risk":
        # Risk records are complete source-backed statements, not short card
        # captions. A compatible detail page needs one heading and a readable
        # body surface for each listed risk.
        return int(counts["title"]) >= 1 and int(counts["body"]) >= minimum_capacity
    if role == "process":
        expected = max(0, minimum_capacity - 1)
        return (
            int(counts["title"]) >= 1
            and int(counts["label"]) == expected
            and int(counts["body"]) == expected
        )
    return True


def _eligible_candidates(
    catalog: Mapping[str, Any],
    observations: Mapping[str, Mapping[str, Any]],
    *,
    slide: Mapping[str, Any],
    suitability: str,
    sequence_cardinality_adaptation_keys: Collection[tuple[str, str, int]] = (),
) -> list[dict[str, Any]]:
    active = set(catalog.get("active_categories", []))
    region_counts: dict[str, int] = {}
    for region in catalog.get("regions", []):
        if isinstance(region, Mapping):
            page_id = region.get("page_id")
            if isinstance(page_id, str):
                region_counts[page_id] = region_counts.get(page_id, 0) + 1
    role = str(slide["role"])
    candidates: list[dict[str, Any]] = []
    for page in catalog.get("pages", []):
        if (
            not isinstance(page, Mapping)
            or page.get("category") not in active
            or page.get("component_only") is True
            or not materialization_eligible(page)
        ):
            continue
        observation = _observation_for(page, observations)
        if observation is None or not _suitability_safe(observation, profile=suitability):
            continue
        if not role_matches_page(page, observation, role):
            continue
        page_id = str(page.get("page_id"))
        if region_counts.get(page_id, 0) < minimum_distinct_client_facts(role):
            continue
        candidate = _public_candidate(page, observation)
        candidate["role"] = role
        candidate["surface_profile"] = _binding_surface_profile(page, role=role)
        candidate["certified_sequence_cardinality_adaptation"] = (
            page_id, role, int(slide["minimum_capacity"]),
        ) in sequence_cardinality_adaptation_keys
        if (
            role in _FRAGMENT_INTENSIVE_ROLE_BLOCKLIST
            and int(candidate["fragment_slot_count"]) >= 3
        ):
            continue
        maximum_visual_units = _MAX_VISUAL_TEXT_UNITS_BY_ROLE.get(role)
        if maximum_visual_units is not None and int(candidate["visual_text_unit_count"]) > maximum_visual_units:
            continue
        if not _surface_contract_safe(
            candidate,
            role=role,
            minimum_capacity=int(slide["minimum_capacity"]),
            content_requirements=slide.get("content_requirements"),
            minimum_role_capacities=slide.get("minimum_role_capacities"),
        ):
            continue
        # A cover's visual title cannot use total page text capacity: it must
        # fit one certified native title region. The author supplies its exact
        # source-grounded visual-title length as minimum_capacity; the full
        # formal title may separately occupy an ordinary certified body/label
        # surface when the selected cover exposes one.
        if role == "cover":
            page_regions = [
                region for region in catalog.get("regions", [])
                if isinstance(region, Mapping) and region.get("page_id") == page_id
            ]
            title_capacities = [
                int(region.get("capacity", {}).get("max_text_chars", 0))
                for region in page_regions
                if region.get("region_kind") == "title"
                and isinstance(region.get("capacity"), Mapping)
            ]
            # Legacy synthetic catalogs with no region inventory cannot claim
            # a title semantic. Keep them testable through the same single
            # shape capacity used by earlier releases; compiled production
            # catalogs always have regions and therefore never take this path.
            if not page_regions or not any("region_kind" in region for region in page_regions):
                title_capacities = [
                    int(shape.get("max_chars", 0))
                    for shape in page.get("shapes", [])
                    if isinstance(shape, Mapping)
                ]
            # The catalog records a fragment lockup as its individually
            # editable letters.  Its per-letter regions are intentionally
            # narrower than the certified native title surface discovered
            # from the slide text.  Prefer neither representation blindly:
            # use their conservative published maximum and retain physical
            # preflight as the authoritative final binding/capacity gate.
            title_capacities.append(
                int(candidate["surface_profile"]["maximum_title_capacity"])
            )
            if max(title_capacities, default=0) < int(slide["minimum_capacity"]):
                continue
        # A native chart/table/workbook is not a decorative page. This v1
        # request carries no complete structured-data contract, so selecting
        # one would merely defer an inevitable compiler rejection (or tempt an
        # author to retain sample values). A later explicit data-planning
        # contract may opt such pages in; this safe default cannot.
        if governed_content_slot_count(page) > 0:
            continue
        if candidate["capacity"] < int(slide["minimum_capacity"]):
            continue
        candidates.append(candidate)
    # Prefer canonical categories, visual quality and spare native capacity.
    # This is a deterministic tie-breaker, not a model-owned aesthetic score.
    canonical = _CATEGORY_ROLES.get
    candidates.sort(key=lambda item: (
        -int(role in canonical(item["category"], frozenset())),
        -item["page_visual_quality"],
        -item["capacity"],
        item["page_id"],
    ))
    return candidates


def _compatible_signature_sets(
    anchor: Mapping[str, Any], candidates_by_beat: list[list[dict[str, Any]]],
) -> list[tuple[str, ...]]:
    """Return deterministic certified companion sets, smallest first.

    A single compatible companion is preferred. Two are considered only after
    all one-signature options, and each independently satisfies the anchor
    profile rule. The pool is intentionally bounded so this remains a
    predictable feasibility solver rather than open-ended visual search.
    """
    anchor_signature = str(anchor["style_signature"])
    anchor_profile = anchor["style_profile"]
    frequencies: dict[str, int] = {}
    sample: dict[str, Mapping[str, Any]] = {}
    for candidates in candidates_by_beat:
        for candidate in candidates:
            signature = str(candidate["style_signature"])
            if signature == anchor_signature:
                continue
            if not _style_profiles_compatible(anchor_profile, candidate["style_profile"]):
                continue
            frequencies[signature] = frequencies.get(signature, 0) + 1
            sample.setdefault(signature, candidate)
    ordered = sorted(
        frequencies,
        key=lambda signature: (-frequencies[signature], -float(sample[signature]["page_visual_quality"]), signature),
    )[:_MAX_COMPANION_SIGNATURE_POOL]
    # Include every bounded cardinality.  The former two-signature limit made
    # singleton plus exactly-two sufficient; with three permitted companions,
    # omitting pairs incorrectly rejects otherwise coherent small cadences.
    return [()] + [
        combination
        for size in range(1, _MAX_COMPANION_SIGNATURES + 1)
        for combination in combinations(ordered, size)
    ]


def _eligible_for_cluster(
    candidate: Mapping[str, Any], *, anchor: Mapping[str, Any], companion_signatures: frozenset[str],
) -> bool:
    quality_floor = (
        _STRUCTURAL_QUALITY_FLOOR
        if candidate.get("role") == "section"
        else _CROSS_PACKAGE_QUALITY_FLOOR
    )
    if float(candidate["page_visual_quality"]) < quality_floor:
        return False
    # A certified complete-work family may legitimately use several page-level
    # signatures while retaining one native master/palette/grid. It receives
    # the family compatibility exemption only after passing the page-quality
    # floor above.
    if candidate["deck_id"] == anchor["deck_id"]:
        return True
    signature = str(candidate["style_signature"])
    if signature != anchor["style_signature"] and signature not in companion_signatures:
        return False
    return True


def _state_score(state: Mapping[str, Any]) -> tuple[float, int, int, int, float, tuple[str, ...]]:
    # Satisfaction of the eventual provenance floor dominates quality. It
    # makes a rule-compliant multi-package deck the default rather than a
    # single reference deck with cosmetic alternates.
    packages = state["packages"]
    categories = state["categories"]
    return (
        float(state["quality"]) + 3.0 * len(packages) + 1.5 * len(categories)
        - 2.0 * int(state["reused_page_instances"])
        - float(state["dependency_bytes"]) / (8 * 1024 * 1024),
        len(packages), len(categories), -max(packages.values(), default=0),
        -float(state["dependency_bytes"]),
        tuple(state["selected"]),
    )


def _search_selection(
    slides: list[dict[str, Any]], candidates_by_beat: list[list[dict[str, Any]]], *,
    anchor: dict[str, Any], companion_signatures: frozenset[str],
) -> list[dict[str, Any]] | None:
    # Preserve client narrative order in the result but use the smallest
    # candidate domain first while solving, making the bounded search robust.
    domains: list[list[dict[str, Any]]] = []
    for index, candidates in enumerate(candidates_by_beat):
        allowed = [
            item for item in candidates
            if _eligible_for_cluster(item, anchor=anchor, companion_signatures=companion_signatures)
        ]
        if index == 0:
            allowed = [item for item in allowed if item["page_id"] == anchor["page_id"]]
        if not allowed:
            return None
        domains.append(allowed[:_MAX_CANDIDATES_PER_BEAT])
    order = sorted(range(len(slides)), key=lambda index: (len(domains[index]), index))
    states: list[dict[str, Any]] = [{
        "selected": [""] * len(slides), "page_counts": {}, "page_roles": {},
        "packages": {}, "categories": set(), "quality": 0.0,
        "dependency_bytes": 0, "reused_page_instances": 0,
        "content_reused_page_instances": 0,
        "shared_card_reused_page_instances": 0,
    }]
    for index in order:
        next_states: list[dict[str, Any]] = []
        for state in states:
            for candidate in domains[index]:
                page_id, package = candidate["page_id"], candidate["package_sha256"]
                page_count = int(state["page_counts"].get(page_id, 0))
                repeated = page_count > 0
                role = slides[index]["role"]
                prior_role = state["page_roles"].get(page_id)
                shared_card_layout = _shared_card_layout({role, prior_role}) if isinstance(prior_role, str) else False
                reuse_limit = (
                    _MAX_SECTION_REUSE_PER_PAGE
                    if role == "section"
                    else _MAX_SHARED_CARD_LAYOUT_INSTANCES
                    if shared_card_layout
                    else _MAX_CONTENT_REUSE_PER_PAGE
                    if role in _REUSABLE_PAGE_ROLES
                    else 1
                )
                sequence_index = int(slides[index].get("sequence_index", index))
                adjacent_repeat = repeated and any(
                    selected_page_id == page_id
                    and abs(sequence_index - int(slides[other_index].get("sequence_index", other_index))) == 1
                    for other_index, selected_page_id in enumerate(state["selected"])
                )
                if (
                    page_count >= reuse_limit
                    or adjacent_repeat
                    or (
                        repeated
                        and role != "section"
                        and (
                            role not in _REUSABLE_PAGE_ROLES
                            or (state["page_roles"].get(page_id) != role and not shared_card_layout)
                            or (
                                int(state["shared_card_reused_page_instances"])
                                if shared_card_layout
                                else int(state["content_reused_page_instances"])
                            )
                            >= (
                                _max_reused_page_instances(len(slides)) + 1
                                if shared_card_layout
                                else _max_reused_page_instances(len(slides))
                            )
                        )
                    )
                    or state["packages"].get(package, 0) >= _MAX_MIXED_PAGES_PER_SOURCE
                ):
                    continue
                dependency_bytes = int(state["dependency_bytes"]) + int(candidate["dependency_bytes"])
                if len(slides) >= 10 and dependency_bytes > _MAX_ESTIMATED_DEPENDENCY_BYTES:
                    continue
                next_state = {
                    "selected": list(state["selected"]),
                    "page_counts": dict(state["page_counts"]),
                    "page_roles": dict(state["page_roles"]),
                    "packages": dict(state["packages"]),
                    "categories": set(state["categories"]),
                    "quality": float(state["quality"]) + float(candidate["page_visual_quality"]),
                    "dependency_bytes": dependency_bytes,
                    "reused_page_instances": int(state["reused_page_instances"]) + int(repeated),
                    "content_reused_page_instances": int(state["content_reused_page_instances"]) + int(
                        repeated and role != "section" and not shared_card_layout
                    ),
                    "shared_card_reused_page_instances": int(state["shared_card_reused_page_instances"]) + int(
                        repeated and shared_card_layout
                    ),
                }
                next_state["selected"][index] = page_id
                next_state["page_counts"][page_id] = page_count + 1
                next_state["page_roles"].setdefault(page_id, slides[index]["role"])
                next_state["packages"][package] = next_state["packages"].get(package, 0) + 1
                next_state["categories"].add(candidate["category"])
                next_states.append(next_state)
        if not next_states:
            return None
        next_states.sort(key=_state_score, reverse=True)
        states = next_states[:_BEAM_WIDTH]
    for state in sorted(states, key=_state_score, reverse=True):
        total = len(slides)
        if total >= 10 and (
            len(state["packages"]) < _MIN_MIXED_SOURCE_PACKAGES
            or len(state["categories"]) < _MIN_MIXED_SOURCE_CATEGORIES
        ):
            continue
        repeated_positions: dict[str, list[int]] = {}
        for index, page_id in enumerate(state["selected"]):
            repeated_positions.setdefault(page_id, []).append(index)
        if any(
            len(positions) > (
                _MAX_SECTION_REUSE_PER_PAGE
                if {slides[index]["role"] for index in positions} == {"section"}
                else _MAX_SHARED_CARD_LAYOUT_INSTANCES
                if _shared_card_layout({slides[index]["role"] for index in positions})
                else _MAX_CONTENT_REUSE_PER_PAGE
                if {slides[index]["role"] for index in positions}.issubset(_REUSABLE_PAGE_ROLES)
                else 1
            )
            or any(
                int(slides[right].get("sequence_index", right))
                - int(slides[left].get("sequence_index", left)) == 1
                for left, right in zip(positions, positions[1:])
            )
            for page_id, positions in repeated_positions.items()
        ):
            continue
        selected_by_id = {
            candidate["page_id"]: candidate
            for candidates in domains for candidate in candidates
        }
        return [selected_by_id[page_id] for page_id in state["selected"]]
    return None


def plan_style_cluster(
    catalog: Mapping[str, Any], *, observations: Mapping[str, Mapping[str, Any]],
    request: Mapping[str, Any],
    sequence_cardinality_adaptation_keys: Collection[tuple[str, str, int]] = (),
) -> dict[str, Any]:
    """Return one compiler-feasible, safe physical-page selection.

    The returned selection is intentionally exact. An agent can decide the
    narrative grammar, but it cannot accidentally combine individually valid
    candidates into a plan the composition compiler must reject later.
    """

    suitability, slides, locked_anchor_page_id = _validate_request(request)
    candidates_by_beat = [
        _eligible_candidates(
            catalog, observations, slide=slide, suitability=suitability,
            sequence_cardinality_adaptation_keys=sequence_cardinality_adaptation_keys,
        )
        for slide in slides
    ]
    if any(not candidates for candidates in candidates_by_beat):
        missing = [slides[index]["beat_id"] for index, candidates in enumerate(candidates_by_beat) if not candidates]
        return {
            "schema_version": "pptx-studio-style-cluster-plan.v1", "status": "NO_MATCH",
            "code": "STYLE_CLUSTER_ROLE_NO_MATCH", "missing_beat_ids": missing,
        }

    # Distinguish a real library-quality gap from a cross-style combinatorial
    # failure.  The latter can be recovered by another compatible anchor or a
    # bounded component fallback; the former has no whole-page candidate that
    # can legally enter any production cluster.  Returning the affected beats
    # lets the weak-model workflow use components only for named
    # non-structural gaps while it correctly stops for a cover/contents/
    # section/closing asset that must be curated.
    quality_missing = [
        slides[index]["beat_id"]
        for index, candidates in enumerate(candidates_by_beat)
        if not any(
            float(candidate["page_visual_quality"]) >= (
                _STRUCTURAL_QUALITY_FLOOR
                if slides[index]["role"] == "section"
                else _CROSS_PACKAGE_QUALITY_FLOOR
            )
            for candidate in candidates
        )
    ]
    if quality_missing:
        return {
            "schema_version": "pptx-studio-style-cluster-plan.v1", "status": "NO_MATCH",
            "code": "STYLE_CLUSTER_ROLE_NO_MATCH", "missing_beat_ids": quality_missing,
        }
    anchors = candidates_by_beat[0][:_MAX_ANCHORS]
    if locked_anchor_page_id is not None:
        anchors = [item for item in anchors if item["page_id"] == locked_anchor_page_id]
        if not anchors:
            return {
                "schema_version": "pptx-studio-style-cluster-plan.v1", "status": "NO_MATCH",
                "code": "STYLE_CLUSTER_LOCKED_ANCHOR_NO_MATCH", "missing_beat_ids": [slides[0]["beat_id"]],
            }
    for anchor in anchors:
        for companion_signature_set in _compatible_signature_sets(anchor, candidates_by_beat):
            selected = _search_selection(
                slides,
                candidates_by_beat,
                anchor=anchor,
                companion_signatures=frozenset(companion_signature_set),
            )
            if selected is None:
                continue
            package_counts: dict[str, int] = {}
            categories: set[str] = set()
            anchor_count = 0
            for candidate in selected:
                package = str(candidate["package_sha256"])
                package_counts[package] = package_counts.get(package, 0) + 1
                categories.add(str(candidate["category"]))
                if candidate["deck_id"] == anchor["deck_id"] or _style_profiles_compatible(
                    anchor["style_profile"], candidate["style_profile"],
                ):
                    anchor_count += 1
            if len(selected) >= 10 and anchor_count / len(selected) < 0.70:
                # Keep searching rather than returning a plan which the
                # composition coverage gate would correctly reject.
                continue
            allowed = [str(anchor["style_signature"]), *companion_signature_set]
            return {
                "schema_version": "pptx-studio-style-cluster-plan.v1",
                "status": "PASS",
                "art_direction": {
                    "anchor_page_id": anchor["page_id"],
                    "allowed_style_signatures": allowed,
                    "suitability": suitability,
                },
                "recommended_slides": [
                    {
                        "beat_id": slides[index]["beat_id"], "role": slides[index]["role"],
                        "minimum_capacity": slides[index]["minimum_capacity"],
                        "selected_candidate_id": candidate["page_id"],
                        # Exact by design: composition must not become a
                        # second, model-driven combinatorial search.
                        "candidate_ids": [candidate["page_id"]],
                        "page_visual_quality": round(float(candidate["page_visual_quality"]), 6),
                    }
                    for index, candidate in enumerate(selected)
                ],
                "evidence": {
                    "source_package_count": len(package_counts),
                    "source_category_count": len(categories),
                    "maximum_pages_from_one_source": max(package_counts.values()),
                    "reused_page_instance_count": len(selected) - len({item["page_id"] for item in selected}),
                    "maximum_reuse_per_page": _MAX_REUSE_PER_PAGE,
                    "anchor_cluster_coverage": round(anchor_count / len(selected), 6),
                    "cross_package_quality_floor": _CROSS_PACKAGE_QUALITY_FLOOR,
                    "estimated_dependency_bytes": sum(
                        int(candidate["dependency_bytes"]) for candidate in selected
                    ),
                    "maximum_estimated_dependency_bytes": _MAX_ESTIMATED_DEPENDENCY_BYTES,
                },
            }
    return {
        "schema_version": "pptx-studio-style-cluster-plan.v1", "status": "NO_MATCH",
        "code": "STYLE_CLUSTER_FEASIBILITY_NO_MATCH",
        "missing_beat_ids": [],
    }
