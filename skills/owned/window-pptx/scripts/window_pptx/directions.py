"""Deterministic native-PPTX art-direction registry and selector."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


SKILL_ROOT = Path(__file__).resolve().parents[2]
ART_DIRECTIONS_PATH = SKILL_ROOT / "registries" / "art-directions.json"
ART_DIRECTION_IDS = frozenset(
    {
        "quiet-assertion-evidence",
        "quiet-institutional-grid",
        "quiet-editorial-longform",
        "quiet-research-dense",
        "neutral-consulting-dual-type",
        "neutral-diagram-driven",
        "neutral-diagrammatic-minimal",
        "neutral-narrative-sparkline",
        "bold-mono-brand-poster",
        "bold-stage-keynote",
        "bold-asymmetric-bento",
        "bold-typographic-manifesto",
    }
)


@dataclass(frozen=True)
class ArtDirectionProfile:
    id: str
    temperature: str
    scenario_fit: tuple[str, ...]
    audience_fit: tuple[str, ...]
    asset_requirements: tuple[str, ...]
    theme_candidates: tuple[str, ...]
    typography_scale_id: str
    color_strategy_id: str
    preferred_families: tuple[str, ...]
    forbidden_patterns: tuple[str, ...]
    rhythm_profile: str
    editability_risk: str
    preview_roles: tuple[str, ...]


@dataclass(frozen=True)
class DirectionContext:
    scenario: str
    audience: str | None
    density: str
    tone: str
    locale: str
    available_asset_kinds: frozenset[str]
    has_brand: bool


@dataclass(frozen=True)
class DirectionCandidate:
    slot: str
    profile_id: str
    score: float
    theme_id: str
    reasons: tuple[str, ...]
    asset_gaps: tuple[str, ...]


@dataclass(frozen=True)
class DirectionDecision:
    schema_version: str
    candidates: tuple[DirectionCandidate, ...]
    selected_slot: str
    selected_profile_id: str
    confidence: float
    fallback_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "candidates": [
                {
                    "slot": item.slot,
                    "profile_id": item.profile_id,
                    "score": item.score,
                    "theme_id": item.theme_id,
                    "reasons": list(item.reasons),
                    "asset_gaps": list(item.asset_gaps),
                }
                for item in self.candidates
            ],
            "selected_slot": self.selected_slot,
            "selected_profile_id": self.selected_profile_id,
            "confidence": self.confidence,
            "fallback_reason": self.fallback_reason,
        }


def _strings(value: Any, path: str, *, non_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (non_empty and not value) or not all(
        isinstance(item, str) and item.strip() == item and item for item in value
    ):
        raise ValueError(f"{path} must be a controlled string array")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise ValueError(f"{path} contains duplicates")
    return result


def load_art_directions(path: Path | str | None = None) -> dict[str, ArtDirectionProfile]:
    registry_path = Path(path) if path is not None else ART_DIRECTIONS_PATH
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "profiles"}:
        raise ValueError("art-direction registry root is invalid")
    if raw["schema_version"] != "1.0" or not isinstance(raw["profiles"], list):
        raise ValueError("art-direction schema_version must equal 1.0")
    allowed = {
        "id", "temperature", "scenario_fit", "audience_fit", "asset_requirements",
        "theme_candidates", "typography_scale_id", "color_strategy_id",
        "preferred_families", "forbidden_patterns", "rhythm_profile",
        "editability_risk", "preview_roles",
    }
    result: dict[str, ArtDirectionProfile] = {}
    for index, value in enumerate(raw["profiles"]):
        if not isinstance(value, dict) or set(value) != allowed:
            raise ValueError(f"profiles[{index}] has invalid fields")
        profile = ArtDirectionProfile(
            id=value["id"],
            temperature=value["temperature"],
            scenario_fit=_strings(value["scenario_fit"], f"profiles[{index}].scenario_fit"),
            audience_fit=_strings(value["audience_fit"], f"profiles[{index}].audience_fit"),
            asset_requirements=_strings(value["asset_requirements"], f"profiles[{index}].asset_requirements"),
            theme_candidates=_strings(value["theme_candidates"], f"profiles[{index}].theme_candidates", non_empty=True),
            typography_scale_id=value["typography_scale_id"],
            color_strategy_id=value["color_strategy_id"],
            preferred_families=_strings(value["preferred_families"], f"profiles[{index}].preferred_families", non_empty=True),
            forbidden_patterns=_strings(value["forbidden_patterns"], f"profiles[{index}].forbidden_patterns"),
            rhythm_profile=value["rhythm_profile"],
            editability_risk=value["editability_risk"],
            preview_roles=_strings(value["preview_roles"], f"profiles[{index}].preview_roles", non_empty=True),
        )
        if profile.id in result or profile.temperature not in {"quiet", "neutral", "bold"}:
            raise ValueError(f"profiles[{index}] is duplicated or has invalid temperature")
        if profile.editability_risk not in {"low", "medium"}:
            raise ValueError(f"profiles[{index}] editability risk is invalid")
        result[profile.id] = profile
    if set(result) != ART_DIRECTION_IDS:
        raise ValueError("art-direction registry must contain the exact 12 profiles")
    return result


def _profile_score(profile: ArtDirectionProfile, context: DirectionContext) -> tuple[float, tuple[str, ...], tuple[str, ...]]:
    score = 0.25 if context.scenario in profile.scenario_fit else 0.08
    reasons = ["scenario-fit" if context.scenario in profile.scenario_fit else "scenario-neutral"]
    audience = (context.audience or "").casefold()
    audience_match = any(token.casefold() in audience for token in profile.audience_fit)
    score += 0.15 if audience_match else 0.06
    reasons.append("audience-fit" if audience_match else "audience-neutral")
    density_match = (
        context.density == "dense" and "dense" in profile.rhythm_profile
        or context.density == "sparse" and "spacious" in profile.rhythm_profile
        or context.density == "balanced"
    )
    score += 0.15 if density_match else 0.07
    if context.has_brand:
        score += 0.15
        reasons.append("brand-available")
    else:
        score += 0.08 if profile.temperature != "bold" else 0.02
        reasons.append("brand-unavailable")
    gaps = tuple(sorted(set(profile.asset_requirements) - set(context.available_asset_kinds)))
    score += 0.15 if not gaps else 0.02
    reasons.append("assets-complete" if not gaps else "assets-missing")
    score += 0.10 if profile.editability_risk == "low" else 0.06
    language = context.locale.casefold().split("-", 1)[0]
    score += 0.05 if language in {"zh", "en", "ja", "ko"} else 0.03
    if context.tone == "bold" and profile.temperature == "bold":
        score += 0.05
    if context.tone == "editorial" and "editorial" in profile.id:
        score += 0.05
    return round(min(score, 1.0), 3), tuple(reasons), gaps


def select_art_directions(context: DirectionContext, registry: Mapping[str, ArtDirectionProfile] | None = None) -> DirectionDecision:
    """Return stable safe/editorial/expressive candidates and an auto choice."""

    profiles = dict(registry or load_art_directions())
    buckets = {
        "safe": tuple(item for item in profiles.values() if item.temperature == "quiet"),
        "editorial": tuple(item for item in profiles.values() if item.temperature == "neutral"),
        "expressive": tuple(item for item in profiles.values() if item.temperature == "bold"),
    }
    candidates: list[DirectionCandidate] = []
    for slot, bucket in buckets.items():
        ranked: list[tuple[float, str, ArtDirectionProfile, tuple[str, ...], tuple[str, ...]]] = []
        for profile in bucket:
            score, reasons, gaps = _profile_score(profile, context)
            ranked.append((score, profile.editability_risk, profile, reasons, gaps))
        score, _, profile, reasons, gaps = sorted(
            ranked, key=lambda item: (-item[0], item[1], item[2].id)
        )[0]
        candidates.append(
            DirectionCandidate(
                slot=slot,
                profile_id=profile.id,
                score=score,
                theme_id=profile.theme_candidates[0],
                reasons=reasons,
                asset_gaps=gaps,
            )
        )
    ranked_candidates = sorted(candidates, key=lambda item: (-item.score, item.slot))
    top = ranked_candidates[0]
    gap = top.score - ranked_candidates[1].score
    safe = candidates[0]
    fallback = None
    selected = top
    # Brand absence is already represented in each candidate score.  It must
    # not, by itself, discard a high-confidence scenario/audience match; doing
    # so made every unbranded product launch select an unrelated quiet profile
    # while a different scenario theme was applied downstream.
    if top.score < 0.65 or gap < 0.05 or top.asset_gaps:
        selected = safe
        fallback = "LOW_CONFIDENCE_SAFE_DEFAULT"
    return DirectionDecision(
        "1.0", tuple(candidates), selected.slot, selected.profile_id, selected.score, fallback
    )


def lock_art_direction(
    context: DirectionContext,
    profile_id: str,
    registry: Mapping[str, ArtDirectionProfile] | None = None,
) -> DirectionDecision:
    """Select one registered profile while preserving the three-candidate audit."""

    profiles = dict(registry or load_art_directions())
    if profile_id not in profiles:
        raise ValueError(f"unknown art direction: {profile_id}")
    baseline = select_art_directions(context, profiles)
    profile = profiles[profile_id]
    slot = {"quiet": "safe", "neutral": "editorial", "bold": "expressive"}[
        profile.temperature
    ]
    score, reasons, gaps = _profile_score(profile, context)
    locked = DirectionCandidate(
        slot=slot,
        profile_id=profile.id,
        score=score,
        theme_id=profile.theme_candidates[0],
        reasons=(*reasons, "operator-locked"),
        asset_gaps=gaps,
    )
    candidates = tuple(
        locked if candidate.slot == slot else candidate
        for candidate in baseline.candidates
    )
    return DirectionDecision(
        "1.0",
        candidates,
        slot,
        profile.id,
        score,
        "LOCKED_WITH_ASSET_GAPS" if gaps else None,
    )


def select_proof_slide_ids(compiled: Mapping[str, Any]) -> tuple[str, ...]:
    slides = compiled.get("slides", [])
    if not isinstance(slides, list) or len(slides) < 5:
        return ()
    cover = next((item for item in slides if item.get("role") == "cover"), slides[0])
    weights = {"low": 0, "normal": 1, "high": 2, "critical": 3}
    eligible = [item for item in slides if item is not cover and item.get("role") not in {"closing", "cta"}]
    if not eligible:
        return (cover["id"],)
    def key(item: Mapping[str, Any]) -> tuple[int, int, str]:
        item_count = sum(len(block.get("items", [])) or 1 for block in item.get("blocks", []))
        return (weights.get(item.get("importance", "normal"), 1), item_count, str(item.get("id", "")))
    key_slide = max(eligible, key=key)
    return (str(cover["id"]), str(key_slide["id"]))


__all__ = [
    "ART_DIRECTION_IDS", "ArtDirectionProfile", "DirectionCandidate", "DirectionContext",
    "DirectionDecision", "load_art_directions", "lock_art_direction",
    "select_art_directions", "select_proof_slide_ids",
]
