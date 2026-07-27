from __future__ import annotations

import json
import shutil
import sys
import zipfile
import re
import types
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.backends import (  # noqa: E402
    CapabilityError,
    backend_capabilities,
    negotiate_backend,
)
from window_pptx.assets import AssetRecord  # noqa: E402
from window_pptx.cli import build_dry_run_result, parse_args  # noqa: E402
from window_pptx.com_diagnostics import (  # noqa: E402
    InterfaceTypeLibRegistration,
    classify_interface_registration,
)
import window_pptx.com_diagnostics as com_diagnostics  # noqa: E402
import window_pptx.libreoffice as libreoffice_module  # noqa: E402
from window_pptx.html_proof import render_html_proof  # noqa: E402
from window_pptx.layouts import SlideSize  # noqa: E402
from window_pptx.libreoffice import (  # noqa: E402
    LibreOfficeVerificationError,
    LibreOfficeVerifier,
)
from window_pptx.models import OutputPolicy  # noqa: E402
from window_pptx.ooxml import (  # noqa: E402
    OoxmlSemanticError,
    inspect_rendered_pptx,
    normalize_pptx_package,
)
from window_pptx.portable_renderer import PptxGenJSRenderer  # noqa: E402
from window_pptx.portable_runner import execute_portable_render_plan  # noqa: E402
import window_pptx.portable_runner as portable_runner_module  # noqa: E402
from window_pptx.preview_quality import inspect_render_plan_delivery  # noqa: E402
from window_pptx.render_plan import AssetBinding, build_render_plan  # noqa: E402
from window_pptx.render_plan import ChartSpec  # noqa: E402
from window_pptx.transaction import TransactionError, sha256_file  # noqa: E402
import window_pptx_automation as automation  # noqa: E402


def portable_deck(*, motion: str = "off") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "project": {
            "title": "Portable engine",
            "scenario": "business-report",
            "audience": "executive",
            "language": "zh-CN",
        },
        "preferences": {"density": "balanced", "motion": motion},
        "slides": [
            {
                "id": "trend",
                "role": "performance",
                "title": "收入趋势",
                "speaker_notes": "说明第三季度增长的原因。",
                "blocks": [
                    {
                        "id": "revenue",
                        "kind": "trend",
                        "chart_intent": "trend",
                        "hyperlink": "https://example.test/evidence",
                        "items": [
                            {"category": "Q1", "series": "收入", "value": 12},
                            {"category": "Q2", "series": "收入", "value": 18},
                            {"category": "Q3", "series": "收入", "value": 27},
                        ],
                    }
                ],
            },
            {
                "id": "comparison",
                "role": "insights",
                "title": "计划与实际",
                "blocks": [
                    {
                        "id": "comparison-table",
                        "kind": "table",
                        "hyperlink": "slide:process",
                        "items": [
                            {"label": "收入", "actual": 27, "target": 25},
                            {"label": "毛利率", "actual": "42%", "target": "40%"},
                        ],
                    }
                ],
            },
            {
                "id": "process",
                "role": "next-steps",
                "title": "交付流程",
                "blocks": [
                    {
                        "id": "delivery-process",
                        "kind": "sequence",
                        "items": ["发现", "设计", "交付"],
                    }
                ],
            },
        ],
    }


def build_portable_plan(*, motion: str = "off"):
    return build_render_plan(
        portable_deck(motion=motion),
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )


def build_percent_chart_plan():
    return build_render_plan(
        {
            "schema_version": "1.0",
            "project": {
                "title": "Percent chart contract",
                "scenario": "data-analysis",
                "audience": "executive",
                "language": "en-US",
            },
            "preferences": {"density": "balanced", "motion": "off"},
            "slides": [
                {
                    "id": "conversion",
                    "role": "analysis",
                    "title": "Conversion trend",
                    "blocks": [
                        {
                            "id": "conversion-data",
                            "kind": "trend",
                            "chart_intent": "trend",
                            "items": [
                                {
                                    "category": "Q3",
                                    "series": "Conversion",
                                    "value": 81,
                                    "unit": "percent",
                                },
                                {
                                    "category": "Q1",
                                    "series": "Conversion",
                                    "value": 59,
                                    "unit": "percent",
                                },
                                {
                                    "category": "Q2",
                                    "series": "Conversion",
                                    "value": 72,
                                    "unit": "percent",
                                },
                            ],
                        }
                    ],
                }
            ],
        },
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )


def build_rich_metric_plan():
    return build_render_plan(
        {
            "schema_version": "1.0",
            "project": {
                "title": "Metric hierarchy",
                "scenario": "business-report",
                "audience": "executive",
                "language": "en-US",
            },
            "preferences": {"density": "balanced", "motion": "off"},
            "slides": [
                {
                    "id": "metric",
                    "role": "performance",
                    "title": "Q2 revenue was 48.2 million dollars.",
                    "blocks": [
                        {
                            "id": "metric-values",
                            "kind": "metrics",
                            "items": [
                                {
                                    "label": "Revenue",
                                    "value": 48.2,
                                    "unit": "million dollars",
                                    "category": "Q2",
                                },
                                {"label": "Change", "value": 12, "unit": "percent"},
                            ],
                        }
                    ],
                }
            ],
        },
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )


