"""Independent-context AI blind-review contracts for Window-PPTX."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Mapping

from .benchmark import (
    BENCHMARK_SCHEMA_VERSION,
    SHA256_PATTERN,
    BlindReviewPacket,
    canonical_sha256,
)


AI_BLIND_PROTOCOL_ID = "window-pptx-ai-blind-v1"
AI_BLIND_MODEL_ID = "agnes/agnes-2.0-flash"
AI_BLIND_REVIEWER_IDS = (
    "R-AI-ART-DIRECTOR",
    "R-AI-NARRATIVE",
    "R-AI-PRODUCTION",
)
AI_BLIND_RUBRIC = (
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
_VISIBLE_SLIDE_REF = re.compile(r"\bslide\s+0*(\d{1,3})\b", re.IGNORECASE)


def _finding_target(evidence: str) -> tuple[str, ...]:
    """Return the visible slide targets that make two findings the same issue.

    Consensus must refer to the same candidate region, not merely the same
    broad rubric.  Without this key, unrelated observations on Slide 01 and
    Slide 09 are incorrectly merged into a synthetic consensus finding.
    """

    targets = tuple(
        sorted(
            {f"slide-{int(match)}" for match in _VISIBLE_SLIDE_REF.findall(evidence)}
        )
    )
    return targets or ("slide-unspecified",)


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    return dict(value)


def _exact(value: Mapping[str, Any], keys: set[str], path: str) -> None:
    missing = keys - set(value)
    extra = set(value) - keys
    if missing or extra:
        raise ValueError(
            f"{path} keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{path} must be a trimmed non-empty string")
    return value


@dataclass(frozen=True)
class AiBlindFinding:
    severity: str
    dimension: str
    evidence: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "dimension": self.dimension,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class AiBlindReviewUnit:
    schema_version: str
    protocol_id: str
    benchmark_id: str
    packet_sha256: str
    reviewer_id: str
    blind_id: str
    evidence_sha256: str
    model_id: str
    session_id: str
    context_mode: str
    attachment_sha256s: tuple[str, ...]
    prompt_sha256: str
    response_sha256: str
    scores: tuple[tuple[str, int], ...]
    findings: tuple[AiBlindFinding, ...]
    notes: str
    verdict: str

    @property
    def mean_score(self) -> float:
        return sum(score for _rubric, score in self.scores) / len(self.scores)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "protocol_id": self.protocol_id,
            "benchmark_id": self.benchmark_id,
            "packet_sha256": self.packet_sha256,
            "reviewer_id": self.reviewer_id,
            "blind_id": self.blind_id,
            "evidence_sha256": self.evidence_sha256,
            "model_id": self.model_id,
            "session_id": self.session_id,
            "context_mode": self.context_mode,
            "attachment_sha256s": list(self.attachment_sha256s),
            "prompt_sha256": self.prompt_sha256,
            "response_sha256": self.response_sha256,
            "scores": dict(self.scores),
            "findings": [finding.to_dict() for finding in self.findings],
            "notes": self.notes,
            "verdict": self.verdict,
        }


def load_ai_blind_review_unit(
    packet: BlindReviewPacket,
    value: Any,
) -> AiBlindReviewUnit:
    raw = _object(value, "ai_blind_review")
    keys = {
        "schema_version",
        "protocol_id",
        "benchmark_id",
        "packet_sha256",
        "reviewer_id",
        "blind_id",
        "evidence_sha256",
        "model_id",
        "session_id",
        "context_mode",
        "attachment_sha256s",
        "prompt_sha256",
        "response_sha256",
        "scores",
        "findings",
        "notes",
        "verdict",
    }
    _exact(raw, keys, "ai_blind_review")
    if raw["schema_version"] != BENCHMARK_SCHEMA_VERSION:
        raise ValueError("ai_blind_review.schema_version must equal 1.0")
    if raw["protocol_id"] != AI_BLIND_PROTOCOL_ID:
        raise ValueError("ai_blind_review.protocol_id mismatch")
    if raw["benchmark_id"] != packet.benchmark_id:
        raise ValueError("ai_blind_review.benchmark_id mismatch")
    if raw["packet_sha256"] != packet.packet_sha256:
        raise ValueError("ai_blind_review.packet_sha256 mismatch")
    reviewer_id = _text(raw["reviewer_id"], "ai_blind_review.reviewer_id")
    if reviewer_id not in AI_BLIND_REVIEWER_IDS:
        raise ValueError("ai_blind_review.reviewer_id is not frozen")
    blind_id = _text(raw["blind_id"], "ai_blind_review.blind_id")
    entries = {entry.blind_id: entry for entry in packet.entries}
    if blind_id not in entries:
        raise ValueError("ai_blind_review.blind_id is not in the packet")
    entry = entries[blind_id]
    if raw["evidence_sha256"] != entry.evidence_sha256:
        raise ValueError("ai_blind_review.evidence_sha256 mismatch")
    if raw["model_id"] != AI_BLIND_MODEL_ID:
        raise ValueError("ai_blind_review.model_id must use frozen Agnes")
    session_id = _text(raw["session_id"], "ai_blind_review.session_id")
    if (
        re.fullmatch(r"ses_[A-Za-z0-9_-]{8,80}", session_id) is None
        and re.fullmatch(r"[0-9a-f]{24}", session_id) is None
    ):
        raise ValueError("ai_blind_review.session_id is invalid")
    if raw["context_mode"] != "fresh-isolated":
        raise ValueError("ai_blind_review.context_mode must equal fresh-isolated")
    attachment_values = raw["attachment_sha256s"]
    if (
        not isinstance(attachment_values, list)
        or len(attachment_values) < 2
        or len(attachment_values) != len(set(attachment_values))
        or any(
            not isinstance(item, str) or SHA256_PATTERN.fullmatch(item) is None
            for item in attachment_values
        )
    ):
        raise ValueError(
            "ai_blind_review.attachment_sha256s must contain unique SHA-256 values"
        )
    prompt_sha256 = _text(
        raw["prompt_sha256"], "ai_blind_review.prompt_sha256"
    )
    response_sha256 = _text(
        raw["response_sha256"], "ai_blind_review.response_sha256"
    )
    if (
        SHA256_PATTERN.fullmatch(prompt_sha256) is None
        or SHA256_PATTERN.fullmatch(response_sha256) is None
    ):
        raise ValueError("ai_blind_review prompt/response hashes must be SHA-256")
    if tuple(entry.rubric) != AI_BLIND_RUBRIC:
        raise ValueError("blind packet rubric does not match AI blind protocol")
    score_values = _object(raw["scores"], "ai_blind_review.scores")
    _exact(score_values, set(AI_BLIND_RUBRIC), "ai_blind_review.scores")
    scores: list[tuple[str, int]] = []
    for rubric in AI_BLIND_RUBRIC:
        score = score_values[rubric]
        if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
            raise ValueError(
                f"ai_blind_review.scores.{rubric} must be an integer from 1 to 5"
            )
        scores.append((rubric, score))
    finding_values = raw["findings"]
    if not isinstance(finding_values, list):
        raise ValueError("ai_blind_review.findings must be an array")
    findings: list[AiBlindFinding] = []
    for index, value_item in enumerate(finding_values):
        path = f"ai_blind_review.findings[{index}]"
        item = _object(value_item, path)
        _exact(item, {"severity", "dimension", "evidence"}, path)
        severity = _text(item["severity"], f"{path}.severity")
        dimension = _text(item["dimension"], f"{path}.dimension")
        evidence = _text(item["evidence"], f"{path}.evidence")
        if severity not in {"blocker", "important", "nitpick"}:
            raise ValueError(f"{path}.severity is invalid")
        if dimension not in AI_BLIND_RUBRIC:
            raise ValueError(f"{path}.dimension is invalid")
        findings.append(AiBlindFinding(severity, dimension, evidence))
    notes = _text(raw["notes"], "ai_blind_review.notes")
    verdict = raw["verdict"]
    score_map = dict(scores)
    expected_verdict = (
        "PASS"
        if sum(score_map.values()) / len(score_map) >= 4.2
        and min(score_map.values()) >= 4
        else "FAIL"
    )
    if verdict != expected_verdict:
        raise ValueError("ai_blind_review.verdict is inconsistent with scores")
    return AiBlindReviewUnit(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        protocol_id=AI_BLIND_PROTOCOL_ID,
        benchmark_id=packet.benchmark_id,
        packet_sha256=packet.packet_sha256,
        reviewer_id=reviewer_id,
        blind_id=blind_id,
        evidence_sha256=entry.evidence_sha256,
        model_id=AI_BLIND_MODEL_ID,
        session_id=session_id,
        context_mode="fresh-isolated",
        attachment_sha256s=tuple(attachment_values),
        prompt_sha256=prompt_sha256,
        response_sha256=response_sha256,
        scores=tuple(scores),
        findings=tuple(findings),
        notes=notes,
        verdict=expected_verdict,
    )


@dataclass(frozen=True)
class AiBlindAggregateReport:
    schema_version: str
    protocol_id: str
    benchmark_id: str
    packet_sha256: str
    status: str
    milestone_gate_status: str
    reviewer_count: int
    candidate_count: int
    unit_count: int
    coverage: float
    session_uniqueness: float
    overall_mean: float
    dimension_means: tuple[tuple[str, float], ...]
    candidate_means: tuple[tuple[str, float], ...]
    failed_dimensions: tuple[str, ...]
    failed_candidates: tuple[str, ...]
    consensus_blocker_count: int
    consensus_important_count: int
    thresholds: tuple[tuple[str, float], ...]
    unit_bundle_sha256: str
    findings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "protocol_id": self.protocol_id,
            "benchmark_id": self.benchmark_id,
            "packet_sha256": self.packet_sha256,
            "status": self.status,
            "milestone_gate_status": self.milestone_gate_status,
            "reviewer_count": self.reviewer_count,
            "candidate_count": self.candidate_count,
            "unit_count": self.unit_count,
            "coverage": self.coverage,
            "session_uniqueness": self.session_uniqueness,
            "overall_mean": self.overall_mean,
            "dimension_means": dict(self.dimension_means),
            "candidate_means": dict(self.candidate_means),
            "failed_dimensions": list(self.failed_dimensions),
            "failed_candidates": list(self.failed_candidates),
            "consensus_blocker_count": self.consensus_blocker_count,
            "consensus_important_count": self.consensus_important_count,
            "thresholds": dict(self.thresholds),
            "unit_bundle_sha256": self.unit_bundle_sha256,
            "findings": list(self.findings),
        }


def aggregate_ai_blind_reviews(
    packet: BlindReviewPacket,
    units: tuple[AiBlindReviewUnit, ...],
    *,
    overall_threshold: float = 4.2,
    dimension_threshold: float = 4.0,
    candidate_threshold: float = 4.0,
) -> AiBlindAggregateReport:
    for label, value in (
        ("overall_threshold", overall_threshold),
        ("dimension_threshold", dimension_threshold),
        ("candidate_threshold", candidate_threshold),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or not 1 <= float(value) <= 5
        ):
            raise ValueError(f"{label} must be a finite number from 1 to 5")
    expected_grid = {
        (reviewer_id, entry.blind_id)
        for reviewer_id in AI_BLIND_REVIEWER_IDS
        for entry in packet.entries
    }
    observed_grid = {(unit.reviewer_id, unit.blind_id) for unit in units}
    if len(observed_grid) != len(units) or observed_grid != expected_grid:
        raise ValueError("AI blind-review units must cover the exact frozen grid")
    sessions = [unit.session_id for unit in units]
    if len(sessions) != len(set(sessions)):
        raise ValueError("AI blind-review session_id values must be unique")
    if any(
        unit.packet_sha256 != packet.packet_sha256
        or unit.benchmark_id != packet.benchmark_id
        or unit.context_mode != "fresh-isolated"
        or unit.model_id != AI_BLIND_MODEL_ID
        for unit in units
    ):
        raise ValueError("AI blind-review unit provenance mismatch")

    dimension_values = {rubric: [] for rubric in AI_BLIND_RUBRIC}
    candidate_values = {entry.blind_id: [] for entry in packet.entries}
    all_scores: list[int] = []
    consensus: dict[tuple[str, str, str, tuple[str, ...]], set[str]] = {}
    for unit in units:
        for rubric, score in unit.scores:
            dimension_values[rubric].append(score)
            candidate_values[unit.blind_id].append(score)
            all_scores.append(score)
        for finding in unit.findings:
            key = (
                unit.blind_id,
                finding.dimension,
                finding.severity,
                _finding_target(finding.evidence),
            )
            consensus.setdefault(key, set()).add(unit.reviewer_id)
    dimension_means = tuple(
        (rubric, round(sum(values) / len(values), 6))
        for rubric, values in dimension_values.items()
    )
    candidate_means = tuple(
        (blind_id, round(sum(values) / len(values), 6))
        for blind_id, values in candidate_values.items()
    )
    overall_mean = round(sum(all_scores) / len(all_scores), 6)
    failed_dimensions = tuple(
        rubric
        for rubric, mean in dimension_means
        if mean < float(dimension_threshold)
    )
    failed_candidates = tuple(
        blind_id
        for blind_id, mean in candidate_means
        if mean < float(candidate_threshold)
    )
    consensus_blocker_count = sum(
        1
        for (
            _blind_id,
            _dimension,
            severity,
            _target,
        ), reviewers in consensus.items()
        if severity == "blocker" and len(reviewers) >= 2
    )
    consensus_important_count = sum(
        1
        for (
            _blind_id,
            _dimension,
            severity,
            _target,
        ), reviewers in consensus.items()
        if severity == "important" and len(reviewers) >= 2
    )
    findings: list[str] = []
    if overall_mean < float(overall_threshold):
        findings.append(
            f"overall_mean {overall_mean:.3f} is below {overall_threshold:.3f}"
        )
    findings.extend(
        f"dimension {rubric} mean {mean:.3f} is below {dimension_threshold:.3f}"
        for rubric, mean in dimension_means
        if rubric in failed_dimensions
    )
    findings.extend(
        f"candidate {blind_id} mean {mean:.3f} is below {candidate_threshold:.3f}"
        for blind_id, mean in candidate_means
        if blind_id in failed_candidates
    )
    if consensus_blocker_count:
        findings.append(
            f"{consensus_blocker_count} blocker finding(s) reached reviewer consensus"
        )
    if consensus_important_count:
        findings.append(
            f"{consensus_important_count} important finding(s) reached reviewer consensus"
        )
    status = "PASS" if not findings else "FAIL"
    ordered_units = tuple(
        unit.to_dict()
        for unit in sorted(units, key=lambda item: (item.reviewer_id, item.blind_id))
    )
    return AiBlindAggregateReport(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        protocol_id=AI_BLIND_PROTOCOL_ID,
        benchmark_id=packet.benchmark_id,
        packet_sha256=packet.packet_sha256,
        status=status,
        milestone_gate_status=status,
        reviewer_count=len(AI_BLIND_REVIEWER_IDS),
        candidate_count=len(packet.entries),
        unit_count=len(units),
        coverage=1.0,
        session_uniqueness=1.0,
        overall_mean=overall_mean,
        dimension_means=dimension_means,
        candidate_means=candidate_means,
        failed_dimensions=failed_dimensions,
        failed_candidates=failed_candidates,
        consensus_blocker_count=consensus_blocker_count,
        consensus_important_count=consensus_important_count,
        thresholds=(
            ("overall_mean", float(overall_threshold)),
            ("dimension_mean", float(dimension_threshold)),
            ("candidate_mean", float(candidate_threshold)),
        ),
        unit_bundle_sha256=canonical_sha256(ordered_units),
        findings=tuple(findings),
    )


__all__ = [
    "AI_BLIND_MODEL_ID",
    "AI_BLIND_PROTOCOL_ID",
    "AI_BLIND_REVIEWER_IDS",
    "AI_BLIND_RUBRIC",
    "AiBlindAggregateReport",
    "AiBlindFinding",
    "AiBlindReviewUnit",
    "aggregate_ai_blind_reviews",
    "load_ai_blind_review_unit",
]
