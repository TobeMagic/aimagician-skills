from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.ai_blind_review import (  # noqa: E402
    AI_BLIND_REVIEWER_IDS,
    aggregate_ai_blind_reviews,
    load_ai_blind_review_unit,
)
from window_pptx.benchmark import (  # noqa: E402
    BlindReviewArtifact,
    BlindReviewEntry,
    BlindReviewPacket,
    canonical_sha256,
)


RUBRIC = (
    "narrative_clarity",
    "content_accuracy",
    "visual_hierarchy",
    "layout_fitness_variety",
    "readability",
    "chart_diagram_appropriateness",
    "brand_consistency",
    "editability",
    "customer_delivery_readiness",
)


def packet_fixture() -> BlindReviewPacket:
    entries = tuple(
        BlindReviewEntry(
            blind_id=f"B-00{index}-{index:08x}",
            scenario_id=f"scenario-{index}",
            evidence_sha256=f"{index}" * 64,
            rubric=RUBRIC,
            artifacts=(
                BlindReviewArtifact(
                    kind="editable-pptx",
                    review_path=f"B-00{index}-{index:08x}/delivery.pptx",
                    sha256="a" * 64,
                    size_bytes=100,
                ),
                BlindReviewArtifact(
                    kind="slide-preview",
                    review_path=f"B-00{index}-{index:08x}/slide-001.png",
                    sha256="b" * 64,
                    size_bytes=100,
                ),
            ),
        )
        for index in (1, 2)
    )
    basis = {
        "schema_version": "1.0",
        "benchmark_id": "fixture",
        "delivery_evidence_ready": True,
        "entries": [entry.to_dict() for entry in entries],
    }
    return BlindReviewPacket(
        schema_version="1.0",
        benchmark_id="fixture",
        packet_sha256=canonical_sha256(basis),
        delivery_evidence_ready=True,
        entries=entries,
    )


