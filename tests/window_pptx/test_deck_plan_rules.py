from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from window_pptx.capacity import split_slide
from window_pptx.deck_plan import (
    ContentBlock,
    DeckPlan,
    DeckPlanValidationError,
    ProjectIntent,
    SlideIntent,
    compile_deck_plan,
    load_deck_plan,
    validate_deck_plan,
)
from window_pptx.registry import load_archetypes, resolve_archetype
from window_pptx.rules import rank_page_families


EXPECTED_ARCHETYPES = {
    "annual-review",
    "brand-introduction",
    "business-report",
    "data-analysis",
    "ecommerce-marketing",
    "investor-pitch",
    "market-analysis",
    "operations-review",
    "product-launch",
    "project-kickoff",
    "project-proposal",
    "research-report",
    "sales-proposal",
    "strategic-plan",
    "training",
}


def minimal_plan(*, kind: str = "metrics", items: list[object] | None = None) -> dict:
    return {
        "schema_version": "1.0",
        "project": {
            "title": "Q3 经营复盘",
            "scenario": "business-report",
            "audience": "management",
            "objective": "align decisions",
        },
        "slides": [
            {
                "id": "summary",
                "role": "executive-summary",
                "title": "核心结论",
                "importance": "high",
                "blocks": [
                    {
                        "id": "summary-kpis",
                        "kind": kind,
                        "items": items
                        if items is not None
                        else [
                            {"label": "Revenue", "value": 42, "unit": "M"},
                            {"label": "Growth", "value": 18, "unit": "%"},
                        ],
                    }
                ],
            }
        ],
    }


def test_schema_artifact_is_versioned_and_strict() -> None:
    schema = json.loads(
        (SKILL_ROOT / "schemas" / "deck-plan.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["$id"].endswith("deck-plan.v1.schema.json")
    assert schema["properties"]["schema_version"]["const"] == "1.0"
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["slide"]["additionalProperties"] is False
    assert schema["$defs"]["contentBlock"]["additionalProperties"] is False
    assert schema["$defs"]["dataItem"]["additionalProperties"] is False
    assert schema["$defs"]["dataItem"]["minProperties"] == 1
    assert schema["$defs"]["contentBlock"]["anyOf"]
    assert schema["$defs"]["contentBlock"]["properties"]["items"]["minItems"] == 1


def test_schema_and_manual_validator_agree_on_whitespace_and_data_item_types() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SKILL_ROOT / "schemas" / "deck-plan.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = jsonschema.Draft202012Validator(schema)
    whitespace = minimal_plan()
    whitespace["slides"][0]["title"] = "   "
    wrong_label = minimal_plan(items=[{"label": 42, "value": 7}])
    long_label = minimal_plan(items=[{"label": "x" * 301, "value": 7}])
    short_language = minimal_plan()
    short_language["project"]["language"] = "x"
    padded_language = minimal_plan()
    padded_language["project"]["language"] = " x "
    padded_id = minimal_plan()
    padded_id["slides"][0]["id"] = " summary "
    padded_max_title = minimal_plan()
    padded_max_title["slides"][0]["title"] = " " + ("x" * 200) + " "
    explicit_empty_items = minimal_plan(items=[])
    explicit_empty_items["slides"][0]["blocks"][0]["title"] = "Title only"

    for payload in (
        whitespace,
        wrong_label,
        long_label,
        short_language,
        padded_language,
        padded_id,
        padded_max_title,
        explicit_empty_items,
    ):
        assert list(validator.iter_errors(payload))
        with pytest.raises(DeckPlanValidationError):
            validate_deck_plan(payload)


def test_minimal_semantic_plan_validates_without_design_geometry() -> None:
    plan = validate_deck_plan(minimal_plan())

    assert plan.schema_version == "1.0"
    assert plan.project.scenario == "business-report"
    assert plan.slides[0].blocks[0].kind == "metrics"
    assert plan.slides[0].blocks[0].items[0]["label"] == "Revenue"


def test_load_deck_plan_reads_utf8_and_compile_accepts_validated_model(
    tmp_path: Path,
) -> None:
    path = tmp_path / "deck-plan.json"
    path.write_text(json.dumps(minimal_plan(), ensure_ascii=False), encoding="utf-8")

    plan = load_deck_plan(path)
    compiled = compile_deck_plan(plan)

    assert plan.project.title == "Q3 经营复盘"
    assert compiled["archetype_id"] == "business-report"


def test_load_deck_plan_wraps_invalid_json_as_validation_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(DeckPlanValidationError, match="cannot load"):
        load_deck_plan(path)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("x",), 1),
        (("width",), 4),
        (("font",), "Arial"),
        (("color",), "#ff0000"),
        (("layout_id",), "invented-layout"),
        (("script",), "run arbitrary code"),
        (("com_call",), "PowerPoint.Application"),
        (("vba",), "Sub AutoOpen()"),
    ],
)
def test_raw_design_and_code_fields_are_rejected(
    path: tuple[str, ...], value: object
) -> None:
    payload = minimal_plan()
    payload["slides"][0]["blocks"][0][path[0]] = value

    with pytest.raises(DeckPlanValidationError, match=path[0]):
        validate_deck_plan(payload)


