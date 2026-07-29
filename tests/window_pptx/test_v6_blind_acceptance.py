from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.v6_blind_acceptance import (
    V6_BLIND_IDS,
    V6_REVIEW_DIMENSIONS,
    aggregate_v6_blind_reviews,
)


def report(reviewer_id: str, score: float = 4.5) -> dict:
    candidates = {}
    for blind_id in V6_BLIND_IDS:
        candidates[blind_id] = {
            "scores": {dimension: score for dimension in V6_REVIEW_DIMENSIONS},
            "mean_score": score,
            "reference_parity": True,
            "verdict": "PASS",
            "findings": [],
        }
    return {
        "reviewer_id": reviewer_id,
        "fresh_context": True,
        "candidates": candidates,
        "overall_comment": "Independent visual review.",
    }


def test_v6_blind_acceptance_passes_exact_fresh_matrix() -> None:
    result = aggregate_v6_blind_reviews(
        [report("art"), report("narrative"), report("production")]
    )

    assert result["status"] == "PASS"
    assert result["overall_mean"] == 4.5
    assert result["consensus_failures"] == []


def test_v6_blind_acceptance_fails_same_slide_dimension_consensus() -> None:
    reviews = [report("art"), report("narrative"), report("production")]
    for review in reviews[:2]:
        review["candidates"]["B-001"]["findings"] = [
            {
                "severity": "Important",
                "dimension": "layout_craft",
                "evidence": "Slide 11 repeats a generic horizontal sequence.",
                "issue": "Repeated composition.",
                "repair": "Use a scenario-specific composition.",
            }
        ]

    result = aggregate_v6_blind_reviews(reviews)

    assert result["status"] == "FAIL"
    assert result["reasons"] == ["consensus_blocker_or_important"]
    assert result["consensus_failures"][0]["slide"] == 11


def test_v6_blind_acceptance_rejects_non_fresh_or_incomplete_reviews() -> None:
    reviews = [report("art"), report("narrative"), report("production")]
    reviews[0]["fresh_context"] = False
    with pytest.raises(ValueError, match="fresh_context"):
        aggregate_v6_blind_reviews(reviews)

    reviews = [report("art"), report("narrative"), report("production")]
    del reviews[0]["candidates"]["B-003"]
    with pytest.raises(ValueError, match="exact anonymous candidate set"):
        aggregate_v6_blind_reviews(reviews)


def test_v6_blind_acceptance_accepts_raw_candidate_arrays() -> None:
    reviews = [report("art"), report("narrative"), report("production")]
    for review in reviews:
        review["candidates"] = [
            {"candidate_id": blind_id, **candidate}
            for blind_id, candidate in review["candidates"].items()
        ]

    assert aggregate_v6_blind_reviews(reviews)["status"] == "PASS"
