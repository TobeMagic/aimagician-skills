"""Deterministic, fail-closed v6.1 visual blind-review acceptance.

The authoring agent is not allowed to score or release its own deck.  This
module consumes six hash-bound Agnes segment records and three fresh-context
review syntheses.  It deliberately distinguishes an unavailable/untrustworthy
review round (``NOT_RUN``) from a complete round that found material visual
defects (``FAIL``).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence


V61_BLIND_PROTOCOL_ID = "window-pptx-v61-blind-v1"
V61_REVIEWER_IDS = ("ART", "NARRATIVE", "PRODUCTION")
V61_SEGMENT_SLIDES = {
    "SLIDES_01_08": tuple(range(1, 9)),
    "SLIDES_09_15": tuple(range(9, 16)),
}
V61_REVIEW_DIMENSIONS = (
    "narrative_logic",
    "visual_hierarchy",
    "layout_craft",
    "typography_readability",
    "data_visualization",
    "visual_rhythm",
    "brand_coherence",
    "art_direction",
    "delivery_readiness",
)
V61_REVIEW_MEDIAN_THRESHOLD = Decimal("8")
V61_AGNES_ROUTE_ID = "agnes-direct/agnes-2.0-flash"
V61_AGNES_MODEL_ID = "agnes-2.0-flash"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EXECUTION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,159}$")
_SEGMENT_REQUIRED_KEYS = {
    "schema_version",
    "protocol_id",
    "reviewer_id",
    "segment_id",
    "packet_sha256",
    "rubric_sha256",
    "route_id",
    "model_id",
    "invocation_id",
    "context_mode",
    "image_sha256s",
    "request_sha256",
    "response_sha256",
    "status",
    "inspected_slides",
    "observations",
}
_REVIEW_REQUIRED_KEYS = {
    "schema_version",
    "protocol_id",
    "reviewer_id",
    "packet_sha256",
    "rubric_sha256",
    "synthesis_model_id",
    "synthesis_context_id",
    "context_mode",
    "prompt_sha256",
    "response_sha256",
    "segment_refs",
    "inspected_slides",
    "scores",
    "median_score",
    "reference_parity",
    "findings",
    "status",
    "notes",
}


@dataclass(frozen=True)
class HashedJsonDocument:
    """A parsed JSON object plus the SHA-256 of its exact serialized bytes."""

    source: str
    value: Mapping[str, Any]
    sha256: str


@dataclass(frozen=True)
class _VisualSegment:
    document: HashedJsonDocument
    reviewer_id: str
    segment_id: str
    packet_sha256: str
    rubric_sha256: str
    invocation_id: str
    status: str


@dataclass(frozen=True)
class _SegmentRef:
    segment_id: str
    document_sha256: str
    invocation_id: str


@dataclass(frozen=True)
class _Finding:
    severity: str
    dimension: str
    slides: tuple[int, ...]
    evidence: str


@dataclass(frozen=True)
class _BlindReview:
    document: HashedJsonDocument
    reviewer_id: str
    packet_sha256: str
    rubric_sha256: str
    synthesis_context_id: str
    status: str
    segment_refs: tuple[_SegmentRef, ...]
    scores: tuple[tuple[str, Decimal], ...]
    reported_median: Decimal
    reference_parity: bool
    findings: tuple[_Finding, ...]

    @property
    def recomputed_median(self) -> Decimal:
        ordered = sorted(score for _dimension, score in self.scores)
        return ordered[len(ordered) // 2]

    @property
    def finding_counts(self) -> dict[str, int]:
        return {
            severity: sum(
                finding.severity == severity for finding in self.findings
            )
            for severity in ("Blocker", "Important", "Nitpick")
        }

    @property
    def recomputed_status(self) -> str:
        counts = self.finding_counts
        return (
            "PASS"
            if self.recomputed_median >= V61_REVIEW_MEDIAN_THRESHOLD
            and self.reference_parity
            and counts["Blocker"] == 0
            and counts["Important"] == 0
            else "FAIL"
        )


class _ContractError(ValueError):
    def __init__(
        self,
        code: str,
        detail: str,
        *,
        reviewer_id: str | None = None,
        segment_id: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.reviewer_id = reviewer_id
        self.segment_id = segment_id


def canonical_document_bytes(value: Mapping[str, Any]) -> bytes:
    """Serialize an in-memory fixture with the canonical v6.1 JSON encoding."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def hashed_document(
    value: Mapping[str, Any], *, source: str = "<memory>"
) -> HashedJsonDocument:
    payload = canonical_document_bytes(value)
    return HashedJsonDocument(
        source=source,
        value=dict(value),
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def load_hashed_document(path: str | Path) -> HashedJsonDocument:
    """Load a regular, non-symlink JSON file while retaining its raw-byte hash."""

    source_path = Path(path)
    if source_path.is_symlink():
        raise ValueError(f"blind-review input must not be a symlink: {source_path}")
    if not source_path.is_file():
        raise ValueError(f"blind-review input is not a regular file: {source_path}")
    payload = source_path.read_bytes()
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"blind-review input is not valid UTF-8 JSON: {source_path}") from exc
    if not isinstance(value, Mapping):
        raise ValueError(f"blind-review input root must be an object: {source_path}")
    return HashedJsonDocument(
        source=str(source_path),
        value=dict(value),
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def _coerce_documents(
    values: Sequence[HashedJsonDocument | Mapping[str, Any]], *, kind: str
) -> tuple[HashedJsonDocument, ...]:
    documents: list[HashedJsonDocument] = []
    for index, value in enumerate(values):
        if isinstance(value, HashedJsonDocument):
            if _SHA256.fullmatch(value.sha256) is None:
                raise ValueError(f"{kind}[{index}] has an invalid document hash")
            documents.append(value)
        elif isinstance(value, Mapping):
            documents.append(hashed_document(value, source=f"<{kind}-{index}>"))
        else:
            raise TypeError(f"{kind}[{index}] must be a mapping or HashedJsonDocument")
    return tuple(sorted(documents, key=lambda item: (item.sha256, item.source)))


def _exact_keys(
    value: Mapping[str, Any],
    required: set[str],
    *,
    optional: set[str] = frozenset(),
    kind: str,
) -> None:
    missing = required - set(value)
    extra = set(value) - required - optional
    if missing or extra:
        raise _ContractError(
            f"{kind}_STRUCTURE_INVALID",
            f"keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}",
        )


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{path} must be a trimmed non-empty string")
    return value


def _sha(value: Any, path: str) -> str:
    text = _text(value, path)
    if _SHA256.fullmatch(text) is None:
        raise ValueError(f"{path} must be a lowercase SHA-256")
    return text


def _execution_id(value: Any, path: str) -> str:
    text = _text(value, path)
    if _EXECUTION_ID.fullmatch(text) is None:
        raise ValueError(f"{path} is not a valid execution identifier")
    return text


def _object(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object")
    return value


def _array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array")
    return value


def _slide_list(value: Any, path: str, *, allow_empty: bool = False) -> tuple[int, ...]:
    items = _array(value, path)
    if not items and allow_empty:
        return ()
    if (
        not items
        or any(isinstance(item, bool) or not isinstance(item, int) for item in items)
        or any(item < 1 or item > 15 for item in items)
        or len(items) != len(set(items))
        or items != sorted(items)
    ):
        raise ValueError(f"{path} must contain unique ascending slide numbers 1..15")
    return tuple(items)


def _decimal_score(value: Any, path: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{path} must be a number from 0 to 10")
    if not math.isfinite(float(value)):
        raise ValueError(f"{path} must be finite")
    score = Decimal(str(value))
    if score < 0 or score > 10:
        raise ValueError(f"{path} must be a number from 0 to 10")
    return score


def _parse_segment(document: HashedJsonDocument) -> _VisualSegment:
    raw = document.value
    try:
        _exact_keys(
            raw,
            _SEGMENT_REQUIRED_KEYS,
            optional={"failure_reason"},
            kind="SEGMENT",
        )
        if raw["schema_version"] != "1.0":
            raise ValueError("schema_version must equal 1.0")
        if raw["protocol_id"] != V61_BLIND_PROTOCOL_ID:
            raise ValueError("protocol_id mismatch")
        reviewer_id = _text(raw["reviewer_id"], "reviewer_id")
        if reviewer_id not in V61_REVIEWER_IDS:
            raise ValueError("reviewer_id is not frozen")
        segment_id = _text(raw["segment_id"], "segment_id")
        if segment_id not in V61_SEGMENT_SLIDES:
            raise ValueError("segment_id is not frozen")
        if raw["route_id"] != V61_AGNES_ROUTE_ID:
            raise ValueError("route_id must use the frozen direct Agnes route")
        if raw["model_id"] != V61_AGNES_MODEL_ID:
            raise ValueError("model_id must use frozen Agnes")
        invocation_id = _execution_id(raw["invocation_id"], "invocation_id")
        if raw["context_mode"] != "fresh-isolated":
            raise ValueError("context_mode must equal fresh-isolated")
        image_sha256s = _array(raw["image_sha256s"], "image_sha256s")
        if (
            not image_sha256s
            or len(image_sha256s) != len(set(image_sha256s))
            or any(
                not isinstance(item, str) or _SHA256.fullmatch(item) is None
                for item in image_sha256s
            )
        ):
            raise ValueError("image_sha256s must contain unique lowercase SHA-256 values")
        _sha(raw["request_sha256"], "request_sha256")
        _sha(raw["response_sha256"], "response_sha256")
        status = raw["status"]
        if status not in {"PASS", "NOT_RUN"}:
            raise ValueError("status must be PASS or NOT_RUN")
        if status == "NOT_RUN":
            _text(raw.get("failure_reason"), "failure_reason")
        inspected = _slide_list(
            raw["inspected_slides"],
            "inspected_slides",
            allow_empty=status == "NOT_RUN",
        )
        observations = _array(raw["observations"], "observations")
        observation_slides: list[int] = []
        for index, value in enumerate(observations):
            item = _object(value, f"observations[{index}]")
            _exact_keys(item, {"slide", "evidence"}, kind="SEGMENT")
            slide = item["slide"]
            if isinstance(slide, bool) or not isinstance(slide, int) or not 1 <= slide <= 15:
                raise ValueError(f"observations[{index}].slide must be 1..15")
            _text(item["evidence"], f"observations[{index}].evidence")
            observation_slides.append(slide)
        if status == "PASS":
            expected = V61_SEGMENT_SLIDES[segment_id]
            if inspected != expected:
                raise ValueError(f"inspected_slides must equal {list(expected)}")
            if tuple(observation_slides) != expected:
                raise ValueError(
                    "observations must cover each inspected slide exactly once in order"
                )
        packet_sha256 = _sha(raw["packet_sha256"], "packet_sha256")
        rubric_sha256 = _sha(raw["rubric_sha256"], "rubric_sha256")
    except _ContractError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise _ContractError("SEGMENT_STRUCTURE_INVALID", str(exc)) from exc
    return _VisualSegment(
        document=document,
        reviewer_id=reviewer_id,
        segment_id=segment_id,
        packet_sha256=packet_sha256,
        rubric_sha256=rubric_sha256,
        invocation_id=invocation_id,
        status=status,
    )


def _parse_review(document: HashedJsonDocument) -> _BlindReview:
    raw = document.value
    try:
        _exact_keys(
            raw,
            _REVIEW_REQUIRED_KEYS,
            optional={"failure_reason"},
            kind="REVIEW",
        )
        if raw["schema_version"] != "1.0":
            raise ValueError("schema_version must equal 1.0")
        if raw["protocol_id"] != V61_BLIND_PROTOCOL_ID:
            raise ValueError("protocol_id mismatch")
        reviewer_id = _text(raw["reviewer_id"], "reviewer_id")
        if reviewer_id not in V61_REVIEWER_IDS:
            raise ValueError("reviewer_id is not frozen")
        _text(raw["synthesis_model_id"], "synthesis_model_id")
        context_id = _execution_id(raw["synthesis_context_id"], "synthesis_context_id")
        if raw["context_mode"] != "fresh-isolated":
            raise ValueError("context_mode must equal fresh-isolated")
        _sha(raw["prompt_sha256"], "prompt_sha256")
        _sha(raw["response_sha256"], "response_sha256")
        status = raw["status"]
        if status not in {"PASS", "FAIL", "NOT_RUN"}:
            raise ValueError("status must be PASS, FAIL, or NOT_RUN")
        if status == "NOT_RUN":
            _text(raw.get("failure_reason"), "failure_reason")
        refs: list[_SegmentRef] = []
        for index, value in enumerate(_array(raw["segment_refs"], "segment_refs")):
            item = _object(value, f"segment_refs[{index}]")
            _exact_keys(
                item,
                {"segment_id", "document_sha256", "invocation_id"},
                kind="REVIEW",
            )
            segment_id = _text(item["segment_id"], f"segment_refs[{index}].segment_id")
            if segment_id not in V61_SEGMENT_SLIDES:
                raise ValueError(f"segment_refs[{index}].segment_id is not frozen")
            refs.append(
                _SegmentRef(
                    segment_id=segment_id,
                    document_sha256=_sha(
                        item["document_sha256"],
                        f"segment_refs[{index}].document_sha256",
                    ),
                    invocation_id=_execution_id(
                        item["invocation_id"],
                        f"segment_refs[{index}].invocation_id",
                    ),
                )
            )
        if len(refs) != 2 or {item.segment_id for item in refs} != set(V61_SEGMENT_SLIDES):
            raise ValueError("segment_refs must cover both frozen segments exactly once")
        inspected = _slide_list(raw["inspected_slides"], "inspected_slides")
        if inspected != tuple(range(1, 16)):
            raise ValueError("inspected_slides must equal 1..15")
        score_values = _object(raw["scores"], "scores")
        if set(score_values) != set(V61_REVIEW_DIMENSIONS):
            raise ValueError("scores must contain the exact frozen nine dimensions")
        scores = tuple(
            (dimension, _decimal_score(score_values[dimension], f"scores.{dimension}"))
            for dimension in V61_REVIEW_DIMENSIONS
        )
        reported_median = _decimal_score(raw["median_score"], "median_score")
        if not isinstance(raw["reference_parity"], bool):
            raise ValueError("reference_parity must be boolean")
        findings: list[_Finding] = []
        for index, value in enumerate(_array(raw["findings"], "findings")):
            item = _object(value, f"findings[{index}]")
            _exact_keys(
                item,
                {"severity", "dimension", "slides", "evidence"},
                kind="REVIEW",
            )
            severity = _text(item["severity"], f"findings[{index}].severity")
            if severity not in {"Blocker", "Important", "Nitpick"}:
                raise ValueError(f"findings[{index}].severity is not frozen")
            dimension = _text(item["dimension"], f"findings[{index}].dimension")
            if dimension not in V61_REVIEW_DIMENSIONS:
                raise ValueError(f"findings[{index}].dimension is not frozen")
            slides = _slide_list(item["slides"], f"findings[{index}].slides")
            evidence = _text(item["evidence"], f"findings[{index}].evidence")
            findings.append(_Finding(severity, dimension, slides, evidence))
        notes = raw["notes"]
        if not isinstance(notes, str) or notes != notes.strip() or not notes:
            raise ValueError("notes must be a trimmed non-empty string")
        packet_sha256 = _sha(raw["packet_sha256"], "packet_sha256")
        rubric_sha256 = _sha(raw["rubric_sha256"], "rubric_sha256")
    except _ContractError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise _ContractError("REVIEW_STRUCTURE_INVALID", str(exc)) from exc
    return _BlindReview(
        document=document,
        reviewer_id=reviewer_id,
        packet_sha256=packet_sha256,
        rubric_sha256=rubric_sha256,
        synthesis_context_id=context_id,
        status=status,
        segment_refs=tuple(refs),
        scores=scores,
        reported_median=reported_median,
        reference_parity=raw["reference_parity"],
        findings=tuple(findings),
    )


def _decimal_json(value: Decimal) -> int | float:
    integral = value.to_integral_value()
    return int(integral) if value == integral else float(value)


def _issue(
    issues: list[dict[str, Any]],
    code: str,
    disposition: str,
    detail: str,
    *,
    reviewer_id: str | None = None,
    segment_id: str | None = None,
) -> None:
    item: dict[str, Any] = {
        "code": code,
        "disposition": disposition,
        "detail": detail,
    }
    if reviewer_id in V61_REVIEWER_IDS:
        item["reviewer_id"] = reviewer_id
    if segment_id in V61_SEGMENT_SLIDES:
        item["segment_id"] = segment_id
    issues.append(item)


def aggregate_v61_blind_acceptance(
    segments: Sequence[HashedJsonDocument | Mapping[str, Any]],
    reviews: Sequence[HashedJsonDocument | Mapping[str, Any]],
    *,
    expected_packet_sha256: str,
    expected_rubric_sha256: str,
) -> dict[str, Any]:
    """Recompute the three-reviewer v6.1 blind acceptance gate.

    Integrity, provenance, coverage, uniqueness, and execution failures have
    precedence and yield ``NOT_RUN``.  Only a complete trustworthy matrix is
    eligible for the quality verdict: any median below 8, parity failure, or
    Blocker/Important finding yields ``FAIL``; otherwise the gate is ``PASS``.
    """

    if _SHA256.fullmatch(expected_packet_sha256) is None:
        raise ValueError("expected_packet_sha256 must be a lowercase SHA-256")
    if _SHA256.fullmatch(expected_rubric_sha256) is None:
        raise ValueError("expected_rubric_sha256 must be a lowercase SHA-256")
    segment_documents = _coerce_documents(segments, kind="segment")
    review_documents = _coerce_documents(reviews, kind="review")
    issues: list[dict[str, Any]] = []
    if len(segment_documents) != 6:
        _issue(
            issues,
            "SEGMENT_COUNT_MISMATCH",
            "NOT_RUN",
            f"expected 6 segment documents, observed {len(segment_documents)}",
        )
    if len(review_documents) != 3:
        _issue(
            issues,
            "REVIEW_COUNT_MISMATCH",
            "NOT_RUN",
            f"expected 3 review documents, observed {len(review_documents)}",
        )

    parsed_segments: list[_VisualSegment] = []
    for document in segment_documents:
        try:
            parsed_segments.append(_parse_segment(document))
        except _ContractError as exc:
            _issue(
                issues,
                exc.code,
                "NOT_RUN",
                f"document {document.sha256}: {exc.detail}",
                reviewer_id=exc.reviewer_id,
                segment_id=exc.segment_id,
            )
    parsed_reviews: list[_BlindReview] = []
    for document in review_documents:
        try:
            parsed_reviews.append(_parse_review(document))
        except _ContractError as exc:
            _issue(
                issues,
                exc.code,
                "NOT_RUN",
                f"document {document.sha256}: {exc.detail}",
                reviewer_id=exc.reviewer_id,
                segment_id=exc.segment_id,
            )

    segment_groups: dict[tuple[str, str], list[_VisualSegment]] = {}
    for segment in parsed_segments:
        segment_groups.setdefault((segment.reviewer_id, segment.segment_id), []).append(segment)
    review_groups: dict[str, list[_BlindReview]] = {}
    for review in parsed_reviews:
        review_groups.setdefault(review.reviewer_id, []).append(review)
    expected_segment_grid = {
        (reviewer_id, segment_id)
        for reviewer_id in V61_REVIEWER_IDS
        for segment_id in V61_SEGMENT_SLIDES
    }
    if set(segment_groups) != expected_segment_grid or any(
        len(group) != 1 for group in segment_groups.values()
    ):
        _issue(
            issues,
            "SEGMENT_GRID_MISMATCH",
            "NOT_RUN",
            "segments must cover each of 3 reviewers x 2 frozen segments exactly once",
        )
    if set(review_groups) != set(V61_REVIEWER_IDS) or any(
        len(group) != 1 for group in review_groups.values()
    ):
        _issue(
            issues,
            "REVIEWER_GRID_MISMATCH",
            "NOT_RUN",
            "reviews must cover ART, NARRATIVE, and PRODUCTION exactly once",
        )
    selected_segments = {
        key: sorted(group, key=lambda item: item.document.sha256)[0]
        for key, group in segment_groups.items()
    }
    selected_reviews = {
        key: sorted(group, key=lambda item: item.document.sha256)[0]
        for key, group in review_groups.items()
    }

    for segment in selected_segments.values():
        if segment.packet_sha256 != expected_packet_sha256:
            _issue(
                issues,
                "PACKET_SHA256_MISMATCH",
                "NOT_RUN",
                "segment packet hash differs from the frozen packet",
                reviewer_id=segment.reviewer_id,
                segment_id=segment.segment_id,
            )
        if segment.rubric_sha256 != expected_rubric_sha256:
            _issue(
                issues,
                "RUBRIC_SHA256_MISMATCH",
                "NOT_RUN",
                "segment rubric hash differs from the frozen rubric",
                reviewer_id=segment.reviewer_id,
                segment_id=segment.segment_id,
            )
        if segment.status == "NOT_RUN":
            _issue(
                issues,
                "SEGMENT_NOT_RUN",
                "NOT_RUN",
                "Agnes segment did not complete",
                reviewer_id=segment.reviewer_id,
                segment_id=segment.segment_id,
            )
    for review in selected_reviews.values():
        if review.packet_sha256 != expected_packet_sha256:
            _issue(
                issues,
                "PACKET_SHA256_MISMATCH",
                "NOT_RUN",
                "review packet hash differs from the frozen packet",
                reviewer_id=review.reviewer_id,
            )
        if review.rubric_sha256 != expected_rubric_sha256:
            _issue(
                issues,
                "RUBRIC_SHA256_MISMATCH",
                "NOT_RUN",
                "review rubric hash differs from the frozen rubric",
                reviewer_id=review.reviewer_id,
            )
        if review.status == "NOT_RUN":
            _issue(
                issues,
                "REVIEW_NOT_RUN",
                "NOT_RUN",
                "review synthesis did not complete",
                reviewer_id=review.reviewer_id,
            )
        if review.reported_median != review.recomputed_median:
            _issue(
                issues,
                "MEDIAN_SCORE_MISMATCH",
                "NOT_RUN",
                (
                    f"reported median {_decimal_json(review.reported_median)} differs "
                    f"from recomputed median {_decimal_json(review.recomputed_median)}"
                ),
                reviewer_id=review.reviewer_id,
            )

    context_ids = [review.synthesis_context_id for review in selected_reviews.values()]
    invocation_ids = [segment.invocation_id for segment in selected_segments.values()]
    if len(context_ids) != 3 or len(context_ids) != len(set(context_ids)):
        _issue(
            issues,
            "SYNTHESIS_CONTEXT_ID_DUPLICATE",
            "NOT_RUN",
            "three unique synthesis context IDs are required",
        )
    if len(invocation_ids) != 6 or len(invocation_ids) != len(set(invocation_ids)):
        _issue(
            issues,
            "AGNES_INVOCATION_ID_DUPLICATE",
            "NOT_RUN",
            "six unique Agnes invocation IDs are required",
        )
    collisions = sorted(set(context_ids) & set(invocation_ids))
    if collisions:
        _issue(
            issues,
            "CONTEXT_INVOCATION_ID_COLLISION",
            "NOT_RUN",
            f"synthesis and Agnes identifiers overlap: {collisions}",
        )

    for reviewer_id, review in selected_reviews.items():
        refs = {item.segment_id: item for item in review.segment_refs}
        for segment_id in V61_SEGMENT_SLIDES:
            segment = selected_segments.get((reviewer_id, segment_id))
            ref = refs.get(segment_id)
            if segment is None or ref is None:
                continue
            if ref.document_sha256 != segment.document.sha256:
                _issue(
                    issues,
                    "SEGMENT_DOCUMENT_SHA256_MISMATCH",
                    "NOT_RUN",
                    "review reference does not match the exact segment file bytes",
                    reviewer_id=reviewer_id,
                    segment_id=segment_id,
                )
            if ref.invocation_id != segment.invocation_id:
                _issue(
                    issues,
                    "SEGMENT_INVOCATION_ID_MISMATCH",
                    "NOT_RUN",
                    "review reference does not match the segment invocation",
                    reviewer_id=reviewer_id,
                    segment_id=segment_id,
                )

    integrity_failed = any(item["disposition"] == "NOT_RUN" for item in issues)
    if not integrity_failed:
        for reviewer_id in V61_REVIEWER_IDS:
            review = selected_reviews[reviewer_id]
            counts = review.finding_counts
            if review.recomputed_median < V61_REVIEW_MEDIAN_THRESHOLD:
                _issue(
                    issues,
                    "REVIEWER_MEDIAN_BELOW_THRESHOLD",
                    "FAIL",
                    (
                        f"median {_decimal_json(review.recomputed_median)} is below "
                        f"{_decimal_json(V61_REVIEW_MEDIAN_THRESHOLD)}"
                    ),
                    reviewer_id=reviewer_id,
                )
            if not review.reference_parity:
                _issue(
                    issues,
                    "REFERENCE_PARITY_FALSE",
                    "FAIL",
                    "reviewer did not find reference parity",
                    reviewer_id=reviewer_id,
                )
            if counts["Blocker"]:
                _issue(
                    issues,
                    "BLOCKER_FINDING_PRESENT",
                    "FAIL",
                    f"review contains {counts['Blocker']} Blocker finding(s)",
                    reviewer_id=reviewer_id,
                )
            if counts["Important"]:
                _issue(
                    issues,
                    "IMPORTANT_FINDING_PRESENT",
                    "FAIL",
                    f"review contains {counts['Important']} Important finding(s)",
                    reviewer_id=reviewer_id,
                )

    finding_counts = {severity: 0 for severity in ("Blocker", "Important", "Nitpick")}
    review_results: list[dict[str, Any]] = []
    for reviewer_id in V61_REVIEWER_IDS:
        review = selected_reviews.get(reviewer_id)
        if review is None:
            continue
        counts = review.finding_counts
        for severity, count in counts.items():
            finding_counts[severity] += count
        recomputed_status = "NOT_RUN" if review.status == "NOT_RUN" else review.recomputed_status
        review_results.append(
            {
                "reviewer_id": reviewer_id,
                "reported_status": review.status,
                "recomputed_status": recomputed_status,
                "recomputed_median": _decimal_json(review.recomputed_median),
                "reference_parity": review.reference_parity,
                "finding_counts": counts,
            }
        )

    issues = sorted(
        issues,
        key=lambda item: (
            item["disposition"],
            item["code"],
            item.get("reviewer_id", ""),
            item.get("segment_id", ""),
            item["detail"],
        ),
    )
    if any(item["disposition"] == "NOT_RUN" for item in issues):
        status = "NOT_RUN"
    elif any(item["disposition"] == "FAIL" for item in issues):
        status = "FAIL"
    else:
        status = "PASS"
    segment_hashes = sorted(document.sha256 for document in segment_documents)
    review_hashes = sorted(document.sha256 for document in review_documents)
    bundle_value = {
        "packet_sha256": expected_packet_sha256,
        "rubric_sha256": expected_rubric_sha256,
        "segments": segment_hashes,
        "reviews": review_hashes,
    }
    return {
        "schema_version": "1.0",
        "protocol_id": V61_BLIND_PROTOCOL_ID,
        "packet_sha256": expected_packet_sha256,
        "rubric_sha256": expected_rubric_sha256,
        "status": status,
        "reviewer_ids": [
            reviewer_id for reviewer_id in V61_REVIEWER_IDS if reviewer_id in selected_reviews
        ],
        "reviewer_count": len(selected_reviews),
        "segment_count": len(selected_segments),
        "synthesis_context_ids": sorted(set(context_ids)),
        "agnes_invocation_ids": sorted(set(invocation_ids)),
        "thresholds": {
            "reviewer_median": 8,
            "reference_parity": True,
            "allowed_blocker_count": 0,
            "allowed_important_count": 0,
        },
        "review_results": review_results,
        "finding_counts": finding_counts,
        "input_documents": {
            "segments": segment_hashes,
            "reviews": review_hashes,
        },
        "input_bundle_sha256": hashlib.sha256(
            canonical_document_bytes(bundle_value)
        ).hexdigest(),
        "issues": issues,
    }


__all__ = [
    "HashedJsonDocument",
    "V61_AGNES_MODEL_ID",
    "V61_AGNES_ROUTE_ID",
    "V61_BLIND_PROTOCOL_ID",
    "V61_REVIEWER_IDS",
    "V61_REVIEW_DIMENSIONS",
    "V61_REVIEW_MEDIAN_THRESHOLD",
    "V61_SEGMENT_SLIDES",
    "aggregate_v61_blind_acceptance",
    "canonical_document_bytes",
    "hashed_document",
    "load_hashed_document",
]