def test_unknown_top_level_field_is_rejected() -> None:
    payload = minimal_plan()
    payload["surprise"] = "uncontrolled"

    with pytest.raises(DeckPlanValidationError, match="surprise"):
        validate_deck_plan(payload)


def test_unregistered_data_item_field_is_rejected() -> None:
    payload = minimal_plan(items=[{"label": "Revenue", "value": 42, "mystery": 7}])

    with pytest.raises(DeckPlanValidationError, match="mystery"):
        validate_deck_plan(payload)


def test_empty_content_block_is_rejected_instead_of_padding_a_slide() -> None:
    payload = minimal_plan(kind="generic", items=[])

    with pytest.raises(DeckPlanValidationError, match="items.*non-empty"):
        validate_deck_plan(payload)


def test_non_finite_numbers_are_rejected_for_stable_json() -> None:
    payload = minimal_plan(items=[{"label": "bad", "value": math.nan}])

    with pytest.raises(DeckPlanValidationError, match="finite"):
        validate_deck_plan(payload)


def test_oversized_atomic_item_is_rejected_by_both_validation_paths() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SKILL_ROOT / "schemas" / "deck-plan.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    payload = minimal_plan(kind="bullets", items=["x" * 10_000])

    assert list(jsonschema.Draft202012Validator(schema).iter_errors(payload))
    with pytest.raises(DeckPlanValidationError, match="600"):
        validate_deck_plan(payload)


def test_data_item_aggregate_budget_is_enforced_by_both_validation_paths() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SKILL_ROOT / "schemas" / "deck-plan.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    payload = minimal_plan(
        items=[
            {
                "label": "a" * 160,
                "title": "b" * 160,
                "name": "c" * 160,
                "description": "d" * 160,
                "category": "e" * 160,
                "series": "f" * 160,
            }
        ]
    )

    assert list(jsonschema.Draft202012Validator(schema).iter_errors(payload))
    with pytest.raises(DeckPlanValidationError, match="at most 5"):
        validate_deck_plan(payload)


def test_publicly_constructed_deck_plan_is_revalidated_before_compile() -> None:
    plan = DeckPlan(
        schema_version="1.0",
        project=ProjectIntent(title="Bad", scenario="business-report"),
        slides=(
            SlideIntent(
                id="slide",
                role="insights",
                title="Bad",
                importance="normal",
                blocks=(ContentBlock(id="block", kind="not-registered", items=(1,)),),
            ),
        ),
    )

    with pytest.raises(DeckPlanValidationError, match="not-registered"):
        compile_deck_plan(plan)


def test_duplicate_block_ids_across_slides_are_rejected() -> None:
    payload = minimal_plan()
    duplicate = json.loads(json.dumps(payload["slides"][0]))
    duplicate["id"] = "detail"
    payload["slides"].append(duplicate)

    with pytest.raises(DeckPlanValidationError, match="duplicate block"):
        validate_deck_plan(payload)


def test_invalid_preference_type_raises_controlled_validation_error() -> None:
    payload = minimal_plan()
    payload["preferences"] = {"density": ["dense"]}

    with pytest.raises(DeckPlanValidationError, match="preferences.density"):
        validate_deck_plan(payload)


def test_all_fifteen_business_archetypes_are_unique_and_ordered() -> None:
    registry = load_archetypes()

    assert set(registry) == EXPECTED_ARCHETYPES
    assert len(registry) == 15
    for archetype in registry.values():
        assert len(archetype.sections) >= 6
        assert len(set(archetype.sections)) == len(archetype.sections)
        assert archetype.sections[0] == "cover"
        assert archetype.sections[-1] == "closing"


def test_scenario_aliases_resolve_to_stable_archetypes() -> None:
    assert resolve_archetype("商业汇报").id == "business-report"
    assert resolve_archetype("pitch deck").id == "investor-pitch"
    assert resolve_archetype("电商营销方案").id == "ecommerce-marketing"


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("sequence", "process"),
        ("timeline", "timeline"),
        ("comparison", "comparison"),
        ("bullets", "cards"),
        ("metrics", "big-number"),
        ("trend", "line-chart"),
        ("composition", "composition-chart"),
        ("matrix", "matrix"),
        ("risk", "risk-recommendation"),
        ("recommendation", "recommendation"),
        ("quote", "focal-statement"),
        ("table", "table"),
        ("image", "image-story"),
    ],
)
def test_semantics_map_to_expected_page_family(kind: str, expected: str) -> None:
    decision = rank_page_families(kind, item_count=3)

    assert decision.selected == expected
    assert decision.top_candidates[0].candidate_id == expected
    assert len(decision.top_candidates) == 3


