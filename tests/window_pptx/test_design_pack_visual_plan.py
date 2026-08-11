from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
EVAL_ROOT = REPO_ROOT / "quality" / "skill-evals" / "window-pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.design_packs import (
    DesignPackError,
    SCENARIO_DEFAULT_PACK,
    canonical_scenario_id,
    load_design_packs,
    select_design_pack,
)
from window_pptx.generation import prepare_brief_generation
from window_pptx.layouts import SlideSize
from window_pptx.visual_plan import compile_visual_plan
from window_pptx.composition_plan import compile_composition_plan
from window_pptx.composition_grammar import load_composition_grammars
from window_pptx.weak_model import NarrativePlan, NarrativeSlide

def _narrative(archetype_id: str = "business-report") -> NarrativePlan:
    roles = (
        "cover",
        "executive-summary",
        "performance",
        "competition",
        "timeline",
        "team",
        "risks",
        "recommendations",
        "closing",
    )
    return NarrativePlan(
        schema_version="1.0",
        archetype_id=archetype_id,
        fact_store_digest="0" * 64,
        slides=tuple(
            NarrativeSlide(
                id=f"slide-{index + 1:02d}",
                role=role,
                title=f"Claim {index + 1}",
                importance="critical" if role == "performance" else "normal",
                fact_refs=(f"fact-{index + 1:02d}",),
                semantic_kind="trend" if role == "performance" else "cards",
                structural=role == "cover",
            )
            for index, role in enumerate(roles)
        ),
        coverage={"required_fact_ids": [], "covered_fact_ids": []},
        decisions=(),
    )


def test_registry_covers_all_fifteen_business_scenarios() -> None:
    packs = load_design_packs()
    assert len(packs) == 4
    assert len(SCENARIO_DEFAULT_PACK) == 15
    for scenario, expected_pack in SCENARIO_DEFAULT_PACK.items():
        selected = select_design_pack(scenario, packs=packs)
        assert selected.id == expected_pack
        assert canonical_scenario_id(scenario) in selected.scenarios
    assert select_design_pack("strategic-plan", packs=packs).id == "consulting-executive"
    assert select_design_pack("training", packs=packs).id == "data-research-editorial"


def test_preferred_pack_must_explicitly_support_scenario() -> None:
    with pytest.raises(DesignPackError, match="does not support"):
        select_design_pack(
            "investor-pitch",
            preferred_pack_id="institutional-annual-editorial",
        )


