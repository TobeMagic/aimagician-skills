from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = SKILL_ROOT / "schemas"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import aggregate_window_pptx_v61_blind_reviews as aggregate_cli  # noqa: E402
from window_pptx.v61_blind_acceptance import (  # noqa: E402
    V61_REVIEWER_IDS,
    V61_REVIEW_DIMENSIONS,
    V61_SEGMENT_SLIDES,
    aggregate_v61_blind_acceptance,
    canonical_document_bytes,
    hashed_document,
)


PACKET_SHA256 = "a" * 64
RUBRIC_SHA256 = "b" * 64


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _segments():
    result = []
    for reviewer_id in V61_REVIEWER_IDS:
        for segment_id, slides in V61_SEGMENT_SLIDES.items():
            marker = f"{reviewer_id.lower()}-{segment_id.lower()}"
            value = {
                "schema_version": "1.0",
                "protocol_id": "window-pptx-v61-blind-v1",
                "reviewer_id": reviewer_id,
                "segment_id": segment_id,
                "packet_sha256": PACKET_SHA256,
                "rubric_sha256": RUBRIC_SHA256,
                "route_id": "agnes-direct/agnes-2.0-flash",
                "model_id": "agnes-2.0-flash",
                "invocation_id": f"agnes-invocation-{marker}",
                "context_mode": "fresh-isolated",
                "image_sha256s": [_digest(f"image-{marker}-{index}") for index in range(4)],
                "request_sha256": _digest(f"request-{marker}"),
                "response_sha256": _digest(f"response-{marker}"),
                "status": "PASS",
                "inspected_slides": list(slides),
                "observations": [
                    {"slide": slide, "evidence": f"Visible evidence on Slide {slide}."}
                    for slide in slides
                ],
            }
            result.append(hashed_document(value, source=f"{marker}.json"))
    return result