def test_ranking_is_deterministic_and_trace_is_json_serializable() -> None:
    first = rank_page_families("trend", item_count=8)
    second = rank_page_families("trend", item_count=8)

    assert first == second
    serialized = json.dumps(first.to_dict(), ensure_ascii=False, sort_keys=True)
    assert json.loads(serialized)["selected"] == "line-chart"
    assert json.loads(serialized)["top_candidates"][0]["rule_ids"]
    assert json.loads(serialized)["rejected_candidates"]


def test_low_confidence_uses_safe_default_with_reason() -> None:
    decision = rank_page_families("generic", item_count=2)

    assert decision.selected == "structured-content"
    assert decision.fallback_reason == "LOW_CONFIDENCE_SAFE_DEFAULT"
    assert decision.confidence < decision.confidence_threshold
    assert decision.top_candidates[0].candidate_id == decision.selected
    assert "LOW_CONFIDENCE_SAFE_DEFAULT" in decision.top_candidates[0].rule_ids
    assert decision.selected not in {
        candidate.candidate_id for candidate in decision.rejected_candidates
    }


def test_single_parallel_point_uses_quiet_sparse_form() -> None:
    decision = rank_page_families("bullets", item_count=1)

    assert decision.selected == "text-media"
    assert decision.top_candidates[0].candidate_id == "text-media"


@pytest.mark.parametrize(
    ("chart_intent", "expected"),
    [
        ("trend", "line-chart"),
        ("comparison", "comparison"),
        ("composition", "composition-chart"),
        ("distribution", "distribution-chart"),
        ("relationship", "scatter-plot"),
    ],
)
def test_explicit_chart_intent_governs_compiled_family(
    chart_intent: str, expected: str
) -> None:
    payload = minimal_plan(kind="generic", items=[1, 2, 3])
    payload["slides"][0]["blocks"][0]["chart_intent"] = chart_intent

    compiled = compile_deck_plan(payload)

    assert compiled["slides"][0]["page_family"] == expected
    assert compiled["slides"][0]["decision_trace"]["semantic_type"] == chart_intent


def test_repetition_penalty_changes_third_parallel_page() -> None:
    decision = rank_page_families(
        "bullets", item_count=4, previous_families=("cards", "cards")
    )

    assert decision.selected == "modular-grid"
    cards = next(
        item for item in decision.top_candidates if item.candidate_id == "cards"
    )
    assert "RHYTHM_REPEAT_2" in cards.rule_ids


def test_capacity_split_preserves_every_item_and_continuation_order() -> None:
    payload = minimal_plan(
        kind="bullets", items=[f"point-{number}" for number in range(1, 12)]
    )
    slide = validate_deck_plan(payload).slides[0]

    split = split_slide(slide)

    assert [part.id for part in split] == [
        "summary",
        "summary--cont-2",
        "summary--cont-3",
    ]
    assert [part.continuation_of for part in split] == [None, "summary", "summary"]
    assert [len(part.blocks[0].items) for part in split] == [4, 4, 3]
    assert [item for part in split for item in part.blocks[0].items] == [
        f"point-{number}" for number in range(1, 12)
    ]


def test_sparse_content_is_preserved_without_generated_filler() -> None:
    payload = minimal_plan(kind="bullets", items=["one decisive point"])
    slide = validate_deck_plan(payload).slides[0]

    split = split_slide(slide)

    assert len(split) == 1
    assert split[0].blocks[0].items == ("one decisive point",)
    assert split[0].title == "核心结论"


def test_density_preference_changes_capacity_with_safe_registered_limits() -> None:
    payload = minimal_plan(
        kind="bullets", items=[f"point-{number}" for number in range(1, 6)]
    )
    slide = validate_deck_plan(payload).slides[0]

    sparse = split_slide(slide, density="sparse")
    balanced = split_slide(slide, density="balanced")
    dense = split_slide(slide, density="dense")

    assert [len(part.blocks[0].items) for part in sparse] == [3, 2]
    assert [len(part.blocks[0].items) for part in balanced] == [4, 1]
    assert [len(part.blocks[0].items) for part in dense] == [5]


