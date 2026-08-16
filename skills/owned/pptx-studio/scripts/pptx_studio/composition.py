"""Deterministic whole-deck/page/component composition over the curated catalog."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .component_profiles import ComponentProfileError, ComponentProfileIndex
from .query import (
    _SUITABILITY_PROFILES,
    _suitability_safe,
    governed_content_slot_count,
    materialization_eligible,
    role_matches_page,
    style_profile_from_observation,
    style_signature_from_observation,
)
from .role_policy import minimum_distinct_client_facts
from .structured_data import contract_for_source


class CompositionError(ValueError):
    """Raised when an agent intent exceeds governed composition authority."""


_STRATEGIES = frozenset({"exact_deck", "family_assembly", "page_assembly", "component_assembly"})
_REQUEST_FIELDS_V1 = frozenset({"schema_version", "strategy", "art_direction", "slides"})
_REQUEST_FIELDS_V2 = _REQUEST_FIELDS_V1 | {"narrative_validation"}
_REQUEST_FIELDS_V3 = _REQUEST_FIELDS_V2 | {"component_profile"}
_REQUEST_FIELDS_V4 = _REQUEST_FIELDS_V3
_ART_FIELDS = frozenset({"anchor_page_id", "allowed_style_signatures", "suitability"})
_SLIDE_FIELDS_V1 = frozenset({"slide_id", "role", "candidate_ids", "selected_candidate_id", "minimum_capacity"})
_SLIDE_FIELDS_V2 = _SLIDE_FIELDS_V1 | {"beat_id"}
_COMPONENT_SLIDE_FIELDS_V3 = frozenset({
    "slide_id", "beat_id", "role", "host_candidate_ids",
    "selected_host_candidate_id", "host_anchor_id", "selected_component_ids",
    "minimum_capacity",
})
_COMPONENT_PLACEMENT_FIELDS_V4 = frozenset({"host_anchor_id", "component_id"})
_COMPONENT_SLIDE_FIELDS_V4 = frozenset({
    "slide_id", "beat_id", "role", "host_candidate_ids",
    "selected_host_candidate_id", "component_placements", "minimum_capacity",
})
_COMPONENT_PROFILE_FIELDS = frozenset({"profile_id", "profile_sha256"})
_NARRATIVE_VALIDATION_FIELDS = frozenset({
    "schema_version", "status", "brief_id", "brief_sha256", "narrative_sha256",
    "slide_count", "delivery_beat_ids", "section_evidence",
})
_REPLAY_LOCK_FIELDS = frozenset({
    "schema_version", "catalog_sha256", "observations_sha256", "compiler_sha256",
    "narrative_sha256",
})
_REUSABLE_PAGE_ROLES = frozenset({
    "one-item", "two-item", "three-item", "four-item", "five-item",
    "six-item", "multi-item", "comparison", "case-study", "process", "risk",
})
_MAX_CONTENT_REUSE_PER_PAGE = 2
_CARD_LAYOUT_ROLES = frozenset({"three-item", "risk"})
_MAX_SHARED_CARD_LAYOUT_INSTANCES = 3
_MAX_SECTION_REUSE_PER_PAGE = 4
# A component host is not a replayed complete page. Two non-adjacent uses are
# permitted only when the selected certified components differ globally.
_MAX_COMPONENT_HOST_REUSE_PER_PAGE = 2
_PAGE_VISUAL_QUALITY_FLOOR = 0.80
_SECTION_VISUAL_QUALITY_FLOOR = 0.78


def _max_reused_page_instances(slide_count: int) -> int:
    return 0 if slide_count < 10 else max(1, slide_count // 20)


def _shared_card_layout(roles: set[str]) -> bool:
    return bool(roles) and roles.issubset(_CARD_LAYOUT_ROLES)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def serialize_composition_plan(plan: Mapping[str, Any]) -> str:
    """Serialize a validated plan deterministically for later plan binding."""

    return _canonical_json(plan)


def composition_plan_sha256(plan: Mapping[str, Any]) -> str:
    return hashlib.sha256(serialize_composition_plan(plan).encode("utf-8")).hexdigest()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _compiler_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def verify_composition_replay_lock(
    plan: Mapping[str, Any],
    *,
    catalog: Mapping[str, Any],
    observations: Mapping[str, Mapping[str, Any]] | None = None,
    component_profiles: ComponentProfileIndex | None = None,
) -> None:
    """Fail closed when a v2 plan is replayed under different inputs/code.

    Downstream physical assembly has no reason to reinterpret a selection
    under a changed catalog/compiler.  Observation index verification is done
    whenever it is available (composition and the explicit replay command);
    catalog/compiler verification is repeated by preflight/adaptation.
    """

    if plan.get("schema_version") == "1.0":
        return
    if plan.get("schema_version") not in {"2.0", "3.0", "4.0"}:
        raise CompositionError("REPLAY_PLAN_VERSION_UNSUPPORTED")
    lock = plan.get("replay_lock")
    if not isinstance(lock, Mapping) or set(lock) != _REPLAY_LOCK_FIELDS:
        raise CompositionError("REPLAY_LOCK_INVALID")
    if lock.get("schema_version") != "pptx-studio-replay-lock.v1":
        raise CompositionError("REPLAY_LOCK_INVALID")
    if lock.get("catalog_sha256") != _digest(catalog):
        raise CompositionError("REPLAY_CATALOG_DRIFT")
    if lock.get("compiler_sha256") != _compiler_sha256():
        raise CompositionError("REPLAY_COMPILER_DRIFT")
    narrative = plan.get("narrative_validation")
    if not isinstance(narrative, Mapping) or lock.get("narrative_sha256") != narrative.get("narrative_sha256"):
        raise CompositionError("REPLAY_NARRATIVE_DRIFT")
    if observations is not None and lock.get("observations_sha256") != _digest(observations):
        raise CompositionError("REPLAY_OBSERVATIONS_DRIFT")
    if plan.get("schema_version") in {"3.0", "4.0"}:
        authority = plan.get("component_profile")
        if not isinstance(authority, Mapping) or set(authority) != _COMPONENT_PROFILE_FIELDS:
            raise CompositionError("REPLAY_COMPONENT_PROFILE_INVALID")
        if component_profiles is None:
            raise CompositionError("REPLAY_COMPONENT_PROFILE_REQUIRED")
        if (
            authority.get("profile_id") != component_profiles.profile_id
            or authority.get("profile_sha256") != component_profiles.profile_sha256
        ):
            raise CompositionError("REPLAY_COMPONENT_PROFILE_DRIFT")


def _observation(page: Mapping[str, Any], observations: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]:
    observation = observations.get(str(page.get("page_id")))
    render = page.get("render")
    if not isinstance(observation, Mapping) or not isinstance(render, Mapping):
        raise CompositionError("OBSERVATION_MISSING")
    if observation.get("image_sha256") != render.get("image_sha256"):
        raise CompositionError("OBSERVATION_HASH_MISMATCH")
    detail = observation.get("observation")
    if not isinstance(detail, Mapping) or detail.get("uncertainty") == "high":
        raise CompositionError("OBSERVATION_INELIGIBLE")
    styles = detail.get("visual_style")
    if not isinstance(styles, list) or not styles or any(not isinstance(item, str) or not item for item in styles):
        raise CompositionError("OBSERVATION_STYLE_INVALID")
    return detail


def style_profile(page: Mapping[str, Any], observations: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    """Reduce free-form visual prose to a small deterministic compatibility taxonomy."""

    detail = _observation(page, observations)
    return style_profile_from_observation(detail)


def style_signature(page: Mapping[str, Any], observations: Mapping[str, Mapping[str, Any]]) -> str:
    """Return a catalog-derived visual-style cluster identifier, never agent text."""

    return style_signature_from_observation(_observation(page, observations))


def _style_profiles_compatible(
    anchor: Mapping[str, str], candidate: Mapping[str, str],
) -> bool:
    """Allow controlled family variants without collapsing visual direction.

    The previous two-axis taxonomy treated a blue finance deck and a red
    ceremonial deck as equivalent ``corporate/balanced`` pages. Colour is a
    non-negotiable deck commitment. Within a cool professional system, a
    dark-blue chapter/data/process page or a light cyan evidence page is an
    intentional cadence change, not a style break, so light, balanced and dark
    tones may coexist inside that one cool professional colour family.
    Neutral, warm, green and non-professional fallbacks remain isolated.
    """

    if anchor["color_family"] != candidate["color_family"]:
        return False
    professional = {"corporate", "minimal", "technology"}
    if anchor["archetype"] in professional:
        if candidate["archetype"] not in professional:
            return False
        if anchor["color_family"] == "cool":
            return anchor["tone"] in {"light", "balanced", "dark"} and candidate["tone"] in {"light", "balanced", "dark"}
        return anchor["tone"] == candidate["tone"]
    if anchor["tone"] != candidate["tone"]:
        return False
    return anchor["archetype"] == candidate["archetype"]


def _page_capacity(page: Mapping[str, Any]) -> int:
    shapes = page.get("shapes")
    if not isinstance(shapes, list):
        return 0
    return sum(
        int(shape.get("max_chars", 0))
        for shape in shapes
        if isinstance(shape, Mapping) and type(shape.get("max_chars", 0)) is int
    )


def _mixed_library_evidence(slides: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Enforce provenance diversity for every substantive v2 assembly.

    A narrative author can legitimately merge under-filled beats, but it must
    not evade the mixed-library product boundary by shrinking a 12-page
    decision deck to 11 pages and replaying one attractive source work. Ten
    pages is the smallest normal cover/directory/evidence/decision/closing
    business deck; all decks at or above that threshold therefore use the same
    multi-source floor. Short executive notes remain eligible for a coherent
    single certified work.
    """

    packages: dict[str, int] = {}
    categories: set[str] = set()
    for slide in slides:
        source = slide.get("source")
        if not isinstance(source, Mapping):
            raise CompositionError("MIXED_LIBRARY_SOURCE_INVALID")
        package_sha, category = source.get("package_sha256"), source.get("category")
        if not isinstance(package_sha, str) or not package_sha or not isinstance(category, str) or not category:
            raise CompositionError("MIXED_LIBRARY_SOURCE_INVALID")
        packages[package_sha] = packages.get(package_sha, 0) + 1
        categories.add(category)
    result = {
        "enforced": len(slides) >= 10,
        "source_package_count": len(packages),
        "source_category_count": len(categories),
        "maximum_pages_from_one_source": max(packages.values(), default=0),
    }
    if result["enforced"] and (
        result["source_package_count"] < 6
        or result["source_category_count"] < 5
        or result["maximum_pages_from_one_source"] > 4
    ):
        raise CompositionError(
            "MIXED_LIBRARY_DIVERSITY_REQUIRED:"
            f"packages={result['source_package_count']}:"
            f"categories={result['source_category_count']}:"
            f"max_pages_per_source={result['maximum_pages_from_one_source']}"
        )
    return result


