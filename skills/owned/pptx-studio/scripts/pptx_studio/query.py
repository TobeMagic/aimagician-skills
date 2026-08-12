"""Bounded deterministic retrieval over compiled PPTX Studio catalog records."""

from __future__ import annotations

import json
import hashlib
import re
from typing import Any, Mapping

from .role_policy import minimum_distinct_client_facts


class QueryError(ValueError):
    """Raised for an invalid query instead of falling back to file discovery."""


_ALLOWED_REQUEST = {"mode", "role", "tags", "style", "capacity", "limit", "suitability", "candidate_ids", "deck_id"}
_MODES = {"deck", "page", "region"}
_SUITABILITY_PROFILES = {"general", "institutional-finance"}
_INSTITUTIONAL_FINANCE_EXCLUSIONS = (
    "anime", "brand-characters", "metaverse", "virtual world", "vr",
    "robot", "smartphone", "app screenshots", "product showcase",
    "warehouse", "energy", "fuel cells", "nature journal", "solar cells",
    "gaming", "fashion",
    # A finance/institutional brief without supplied imagery must not inherit
    # an unrelated stock-photo subject merely because its layout is usable.
    # Neutral abstract geometry remains available; scenic/photo narratives do
    # not.  This is deliberately a suitability constraint, not a deletion of
    # the private library: those pages remain queryable for suitable briefs.
    "landscape", "mountain", "clouds", "sailboat", "scenery", "nature-themed",
    # Full-work template covers can otherwise dominate on page-family count
    # while carrying an unmistakably unrelated commercial subject.  An
    # institutional finance/hospital briefing has no approved client imagery
    # with which to recontextualize automotive, agricultural or food brands.
    "automotive", "car", "agricultural", "agriculture", "coffee", "banana",
    "citrus", "farming", "farm",
    # "Institutional finance" is not a loose green/medical visual style.  A
    # hospital report can retain neutral healthcare imagery, but it cannot
    # honestly inherit a deck whose composition depends on a particular TCM
    # product, pathology specimen, experimental result or crop story.  Those
    # subjects must be supplied by the client and explicitly bound as assets;
    # the text-only route has no authority to silently repurpose them.
    "traditional chinese medicine", "tcm", "herbal medicine", "herbal",
    "moxibustion", "anatomy", "dermatology", "digestive system",
    "histology", "pathology", "mouse model", "experimental support",
    "epidemiology", "essential oils", "tea products", "medicinal plants",
    "rural revitalization", "crop showcase", "cultivation",
)
# User-confirmed source categories are stronger evidence of a page's intended
# structural role than an OCR/vision model's free-form description.  Visual
# evidence still determines style and fine-grained semantic compatibility.
_CATEGORY_ROLES: dict[str, frozenset[str]] = {
    "003-封面模板": frozenset({"cover"}),
    "036-目录模板": frozenset({"contents"}),
    "037-章节模板": frozenset({"section"}),
    "038-标题模板": frozenset({"title"}),
    "039-结尾模板": frozenset({"closing"}),
    "041-二段内容": frozenset({"two-item"}),
    "042-三段内容": frozenset({"three-item"}),
    "043-四段内容": frozenset({"four-item"}),
    "044-五段内容": frozenset({"five-item"}),
    "045-六段内容": frozenset({"six-item"}),
    "046-多段内容": frozenset({"multi-item"}),
    "047-人物介绍": frozenset({"team"}),
    "048-荣誉奖项": frozenset({"awards"}),
    "049-时间轴图": frozenset({"timeline"}),
    "050-架构流程": frozenset({"process"}),
    "051-商业模型": frozenset({"business-model"}),
    "052-样机展示": frozenset({"product"}),
    "053-金句模板": frozenset({"quote"}),
    "054-合作伙伴": frozenset({"partners"}),
    "057-优秀作品": frozenset({"case-study"}),
    "059-一段内容": frozenset({"one-item"}),
    "082-地图排版": frozenset({"map"}),
}

_ROLE_SEMANTIC_HINTS: dict[str, frozenset[str]] = {
    "cover": frozenset({"cover", "title slide", "title_slide", "title slide"}),
    "contents": frozenset({"contents", "agenda", "outline", "table of contents", "table-of-contents", "navigation"}),
    "section": frozenset({"section", "chapter", "chapter_title", "chapter-title", "section divider", "section_divider", "section header", "section-header"}),
    "closing": frozenset({"closing", "thank you", "thanks", "presentation end", "presentation_end", "end"}),
    "dashboard": frozenset({"dashboard", "kpi", "metrics", "data visualization", "data_visualization", "performance assessment"}),
    "process": frozenset({"process", "flow", "workflow", "roadmap", "flowchart"}),
    "timeline": frozenset({"timeline", "milestone", "milestones", "schedule", "annual_work_plan"}),
    "team": frozenset({"team", "team introduction", "team_introduction", "profile cards", "profile_cards"}),
}

