from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.composition_plan import compile_composition_plan
from window_pptx.design_packs import select_design_pack
from window_pptx.quality_v3 import (
    QualityAxisScores,
    QualityFindingV3,
    assess_evidence_bundle_v3,
    build_quality_report_v3,
    execute_composition_repairs,
    finalize_quality_release_v3,
    inspect_composition_floor,
)
from window_pptx.generation import prepare_brief_generation
from window_pptx.layouts import SlideSize
from window_pptx.visual_plan import compile_visual_plan
from window_pptx.weak_model import NarrativePlan, NarrativeSlide


def _composition():
    narrative = NarrativePlan(
        schema_version="1.0",
        archetype_id="project-proposal",
        fact_store_digest="b" * 64,
        slides=(
            NarrativeSlide(
                id="cover",
                role="cover",
                title="A governed proposal",
                importance="critical",
                fact_refs=("fact-01",),
                semantic_kind="cards",
                structural=True,
            ),
        ),
        coverage={
            "required_fact_ids": ["fact-01"],
            "covered_fact_ids": ["fact-01"],
        },
        decisions=(),
    )
    pack = select_design_pack("project-proposal")
    visual, assets = compile_visual_plan(narrative, design_pack=pack)
    return compile_composition_plan(narrative, visual, assets, pack)


def test_quality_v3_requires_total_axis_and_art_review_gates() -> None:
    scores = QualityAxisScores(90, 88, 86, 84, 82, 80)
    not_reviewed = build_quality_report_v3(
        scores=scores,
        findings=(),
        engineering_passed=True,
        art_review_status="NOT_RUN",
    )
    assert not_reviewed.visual_passed is True
    assert not_reviewed.art_review_passed is False
    assert not_reviewed.release_passed is False

    released = build_quality_report_v3(
        scores=QualityAxisScores(90, 88, 86, 86, 86, 86),
        findings=(),
        engineering_passed=True,
        art_review_status="PASS",
    )
    assert released.total_score >= 84
    assert released.visual_passed is True
    assert released.art_review_passed is True
    assert released.release_passed is True

    low_axis = build_quality_report_v3(
        scores=QualityAxisScores(95, 95, 95, 95, 95, 74),
        findings=(),
        engineering_passed=True,
        art_review_status="PASS",
    )
    assert low_axis.total_score >= 84
    assert low_axis.visual_passed is False
    assert low_axis.release_passed is False


