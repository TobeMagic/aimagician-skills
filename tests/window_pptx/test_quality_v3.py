from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import jsonschema

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
)
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


def test_frozen_r2_is_rejected_by_reference_grade_profile() -> None:
    evidence = (
        REPO_ROOT
        / ".planning"
        / "evidence"
        / "phase32-consulting-tracer-r2"
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
