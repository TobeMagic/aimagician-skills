"""Deterministic whole-deck/page/component composition over the curated catalog."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

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
_REQUEST_FIELDS = frozenset({"schema_version", "strategy", "art_direction", "slides"})
_ART_FIELDS = frozenset({"anchor_page_id", "allowed_style_signatures", "suitability"})
_SLIDE_FIELDS = frozenset({"slide_id", "role", "candidate_ids", "selected_candidate_id", "minimum_capacity"})


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def serialize_composition_plan(plan: Mapping[str, Any]) -> str:
    """Serialize a validated plan deterministically for later plan binding."""

    return _canonical_json(plan)


def composition_plan_sha256(plan: Mapping[str, Any]) -> str:
    return hashlib.sha256(serialize_composition_plan(plan).encode("utf-8")).hexdigest()


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
    dark-blue chapter/data/process page is an intentional cadence change, not
    a style break, so balanced and dark tones may coexist. Neutral/light,
    warm, green and non-professional fallbacks remain isolated.
    """

    if anchor["color_family"] != candidate["color_family"]:
        return False
    professional = {"corporate", "minimal", "technology"}
    if anchor["archetype"] in professional:
        if candidate["archetype"] not in professional:
            return False
        if anchor["color_family"] == "cool":
            return anchor["tone"] in {"balanced", "dark"} and candidate["tone"] in {"balanced", "dark"}
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


def _role_matches(page: Mapping[str, Any], detail: Mapping[str, Any], role: str) -> bool:
    return role_matches_page(page, detail, role)


def _validate_request(request: Mapping[str, Any]) -> tuple[str, Mapping[str, Any], list[Mapping[str, Any]]]:
    if set(request) != _REQUEST_FIELDS or request.get("schema_version") != "1.0":
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
    if len(set(signatures)) != len(signatures) or len(signatures) > 2:
        raise CompositionError("STYLE_SIGNATURES_DUPLICATE")
    if suitability not in _SUITABILITY_PROFILES:
        raise CompositionError("SUITABILITY_INVALID")
    slides = request.get("slides")
    if not isinstance(slides, list) or not slides:
        raise CompositionError("SLIDES_INVALID")
    seen: set[str] = set()
    selected_page_ids: set[str] = set()
    for item in slides:
        if not isinstance(item, Mapping) or set(item) != _SLIDE_FIELDS:
            raise CompositionError("SLIDE_SCHEMA_INVALID")
        slide_id, role = item.get("slide_id"), item.get("role")
        candidates, selected = item.get("candidate_ids"), item.get("selected_candidate_id")
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
        # Physical assembly imports a certified source page once. Reusing one
        # page ID would fail later and also makes a deck visibly repetitive, so
        # reject it while the agent still has the candidate lists to choose a
        # distinct alternative.
        if strategy != "component_assembly":
            if selected in selected_page_ids:
                raise CompositionError("PAGE_SOURCE_DUPLICATE")
            selected_page_ids.add(selected)
        if type(capacity) is not int or capacity < 0:
            raise CompositionError("SLIDE_CAPACITY_INVALID")
    return strategy, art, slides


def compile_composition(
    catalog: Mapping[str, Any],
    *,
    observations: Mapping[str, Mapping[str, Any]],
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Compile a bounded agent selection without filesystem, model or write access."""

    strategy, art, requested_slides = _validate_request(request)
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
        selected_id = str(item["selected_candidate_id"])
        region: Mapping[str, Any] | None = None
        if strategy == "component_assembly":
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
            # Exact-deck reuse is a controlled reproduction route. A page may
            # be a certified chart/infographic whose vision label does not map
            # to the generic role taxonomy and whose visible data surface is a
            # single native heading. It still needs at least one editable
            # client slot, but cannot honestly be rejected as a six-card page
            # merely because a classifier called it a dashboard. The native
            # preflight and binding-completeness gate retain authority over its
            # actual editable surface. Page/component assembly keeps the
            # stricter role floor before any source import.
            # ``family_assembly`` is the controlled adaptation route for a
            # complete certified work. Unlike exact-deck reproduction, its
            # source order may be recomposed for the client narrative; unlike
            # generic page assembly, it must not reject a genuine editorial
            # page because a visual classifier did not reduce it to one of the
            # small generic role labels. It remains constrained to the anchor
            # deck, physical native slots and the downstream binding gate.
            required_regions = 1 if strategy in {"exact_deck", "family_assembly"} else minimum_distinct_client_facts(item["role"])
            if len(source_region_ids) < required_regions:
                raise CompositionError("BINDABLE_REGION_COUNT_INSUFFICIENT")
            # A native chart/table/workbook page is eligible only when a
            # source-fingerprinted business-data contract exists. A later
            # adaptation request must still provide every declared value;
            # this never grants generic chart-editing authority.
            if governed_content_slot_count(page) > 0 and contract_for_source(
                str(page.get("package_sha256")), int(page.get("slide_number", 0)),
            ) is None:
                raise CompositionError("STRUCTURED_DATA_CONTRACT_UNAVAILABLE")
        if page.get("category") not in active:
            raise CompositionError("SOURCE_SCOPE_INVALID")
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
        # request lists only the anchor plus at most one cross-deck fallback.
        if signature not in allowed_signatures and not same_certified_theme_family:
            raise CompositionError("STYLE_SIGNATURE_NOT_ALLOWED")
        if not same_certified_theme_family and not _style_profiles_compatible(anchor_profile, style_profile(page, observations)):
            raise CompositionError("STYLE_FALLBACK_INCOMPATIBLE")
        if strategy not in {"exact_deck", "family_assembly"} and not _role_matches(page, detail, str(item["role"])):
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
        rank = list(item["candidate_ids"]).index(selected_id) + 1
        output_slides.append({
            "slide_id": item["slide_id"],
            "role": item["role"],
            "source": {
                "deck_id": page.get("deck_id"),
                "page_id": page.get("page_id"),
                "package_sha256": page.get("package_sha256"),
                "slide_number": page.get("slide_number"),
                "region_ids": source_region_ids,
            },
            "evidence": {
                "selected_candidate_id": selected_id,
                "candidate_rank": rank,
                "style_signature": signature,
                "style_match": (
                    "anchor" if signature == anchor_signature
                    else "same_certified_theme_family" if same_certified_theme_family
                    else "explicit_fallback"
                ),
                "capacity": capacity,
                "capacity_residue": capacity - item["minimum_capacity"],
                "confidence": 1.0 if strategy == "exact_deck" else (0.95 if strategy == "family_assembly" else (0.85 if strategy == "page_assembly" else 0.7)),
            },
        })
    return {
        "schema_version": "1.0",
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
    }