def test_long_narrative_text_splits_without_dropping_characters() -> None:
    text = "第一段说明业务背景。" * 90
    payload = minimal_plan(kind="statement", items=[])
    del payload["slides"][0]["blocks"][0]["items"]
    payload["slides"][0]["blocks"][0]["text"] = text
    slide = validate_deck_plan(payload).slides[0]

    split = split_slide(slide, density="balanced")

    assert len(split) > 1
    assert "".join(part.blocks[0].text or "" for part in split) == text
    assert all(len(part.blocks[0].text or "") <= 720 for part in split)


def test_every_block_obeys_density_unit_limit_even_if_kind_limit_is_higher() -> None:
    payload = minimal_plan(kind="trend", items=list(range(9)))
    slide = validate_deck_plan(payload).slides[0]

    split = split_slide(slide, density="balanced")

    assert [len(part.blocks[0].items) for part in split] == [8, 1]


def test_mixed_text_and_items_split_once_without_duplication() -> None:
    text = "业务背景说明。" * 120
    items = [f"point-{number}" for number in range(1, 7)]
    payload = minimal_plan(kind="bullets", items=items)
    payload["slides"][0]["blocks"][0]["text"] = text
    slide = validate_deck_plan(payload).slides[0]

    split = split_slide(slide, density="balanced")

    assert "".join(part.blocks[0].text or "" for part in split) == text
    assert [item for part in split for item in part.blocks[0].items] == items
    assert sum(1 for part in split if part.blocks[0].text) >= 2
    assert sum(1 for part in split if part.blocks[0].items) == 2


def test_mixed_chart_text_continuations_do_not_claim_data_chart_semantics() -> None:
    payload = minimal_plan(kind="trend", items=[1, 2])
    payload["slides"][0]["blocks"][0]["chart_intent"] = "trend"
    payload["slides"][0]["blocks"][0]["text"] = "趋势背景说明。" * 180

    compiled = compile_deck_plan(payload)

    text_pages = [
        slide for slide in compiled["slides"] if slide["blocks"][0].get("text")
    ]
    data_pages = [
        slide for slide in compiled["slides"] if slide["blocks"][0].get("items")
    ]
    assert text_pages and data_pages
    assert all(slide["page_family"] not in {"line-chart", "area-chart"} for slide in text_pages)
    assert all(slide["semantic_basis"]["semantic_type"] == "statement" for slide in text_pages)
    assert all(slide["page_family"] in {"line-chart", "area-chart"} for slide in data_pages)


def test_content_only_plan_is_ordered_by_archetype_not_model_input_order() -> None:
    payload = {
        "schema_version": "1.0",
        "project": {"title": "运营复盘", "scenario": "operations-review"},
        "content": [
            {"id": "actions", "kind": "recommendation", "items": ["Fix"]},
            {"id": "risks", "kind": "risk", "items": ["Churn"]},
            {
                "id": "performance",
                "kind": "metrics",
                "items": [{"label": "GMV", "value": 120, "unit": "M"}],
            },
        ],
    }

    compiled = compile_deck_plan(payload)

    assert [slide["role"] for slide in compiled["slides"]] == [
        "performance",
        "issues",
        "action-plan",
    ]
    assert [slide["id"] for slide in compiled["slides"]] == [
        "performance",
        "risks",
        "actions",
    ]


def test_compile_preserves_archetype_outline_and_capacity_trace() -> None:
    payload = minimal_plan(
        kind="bullets", items=[f"point-{number}" for number in range(1, 7)]
    )

    compiled = compile_deck_plan(payload)

    assert compiled["schema_version"] == "1.0"
    assert compiled["archetype_id"] == "business-report"
    assert compiled["archetype_outline"] == list(
        resolve_archetype("business-report").sections
    )
    assert [slide["id"] for slide in compiled["slides"]] == [
        "summary",
        "summary--cont-2",
    ]
    assert compiled["slides"][1]["continuation_of"] == "summary"
    assert compiled["slides"][0]["decision_trace"]["top_candidates"]
    assert json.loads(json.dumps(compiled, ensure_ascii=False)) == compiled


def test_multi_block_slide_uses_dominant_data_semantics_not_first_block() -> None:
    payload = minimal_plan(kind="generic", items=["context"])
    payload["slides"][0]["blocks"].append(
        {
            "id": "trend-data",
            "kind": "trend",
            "items": [1, 2, 3, 4],
        }
    )

    compiled = compile_deck_plan(payload)

    assert compiled["slides"][0]["page_family"] == "line-chart"
    assert compiled["slides"][0]["semantic_basis"]["block_id"] == "trend-data"
    assert compiled["slides"][0]["semantic_basis"]["semantic_type"] == "trend"


def test_compilation_is_byte_for_byte_stable_for_same_input() -> None:
    payload = minimal_plan(kind="comparison", items=["before", "after"])

    first = json.dumps(
        compile_deck_plan(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    second = json.dumps(
        compile_deck_plan(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )

    assert first == second
