from __future__ import annotations

import binascii
import json
import struct
import sys
import zipfile
import zlib
from dataclasses import replace
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import window_pptx
import window_pptx_automation as automation
from window_pptx.assets import AssetRecord
from window_pptx.cli import build_dry_run_result, collect_requested_actions, parse_args
from window_pptx.deck_plan import DeckPlanValidationError
from window_pptx.errors import OutputPolicyError
from window_pptx.layouts import SlideSize
from window_pptx.models import CandidateResult, OutputPolicy, PowerPointHandle
from window_pptx.recording_com import RecordingPresentation
from window_pptx.render_plan import (
    AssetBinding,
    RenderPlanError,
    build_render_plan,
    inches_to_points,
    load_asset_bindings,
    validate_render_plan,
)
from window_pptx.renderer import PowerPointRenderer, RenderError
from window_pptx.runner import run_render_pipeline
from window_pptx.themes import BrandOverrides


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


def write_png(path: Path, width: int = 1200, height: int = 1000) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
        )

    rows = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, level=9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def asset_binding(
    path: Path,
    *,
    asset_id: str = "hero",
    width: int = 1200,
    height: int = 1000,
) -> AssetBinding:
    return AssetBinding(
        path=path,
        record=AssetRecord(
            id=asset_id,
            kind="photo",
            style="editorial",
            aspect_ratio=width / height,
            quality=90,
            source="https://example.test/asset",
            license="CC0",
            retrieved_at="2026-07-20",
            width_px=width,
            height_px=height,
        ),
    )


