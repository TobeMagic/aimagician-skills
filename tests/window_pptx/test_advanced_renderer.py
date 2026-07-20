from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.deck_plan import (  # noqa: E402
    DeckPlanValidationError,
    compile_deck_plan,
    validate_deck_plan,
)
import window_pptx_automation as automation  # noqa: E402
from window_pptx.cli import build_dry_run_result, parse_args  # noqa: E402
from window_pptx.layouts import SlideSize  # noqa: E402
from window_pptx.recording_com import RecordingPresentation  # noqa: E402
from window_pptx.render_plan import (  # noqa: E402
    ChartSpec,
    DiagramSpec,
    RenderPlanError,
    TableSpec,
    build_render_plan,
    validate_render_plan,
)
from window_pptx.renderer import PowerPointRenderer  # noqa: E402
from window_pptx.renderer import RenderError  # noqa: E402
from window_pptx.models import OutputPolicy  # noqa: E402
from window_pptx.runner import run_render_pipeline  # noqa: E402


def advanced_deck(*, motion: str = "off") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "project": {
            "title": "Operating model",
            "scenario": "business-report",
            "audience": "executive",
            "language": "en-US",
        },
        "preferences": {"density": "balanced", "motion": motion},
        "slides": [
            {
                "id": "trend",
                "role": "performance",
                "title": "Revenue trend",
                "importance": "high",
                "speaker_notes": "Explain the inflection after the second quarter.",
                "blocks": [
                    {
                        "id": "revenue",
                        "kind": "trend",
                        "chart_intent": "trend",
                        "hyperlink": "https://example.test/evidence",
                        "items": [
                            {"category": "Q1", "series": "Revenue", "value": 12},
                            {"category": "Q2", "series": "Revenue", "value": 18},
                            {"category": "Q3", "series": "Revenue", "value": 27},
                        ],
                    }
                ],
            },
            {
                "id": "comparison",
                "role": "insights",
                "title": "Plan versus actual",
                "importance": "normal",
                "blocks": [
                    {
                        "id": "comparison-table",
                        "kind": "table",
                        "hyperlink": "slide:process",
                        "items": [
                            {"label": "Revenue", "actual": 27, "target": 25},
                            {"label": "Margin", "actual": "42%", "target": "40%"},
                        ],
                    }
                ],
            },
            {
                "id": "process",
                "role": "next-steps",
                "title": "Delivery process",
                "importance": "normal",
                "blocks": [
                    {
                        "id": "delivery-process",
                        "kind": "sequence",
                        "items": ["Discover", "Design", "Deliver"],
                    }
                ],
            },
        ],
    }


