"""Bounded deterministic retrieval over compiled PPTX Studio catalog records."""

from __future__ import annotations

import json
import hashlib
from typing import Any, Mapping


class QueryError(ValueError):
    """Raised for an invalid query instead of falling back to file discovery."""


_ALLOWED_REQUEST = {"mode", "role", "tags", "style", "capacity", "limit", "suitability"}
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
    return {"mode": mode, "role": role, "tags": _normal_tags(request.get("tags")), "style": style, "capacity": capacity, "limit": limit, "suitability": suitability}


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
        if not candidate_id or page.get("category") not in active:
            continue
        if query["mode"] == "region" and page.get("component_eligible") is not True:
            continue
        observation = _observation_for(page, observations)
        if observation is None:
            continue
        if not _suitability_safe(observation, profile=query["suitability"]):
            continue
        capacity = _capacity(page, region)
        if capacity < query["capacity"]:
            continue
        roles = set(observation.get("suggested_roles", []))
        category_roles = _CATEGORY_ROLES.get(str(page.get("category")), frozenset())
        tags = set(observation.get("semantic_tags", []))
        styles = set(observation.get("visual_style", []))
        category_role_score = 1.0 if query["role"] in category_roles else 0.0
        visual_role_score = 1.0 if query["role"] in roles else 0.0
        tag_score = 1.0 if not query["tags"] else len(set(query["tags"]) & tags) / len(query["tags"])
        style_score = 1.0 if query["style"] is None or query["style"] in styles else 0.0
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
            "mode": query["mode"],
            "style_signature": style_signature_from_observation(observation),
            "gates": ["active_source", "observation_hash", "capacity"],
            "scores": {"canonical_role": category_role_score, "visual_role": visual_role_score, "tags": round(tag_score, 6), "style": style_score, "capacity": round(capacity_score, 6), "total": total},
            "reasons": reasons,
        })
    candidates.sort(key=lambda item: (-item["scores"]["total"], item["candidate_id"]))
    selected = candidates[:query["limit"]]
    return {"schema_version": "1.0", "status": "PASS" if selected else "NO_MATCH", "request": query, "candidates": selected}


def serialize_query_result(result: Mapping[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