def test_quality_release_hash_binds_passed_direct_reviews(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.pptx"
    with zipfile.ZipFile(candidate, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("_rels/.rels", "<Relationships/>")
        archive.writestr("ppt/presentation.xml", "<p:presentation/>")
    candidate_sha256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
    portable = tmp_path / "portable-verification.json"
    portable.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "candidate_sha256": candidate_sha256,
                "verification": {
                    "quality": {
                        "passed": True,
                        "hard_gate_failures": [],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    automatic = tmp_path / "quality-report.v3.json"
    automatic.write_text(
        json.dumps(
            build_quality_report_v3(
                scores=QualityAxisScores(90, 89, 88, 87, 86, 85),
                findings=(),
                engineering_passed=True,
                art_review_status="NOT_RUN",
            ).to_dict()
        ),
        encoding="utf-8",
    )
    review = tmp_path / "agnes-review.json"
    visual_evidence = tmp_path / "contact-sheet.png"
    visual_evidence.write_bytes(b"\x89PNG\r\n\x1a\nvisual")
    review.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "candidate_sha256": candidate_sha256,
                "visual_evidence": {
                    "items": [
                        {
                            "path": str(visual_evidence),
                            "sha256": hashlib.sha256(
                                visual_evidence.read_bytes()
                            ).hexdigest(),
                        }
                    ],
                },
                "route_id": "agnes-direct/agnes-2.0-flash",
                "model": "agnes-2.0-flash",
                "request_sha256": "a" * 64,
                "response_sha256": "b" * 64,
                "payload": {
                    "schema_version": "1.0",
                    "scope": "deck",
                    "observations": [
                        {
                            "slide_id": "1",
                            "region": "whole-slide",
                            "evidence": "visible evidence",
                        }
                    ],
                    "findings": [],
                    "scores": {
                        "hierarchy_readability": 92,
                        "composition_space": 88,
                        "art_direction": 85,
                        "business_evidence": 90,
                        "deck_rhythm": 87,
                        "asset_polish": 86,
                    },
                    "verdict": "PASS",
                },
            }
        ),
        encoding="utf-8",
    )

    release = finalize_quality_release_v3(
        automatic_report_path=automatic,
        portable_verification_path=portable,
        direct_review_paths=(review,),
        candidate_path=candidate,
    )

    assert release["report"]["release_passed"] is True
    assert release["candidate"]["sha256"] == candidate_sha256
    assert release["portable_verification"]["sha256"] == hashlib.sha256(
        portable.read_bytes()
    ).hexdigest()
    failed = json.loads(review.read_text(encoding="utf-8"))
    failed["payload"]["scores"]["art_direction"] = 74
    review.write_text(json.dumps(failed), encoding="utf-8")
    with pytest.raises(ValueError, match="direct visual review"):
        finalize_quality_release_v3(
            automatic_report_path=automatic,
            portable_verification_path=portable,
            direct_review_paths=(review,),
            candidate_path=candidate,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "missing-portable",
        "invalid-ooxml",
        "automatic-invalid-json",
        "automatic-schema",
        "automatic-engineering",
        "automatic-visual",
        "automatic-axes",
        "portable-invalid-json",
        "portable-candidate-hash",
        "portable-quality-failed",
        "review-invalid-json",
        "review-schema",
        "review-candidate-hash",
        "review-evidence-missing",
        "review-evidence-hash",
        "review-route",
        "review-request-sha",
        "review-verdict",
        "review-important-finding",
        "review-axes",
        "review-low-axis",
        "combined-low-total",
    ),
)
def test_quality_release_failure_modes_fail_closed(
    tmp_path: Path,
    mutation: str,
) -> None:
    candidate = tmp_path / "candidate.pptx"
    with zipfile.ZipFile(candidate, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("_rels/.rels", "<Relationships/>")
        archive.writestr("ppt/presentation.xml", "<p:presentation/>")
    candidate_sha256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
    automatic = tmp_path / "quality-report.v3.json"
    automatic_payload = build_quality_report_v3(
        scores=QualityAxisScores(90, 89, 88, 87, 86, 85),
        findings=(),
        engineering_passed=True,
        art_review_status="NOT_RUN",
    ).to_dict()
    automatic.write_text(json.dumps(automatic_payload), encoding="utf-8")
    portable = tmp_path / "portable-verification.json"
    portable_payload = {
        "schema_version": "1.0",
        "candidate_sha256": candidate_sha256,
        "verification": {
            "quality": {
                "passed": True,
                "hard_gate_failures": [],
            }
        },
    }
    portable.write_text(json.dumps(portable_payload), encoding="utf-8")
    review = tmp_path / "agnes-review.json"
    visual_evidence = tmp_path / "contact-sheet.png"
    visual_evidence.write_bytes(b"\x89PNG\r\n\x1a\nvisual")
    review_payload = {
        "schema_version": "1.0",
        "candidate_sha256": candidate_sha256,
        "visual_evidence": {
            "items": [
                {
                    "path": str(visual_evidence),
                    "sha256": hashlib.sha256(
                        visual_evidence.read_bytes()
                    ).hexdigest(),
                }
            ],
        },
        "route_id": "agnes-direct/agnes-2.0-flash",
        "model": "agnes-2.0-flash",
        "request_sha256": "a" * 64,
        "response_sha256": "b" * 64,
        "payload": {
            "schema_version": "1.0",
            "scope": "deck",
            "observations": [],
            "findings": [],
            "scores": {
                "hierarchy_readability": 92,
                "composition_space": 88,
                "art_direction": 85,
                "business_evidence": 90,
                "deck_rhythm": 87,
                "asset_polish": 86,
            },
            "verdict": "PASS",
        },
    }
    review.write_text(json.dumps(review_payload), encoding="utf-8")

    if mutation == "missing-portable":
        portable.unlink()
    elif mutation == "invalid-ooxml":
        candidate.write_bytes(b"not-a-pptx")
    elif mutation == "automatic-invalid-json":
        automatic.write_text("{", encoding="utf-8")
    elif mutation == "automatic-schema":
        automatic_payload["schema_version"] = "2.0"
        automatic.write_text(json.dumps(automatic_payload), encoding="utf-8")
    elif mutation == "automatic-engineering":
        automatic_payload["engineering_passed"] = False
        automatic.write_text(json.dumps(automatic_payload), encoding="utf-8")
    elif mutation == "automatic-visual":
        automatic_payload["visual_passed"] = False
        automatic.write_text(json.dumps(automatic_payload), encoding="utf-8")
    elif mutation == "automatic-axes":
        automatic_payload["scores"].pop("asset_polish")
        automatic.write_text(json.dumps(automatic_payload), encoding="utf-8")
    elif mutation == "portable-invalid-json":
        portable.write_text("{", encoding="utf-8")
    elif mutation == "portable-candidate-hash":
        portable_payload["candidate_sha256"] = "f" * 64
        portable.write_text(json.dumps(portable_payload), encoding="utf-8")
    elif mutation == "portable-quality-failed":
        portable_payload["verification"]["quality"]["passed"] = False
        portable_payload["verification"]["quality"]["hard_gate_failures"] = [
            "OVERFLOW"
        ]
        portable.write_text(json.dumps(portable_payload), encoding="utf-8")
    elif mutation == "review-invalid-json":
        review.write_text("{", encoding="utf-8")
    elif mutation == "review-schema":
        review_payload["payload"]["schema_version"] = "2.0"
        review.write_text(json.dumps(review_payload), encoding="utf-8")
    elif mutation == "review-candidate-hash":
        review_payload["candidate_sha256"] = "f" * 64
        review.write_text(json.dumps(review_payload), encoding="utf-8")
    elif mutation == "review-evidence-missing":
        visual_evidence.unlink()
    elif mutation == "review-evidence-hash":
        review_payload["visual_evidence"]["items"][0]["sha256"] = "f" * 64
        review.write_text(json.dumps(review_payload), encoding="utf-8")
    elif mutation == "review-route":
        review_payload["route_id"] = "opencode/agnes"
        review.write_text(json.dumps(review_payload), encoding="utf-8")
    elif mutation == "review-request-sha":
        review_payload["request_sha256"] = "not-a-sha"
        review.write_text(json.dumps(review_payload), encoding="utf-8")
    elif mutation == "review-verdict":
        review_payload["payload"]["verdict"] = "FAIL"
        review.write_text(json.dumps(review_payload), encoding="utf-8")
    elif mutation == "review-important-finding":
        review_payload["payload"]["findings"] = [
            {
                "code": "VISIBLE_DEFECT",
                "severity": "important",
                "slide_id": "1",
                "region": "hero",
                "evidence": "A visible alignment defect remains.",
                "repair_code": "ALIGN_GRID",
            }
        ]
        review.write_text(json.dumps(review_payload), encoding="utf-8")
    elif mutation == "review-axes":
        review_payload["payload"]["scores"].pop("asset_polish")
        review.write_text(json.dumps(review_payload), encoding="utf-8")
    elif mutation == "review-low-axis":
        review_payload["payload"]["scores"]["asset_polish"] = 74
        review.write_text(json.dumps(review_payload), encoding="utf-8")
    elif mutation == "combined-low-total":
        review_payload["payload"]["scores"] = {
            axis: 75 for axis in QualityAxisScores.__annotations__
        }
        review.write_text(json.dumps(review_payload), encoding="utf-8")

    with pytest.raises(ValueError):
        finalize_quality_release_v3(
            automatic_report_path=automatic,
            portable_verification_path=portable,
            direct_review_paths=(review,),
            candidate_path=candidate,
        )


def test_frozen_r2_is_rejected_by_reference_grade_profile() -> None:
    evidence = (
        REPO_ROOT
        / ".planning"
        / "evidence"
        / "phase32-consulting-tracer-r2"
    )
    if not evidence.is_dir():
        pytest.skip(
            "local frozen Phase 32 evidence is intentionally gitignored"
        )
    report = assess_evidence_bundle_v3(evidence)
    codes = {finding.code for finding in report.findings}

    assert report.engineering_passed is True
    assert report.visual_passed is False
    assert report.release_passed is False
    assert "SEMANTIC_COMPONENT_UNMATERIALIZED" in codes
    assert "ASSET_INTENT_UNMATERIALIZED" in codes
    assert "ART_DIRECTION_NOT_MATERIALIZED" in codes

    schema = json.loads(
        (SKILL_ROOT / "schemas" / "quality-report.v3.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(report.to_dict(), schema)


def test_sparse_synthetic_baseline_fails_executable_composition_floor() -> None:
    facts = json.loads(
        (
            SKILL_ROOT / "evals" / "consulting-project-proposal-facts.json"
        ).read_text(encoding="utf-8")
    )
    brief = json.loads(
        (
            SKILL_ROOT / "evals" / "consulting-project-proposal-brief.json"
        ).read_text(encoding="utf-8")
    )
    generation = prepare_brief_generation(
        facts,
        brief,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        build_render=True,
    )

    assert generation.render_plan is not None
    sparse_plan = replace(
        generation.render_plan,
        slides=tuple(
            replace(
                slide,
                layout_id="executive-summary.top-band",
                objects=tuple(
                    item
                    for item in slide.objects
                    if item.component
                    in {
                        "title",
                        "body-text",
                        "footer",
                        "card",
                        "risk-panel",
                    }
                ),
            )
            for slide in generation.render_plan.slides
        ),
    )
    floor = inspect_composition_floor(
        SimpleNamespace(render_plan=sparse_plan)
    )
    codes = {finding.code for finding in floor.findings}
    assert floor.eligible_slide_ids
    assert floor.dominant_anchor_ratio < 0.35
    assert floor.asymmetric_ratio < 0.4
    assert "DOMINANT_ANCHOR_COVERAGE_LOW" in codes
    assert "ASYMMETRIC_COMPOSITION_COVERAGE_LOW" in codes
    assert floor.to_dict()["dominant_anchor"]["threshold"] == 0.35


def test_composition_floor_excludes_structural_full_bleed_heroes() -> None:
    facts = json.loads(
        (
            SKILL_ROOT / "evals" / "consulting-project-proposal-facts.json"
        ).read_text(encoding="utf-8")
    )
    brief = json.loads(
        (
            SKILL_ROOT / "evals" / "consulting-project-proposal-brief.json"
        ).read_text(encoding="utf-8")
    )
    generation = prepare_brief_generation(
        facts,
        brief,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        build_render=True,
    )

    assert generation.render_plan is not None
    cover = generation.render_plan.slides[0]
    hero = replace(
        cover.objects[0],
        component="image-frame",
        kind="image",
        x=0.5,
        y=0.4,
        width=12.333,
        height=6.7,
    )
    hero_cover = replace(cover, objects=(hero,))
    plan = replace(
        generation.render_plan,
        slides=(hero_cover, *generation.render_plan.slides[1:]),
    )

    floor = inspect_composition_floor(SimpleNamespace(render_plan=plan))

    assert hero_cover.source_id not in floor.eligible_slide_ids
    assert hero_cover.source_id not in floor.dominant_anchor_slide_ids


def test_composition_repair_accepts_only_monotonic_fact_safe_change() -> None:
    initial = _composition()
    initial_report = build_quality_report_v3(
        scores=QualityAxisScores(70, 65, 60, 80, 62, 68),
        findings=(
            QualityFindingV3(
                code="DECK_CHOREOGRAPHY_FLAT",
                severity="important",
                message="The deck rhythm is visibly flat.",
                slide_id="cover",
                repair_code="VARY_REGISTERED_COMPOSITION",
            ),
        ),
        engineering_passed=True,
        art_review_status="FAIL",
    )

    def evaluate(plan):
        if plan.slides[0].variant_id.endswith("-repaired"):
            return build_quality_report_v3(
                scores=QualityAxisScores(86, 85, 83, 85, 86, 83),
                findings=(),
                engineering_passed=True,
                art_review_status="PASS",
            )
        return initial_report

    def recompile(plan, action, _round):
        assert action == "VARY_REGISTERED_COMPOSITION"
        slide = replace(
            plan.slides[0],
            variant_id=f"{plan.slides[0].variant_id}-repaired",
        )
        return replace(plan, slides=(slide,))

    result = execute_composition_repairs(
        initial,
        evaluate=evaluate,
        recompile=recompile,
        max_rounds=2,
    )
    assert result.final_report.release_passed is True
    assert len(result.passes) == 1
    assert result.passes[0].accepted is True
    assert result.final_plan.fact_store_digest == initial.fact_store_digest
    assert result.final_plan.slides[0].fact_refs == initial.slides[0].fact_refs


def test_composition_repair_rolls_back_fact_drift() -> None:
    initial = _composition()
    report = build_quality_report_v3(
        scores=QualityAxisScores(70, 65, 60, 80, 62, 68),
        findings=(
            QualityFindingV3(
                code="DECK_CHOREOGRAPHY_FLAT",
                severity="important",
                message="The deck rhythm is visibly flat.",
                slide_id="cover",
                repair_code="VARY_REGISTERED_COMPOSITION",
            ),
        ),
        engineering_passed=True,
        art_review_status="FAIL",
    )

    def recompile(plan, _action, _round):
        slide = replace(plan.slides[0], fact_refs=("invented-fact",))
        return replace(plan, slides=(slide,))

    result = execute_composition_repairs(
        initial,
        evaluate=lambda _plan: report,
        recompile=recompile,
        max_rounds=2,
    )
    assert result.final_plan == initial
    assert result.passes[0].accepted is False
    assert result.passes[0].failure_code == "PROTECTED_CONTENT_CHANGED"