def write_asset_manifest(path: Path, image: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "bindings": {
                    "asset:hero": {
                        "path": image.name,
                        "record": {
                            "id": "hero",
                            "kind": "photo",
                            "style": "editorial",
                            "aspect_ratio": 1.2,
                            "quality": 90,
                            "source": "https://example.test/asset",
                            "license": "CC0",
                            "retrieved_at": "2026-07-20",
                            "width_px": 1200,
                            "height_px": 1000,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )


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
    write_png(image)

    with_asset = build_render_plan(
        image_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_bindings={"asset:hero": asset_binding(image)},
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
    fallback_visual = next(
        obj for obj in fallback.slides[0].objects if obj.component == "image-frame"
    )
    assert fallback_visual.text
    assert fallback_visual.text != "Visual asset unavailable"
    assert fallback.slides[0].title in fallback_visual.text

    readme = tmp_path / "README.md"
    readme.write_text("not an image", encoding="utf-8")
    unsafe = build_render_plan(
        image_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_bindings={"asset:hero": asset_binding(readme)},
    )
    assert not any(obj.kind == "image" for obj in unsafe.slides[0].objects)
    assert any(finding.code == "ASSET_POLICY_REJECTED" for finding in unsafe.findings)

    low_resolution = build_render_plan(
        image_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_bindings={
            "asset:hero": asset_binding(image, width=10, height=10)
        },
    )
    assert not any(obj.kind == "image" for obj in low_resolution.slides[0].objects)
    assert any(
        finding.code == "ASSET_POLICY_REJECTED"
        for finding in low_resolution.findings
    )

    forged_dimensions = tmp_path / "forged.png"
    write_png(forged_dimensions, width=100, height=100)
    forged = build_render_plan(
        image_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_bindings={"asset:hero": asset_binding(forged_dimensions)},
    )
    assert not any(obj.kind == "image" for obj in forged.slides[0].objects)
    assert any(
        "dimensions do not match" in finding.message
        for finding in forged.findings
    )


def test_governed_asset_manifest_loads_relative_paths_and_rejects_bad_schema(
    tmp_path: Path,
) -> None:
    image = tmp_path / "hero.png"
    write_png(image)
    manifest = tmp_path / "render-assets.json"
    write_asset_manifest(manifest, image)

    bindings = load_asset_bindings(manifest)

    assert bindings["asset:hero"].path == image.resolve()
    assert bindings["asset:hero"].record.license == "CC0"

    manifest.write_text('{"schema_version":"2.0","bindings":{}}', encoding="utf-8")
    with pytest.raises(RenderPlanError, match="schema_version"):
        load_asset_bindings(manifest)


def test_multiple_image_frames_consume_distinct_governed_assets(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    third = tmp_path / "third.png"
    for path in (first, second, third):
        write_png(path)
    payload = image_deck()
    payload["slides"].append(  # type: ignore[union-attr]
        {
            "id": "gallery",
            "role": "product-showcase",
            "title": "Product gallery",
            "importance": "high",
            "blocks": [
                {
                    "id": "gallery-one",
                    "kind": "image",
                    "source_ref": "asset:second",
                },
                {
                    "id": "gallery-two",
                    "kind": "image",
                    "source_ref": "asset:third",
                },
                {
                    "id": "gallery-unused",
                    "kind": "image",
                    "source_ref": "asset:unused",
                },
            ],
        }
    )

    plan = build_render_plan(
        payload,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_bindings={
            "asset:hero": asset_binding(first, asset_id="first"),
            "asset:second": asset_binding(second, asset_id="second"),
            "asset:third": asset_binding(third, asset_id="third"),
            "asset:unused": asset_binding(first, asset_id="unused"),
        },
    )

    gallery_images = [
        item.source_path
        for item in plan.slides[1].objects
        if item.kind == "image"
    ]
    assert gallery_images == [second.resolve(), third.resolve()]
    assert any(
        finding.code == "ASSET_SOURCE_UNUSED"
        and "asset:unused" in finding.message
        for finding in plan.findings
    )


def test_multi_image_layout_marks_missing_slot_as_native_fallback(
    tmp_path: Path,
) -> None:
    image = tmp_path / "only.png"
    write_png(image)
    payload = image_deck()
    payload["slides"].append(  # type: ignore[union-attr]
        {
            "id": "partial-gallery",
            "role": "product-showcase",
            "title": "Partial gallery",
            "importance": "high",
            "blocks": [
                {
                    "id": "partial-one",
                    "kind": "image",
                    "source_ref": "asset:only",
                    "items": ["one", "two"],
                }
            ],
        }
    )

    plan = build_render_plan(
        payload,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_bindings={
            "asset:hero": asset_binding(image),
            "asset:only": asset_binding(image, asset_id="only"),
        },
    )

    assert sum(item.kind == "image" for item in plan.slides[1].objects) == 1
    assert any(
        finding.code == "ASSET_NATIVE_FALLBACK"
        and "no asset reference" in finding.message
        for finding in plan.findings
    )


def test_renderer_creates_native_named_tagged_grouped_and_layered_objects(
    tmp_path: Path,
) -> None:
    image = tmp_path / "hero.png"
    write_png(image)
    plan = build_render_plan(
        image_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_bindings={"asset:hero": asset_binding(image)},
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
    assert any(shape.kind == "group" for shape in slide.Shapes.items)
    assert not any(shape.Name in report.object_names[:-1] for shape in slide.Shapes.items)
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


def test_renderer_replaces_template_slides_and_master_content_before_rendering() -> None:
    plan = build_render_plan(
        sample_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )
    presentation = RecordingPresentation(
        initial_slide_count=3,
        initial_master_shape_count=2,
    )

    report = PowerPointRenderer().render(plan, presentation)

    assert report.slide_count == 2
    assert len(presentation.Slides.items) == 2
    assert sum(call.operation == "delete-slide" for call in presentation.calls) == 3
    assert [slide.index for slide in presentation.Slides.items] == [1, 2]
    assert [shape.Name for shape in presentation.SlideMaster.Shapes.items] == [
        "wp_master_background"
    ]
    assert sum(call.operation == "delete-shape" for call in presentation.calls) == 2


@pytest.mark.parametrize(
    "operation",
    [
        "z-order",
        "shape-range",
        "group",
        "crop-cover",
        "delete-shape",
        "master-background",
    ],
)
def test_recording_com_injects_renderer_boundary_failures(
    tmp_path: Path, operation: str
) -> None:
    image = tmp_path / "hero.png"
    write_png(image)
    plan = build_render_plan(
        image_deck(),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_bindings={"asset:hero": asset_binding(image)},
    )

    with pytest.raises(RenderError):
        PowerPointRenderer().render(
            plan,
            RecordingPresentation(
                fail_operation=operation,
                initial_master_shape_count=(
                    1 if operation == "delete-shape" else 0
                ),
            ),
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda item: replace(item, x=-0.1), "geometry"),
        (lambda item: replace(item, width=0), "geometry"),
        (lambda item: replace(item, x=item.x + 0.01), "governed layout"),
        (lambda item: replace(item, font_size_pt=8), "font"),
        (lambda item: replace(item, font_size_pt=99), "governed theme"),
        (lambda item: replace(item, font_name="Comic Sans MS"), "governed theme"),
        (lambda item: replace(item, component="invented"), "component"),
        (lambda item: replace(item, fill_color="red"), "color"),
        (lambda item: replace(item, fill_color="#FF00FF"), "governed theme"),
        (lambda item: replace(item, kind="shape"), "governed component"),
        (lambda item: replace(item, layer=999), "governed component"),
        (lambda item: replace(item, group_id="model-group"), "governed component"),
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

    weakly_typed = replace(plan, slides=({"id": "not-a-slide"},))  # type: ignore[arg-type]
    with pytest.raises(RenderPlanError, match="render slide"):
        validate_render_plan(weakly_typed)

    invalid_brand = replace(
        plan,
        brand=BrandOverrides(primary=42),  # type: ignore[arg-type]
    )
    with pytest.raises(RenderPlanError, match="brand primary"):
        validate_render_plan(invalid_brand)


def test_powerpoint_slide_size_limits_are_enforced_before_com() -> None:
    with pytest.raises(RenderPlanError, match="between 1 and 56"):
        build_render_plan(
            sample_deck(),
            slide_size=SlideSize(57, 57),
            installed_fonts={"Arial"},
        )


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
    assert dry["would_write"] == [
        "project/.window-pptx/audits/quality-report.json",
        "project/.window-pptx/audits/repair-log.json",
        "project/output/final.pptx",
    ]

    with pytest.raises(SystemExit):
        parse_args(
            [
                "--project-dir",
                "project",
                "--deck-plan",
                "deck-plan.json",
                "--render-deck-plan",
                "--attach-existing",
            ]
        )
    with pytest.raises(SystemExit):
        parse_args(
            [
                "--project-dir",
                "project",
                "--deck-plan",
                "deck-plan.json",
                "--render-deck-plan",
                "--list-addins",
            ]
        )
    with pytest.raises(SystemExit):
        parse_args(
            [
                "--project-dir",
                "project",
                "--deck-plan",
                "deck-plan.json",
                "--render-deck-plan",
                "--slide-width-in",
                "57",
                "--slide-height-in",
                "57",
            ]
        )


def test_render_cli_preflights_plan_and_output_before_com(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid = tmp_path / "invalid.json"
    payload = sample_deck()
    payload["slides"][0]["blocks"][0]["x"] = 1  # type: ignore[index]
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    events: list[str] = []
    monkeypatch.setattr(
        automation, "require_windows", lambda: events.append("require_windows")
    )
    monkeypatch.setattr(
        automation,
        "dispatch_powerpoint",
        lambda *args: events.append("dispatch"),
    )

    with pytest.raises(DeckPlanValidationError):
        automation.main(
            [
                "--project-dir",
                str(tmp_path),
                "--deck-plan",
                invalid.name,
                "--render-deck-plan",
                "--no-output-deck",
            ],
            com_client=object(),
        )
    assert events == []

    valid = tmp_path / "valid.json"
    valid.write_text(json.dumps(sample_deck()), encoding="utf-8")
    with pytest.raises(OutputPolicyError):
        automation.main(
            [
                "--project-dir",
                str(tmp_path),
                "--deck-plan",
                valid.name,
                "--render-deck-plan",
                "--output",
                "bad.txt",
            ],
            com_client=object(),
        )
    assert events == []

    with pytest.raises(DeckPlanValidationError):
        automation.main(
            [
                "--project-dir",
                str(tmp_path),
                "--deck-plan",
                "missing.json",
                "--render-deck-plan",
                "--dry-run",
            ]
        )
    assert events == []


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
    template = tmp_path / "template.pptx"
    template.write_bytes(b"test template is opened by the injected fake")
    opened_templates: list[Path | None] = []
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
        lambda current_app, current_template, visible: (
            opened_templates.append(current_template) or presentation
        ),
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
            "--template",
            template.name,
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
    assert opened_templates == [template.resolve()]
    assert presentation.close_calls == 1


def test_render_cli_uses_ooxml_size_and_governed_asset_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan_path = tmp_path / "deck-plan.json"
    plan_path.write_text(json.dumps(image_deck()), encoding="utf-8")
    image = tmp_path / "hero.png"
    write_png(image)
    manifest = tmp_path / "render-assets.json"
    write_asset_manifest(manifest, image)
    template = tmp_path / "template.pptx"
    with zipfile.ZipFile(template, "w") as archive:
        archive.writestr(
            "ppt/presentation.xml",
            (
                '<p:presentation xmlns:p="http://schemas.openxmlformats.org/'
                'presentationml/2006/main"><p:sldSz cx="9144000" '
                'cy="6858000"/></p:presentation>'
            ),
        )
    presentation = RecordingPresentation(initial_slide_count=2)
    monkeypatch.setattr(automation, "require_windows", lambda: None)
    monkeypatch.setattr(
        automation,
        "dispatch_powerpoint",
        lambda attach_existing, client: PowerPointHandle(
            app=object(), owned=False, dispatch_mode="recording"
        ),
    )
    monkeypatch.setattr(
        automation,
        "open_or_create_presentation",
        lambda app, current_template, visible: presentation,
    )

    result = automation.main(
        [
            "--project-dir",
            str(tmp_path),
            "--deck-plan",
            plan_path.name,
            "--render-deck-plan",
            "--template",
            template.name,
            "--asset-manifest",
            manifest.name,
            "--no-output-deck",
            "--json",
        ],
        com_client=object(),
    )

    payload = json.loads(capsys.readouterr().out)["render_pipeline"]
    assert result == 0
    assert payload["render_plan"]["slide_size"] == {
        "width_in": 10.0,
        "height_in": 7.5,
    }
    assert any(
        item["kind"] == "image"
        for item in payload["render_plan"]["slides"][0]["objects"]
    )
    assert sum(call.operation == "delete-slide" for call in presentation.calls) == 2
    assert any(call.operation == "add-picture" for call in presentation.calls)
