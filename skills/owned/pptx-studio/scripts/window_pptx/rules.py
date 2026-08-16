"""Deterministic semantic-to-page ranking for weak-model DeckPlans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


CONFIDENCE_THRESHOLD = 0.62
SAFE_DEFAULT_FAMILY = "structured-content"
STRUCTURAL_ROLE_FAMILIES = {
    "cover": "cover",
    "agenda": "agenda",
    "closing": "cta",
    "section": "section",
}


_CANDIDATES: dict[str, tuple[tuple[str, float], ...]] = {
    "process": (
        ("process", 0.96),
        ("timeline", 0.72),
        ("structured-content", 0.58),
    ),
    "roadmap": (
        ("roadmap", 0.96),
        ("timeline", 0.82),
        ("process", 0.68),
        ("structured-content", 0.58),
    ),
    "quadrant": (
        ("quadrant", 0.96),
        ("matrix", 0.84),
        ("structured-content", 0.58),
    ),
    "funnel": (
        ("funnel", 0.96),
        ("process", 0.76),
        ("data-chart", 0.68),
        ("structured-content", 0.58),
    ),
    "sequence": (
        ("process", 0.94),
        ("timeline", 0.73),
        ("roadmap", 0.65),
        ("structured-content", 0.58),
    ),
    "timeline": (
        ("timeline", 0.95),
        ("roadmap", 0.80),
        ("process", 0.71),
        ("structured-content", 0.58),
    ),
    "comparison": (
        ("comparison", 0.95),
        ("before-after", 0.84),
        ("bar-chart", 0.80),
        ("table", 0.69),
        ("structured-content", 0.58),
    ),
    "categorical-comparison": (
        ("comparison", 0.95),
        ("before-after", 0.84),
        ("bar-chart", 0.80),
        ("table", 0.69),
        ("structured-content", 0.58),
    ),
    "bullets": (
        ("cards", 0.90),
        ("modular-grid", 0.82),
        ("text-media", 0.68),
        ("structured-content", 0.60),
    ),
    "metrics": (
        ("big-number", 0.96),
        ("kpi-dashboard", 0.86),
        ("focal-statement", 0.70),
        ("bar-chart", 0.65),
        ("structured-content", 0.57),
    ),
    "trend": (
        ("line-chart", 0.96),
        ("area-chart", 0.84),
        ("bar-chart", 0.72),
        ("structured-content", 0.58),
    ),
    "composition": (
        ("composition-chart", 0.94),
        ("stacked-bar", 0.85),
        ("bar-chart", 0.72),
        ("structured-content", 0.58),
    ),
    "distribution": (
        ("distribution-chart", 0.94),
        ("bar-chart", 0.82),
        ("dot-plot", 0.73),
        ("structured-content", 0.58),
    ),
    "relationship": (
        ("scatter-plot", 0.94),
        ("bubble-chart", 0.82),
        ("matrix", 0.68),
        ("structured-content", 0.58),
    ),
    "matrix": (
        ("matrix", 0.95),
        ("quadrant", 0.83),
        ("table", 0.68),
        ("structured-content", 0.58),
    ),
    "risk": (
        ("risk-recommendation", 0.94),
        ("matrix", 0.75),
        ("focal-statement", 0.72),
        ("cards", 0.69),
        ("structured-content", 0.60),
    ),
    "recommendation": (
        ("recommendation", 0.95),
        ("roadmap", 0.78),
        ("focal-statement", 0.72),
        ("cards", 0.71),
        ("structured-content", 0.60),
    ),
    "quote": (
        ("focal-statement", 0.95),
        ("text-media", 0.72),
        ("image-story", 0.63),
        ("structured-content", 0.59),
    ),
    "statement": (
        ("focal-statement", 0.78),
        ("text-media", 0.70),
        ("structured-content", 0.65),
        ("cards", 0.55),
    ),
    "table": (
        ("table", 0.96),
        ("comparison", 0.70),
        ("structured-content", 0.62),
        ("cards", 0.57),
    ),
    "image": (
        ("image-story", 0.95),
        ("text-media", 0.78),
        ("product-showcase", 0.70),
        ("structured-content", 0.56),
    ),
    "generic": (
        ("focal-statement", 0.56),
        ("text-media", 0.55),
        ("cards", 0.54),
        ("structured-content", 0.53),
    ),
}


@dataclass(frozen=True)
class CandidateScore:
    """One page-family candidate and the rules that produced its score."""

    candidate_id: str
    score: float
    rule_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "score": self.score,
            "rule_ids": list(self.rule_ids),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class DecisionTrace:
    """Serializable explanation for a deterministic page-family decision."""

    semantic_type: str
    selected: str
    confidence: float
    confidence_threshold: float
    top_candidates: tuple[CandidateScore, ...]
    rejected_candidates: tuple[CandidateScore, ...]
    fallback_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_type": self.semantic_type,
            "selected": self.selected,
            "confidence": self.confidence,
            "confidence_threshold": self.confidence_threshold,
            "top_candidates": [candidate.to_dict() for candidate in self.top_candidates],
            "rejected_candidates": [
                candidate.to_dict() for candidate in self.rejected_candidates
            ],
            "fallback_reason": self.fallback_reason,
        }


def _score_candidate(
    semantic_type: str,
    candidate_id: str,
    base_score: float,
    item_count: int,
    previous_families: tuple[str, ...],
    preferred_families: frozenset[str],
) -> CandidateScore:
    score = base_score
    rule_ids = [f"SEMANTIC_{semantic_type.upper().replace('-', '_')}"]
    reasons = [f"registered semantic fit for {semantic_type}"]

    governed_family = {
        "line-chart": "data-chart",
        "area-chart": "data-chart",
        "bar-chart": "data-chart",
        "composition-chart": "data-chart",
        "stacked-bar": "data-chart",
        "distribution-chart": "data-chart",
        "dot-plot": "data-chart",
        "scatter-plot": "data-chart",
        "bubble-chart": "data-chart",
        "before-after": "comparison",
        "recommendation": "risk-recommendation",
        "modular-grid": "cards",
    }.get(candidate_id, candidate_id)
    if candidate_id in preferred_families or governed_family in preferred_families:
        score += 0.05
        rule_ids.append("ART_DIRECTION_FAMILY_PREFERENCE")
        reasons.append("preferred by the selected governed art direction")

    repeat_count = 0
    for previous in reversed(previous_families):
        if previous != candidate_id:
            break
        repeat_count += 1
    if repeat_count >= 2:
        score -= 0.35
        rule_ids.append("RHYTHM_REPEAT_2")
        reasons.append("penalized after two consecutive uses")
    elif repeat_count == 1:
        score -= 0.08
        rule_ids.append("RHYTHM_REPEAT_1")
        reasons.append("penalized after one consecutive use")

    if semantic_type == "bullets" and item_count == 1:
        if candidate_id == "text-media":
            score += 0.20
            rule_ids.append("SPARSE_SINGLE_POINT")
            reasons.append("single point receives a quieter emphasis form")
        elif candidate_id in {"cards", "modular-grid"}:
            score -= 0.18
            rule_ids.append("SPARSE_AVOID_EMPTY_CARDS")
            reasons.append("avoids manufacturing empty peer modules")
    if semantic_type == "bullets" and item_count >= 4 and candidate_id == "modular-grid":
        score += 0.03
        rule_ids.append("PARALLEL_DENSITY_GRID")
        reasons.append("four parallel points fit a governed grid")
    if semantic_type == "metrics":
        if item_count <= 1:
            if candidate_id == "big-number":
                score += 0.04
                rule_ids.append("SINGLE_METRIC_HERO")
                reasons.append("one metric receives a governed hero treatment")
                if repeat_count == 1:
                    score -= 0.25
                    rule_ids.append("METRIC_HERO_RHYTHM_BREAK")
                    reasons.append(
                        "a second consecutive single-metric page switches composition"
                    )
            elif candidate_id == "kpi-dashboard":
                score -= 0.22
                rule_ids.append("SINGLE_METRIC_AVOID_DASHBOARD")
                reasons.append("one metric does not require a dashboard grid")
            elif candidate_id == "bar-chart":
                score -= 0.15
                rule_ids.append("SINGLE_METRIC_AVOID_CHART")
                reasons.append("one scalar does not justify a categorical chart")
        elif item_count <= 4:
            if candidate_id == "kpi-dashboard":
                score += 0.14
                rule_ids.append("MULTI_METRIC_DASHBOARD")
                reasons.append("parallel metrics receive a governed KPI composition")
            elif candidate_id == "big-number":
                score -= 0.18
                rule_ids.append("MULTI_METRIC_AVOID_SINGLE_HERO")
                reasons.append("multiple metrics should not share one hero slot")
    if (
        semantic_type == "categorical-comparison"
        and 2 <= item_count <= 6
        and candidate_id == "bar-chart"
        and "data-chart" in preferred_families
    ):
        score += 0.16
        rule_ids.append("ANALYTICAL_COMPARISON_BAR_CHART")
        reasons.append(
            "the selected analytical direction turns a structured comparison into a bar chart"
        )
    if semantic_type in {"risk", "recommendation"} and item_count == 1:
        if candidate_id == "focal-statement":
            score += 0.10
            rule_ids.append("SPARSE_SINGLE_DECISION")
            reasons.append("one decision receives a complete focal composition")
        elif candidate_id == "recommendation" and semantic_type == "recommendation":
            score += 0.05
            rule_ids.append("SINGLE_RECOMMENDATION_FOCUS")
            reasons.append("one recommendation receives a governed focus panel")
        elif candidate_id in {"risk-recommendation", "matrix", "roadmap", "cards"}:
            score -= 0.20
            rule_ids.append("SPARSE_AVOID_EMPTY_PEERS")
            reasons.append("avoids manufacturing an empty comparison or matrix peer")

    return CandidateScore(
        candidate_id=candidate_id,
        score=round(max(0.0, min(1.0, score)), 3),
        rule_ids=tuple(rule_ids),
        reasons=tuple(reasons),
    )


def rank_page_families(
    semantic_type: str,
    *,
    item_count: int = 0,
    previous_families: Iterable[str] = (),
    preferred_families: Iterable[str] = (),
    structural_role: str | None = None,
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
) -> DecisionTrace:
    """Rank registered page families with stable ties and rhythm penalties."""

    normalized = (
        semantic_type.casefold().strip() if isinstance(semantic_type, str) else ""
    )
    normalized_role = (
        structural_role.casefold().strip()
        if isinstance(structural_role, str)
        else ""
    )
    structural_family = STRUCTURAL_ROLE_FAMILIES.get(normalized_role)
    if structural_family is not None:
        rule_id = f"STRUCTURAL_ROLE_{normalized_role.upper()}"
        selected = CandidateScore(
            candidate_id=structural_family,
            score=1.0,
            rule_ids=(rule_id,),
            reasons=(
                f"structural role {normalized_role} requires the governed "
                f"{structural_family} family",
            ),
        )
        return DecisionTrace(
            semantic_type=normalized or "generic",
            selected=structural_family,
            confidence=1.0,
            confidence_threshold=confidence_threshold,
            top_candidates=(selected,),
            rejected_candidates=(),
            fallback_reason=None,
        )
    candidates = _CANDIDATES.get(normalized, _CANDIDATES["generic"])
    history = tuple(previous_families)
    preferences = frozenset(preferred_families)
    scored = [
        _score_candidate(
            normalized or "generic",
            candidate_id,
            score,
            item_count,
            history,
            preferences,
        )
        for candidate_id, score in candidates
    ]
    ranked = tuple(sorted(scored, key=lambda item: (-item.score, item.candidate_id)))
    confidence = ranked[0].score
    if confidence < confidence_threshold:
        selected = SAFE_DEFAULT_FAMILY
        fallback_reason = "LOW_CONFIDENCE_SAFE_DEFAULT"
        registered_default = next(
            (item for item in ranked if item.candidate_id == SAFE_DEFAULT_FAMILY),
            CandidateScore(
                candidate_id=SAFE_DEFAULT_FAMILY,
                score=confidence,
                rule_ids=(),
                reasons=(),
            ),
        )
        selected_candidate = CandidateScore(
            candidate_id=registered_default.candidate_id,
            score=registered_default.score,
            rule_ids=registered_default.rule_ids + (fallback_reason,),
            reasons=registered_default.reasons
            + ("selected by the governed low-confidence fallback policy",),
        )
        ordered = (selected_candidate,) + tuple(
            item for item in ranked if item.candidate_id != SAFE_DEFAULT_FAMILY
        )
    else:
        selected = ranked[0].candidate_id
        fallback_reason = None
        ordered = ranked
    return DecisionTrace(
        semantic_type=normalized or "generic",
        selected=selected,
        confidence=confidence,
        confidence_threshold=confidence_threshold,
        top_candidates=ordered[:3],
        rejected_candidates=ordered[3:],
        fallback_reason=fallback_reason,
    )
