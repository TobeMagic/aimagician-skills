from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import window_pptx.quality as quality_module  # noqa: E402
from window_pptx.layouts import SlideSize  # noqa: E402
from window_pptx.models import CandidateResult, OutputPolicy  # noqa: E402
from window_pptx.quality import (  # noqa: E402
    HARD_GATE_CODES,
    QUALITY_LAYERS,
    QualityReport,
    finalize_quality_report,
    inspect_quality,
    repair_quality,
    write_quality_artifacts,
)
from window_pptx.recording_com import RecordingPresentation  # noqa: E402
from window_pptx.render_plan import build_render_plan  # noqa: E402
from window_pptx.renderer import PowerPointRenderer  # noqa: E402
from window_pptx.runner import run_render_pipeline  # noqa: E402


def quality_deck(*, repeated: bool = False) -> dict[str, object]:
    slides: list[dict[str, object]] = [
        {
            "id": "trend",
            "role": "performance",
            "title": "Revenue trend",
            "importance": "high",
            "blocks": [
                {
                    "id": "trend-data",
                    "kind": "trend",
                    "items": [
                        {"category": "Q1", "series": "Revenue", "value": 12},
                        {"category": "Q2", "series": "Revenue", "value": 18},
                        {"category": "Q3", "series": "Revenue", "value": 27},
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
                    "id": "process-data",
                    "kind": "process",
                    "items": ["Discover", "Design", "Deliver"],
                }
            ],
        },
    ]
    if repeated:
        slides = [
            {
                "id": f"cards-{index}",
                "role": "insights",
                "title": f"Insights {index}",
                "importance": "normal",
                "blocks": [
                    {
                        "id": f"cards-data-{index}",
                        "kind": "bullets",
                        "items": ["One", "Two", "Three"],
                    }
                ],
            }
            for index in range(1, 4)
        ]
    return {
        "schema_version": "1.0",
        "project": {
            "title": "Quality deck",
            "scenario": "business-report",
            "audience": "executive",
        },
        "preferences": {"density": "balanced", "motion": "step-reveal"},
        "slides": slides,
    }


def render_quality_deck(
    *, repeated: bool = False
) -> tuple[object, RecordingPresentation, object]:
    plan = build_render_plan(
        quality_deck(repeated=repeated),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    presentation = RecordingPresentation()
    report = PowerPointRenderer().render(plan, presentation)
    return plan, presentation, report


def test_quality_and_repair_schemas_are_versioned_strict_and_accept_outputs() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    quality_schema = json.loads(
        (SKILL_ROOT / "schemas" / "quality-report.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    repair_schema = json.loads(
        (SKILL_ROOT / "schemas" / "repair-log.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    plan, presentation, render_report = render_quality_deck()
    report = inspect_quality(plan, render_report, presentation)
    repair = repair_quality(plan, render_report, presentation, report)

    assert quality_schema["properties"]["schema_version"]["const"] == "1.0"
    assert repair_schema["properties"]["schema_version"]["const"] == "1.0"
    assert not list(
        jsonschema.Draft202012Validator(quality_schema).iter_errors(report.to_dict())
    )
    assert not list(
        jsonschema.Draft202012Validator(repair_schema).iter_errors(repair.to_dict())
    )


def test_clean_candidate_emits_all_five_deterministic_layers() -> None:
    plan, presentation, render_report = render_quality_deck()

    first = inspect_quality(plan, render_report, presentation)
    second = inspect_quality(plan, render_report, presentation)

    assert first == second
    assert tuple(snapshot.layer for snapshot in first.layers) == QUALITY_LAYERS
    assert first.hard_gate_failures == ()
    assert first.passed is True
    assert not any(finding.repairable for finding in first.findings)
    assert first.to_dict() == second.to_dict()
    assert all(finding.code not in HARD_GATE_CODES for finding in first.findings)


def test_inspector_detects_com_geometry_font_tag_and_page_drift() -> None:
    plan, presentation, render_report = render_quality_deck()
    first_object = plan.slides[0].objects[0]
    shape = presentation.Slides.items[0].Shapes.Item(first_object.name)
    shape.Left += 12
    shape.TextFrame.TextRange.Font.Name = "Comic Sans MS"
    shape.Tags.values.pop("window-pptx:editable")
    presentation.PageSetup.SlideWidth += 20

    report = inspect_quality(plan, render_report, presentation)
    codes = {finding.code for finding in report.findings}

    assert {
        "PAGE_SIZE_MISMATCH",
        "COM_GEOMETRY_DRIFT",
        "FONT_DRIFT",
        "EDITABLE_TAG_MISSING",
    } <= codes
    assert "PAGE_SIZE_MISMATCH" in report.hard_gate_failures
    assert report.passed is False


def test_repair_is_candidate_only_bounded_and_monotonically_improves() -> None:
    plan, presentation, render_report = render_quality_deck()
    original_plan = plan.to_dict()
    first_object = plan.slides[0].objects[0]
    shape = presentation.Slides.items[0].Shapes.Item(first_object.name)
    shape.Left += 12
    shape.TextFrame.TextRange.Font.Name = "Comic Sans MS"
    shape.Tags.values.pop("window-pptx:editable")
    presentation.PageSetup.SlideWidth += 20
    before = inspect_quality(plan, render_report, presentation)

    repair = repair_quality(plan, render_report, presentation, before, max_passes=2)
    after = inspect_quality(plan, render_report, presentation)

    assert repair.changed is True
    assert 1 <= len(repair.passes) <= 2
    assert all(item.accepted for item in repair.passes)
    assert after.weighted_score < before.weighted_score
    assert not {
        "PAGE_SIZE_MISMATCH",
        "COM_GEOMETRY_DRIFT",
        "FONT_DRIFT",
        "EDITABLE_TAG_MISSING",
    } & {finding.code for finding in after.findings}
    assert plan.to_dict() == original_plan


def test_repair_keeps_name_change_last_for_compound_shape_repairs() -> None:
    plan, presentation, render_report = render_quality_deck()
    first_object = plan.slides[0].objects[0]
    shape = presentation.Slides.items[0].Shapes.Item(first_object.name)
    shape.Name = "drifted-name"
    shape.Left += 12
    shape.Tags.values.pop("window-pptx:editable")
    before = inspect_quality(plan, render_report, presentation)

    repair = repair_quality(plan, render_report, presentation, before)

    assert repair.changed is True
    assert repair.passes[0].failure_code is None
    repaired = presentation.Slides.items[0].Shapes.Item(first_object.name)
    assert repaired.Name == first_object.name
    assert repaired.Left == pytest.approx(first_object.x * 72)
    assert repaired.Tags.values["window-pptx:editable"] == "true"
    assert repair.final_report.hard_gate_failures == ()


def test_repair_rolls_back_a_non_monotonic_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, presentation, render_report = render_quality_deck()
    first_object = plan.slides[0].objects[0]
    shape = presentation.Slides.items[0].Shapes.Item(first_object.name)
    shape.Left += 12
    drifted_left = shape.Left
    before = inspect_quality(plan, render_report, presentation)
    original_width = presentation.PageSetup.SlideWidth

    original_executor = quality_module._apply_repair_action

    def worsening_executor(*args: object, **kwargs: object) -> None:
        original_executor(*args, **kwargs)
        presentation.PageSetup.SlideWidth = 1

    monkeypatch.setattr(quality_module, "_apply_repair_action", worsening_executor)
    repair = repair_quality(plan, render_report, presentation, before, max_passes=2)

    assert len(repair.passes) == 1
    assert repair.passes[0].accepted is False
    assert repair.passes[0].rolled_back is True
    assert repair.changed is False
    assert presentation.PageSetup.SlideWidth == original_width
    assert presentation.Slides.items[0].Shapes.Item(first_object.name).Left == drifted_left


def test_repair_rolls_back_when_a_com_action_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, presentation, render_report = render_quality_deck()
    first_object = plan.slides[0].objects[0]
    shape = presentation.Slides.items[0].Shapes.Item(first_object.name)
    shape.Left += 12
    drifted_left = shape.Left
    before = inspect_quality(plan, render_report, presentation)

    def failing_executor(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated COM write failure")

    monkeypatch.setattr(quality_module, "_apply_repair_action", failing_executor)
    repair = repair_quality(plan, render_report, presentation, before)

    assert repair.changed is False
    assert len(repair.passes) == 1
    assert repair.passes[0].accepted is False
    assert repair.passes[0].rolled_back is True
    assert repair.passes[0].failure_code == "REPAIR_ACTION_FAILED"
    assert presentation.Slides.items[0].Shapes.Item(first_object.name).Left == drifted_left
    assert "COM_GEOMETRY_DRIFT" in repair.final_report.hard_gate_failures


def test_missing_native_object_and_low_editable_coverage_are_hard_gates() -> None:
    plan, presentation, render_report = render_quality_deck()
    chart = next(item for item in plan.slides[0].objects if item.kind == "chart")
    presentation.Slides.items[0].Shapes.Item(chart.name).Delete()

    report = inspect_quality(plan, render_report, presentation)

    assert "NATIVE_OBJECT_MISSING" in report.hard_gate_failures
    assert "EDITABLE_COVERAGE_LOW" in report.hard_gate_failures
    assert report.passed is False


def test_deck_layer_reports_excessive_family_repetition() -> None:
    plan, presentation, render_report = render_quality_deck(repeated=True)

    report = inspect_quality(plan, render_report, presentation)

    assert any(
        finding.code == "DECK_FAMILY_REPETITION" for finding in report.findings
    )
    deck_snapshot = next(item for item in report.layers if item.layer == "deck")
    assert deck_snapshot.metrics_dict()["max_family_run"] == 3


def test_transaction_finalization_enforces_package_and_source_hard_gates() -> None:
    plan, presentation, render_report = render_quality_deck()
    preliminary = inspect_quality(plan, render_report, presentation)
    policy = OutputPolicy(source_path=Path("source.pptx"), output_path=Path("final.pptx"))
    invalid = CandidateResult(
        output_path=Path("final.pptx"),
        promoted=True,
        candidate_path=None,
        source_hash_before="before",
        source_hash_after="after",
        validation_steps=("save-copy",),
        cleanup_errors=(),
    )

    failed = finalize_quality_report(preliminary, invalid, policy, export_pdf=False)
    assert {"PACKAGE_VALIDATION_MISSING", "SOURCE_INTEGRITY_FAILURE"} <= set(
        failed.hard_gate_failures
    )
    assert failed.passed is False

    valid = CandidateResult(
        output_path=Path("final.pptx"),
        promoted=True,
        candidate_path=None,
        source_hash_before="same",
        source_hash_after="same",
        validation_steps=(
            "save-copy",
            "ooxml-package",
            "macro-disabled-reopen",
            "validation-copy-closed",
            "atomic-promote",
        ),
        cleanup_errors=(),
    )
    passed = finalize_quality_report(preliminary, valid, policy, export_pdf=False)
    assert passed.hard_gate_failures == ()
    assert passed.passed is True
    assert next(item for item in passed.layers if item.layer == "package").status == "pass"


def test_default_runner_serializes_quality_report_and_repair_log() -> None:
    presentation = RecordingPresentation()

    def saver(
        current: object,
        app: object,
        policy: OutputPolicy,
        **kwargs: object,
    ) -> CandidateResult:
        return CandidateResult(
            output_path=policy.output_path or Path(),
            promoted=False,
            candidate_path=None,
            source_hash_before=None,
            source_hash_after=None,
            validation_steps=(),
            cleanup_errors=(),
        )

    result = run_render_pipeline(
        quality_deck(),
        presentation=presentation,
        app=object(),
        output_policy=OutputPolicy(
            source_path=None,
            output_path=None,
            no_output_deck=True,
        ),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        saver=saver,
    )
    payload = result.to_dict()

    assert isinstance(result.inspection, QualityReport)
    assert payload["inspection"]["schema_version"] == "1.0"
    assert payload["repair"]["schema_version"] == "1.0"
    assert payload["inspection"]["transaction_status"] == "skipped"


def test_chart_table_and_diagram_data_fidelity_are_hard_gates() -> None:
    payload = quality_deck()
    payload["slides"].append(  # type: ignore[union-attr]
        {
            "id": "table",
            "role": "insights",
            "title": "Plan versus actual",
            "importance": "normal",
            "blocks": [
                {
                    "id": "table-data",
                    "kind": "table",
                    "items": [
                        {"label": "Revenue", "actual": 27, "target": 25},
                        {"label": "Margin", "actual": "42%", "target": "40%"},
                    ],
                }
            ],
        }
    )
    plan = build_render_plan(
        payload,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    presentation = RecordingPresentation()
    render_report = PowerPointRenderer().render(plan, presentation)
    chart_item = next(item for item in plan.slides[0].objects if item.kind == "chart")
    chart_shape = presentation.Slides.items[0].Shapes.Item(chart_item.name)
    chart_shape.Chart.spec = None
    chart_shape.Chart.SeriesCollection = lambda: type("Series", (), {"Count": 99})()

    diagram_item = next(
        item for item in plan.slides[1].objects if item.kind == "diagram"
    )
    diagram_shape = presentation.Slides.items[1].Shapes.Item(diagram_item.name)
    diagram_shape.GroupItems = tuple(
        child for child in diagram_shape.GroupItems if "__node_03" not in child.Name
    )

    table_item = next(item for item in plan.slides[2].objects if item.kind == "table")
    table_shape = presentation.Slides.items[2].Shapes.Item(table_item.name)
    table_shape.Table.Cell(2, 1).Shape.TextFrame.TextRange.Text = "Invented"
    table_shape.Table.Cell(2, 1).Shape.TextFrame.TextRange.Font.Size = 8

    report = inspect_quality(plan, render_report, presentation)

    assert {
        "CHART_DATA_MISMATCH",
        "DIAGRAM_NODE_MISMATCH",
        "TABLE_DATA_MISMATCH",
        "TABLE_LABELS_UNREADABLE",
    } <= set(report.hard_gate_failures)


def test_real_com_chart_fidelity_fails_closed_on_value_or_category_drift() -> None:
    plan, presentation, render_report = render_quality_deck()
    chart_item = next(item for item in plan.slides[0].objects if item.kind == "chart")
    chart_shape = presentation.Slides.items[0].Shapes.Item(chart_item.name)
    chart_shape.Chart.spec = None

    series = SimpleNamespace(
        Name="Revenue",
        Values=(12.0, 99.0, 27.0),
        XValues=("Q1", "Q2", "Q3"),
    )

    class SeriesCollection:
        Count = 1

        def __call__(self, index: int) -> object:
            return series

    chart_shape.Chart.SeriesCollection = lambda: SeriesCollection()

    report = inspect_quality(plan, render_report, presentation)

    assert "CHART_DATA_MISMATCH" in report.hard_gate_failures


def test_native_table_dimensions_and_diagram_labels_are_verified() -> None:
    payload = quality_deck()
    payload["slides"].append(  # type: ignore[union-attr]
        {
            "id": "table",
            "role": "insights",
            "title": "Plan versus actual",
            "importance": "normal",
            "blocks": [
                {
                    "id": "table-data",
                    "kind": "table",
                    "items": [{"label": "Revenue", "actual": 27, "target": 25}],
                }
            ],
        }
    )
    plan = build_render_plan(
        payload,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    presentation = RecordingPresentation()
    render_report = PowerPointRenderer().render(plan, presentation)
    diagram = next(item for item in plan.slides[1].objects if item.kind == "diagram")
    diagram_shape = presentation.Slides.items[1].Shapes.Item(diagram.name)
    diagram_node = next(
        child for child in diagram_shape.GroupItems if "__node_01" in child.Name
    )
    diagram_node.TextFrame.TextRange.Text = "Invented label"
    table = next(item for item in plan.slides[2].objects if item.kind == "table")
    table_shape = presentation.Slides.items[2].Shapes.Item(table.name)
    table_shape.Table.columns += 1

    report = inspect_quality(plan, render_report, presentation)

    assert {"TABLE_DATA_MISMATCH", "DIAGRAM_NODE_MISMATCH"} <= set(
        report.hard_gate_failures
    )


def test_visual_layer_reports_text_density_and_overflow() -> None:
    plan, presentation, render_report = render_quality_deck()
    text_item = plan.slides[0].objects[0]
    shape = presentation.Slides.items[0].Shapes.Item(text_item.name)
    shape.TextFrame.TextRange.Text = "Dense content " * 500

    report = inspect_quality(plan, render_report, presentation)
    codes = {finding.code for finding in report.findings}

    assert "TEXT_CONTENT_MISMATCH" in report.hard_gate_failures
    assert "TEXT_OVERFLOW_RISK" in codes
    assert "PAGE_TEXT_DENSITY_HIGH" in codes
    visual = next(item for item in report.layers if item.layer == "visual")
    assert float(visual.metrics_dict()["max_text_utilization"]) > 0.85


def test_customer_delivery_hard_gates_cover_bounds_placeholders_and_com_overflow() -> None:
    plan, presentation, render_report = render_quality_deck()
    text_item = plan.slides[0].objects[0]
    shape = presentation.Slides.items[0].Shapes.Item(text_item.name)
    shape.Left = presentation.PageSetup.SlideWidth - shape.Width + 10
    shape.TextFrame.TextRange.Text = "Placeholder"
    shape.TextFrame2 = SimpleNamespace(
        TextRange=SimpleNamespace(BoundHeight=shape.Height + 20)
    )

    report = inspect_quality(plan, render_report, presentation)

    assert {
        "OBJECT_OUT_OF_BOUNDS",
        "PLACEHOLDER_CONTENT",
        "TEXT_OVERFLOW_RISK",
    } <= set(report.hard_gate_failures)
    assert report.passed is False


def test_default_runner_blocks_hard_gates_before_saver(tmp_path: Path) -> None:
    class CorruptingRenderer(PowerPointRenderer):
        def render(self, plan: object, presentation: object) -> object:
            report = super().render(plan, presentation)  # type: ignore[arg-type]
            chart = next(
                item for item in plan.slides[0].objects if item.kind == "chart"  # type: ignore[union-attr]
            )
            presentation.Slides.items[0].Shapes.Item(chart.name).Delete()  # type: ignore[union-attr]
            return report

    saves: list[str] = []

    def saver(*args: object, **kwargs: object) -> CandidateResult:
        saves.append("save")
        raise AssertionError("hard-gate candidate must not reach saver")

    with pytest.raises(
        quality_module.QualityGateError, match="NATIVE_OBJECT_MISSING"
    ) as captured:
        run_render_pipeline(
            quality_deck(),
            presentation=RecordingPresentation(),
            app=object(),
            output_policy=OutputPolicy(
                source_path=None,
                output_path=None,
                no_output_deck=True,
            ),
            slide_size=SlideSize(13.333, 7.5),
            installed_fonts={"Arial"},
            renderer=CorruptingRenderer(),
            saver=saver,
            audit_dir=tmp_path / "audits",
        )

    assert saves == []
    assert captured.value.report is not None
    assert captured.value.repair is not None
    assert json.loads(
        Path(captured.value.artifacts["quality_report"]).read_text(encoding="utf-8")
    )["passed"] is False


def test_default_runner_blocks_failed_transaction_evidence_after_save(
    tmp_path: Path,
) -> None:
    invalid = CandidateResult(
        output_path=tmp_path / "final.pptx",
        promoted=True,
        candidate_path=None,
        source_hash_before="same",
        source_hash_after="same",
        validation_steps=("save-copy",),
        cleanup_errors=(),
    )

    def saver(*args: object, **kwargs: object) -> CandidateResult:
        return invalid

    with pytest.raises(
        quality_module.QualityGateError, match="PACKAGE_VALIDATION_MISSING"
    ) as captured:
        run_render_pipeline(
            quality_deck(),
            presentation=RecordingPresentation(),
            app=object(),
            output_policy=OutputPolicy(
                source_path=None,
                output_path=tmp_path / "final.pptx",
            ),
            slide_size=SlideSize(13.333, 7.5),
            installed_fonts={"Arial"},
            saver=saver,
            audit_dir=tmp_path / "audits",
        )

    assert captured.value.candidate_result == invalid
    assert captured.value.report is not None
    assert captured.value.report.transaction_status == "failed"
    assert Path(captured.value.artifacts["repair_log"]).is_file()


def test_quality_artifacts_are_written_atomically_and_validate(
    tmp_path: Path,
) -> None:
    plan, presentation, render_report = render_quality_deck()
    report = inspect_quality(plan, render_report, presentation)
    repair = repair_quality(plan, render_report, presentation, report)

    outputs = write_quality_artifacts(report, repair, tmp_path / "audits")

    assert json.loads(Path(outputs["quality_report"]).read_text(encoding="utf-8")) == report.to_dict()
    assert json.loads(Path(outputs["repair_log"]).read_text(encoding="utf-8")) == repair.to_dict()
    assert not list((tmp_path / "audits").glob("*.tmp"))
