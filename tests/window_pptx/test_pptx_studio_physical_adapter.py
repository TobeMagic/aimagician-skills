from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.adaptation import compile_adaptation  # noqa: E402
from pptx_studio.physical_adapter import (  # noqa: E402
    PhysicalAdapterError,
    assemble_from_plans,
    compile_physical_adapter,
    resolve_catalog_sources,
)
from pptx_studio.qa import run_studio_qa  # noqa: E402
from manage_pptx_studio_library import run  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_pack(tmp_path: Path) -> tuple[Path, dict[str, object], dict[str, object], dict[str, object], Path]:
    source_root = tmp_path / "private"
    category = source_root / "003-封面模板"
    category.mkdir(parents=True)
    source_image = tmp_path / "source.png"
    Image.new("RGB", (300, 180), "#123456").save(source_image)
    deck = category / "cover.pptx"
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    title = slide.shapes.add_textbox(Inches(1), Inches(0.7), Inches(9), Inches(0.8))
    title.text_frame.paragraphs[0].text = "模板标题"
    title.text_frame.paragraphs[0].font.size = Pt(30)
    subtitle = slide.shapes.add_textbox(Inches(1), Inches(1.7), Inches(9), Inches(0.6))
    subtitle.text_frame.paragraphs[0].text = "模板副标题"
    subtitle.text_frame.paragraphs[0].font.size = Pt(18)
    picture = slide.shapes.add_picture(str(source_image), Inches(7), Inches(3), width=Inches(2.5), height=Inches(1.5))
    presentation.save(deck)
    package_sha = _sha(deck)
    page_id = f"page_{package_sha[:24]}_001"
    title_id, subtitle_id, picture_id = str(title.shape_id), str(subtitle.shape_id), str(picture.shape_id)
    region_title, region_subtitle = "region-title", "region-subtitle"
    catalog: dict[str, object] = {
        "catalog_id": "test-catalog",
        "active_categories": ["003-封面模板"],
        "pages": [{
            "page_id": page_id, "deck_id": f"deck_{package_sha[:24]}",
            "package_sha256": package_sha, "slide_number": 1,
            "category": "003-封面模板", "style": {"palette": ["#123456"]},
            "render": {"visual_quality": 1.0},
            "shapes": [
                {"shape_id": title_id, "kind": "text", "max_chars": 48},
                {"shape_id": subtitle_id, "kind": "text", "max_chars": 72},
                {"shape_id": picture_id, "kind": "image", "max_chars": 0},
            ],
        }],
        "regions": [
            {"region_id": region_title, "page_id": page_id, "editable_shape_ids": [title_id], "capacity": {"max_text_chars": 48}},
            {"region_id": region_subtitle, "page_id": page_id, "editable_shape_ids": [subtitle_id], "capacity": {"max_text_chars": 72}},
        ],
    }
    composition: dict[str, object] = {
        "schema_version": "1.0", "status": "PASS", "art_direction": {"anchor_style_signature": "test"},
        "slides": [{
            "slide_id": "slide-01", "role": "cover",
            "source": {"page_id": page_id, "package_sha256": package_sha, "slide_number": 1, "region_ids": [region_title, region_subtitle]},
        }],
    }
    replacement = tmp_path / "replacement.png"
    Image.new("RGB", (180, 300), "#B96C3A").save(replacement)
    request: dict[str, object] = {
        "schema_version": "1.0",
        "facts": [
            {"fact_id": "report-title", "value": "2025年度工作汇报"},
            {"fact_id": "report-subtitle", "value": "财务运营部｜林晓"},
        ],
        "assets": [{"asset_id": "cover-image", "sha256": _sha(replacement)}],
        "bindings": [
            {"slide_id": "slide-01", "operation": "replace_text", "region_id": region_title, "shape_id": None, "fact_id": "report-title", "asset_id": None},
            {"slide_id": "slide-01", "operation": "replace_text", "region_id": region_subtitle, "shape_id": None, "fact_id": "report-subtitle", "asset_id": None},
            {"slide_id": "slide-01", "operation": "replace_asset", "region_id": None, "shape_id": picture_id, "fact_id": None, "asset_id": "cover-image"},
        ],
    }
    return source_root, catalog, composition, request, replacement