def _quality_status(
    scores: dict[str, float], reference_parity: bool, findings: list[dict]
) -> str:
    median = sorted(scores.values())[len(scores) // 2]
    has_material = any(
        finding["severity"] in {"Blocker", "Important"} for finding in findings
    )
    return "PASS" if median >= 8 and reference_parity and not has_material else "FAIL"


def _reviews(
    segments,
    *,
    reviewer_scores: dict[str, float] | None = None,
    reviewer_parity: dict[str, bool] | None = None,
    reviewer_findings: dict[str, list[dict]] | None = None,
):
    reviewer_scores = reviewer_scores or {}
    reviewer_parity = reviewer_parity or {}
    reviewer_findings = reviewer_findings or {}
    lookup = {
        (document.value["reviewer_id"], document.value["segment_id"]): document
        for document in segments
    }
    result = []
    for reviewer_id in V61_REVIEWER_IDS:
        score = reviewer_scores.get(reviewer_id, 8.5)
        scores = {dimension: score for dimension in V61_REVIEW_DIMENSIONS}
        findings = copy.deepcopy(reviewer_findings.get(reviewer_id, []))
        parity = reviewer_parity.get(reviewer_id, True)
        refs = []
        for segment_id in V61_SEGMENT_SLIDES:
            segment = lookup[(reviewer_id, segment_id)]
            refs.append(
                {
                    "segment_id": segment_id,
                    "document_sha256": segment.sha256,
                    "invocation_id": segment.value["invocation_id"],
                }
            )
        value = {
            "schema_version": "1.0",
            "protocol_id": "window-pptx-v61-blind-v1",
            "reviewer_id": reviewer_id,
            "packet_sha256": PACKET_SHA256,
            "rubric_sha256": RUBRIC_SHA256,
            "synthesis_model_id": "gpt-5.6-terra",
            "synthesis_context_id": f"synthesis-context-{reviewer_id.lower()}",
            "context_mode": "fresh-isolated",
            "prompt_sha256": _digest(f"prompt-{reviewer_id}"),
            "response_sha256": _digest(f"synthesis-{reviewer_id}"),
            "segment_refs": refs,
            "inspected_slides": list(range(1, 16)),
            "scores": scores,
            "median_score": score,
            "reference_parity": parity,
            "findings": findings,
            "status": _quality_status(scores, parity, findings),
            "notes": "Fresh isolated synthesis of both frozen visual segments.",
        }
        result.append(hashed_document(value, source=f"review-{reviewer_id}.json"))
    return result


def _aggregate(segments, reviews):
    return aggregate_v61_blind_acceptance(
        segments,
        reviews,
        expected_packet_sha256=PACKET_SHA256,
        expected_rubric_sha256=RUBRIC_SHA256,
    )


def _validate_aggregate_schema(value: dict) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SCHEMA_ROOT / "v61-blind-aggregate.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.Draft202012Validator(schema).validate(value)


def _replace_document(documents, predicate, mutate):
    result = []
    for document in documents:
        if predicate(document.value):
            value = copy.deepcopy(document.value)
            mutate(value)
            result.append(hashed_document(value, source=document.source))
        else:
            result.append(document)
    return result


def test_v61_blind_schemas_and_exact_matrix_pass() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    segments = _segments()
    reviews = _reviews(segments)
    aggregate = _aggregate(segments, reviews)

    for name in (
        "v61-visual-segment.v1.schema.json",
        "v61-blind-review.v1.schema.json",
        "v61-blind-aggregate.v1.schema.json",
    ):
        schema = json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
    segment_schema = json.loads(
        (SCHEMA_ROOT / "v61-visual-segment.v1.schema.json").read_text(encoding="utf-8")
    )
    review_schema = json.loads(
        (SCHEMA_ROOT / "v61-blind-review.v1.schema.json").read_text(encoding="utf-8")
    )
    aggregate_schema = json.loads(
        (SCHEMA_ROOT / "v61-blind-aggregate.v1.schema.json").read_text(encoding="utf-8")
    )
    for document in segments:
        jsonschema.Draft202012Validator(segment_schema).validate(document.value)
    for document in reviews:
        jsonschema.Draft202012Validator(review_schema).validate(document.value)
    jsonschema.Draft202012Validator(aggregate_schema).validate(aggregate)

    assert aggregate["status"] == "PASS"
    assert aggregate["reviewer_ids"] == list(V61_REVIEWER_IDS)
    assert aggregate["reviewer_count"] == 3
    assert aggregate["segment_count"] == 6
    assert len(aggregate["synthesis_context_ids"]) == 3
    assert len(aggregate["agnes_invocation_ids"]) == 6
    assert aggregate["issues"] == []


def test_v61_blind_aggregate_is_input_order_independent() -> None:
    segments = _segments()
    reviews = _reviews(segments)

    assert _aggregate(segments, reviews) == _aggregate(
        list(reversed(segments)), list(reversed(reviews))
    )


@pytest.mark.parametrize(
    ("scores", "parity", "findings", "code"),
    [
        ({"ART": 7.9}, {}, {}, "REVIEWER_MEDIAN_BELOW_THRESHOLD"),
        ({}, {"ART": False}, {}, "REFERENCE_PARITY_FALSE"),
        (
            {},
            {},
            {
                "ART": [
                    {
                        "severity": "Blocker",
                        "dimension": "art_direction",
                        "slides": [8],
                        "evidence": "Slide 8 has a release-blocking visual defect.",
                    }
                ]
            },
            "BLOCKER_FINDING_PRESENT",
        ),
        (
            {},
            {},
            {
                "PRODUCTION": [
                    {
                        "severity": "Important",
                        "dimension": "typography_readability",
                        "slides": [12],
                        "evidence": "Slide 12 has an important overlap.",
                    }
                ]
            },
            "IMPORTANT_FINDING_PRESENT",
        ),
    ],
)
def test_v61_blind_quality_defect_is_fail_not_not_run(
    scores, parity, findings, code
) -> None:
    segments = _segments()
    reviews = _reviews(
        segments,
        reviewer_scores=scores,
        reviewer_parity=parity,
        reviewer_findings=findings,
    )

    result = _aggregate(segments, reviews)

    _validate_aggregate_schema(result)
    assert result["status"] == "FAIL"
    assert code in {issue["code"] for issue in result["issues"]}
    assert {issue["disposition"] for issue in result["issues"]} == {"FAIL"}


def test_v61_blind_nitpick_does_not_fail_release() -> None:
    segments = _segments()
    reviews = _reviews(
        segments,
        reviewer_findings={
            "ART": [
                {
                    "severity": "Nitpick",
                    "dimension": "layout_craft",
                    "slides": [4],
                    "evidence": "Slide 4 could use a slightly tighter optical alignment.",
                }
            ]
        },
    )

    result = _aggregate(segments, reviews)

    assert result["status"] == "PASS"
    assert result["finding_counts"] == {"Blocker": 0, "Important": 0, "Nitpick": 1}


def test_v61_blind_recomputes_quality_instead_of_trusting_reported_pass() -> None:
    segments = _segments()
    reviews = _reviews(segments, reviewer_scores={"ART": 7.5})
    reviews = _replace_document(
        reviews,
        lambda value: value["reviewer_id"] == "ART",
        lambda value: value.update({"status": "PASS"}),
    )

    result = _aggregate(segments, reviews)

    assert result["status"] == "FAIL"
    assert result["review_results"][0]["reported_status"] == "PASS"
    assert result["review_results"][0]["recomputed_status"] == "FAIL"


def test_v61_blind_missing_input_is_not_run() -> None:
    segments = _segments()
    reviews = _reviews(segments)

    result = _aggregate(segments, reviews[:-1])

    _validate_aggregate_schema(result)
    assert result["status"] == "NOT_RUN"
    assert {issue["code"] for issue in result["issues"]} >= {
        "REVIEW_COUNT_MISMATCH",
        "REVIEWER_GRID_MISMATCH",
    }


def test_v61_blind_hash_or_median_mismatch_is_not_run() -> None:
    segments = _segments()
    reviews = _reviews(segments)
    reviews = _replace_document(
        reviews,
        lambda value: value["reviewer_id"] == "ART",
        lambda value: value["segment_refs"][0].update({"document_sha256": "c" * 64}),
    )
    hash_result = _aggregate(segments, reviews)
    assert hash_result["status"] == "NOT_RUN"
    assert "SEGMENT_DOCUMENT_SHA256_MISMATCH" in {
        issue["code"] for issue in hash_result["issues"]
    }

    reviews = _reviews(segments)
    reviews = _replace_document(
        reviews,
        lambda value: value["reviewer_id"] == "ART",
        lambda value: value.update({"median_score": 9}),
    )
    median_result = _aggregate(segments, reviews)
    assert median_result["status"] == "NOT_RUN"
    assert "MEDIAN_SCORE_MISMATCH" in {
        issue["code"] for issue in median_result["issues"]
    }


def test_v61_blind_packet_and_rubric_are_frozen_across_every_input() -> None:
    segments = _segments()
    segments = _replace_document(
        segments,
        lambda value: value["reviewer_id"] == "ART"
        and value["segment_id"] == "SLIDES_01_08",
        lambda value: value.update({"packet_sha256": "d" * 64}),
    )
    reviews = _reviews(segments)
    reviews = _replace_document(
        reviews,
        lambda value: value["reviewer_id"] == "PRODUCTION",
        lambda value: value.update({"rubric_sha256": "e" * 64}),
    )

    result = _aggregate(segments, reviews)

    assert result["status"] == "NOT_RUN"
    assert {issue["code"] for issue in result["issues"]} >= {
        "PACKET_SHA256_MISMATCH",
        "RUBRIC_SHA256_MISMATCH",
    }


def test_v61_blind_duplicate_or_cross_class_execution_ids_are_not_run() -> None:
    segments = _segments()
    first_invocation = segments[0].value["invocation_id"]
    segments = _replace_document(
        segments,
        lambda value: value["reviewer_id"] == "PRODUCTION"
        and value["segment_id"] == "SLIDES_09_15",
        lambda value: value.update({"invocation_id": first_invocation}),
    )
    reviews = _reviews(segments)
    duplicate_result = _aggregate(segments, reviews)
    assert duplicate_result["status"] == "NOT_RUN"
    assert "AGNES_INVOCATION_ID_DUPLICATE" in {
        issue["code"] for issue in duplicate_result["issues"]
    }

    segments = _segments()
    reviews = _reviews(segments)
    reviews = _replace_document(
        reviews,
        lambda value: value["reviewer_id"] == "ART",
        lambda value: value.update({"synthesis_context_id": first_invocation}),
    )
    collision_result = _aggregate(segments, reviews)
    assert collision_result["status"] == "NOT_RUN"
    assert "CONTEXT_INVOCATION_ID_COLLISION" in {
        issue["code"] for issue in collision_result["issues"]
    }


def test_v61_blind_duplicate_synthesis_context_or_not_run_input_is_not_run() -> None:
    segments = _segments()
    reviews = _reviews(segments)
    shared_context = reviews[0].value["synthesis_context_id"]
    reviews = _replace_document(
        reviews,
        lambda value: value["reviewer_id"] == "NARRATIVE",
        lambda value: value.update({"synthesis_context_id": shared_context}),
    )
    duplicate_result = _aggregate(segments, reviews)
    assert duplicate_result["status"] == "NOT_RUN"
    assert "SYNTHESIS_CONTEXT_ID_DUPLICATE" in {
        issue["code"] for issue in duplicate_result["issues"]
    }

    segments = _segments()
    segments = _replace_document(
        segments,
        lambda value: value["reviewer_id"] == "ART"
        and value["segment_id"] == "SLIDES_01_08",
        lambda value: value.update(
            {"status": "NOT_RUN", "failure_reason": "Agnes image load failed."}
        ),
    )
    reviews = _reviews(segments)
    not_run_result = _aggregate(segments, reviews)
    assert not_run_result["status"] == "NOT_RUN"
    assert "SEGMENT_NOT_RUN" in {issue["code"] for issue in not_run_result["issues"]}


def test_v61_blind_exact_slide_coverage_is_required() -> None:
    segments = _segments()
    reviews = _reviews(segments)
    reviews = _replace_document(
        reviews,
        lambda value: value["reviewer_id"] == "ART",
        lambda value: value["inspected_slides"].pop(),
    )

    result = _aggregate(segments, reviews)

    assert result["status"] == "NOT_RUN"
    assert "REVIEW_STRUCTURE_INVALID" in {issue["code"] for issue in result["issues"]}


def test_v61_blind_cli_hashes_exact_file_bytes_and_writes_gate(
    tmp_path: Path,
) -> None:
    segment_documents = _segments()
    review_documents = _reviews(segment_documents)
    segment_paths = []
    review_paths = []
    for index, document in enumerate(segment_documents):
        path = tmp_path / f"segment-{index}.json"
        path.write_bytes(canonical_document_bytes(document.value))
        segment_paths.append(path)
    for index, document in enumerate(review_documents):
        path = tmp_path / f"review-{index}.json"
        path.write_bytes(canonical_document_bytes(document.value))
        review_paths.append(path)
    output = tmp_path / "aggregate.json"
    argv = []
    for path in segment_paths:
        argv.extend(("--segment", str(path)))
    for path in review_paths:
        argv.extend(("--review", str(path)))
    argv.extend(
        (
            "--packet-sha256",
            PACKET_SHA256,
            "--rubric-sha256",
            RUBRIC_SHA256,
            "--output",
            str(output),
        )
    )

    assert aggregate_cli.main(argv) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "PASS"