# A complete-work anchor is a quality commitment, not merely a convenient
# source of many pages. The portable render fingerprint is only a coarse
# prefilter; later blind visual review remains mandatory. It nonetheless
# rejects a family whose weak pages would otherwise win solely on page count.
_COMPLETE_FAMILY_MIN_VISUAL_QUALITY = 0.80


def role_matches_page(page: Mapping[str, Any], observation: Mapping[str, Any], role: str) -> bool:
    """Match a page role using certified category, vision role and tags.

    Full-work template decks frequently identify a chapter divider as
    ``chapter_title`` in visual evidence rather than the generic ``section``
    role.  Treat that controlled taxonomy as equivalent; never use free-form
    model prose as a role grant.
    """

    if role in _CATEGORY_ROLES.get(str(page.get("category")), frozenset()):
        return True
    suggested = observation.get("suggested_roles", [])
    if isinstance(suggested, list) and role in suggested:
        return True
    hints = _ROLE_SEMANTIC_HINTS.get(role)
    if not hints:
        return False
    terms = {
        str(item).casefold()
        for field in ("semantic_tags", "suggested_roles")
        for item in observation.get(field, [])
        if isinstance(item, str)
    }
    return bool(terms & hints)


def style_profile_from_observation(observation: Mapping[str, Any]) -> dict[str, str]:
    """Reduce certified visual evidence to the public style-cluster taxonomy."""

    styles = observation.get("visual_style")
    if not isinstance(styles, list) or not styles or any(not isinstance(item, str) or not item for item in styles):
        raise QueryError("OBSERVATION_STYLE_INVALID")
    labels = " ".join(item.casefold() for item in styles)
    if any(token in labels for token in ("academic", "research", "scholarly")):
        archetype = "academic"
    elif any(token in labels for token in ("festive", "celebration", "ceremonial")):
        archetype = "festive"
    elif any(token in labels for token in ("tech", "technology", "digital", "futur")):
        archetype = "technology"
    elif any(token in labels for token in ("editorial", "magazine", "luxury")):
        archetype = "editorial"
    elif any(token in labels for token in ("minimal", "clean layout", "clean corporate")):
        archetype = "minimal"
    elif any(token in labels for token in ("infographic", "data visual")):
        archetype = "infographic"
    elif any(token in labels for token in ("corporate", "professional", "formal", "business")):
        archetype = "corporate"
    else:
        archetype = "general"
    if any(token in labels for token in ("dark", "black", "night")):
        tone = "dark"
    elif any(token in labels for token in ("light", "white", "bright")):
        tone = "light"
    else:
        tone = "balanced"
    cool = any(token in labels for token in ("blue", "cyan", "teal"))
    warm = any(token in labels for token in ("red", "orange", "yellow", "gold"))
    green = "green" in labels
    color_family = (
        "mixed" if cool and warm else "cool" if cool else "warm"
        if warm else "green" if green else "neutral"
    )
    return {"archetype": archetype, "tone": tone, "color_family": color_family}