def test_visual_and_asset_plan_are_deterministic_and_schema_valid() -> None:
    narrative = _narrative()
    first_visual, first_assets = compile_visual_plan(narrative)
    second_visual, second_assets = compile_visual_plan(narrative)
    assert first_visual == second_visual
    assert first_assets == second_assets
    assert first_visual.design_pack_id == "institutional-annual-editorial"
    assert first_visual.template_pack_id == "institutional-work-summary-v1"
    assert first_visual.slides[0].family == "cover"
    assert first_visual.slides[2].family in {"chart-story", "big-number"}
    assert first_visual.slides[2].emphasis == "hero"
    assert all(slide.decision_rules for slide in first_visual.slides)
    assert any(asset.editable for asset in first_assets.assets)

    visual_schema = json.loads(
        (SKILL_ROOT / "schemas" / "visual-plan.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    asset_schema = json.loads(
        (SKILL_ROOT / "schemas" / "asset-plan.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(first_visual.to_dict(), visual_schema)
    jsonschema.validate(first_assets.to_dict(), asset_schema)


def test_structural_section_and_closing_keep_image_led_art_direction() -> None:
    base = _narrative("project-proposal")
    narrative = NarrativePlan(
        schema_version=base.schema_version,
        archetype_id=base.archetype_id,
        fact_store_digest=base.fact_store_digest,
        slides=(
            NarrativeSlide(
                id="section-why",
                role="section",
                title="Why now",
                importance="high",
                fact_refs=("fact-section",),
                semantic_kind="cards",
                structural=True,
            ),
            NarrativeSlide(
                id="closing",
                role="closing",
                title="Decision",
                importance="critical",
                fact_refs=("fact-close",),
                semantic_kind="cards",
                structural=False,
            ),
        ),
        coverage={"required_fact_ids": [], "covered_fact_ids": []},
        decisions=(),
    )

    visual, assets = compile_visual_plan(narrative)

    assert visual.slides[0].family == "section"
    assert visual.slides[0].recipe_id is None
    assert visual.slides[0].asset_refs == ("asset-section-why",)
    assert visual.slides[1].family == "closing"
    assert visual.slides[1].asset_refs == ("asset-closing",)
    assert {asset.id: asset.kind for asset in assets.assets} == {
        "asset-section-why": "photo",
        "asset-closing": "photo",
    }


def test_data_research_pack_uses_capacity_safe_editorial_layouts() -> None:
    roles = (
        "data-scope",
        "key-metrics",
        "trends",
        "segments",
        "drivers",
        "recommendations",
    )
    narrative = NarrativePlan(
        schema_version="1.0",
        archetype_id="data-analysis",
        fact_store_digest="0" * 64,
        slides=tuple(
            NarrativeSlide(
                id=role,
                role=role,
                title=role,
                importance="high",
                fact_refs=(f"fact-{role}",),
                semantic_kind="trend" if role == "trends" else "metrics",
                structural=False,
            )
            for role in roles
        ),
        coverage={"required_fact_ids": [], "covered_fact_ids": []},
        decisions=(),
    )
    pack = select_design_pack("data-analysis")
    visual, assets = compile_visual_plan(narrative, design_pack=pack)

    composition = compile_composition_plan(narrative, visual, assets, pack)

    assert {slide.role: slide.layout_id for slide in composition.slides} == {
        "data-scope": "big-number.editorial-left",
        "key-metrics": "big-number.centered",
        "trends": "focal-statement.editorial-left",
        "segments": "data-chart.focus",
        "drivers": "big-number.split",
        "recommendations": "recommendation.focus",
    }


def test_all_design_pack_manifests_validate_against_schema() -> None:
    registry = json.loads(
        (SKILL_ROOT / "registries" / "design-packs.json").read_text(
            encoding="utf-8"
        )
    )
    for entry in registry["packs"]:
        payload = json.loads(
            (SKILL_ROOT / entry["manifest"]).read_text(encoding="utf-8")
        )
        schema_name = (
            "design-pack.v2.schema.json"
            if payload["schema_version"] == "2.0"
            else "design-pack.v1.schema.json"
        )
        schema = json.loads(
            (SKILL_ROOT / "schemas" / schema_name).read_text(encoding="utf-8")
        )
        jsonschema.validate(payload, schema)


def test_consulting_design_pack_v2_locks_knowledge_wayfinding_system() -> None:
    pack = select_design_pack("project-proposal")

    assert pack.schema_version == "2.0"
    assert pack.art_direction is not None
    assert pack.art_direction.id == "knowledge-wayfinding"
    assert pack.art_direction.palette_roles["canvas"] == "F4F0E7"
    assert pack.art_direction.palette_roles["ink"] == "12213A"
    assert pack.art_direction.grid_columns == 12
    assert pack.art_direction.safe_margin_in >= 0.55
    assert pack.art_direction.spacing_scale_pt == (4, 8, 12, 16, 24, 32, 48)
    assert pack.art_direction.motif_variants == (
        "portal",
        "path",
        "node",
        "frame",
    )
    assert pack.art_direction.energy_pattern == (
        "peak",
        "flow",
        "flow",
        "pause",
    )
    assert pack.art_direction.quality_thresholds["release"] == 84


def test_all_four_design_packs_are_distinct_v2_art_direction_systems() -> None:
    packs = load_design_packs()

    assert len(packs) == 4
    assert all(pack.schema_version == "2.0" for pack in packs.values())
    assert all(pack.art_direction is not None for pack in packs.values())
    assert len(
        {pack.art_direction.id for pack in packs.values() if pack.art_direction}
    ) == 4
    assert len(
        {
            tuple(pack.art_direction.palette_roles.values())
            for pack in packs.values()
            if pack.art_direction
        }
    ) == 4
    assert all(
        pack.art_direction.quality_thresholds["release"] >= 84
        and pack.art_direction.quality_thresholds["axis_floor"] >= 75
        for pack in packs.values()
        if pack.art_direction
    )


def test_brief_generation_consumes_design_visual_and_asset_plans() -> None:
    fact_store = {
        "schema_version": "1.0",
        "project": {
            "title": "Northstar Q2 Review",
            "objective": "Choose the Q3 priority.",
            "audience": "executive committee",
            "language": "en-US",
        },
        "sources": [
            {"id": "request", "kind": "request", "locator": "REQUEST.md"}
        ],
        "facts": [
            {
                "id": "revenue",
                "kind": "metric",
                "text": "Revenue reached 48.2 million dollars in Q2.",
                "language": "en-US",
                "source_id": "request",
                "locator": "line:1",
                "required": True,
                "value": 48.2,
                "unit": "million dollars",
            }
        ],
    }
    brief = {
        "schema_version": "1.0",
        "scenario_id": "business-report",
        "groups": [
            {
                "id": "evidence",
                "fact_refs": ["revenue"],
                "beat_hint": "performance",
                "semantic_hint": "metrics",
                "importance": "critical",
            }
        ],
        "preferences": {
            "tone": "professional",
            "density": "balanced",
            "audience_mode": "executive",
            "motion": "off",
        },
    }
    generation = prepare_brief_generation(
        fact_store,
        brief,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        build_render=True,
    )

    assert generation.design_pack.id == "institutional-annual-editorial"
    assert generation.visual_plan.design_pack_id == generation.design_pack.id
    assert generation.asset_plan.design_pack_id == generation.design_pack.id
    assert generation.render_plan is not None
    assert {
        slide["id"] for slide in generation.compiled_deck["slides"]
    } == {slide.slide_id for slide in generation.visual_plan.slides}
    assert all(
        "visual_plan_recommendation" in slide["decision_trace"]
        for slide in generation.compiled_deck["slides"]
    )
    payload = generation.to_dict(include_render_plan=False)
    assert payload["design_pack_id"] == generation.design_pack.id
    assert payload["visual_plan"]["slides"]
    assert "asset_plan" in payload


def test_project_proposal_uses_deterministic_consulting_composition_grammar() -> None:
    roles = (
        "cover",
        "executive-summary",
        "problem",
        "objectives",
        "approach",
        "workstreams",
        "timeline",
        "governance",
        "risks",
        "recommendations",
        "closing",
    )
    semantics = (
        "cards",
        "cards",
        "comparison",
        "metrics",
        "process",
        "matrix",
        "timeline",
        "hierarchy",
        "risk",
        "recommendation",
        "cards",
    )
    narrative = NarrativePlan(
        schema_version="1.0",
        archetype_id="project-proposal",
        fact_store_digest="0" * 64,
        slides=tuple(
            NarrativeSlide(
                id=f"proposal-{index:02d}",
                role=role,
                title=f"Proposal claim {index}",
                importance="normal",
                fact_refs=(f"fact-{index:02d}",),
                semantic_kind=semantics[index - 1],
                structural=role == "cover",
            )
            for index, role in enumerate(roles, start=1)
        ),
        coverage={"required_fact_ids": [], "covered_fact_ids": []},
        decisions=(),
    )

    grammar = load_composition_grammars()
    visual, _assets = compile_visual_plan(narrative)

    assert len(grammar) == 1
    assert visual.design_pack_id == "consulting-executive"
    assert [slide.recipe_id for slide in visual.slides] == [
        "proposal.cover",
        "proposal.executive-summary",
        "proposal.problem",
        "proposal.outcomes",
        "proposal.approach",
        "proposal.workstreams",
        "proposal.timeline",
        "proposal.governance",
        "proposal.risks",
        "proposal.next-step",
        "proposal.close",
    ]
    assert [slide.family for slide in visual.slides] == [
        "cover",
        "executive-summary",
        "comparison",
        "big-number",
        "process",
        "matrix",
        "timeline",
        "process",
        "risk-actions",
        "recommendation",
        "closing",
    ]
    assert visual.slides[5].density == "dense"
    assert "CAPACITY_MAX_ITEMS_8" in visual.slides[5].decision_rules


def test_project_proposal_metric_problem_and_bullet_solution_use_authored_recipes() -> None:
    narrative = NarrativePlan(
        schema_version="1.0",
        archetype_id="project-proposal",
        fact_store_digest="1" * 64,
        slides=(
            NarrativeSlide(
                id="problem",
                role="problem",
                title="Manual reassignment remains high",
                importance="high",
                fact_refs=("problem-fact",),
                semantic_kind="metrics",
                structural=False,
            ),
            NarrativeSlide(
                id="solution",
                role="solution",
                title="Pilot scope",
                importance="high",
                fact_refs=("solution-fact",),
                semantic_kind="cards",
                structural=False,
            ),
            NarrativeSlide(
                id="risk",
                role="risks",
                title="Fourteen categories lack ownership",
                importance="high",
                fact_refs=("risk-fact",),
                semantic_kind="metrics",
                structural=False,
            ),
        ),
        coverage={"required_fact_ids": [], "covered_fact_ids": []},
        decisions=(),
    )

    visual, _assets = compile_visual_plan(narrative)

    assert [slide.recipe_id for slide in visual.slides] == [
        "proposal.problem-metric",
        "proposal.solution",
        "proposal.risk-metric",
    ]
    assert [slide.family for slide in visual.slides] == [
        "big-number",
        "process",
        "big-number",
    ]


def test_consulting_tracer_structures_chinese_process_timeline_and_risk_evidence() -> None:
    facts = json.loads(
        (
            EVAL_ROOT / "consulting-project-proposal-facts.json"
        ).read_text(encoding="utf-8")
    )
    brief = json.loads(
        (
            EVAL_ROOT / "consulting-project-proposal-brief.json"
        ).read_text(encoding="utf-8")
    )

    generation = prepare_brief_generation(
        facts,
        brief,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        build_render=True,
    )
    deck_slides = {
        slide["id"]: slide for slide in generation.compilation.deck_plan["slides"]
    }

    assert list(deck_slides) == [
        "cover",
        "executive-summary",
        "section-why-now",
        "current-state",
        "transformation-bridge",
        "section-what-built",
        "solution",
        "scope",
        "section-how-delivery",
        "delivery-rail",
        "team",
        "risks",
        "next-steps",
        "closing",
    ]
    assert len(deck_slides["solution"]["blocks"][0]["items"]) == 4
    assert len(deck_slides["scope"]["blocks"][0]["items"]) == 4
    assert len(deck_slides["delivery-rail"]["blocks"][0]["items"]) == 5
    assert len(deck_slides["team"]["blocks"][0]["items"]) == 4
    assert deck_slides["risks"]["blocks"][0]["items"] == [
        {"label": "风险", "text": "业务采用不足"},
        {
            "label": "应对",
            "text": "选择高频场景、设置内容责任人并按周复盘使用数据",
        },
    ]
    assert deck_slides["current-state"]["blocks"][0]["items"] == [
        {
            "label": "现状断点",
            "text": (
                "当前知识分散在文档库、即时通讯和个人网盘，"
                "员工无法通过统一入口检索权威版本。"
            ),
        },
        {"label": "审批周期", "text": "关键知识审批平均需要 10 天。"},
    ]
    assert deck_slides["next-steps"]["blocks"][0]["items"] == [
        "01\n确定试点范围",
        "02\n指定业务负责人",
        "03\n确认启动日期",
    ]
    assert deck_slides["scope"]["title"] == "试点范围"
    assert deck_slides["team"]["title"] == "治理机制"
    assert deck_slides["risks"]["title"] == "风险与应对"
    bridge = deck_slides["transformation-bridge"]["blocks"][-1]["items"]
    assert bridge[-1] == {"label": "改善幅度", "value": -50, "unit": "%"}
    composition_bridge = next(
        slide
        for slide in generation.composition_plan.slides
        if slide.slide_id == "transformation-bridge"
    )
    assert composition_bridge.derived_fact_refs == (
        "derived-cycle-reduction-50pct",
    )
    assert all(
        binding.status in {"resolved", "generated", "native-materialized", "fallback"}
        for slide in generation.composition_plan.slides
        for binding in slide.asset_bindings
        if binding.required
    )
    next_step = next(
        slide
        for slide in generation.render_plan.slides
        if slide.source_id == "next-steps"
    )
    assert all(item.text != "Next Steps" for item in next_step.objects)
    assert next_step.layout_id == "recommendation.columns"
    current_state = next(
        slide
        for slide in generation.render_plan.slides
        if slide.source_id == "current-state"
    )
    assert current_state.layout_id == "comparison.split"
    assert [
        item.component
        for item in current_state.objects
        if item.component == "comparison-panel"
    ] == ["comparison-panel", "comparison-panel"]


def test_consulting_art_layout_falls_back_when_group_capacity_differs() -> None:
    facts = json.loads(
        (
            EVAL_ROOT / "consulting-project-proposal-facts.json"
        ).read_text(encoding="utf-8")
    )
    brief = json.loads(
        (
            EVAL_ROOT / "consulting-project-proposal-brief.json"
        ).read_text(encoding="utf-8")
    )
    brief["groups"] = [
        brief["groups"][0],
        {
            "id": "outcomes",
            "fact_refs": ["problem-cycle", "objective-cycle"],
            "beat_hint": "objectives",
            "semantic_hint": "metrics",
            "importance": "critical",
        },
        *brief["groups"][3:],
    ]

    generation = prepare_brief_generation(
        facts,
        brief,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        build_render=True,
    )

    compiled_outcomes = [
        slide
        for slide in generation.compiled_deck["slides"]
        if slide["id"].startswith("outcomes")
    ]
    rendered_outcomes = [
        slide
        for slide in generation.render_plan.slides
        if slide.source_id.startswith("outcomes")
    ]
    assert compiled_outcomes
    assert any(
        slide["composition_layout_id"] == "big-number.editorial-three"
        for slide in compiled_outcomes
    )
    editorial_three = [
        slide
        for slide in compiled_outcomes
        if slide["composition_layout_id"] == "big-number.editorial-three"
    ]
    assert editorial_three
    assert all(
        slide["composition_layout_enforced"] is False
        for slide in editorial_three
    )
    assert all(
        slide.layout_id != "big-number.editorial-three"
        for slide in rendered_outcomes
    )
    assert any(
        slide["composition_layout_id"] == "big-number.metric-left"
        and slide["composition_layout_enforced"] is True
        for slide in compiled_outcomes
    )