def test_adapter_materializes_native_editable_pptx_with_lineage(tmp_path: Path) -> None:
    source_root, catalog, composition, request, replacement = _source_pack(tmp_path)
    adaptation = compile_adaptation(composition, catalog=catalog, request=request)
    output = tmp_path / "output.pptx"
    report, lineage = assemble_from_plans(
        composition, adaptation, request, catalog=catalog,
        private_source_root=source_root, workspace=tmp_path / "stage", output_path=output,
        asset_paths={"cover-image": replacement},
    )
    assert report.status == "pass"
    assert output.is_file()
    produced = Presentation(output)
    text = "\n".join(shape.text for shape in produced.slides[0].shapes if hasattr(shape, "text"))
    assert "2025年度工作汇报" in text
    assert lineage["status"] == "PASS"
    assert lineage["qa"]["status"] == "pass"
    assert lineage["slides"][0]["source"]["slide_number"] == 1
    assert lineage["slides"][0]["asset_bindings"][0]["asset_id"] == "cover-image"


def test_adapter_rejects_unmapped_private_package(tmp_path: Path) -> None:
    source_root, catalog, composition, request, replacement = _source_pack(tmp_path)
    catalog["pages"][0]["package_sha256"] = "a" * 64  # type: ignore[index]
    with pytest.raises(PhysicalAdapterError, match="PRIVATE_PACKAGE_MISSING"):
        resolve_catalog_sources(catalog, private_source_root=source_root)


def test_adapter_rejects_value_plan_drift(tmp_path: Path) -> None:
    source_root, catalog, composition, request, replacement = _source_pack(tmp_path)
    adaptation = compile_adaptation(composition, catalog=catalog, request=request)
    request["facts"][0]["value"] = "另一份汇报"  # type: ignore[index]
    with pytest.raises(PhysicalAdapterError, match="ADAPTATION_REQUEST_DRIFT"):
        compile_physical_adapter(
            composition, adaptation, request, catalog=catalog,
            private_source_root=source_root, workspace=tmp_path / "stage",
            asset_paths={"cover-image": replacement},
        )


def test_cli_assembly_writes_only_output_and_nonliteral_lineage(tmp_path: Path) -> None:
    source_root, catalog, composition, request, replacement = _source_pack(tmp_path)
    adaptation = compile_adaptation(composition, catalog=catalog, request=request)
    files = {
        "catalog": tmp_path / "catalog.json", "composition": tmp_path / "composition.json",
        "request": tmp_path / "request.json", "adaptation": tmp_path / "adaptation.json",
        "assets": tmp_path / "assets.json", "lineage": tmp_path / "lineage.json",
    }
    (tmp_path / "unused.json").write_text('{"status":"APPLIED"}', encoding="utf-8")
    for name, value in (("catalog", catalog), ("composition", composition), ("request", request), ("adaptation", adaptation), ("assets", {"cover-image": str(replacement)})):
        files[name].write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    result = run([
        "assemble", "--source-root", str(tmp_path), "--archive-root", str(tmp_path), "--manifest", str(tmp_path / "unused.json"),
        "--catalog", str(files["catalog"]), "--composition-plan", str(files["composition"]),
        "--adaptation-input", str(files["request"]), "--adaptation-output", str(files["adaptation"]),
        "--private-source-root", str(source_root), "--assembly-workspace", str(tmp_path / "stage"),
        "--pptx-output", str(tmp_path / "cli-output.pptx"), "--lineage-output", str(files["lineage"]),
        "--asset-paths", str(files["assets"]),
    ])
    assert result["status"] == "PASS"
    lineage = files["lineage"].read_text(encoding="utf-8")
    assert "2025年度工作汇报" not in lineage
    assert (tmp_path / "cli-output.pptx").is_file()


def test_plan_qa_fails_closed_on_post_assembly_placeholder(tmp_path: Path) -> None:
    source_root, catalog, composition, request, replacement = _source_pack(tmp_path)
    adaptation = compile_adaptation(composition, catalog=catalog, request=request)
    compiled = compile_physical_adapter(
        composition, adaptation, request, catalog=catalog, private_source_root=source_root,
        workspace=tmp_path / "stage", asset_paths={"cover-image": replacement},
    )
    output = tmp_path / "output.pptx"
    report, lineage = assemble_from_plans(
        composition, adaptation, request, catalog=catalog, private_source_root=source_root,
        workspace=tmp_path / "stage", output_path=output, asset_paths={"cover-image": replacement},
    )
    deck = Presentation(output)
    next(shape for shape in deck.slides[0].shapes if hasattr(shape, "text") and shape.text).text = "20XX"
    deck.save(output)
    qa = run_studio_qa(output, plan=compiled.plan, physical_report=report, lineage=lineage)
    assert qa.status == "fail"
    assert any(item["rule"] == "placeholder" for item in qa.blockers)