def _style_anchor_evidence(
    slides: list[Mapping[str, Any]],
    *,
    anchor_signature: str,
) -> dict[str, Any]:
    """Make visual-anchor coverage observable instead of trusting a prompt.

    A v2 plan may register one compatible signature in the locked anchor
    cluster. A signature is a *page-description fingerprint*, whereas the
    cluster is the governed colour/tone/professionalism system. For example,
    cool balanced `corporate` and `minimal` pages are one deliberate
    institutional cluster, not a visual collage. The coverage gate therefore
    counts cluster membership, not an arbitrary preference for one of those
    two fingerprints.
    """

    fallback_count = 0
    for slide in slides:
        evidence = slide.get("evidence")
        if not isinstance(evidence, Mapping):
            raise CompositionError("STYLE_ANCHOR_EVIDENCE_INVALID")
        if evidence.get("style_match") == "explicit_fallback":
            fallback_count += 1
    total = len(slides)
    anchor_count = total - fallback_count
    coverage = round(anchor_count / total, 6) if total else 0.0
    result = {
        "anchor_style_signature": anchor_signature,
        "anchor_cluster_page_count": anchor_count,
        "compatible_fallback_page_count": fallback_count,
        "anchor_cluster_coverage": coverage,
        "enforced": total >= 10,
    }
    if result["enforced"] and coverage < 0.70:
        raise CompositionError(
            "STYLE_ANCHOR_COVERAGE_INSUFFICIENT:"
            f"coverage={coverage:.6f}:minimum=0.700000"
        )
    return result


