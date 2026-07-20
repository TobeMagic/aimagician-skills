from __future__ import annotations

import sys
import json
from dataclasses import replace
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import window_pptx
import window_pptx_automation as automation
from window_pptx.cli import build_dry_run_result, collect_requested_actions, parse_args
from window_pptx.deck_plan import DeckPlanValidationError
from window_pptx.errors import OutputPolicyError
from window_pptx.layouts import SlideSize
from window_pptx.models import CandidateResult, OutputPolicy, PowerPointHandle
from window_pptx.recording_com import RecordingPresentation
from window_pptx.render_plan import (
    RenderPlanError,
    build_render_plan,
    inches_to_points,
    validate_render_plan,
)
from window_pptx.renderer import PowerPointRenderer, RenderError
from window_pptx.runner import run_render_pipeline


def sample_deck() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "project": {
            "title": "Quarterly Growth Review",
            "scenario": "business-report",
            "audience": "executive",
            "language": "en-US",
        },
        "preferences": {"density": "balanced", "tone": "professional"},
        "slides": [
            {
                "id": "growth",
                "role": "performance",
                "title": "Growth accelerated",
                "importance": "high",
                "blocks": [
                    {
                        "id": "growth-kpis",
                        "kind": "metrics",
                        "items": [
                            {"label": "Revenue", "value": 42, "unit": "%"},
                            {"label": "Retention", "value": 96, "unit": "%"},
                            {"label": "NPS", "value": 61},
                        ],
                    }
                ],
            },
            {
                "id": "priorities",
                "role": "next-steps",
                "title": "Three priorities",
                "importance": "normal",
                "blocks": [
                    {
                        "id": "priority-list",
                        "kind": "bullets",
                        "items": ["Expand enterprise", "Improve onboarding", "Ship AI copilot"],
                    }
                ],
            },
        ],
    }


def image_deck() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "project": {
            "title": "Product Launch",
            "scenario": "product-launch",
            "audience": "customer",
        },
        "slides": [
            {
                "id": "hero",
                "role": "product-showcase",
                "title": "Meet the product",
                "importance": "critical",
                "blocks": [
                    {
                        "id": "hero-image",
                        "kind": "image",
                        "title": "Product hero",
                        "source_ref": "asset:hero",
                    }
                ],
            }
        ],
    }


