from __future__ import annotations

import copy
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest
import jsonschema
from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "skills" / "owned" / "window-pptx" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


from window_pptx.cli import build_dry_run_result, collect_requested_actions, parse_args  # noqa: E402
from window_pptx.generation import GenerationGateError, prepare_brief_generation  # noqa: E402
from window_pptx.design_quality import inspect_design_quality  # noqa: E402
from window_pptx.layouts import ResolvedSlot, SlideSize  # noqa: E402
from window_pptx.render_plan import (  # noqa: E402
    AssetBinding,
    RenderPlanError,
    _font_size,
    _poster_closing_slot_texts,
    _poster_title_text,
    _rich_text_runs,
    semantic_form_chart_type,
    validate_render_plan,
)
from window_pptx.assets import AssetRecord  # noqa: E402
from window_pptx.preview_quality import inspect_preview_images  # noqa: E402
from window_pptx.text_layout import estimate_text_layout  # noqa: E402
from window_pptx.quality_v2 import (  # noqa: E402
    StageRepairPass,
    build_quality_report_v2,
    generation_quality_findings,
)
from window_pptx.weak_model import (  # noqa: E402
    _exact_number_word,
    compile_brief_plan,
    compile_brief_with_retries,
    load_narrative_rules,
    normalize_brief_plan,
)
import window_pptx_automation as automation  # noqa: E402


def test_bounded_number_word_normalization_supports_editable_metric_values() -> None:
    assert _exact_number_word("Forty-one") == 41
    assert _exact_number_word("one hundred and twenty") == 120
    assert _exact_number_word("not a number") is None


def test_shared_text_layout_counts_explicit_lines_before_character_capacity() -> None:
    compact = estimate_text_layout(
        "Before 44 percent After 41 percent",
        width_in=5.0,
        height_in=0.8,
        font_size_pt=18,
    )
    forced = estimate_text_layout(
        "Before\n44 percent\nAfter\n41 percent",
        width_in=5.0,
        height_in=0.8,
        font_size_pt=18,
    )

    assert compact.fits is True
    assert forced.fits is False
    assert forced.required_lines == 4
    assert forced.available_lines == 2


def test_shared_text_layout_uses_wide_glyph_width_for_cjk() -> None:
    latin = estimate_text_layout(
        "AAAAAAAAAAAA",
        width_in=1.2,
        height_in=1.5,
        font_size_pt=18,
    )
    cjk = estimate_text_layout(
        "数据分析数据分析",
        width_in=1.2,
        height_in=1.5,
        font_size_pt=18,
    )

    assert cjk.required_lines > latin.required_lines


def test_shared_text_layout_does_not_reject_calibrated_latin_cover_title() -> None:
    estimate = estimate_text_layout(
        "Pulse AI Assistant Launch",
        width_in=8.147926,
        height_in=1.591667,
        font_size_pt=44,
    )

    assert estimate.required_lines == 1
    assert estimate.available_lines == 1
    assert estimate.fits is True


def test_long_closing_cta_uses_body_scale_instead_of_oversized_title_text() -> None:
    slot = ResolvedSlot(
        id="body",
        component="cta",
        x=5.7,
        y=3.2,
        width=6.05,
        height=3.1,
        allow_overlap=True,
    )
    typography = {
        "display": 44,
        "title": 32,
        "subtitle": 22,
        "body": 18,
        "label": 12,
        "footnote": 11,
    }

    assert (
        _font_size(
            "cta",
            typography,
            text=(
                "统一知识入口 · 审批周期 10 → 5 天 · 建立运营闭环\n\n"
                "决策：试点范围｜业务负责人｜启动日期"
            ),
            slot=slot,
            role="closing",
            family_id="cta",
        )
        == 18
    )


def test_poster_title_keeps_business_suffix_intact_and_avoids_orphan() -> None:
    assert _poster_title_text(
        "企业知识协同平台建设提案",
        layout_id="cover.poster-editorial",
    ) == "企业知识协同平台\n建设提案"
    assert _poster_title_text(
        "企业知识协同平台建设提案",
        layout_id="cover.full-visual",
    ) == "企业知识协同平台建设提案"


def test_poster_closing_splits_evidence_and_three_decision_chips() -> None:
    assert _poster_closing_slot_texts(
        "统一知识入口 · 审批周期 10 → 5 天 · 建立运营闭环\n\n"
        "决策：试点范围｜业务负责人｜启动日期"
    ) == {
        "primary": "统一知识入口 · 审批周期 10 → 5 天\n建立运营闭环",
        "decision-one": "试点范围",
        "decision-two": "业务负责人",
        "decision-three": "启动日期",
    }


def test_closing_cta_promotes_arrow_metric_to_editable_rich_text() -> None:
    runs = _rich_text_runs(
        "cta",
        "统一知识入口 · 审批周期 10 → 5 天\n建立运营闭环",
        value_font_size_pt=32,
        typography={
            "display": 44,
            "title": 32,
            "subtitle": 22,
            "body": 18,
            "label": 12,
            "footnote": 11,
        },
        colors={
            "text": "#111827",
            "muted_text": "#4B5563",
            "primary": "#B45309",
        },
    )

    assert runs is not None
    assert [(run.text, run.font_size_pt, run.bold) for run in runs] == [
        ("统一知识入口 · 审批周期 ", 18, False),
        ("10 → 5", 32, True),
        (" 天", 18, False),
        ("建立运营闭环", 18, False),
    ]