def _role_matches(page: Mapping[str, Any], detail: Mapping[str, Any], role: str) -> bool:
    return role_matches_page(page, detail, role)


def _validate_request(
    request: Mapping[str, Any],
    *,
    component_profiles: ComponentProfileIndex | None = None,
) -> tuple[
    str, Mapping[str, Any], list[Mapping[str, Any]], Mapping[str, Any] | None,
]:
    version = request.get("schema_version")
    if version == "1.0":
        expected_fields = _REQUEST_FIELDS_V1
        slide_fields = _SLIDE_FIELDS_V1
        narrative_validation: Mapping[str, Any] | None = None
    elif version == "2.0":
        expected_fields = _REQUEST_FIELDS_V2
        slide_fields = _SLIDE_FIELDS_V2
        candidate_validation = request.get("narrative_validation")
        if (
            not isinstance(candidate_validation, Mapping)
            or set(candidate_validation) != _NARRATIVE_VALIDATION_FIELDS
            or candidate_validation.get("schema_version") != "pptx-studio-narrative-validation.v1"
            or candidate_validation.get("status") != "PASS"
            or not isinstance(candidate_validation.get("brief_id"), str)
            or not isinstance(candidate_validation.get("brief_sha256"), str)
            or not isinstance(candidate_validation.get("narrative_sha256"), str)
            or type(candidate_validation.get("slide_count")) is not int
            or not isinstance(candidate_validation.get("delivery_beat_ids"), list)
            or not isinstance(candidate_validation.get("section_evidence"), list)
        ):
            raise CompositionError("NARRATIVE_VALIDATION_INVALID")
        narrative_validation = candidate_validation
    elif version in {"3.0", "4.0"}:
        expected_fields = _REQUEST_FIELDS_V3 if version == "3.0" else _REQUEST_FIELDS_V4
        slide_fields = _SLIDE_FIELDS_V2
        candidate_validation = request.get("narrative_validation")
        if (
            not isinstance(candidate_validation, Mapping)
            or set(candidate_validation) != _NARRATIVE_VALIDATION_FIELDS
            or candidate_validation.get("schema_version") != "pptx-studio-narrative-validation.v1"
            or candidate_validation.get("status") != "PASS"
            or not isinstance(candidate_validation.get("brief_id"), str)
            or not isinstance(candidate_validation.get("brief_sha256"), str)
            or not isinstance(candidate_validation.get("narrative_sha256"), str)
            or type(candidate_validation.get("slide_count")) is not int
            or not isinstance(candidate_validation.get("delivery_beat_ids"), list)
            or not isinstance(candidate_validation.get("section_evidence"), list)
        ):
            raise CompositionError("NARRATIVE_VALIDATION_INVALID")
        authority = request.get("component_profile")
        if (
            not isinstance(authority, Mapping)
            or set(authority) != _COMPONENT_PROFILE_FIELDS
            or not isinstance(authority.get("profile_id"), str)
            or not isinstance(authority.get("profile_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", str(authority.get("profile_sha256")))
            or component_profiles is None
            or authority.get("profile_id") != component_profiles.profile_id
            or authority.get("profile_sha256") != component_profiles.profile_sha256
        ):
            raise CompositionError("COMPONENT_PROFILE_AUTHORITY_INVALID")
        narrative_validation = candidate_validation
    else:
        raise CompositionError("REQUEST_SCHEMA_INVALID")
    if set(request) != expected_fields:
        raise CompositionError("REQUEST_SCHEMA_INVALID")
    strategy = request.get("strategy")
    if strategy not in _STRATEGIES:
        raise CompositionError("STRATEGY_INVALID")
    art = request.get("art_direction")
    if not isinstance(art, Mapping) or set(art) != _ART_FIELDS:
        raise CompositionError("ART_DIRECTION_INVALID")
    anchor = art.get("anchor_page_id")
    signatures = art.get("allowed_style_signatures")
    suitability = art.get("suitability")
    if not isinstance(anchor, str) or not anchor:
        raise CompositionError("ART_DIRECTION_ANCHOR_INVALID")
    if not isinstance(signatures, list) or not signatures or any(not isinstance(item, str) or not item.startswith("style_") for item in signatures):
        raise CompositionError("STYLE_SIGNATURES_INVALID")
    # Anchor plus no more than three independently certified compatible
    # signatures. Four is a hard readability boundary, not permission to mix
    # arbitrary visual systems: every non-anchor entry is checked against the
    # anchor's colour family, tone and professional archetype below.
    if len(set(signatures)) != len(signatures) or len(signatures) > 4:
        raise CompositionError("STYLE_SIGNATURES_DUPLICATE")
    if suitability not in _SUITABILITY_PROFILES:
        raise CompositionError("SUITABILITY_INVALID")
    slides = request.get("slides")
    if not isinstance(slides, list) or not slides:
        raise CompositionError("SLIDES_INVALID")
    seen: set[str] = set()
    selected_page_occurrences: dict[str, list[tuple[int, str]]] = {}
    component_host_pages: set[str] = set()
    component_host_occurrence_counts: dict[str, int] = {}
    selected_component_ids: set[str] = set()
    requested_beat_ids: list[str] = []
    for item in slides:
        component_mode = (
            isinstance(item, Mapping)
            and (
                version == "3.0" and set(item) == _COMPONENT_SLIDE_FIELDS_V3
                or version == "4.0" and set(item) == _COMPONENT_SLIDE_FIELDS_V4
            )
        )
        if not isinstance(item, Mapping) or (set(item) != slide_fields and not component_mode):
            raise CompositionError("SLIDE_SCHEMA_INVALID")
        slide_id, role = item.get("slide_id"), item.get("role")
        candidates = item.get("host_candidate_ids") if component_mode else item.get("candidate_ids")
        selected = item.get("selected_host_candidate_id") if component_mode else item.get("selected_candidate_id")
        capacity = item.get("minimum_capacity")
        if not isinstance(slide_id, str) or not slide_id or slide_id in seen:
            raise CompositionError("SLIDE_ID_INVALID")
        seen.add(slide_id)
        if not isinstance(role, str) or not role:
            raise CompositionError("SLIDE_ROLE_INVALID")
        if not isinstance(candidates, list) or not candidates or any(not isinstance(value, str) or not value for value in candidates):
            raise CompositionError("CANDIDATE_IDS_INVALID")
        if len(set(candidates)) != len(candidates) or not isinstance(selected, str) or selected not in candidates:
            raise CompositionError("CANDIDATE_SELECTION_INVALID")
        selected_page_occurrences.setdefault(selected, []).append((len(seen), role))
        if component_mode:
            assert component_profiles is not None  # verified above
            try:
                if version == "4.0":
                    raw_placements = item.get("component_placements")
                    if (
                        not isinstance(raw_placements, list)
                        or any(not isinstance(entry, Mapping) or set(entry) != _COMPONENT_PLACEMENT_FIELDS_V4 for entry in raw_placements)
                    ):
                        raise CompositionError("COMPONENT_SELECTION_INVALID")
                    placements = tuple(
                        (entry.get("host_anchor_id"), entry.get("component_id"))
                        for entry in raw_placements
                    )
                    if any(not isinstance(anchor_id, str) or not anchor_id or not isinstance(component_id, str) or not component_id for anchor_id, component_id in placements):
                        raise CompositionError("COMPONENT_SELECTION_INVALID")
                    certified = component_profiles.validate_placements(
                        host_page_id=str(selected), placements=placements,
                    )
                    host_anchor = certified[0][0]
                    components = tuple(component for _anchor, component in certified)
                else:
                    anchor_id = item.get("host_anchor_id")
                    component_ids = item.get("selected_component_ids")
                    if (
                        not isinstance(anchor_id, str)
                        or not isinstance(component_ids, list)
                        or any(not isinstance(value, str) or not value for value in component_ids)
                    ):
                        raise CompositionError("COMPONENT_SELECTION_INVALID")
                    host_anchor, components = component_profiles.validate_selection(
                        host_page_id=str(selected), host_anchor_id=anchor_id,
                        component_ids=tuple(component_ids),
                    )
            except ComponentProfileError as exc:
                raise CompositionError(str(exc)) from exc
            if any(role not in component.allowed_roles for component in components):
                raise CompositionError("COMPONENT_ROLE_INCOMPATIBLE")
            if host_anchor.page_id != selected:
                raise CompositionError("COMPONENT_HOST_PAGE_MISMATCH")
            component_ids = {component.component_id for component in components}
            if component_ids & selected_component_ids:
                raise CompositionError("COMPONENT_SELECTION_DUPLICATE")
            selected_component_ids.update(component_ids)
            component_host_pages.add(str(selected))
            component_host_occurrence_counts[str(selected)] = component_host_occurrence_counts.get(str(selected), 0) + 1
        if type(capacity) is not int or capacity < 0:
            raise CompositionError("SLIDE_CAPACITY_INVALID")
        if narrative_validation is not None:
            beat_id = item.get("beat_id")
            if not isinstance(beat_id, str) or not beat_id or beat_id in requested_beat_ids:
                raise CompositionError("NARRATIVE_BEAT_BINDING_INVALID")
            requested_beat_ids.append(beat_id)
    if narrative_validation is not None:
        expected_beats = narrative_validation["delivery_beat_ids"]
        if (
            narrative_validation["slide_count"] != len(slides)
            or requested_beat_ids != expected_beats
            or len(set(expected_beats)) != len(expected_beats)
            or any(not isinstance(item, str) or not item for item in expected_beats)
        ):
            raise CompositionError("NARRATIVE_DELIVERY_BINDING_MISMATCH")
    if strategy != "component_assembly":
        content_reused_instances = 0
        shared_card_reused_instances = 0
        for page_id, occurrences in selected_page_occurrences.items():
            if len(occurrences) == 1:
                continue
            indices = [index for index, _role in occurrences]
            roles = {role for _index, role in occurrences}
            if page_id in component_host_pages:
                if (
                    component_host_occurrence_counts.get(page_id) != len(occurrences)
                    or len(roles) != 1
                    or len(occurrences) > _MAX_COMPONENT_HOST_REUSE_PER_PAGE
                    or any(right - left == 1 for left, right in zip(indices, indices[1:]))
                ):
                    raise CompositionError("PAGE_SOURCE_DUPLICATE")
                continue
            shared_card_layout = _shared_card_layout(roles)
            if (len(roles) != 1 and not shared_card_layout) or any(
                right - left == 1 for left, right in zip(indices, indices[1:])
            ):
                raise CompositionError("PAGE_SOURCE_DUPLICATE")
            role = next(iter(roles))
            if role == "section":
                if len(occurrences) > _MAX_SECTION_REUSE_PER_PAGE:
                    raise CompositionError("PAGE_SOURCE_DUPLICATE")
            elif shared_card_layout:
                if len(occurrences) > _MAX_SHARED_CARD_LAYOUT_INSTANCES:
                    raise CompositionError("PAGE_SOURCE_DUPLICATE")
                shared_card_reused_instances += len(occurrences) - 1
            elif role in _REUSABLE_PAGE_ROLES:
                if len(occurrences) > _MAX_CONTENT_REUSE_PER_PAGE:
                    raise CompositionError("PAGE_SOURCE_DUPLICATE")
                content_reused_instances += len(occurrences) - 1
            else:
                raise CompositionError("PAGE_SOURCE_DUPLICATE")
        if content_reused_instances > _max_reused_page_instances(len(slides)):
            raise CompositionError("PAGE_SOURCE_DUPLICATE")
        if shared_card_reused_instances > _max_reused_page_instances(len(slides)) + 1:
            raise CompositionError("PAGE_SOURCE_DUPLICATE")
        if any(len(items) > 1 for items in selected_page_occurrences.values()) and strategy != "page_assembly":
            raise CompositionError("PAGE_SOURCE_DUPLICATE")
    return strategy, art, slides, narrative_validation


def compile_composition(
    catalog: Mapping[str, Any],
    *,
    observations: Mapping[str, Mapping[str, Any]],
    request: Mapping[str, Any],
    component_profiles: ComponentProfileIndex | None = None,
) -> dict[str, Any]:
    """Compile a bounded agent selection without filesystem, model or write access."""

    strategy, art, requested_slides, narrative_validation = _validate_request(
        request, component_profiles=component_profiles,
    )
    component_authority = (
        {
            "profile_id": component_profiles.profile_id,
            "profile_sha256": component_profiles.profile_sha256,
        }
        if request.get("schema_version") in {"3.0", "4.0"} and component_profiles is not None
        else None
    )
    active = set(catalog.get("active_categories", []))
    pages = {str(page.get("page_id")): page for page in catalog.get("pages", []) if isinstance(page, Mapping)}
    regions = {str(region.get("region_id")): region for region in catalog.get("regions", []) if isinstance(region, Mapping)}
    anchor = pages.get(str(art["anchor_page_id"]))
    if anchor is None or anchor.get("category") not in active or not materialization_eligible(anchor):
        raise CompositionError("ANCHOR_PAGE_INVALID")
    anchor_signature = style_signature(anchor, observations)
    anchor_profile = style_profile(anchor, observations)
    anchor_deck_id = str(anchor.get("deck_id"))
    allowed_signatures = list(art["allowed_style_signatures"])
    if anchor_signature not in allowed_signatures:
        raise CompositionError("ANCHOR_SIGNATURE_NOT_ALLOWED")
    signature_pages: dict[str, list[Mapping[str, Any]]] = {}
    for page in pages.values():
        signature_pages.setdefault(style_signature(page, observations), []).append(page)
    for signature in allowed_signatures:
        signature_candidates = signature_pages.get(signature, [])
        if not signature_candidates:
            raise CompositionError("STYLE_FALLBACK_INCOMPATIBLE")
        # A certified multi-page work is its own strongest style evidence.
        # OCR/vision descriptions may call its title page "corporate" and a
        # chart page "infographic" despite sharing the same master, palette,
        # grid and decoration.  Its sibling pages are therefore a controlled
        # theme family, not arbitrary cross-style fallback.
        if any(str(page.get("deck_id")) == anchor_deck_id for page in signature_candidates):
            continue
        if not any(
            _style_profiles_compatible(anchor_profile, style_profile(page, observations))
            for page in signature_candidates
        ):
            raise CompositionError("STYLE_FALLBACK_INCOMPATIBLE")

    output_slides: list[dict[str, Any]] = []
    exact_deck_id: str | None = None
    used_source_pages: set[str] = set()
    last_exact_slide_number = 0
    for item in requested_slides:
        component_mode = "selected_host_candidate_id" in item
        selected_id = str(
            item["selected_host_candidate_id"] if component_mode
            else item["selected_candidate_id"]
        )
        region: Mapping[str, Any] | None = None
        required_regions = 1
        component_selection: Mapping[str, Any] | None = None
        if component_mode:
            page = pages.get(selected_id)
            if page is None:
                raise CompositionError("COMPONENT_HOST_PAGE_UNKNOWN")
            if component_profiles is None:
                raise CompositionError("COMPONENT_PROFILE_AUTHORITY_INVALID")
            try:
                if request.get("schema_version") == "4.0":
                    certified = component_profiles.validate_placements(
                        host_page_id=selected_id,
                        placements=tuple(
                            (str(entry["host_anchor_id"]), str(entry["component_id"]))
                            for entry in item["component_placements"]
                        ),
                    )
                    host_anchor = certified[0][0]
                    components = tuple(component for _anchor, component in certified)
                else:
                    host_anchor, components = component_profiles.validate_selection(
                        host_page_id=selected_id,
                        host_anchor_id=str(item["host_anchor_id"]),
                        component_ids=tuple(str(value) for value in item["selected_component_ids"]),
                    )
            except ComponentProfileError as exc:
                raise CompositionError(str(exc)) from exc
            # The component profile is the role authority for this bounded
            # exception. A host is a pre-certified reservation, not a claim
            # that its surrounding whole page is semantically interchangeable.
            if any(str(item["role"]) not in component.allowed_roles for component in components):
                raise CompositionError("COMPONENT_ROLE_INCOMPATIBLE")
            # A component is visual content, not an invisible implementation
            # detail. Checking only its host page would let a green/consumer
            # component enter a cool institutional host through an otherwise
            # valid opaque placement. Re-apply the locked cluster boundary to
            # every physical component source before a plan can be emitted.
            for component in components:
                component_page = pages.get(component.page_id)
                if component_page is None or not materialization_eligible(component_page):
                    raise CompositionError("COMPONENT_SOURCE_MATERIALIZATION_INELIGIBLE")
                certified_visual = component.visual_certification
                if certified_visual is not None:
                    # A reviewed native closure can omit an unrelated image or
                    # stock subject from its source page. The profile binds the
                    # fragment-level review to this exact closure/hash; it is
                    # more precise than, but never weaker than, an agent guess.
                    if str(art["suitability"]) not in certified_visual.suitability:
                        raise CompositionError("COMPONENT_VISUAL_SUITABILITY_NOT_ALLOWED")
                    if not _style_profiles_compatible(
                        anchor_profile, certified_visual.style_profile,
                    ):
                        raise CompositionError("COMPONENT_VISUAL_STYLE_INCOMPATIBLE")
                else:
                    component_detail = _observation(component_page, observations)
                    if not _suitability_safe(component_detail, profile=str(art["suitability"])):
                        raise CompositionError("COMPONENT_SOURCE_SUBJECT_INCOMPATIBLE")
                    component_signature = style_signature(component_page, observations)
                    same_component_theme_family = str(component_page.get("deck_id")) == anchor_deck_id
                    if component_signature not in allowed_signatures and not same_component_theme_family:
                        raise CompositionError("COMPONENT_STYLE_SIGNATURE_NOT_ALLOWED")
                    if (
                        not same_component_theme_family
                        and not _style_profiles_compatible(
                            anchor_profile, style_profile(component_page, observations),
                        )
                    ):
                        raise CompositionError("COMPONENT_STYLE_FALLBACK_INCOMPATIBLE")
            source_region_ids = [
                str(region_id) for region_id, record in regions.items()
                if record.get("page_id") == page.get("page_id")
            ]
            capacity = _page_capacity(page)
            required_regions = 0
            if request.get("schema_version") == "4.0":
                component_selection = {
                    "placements": [
                        {
                            "host_anchor_id": anchor.host_anchor_id,
                            "component_id": component.component_id,
                            "component_intent": component.semantic_intent,
                        }
                        for anchor, component in certified
                    ],
                }
            else:
                component_selection = {
                    "host_anchor_id": host_anchor.host_anchor_id,
                    "component_ids": [component.component_id for component in components],
                    "component_intents": [component.semantic_intent for component in components],
                }
        elif strategy == "component_assembly":
            region = regions.get(selected_id)
            if region is None:
                raise CompositionError("REGION_CANDIDATE_UNKNOWN")
            page = pages.get(str(region.get("page_id")))
            if page is None or page.get("component_eligible") is not True:
                raise CompositionError("REGION_PAGE_INELIGIBLE")
            source_region_ids = [selected_id]
            capacity = region.get("capacity", {}).get("max_text_chars", 0) if isinstance(region.get("capacity"), Mapping) else 0
        else:
            page = pages.get(selected_id)
            if page is None:
                raise CompositionError("PAGE_CANDIDATE_UNKNOWN")
            source_region_ids = [str(region_id) for region_id, record in regions.items() if record.get("page_id") == page.get("page_id")]
            capacity = _page_capacity(page)
            # A native chart/table/workbook page is eligible only when a
            # source-fingerprinted business-data contract exists. Check
            # this before generic region floors so a missing governed-data
            # authority is never masked as an ordinary capacity repair.
            if governed_content_slot_count(page) > 0 and contract_for_source(
                str(page.get("package_sha256")), int(page.get("slide_number", 0)),
            ) is None:
                raise CompositionError("STRUCTURED_DATA_CONTRACT_UNAVAILABLE")
            # ``exact_deck`` preserves a certified page order, but it does
            # not make a source page semantically interchangeable.  Allowing
            # the route to bypass the native-region floor was the mechanism
            # by which a clinical-department network could be selected for a
            # financial-efficiency comparison merely because both were in one
            # attractive work-report deck.  A complete-work reproduction is
            # allowed only when every client page has the same role grammar
            # and enough independent client-owned surfaces as page assembly.
            # Native preflight remains the final per-string capacity authority.
            required_regions = minimum_distinct_client_facts(item["role"])
            if len(source_region_ids) < required_regions:
                raise CompositionError("BINDABLE_REGION_COUNT_INSUFFICIENT")
        if page.get("category") not in active:
            raise CompositionError("SOURCE_SCOPE_INVALID")
        if page.get("component_only") is True and not component_mode:
            raise CompositionError("COMPONENT_ONLY_PAGE_REQUIRES_COMPONENT_PLACEMENT")
        if not materialization_eligible(page):
            raise CompositionError("SOURCE_MATERIALIZATION_INELIGIBLE")
        if not isinstance(page.get("deck_id"), str) or not re.fullmatch(r"[0-9a-f]{64}", str(page.get("package_sha256"))):
            raise CompositionError("SOURCE_PROVENANCE_INVALID")
        if type(page.get("slide_number")) is not int or int(page["slide_number"]) < 1:
            raise CompositionError("SOURCE_PROVENANCE_INVALID")
        detail = _observation(page, observations)
        # Query results are advisory candidates; a model can otherwise copy a
        # stale page ID into a composition request and bypass the subject
        # filter.  Re-apply the same certified visual-subject policy at the
        # compilation boundary before any private source is opened.
        if not _suitability_safe(detail, profile=str(art["suitability"])):
            raise CompositionError("SOURCE_SUBJECT_INCOMPATIBLE")
        signature = style_signature(page, observations)
        same_certified_theme_family = str(page.get("deck_id")) == anchor_deck_id
        # One complete certified PPTX is an indivisible visual family.  Its
        # cover, timeline and data pages may receive different vision labels
        # and therefore different derived signatures, but its PowerPoint
        # master/grid/palette are the authoritative common direction.  The
        # request lists only the anchor plus at most three certified cross-deck
        # companion signatures.
        if signature not in allowed_signatures and not same_certified_theme_family:
            raise CompositionError("STYLE_SIGNATURE_NOT_ALLOWED")
        if not same_certified_theme_family and not _style_profiles_compatible(anchor_profile, style_profile(page, observations)):
            raise CompositionError("STYLE_FALLBACK_INCOMPATIBLE")
        # The planner and compiler share one quality contract. Same-deck
        # membership proves visual-family continuity, not page quality, so it
        # cannot bypass this gate. A genuinely sparse section divider has its
        # own slightly lower certified floor; every ordinary page remains at
        # the reference-grade 0.80 threshold.
        quality_floor = (
            _SECTION_VISUAL_QUALITY_FLOOR
            if item["role"] == "section"
            else _PAGE_VISUAL_QUALITY_FLOOR
        )
        render = page.get("render")
        quality = render.get("visual_quality") if isinstance(render, Mapping) else None
        if not isinstance(quality, (int, float)) or float(quality) < quality_floor:
            raise CompositionError("STYLE_FALLBACK_VISUAL_QUALITY_INSUFFICIENT")
        # Source order and a shared master establish visual continuity; they
        # never establish semantic equivalence.  Enforce the certified
        # category/vision role mapping for every strategy, including exact
        # deck reproduction.
        if not component_mode and not _role_matches(page, detail, str(item["role"])):
            raise CompositionError("ROLE_INCOMPATIBLE")
        if type(capacity) is not int or capacity < item["minimum_capacity"]:
            raise CompositionError("CAPACITY_INSUFFICIENT")
        if strategy == "exact_deck":
            deck_id = page.get("deck_id")
            slide_number = page.get("slide_number")
            if not isinstance(deck_id, str) or type(slide_number) is not int:
                raise CompositionError("EXACT_DECK_SOURCE_INVALID")
            if exact_deck_id is None:
                exact_deck_id = deck_id
            if deck_id != exact_deck_id or str(page["page_id"]) in used_source_pages or slide_number <= last_exact_slide_number:
                raise CompositionError("EXACT_DECK_SEQUENCE_INVALID")
            used_source_pages.add(str(page["page_id"]))
            last_exact_slide_number = slide_number
        elif strategy == "family_assembly":
            # A family assembly is still a physical-template composition, not
            # a relaxed cross-deck collage. The explicit anchor family is the
            # only source authority.
            if str(page.get("deck_id")) != anchor_deck_id:
                raise CompositionError("FAMILY_ASSEMBLY_SOURCE_DECK_INVALID")
        candidate_ids = item["host_candidate_ids"] if component_mode else item["candidate_ids"]
        rank = list(candidate_ids).index(selected_id) + 1
        output_slides.append({
            "slide_id": item["slide_id"],
            **({"beat_id": item["beat_id"]} if narrative_validation is not None else {}),
            "role": item["role"],
            "source": {
                "deck_id": page.get("deck_id"),
                "page_id": page.get("page_id"),
                "package_sha256": page.get("package_sha256"),
                "category": page.get("category"),
                "slide_number": page.get("slide_number"),
                "region_ids": source_region_ids,
                **({"component_assembly": component_selection} if component_selection is not None else {}),
            },
            "evidence": {
                "selected_candidate_id": selected_id,
                "candidate_rank": rank,
                "style_signature": signature,
                "style_match": (
                    "anchor" if signature == anchor_signature
                    else "same_certified_theme_family" if same_certified_theme_family
                    else "compatible_cluster"
                ),
                "capacity": capacity,
                "capacity_residue": capacity - item["minimum_capacity"],
                "confidence": 1.0 if strategy == "exact_deck" else (0.95 if strategy == "family_assembly" else (0.85 if strategy == "page_assembly" and not component_mode else 0.7)),
            },
        })
    mixed_library = _mixed_library_evidence(output_slides) if narrative_validation is not None else None
    style_anchor = (
        _style_anchor_evidence(output_slides, anchor_signature=anchor_signature)
        if narrative_validation is not None else None
    )
    replay_lock = (
        {
            "schema_version": "pptx-studio-replay-lock.v1",
            "catalog_sha256": _digest(catalog),
            "observations_sha256": _digest(observations),
            "compiler_sha256": _compiler_sha256(),
            "narrative_sha256": narrative_validation["narrative_sha256"],
        }
        if narrative_validation is not None else None
    )
    return {
        "schema_version": (str(request.get("schema_version")) if component_authority is not None else ("2.0" if narrative_validation is not None else "1.0")),
        "status": "PASS",
        "strategy": strategy,
        "art_direction": {
            "anchor_page_id": anchor["page_id"],
            "anchor_style_signature": anchor_signature,
            "allowed_style_signatures": sorted(allowed_signatures),
            "exact_deck_id": exact_deck_id,
            "family_deck_id": anchor_deck_id if strategy == "family_assembly" else None,
        },
        "slides": output_slides,
        **({"narrative_validation": dict(narrative_validation)} if narrative_validation is not None else {}),
        **({"mixed_library": mixed_library} if mixed_library is not None else {}),
        **({"style_anchor": style_anchor} if style_anchor is not None else {}),
        **({"replay_lock": replay_lock} if replay_lock is not None else {}),
        **({"component_profile": component_authority} if component_authority is not None else {}),
    }
