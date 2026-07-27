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

from window_pptx.composition_plan import (
    CompositionPlanError,
    compile_composition_plan,
)
from window_pptx.design_packs import select_design_pack
from window_pptx.generation import prepare_brief_generation
from window_pptx.layouts import SlideSize, load_layout_registry
from window_pptx.visual_plan import compile_visual_plan
from window_pptx.weak_model import NarrativePlan, NarrativeSlide


def _proposal_narrative() -> NarrativePlan:
    roles = (
        "cover",
        "executive-summary",
        "approach",
        "timeline",
        "risks",
        "closing",
    )
    semantics = ("cards", "cards", "process", "timeline", "risk", "cards")
    return NarrativePlan(
        schema_version="1.0",
        archetype_id="project-proposal",
        fact_store_digest="a" * 64,
        slides=tuple(
            NarrativeSlide(
                id=f"proposal-{index:02d}",
                role=role,
                title=f"Proposal claim {index}",
                importance="critical" if role in {"cover", "closing"} else "normal",
                fact_refs=(f"fact-{index:02d}",),
                semantic_kind=semantics[index - 1],
                structural=role == "cover",
            )
            for index, role in enumerate(roles, start=1)
        ),
        coverage={
            "required_fact_ids": [f"fact-{index:02d}" for index in range(1, 7)],
            "covered_fact_ids": [f"fact-{index:02d}" for index in range(1, 7)],
        },
        decisions=(),
    )


def test_composition_plan_is_deterministic_registered_and_schema_valid() -> None:
    narrative = _proposal_narrative()
    pack = select_design_pack("project-proposal")
    visual, assets = compile_visual_plan(narrative, design_pack=pack)

    first = compile_composition_plan(narrative, visual, assets, pack)
    second = compile_composition_plan(narrative, visual, assets, pack)

    assert first == second
    assert first.fact_store_digest == narrative.fact_store_digest
    assert [slide.slide_id for slide in first.slides] == [
        slide.id for slide in narrative.slides
    ]
    assert [slide.fact_refs for slide in first.slides] == [
        slide.fact_refs for slide in narrative.slides
    ]
    assert all(slide.slot_bindings for slide in first.slides)
    assert all(slide.repair_variant_ids for slide in first.slides)

    registry = load_layout_registry()
    assert all(slide.layout_id in registry.variants for slide in first.slides)
    assert all(
        binding.component_id
        in {
            "title",
            "body-text",
            "card",
            "kpi",
            "image-frame",
            "icon",
            "chart",
            "table",
            "process-step",
            "timeline-node",
            "matrix-cell",
            "comparison-panel",
            "risk-panel",
            "recommendation-panel",
            "footer",
            "decoration",
            "accent",
            "statement",
            "quote",
            "team-member",
            "cta",
        }
        for slide in first.slides
        for binding in slide.slot_bindings
    )

    schema = json.loads(
        (SKILL_ROOT / "schemas" / "composition-plan.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(first.to_dict(), schema)


def test_composition_plan_rejects_slide_identity_drift() -> None:
    narrative = _proposal_narrative()
    pack = select_design_pack("project-proposal")
    visual, assets = compile_visual_plan(narrative, design_pack=pack)
    broken = type(visual)(
        design_pack_id=visual.design_pack_id,
        template_pack_id=visual.template_pack_id,
        theme_id=visual.theme_id,
        slides=visual.slides[:-1],
    )

    with pytest.raises(CompositionPlanError, match="slide ids"):
        compile_composition_plan(narrative, broken, assets, pack)


def test_generation_materializes_composition_plan_into_render_plan() -> None:
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
    composition_by_id = {
        slide.slide_id: slide for slide in generation.composition_plan.slides
    }
    compiled_by_id = {
        slide["id"]: slide for slide in generation.compiled_deck["slides"]
    }
    rendered_by_id = {
        slide.source_id: slide for slide in generation.render_plan.slides
    }
    assert set(composition_by_id) == set(compiled_by_id) == set(rendered_by_id)
    for slide_id, composition in composition_by_id.items():
        compiled = compiled_by_id[slide_id]
        rendered = rendered_by_id[slide_id]
        assert compiled["composition_id"] == composition.composition_id
        assert compiled["composition_variant_id"] == composition.variant_id
        assert compiled["composition_layout_id"] == composition.layout_id
        assert compiled["composition_density"] == composition.density
        assert compiled["composition_fact_refs"] == list(composition.fact_refs)
        assert rendered.composition_id == composition.composition_id
        assert rendered.variant_id == composition.variant_id
        assert rendered.requested_density == composition.density
        assert rendered.fact_refs == composition.fact_refs

    payload = generation.to_dict(include_render_plan=False)
    assert payload["composition_plan"]["slides"]