def unit_payload(
    packet: BlindReviewPacket,
    *,
    reviewer_id: str,
    blind_id: str,
    session_id: str,
    scores: dict[str, int] | None = None,
    findings: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    entry = next(item for item in packet.entries if item.blind_id == blind_id)
    resolved_scores = scores or {rubric: 5 for rubric in RUBRIC}
    local_pass = (
        sum(resolved_scores.values()) / len(resolved_scores) >= 4.2
        and min(resolved_scores.values()) >= 4
    )
    return {
        "schema_version": "1.0",
        "protocol_id": "pptx-studio-ai-blind-v1",
        "benchmark_id": packet.benchmark_id,
        "packet_sha256": packet.packet_sha256,
        "reviewer_id": reviewer_id,
        "blind_id": blind_id,
        "evidence_sha256": entry.evidence_sha256,
        "model_id": "agnes/agnes-2.0-flash",
        "session_id": session_id,
        "context_mode": "fresh-isolated",
        "attachment_sha256s": ["c" * 64, "d" * 64],
        "prompt_sha256": "e" * 64,
        "response_sha256": "f" * 64,
        "scores": resolved_scores,
        "findings": findings or [],
        "notes": "Independent image-only blind review.",
        "verdict": "PASS" if local_pass else "FAIL",
    }


def test_ai_blind_unit_requires_fresh_agnes_provenance_and_exact_scores() -> None:
    packet = packet_fixture()
    payload = unit_payload(
        packet,
        reviewer_id=AI_BLIND_REVIEWER_IDS[0],
        blind_id=packet.entries[0].blind_id,
        session_id="ses_unique_001",
    )

    unit = load_ai_blind_review_unit(packet, payload)

    assert unit.context_mode == "fresh-isolated"
    assert unit.model_id == "agnes/agnes-2.0-flash"
    assert dict(unit.scores) == {rubric: 5 for rubric in RUBRIC}

    payload["session_id"] = "0123456789abcdef01234567"
    assert load_ai_blind_review_unit(packet, payload).session_id == payload["session_id"]

    payload["context_mode"] = "continued"
    with pytest.raises(ValueError, match="fresh-isolated"):
        load_ai_blind_review_unit(packet, payload)


def test_ai_blind_aggregate_requires_complete_unique_session_grid() -> None:
    packet = packet_fixture()
    units = []
    for reviewer_index, reviewer_id in enumerate(AI_BLIND_REVIEWER_IDS, start=1):
        for entry_index, entry in enumerate(packet.entries, start=1):
            units.append(
                load_ai_blind_review_unit(
                    packet,
                    unit_payload(
                        packet,
                        reviewer_id=reviewer_id,
                        blind_id=entry.blind_id,
                        session_id=f"ses_unique_{reviewer_index}_{entry_index}",
                    ),
                )
            )

    report = aggregate_ai_blind_reviews(packet, tuple(units))

    assert report.status == "PASS"
    assert report.milestone_gate_status == "PASS"
    assert report.session_uniqueness == 1.0
    assert report.coverage == 1.0
    assert report.overall_mean == 5.0

    duplicate = list(units)
    duplicate[-1] = duplicate[-1].__class__(
        **{
            **duplicate[-1].__dict__,
            "session_id": duplicate[0].session_id,
        }
    )
    with pytest.raises(ValueError, match="session_id values must be unique"):
        aggregate_ai_blind_reviews(packet, tuple(duplicate))


def test_ai_blind_aggregate_fails_candidate_floor_and_consensus_important() -> None:
    packet = packet_fixture()
    units = []
    weak_entry = packet.entries[1]
    for reviewer_index, reviewer_id in enumerate(AI_BLIND_REVIEWER_IDS, start=1):
        for entry_index, entry in enumerate(packet.entries, start=1):
            scores = {rubric: 5 for rubric in RUBRIC}
            findings: list[dict[str, str]] = []
            if entry == weak_entry:
                scores = {rubric: 3 for rubric in RUBRIC}
                if reviewer_index <= 2:
                    findings = [
                        {
                            "severity": "important",
                            "dimension": "readability",
                            "evidence": "Slide 04 labels are visibly too small.",
                        }
                    ]
            units.append(
                load_ai_blind_review_unit(
                    packet,
                    unit_payload(
                        packet,
                        reviewer_id=reviewer_id,
                        blind_id=entry.blind_id,
                        session_id=f"ses_fail_{reviewer_index}_{entry_index}",
                        scores=scores,
                        findings=findings,
                    ),
                )
            )

    report = aggregate_ai_blind_reviews(packet, tuple(units))

    assert report.status == "FAIL"
    assert report.milestone_gate_status == "FAIL"
    assert weak_entry.blind_id in report.failed_candidates
    assert report.consensus_important_count == 1


def test_ai_blind_consensus_requires_same_visible_slide_target() -> None:
    packet = packet_fixture()
    units = []
    for reviewer_index, reviewer_id in enumerate(AI_BLIND_REVIEWER_IDS, start=1):
        for entry_index, entry in enumerate(packet.entries, start=1):
            findings: list[dict[str, str]] = []
            if entry_index == 1 and reviewer_index <= 2:
                findings = [
                    {
                        "severity": "important",
                        "dimension": "layout_fitness_variety",
                        "evidence": (
                            "Slide 02 has an imbalanced card."
                            if reviewer_index == 1
                            else "Slide 08 repeats a card composition."
                        ),
                    }
                ]
            units.append(
                load_ai_blind_review_unit(
                    packet,
                    unit_payload(
                        packet,
                        reviewer_id=reviewer_id,
                        blind_id=entry.blind_id,
                        session_id=f"ses_target_{reviewer_index}_{entry_index}",
                        findings=findings,
                    ),
                )
            )

    report = aggregate_ai_blind_reviews(packet, tuple(units))

    assert report.status == "PASS"
    assert report.consensus_important_count == 0


def test_ai_blind_unit_rejects_model_verdict_inconsistent_with_scores() -> None:
    packet = packet_fixture()
    payload = unit_payload(
        packet,
        reviewer_id=AI_BLIND_REVIEWER_IDS[0],
        blind_id=packet.entries[0].blind_id,
        session_id="ses_inconsistent",
    )
    payload["verdict"] = "FAIL"

    with pytest.raises(ValueError, match="verdict is inconsistent"):
        load_ai_blind_review_unit(packet, payload)