def test_advanced_semantics_are_versioned_and_survive_compilation() -> None:
    payload = advanced_deck(motion="subtle-fade")
    schema = json.loads(
        (SKILL_ROOT / "schemas" / "deck-plan.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema = pytest.importorskip("jsonschema")

    assert not list(jsonschema.Draft202012Validator(schema).iter_errors(payload))
    validated = validate_deck_plan(payload)
    compiled = compile_deck_plan(validated)

    assert validated.preferences_dict()["motion"] == "subtle-fade"
    assert validated.slides[0].speaker_notes.startswith("Explain")
    assert validated.slides[0].blocks[0].hyperlink == "https://example.test/evidence"
    assert compiled["slides"][0]["speaker_notes"].startswith("Explain")
    assert compiled["slides"][1]["blocks"][0]["hyperlink"] == "slide:process"


@pytest.mark.parametrize(
    "target",
    [
        "javascript:alert(1)",
        "file:///c:/secret.txt",
        "data:text/html,bad",
        "slide:missing",
        "https://example.test/has space",
    ],
)
def test_unsafe_or_unresolved_hyperlinks_are_rejected(target: str) -> None:
    payload = advanced_deck()
    payload["slides"][0]["blocks"][0]["hyperlink"] = target  # type: ignore[index]

    with pytest.raises(DeckPlanValidationError, match="hyperlink"):
        validate_deck_plan(payload)


def test_motion_is_off_by_default_and_only_governed_presets_are_accepted() -> None:
    payload = advanced_deck()
    payload["preferences"] = {"density": "balanced"}
    assert validate_deck_plan(payload).preferences_dict().get("motion", "off") == "off"

    payload["preferences"] = {"motion": "fly-in-from-random-side"}
    with pytest.raises(DeckPlanValidationError, match="motion"):
        validate_deck_plan(payload)


def test_render_plan_contains_exact_native_advanced_specs() -> None:
    plan = build_render_plan(
        advanced_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )

    chart = next(
        item for item in plan.slides[0].objects if isinstance(item.advanced, ChartSpec)
    )
    table = next(
        item for item in plan.slides[1].objects if isinstance(item.advanced, TableSpec)
    )
    diagram = next(
        item for item in plan.slides[2].objects if isinstance(item.advanced, DiagramSpec)
    )

    assert chart.kind == "chart"
    assert chart.text is None
    assert chart.advanced.chart_type == "line"
    assert chart.advanced.categories == ("Q1", "Q2", "Q3")
    assert chart.advanced.series[0].name == "Revenue"
    assert chart.advanced.series[0].values == (12.0, 18.0, 27.0)
    assert chart.hyperlink == "https://example.test/evidence"
    assert table.kind == "table"
    assert table.advanced.columns == ("Label", "Actual", "Target")
    assert table.advanced.rows == (
        ("Revenue", "27", "25"),
        ("Margin", "42%", "40%"),
    )
    assert table.hyperlink == "slide:process"
    assert diagram.kind == "diagram"
    assert diagram.advanced.diagram_type == "process"
    assert tuple(node.label for node in diagram.advanced.nodes) == (
        "Discover",
        "Design",
        "Deliver",
    )
    assert plan.slides[0].speaker_notes.startswith("Explain")
    assert plan.slides[0].motion == "off"
    assert not any(
        finding.code == "DEFERRED_ADVANCED_COMPONENT" for finding in plan.findings
    )


def test_public_advanced_specs_are_rederived_before_com_mutation() -> None:
    plan = build_render_plan(
        advanced_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    slide = plan.slides[0]
    index = next(
        index
        for index, item in enumerate(slide.objects)
        if isinstance(item.advanced, ChartSpec)
    )
    original = slide.objects[index]
    assert isinstance(original.advanced, ChartSpec)
    forged = replace(
        original,
        advanced=replace(original.advanced, categories=("invented",)),
    )
    objects = list(slide.objects)
    objects[index] = forged
    broken = replace(plan, slides=(replace(slide, objects=tuple(objects)), *plan.slides[1:]))
    presentation = RecordingPresentation()

    with pytest.raises(RenderPlanError, match="advanced semantics"):
        PowerPointRenderer().render(broken, presentation)

    assert presentation.calls == []


def test_renderer_creates_native_chart_table_diagram_notes_links_and_opt_in_motion() -> None:
    plan = build_render_plan(
        advanced_deck(motion="step-reveal"),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    presentation = RecordingPresentation()

    report = PowerPointRenderer().render(plan, presentation)

    operations = [call.operation for call in presentation.calls]
    assert report.native_editable_count == sum(len(slide.objects) for slide in plan.slides)
    assert "add-chart" in operations
    assert "set-chart-data" in operations
    assert "add-table" in operations
    assert "set-table-cell" in operations
    assert "add-diagram-node" in operations
    assert "set-speaker-notes" in operations
    assert operations.count("add-hyperlink") == 2
    assert "add-motion-effect" in operations
    assert all(shape.editable for slide in presentation.Slides.items for shape in slide.Shapes.items)
    assert presentation.Slides.items[0].notes_text.startswith("Explain")
    native_chart = presentation.Slides.items[0].Shapes.Item(
        next(item.name for item in plan.slides[0].objects if item.kind == "chart")
    )
    native_table = presentation.Slides.items[1].Shapes.Item(
        next(item.name for item in plan.slides[1].objects if item.kind == "table")
    )
    assert native_chart.Chart.spec.categories == ("Q1", "Q2", "Q3")
    assert native_table.Table.Cell(2, 1).Shape.TextFrame.TextRange.Text == "Revenue"
    assert native_chart.ActionSettings(1).Hyperlink.Address == "https://example.test/evidence"
    assert native_table.ActionSettings(1).Hyperlink.SubAddress.startswith("258,3,")


def test_advanced_renderer_is_deterministic() -> None:
    plan = build_render_plan(
        advanced_deck(motion="subtle-fade"),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    first = RecordingPresentation()
    second = RecordingPresentation()

    PowerPointRenderer().render(plan, first)
    PowerPointRenderer().render(plan, second)

    assert first.calls == second.calls
    assert validate_render_plan(plan) is plan


@pytest.mark.parametrize(
    "diagram_type",
    ["process", "timeline", "matrix", "quadrant", "funnel", "roadmap"],
)
def test_all_governed_diagram_families_compile_to_native_specs(
    diagram_type: str,
) -> None:
    payload = advanced_deck()
    payload["slides"] = [  # type: ignore[index]
        {
            "id": diagram_type,
            "role": "insights",
            "title": f"{diagram_type.title()} view",
            "importance": "normal",
            "blocks": [
                {
                    "id": f"{diagram_type}-data",
                    "kind": diagram_type,
                    "items": ["One", "Two", "Three", "Four"],
                }
            ],
        }
    ]

    plan = build_render_plan(
        payload,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    diagrams = [
        item.advanced
        for item in plan.slides[0].objects
        if isinstance(item.advanced, DiagramSpec)
    ]

    assert diagrams
    assert all(diagram.diagram_type == diagram_type for diagram in diagrams)
    assert sum(len(diagram.nodes) for diagram in diagrams) == 4


def test_render_route_allows_ratio_aware_png_exports_after_render(
    tmp_path: Path,
) -> None:
    args = parse_args(
        [
            "--project-dir",
            str(tmp_path),
            "--deck-plan",
            "deck-plan.json",
            "--render-deck-plan",
            "--export-qa",
            "--dry-run",
        ]
    )
    dry_run = build_dry_run_result(args, tmp_path)
    assert dry_run["would_run"] == ["render_deck_plan", "export_qa"]
    assert str(tmp_path / ".window-pptx" / "exports" / "qa") in dry_run["would_write"]

    plan = build_render_plan(
        advanced_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    presentation = RecordingPresentation()
    PowerPointRenderer().render(plan, presentation)
    result = automation.export_all_slides_to_png(presentation, tmp_path / "png")
    export_calls = [
        call for call in presentation.calls if call.operation == "export-slide"
    ]

    assert len(export_calls) == 3
    assert [call.arguments[-2:] for call in export_calls] == [(1600, 900)] * 3
    assert result["files"] == [
        str(tmp_path / "png" / f"slide-{index}.png") for index in range(1, 4)
    ]


@pytest.mark.parametrize(
    "operation",
    [
        "add-chart",
        "set-chart-data",
        "add-table",
        "set-table-cell",
        "add-diagram-node",
        "set-speaker-notes",
        "add-hyperlink",
        "add-motion-effect",
    ],
)
def test_advanced_com_failures_never_reach_candidate_save(operation: str) -> None:
    presentation = RecordingPresentation(fail_operation=operation)
    saves: list[str] = []

    def saver(*args: object, **kwargs: object) -> object:
        saves.append("save")
        raise AssertionError("advanced render failure must stop before save")

    with pytest.raises(RenderError):
        run_render_pipeline(
            advanced_deck(motion="step-reveal"),
            presentation=presentation,
            app=object(),
            output_policy=OutputPolicy(
                source_path=None,
                output_path=None,
                no_output_deck=True,
            ),
            slide_size=SlideSize(13.333, 7.5),
            installed_fonts={"Arial"},
            saver=saver,  # type: ignore[arg-type]
        )

    assert saves == []


def test_chart_missing_values_are_native_gaps_not_invented_zeroes() -> None:
    payload = advanced_deck()
    payload["slides"] = [  # type: ignore[index]
        {
            "id": "series-gap",
            "role": "performance",
            "title": "Series gap",
            "importance": "normal",
            "blocks": [
                {
                    "id": "series-gap-data",
                    "kind": "trend",
                    "items": [
                        {"category": "Q1", "series": "A", "value": 10},
                        {"category": "Q2", "series": "A", "value": 12},
                        {"category": "Q1", "series": "B", "value": 8},
                    ],
                }
            ],
        }
    ]
    plan = build_render_plan(
        payload,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    chart_object = next(item for item in plan.slides[0].objects if item.kind == "chart")
    assert isinstance(chart_object.advanced, ChartSpec)
    assert chart_object.advanced.series[1].values == (8.0, None)

    presentation = RecordingPresentation()
    PowerPointRenderer().render(plan, presentation)
    content_group = presentation.Slides.items[0].Shapes.Item("wp_s001_content")
    native_chart = next(
        shape for shape in content_group.GroupItems if shape.Name == chart_object.name
    )
    assert native_chart.Chart.DisplayBlanksAs == 1


def test_multi_node_diagram_hyperlink_is_applied_to_editable_children() -> None:
    payload = advanced_deck(motion="step-reveal")
    payload["slides"][2]["blocks"][0]["hyperlink"] = "https://example.test/process"  # type: ignore[index]
    plan = build_render_plan(
        payload,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    presentation = RecordingPresentation()
    PowerPointRenderer().render(plan, presentation)

    diagram_name = next(
        item.name for item in plan.slides[2].objects if item.kind == "diagram"
    )
    diagram = presentation.Slides.items[2].Shapes.Item(diagram_name)
    diagram_nodes = [
        child for child in diagram.GroupItems if "__node_" in child.Name
    ]
    assert len(diagram_nodes) == 3
    assert all(
        child.ActionSettings(1).Hyperlink.Address
        == "https://example.test/process"
        for child in diagram.GroupItems
    )