def test_multiparagraph_cta_uses_plain_editable_text() -> None:
    runs = _rich_text_runs(
        "cta",
        (
            "统一知识入口 · 审批周期 10 → 5 天 · 建立运营闭环\n\n"
            "决策：试点范围｜业务负责人｜启动日期"
        ),
        value_font_size_pt=32,
        typography={
            "display": 44,
            "title": 32,
            "subtitle": 22,
            "body": 18,
            "label": 12,
            "footnote": 11,
        },
        colors={
            "text": "#111827",
            "muted_text": "#4B5563",
            "primary": "#B45309",
        },
    )

    assert runs is None


def facts() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "project": {
            "title": "Northstar Q2 Review",
            "objective": "Choose the two Q3 priorities.",
            "audience": "executive committee",
            "language": "en-US",
        },
        "sources": [{"id": "request", "kind": "request", "locator": "REQUEST.md"}],
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


def brief(*, scenario: str = "business-report", beat: str = "performance") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "scenario_id": scenario,
        "groups": [
            {
                "id": "evidence",
                "fact_refs": ["revenue"],
                "beat_hint": beat,
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


def test_common_role_like_semantic_alias_is_normalized_safely() -> None:
    payload = brief(scenario="business-report", beat="performance")
    payload["groups"][0]["semantic_hint"] = "scope"  # type: ignore[index]

    normalized, trace = normalize_brief_plan(payload)

    assert normalized["groups"][0]["semantic_hint"] == "bullets"
    assert "NORMALIZED_SEMANTIC_ALIAS" in trace.changes
    compilation = compile_brief_plan(facts(), normalized)
    assert compilation.brief_plan.groups[0].semantic_hint == "bullets"


def test_product_showcase_role_alias_normalizes_to_image_semantic() -> None:
    payload = brief(scenario="product-launch", beat="product-vision")
    payload["groups"][0]["semantic_hint"] = "product-showcase"  # type: ignore[index]

    normalized, trace = normalize_brief_plan(payload)

    assert normalized["groups"][0]["semantic_hint"] == "image"
    assert "NORMALIZED_SEMANTIC_ALIAS" in trace.changes


@pytest.mark.parametrize(
    ("objective", "language", "expected_title"),
    [
        ("Decide the Q3 investment priority.", "en-US", "Decision required"),
        ("Approve the Q3 investment plan.", "en-US", "Decision required"),
        ("Select the two Q3 priorities.", "en-US", "Decision required"),
        ("Choose the two Q3 priorities.", "en-US", "Decision required"),
        ("Confirm the Q3 launch scope.", "en-US", "Decision required"),
        ("Commit the Q3 launch budget.", "en-US", "Decision required"),
        ("Prioritize the retention intervention.", "en-US", "Decision required"),
        ("Launch the Q3 retention program.", "en-US", "Next action"),
        ("Review the Q3 retention results.", "en-US", "Next action"),
        ("决定第三季度投资优先级。", "zh-CN", "决策事项"),
        ("批准第三季度投资计划。", "zh-CN", "决策事项"),
        ("选择两项第三季度优先事项。", "zh-CN", "决策事项"),
        ("确认第三季度发布范围。", "zh-CN", "决策事项"),
        ("优先处理留存率改善事项。", "zh-CN", "决策事项"),
        ("启动第三季度留存计划。", "zh-CN", "下一步行动"),
        ("复盘第三季度留存结果。", "zh-CN", "下一步行动"),
    ],
)
def test_closing_title_classifies_decisions_without_rewriting_trusted_action(
    objective: str,
    language: str,
    expected_title: str,
) -> None:
    objective_facts = copy.deepcopy(facts())
    objective_facts["project"]["objective"] = objective  # type: ignore[index]
    objective_facts["project"]["language"] = language  # type: ignore[index]

    compilation = compile_brief_plan(objective_facts, brief())
    closing = compilation.deck_plan["slides"][-1]

    assert closing["id"] == "closing"
    assert closing["title"] == expected_title
    assert closing["blocks"] == [
        {"id": "closing.action", "kind": "recommendation", "text": objective}
    ]
    assert compilation.narrative.slides[-1].title == expected_title


def test_text_metric_requires_numeric_evidence_but_not_structured_value() -> None:
    numeric_facts = copy.deepcopy(facts())
    numeric_facts["facts"][0].pop("value")
    numeric_facts["facts"][0].pop("unit")

    numeric = compile_brief_plan(numeric_facts, brief())

    assert numeric.deck_plan["slides"][1]["blocks"][0]["kind"] == "metrics"
    assert numeric.deck_plan["slides"][1]["blocks"][0]["text"] == (
        "Revenue reached 48.2 million dollars in Q2."
    )

    narrative_only = copy.deepcopy(numeric_facts)
    narrative_only["facts"][0]["text"] = (
        "Leadership selected onboarding quality as the next operating priority."
    )
    downgraded = compile_brief_plan(narrative_only, brief())

    assert downgraded.deck_plan["slides"][1]["blocks"][0]["kind"] == "statement"
    assert downgraded.deck_plan["slides"][1]["title"] == "Performance"


def test_trusted_from_to_metric_becomes_editable_before_after_comparison() -> None:
    metric_facts = copy.deepcopy(facts())
    metric_facts["facts"][0].update(
        {
            "text": "Gross margin declined from 44 percent to 41 percent.",
            "value": 41,
            "unit": "percent",
            "claim_key": "gross-margin",
        }
    )

    result = compile_brief_plan(metric_facts, brief())
    slide = next(item for item in result.deck_plan["slides"] if item["id"] == "evidence")

    assert slide["blocks"][0]["kind"] == "comparison"
    assert slide["blocks"][0]["items"] == [
        {"label": "Before", "value": 44, "unit": "percent"},
        {"label": "After", "value": 41, "unit": "percent"},
    ]
    assert result.narrative.coverage["semantic_adjustments"] == [
        "evidence:EXPLICIT_NUMERIC_CHANGE_OVERRIDES_MODEL:metrics->comparison"
    ]


def test_trusted_cross_unit_change_preserves_each_value_unit_binding() -> None:
    metric_facts = copy.deepcopy(facts())
    metric_facts["facts"][0].update(
        {
            "text": "Pilot teams reduced preparation from 3 hours to 35 minutes.",
            "value": 35,
            "unit": "minutes",
            "claim_key": "preparation-time",
        }
    )

    result = compile_brief_plan(metric_facts, brief())
    slide = next(item for item in result.deck_plan["slides"] if item["id"] == "evidence")

    assert slide["blocks"][0]["items"] == [
        {"label": "Before", "value": 3, "unit": "hours"},
        {"label": "After", "value": 35, "unit": "minutes"},
    ]


def test_comma_grouped_measure_and_source_qualified_labels_remain_exact() -> None:
    metric_facts = copy.deepcopy(facts())
    metric_facts["facts"][0].update(
        {
            "text": "Q2 revenue was 48.2 million dollars, 12 percent above Q1.",
            "value": 48.2,
            "unit": "million dollars",
            "claim_key": "q2-revenue",
            "time_scope": "Q2",
        }
    )
    revenue = compile_brief_plan(metric_facts, brief())
    revenue_slide = next(
        item for item in revenue.deck_plan["slides"] if item["id"] == "evidence"
    )
    assert revenue_slide["blocks"][0]["items"] == [
        {
            "label": "Q2 Revenue",
            "value": 48.2,
            "unit": "million dollars",
            "category": "Q2",
        },
        {"label": "Above Q1", "value": 12, "unit": "percent"},
    ]

    metric_facts["facts"][0].update(
        {
            "text": "The analysis covers 42,180 subscriptions.",
            "value": 42180,
            "unit": "subscriptions",
            "claim_key": "sample",
        }
    )
    metric_facts["facts"][0].pop("time_scope")
    sample = compile_brief_plan(metric_facts, brief())
    sample_slide = next(
        item for item in sample.deck_plan["slides"] if item["id"] == "evidence"
    )
    assert sample_slide["blocks"][0]["items"][0]["value"] == 42180
    rendered_sample = prepare_brief_generation(
        metric_facts,
        brief(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        build_render=True,
    )
    assert rendered_sample.render_plan is not None
    assert any(
        "42,180 subscriptions" in (item.text or "")
        for slide in rendered_sample.render_plan.slides
        for item in slide.objects
        if item.component == "kpi"
    )


def test_precise_month_range_overrides_lossy_year_category() -> None:
    metric_facts = copy.deepcopy(facts())
    metric_facts["facts"][0].update(
        {
            "text": (
                "The analysis covers 42,180 subscriptions from January "
                "through June 2026."
            ),
            "value": 42180,
            "unit": "subscriptions",
            "claim_key": "sample",
            "time_scope": "2026",
        }
    )

    result = compile_brief_plan(metric_facts, brief())
    slide = next(item for item in result.deck_plan["slides"] if item["id"] == "evidence")

    assert slide["blocks"][0]["items"][0]["category"] == "January–June 2026"
    metric_facts["facts"][0].pop("time_scope")

    metric_facts["facts"][0].update(
        {
            "text": (
                "Ninety-day retention is 81 percent for annual plans and "
                "59 percent for monthly plans."
            ),
            "value": 81,
            "unit": "percent",
            "claim_key": "segments",
        }
    )
    segments = compile_brief_plan(metric_facts, brief())
    assert (
        "evidence:LONG_EVIDENCE_TITLE_ROLE_FALLBACK"
        not in segments.narrative.coverage["semantic_adjustments"]
    )
    segment_slide = next(
        item for item in segments.deck_plan["slides"] if item["id"] == "evidence"
    )
    assert segment_slide["title"] == (
        "Ninety-day retention is 81 percent for annual plans and "
        "59 percent for monthly plans."
    )
    assert segment_slide["blocks"][0]["items"] == [
        {"label": "Annual Plans", "value": 81, "unit": "percent"},
        {
            "label": "Monthly Plans",
            "value": 59,
            "unit": "percent",
        },
    ]

    metric_facts["facts"][0].update(
        {
            "text": (
                "Customers completing onboarding within 48 hours retain "
                "11 percentage points better."
            ),
            "value": 48,
            "unit": "hours",
            "claim_key": "driver",
        }
    )
    driver = compile_brief_plan(metric_facts, brief())
    driver_slide = next(
        item for item in driver.deck_plan["slides"] if item["id"] == "evidence"
    )
    assert [item["label"] for item in driver_slide["blocks"][0]["items"]] == [
        "Onboarding Window",
        "Retention Lift",
    ]


def test_exact_parallel_list_becomes_cards_without_model_authored_design() -> None:
    list_facts = copy.deepcopy(facts())
    list_facts["facts"][0].update(
        {
            "kind": "claim",
            "text": "The launch supports Microsoft Teams, Slack, and email summaries.",
            "claim_key": "integrations",
        }
    )
    list_facts["facts"][0].pop("value")
    list_facts["facts"][0].pop("unit")
    list_brief = brief()
    list_brief["groups"][0]["semantic_hint"] = "table"

    result = compile_brief_plan(list_facts, list_brief)
    slide = next(item for item in result.deck_plan["slides"] if item["id"] == "evidence")

    assert slide["blocks"][0]["kind"] == "bullets"
    assert slide["blocks"][0]["items"] == [
        "Microsoft Teams",
        "Slack",
        "email summaries",
    ]
    assert result.narrative.coverage["semantic_adjustments"] == [
        "evidence:EXACT_PARALLEL_LIST_OVERRIDES_MODEL:table->bullets",
        "evidence:LONG_EVIDENCE_TITLE_ROLE_FALLBACK",
    ]


def test_metric_panels_compile_to_governed_editable_text_hierarchy() -> None:
    metric_facts = copy.deepcopy(facts())
    metric_facts["facts"][0].update(
        {
            "text": "Gross margin declined from 44 percent to 41 percent.",
            "value": 41,
            "unit": "percent",
            "claim_key": "gross-margin",
        }
    )
    result = prepare_brief_generation(
        metric_facts,
        brief(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        build_render=True,
    )
    assert result.render_plan is not None
    panels = [
        item
        for slide in result.render_plan.slides
        for item in slide.objects
        if item.component == "comparison-panel"
    ]

    assert len(panels) == 2
    assert panels[0].text == "Before\n44 percent"
    assert panels[0].text_runs is not None
    assert [(run.text, run.font_size_pt, run.bold) for run in panels[0].text_runs] == [
        ("Before", 18, False),
        ("44 percent", panels[0].font_size_pt, True),
    ]
    assert "text_runs" in panels[0].to_dict()
    title = next(
        item
        for slide in result.render_plan.slides
        for item in slide.objects
        if item.component == "title"
    )
    assert "text_runs" not in title.to_dict()

    invalid_run = replace(panels[0].text_runs[0], text_color="#FFFFFF")
    invalid_object = replace(
        panels[0],
        text_runs=(invalid_run, *panels[0].text_runs[1:]),
    )
    target_slide = next(
        slide for slide in result.render_plan.slides if panels[0] in slide.objects
    )
    invalid_slide = replace(
        target_slide,
        objects=tuple(
            invalid_object if item.id == panels[0].id else item
            for item in target_slide.objects
        ),
    )
    invalid_plan = replace(
        result.render_plan,
        slides=tuple(
            invalid_slide if slide.source_id == target_slide.source_id else slide
            for slide in result.render_plan.slides
        ),
    )
    with pytest.raises(RenderPlanError, match="rich text"):
        validate_render_plan(invalid_plan)


def test_explicit_two_priority_instruction_becomes_two_editable_action_panels() -> None:
    instruction_facts = copy.deepcopy(facts())
    instruction_facts["facts"].append(
        {
            "id": "priorities",
            "kind": "instruction",
            "text": (
                "The executive team identified onboarding capacity and gross margin "
                "recovery as the two Q3 operating priorities."
            ),
            "language": "en-US",
            "source_id": "request",
            "locator": "line:2",
            "required": True,
        }
    )
    instruction_brief = brief()
    instruction_brief["groups"].append(
        {
            "id": "action",
            "fact_refs": ["priorities"],
            "beat_hint": "recommendations",
            "semantic_hint": "recommendation",
            "importance": "critical",
        }
    )

    compilation = compile_brief_plan(instruction_facts, instruction_brief)
    action_slide = next(
        slide for slide in compilation.deck_plan["slides"] if slide["id"] == "action"
    )
    assert action_slide["blocks"][0]["items"] == [
        {"label": "Priority 1", "text": "onboarding capacity"},
        {"label": "Priority 2", "text": "gross margin recovery"},
    ]

    generation = prepare_brief_generation(
        instruction_facts,
        instruction_brief,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        build_render=True,
    )
    assert generation.render_plan is not None
    rendered = next(
        slide for slide in generation.render_plan.slides if slide.source_id == "action"
    )
    assert rendered.layout_id == "recommendation.dual"
    panels = [item for item in rendered.objects if item.component == "recommendation-panel"]
    assert [item.text for item in panels] == [
        "Priority 1\nonboarding capacity",
        "Priority 2\ngross margin recovery",
    ]
    assert all(item.text_runs is not None for item in panels)


def test_cli_exposes_strict_brief_routes_and_audited_outputs() -> None:
    args = parse_args(
        [
            "--project-dir",
            "project",
            "--fact-store",
            "facts.json",
            "--brief-plan",
            "brief.json",
            "--render-brief-plan",
            "--dry-run",
        ]
    )
    assert collect_requested_actions(args) == ["render_brief_plan"]
    result = build_dry_run_result(args, "project")
    assert result["would_run"] == ["render_brief_plan"]
    assert "project/.window-pptx/audits/narrative-plan.json" in result["would_write"]
    assert "project/.window-pptx/audits/direction-decision.json" in result["would_write"]
    assert "project/.window-pptx/audits/quality-report.v2.json" in result["would_write"]


def test_cli_requires_both_weak_model_contracts() -> None:
    with pytest.raises(SystemExit):
        parse_args(
            [
                "--project-dir",
                "project",
                "--fact-store",
                "facts.json",
                "--compile-brief-plan",
            ]
        )


def test_cli_scopes_direct_agnes_generation_to_brief_render_route() -> None:
    args = parse_args(
        [
            "--project-dir",
            "project",
            "--fact-store",
            "facts.json",
            "--brief-plan",
            "brief.json",
            "--render-brief-plan",
            "--generate-assets-with-agnes",
            "--dry-run",
        ]
    )
    result = build_dry_run_result(args, "project")

    assert args.generate_assets_with_agnes is True
    assert (
        "project/.window-pptx/audits/asset-materialization.json"
        in result["would_write"]
    )
    assert "project/.window-pptx/generated-assets" in result["would_write"]
    with pytest.raises(SystemExit):
        parse_args(
            [
                "--project-dir",
                "project",
                "--generate-assets-with-agnes",
                "--dry-run",
            ]
        )


def test_cli_rejects_brand_spec_on_legacy_direct_deck_route() -> None:
    with pytest.raises(SystemExit):
        parse_args(
            [
                "--project-dir",
                "project",
                "--deck-plan",
                "deck.json",
                "--render-deck-plan",
                "--brand-spec",
                "brand.json",
            ]
        )


def test_interactive_direction_dry_run_reports_the_pre_com_stop() -> None:
    args = parse_args(
        [
            "--project-dir",
            "project",
            "--fact-store",
            "facts.json",
            "--brief-plan",
            "brief.json",
            "--render-brief-plan",
            "--direction-mode",
            "interactive",
            "--dry-run",
        ]
    )

    result = build_dry_run_result(args, "project")

    assert result["would_write"] == []
    assert any("stops before COM" in item for item in result["warnings"])


def test_facade_compiles_brief_without_powerpoint(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "facts.json").write_text(
        json.dumps(facts()), encoding="utf-8"
    )
    (project / "brief.json").write_text(
        json.dumps(brief()), encoding="utf-8"
    )
    assert automation.main(
        [
            "--project-dir",
            str(project),
            "--fact-store",
            "facts.json",
            "--brief-plan",
            "brief.json",
            "--compile-brief-plan",
            "--no-output-deck",
            "--json",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["fact_store_digest"]
    assert payload["narrative_plan"]["coverage"]["required_fact_coverage"] == 1.0
    assert payload["direction_decision"]["selected_profile_id"]


def test_facade_uses_a_valid_retry_and_records_attempts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "facts.json").write_text(json.dumps(facts()), encoding="utf-8")
    (project / "brief-invalid.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "scenario_id": "business-report",
                "groups": brief()["groups"],
                "font": "Arial",
            }
        ),
        encoding="utf-8",
    )
    (project / "brief-retry.json").write_text(
        json.dumps(brief()), encoding="utf-8"
    )

    assert automation.main(
        [
            "--project-dir",
            str(project),
            "--fact-store",
            "facts.json",
            "--brief-plan",
            "brief-invalid.json",
            "--brief-retry-plan",
            "brief-retry.json",
            "--compile-brief-plan",
            "--no-output-deck",
            "--json",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["brief_fallback_used"] is False
    assert [item["accepted"] for item in payload["brief_attempts"]] == [
        False,
        True,
    ]


def test_facade_uses_fact_safe_default_after_available_attempts_fail(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "facts.json").write_text(json.dumps(facts()), encoding="utf-8")
    (project / "brief-invalid.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "scenario_id": "business-report",
                "groups": [],
            }
        ),
        encoding="utf-8",
    )

    assert automation.main(
        [
            "--project-dir",
            str(project),
            "--fact-store",
            "facts.json",
            "--brief-plan",
            "brief-invalid.json",
            "--compile-brief-plan",
            "--no-output-deck",
            "--json",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["brief_fallback_used"] is True
    assert payload["brief_attempts"][0]["accepted"] is False
    assert payload["narrative_plan"]["coverage"]["required_fact_coverage"] == 1.0


def test_all_15_scenarios_compile_with_their_required_beat() -> None:
    rules = load_narrative_rules()
    assert len(rules) == 15
    for scenario, critical_beats in rules.items():
        result = prepare_brief_generation(
            facts(),
            brief(scenario=scenario, beat=critical_beats[0]),
        )
        assert result.compilation.narrative.archetype_id == scenario
        assert result.compilation.narrative.coverage["required_fact_coverage"] == 1.0


def test_bounded_model_retries_use_fact_safe_default_after_three_failures() -> None:
    invalid = {"schema_version": "1.0", "scenario_id": "business-report", "groups": []}
    result = compile_brief_with_retries(
        facts(),
        (invalid, {"font": "Arial"}, "not json"),
        scenario_id="business-report",
        max_retries=2,
    )
    assert len(result.attempts) == 3
    assert result.fallback_used is True
    assert result.compilation.narrative.coverage["required_fact_coverage"] == 1.0
    assert result.compilation.brief_plan.preferences_dict()["motion"] == "off"


def test_render_preflight_is_native_editable_and_fact_safe() -> None:
    result = prepare_brief_generation(
        facts(),
        brief(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        build_render=True,
    )
    assert result.render_plan is not None
    assert all(
        item.native_editable
        for slide in result.render_plan.slides
        for item in slide.objects
    )
    assert "Revenue reached 48.2 million dollars in Q2." in json.dumps(
        result.compiled_deck, ensure_ascii=False
    )
    assert result.direction is not None
    assert len(result.direction.candidates) == 3


def test_high_confidence_unbranded_direction_keeps_scenario_fit() -> None:
    result = prepare_brief_generation(
        facts(),
        brief(scenario="product-launch", beat="value-proposition"),
    )
    assert result.direction is not None
    assert result.direction.fallback_reason is None
    assert result.direction.selected_profile_id == "neutral-diagrammatic-minimal"
    assert result.selected_theme_id == "executive-light"


def test_missing_image_asset_downgrades_before_layout_selection() -> None:
    image_facts = copy.deepcopy(facts())
    image_facts["facts"][0]["recommended_semantic"] = "image"  # type: ignore[index]
    image_brief = copy.deepcopy(brief())
    image_brief["groups"][0]["semantic_hint"] = "image"  # type: ignore[index]
    result = prepare_brief_generation(image_facts, image_brief)
    assert result.asset_fallbacks
    assert len(result.pre_render_repair_passes) == 1
    assert result.pre_render_repair_passes[0].accepted is True
    assert result.pre_render_repair_passes[0].rolled_back is False
    assert result.effective_deck_plan["slides"][1]["blocks"][0]["kind"] == "statement"
    assert result.compiled_deck["slides"][1]["page_family"] != "image-story"


def test_invalid_asset_binding_is_rejected_before_layout_selection(tmp_path: Path) -> None:
    image_facts = copy.deepcopy(facts())
    image_facts["facts"][0]["recommended_semantic"] = "image"  # type: ignore[index]
    image_brief = copy.deepcopy(brief())
    image_brief["groups"][0]["semantic_hint"] = "image"  # type: ignore[index]
    binding = AssetBinding(
        tmp_path / "missing.png",
        AssetRecord(
            id="product-image",
            kind="image",
            style=None,
            aspect_ratio=1.6,
            quality=90,
            source="trusted",
            license="MIT",
            retrieved_at="2026-07-20",
            width_px=1600,
            height_px=1000,
        ),
    )
    result = prepare_brief_generation(
        image_facts, image_brief, asset_bindings={"request#line:1": binding}
    )
    assert result.asset_rejections
    assert result.asset_fallbacks
    assert result.compiled_deck["slides"][1]["page_family"] != "image-story"


def test_safe_svg_logo_survives_asset_preflight_and_render_compilation(
    tmp_path: Path,
) -> None:
    logo = tmp_path / "northstar-logo.svg"
    logo.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">'
        '<path d="M0 0h200v100H0z" fill="#0B3A67"/></svg>',
        encoding="utf-8",
    )
    image_facts = copy.deepcopy(facts())
    image_facts["facts"][0]["recommended_semantic"] = "image"  # type: ignore[index]
    image_brief = copy.deepcopy(brief())
    image_brief["groups"][0]["semantic_hint"] = "image"  # type: ignore[index]
    binding = AssetBinding(
        logo,
        AssetRecord(
            id="northstar-logo",
            kind="logo",
            style="flat",
            aspect_ratio=2.0,
            quality=95,
            source="request#line:1",
            license="MIT",
            retrieved_at="2026-07-21",
        ),
    )

    result = prepare_brief_generation(
        image_facts,
        image_brief,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_bindings={"request#line:1": binding},
        build_render=True,
    )

    assert result.asset_rejections == ()
    assert result.asset_fallbacks == ()
    assert result.render_plan is not None
    assert any(
        item.source_path == logo.resolve()
        for slide in result.render_plan.slides
        for item in slide.objects
    )


@pytest.mark.parametrize(
    "unsafe_payload",
    [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 1">'
        '<image href="https://example.invalid/tracker.png"/></svg>',
        '<?xml-stylesheet href="https://example.invalid/style.css"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 1">'
        '<path d="M0 0h2v1H0z"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 1">'
        '<style>path{fill:u\\72l(https://example.invalid/a.svg)}</style>'
        '<path d="M0 0h2v1H0z"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xml:base="https://example.invalid/a.svg" viewBox="0 0 2 1">'
        '<defs><path id="shape" d="M0 0h2v1H0z"/></defs>'
        '<use href="#shape"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 1">'
        '<rect width="2" height="1"><animate attributeName="opacity" '
        'values="0;1" repeatCount="indefinite"/></rect></svg>',
    ],
)
def test_active_or_embedded_svg_is_rejected_before_layout_selection(
    tmp_path: Path,
    unsafe_payload: str,
) -> None:
    unsafe = tmp_path / "unsafe.svg"
    unsafe.write_text(unsafe_payload, encoding="utf-8")
    image_facts = copy.deepcopy(facts())
    image_facts["facts"][0]["recommended_semantic"] = "image"  # type: ignore[index]
    binding = AssetBinding(
        unsafe,
        AssetRecord(
            id="unsafe-logo",
            kind="logo",
            style="flat",
            aspect_ratio=2.0,
            quality=95,
            source="request#line:1",
            license="MIT",
            retrieved_at="2026-07-21",
        ),
    )

    result = prepare_brief_generation(
        image_facts,
        brief(),
        asset_bindings={"request#line:1": binding},
    )

    assert result.asset_rejections
    assert any("svg" in item.casefold() for item in result.asset_rejections)
    assert result.asset_fallbacks


def test_interactive_direction_stops_before_render_plan() -> None:
    result = prepare_brief_generation(
        facts(),
        brief(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        direction_mode="interactive",
        build_render=True,
    )
    assert result.interaction_required is True
    assert result.render_plan is not None
    assert result.direction is not None
    assert {item.slot for item in result.direction.candidates} == {
        "safe",
        "editorial",
        "expressive",
    }
    payload = result.to_dict()
    assert payload["proof_render_plan"] is not None
    assert len(payload["proof_render_plan"]["slides"]) == len(result.proof_slide_ids)


def test_brand_fidelity_is_a_hard_gate_when_required_asset_is_missing() -> None:
    brand = {
        "schema_version": "1.0",
        "name": "Northstar",
        "require_brand_fidelity": True,
        "required_assets": [{"kind": "logo", "mandatory": True}],
    }
    with pytest.raises(GenerationGateError, match="BRAND_ASSET_GATE_FAILED"):
        prepare_brief_generation(facts(), brief(), brand_spec=brand)


def test_brand_fidelity_is_a_hard_gate_when_declared_font_is_missing() -> None:
    brand = {
        "schema_version": "1.0",
        "name": "Northstar",
        "require_brand_fidelity": True,
        "fonts": [
            {
                "role": "heading",
                "family": "Northstar Sans",
                "source": "brand-guide",
            }
        ],
    }
    with pytest.raises(GenerationGateError, match="BRAND_FIDELITY_GATE_FAILED"):
        prepare_brief_generation(
            facts(),
            brief(),
            installed_fonts={"Arial"},
            brand_spec=brand,
        )


def test_non_locked_brand_font_fallback_is_explicit_render_evidence() -> None:
    brand = {
        "schema_version": "1.0",
        "name": "Northstar",
        "require_brand_fidelity": False,
        "fonts": [
            {
                "role": "heading",
                "family": "Northstar Sans",
                "source": "brand-guide",
            }
        ],
    }
    result = prepare_brief_generation(
        facts(),
        brief(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        brand_spec=brand,
        build_render=True,
    )
    assert result.render_plan is not None
    assert any(item.code == "BRAND_FONT_MISSING" for item in result.brand_findings)
    assert any(
        item.code == "FONT_FALLBACK" for item in result.render_plan.theme_events
    )


def test_generation_manifest_binds_brand_fonts_and_asset_sources() -> None:
    brand = {
        "schema_version": "1.0",
        "name": "Northstar",
        "require_brand_fidelity": False,
        "palette": [
            {"role": "primary", "value": "#123456", "source": "brand-guide"}
        ],
    }
    result = prepare_brief_generation(
        facts(),
        brief(),
        installed_fonts={"Arial", "Aptos"},
        brand_spec=brand,
        brand_spec_source="/evidence/brand-spec.json",
        asset_manifest_source="/evidence/asset-manifest.json",
    )
    payload = result.to_dict(include_render_plan=False)

    brand_evidence = payload["brand_spec_evidence"]
    assert brand_evidence["source"] == "file"
    assert brand_evidence["path"] == "/evidence/brand-spec.json"
    assert brand_evidence["content"]["name"] == "Northstar"
    assert len(brand_evidence["sha256"]) == 64
    assert payload["font_inventory_evidence"]["fonts"] == ["Aptos", "Arial"]
    assert len(payload["font_inventory_evidence"]["sha256"]) == 64
    assert payload["asset_manifest_evidence"]["path"] == (
        "/evidence/asset-manifest.json"
    )
    assert payload["asset_manifest_evidence"]["content"] == {
        "schema_version": "1.0",
        "bindings": {},
    }


def test_locked_brand_prohibited_pattern_is_enforced_after_compilation() -> None:
    brand = {
        "schema_version": "1.0",
        "name": "Northstar",
        "require_brand_fidelity": True,
        "prohibited_patterns": ["executive-light"],
    }
    with pytest.raises(GenerationGateError, match="BRAND_PROHIBITED_PATTERN_DETECTED"):
        prepare_brief_generation(
            facts(),
            brief(),
            slide_size=SlideSize(13.333, 7.5),
            installed_fonts={"Arial"},
            brand_spec=brand,
            build_render=True,
        )


def test_anti_slop_checks_card_monoculture_and_locked_direction_fit() -> None:
    result = prepare_brief_generation(
        facts(),
        brief(),
        direction_mode="locked",
        direction_id="bold-typographic-manifesto",
    )
    card_slides = [
        {"id": f"card-{index}", "role": "insights", "page_family": "cards"}
        for index in range(3)
    ]
    findings = inspect_design_quality(
        replace(result, compiled_deck={"slides": card_slides})
    )
    codes = {item.code for item in findings}
    assert "CARD_MONOCULTURE" in codes
    assert "CONCEPT_CONTENT_FIT_LOW" in codes


@pytest.mark.parametrize(
    ("semantic_form", "intent", "expected"),
    [
        ("line-chart", "trend", "line"),
        ("stacked-bar", "composition", "stacked-column"),
        ("composition-chart", "composition", "doughnut"),
        ("scatter-plot", "relationship", "scatter"),
        (None, "comparison", "column"),
    ],
)
def test_semantic_chart_form_controls_native_chart_type(
    semantic_form: str | None,
    intent: str,
    expected: str,
) -> None:
    assert semantic_form_chart_type(semantic_form, intent) == expected


def test_png_preview_checks_empty_dense_edge_and_duplicate(tmp_path: Path) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    image = Image.new("RGB", (320, 180), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 40, 160, 140), fill="black")
    image.save(first)
    image.save(second)
    findings = inspect_preview_images(
        (first, second), slide_ids=("slide-one", "slide-two")
    )
    codes = {item.code for item in findings}
    assert "FOREGROUND_TOUCHES_EDGE" in codes
    assert "ADJACENT_SLIDES_NEAR_DUPLICATE" in codes


def test_png_preview_edge_accent_does_not_invert_background_density(
    tmp_path: Path,
) -> None:
    preview = tmp_path / "accented-master.png"
    image = Image.new("RGB", (320, 180), "#F8FAFC")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 3, 179), fill="#0B3A67")
    draw.text((100, 80), "Key point", fill="#0B3A67")
    image.save(preview)

    findings = inspect_preview_images((preview,), slide_ids=("slide-one",))

    assert "PAGE_VISUALLY_DENSE" not in {item.code for item in findings}


def test_png_preview_ignores_thin_governed_edge_frame_and_ticks(
    tmp_path: Path,
) -> None:
    preview = tmp_path / "governed-edge-frame.png"
    image = Image.new("RGB", (320, 180), "#F8FAFC")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 3, 179), fill="#0B3A67")
    draw.rectangle((286, 0, 319, 1), fill="#0B3A67")
    draw.rectangle((306, 138, 319, 141), fill="#CBD5E1")
    draw.rectangle((296, 148, 319, 149), fill="#CBD5E1")
    draw.rectangle((80, 60, 240, 120), fill="#E2E8F0")
    image.save(preview)

    findings = inspect_preview_images((preview,), slide_ids=("slide-one",))

    assert "FOREGROUND_TOUCHES_EDGE" not in {item.code for item in findings}


def test_png_preview_keeps_edge_warning_for_real_text_content(
    tmp_path: Path,
) -> None:
    preview = tmp_path / "edge-text.png"
    image = Image.new("RGB", (320, 180), "white")
    draw = ImageDraw.Draw(image)
    draw.text((-1, 20), "EDGE CONTENT", fill="black", font=ImageFont.load_default())
    draw.rectangle((100, 90, 220, 140), fill="#CBD5E1")
    image.save(preview)

    findings = inspect_preview_images((preview,), slide_ids=("slide-one",))

    assert "FOREGROUND_TOUCHES_EDGE" in {item.code for item in findings}


def test_png_preview_missing_and_unreadable_are_hard_gates_when_expected(
    tmp_path: Path,
) -> None:
    unreadable = tmp_path / "broken.png"
    unreadable.write_text("not a PNG", encoding="utf-8")

    findings = inspect_preview_images(
        (unreadable,),
        slide_ids=("slide-one", "slide-two"),
        expected_slide_count=2,
    )

    by_code = {item.code: item for item in findings}
    assert by_code["PREVIEW_UNREADABLE"].severity == "hard-gate"
    assert by_code["PREVIEW_EXPORT_MISSING"].severity == "hard-gate"
    assert by_code["PREVIEW_EXPORT_MISSING"].slide_id == "slide-two"


def test_new_public_artifacts_validate_against_shipped_schemas() -> None:
    result = prepare_brief_generation(facts(), brief())
    schemas = REPO_ROOT / "skills" / "owned" / "window-pptx" / "schemas"
    payloads = {
        "fact-store.v1.schema.json": facts(),
        "brief-plan.v1.schema.json": brief(),
        "narrative-plan.v1.schema.json": result.compilation.narrative.to_dict(),
        "direction-decision.v1.schema.json": result.direction.to_dict(),
        "quality-report.v2.schema.json": build_quality_report_v2(
            list(generation_quality_findings(result)),
            transaction_status="test",
        ).to_dict(),
    }
    for name, payload in payloads.items():
        schema = json.loads((schemas / name).read_text(encoding="utf-8"))
        assert not list(jsonschema.Draft202012Validator(schema).iter_errors(payload)), name


def test_repair_log_v2_keeps_post_render_vectors_in_v2_semantics(
    tmp_path: Path,
) -> None:
    generation = prepare_brief_generation(facts(), brief())
    post_render = StageRepairPass(
        "post-render",
        (1, 2, 3, 4, 1234),
        (0, 1, 2, 3, 123),
        True,
        False,
        None,
    )

    artifacts = automation.write_brief_generation_artifacts(
        generation,
        tmp_path,
        (post_render,),
    )
    payload = json.loads(Path(artifacts["repair_log_v2"]).read_text(encoding="utf-8"))
    schema = json.loads(
        (
            REPO_ROOT
            / "skills"
            / "owned"
            / "window-pptx"
            / "schemas"
            / "repair-log.v2.schema.json"
        ).read_text(encoding="utf-8")
    )

    assert payload["passes"][-1]["before_vector"] == [1, 2, 3, 4, 1234]
    assert not list(jsonschema.Draft202012Validator(schema).iter_errors(payload))
