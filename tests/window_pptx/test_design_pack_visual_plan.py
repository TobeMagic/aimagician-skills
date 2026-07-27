from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
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


def test_all_design_pack_manifests_validate_against_schema() -> None:
    schema = json.loads(
        (SKILL_ROOT / "schemas" / "design-pack.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    registry = json.loads(
        (SKILL_ROOT / "registries" / "design-packs.json").read_text(
            encoding="utf-8"
        )
    )
    for entry in registry["packs"]:
        payload = json.loads(
            (SKILL_ROOT / entry["manifest"]).read_text(encoding="utf-8")
        )
        jsonschema.validate(payload, schema)


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
