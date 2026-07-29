"""Fail-closed acceptance for the v6 independent-context visual review matrix."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping, Sequence


V6_REVIEW_DIMENSIONS = (
    "narrative_logic",
    "visual_hierarchy",
    "layout_craft",
    "typography_readability",
    "data_visualization",
    "visual_rhythm",
    "brand_coherence",
    "editability_likelihood",
    "delivery_readiness",
)
V6_BLIND_IDS = ("B-001", "B-002", "B-003")
_SLIDE = re.compile(r"\bslide\s+0*(\d{1,3})\b", re.IGNORECASE)


def _object(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object")
    return value


def _score(value: Any, path: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or not 1 <= float(value) <= 5
    ):
        raise ValueError(f"{path} must be a finite score from 1 to 5")
    return float(value)


def _mean_matches_reported_precision(
    reported_mean: float,
    values: Sequence[float],
) -> bool:
    reported = Decimal(str(reported_mean))
    precision = max(1, -reported.as_tuple().exponent)
    quantum = Decimal(1).scaleb(-precision)
    computed = sum((Decimal(str(value)) for value in values), Decimal(0)) / Decimal(
        len(values)
    )
    return reported == computed.quantize(quantum, rounding=ROUND_HALF_UP)


def aggregate_v6_blind_reviews(
    reviews: Sequence[Mapping[str, Any]],
    *,
    overall_threshold: float = 4.3,
    dimension_threshold: float = 4.1,
    candidate_threshold: float = 4.2,
    parity_reviewer_floor: int = 2,
) -> dict[str, Any]:
    """Aggregate three anonymous reviewer reports with conservative consensus."""

    if len(reviews) != 3:
        raise ValueError("exactly three independent reviewer reports are required")
    reviewer_ids = [str(review.get("reviewer_id", "")).strip() for review in reviews]
    if not all(reviewer_ids) or len(set(reviewer_ids)) != 3:
        raise ValueError("reviewer_id values must be non-empty and unique")
    if any(review.get("fresh_context") is not True for review in reviews):
        raise ValueError("every reviewer must declare fresh_context=true")

    dimension_values: dict[str, list[float]] = defaultdict(list)
    candidate_values: dict[str, list[float]] = defaultdict(list)
    parity_counts: dict[str, int] = defaultdict(int)
    consensus: dict[tuple[str, str, str, int], set[str]] = defaultdict(set)

    for review, reviewer_id in zip(reviews, reviewer_ids, strict=True):
        candidate_value = review.get("candidates")
        if isinstance(candidate_value, list):
            candidates = {
                str(_object(item, f"{reviewer_id}.candidate").get("candidate_id", "")): item
                for item in candidate_value
            }
        else:
            candidates = _object(candidate_value, f"{reviewer_id}.candidates")
        if set(candidates) != set(V6_BLIND_IDS):
            raise ValueError(f"{reviewer_id} must cover the exact anonymous candidate set")
        for blind_id in V6_BLIND_IDS:
            candidate = _object(candidates[blind_id], f"{reviewer_id}.{blind_id}")
            scores = _object(candidate.get("scores"), f"{reviewer_id}.{blind_id}.scores")
            if set(scores) != set(V6_REVIEW_DIMENSIONS):
                raise ValueError(f"{reviewer_id}.{blind_id}.scores dimensions mismatch")
            values = []
            for dimension in V6_REVIEW_DIMENSIONS:
                value = _score(
                    scores[dimension],
                    f"{reviewer_id}.{blind_id}.scores.{dimension}",
                )
                values.append(value)
                dimension_values[dimension].append(value)
                candidate_values[blind_id].append(value)
            reported_mean = _score(
                candidate.get("mean_score"),
                f"{reviewer_id}.{blind_id}.mean_score",
            )
            if not _mean_matches_reported_precision(reported_mean, values):
                raise ValueError(f"{reviewer_id}.{blind_id}.mean_score is inconsistent")
            if not isinstance(candidate.get("reference_parity"), bool):
                raise ValueError(f"{reviewer_id}.{blind_id}.reference_parity must be boolean")
            parity_counts[blind_id] += int(candidate["reference_parity"])
            findings = candidate.get("findings", [])
            if not isinstance(findings, list):
                raise ValueError(f"{reviewer_id}.{blind_id}.findings must be an array")
            for finding in findings:
                item = _object(finding, f"{reviewer_id}.{blind_id}.finding")
                severity = str(item.get("severity", "")).strip().lower()
                dimension = str(item.get("dimension", "")).strip()
                evidence = str(item.get("evidence", "")).strip()
                if severity not in {"blocker", "important", "minor"}:
                    raise ValueError("finding severity must be Blocker, Important, or Minor")
                if dimension not in V6_REVIEW_DIMENSIONS:
                    raise ValueError("finding dimension is not frozen")
                slides = {int(value) for value in _SLIDE.findall(evidence)}
                if not slides:
                    raise ValueError("every finding must cite at least one visible Slide NN")
                if severity in {"blocker", "important"}:
                    for slide in slides:
                        consensus[(blind_id, dimension, severity, slide)].add(reviewer_id)

    dimension_means = {
        key: round(sum(values) / len(values), 3)
        for key, values in dimension_values.items()
    }
    candidate_means = {
        key: round(sum(values) / len(values), 3)
        for key, values in candidate_values.items()
    }
    all_values = [value for values in candidate_values.values() for value in values]
    overall_mean = round(sum(all_values) / len(all_values), 3)
    consensus_failures = [
        {
            "blind_id": key[0],
            "dimension": key[1],
            "severity": key[2],
            "slide": key[3],
            "reviewers": sorted(reviewers),
        }
        for key, reviewers in sorted(consensus.items())
        if len(reviewers) >= 2
    ]
    failed_dimensions = sorted(
        key for key, value in dimension_means.items() if value < dimension_threshold
    )
    failed_candidates = sorted(
        key for key, value in candidate_means.items() if value < candidate_threshold
    )
    failed_parity = sorted(
        key for key in V6_BLIND_IDS if parity_counts[key] < parity_reviewer_floor
    )
    reasons = []
    if overall_mean < overall_threshold:
        reasons.append("overall_mean_below_floor")
    if failed_dimensions:
        reasons.append("dimension_mean_below_floor")
    if failed_candidates:
        reasons.append("candidate_mean_below_floor")
    if failed_parity:
        reasons.append("reference_parity_below_floor")
    if consensus_failures:
        reasons.append("consensus_blocker_or_important")
    return {
        "schema_version": "1.0",
        "protocol_id": "window-pptx-v6-independent-gpt55-v1",
        "status": "PASS" if not reasons else "FAIL",
        "reviewer_ids": reviewer_ids,
        "reviewer_count": 3,
        "candidate_count": 3,
        "overall_mean": overall_mean,
        "dimension_means": dimension_means,
        "candidate_means": candidate_means,
        "reference_parity_counts": dict(sorted(parity_counts.items())),
        "failed_dimensions": failed_dimensions,
        "failed_candidates": failed_candidates,
        "failed_reference_parity": failed_parity,
        "consensus_failures": consensus_failures,
        "thresholds": {
            "overall_mean": overall_threshold,
            "dimension_mean": dimension_threshold,
            "candidate_mean": candidate_threshold,
            "reference_parity_reviewers": parity_reviewer_floor,
            "consensus_reviewers": 2,
        },
        "reasons": reasons,
    }


__all__ = [
    "V6_BLIND_IDS",
    "V6_REVIEW_DIMENSIONS",
    "aggregate_v6_blind_reviews",
]