def style_signature_from_observation(observation: Mapping[str, Any]) -> str:
    profile = style_profile_from_observation(observation)
    raw = json.dumps(profile, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"style_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _normal_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise QueryError("TAGS_INVALID")
    return sorted(set(value), key=str.casefold)


def _validate_request(request: Mapping[str, Any]) -> dict[str, Any]:
    if set(request) - _ALLOWED_REQUEST:
        raise QueryError("REQUEST_FIELD_INVALID")
    mode = request.get("mode")
    role = request.get("role")
    if mode not in _MODES:
        raise QueryError("MODE_INVALID")
    if not isinstance(role, str) or not role:
        raise QueryError("ROLE_INVALID")
    style = request.get("style")
    if style is not None and (not isinstance(style, str) or not style):
        raise QueryError("STYLE_INVALID")
    capacity = request.get("capacity", 0)
    if type(capacity) is not int or capacity < 0:
        raise QueryError("CAPACITY_INVALID")
    limit = request.get("limit", 5)
    if type(limit) is not int or not 1 <= limit <= 6:
        raise QueryError("LIMIT_INVALID")
    suitability = request.get("suitability", "general")
    if suitability not in _SUITABILITY_PROFILES:
        raise QueryError("SUITABILITY_INVALID")
    candidate_ids = request.get("candidate_ids")
    if candidate_ids is not None:
        if not isinstance(candidate_ids, list) or not candidate_ids or len(candidate_ids) > 24:
            raise QueryError("CANDIDATE_IDS_INVALID")
        if any(not isinstance(item, str) or not item for item in candidate_ids) or len(set(candidate_ids)) != len(candidate_ids):
            raise QueryError("CANDIDATE_IDS_INVALID")
        if mode != "page":
            raise QueryError("CANDIDATE_IDS_MODE_INVALID")
    deck_id = request.get("deck_id")
    if deck_id is not None and (
        not isinstance(deck_id, str)
        or not re.fullmatch(r"deck_[0-9a-f]{24}", deck_id)
    ):
        raise QueryError("DECK_ID_INVALID")
    return {"mode": mode, "role": role, "tags": _normal_tags(request.get("tags")), "style": style, "capacity": capacity, "limit": limit, "suitability": suitability, "candidate_ids": candidate_ids, "deck_id": deck_id}


def _suitability_safe(observation: Mapping[str, Any], *, profile: str) -> bool:
    """Reject subject matter certified as incompatible with the locked brief."""

    if profile == "general":
        return True
    corpus = " ".join(
        [
            *[item for item in observation.get("semantic_tags", ()) if isinstance(item, str)],
            *[item for item in observation.get("visual_style", ()) if isinstance(item, str)],
            str(observation.get("composition", "")),
        ]
    ).casefold()
    return not any(token in corpus for token in _INSTITUTIONAL_FINANCE_EXCLUSIONS)


def _capacity(page: Mapping[str, Any], region: Mapping[str, Any] | None) -> int:
    if region is not None:
        value = region.get("capacity", {}).get("max_text_chars", 0)
        return int(value) if type(value) is int else 0
    return sum(int(shape.get("max_chars", 0)) for shape in page.get("shapes", []) if isinstance(shape, Mapping))


def materialization_eligible(page: Mapping[str, Any]) -> bool:
    """Return the catalog-certified physical-assembly eligibility.

    Older, explicitly supplied test catalogs have no such record and remain
    readable.  Every compiled production catalog carries this field; a marked
    blocked page is never a query, composition or physical-assembly candidate.
    """

    record = page.get("materialization")
    return record is None or (
        isinstance(record, Mapping) and record.get("status") == "eligible"
    )


def governed_content_slot_count(page: Mapping[str, Any]) -> int:
    """Return certified non-shape data capacity without source content.

    A native chart/table/workbook is editable, but its values are not ordinary
    text slots. The count exposes only whether a client needs a locked
    structured dataset before selecting the page; it never leaks source copy,
    locators, shape IDs, or OPC part names into an agent prompt.
    """

    record = page.get("materialization")
    if not isinstance(record, Mapping):
        return 0
    value = record.get("governed_content_slot_count", 0)
    return value if type(value) is int and value >= 0 else 0


def _observation_for(page: Mapping[str, Any], observations: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any] | None:
    observation = observations.get(str(page.get("page_id")))
    if not isinstance(observation, Mapping):
        return None
    render = page.get("render")
    if not isinstance(render, Mapping) or observation.get("image_sha256") != render.get("image_sha256"):
        return None
    detail = observation.get("observation")
    if not isinstance(detail, Mapping) or detail.get("uncertainty") == "high":
        return None
    return detail


def query_catalog(
    catalog: Mapping[str, Any],
    *,
    observations: Mapping[str, Mapping[str, Any]],
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Query only supplied catalog data; no path, filesystem or model access exists."""

    query = _validate_request(request)
    active = set(catalog.get("active_categories", []))
    pages = {str(page.get("page_id")): page for page in catalog.get("pages", []) if isinstance(page, Mapping)}
    decks = {str(deck.get("deck_id")): deck for deck in catalog.get("decks", []) if isinstance(deck, Mapping)}
    regions = [item for item in catalog.get("regions", []) if isinstance(item, Mapping)]
    bindable_region_count = {
        page_id: sum(1 for item in regions if str(item.get("page_id")) == page_id)
        for page_id in pages
    }
    family_page_count = {
        deck_id: sum(
            1
            for page in pages.values()
            if str(page.get("deck_id")) == deck_id
            and page.get("category") in active
            and materialization_eligible(page)
        )
        for deck_id in decks
    }
    family_visual_quality = {
        deck_id: [
            float(page.get("render", {}).get("visual_quality", 0.0))
            for page in pages.values()
            if str(page.get("deck_id")) == deck_id
            and page.get("category") in active
            and materialization_eligible(page)
            and isinstance(page.get("render"), Mapping)
            and isinstance(page.get("render", {}).get("visual_quality"), (int, float))
        ]
        for deck_id in decks
    }
    family_quality_stats = {
        deck_id: {
            "min": min(values) if values else 0.0,
            "mean": sum(values) / len(values) if values else 0.0,
        }
        for deck_id, values in family_visual_quality.items()
    }
    raw: list[tuple[str, Mapping[str, Any], Mapping[str, Any] | None]] = []
    if query["mode"] == "page":
        raw = [(page_id, page, None) for page_id, page in pages.items()]
    elif query["mode"] == "region":
        raw = [(str(region.get("region_id")), pages.get(str(region.get("page_id")), {}), region) for region in regions]
    else:
        for deck_id, deck in decks.items():
            first = next((page for page in pages.values() if page.get("deck_id") == deck_id), None)
            if first is not None:
                raw.append((deck_id, first, None))
    candidates: list[dict[str, Any]] = []
    for candidate_id, page, region in raw:
        candidate_filter = query["candidate_ids"]
        if candidate_filter is not None and candidate_id not in candidate_filter:
            continue
        if query["deck_id"] is not None and page.get("deck_id") != query["deck_id"]:
            continue
        if not candidate_id or page.get("category") not in active:
            continue
        if not materialization_eligible(page):
            continue
        if query["mode"] == "region" and page.get("component_eligible") is not True:
            continue
        observation = _observation_for(page, observations)
        if observation is None:
            continue
        if not _suitability_safe(observation, profile=query["suitability"]):
            continue
        page_id = str(page.get("page_id"))
        required_regions = minimum_distinct_client_facts(query["role"])
        # A visual five-card layout with only one editable title box is not a
        # reusable five-item page. Filter it before the agent spends a full
        # assembly cycle discovering the mismatch.
        if query["mode"] == "page" and bindable_region_count.get(page_id, 0) < required_regions:
            continue
        if query["mode"] == "page" and not role_matches_page(page, observation, query["role"]):
            continue
        deck_id = str(page.get("deck_id"))
        stats = family_quality_stats.get(deck_id, {"min": 0.0, "mean": 0.0})
        if (
            query["mode"] == "page"
            and query["role"] == "cover"
            and family_page_count.get(deck_id, 0) >= 8
            and stats["min"] < _COMPLETE_FAMILY_MIN_VISUAL_QUALITY
        ):
            continue
        capacity = _capacity(page, region)
        if capacity < query["capacity"]:
            continue
        candidate_style_signature = style_signature_from_observation(observation)
        # ``style`` predates the public signature field and normally denotes a
        # soft visual label (for example ``corporate``).  Once an anchor has
        # been chosen, however, the only deterministic identifier an agent
        # may safely carry into later retrieval is the returned style
        # signature.  Treat that form as an exact hard filter; scoring it as a
        # free-form visual label silently admitted unrelated template decks.
        if query["style"] is not None and query["style"].startswith("style_") and query["style"] != candidate_style_signature:
            continue
        roles = set(observation.get("suggested_roles", []))
        category_roles = _CATEGORY_ROLES.get(str(page.get("category")), frozenset())
        tags = set(observation.get("semantic_tags", []))
        styles = set(observation.get("visual_style", []))
        category_role_score = 1.0 if query["role"] in category_roles else 0.0
        visual_role_score = 1.0 if query["role"] in roles else 0.5
        tag_score = 1.0 if not query["tags"] else len(set(query["tags"]) & tags) / len(query["tags"])
        style_score = 1.0 if (
            query["style"] is None
            or query["style"] == candidate_style_signature
            or query["style"] in styles
        ) else 0.0
        capacity_score = 1.0 if query["capacity"] == 0 else min(1.0, capacity / query["capacity"])
        total = round(
            0.50 * category_role_score
            + 0.20 * visual_role_score
            + 0.20 * tag_score
            + 0.05 * style_score
            + 0.05 * capacity_score,
            6,
        )
        reasons = ["eligible"]
        if category_role_score:
            reasons.append("canonical_category_role")
        if visual_role_score:
            reasons.append("visual_role_match")
        candidates.append({
            "candidate_id": candidate_id,
            "page_id": page["page_id"],
            "deck_id": page.get("deck_id"),
            "theme_family_page_count": family_page_count.get(deck_id, 0),
            "theme_family_visual_quality": {
                "minimum": round(stats["min"], 6),
                "mean": round(stats["mean"], 6),
            },
            "mode": query["mode"],
            "bindable_region_count": bindable_region_count.get(page_id, 0),
            "governed_content_slot_count": governed_content_slot_count(page),
            "requires_structured_data": governed_content_slot_count(page) > 0,
            "style_signature": candidate_style_signature,
            "gates": ["active_source", "materialization", "observation_hash", "capacity"],
            "scores": {"canonical_role": category_role_score, "visual_role": visual_role_score, "tags": round(tag_score, 6), "style": style_score, "capacity": round(capacity_score, 6), "total": total},
            "reasons": reasons,
        })
    # A single-page category cover may carry a perfect canonical-role score
    # while a complete work's coherent cover receives only visual-role credit.
    # For anchor discovery, put the complete eligible family first so the
    # agent can choose a reusable design direction rather than a loud orphan.
    candidates.sort(key=lambda item: (
        -int(item["theme_family_page_count"] >= 8) if query["mode"] == "page" and query["role"] == "cover" else 0,
        -float(item["theme_family_visual_quality"]["mean"]) if query["mode"] == "page" and query["role"] == "cover" else 0,
        -int(item["theme_family_page_count"]) if query["mode"] == "page" and query["role"] == "cover" else 0,
        -item["scores"]["total"],
        item["candidate_id"],
    ))
    selected = candidates[:query["limit"]]
    return {"schema_version": "1.0", "status": "PASS" if selected else "NO_MATCH", "request": query, "candidates": selected}


def inspect_certified_deck(
    catalog: Mapping[str, Any],
    *,
    observations: Mapping[str, Mapping[str, Any]],
    deck_id: str,
) -> dict[str, Any]:
    """Return a bounded, value-free inventory for one already-certified deck.

    A complete work cannot be assembled reliably by asking a model to issue a
    separate semantic-role query for every page: visual classifiers naturally
    call a work-report page ``financial-overview`` rather than the local
    taxonomy's ``five-item``. After a cover query identifies a family, this
    inspection route exposes only family page IDs, source order, safe capacity
    summary and sanitized visual observations. It is not a file-system browse,
    preview export or a route to private template bytes.
    """

    if not isinstance(deck_id, str) or not re.fullmatch(r"deck_[0-9a-f]{24}", deck_id):
        raise QueryError("DECK_ID_INVALID")
    active = set(catalog.get("active_categories", []))
    all_pages = [
        page for page in catalog.get("pages", [])
        if isinstance(page, Mapping)
        and str(page.get("deck_id")) == deck_id
        and page.get("category") in active
        and materialization_eligible(page)
    ]
    if not all_pages:
        return {"schema_version": "1.0", "status": "NO_MATCH", "deck_id": deck_id, "pages": []}
    region_by_page: dict[str, list[Mapping[str, Any]]] = {}
    for region in catalog.get("regions", []):
        if isinstance(region, Mapping):
            region_by_page.setdefault(str(region.get("page_id")), []).append(region)

    pages: list[dict[str, Any]] = []
    for page in sorted(all_pages, key=lambda item: (int(item.get("slide_number", 0)), str(item.get("page_id")))):
        detail = _observation_for(page, observations)
        if detail is None:
            # A complete work can be selected only when every returned page
            # remains hash-bound to a non-uncertain visual observation.
            return {"schema_version": "1.0", "status": "NO_MATCH", "deck_id": deck_id, "pages": []}
        page_regions = region_by_page.get(str(page.get("page_id")), [])
        grammar = {"title": 0, "content": 0}
        for region in page_regions:
            kind = str(region.get("region_kind", "content-item"))
            grammar["title" if kind == "title" else "content"] += len(region.get("editable_shape_ids", []) or [])
        pages.append({
            "page_id": page.get("page_id"),
            "slide_number": page.get("slide_number"),
            "style_signature": style_signature_from_observation(detail),
            "bindable_region_count": len(page_regions),
            "native_text_slot_count": grammar["title"] + grammar["content"],
            "governed_content_slot_count": governed_content_slot_count(page),
            "requires_structured_data": governed_content_slot_count(page) > 0,
            "content_grammar": grammar,
            "visual_observation": {
                "composition": detail.get("composition", ""),
                "hierarchy": detail.get("hierarchy", ""),
                "semantic_tags": list(detail.get("semantic_tags", [])),
                "suggested_roles": list(detail.get("suggested_roles", [])),
                "text_density": detail.get("text_density", ""),
            },
        })
    return {"schema_version": "1.0", "status": "PASS", "deck_id": deck_id, "pages": pages}


def serialize_query_result(result: Mapping[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