def test_render_plan_is_deterministic_governed_and_serializable() -> None:
    first = build_render_plan(
        sample_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    second = build_render_plan(
        sample_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )

    assert first == second
    assert first.schema_version == "1.0"
    assert first.theme_id == "executive-light"
    assert [slide.source_id for slide in first.slides] == ["growth", "priorities"]
    assert all(slide.layout_id for slide in first.slides)
    assert all(slide.objects for slide in first.slides)
    assert all(obj.native_editable for slide in first.slides for obj in slide.objects)
    names = [obj.name for slide in first.slides for obj in slide.objects]
    assert len(names) == len(set(names))
    assert all(name.startswith("wp_s") for name in names)
    assert first.to_dict() == second.to_dict()


def test_core_renderer_is_exposed_from_the_public_package() -> None:
    assert window_pptx.build_render_plan is build_render_plan
    assert window_pptx.PowerPointRenderer is PowerPointRenderer
    assert window_pptx.RecordingPresentation is RecordingPresentation
    assert window_pptx.run_render_pipeline is run_render_pipeline


@pytest.mark.parametrize(
    "size",
    [
        SlideSize(13.333, 7.5),
        SlideSize(10.0, 7.5),
        SlideSize(7.5, 13.333),
        SlideSize(12.0, 6.0),
    ],
)
def test_render_plan_preserves_absolute_safe_geometry_across_sizes(
    size: SlideSize,
) -> None:
    plan = build_render_plan(
        sample_deck(), slide_size=size, installed_fonts={"Arial"}
    )

    assert plan.slide_size == size
    for slide in plan.slides:
        for obj in slide.objects:
            assert obj.x >= 0
            assert obj.y >= 0
            assert obj.width > 0
            assert obj.height > 0
            assert obj.x + obj.width <= size.width + 1e-6
            assert obj.y + obj.height <= size.height + 1e-6
            if obj.component != "footer":
                assert obj.x >= 0.5 - 1e-6
                assert obj.y >= 0.4 - 1e-6
                assert obj.x + obj.width <= size.width - 0.5 + 1e-6
                assert obj.y + obj.height <= size.height - 0.4 + 1e-6
            if obj.text:
                assert obj.font_size_pt >= 11


def test_inches_to_points_is_the_only_geometry_unit_conversion() -> None:
    assert inches_to_points(1) == 72
    assert inches_to_points(0.5) == 36
    with pytest.raises(RenderPlanError, match="finite and non-negative"):
        inches_to_points(float("nan"))
    with pytest.raises(RenderPlanError, match="finite and non-negative"):
        inches_to_points(-1)


def test_render_plan_uses_trusted_asset_mapping_or_native_fallback(
    tmp_path: Path,
) -> None:
    image = tmp_path / "hero.png"
    image.write_bytes(b"recording-fake-image")

    with_asset = build_render_plan(
        image_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_paths={"asset:hero": image},
    )
    image_objects = [
        obj for obj in with_asset.slides[0].objects if obj.kind == "image"
    ]
    assert len(image_objects) == 1
    assert image_objects[0].source_path == image.resolve()

    fallback = build_render_plan(
        image_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    assert not any(obj.kind == "image" for obj in fallback.slides[0].objects)
    assert any(
        finding.code == "ASSET_NATIVE_FALLBACK" for finding in fallback.findings
    )


def test_renderer_creates_native_named_tagged_grouped_and_layered_objects(
    tmp_path: Path,
) -> None:
    image = tmp_path / "hero.png"
    image.write_bytes(b"recording-fake-image")
    plan = build_render_plan(
        image_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_paths={"asset:hero": image},
    )
    presentation = RecordingPresentation()

    report = PowerPointRenderer().render(plan, presentation)

    assert presentation.PageSetup.SlideWidth == pytest.approx(13.333 * 72)
    assert presentation.PageSetup.SlideHeight == pytest.approx(7.5 * 72)
    assert report.slide_count == 1
    assert report.native_editable_count == len(plan.slides[0].objects)
    assert report.object_names == tuple(
        obj.name for obj in plan.slides[0].objects
    )
    assert presentation.SlideMaster.Shapes.items
    slide = presentation.Slides.items[0]
    assert all(shape.Name for shape in slide.Shapes.items)
    assert all(shape.Tags.values["window-pptx:id"] for shape in slide.Shapes.items)
    assert any(call.operation == "group" for call in presentation.calls)
    assert any(call.operation == "z-order" for call in presentation.calls)
    assert any(call.operation == "crop-cover" for call in presentation.calls)
    assert all(shape.editable for shape in slide.Shapes.items)


def test_renderer_call_log_is_identical_across_repeated_runs() -> None:
    plan = build_render_plan(
        sample_deck(),
        slide_size=SlideSize(10.0, 7.5),
        installed_fonts={"Arial"},
    )
    first = RecordingPresentation()
    second = RecordingPresentation()

    PowerPointRenderer().render(plan, first)
    PowerPointRenderer().render(plan, second)

    assert first.calls == second.calls


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda item: replace(item, x=-0.1), "geometry"),
        (lambda item: replace(item, width=0), "geometry"),
        (lambda item: replace(item, font_size_pt=8), "font"),
        (lambda item: replace(item, component="invented"), "component"),
        (lambda item: replace(item, fill_color="red"), "color"),
        (lambda item: replace(item, native_editable=False), "editable"),
    ],
)
def test_public_render_plan_is_revalidated_before_any_com_mutation(
    mutation: object, message: str
) -> None:
    plan = build_render_plan(
        sample_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    first_slide = plan.slides[0]
    first_object = first_slide.objects[0]
    broken_object = mutation(first_object)  # type: ignore[operator]
    broken_slide = replace(
        first_slide, objects=(broken_object, *first_slide.objects[1:])
    )
    broken_plan = replace(plan, slides=(broken_slide, *plan.slides[1:]))
    presentation = RecordingPresentation()

    with pytest.raises(RenderPlanError, match=message):
        PowerPointRenderer().render(broken_plan, presentation)

    assert presentation.calls == []


def test_render_plan_validator_rejects_duplicate_names_and_unknown_layout() -> None:
    plan = build_render_plan(
        sample_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    slide = plan.slides[0]
    duplicate = replace(slide.objects[1], name=slide.objects[0].name)
    duplicate_plan = replace(
        plan,
        slides=(
            replace(slide, objects=(slide.objects[0], duplicate, *slide.objects[2:])),
            *plan.slides[1:],
        ),
    )
    with pytest.raises(RenderPlanError, match="duplicate object name"):
        validate_render_plan(duplicate_plan)

    unknown_layout = replace(
        plan, slides=(replace(slide, layout_id="rogue.layout"), *plan.slides[1:])
    )
    with pytest.raises(RenderPlanError, match="layout"):
        validate_render_plan(unknown_layout)


def test_render_errors_include_slide_and_object_context() -> None:
    plan = build_render_plan(
        sample_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    presentation = RecordingPresentation(fail_operation="add-textbox")

    with pytest.raises(RenderError, match=r"slide growth.*wp_s001"):
        PowerPointRenderer().render(plan, presentation)


def test_pipeline_orders_compile_render_hooks_and_transactional_save() -> None:
    presentation = RecordingPresentation()
    events: list[str] = []

    def inspect(plan: object, render_report: object) -> dict[str, bool]:
        events.append("inspect")
        return {"ok": True}

    def repair(plan: object, inspection: object) -> dict[str, bool]:
        events.append("repair")
        return {"changed": False}

    def saver(
        current: object,
        app: object,
        policy: OutputPolicy,
        **kwargs: object,
    ) -> CandidateResult:
        events.append("save")
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
        sample_deck(),
        presentation=presentation,
        app=object(),
        output_policy=OutputPolicy(
            source_path=None,
            output_path=None,
            dry_run=False,
            no_output_deck=True,
        ),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        inspector=inspect,
        repairer=repair,
        saver=saver,
    )

    assert result.stages == (
        "validate-compile",
        "build-render-plan",
        "render",
        "inspect",
        "repair",
        "transactional-save",
    )
    assert events == ["inspect", "repair", "save"]
    assert result.candidate_result.promoted is False


def test_pipeline_dry_run_builds_plan_without_com_or_save_mutation() -> None:
    presentation = RecordingPresentation()
    saves: list[str] = []

    def saver(*args: object, **kwargs: object) -> CandidateResult:
        saves.append("save")
        raise AssertionError("dry-run must not call saver")

    result = run_render_pipeline(
        sample_deck(),
        presentation=presentation,
        app=object(),
        output_policy=OutputPolicy(
            source_path=None,
            output_path=None,
            dry_run=True,
            no_output_deck=True,
        ),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        saver=saver,
    )

    assert result.stages == ("validate-compile", "build-render-plan", "dry-run")
    assert result.render_report is None
    assert result.candidate_result is None
    assert presentation.calls == []
    assert saves == []


def test_pipeline_rejects_raw_design_before_any_com_mutation() -> None:
    payload = sample_deck()
    payload["slides"][0]["blocks"][0]["x"] = 1  # type: ignore[index]
    presentation = RecordingPresentation()

    with pytest.raises(DeckPlanValidationError, match="forbidden"):
        run_render_pipeline(
            payload,
            presentation=presentation,
            app=object(),
            output_policy=OutputPolicy(
                source_path=None,
                output_path=None,
                dry_run=True,
                no_output_deck=True,
            ),
            slide_size=SlideSize(13.333, 7.5),
            installed_fonts={"Arial"},
        )

    assert presentation.calls == []


def test_pipeline_rejects_unsafe_output_before_any_com_mutation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pptx"
    presentation = RecordingPresentation()

    with pytest.raises(OutputPolicyError, match="same-path"):
        run_render_pipeline(
            sample_deck(),
            presentation=presentation,
            app=object(),
            output_policy=OutputPolicy(
                source_path=source,
                output_path=source,
                allow_overwrite=True,
            ),
            slide_size=SlideSize(13.333, 7.5),
            installed_fonts={"Arial"},
        )

    assert presentation.calls == []


def test_cli_exposes_explicit_compile_and_render_routes() -> None:
    compile_args = parse_args(
        [
            "--project-dir",
            "project",
            "--deck-plan",
            "deck-plan.json",
            "--compile-deck-plan",
            "--no-output-deck",
        ]
    )
    render_args = parse_args(
        [
            "--project-dir",
            "project",
            "--deck-plan",
            "deck-plan.json",
            "--render-deck-plan",
            "--theme-id",
            "executive-light",
            "--slide-width-in",
            "10",
            "--slide-height-in",
            "7.5",
        ]
    )

    assert collect_requested_actions(compile_args) == ["compile_deck_plan"]
    assert collect_requested_actions(render_args) == ["render_deck_plan"]
    dry = build_dry_run_result(
        parse_args(
            [
                "--project-dir",
                "project",
                "--deck-plan",
                "deck-plan.json",
                "--render-deck-plan",
                "--dry-run",
            ]
        ),
        "project",
    )
    assert dry["would_run"] == ["render_deck_plan"]
    assert dry["would_write"] == ["project/output/final.pptx"]


def test_compile_cli_route_is_cross_platform_and_does_not_start_com(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan_path = tmp_path / "deck-plan.json"
    plan_path.write_text(json.dumps(sample_deck()), encoding="utf-8")
    monkeypatch.setattr(
        automation,
        "require_windows",
        lambda: (_ for _ in ()).throw(AssertionError("compile route started COM")),
    )

    result = automation.main(
        [
            "--project-dir",
            str(tmp_path),
            "--deck-plan",
            plan_path.name,
            "--compile-deck-plan",
            "--no-output-deck",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["compiled_deck"]["compiler_version"] == (
        "window-pptx-semantic-1.0"
    )
    assert len(payload["compiled_deck"]["slides"]) == 2


def test_render_cli_route_uses_governed_pipeline_and_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan_path = tmp_path / "deck-plan.json"
    plan_path.write_text(json.dumps(sample_deck()), encoding="utf-8")
    presentation = RecordingPresentation()
    app = object()
    monkeypatch.setattr(automation, "require_windows", lambda: None)
    monkeypatch.setattr(
        automation,
        "dispatch_powerpoint",
        lambda attach_existing, client: PowerPointHandle(
            app=app,
            owned=False,
            dispatch_mode="recording",
        ),
    )
    monkeypatch.setattr(
        automation,
        "open_or_create_presentation",
        lambda current_app, template, visible: presentation,
    )

    result = automation.main(
        [
            "--project-dir",
            str(tmp_path),
            "--deck-plan",
            plan_path.name,
            "--render-deck-plan",
            "--installed-font",
            "Arial",
            "--no-output-deck",
            "--json",
        ],
        com_client=object(),
    )

    payload = json.loads(capsys.readouterr().out)["render_pipeline"]
    assert result == 0
    assert payload["stages"] == [
        "validate-compile",
        "build-render-plan",
        "render",
        "inspect",
        "repair",
        "transactional-save",
    ]
    assert payload["render_report"]["slide_count"] == 2
    assert payload["candidate_result"]["promoted"] is False
    assert presentation.close_calls == 1