def build_image_plan(image: Path):
    return build_render_plan(
        {
            "schema_version": "1.0",
            "project": {
                "title": "Portable image",
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
        },
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        asset_bindings={
            "asset:hero": AssetBinding(
                image,
                AssetRecord(
                    id="hero",
                    kind="vector" if image.suffix.casefold() == ".svg" else "photo",
                    style="editorial",
                    aspect_ratio=1.2,
                    quality=90,
                    source="https://example.test/asset",
                    license="CC0",
                    retrieved_at="2026-07-21",
                    width_px=1200,
                    height_px=1000,
                ),
            )
        },
    )


def build_chart_variant_plan():
    distribution_slides = [
        {
            "id": f"distribution-{index}",
            "role": "analysis",
            "title": f"Distribution view {index}",
            "blocks": [
                {
                    "id": f"distribution-data-{index}",
                    "kind": "generic",
                    "chart_intent": "distribution",
                    "items": [
                        {"label": "A", "value": 10 + index},
                        {"label": "B", "value": 20 + index},
                        {"label": "C", "value": 15 + index},
                    ],
                }
            ],
        }
        for index in range(1, 4)
    ]
    return build_render_plan(
        {
            "schema_version": "1.0",
            "project": {
                "title": "Portable chart variants",
                "scenario": "data-analysis",
                "audience": "executive",
            },
            "slides": [
                {
                    "id": "line",
                    "role": "analysis",
                    "title": "Trend",
                    "blocks": [
                        {
                            "id": "line-data",
                            "kind": "trend",
                            "chart_intent": "trend",
                            "items": [
                                {"category": "Q1", "series": "Value", "value": 10},
                                {"category": "Q2", "series": "Value", "value": 15},
                                {"category": "Q3", "series": "Value", "value": 22},
                            ],
                        }
                    ],
                },
                *distribution_slides,
                {
                    "id": "doughnut",
                    "role": "analysis",
                    "title": "Composition",
                    "blocks": [
                        {
                            "id": "composition-data",
                            "kind": "composition",
                            "chart_intent": "composition",
                            "items": [
                                {"label": "Core", "series": "Share", "value": 62},
                                {"label": "Growth", "series": "Share", "value": 25},
                                {"label": "Other", "series": "Share", "value": 13},
                            ],
                        }
                    ],
                },
                {
                    "id": "stacked",
                    "role": "analysis",
                    "title": "Composition by segment",
                    "blocks": [
                        {
                            "id": "stacked-data",
                            "kind": "composition",
                            "chart_intent": "composition",
                            "items": [
                                {"label": "A", "series": "Plan", "value": 40},
                                {"label": "B", "series": "Plan", "value": 60},
                                {"label": "A", "series": "Actual", "value": 55},
                                {"label": "B", "series": "Actual", "value": 45},
                            ],
                        }
                    ],
                },
                {
                    "id": "scatter",
                    "role": "analysis",
                    "title": "Relationship",
                    "blocks": [
                        {
                            "id": "scatter-data",
                            "kind": "generic",
                            "chart_intent": "relationship",
                            "items": [
                                {"label": "A", "primary": 1, "secondary": 3},
                                {"label": "B", "primary": 2, "secondary": 6},
                                {"label": "C", "primary": 4, "secondary": 8},
                            ],
                        }
                    ],
                },
            ],
        },
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )


@pytest.fixture(scope="module")
def rendered_portable_fixture(
    tmp_path_factory: pytest.TempPathFactory,
):
    plan = build_portable_plan()
    output = tmp_path_factory.mktemp("portable-ooxml-negative") / "base.pptx"
    PptxGenJSRenderer(skill_root=SKILL_ROOT).render(plan, output)
    normalize_pptx_package(output)
    return plan, output


def _mutated_copy(
    source: Path,
    output: Path,
    mutate,
) -> Path:
    with zipfile.ZipFile(source) as archive:
        parts = [(name, archive.read(name)) for name in archive.namelist()]
    rewritten = mutate(dict(parts))
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts:
            archive.writestr(name, rewritten.get(name, payload))
    return output


def test_portable_backend_capabilities_and_auto_selection() -> None:
    capabilities = backend_capabilities("pptxgenjs")

    assert capabilities.native_text is True
    assert capabilities.native_chart is True
    assert capabilities.shape_animation is False
    assert capabilities.headless_render is True
    assert negotiate_backend("auto", build_portable_plan()).backend_id == "pptxgenjs"


def test_portable_delivery_inspector_blocks_truncated_and_duplicate_text() -> None:
    plan = build_portable_plan()
    slide = plan.slides[0]
    title_index = next(
        index for index, item in enumerate(slide.objects) if item.component == "title"
    )
    body_index = next(
        index for index, item in enumerate(slide.objects) if item.component == "body-text"
    )
    objects = list(slide.objects)
    objects[title_index] = replace(objects[title_index], text="Complete claims matter…")
    objects[body_index] = replace(objects[body_index], text="Complete claims matter…")
    slides = list(plan.slides)
    slides[0] = replace(slide, objects=tuple(objects))

    findings = inspect_render_plan_delivery(replace(plan, slides=tuple(slides)))
    codes = {finding.code for finding in findings}

    assert {"TITLE_TRUNCATED", "DUPLICATE_SLIDE_TEXT"} <= codes
    assert all(
        finding.severity == "hard-gate"
        for finding in findings
        if finding.code in {"TITLE_TRUNCATED", "DUPLICATE_SLIDE_TEXT"}
    )


def test_portable_backend_rejects_required_motion_before_render() -> None:
    plan = build_portable_plan(motion="subtle-fade")

    with pytest.raises(CapabilityError, match="shape_animation"):
        negotiate_backend("pptxgenjs", plan)


@pytest.mark.parametrize(
    ("output_name", "capability"),
    (("deck.pptm", "macro_enabled_output"), ("deck.potx", "powerpoint_template_output")),
)
def test_portable_backend_rejects_nonportable_output_formats_before_render(
    tmp_path: Path,
    output_name: str,
    capability: str,
) -> None:
    with pytest.raises(CapabilityError, match=capability):
        negotiate_backend(
            "auto",
            build_portable_plan(),
            output_path=tmp_path / output_name,
        )
    assert not tuple(tmp_path.iterdir())


def test_portable_backend_rejects_physical_template_import_before_render(
    tmp_path: Path,
) -> None:
    with pytest.raises(CapabilityError, match="physical_template_import"):
        negotiate_backend(
            "auto",
            build_portable_plan(),
            require_physical_template=True,
        )
    assert not tuple(tmp_path.iterdir())


def test_cli_rejects_powerpoint_certification_on_the_legacy_com_backend() -> None:
    with pytest.raises(SystemExit):
        parse_args(
            [
                "--project-dir",
                "project",
                "--render-deck-plan",
                "--deck-plan",
                "deck.json",
                "--backend",
                "com",
                "--verification",
                "powerpoint",
            ]
        )

    with pytest.raises(SystemExit):
        parse_args(
            [
                "--project-dir",
                "project",
                "--render-deck-plan",
                "--deck-plan",
                "deck.json",
                "--backend",
                "com",
                "--verification",
                "portable",
            ]
        )

    with pytest.raises(SystemExit):
        parse_args(
            [
                "--project-dir",
                "project",
                "--certify-pptx",
                "delivery.pptx",
            ]
        )


def test_optional_html_proof_can_be_disabled_in_dry_run() -> None:
    args = parse_args(
        [
            "--project-dir",
            "project",
            "--render-deck-plan",
            "--deck-plan",
            "deck.json",
            "--no-html-proof",
            "--dry-run",
        ]
    )
    result = build_dry_run_result(args, "project")
    assert not any(path.endswith("render-proof.html") for path in result["would_write"])


def test_html_proof_is_renderplan_derived_and_deterministic() -> None:
    plan = build_portable_plan()

    first = render_html_proof(plan)
    second = render_html_proof(plan)

    assert first == second
    assert "window-pptx RenderPlan HTML proof" in first
    assert "data-window-pptx-id" in first
    assert "<script" not in first


def test_com_doctor_classifies_stale_wps_typelib_without_registry_mutation(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "WPS Office" / "wppapi.dll"
    registration = InterfaceTypeLibRegistration(
        "{91493442-5A91-11CF-8700-00AA0060263B}",
        "{44720440-94BF-4940-926D-4F38FECF2A48}",
        "3.0",
        missing,
        "64-bit",
    )

    findings = classify_interface_registration(registration)

    assert {item.code for item in findings} == {
        "POWERPOINT_INTERFACE_TYPELIB_MISMATCH",
        "STALE_WPS_TYPELIB_REGISTRATION",
        "TYPELIB_FILE_MISSING",
        "TYPE_E_CANTLOADLIBRARY_ROOT_CAUSE",
    }


def test_powerpoint_certifier_uses_owned_late_bound_read_only_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = tmp_path / "portable.pptx"
    candidate.write_bytes(b"portable candidate remains unchanged")
    before = sha256_file(candidate)
    runtime = {"running": False}
    opened_path: list[Path] = []

    class FakeSlide:
        def Export(self, path: str, kind: str) -> None:
            assert kind == "PNG"
            Path(path).write_bytes(b"\x89PNG\r\n\x1a\nproof")

    class FakeSlides:
        Count = 1

        def Item(self, index: int) -> FakeSlide:
            assert index == 1
            return FakeSlide()

    class FakePresentation:
        Slides = FakeSlides()

        def ExportAsFixedFormat(self, path: str, *_args: object) -> None:
            Path(path).write_bytes(b"%PDF-1.7\nproof")

        def Close(self) -> None:
            pass

    class FakePresentations:
        def Open(self, path: str, read_only: int, untitled: int, with_window: int):
            opened = Path(path)
            assert opened != candidate
            assert opened.name == "candidate-copy.pptx"
            assert sha256_file(opened) == before
            opened_path.append(opened)
            assert (read_only, untitled, with_window) == (-1, 0, 0)
            return FakePresentation()

    class FakeApplication:
        AutomationSecurity = 1
        HWND = 101
        Version = "16.0"
        Presentations = FakePresentations()

        def Quit(self) -> None:
            runtime["running"] = False

    app = FakeApplication()
    pythoncom = types.ModuleType("pythoncom")
    pythoncom.CLSCTX_LOCAL_SERVER = 4
    pythoncom.IID_IDispatch = object()
    def co_create(*_args: object) -> object:
        runtime["running"] = True
        return object()

    pythoncom.CoCreateInstance = co_create
    dynamic = types.SimpleNamespace(Dispatch=lambda _raw: app)
    win32com = types.ModuleType("win32com")
    win32com_client = types.ModuleType("win32com.client")
    win32com_client.dynamic = dynamic
    monkeypatch.setitem(sys.modules, "pythoncom", pythoncom)
    monkeypatch.setitem(sys.modules, "win32com", win32com)
    monkeypatch.setitem(sys.modules, "win32com.client", win32com_client)
    monkeypatch.setattr(com_diagnostics.platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        com_diagnostics,
        "_powerpoint_pids",
        lambda: {4242} if runtime["running"] else set(),
    )
    monkeypatch.setattr(
        com_diagnostics,
        "_pid_for_powerpoint_window",
        lambda hwnd: 4242 if hwnd == 101 else 0,
    )

    result = com_diagnostics.certify_powerpoint(
        candidate,
        artifact_dir=tmp_path / "certification",
    )

    assert result.owned_pid == 4242
    assert result.powerpoint_version == "16.0"
    assert result.candidate_hash_before == before == result.candidate_hash_after
    assert opened_path and not opened_path[0].exists()
    assert app.AutomationSecurity == 1
    assert runtime["running"] is False


def test_powerpoint_certifier_fails_closed_with_preexisting_user_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = tmp_path / "portable.pptx"
    candidate.write_bytes(b"candidate")
    monkeypatch.setattr(com_diagnostics.platform, "system", lambda: "Windows")
    monkeypatch.setattr(com_diagnostics, "_powerpoint_pids", lambda: {99})

    with pytest.raises(
        com_diagnostics.PowerPointCertificationError,
        match="user PowerPoint process already exists",
    ):
        com_diagnostics.certify_powerpoint(
            candidate,
            artifact_dir=tmp_path / "must-not-exist",
        )

    assert not (tmp_path / "must-not-exist").exists()


def test_pptxgenjs_output_is_native_semantic_and_deterministic(tmp_path: Path) -> None:
    plan = build_portable_plan()
    renderer = PptxGenJSRenderer(skill_root=SKILL_ROOT)
    first = tmp_path / "first.pptx"
    second = tmp_path / "second.pptx"

    first_report = renderer.render(plan, first)
    second_report = renderer.render(plan, second)
    normalize_pptx_package(first)
    normalize_pptx_package(second)

    assert first_report.backend_id == "pptxgenjs"
    assert first_report.native_editable_count >= sum(
        len(slide.objects) for slide in plan.slides
    )
    assert sha256_file(first) == sha256_file(second)
    semantic = inspect_rendered_pptx(first, plan)
    assert semantic.slide_count == len(plan.slides)
    assert semantic.object_ids == tuple(
        item.id for slide in plan.slides for item in slide.objects
    )
    assert semantic.notes_count == 1
    assert semantic.hyperlink_count == 2
    assert semantic.chart_count >= 1
    assert semantic.table_count >= 1
    assert semantic.diagram_count >= 1


def test_rich_metric_runs_are_native_deterministic_and_exactly_inspected(
    tmp_path: Path,
) -> None:
    plan = build_rich_metric_plan()
    renderer = PptxGenJSRenderer(skill_root=SKILL_ROOT)
    first = tmp_path / "rich-first.pptx"
    second = tmp_path / "rich-second.pptx"

    first_report = renderer.render(plan, first)
    second_report = renderer.render(plan, second)
    normalize_pptx_package(first)
    normalize_pptx_package(second)

    rich_objects = [
        item
        for slide in plan.slides
        for item in slide.objects
        if item.text_runs is not None
    ]
    assert len(rich_objects) == 2
    assert first_report.planned_object_count == second_report.planned_object_count
    assert first_report.native_editable_count == first_report.planned_object_count
    assert sha256_file(first) == sha256_file(second)
    assert inspect_rendered_pptx(first, plan).object_ids == tuple(
        item.id for slide in plan.slides for item in slide.objects
    )

    target = rich_objects[0]

    def mutate(parts: dict[str, bytes]) -> dict[str, bytes]:
        slide_name = "ppt/slides/slide1.xml"
        root = ET.fromstring(parts[slide_name])
        namespaces = {
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
        }
        for shape in root.findall(".//p:sp", namespaces):
            identity = shape.find("./p:nvSpPr/p:cNvPr", namespaces)
            if identity is None or identity.attrib.get("name") != target.name:
                continue
            properties = shape.find(".//a:r/a:rPr", namespaces)
            assert properties is not None
            properties.set("sz", "1900")
            parts[slide_name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            return parts
        raise AssertionError("rich text target was not found")

    corrupted = _mutated_copy(first, tmp_path / "rich-style-drift.pptx", mutate)
    with pytest.raises(OoxmlSemanticError, match="OBJECT_FONT_SIZE_MISMATCH"):
        inspect_rendered_pptx(corrupted, plan)


def test_pptxgenjs_chart_variants_preserve_exact_native_series(
    tmp_path: Path,
) -> None:
    plan = build_chart_variant_plan()
    chart_types = {
        item.advanced.chart_type
        for slide in plan.slides
        for item in slide.objects
        if item.kind == "chart" and isinstance(item.advanced, ChartSpec)
    }
    assert chart_types == {
        "line",
        "column",
        "bar",
        "doughnut",
        "stacked-column",
        "scatter",
    }
    output = tmp_path / "chart-variants.pptx"

    PptxGenJSRenderer(skill_root=SKILL_ROOT).render(plan, output)
    normalize_pptx_package(output)
    semantic = inspect_rendered_pptx(output, plan)

    assert semantic.chart_count == sum(
        item.kind == "chart" for slide in plan.slides for item in slide.objects
    )


def test_pptxgenjs_percent_chart_has_governed_axis_and_label_formats(
    tmp_path: Path,
) -> None:
    plan = build_percent_chart_plan()
    chart = next(
        item
        for item in plan.slides[0].objects
        if item.kind == "chart" and isinstance(item.advanced, ChartSpec)
    )
    assert chart.advanced.value_unit == "percent"
    assert chart.advanced.categories == ("Q3", "Q1", "Q2")
    output = tmp_path / "percent-chart.pptx"

    PptxGenJSRenderer(skill_root=SKILL_ROOT).render(plan, output)
    normalize_pptx_package(output)
    assert inspect_rendered_pptx(output, plan).chart_count == 1

    with zipfile.ZipFile(output) as package:
        chart_parts = sorted(
            name
            for name in package.namelist()
            if name.startswith("ppt/charts/chart") and name.endswith(".xml")
        )
        assert chart_parts == ["ppt/charts/chart1.xml"]
        root = ET.fromstring(package.read(chart_parts[0]))

    namespaces = {
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    }
    value_axis = root.find(".//c:valAx", namespaces)
    assert value_axis is not None
    assert value_axis.find("c:scaling/c:min", namespaces).attrib["val"] == "0"
    assert value_axis.find("c:scaling/c:max", namespaces).attrib["val"] == "100"
    assert value_axis.find("c:majorUnit", namespaces).attrib["val"] == "20"
    assert value_axis.find("c:numFmt", namespaces).attrib["formatCode"] == '0"%"'
    label_format = root.find(".//c:dLbls/c:numFmt", namespaces)
    assert label_format is not None
    assert label_format.attrib["formatCode"] == '0"%"'
    axis_title = " ".join(
        node.text or "" for node in value_axis.findall("c:title//a:t", namespaces)
    ).strip()
    assert axis_title == "Percent"


@pytest.mark.skipif(
    shutil.which("soffice") is None or shutil.which("pdftoppm") is None,
    reason="LibreOffice and Poppler are required for chart compatibility proof",
)
def test_libreoffice_renders_every_supported_native_chart_variant(
    tmp_path: Path,
) -> None:
    plan = build_chart_variant_plan()
    output = tmp_path / "chart-variants.pptx"
    PptxGenJSRenderer(skill_root=SKILL_ROOT).render(plan, output)
    normalize_pptx_package(output)

    proof = LibreOfficeVerifier(timeout_seconds=120).verify(
        output,
        artifact_dir=tmp_path / "chart-proof",
        expected_slide_count=len(plan.slides),
        slide_size=plan.slide_size,
    )

    assert proof.page_count == len(plan.slides)
    assert len(proof.png_paths) == len(plan.slides)
    assert proof.candidate_hash_before == proof.candidate_hash_after


def test_ooxml_semantic_inspector_rejects_identity_drift(tmp_path: Path) -> None:
    plan = build_portable_plan()
    renderer = PptxGenJSRenderer(skill_root=SKILL_ROOT)
    output = tmp_path / "identity.pptx"
    renderer.render(plan, output)
    normalize_pptx_package(output)

    with zipfile.ZipFile(output) as source:
        parts = {name: source.read(name) for name in source.namelist()}
    slide_name = "ppt/slides/slide1.xml"
    expected = plan.slides[0].objects[0].name.encode("utf-8")
    parts[slide_name] = parts[slide_name].replace(expected, b"wp_identity_drift", 1)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for name, data in parts.items():
            target.writestr(name, data)

    with pytest.raises(OoxmlSemanticError, match="OBJECT_IDENTITY_MISSING"):
        inspect_rendered_pptx(output, plan)


@pytest.mark.skipif(
    shutil.which("soffice") is None or shutil.which("pdftoppm") is None,
    reason="LibreOffice and Poppler are required for the portable render proof",
)
def test_libreoffice_verifier_exports_real_pdf_and_png_without_mutating_pptx(
    tmp_path: Path,
) -> None:
    plan = build_portable_plan()
    output = tmp_path / "客户 deck with spaces.pptx"
    PptxGenJSRenderer(skill_root=SKILL_ROOT).render(plan, output)
    normalize_pptx_package(output)
    before = sha256_file(output)

    result = LibreOfficeVerifier().verify(
        output,
        artifact_dir=tmp_path / "proof",
        expected_slide_count=len(plan.slides),
        slide_size=plan.slide_size,
    )

    assert result.page_count == len(plan.slides)
    assert result.pdf_path.read_bytes().startswith(b"%PDF-")
    assert len(result.png_paths) == len(plan.slides)
    assert all(path.read_bytes().startswith(b"\x89PNG") for path in result.png_paths)
    assert sha256_file(output) == before


def test_libreoffice_verifier_fails_closed_for_missing_runtime(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.pptx"
    candidate.write_bytes(b"candidate")
    verifier = LibreOfficeVerifier(soffice="/definitely/missing/soffice")

    with pytest.raises(
        LibreOfficeVerificationError,
        match="PROOF_PROCESS_START_FAILED",
    ):
        verifier.verify(
            candidate,
            artifact_dir=tmp_path / "proof",
            expected_slide_count=1,
            slide_size=SlideSize(13.333, 7.5),
        )


def test_owned_proof_process_timeout_is_terminated(tmp_path: Path) -> None:
    with pytest.raises(LibreOfficeVerificationError, match="PROOF_PROCESS_TIMEOUT"):
        libreoffice_module._run_owned_process(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            timeout_seconds=1,
            cwd=tmp_path,
        )


@pytest.mark.parametrize(
    "slide_size",
    (SlideSize(10.0, 7.5), SlideSize(11.0, 6.2)),
    ids=("four-three", "custom"),
)
@pytest.mark.skipif(
    shutil.which("soffice") is None or shutil.which("pdftoppm") is None,
    reason="LibreOffice and Poppler are required for the portable render proof",
)
def test_libreoffice_verifier_preserves_supported_page_ratios(
    tmp_path: Path,
    slide_size: SlideSize,
) -> None:
    plan = build_render_plan(
        portable_deck(),
        slide_size=slide_size,
        installed_fonts={"Arial"},
    )
    output = tmp_path / f"ratio-{slide_size.width}-{slide_size.height}.pptx"
    PptxGenJSRenderer(skill_root=SKILL_ROOT).render(plan, output)
    normalize_pptx_package(output)

    result = LibreOfficeVerifier().verify(
        output,
        artifact_dir=tmp_path / "proof",
        expected_slide_count=len(plan.slides),
        slide_size=slide_size,
    )

    assert result.page_width_pt == pytest.approx(slide_size.width * 72, abs=1.5)
    assert result.page_height_pt == pytest.approx(slide_size.height * 72, abs=1.5)


@pytest.mark.skipif(
    shutil.which("soffice") is None or shutil.which("pdftoppm") is None,
    reason="LibreOffice and Poppler are required for the portable render proof",
)
def test_cli_auto_backend_completes_without_powerpoint_com(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "deck.json").write_text(
        json.dumps(portable_deck(), ensure_ascii=False),
        encoding="utf-8",
    )

    def forbidden() -> None:
        raise AssertionError("portable auto route attempted to require PowerPoint")

    def broken_html(*_args: object, **_kwargs: object) -> None:
        raise OSError("injected optional proof failure")

    monkeypatch.setattr(automation, "require_windows", forbidden)
    monkeypatch.setattr(automation, "write_html_proof", broken_html)
    result = automation.main(
        [
            "--project-dir",
            str(tmp_path),
            "--render-deck-plan",
            "--deck-plan",
            "deck.json",
            "--output",
            "delivery.pptx",
            "--export-pdf",
            "--export-qa",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["render_pipeline"]["backend"]["backend_id"] == "pptxgenjs"
    assert payload["render_pipeline"]["verification"]["level"] == "portable"
    assert payload["render_pipeline"]["verification"]["quality"]["passed"] is True
    assert set(payload["render_pipeline"]["artifact_sha256"]) >= {
        "ooxml_report",
        "quality_report_v2",
        "portable_pdf",
        "portable_png_001",
        "portable_verification",
        "output_pptx",
        "output_pdf",
    }
    assert payload["html_proof"] is None
    assert "injected optional proof failure" in payload["html_proof_error"]
    assert (tmp_path / "delivery.pptx").is_file()
    assert (tmp_path / "delivery.pdf").read_bytes().startswith(b"%PDF-")
    assert (tmp_path / ".window-pptx" / "audits" / "ooxml-report.json").is_file()
    verification_report = (
        tmp_path / ".window-pptx" / "audits" / "portable-verification.json"
    )
    assert com_diagnostics.validate_portable_certification_input(
        tmp_path / "delivery.pptx",
        verification_report,
    )["candidate_sha256"] == sha256_file(tmp_path / "delivery.pptx")
    assert len(tuple((tmp_path / ".window-pptx" / "exports" / "qa").glob("*.png"))) == 3


def test_portable_pipeline_never_promotes_a_candidate_when_proof_fails(
    tmp_path: Path,
) -> None:
    output = tmp_path / "delivery.pptx"
    output.write_bytes(b"existing delivery remains intact")

    class FailingVerifier:
        def verify(self, *_args: object, **_kwargs: object):
            raise LibreOfficeVerificationError("INJECTED_PROOF_FAILURE")

    with pytest.raises(LibreOfficeVerificationError, match="INJECTED_PROOF_FAILURE"):
        execute_portable_render_plan(
            {"schema_version": "1.0", "slides": []},
            build_portable_plan(),
            output_policy=OutputPolicy(None, output),
            audit_dir=tmp_path / "audits",
            verifier=FailingVerifier(),  # type: ignore[arg-type]
        )

    assert output.read_bytes() == b"existing delivery remains intact"
    assert not tuple(tmp_path.glob(".window-pptx-*.pptx"))


@pytest.mark.skipif(
    shutil.which("soffice") is None or shutil.which("pdftoppm") is None,
    reason="LibreOffice and Poppler are required for the portable render proof",
)
def test_powerpoint_certifier_cannot_mutate_the_verified_candidate(
    tmp_path: Path,
) -> None:
    output = tmp_path / "delivery.pptx"
    output.write_bytes(b"existing delivery remains intact")
    received: list[Path] = []

    def mutating_certifier(candidate: Path, artifact_dir: Path) -> dict[str, object]:
        received.append(candidate)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(b"corrupt")
        return {}

    with pytest.raises(
        TransactionError,
        match="isolated PowerPoint certification input changed",
    ):
        execute_portable_render_plan(
            {"schema_version": "1.0", "slides": []},
            build_portable_plan(),
            output_policy=OutputPolicy(None, output),
            audit_dir=tmp_path / "audits",
            verification_level="powerpoint",
            powerpoint_certifier=mutating_certifier,
        )

    assert received
    assert received[0] != output
    assert received[0].name == ".powerpoint-certification-input.pptx"
    assert output.read_bytes() == b"existing delivery remains intact"
    assert not tuple(tmp_path.glob(".window-pptx-*.pptx"))


@pytest.mark.parametrize(
    ("payload", "message"),
    (
        ({}, "fields are incomplete"),
        ({"powerpoint_version": "16.0"}, "fields are incomplete"),
        (
            {
                "powerpoint_version": "16.0",
                "pdf_path": "missing.pdf",
                "png_paths": ["one.png", "two.png", "three.png"],
                "candidate_hash_before": "b" * 64,
                "candidate_hash_after": "a" * 64,
                "owned_pid": 42,
            },
            "mismatched candidate_hash_before",
        ),
    ),
)
def test_powerpoint_certification_result_rejects_empty_partial_or_forged_evidence(
    tmp_path: Path,
    payload: dict[str, object],
    message: str,
) -> None:
    artifact_dir = tmp_path / "certification"
    artifact_dir.mkdir()

    with pytest.raises(TransactionError, match=message):
        portable_runner_module._validate_powerpoint_certification_result(
            payload,
            expected_sha256="a" * 64,
            artifact_dir=artifact_dir,
            expected_slide_count=3,
            slide_size=SlideSize(13.333, 7.5),
        )


def test_powerpoint_certification_result_rejects_evidence_outside_staging(
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "certification"
    artifact_dir.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"%PDF-1.4\n")
    payload = {
        "powerpoint_version": "16.0",
        "pdf_path": str(outside),
        "png_paths": [str(tmp_path / f"outside-{index}.png") for index in range(3)],
        "candidate_hash_before": "a" * 64,
        "candidate_hash_after": "a" * 64,
        "owned_pid": 42,
    }

    with pytest.raises(TransactionError, match="outside its staging directory"):
        portable_runner_module._validate_powerpoint_certification_result(
            payload,
            expected_sha256="a" * 64,
            artifact_dir=artifact_dir,
            expected_slide_count=3,
            slide_size=SlideSize(13.333, 7.5),
        )


def test_portable_bundle_promotion_rolls_back_every_target_on_late_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_source = tmp_path / "staged-first.json"
    second_source = tmp_path / "staged-deck.pptx"
    first_target = tmp_path / "stable-first.json"
    second_target = tmp_path / "stable-deck.pptx"
    first_source.write_bytes(b"new report")
    second_source.write_bytes(b"new deck")
    first_target.write_bytes(b"old report")
    second_target.write_bytes(b"old deck")
    original_replace = portable_runner_module.os.replace

    def fail_on_deck_install(source: Path | str, target: Path | str) -> None:
        if Path(source) == second_source and Path(target) == second_target:
            raise OSError("injected final deck promotion failure")
        original_replace(source, target)

    monkeypatch.setattr(portable_runner_module.os, "replace", fail_on_deck_install)

    with pytest.raises(
        portable_runner_module.TransactionError,
        match="portable bundle promotion failed",
    ):
        portable_runner_module._promote_bundle(
            (
                (first_source, first_target),
                (second_source, second_target),
            )
        )

    assert first_target.read_bytes() == b"old report"
    assert second_target.read_bytes() == b"old deck"
    assert not tuple(tmp_path.glob(".*.window-pptx-backup-*"))


def test_ooxml_inspector_rejects_forged_render_plan_without_writing(
    tmp_path: Path,
) -> None:
    plan = build_portable_plan()
    output = tmp_path / "deck.pptx"
    PptxGenJSRenderer(skill_root=SKILL_ROOT).render(plan, output)
    normalize_pptx_package(output)
    first_slide = plan.slides[0]
    first_object = first_slide.objects[0]
    forged = replace(
        plan,
        slides=(
            replace(
                first_slide,
                objects=(replace(first_object, text="伪造内容"), *first_slide.objects[1:]),
            ),
            *plan.slides[1:],
        ),
    )

    with pytest.raises(OoxmlSemanticError, match="OBJECT_TEXT_MISMATCH"):
        inspect_rendered_pptx(output, forged)


def test_ooxml_inspector_validates_native_image_payload_and_crop(
    tmp_path: Path,
) -> None:
    image = tmp_path / "hero.png"
    Image.new("RGB", (1200, 1000), color=(26, 74, 120)).save(image)
    plan = build_image_plan(image)
    output = tmp_path / "image-deck.pptx"
    PptxGenJSRenderer(skill_root=SKILL_ROOT).render(plan, output)
    normalize_pptx_package(output)

    report = inspect_rendered_pptx(output, plan)
    assert report.slide_count == 1
    assert any(item.kind == "image" for item in plan.slides[0].objects)

    def mutate(parts: dict[str, bytes]) -> dict[str, bytes]:
        media = next(
            name
            for name in parts
            if name.startswith("ppt/media/") and not name.endswith("/")
        )
        parts[media] = b"not an image"
        return parts

    corrupted = _mutated_copy(output, tmp_path / "bad-image.pptx", mutate)
    with pytest.raises(OoxmlSemanticError, match="IMAGE_PAYLOAD_UNREADABLE"):
        inspect_rendered_pptx(corrupted, plan)


@pytest.mark.parametrize("extension", ("png", "jpg", "svg"))
def test_portable_images_remain_native_across_supported_formats(
    tmp_path: Path,
    extension: str,
) -> None:
    image = tmp_path / f"hero.{extension}"
    if extension == "svg":
        image.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1000">'
            '<rect width="1200" height="1000" fill="#1A4A78"/>'
            '<circle cx="600" cy="500" r="220" fill="#FFFFFF"/>'
            "</svg>",
            encoding="utf-8",
        )
    else:
        Image.new("RGB", (1200, 1000), color=(26, 74, 120)).save(image)
    plan = build_image_plan(image)
    output = tmp_path / f"image-{extension}.pptx"

    PptxGenJSRenderer(skill_root=SKILL_ROOT).render(plan, output)
    normalize_pptx_package(output)
    semantic = inspect_rendered_pptx(output, plan)

    assert semantic.slide_count == 1
    assert any(item.kind == "image" for item in plan.slides[0].objects)


@pytest.mark.parametrize(
    ("case_id", "expected_code"),
    (
        ("content-type", "CONTENT_TYPE_MISSING"),
        ("relationship-target", "RELATIONSHIP_TARGET_MISSING"),
        ("duplicate-relationship", "RELATIONSHIP_ID_INVALID"),
        ("chart-workbook", "CHART_WORKBOOK_RELATIONSHIP_MISSING"),
        ("chart-order", "CHART_CATEGORY_MISMATCH"),
        ("font-style", "OBJECT_FONT_SIZE_MISMATCH"),
        ("font-weight", "OBJECT_FONT_WEIGHT_MISMATCH"),
        ("diagram-child-style", "OBJECT_FILL_MISMATCH"),
        ("slide-size", "SLIDE_SIZE_MISMATCH"),
        ("notes-link", "NOTES_MISSING"),
        ("hyperlink", "HYPERLINK_TARGET_MISMATCH"),
        ("unexpected-hyperlink", "HYPERLINK_UNEXPECTED"),
        ("master-chain", "SLIDE_LAYOUT_RELATIONSHIP_MISSING"),
        ("role-layout-style", "ROLE_LAYOUT_STYLE_MISMATCH"),
    ),
)
def test_ooxml_inspector_rejects_corrupted_semantic_packages(
    rendered_portable_fixture,
    tmp_path: Path,
    case_id: str,
    expected_code: str,
) -> None:
    plan, source = rendered_portable_fixture

    def mutate(parts: dict[str, bytes]) -> dict[str, bytes]:
        if case_id == "content-type":
            parts["[Content_Types].xml"] = re.sub(
                rb'<Override PartName="/ppt/slides/slide1\.xml"[^>]*/>',
                b"",
                parts["[Content_Types].xml"],
                count=1,
            )
        elif case_id == "relationship-target":
            key = "ppt/slides/_rels/slide1.xml.rels"
            parts[key] = parts[key].replace(
                b"/ppt/charts/chart1.xml",
                b"/ppt/charts/missing-chart.xml",
                1,
            )
        elif case_id == "duplicate-relationship":
            key = "ppt/slides/_rels/slide1.xml.rels"
            identifiers = re.findall(rb'Id="(rId\d+)"', parts[key])
            assert len(identifiers) >= 2
            parts[key] = parts[key].replace(
                b'Id="' + identifiers[1] + b'"',
                b'Id="' + identifiers[0] + b'"',
                1,
            )
        elif case_id == "chart-workbook":
            key = "ppt/charts/chart1.xml"
            parts[key] = re.sub(
                rb"<c:externalData\b[\s\S]*?</c:externalData>",
                b"",
                parts[key],
                count=1,
            )
        elif case_id == "chart-order":
            key = "ppt/charts/chart1.xml"
            category = re.search(
                rb"(<c:cat>[\s\S]*?<c:(?:multiLvlStrCache|strCache)>)"
                rb"([\s\S]*?)(</c:(?:multiLvlStrCache|strCache)>)",
                parts[key],
            )
            assert category is not None
            cache = category.group(2)
            values = re.findall(rb"<c:v>([^<]*)</c:v>", cache)
            assert len(values) >= 2
            marker = b"__WINDOW_PPTX_SWAP__"
            cache = cache.replace(
                b"<c:v>" + values[0] + b"</c:v>",
                marker,
                1,
            ).replace(
                b"<c:v>" + values[1] + b"</c:v>",
                b"<c:v>" + values[0] + b"</c:v>",
                1,
            ).replace(
                marker,
                b"<c:v>" + values[1] + b"</c:v>",
                1,
            )
            parts[key] = (
                parts[key][: category.start(2)]
                + cache
                + parts[key][category.end(2) :]
            )
        elif case_id == "font-style":
            key = "ppt/slides/slide1.xml"
            parts[key] = re.sub(
                rb'(<a:rPr\b[^>]*\bsz=")\d+',
                rb"\g<1>800",
                parts[key],
                count=1,
            )
        elif case_id == "font-weight":
            key = "ppt/slides/slide1.xml"
            parts[key], count = re.subn(
                rb'(<a:rPr\b[^>]*\bb=")1("[^>]*>)',
                rb"\g<1>0\g<2>",
                parts[key],
                count=1,
            )
            assert count == 1
        elif case_id == "diagram-child-style":
            key = "ppt/slides/slide3.xml"
            parts[key] = re.sub(
                rb'(<p:cNvPr\b[^>]*name="[^"]*__node_01"[\s\S]*?'
                rb'<a:solidFill>\s*<a:srgbClr val=")[0-9A-Fa-f]{6}',
                rb"\g<1>FF00FF",
                parts[key],
                count=1,
            )
        elif case_id == "slide-size":
            key = "ppt/presentation.xml"
            parts[key] = re.sub(
                rb'(<p:sldSz\b[^>]*\bcx=")\d+',
                rb"\g<1>1000000",
                parts[key],
                count=1,
            )
        elif case_id == "notes-link":
            key = "ppt/slides/_rels/slide1.xml.rels"
            parts[key] = re.sub(
                rb'<Relationship\b[^>]*Type="[^"]*/notesSlide"[^>]*/>',
                b"",
                parts[key],
                count=1,
            )
        elif case_id == "hyperlink":
            key = "ppt/slides/_rels/slide1.xml.rels"
            parts[key] = re.sub(
                rb'<Relationship\b[^>]*Type="[^"]*/hyperlink"[^>]*/>',
                b"",
                parts[key],
                count=1,
            )
        elif case_id == "unexpected-hyperlink":
            rels_key = "ppt/slides/_rels/slide1.xml.rels"
            hyperlink = re.search(
                rb'<Relationship\b[^>]*Id="([^"]+)"[^>]*'
                rb'Type="[^"]*/hyperlink"[^>]*/>',
                parts[rels_key],
            )
            assert hyperlink is not None
            title_name = plan.slides[0].objects[0].name.encode("utf-8")
            slide_key = "ppt/slides/slide1.xml"
            pattern = (
                rb'<p:cNvPr\b[^>]*\bname="'
                + re.escape(title_name)
                + rb'"[^>]*>'
            )
            replacement = (
                rb'\g<0><a:hlinkClick r:id="'
                + hyperlink.group(1)
                + rb'"/>'
            )
            parts[slide_key], count = re.subn(
                pattern, replacement, parts[slide_key], count=1
            )
            assert count == 1
        elif case_id == "master-chain":
            key = "ppt/slides/_rels/slide1.xml.rels"
            parts[key] = re.sub(
                rb'<Relationship\b[^>]*Type="[^"]*/slideLayout"[^>]*/>',
                b"",
                parts[key],
                count=1,
            )
        elif case_id == "role-layout-style":
            rels = parts["ppt/slides/_rels/slide1.xml.rels"]
            target = re.search(
                rb'Type="[^"]*/slideLayout"[^>]*Target="\.\./slideLayouts/([^"]+)"',
                rels,
            )
            assert target is not None
            key = f"ppt/slideLayouts/{target.group(1).decode('ascii')}"
            primary = plan.slides[0].objects[0].line_color.lstrip("#").encode("ascii")
            parts[key], count = re.subn(
                rb'(<a:solidFill>\s*<a:srgbClr val=")' + primary + rb'(")',
                rb"\g<1>FF00FF\g<2>",
                parts[key],
                count=1,
            )
            assert count == 1
        return parts

    corrupted = _mutated_copy(source, tmp_path / f"{case_id}.pptx", mutate)
    with pytest.raises(OoxmlSemanticError, match=expected_code):
        inspect_rendered_pptx(corrupted, plan)
