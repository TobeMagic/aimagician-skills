from __future__ import annotations

import hashlib
import io
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from pathlib import Path

import pytest
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.template_pack import (  # noqa: E402
    TemplatePackError,
    adapt_template_pack,
    load_template_bindings,
    load_template_pack,
)
from window_pptx.cli import build_dry_run_result, parse_args  # noqa: E402
from window_pptx.golden_template_replay import run_golden_template_replay  # noqa: E402
from window_pptx.libreoffice import LibreOfficeVerificationResult  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _entry_hashes(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        return {
            name: hashlib.sha256(archive.read(name)).hexdigest()
            for name in archive.namelist()
        }


def test_reference_template_pack_is_authorized_hash_bound_and_complete() -> None:
    pack = load_template_pack("institutional-work-summary-v1")

    assert pack.slide_count == 15
    assert pack.template_path.name == "template.pptx"
    assert pack.template_sha256 == _sha(pack.template_path)
    assert len(pack.slots) == 220
    assert len(pack.chart_slots) == 36
    assert len(pack.slots_by_id) == 256
    assert len(pack.visual_masks) == 224
    assert len(pack.chart_slots) == 36
    assert len(pack.slots_by_id) == len(pack.slots) + len(pack.chart_slots)
    assert {slot.slide for slot in pack.slots} == set(range(1, 16))


def test_no_op_adaptation_is_byte_identical(tmp_path: Path) -> None:
    pack = load_template_pack("institutional-work-summary-v1")
    output = tmp_path / "noop.pptx"

    report = adapt_template_pack(
        pack,
        {},
        output,
        require_all_required=False,
    )

    assert output.read_bytes() == pack.template_path.read_bytes()
    assert report.no_op_copy is True
    assert report.changed_parts == ()
    assert report.output_sha256 == report.source_sha256
    assert report.source_integrity_preserved is True


def test_partial_adaptation_changes_only_declared_slide_part(tmp_path: Path) -> None:
    pack = load_template_pack("institutional-work-summary-v1")
    output = tmp_path / "adapted.pptx"
    source_before = _sha(pack.template_path)

    report = adapt_template_pack(
        pack,
        {"s01.presenter": "汇报人：普通模型"},
        output,
        require_all_required=False,
    )

    assert report.changed_parts == ("ppt/slides/slide1.xml",)
    assert report.source_integrity_preserved is True
    assert _sha(pack.template_path) == source_before
    source_entries = _entry_hashes(pack.template_path)
    output_entries = _entry_hashes(output)
    assert source_entries.keys() == output_entries.keys()
    assert {
        name
        for name in source_entries
        if source_entries[name] != output_entries[name]
    } == {"ppt/slides/slide1.xml"}
    with zipfile.ZipFile(output) as archive:
        slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
    slide_root = ET.fromstring(slide_xml)
    visible_text = "".join(
        node.text or ""
        for node in slide_root.iter(
            "{http://schemas.openxmlformats.org/drawingml/2006/main}t"
        )
    )
    assert "汇报人：普通模型" in visible_text
    assert "ppt/media/" in "\n".join(output_entries)


def test_display_title_style_rule_clamps_missing_font_risk(tmp_path: Path) -> None:
    pack = load_template_pack("institutional-work-summary-v1")
    output = tmp_path / "portable-title.pptx"

    adapt_template_pack(
        pack,
        {"s01.title.1": "技"},
        output,
        require_all_required=False,
    )

    with zipfile.ZipFile(output) as archive:
        slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
    assert 'sz="9200"' in slide_xml
    assert 'typeface="Microsoft YaHei"' in slide_xml
    assert 'typeface="演示夏行楷"' in slide_xml


def test_full_work_summary_bindings_adapt_all_fifteen_slides(tmp_path: Path) -> None:
    binding_path = SKILL_ROOT / "evals" / "v5.1-work-summary-bindings.json"
    pack_id, bindings = load_template_bindings(binding_path)
    output = tmp_path / "reference-grade-work-summary.pptx"

    report = adapt_template_pack(pack_id, bindings, output)

    assert report.slide_count == 15
    assert set(report.changed_parts) == {
        *(f"ppt/slides/slide{index}.xml" for index in range(1, 16)),
        *(f"ppt/charts/chart{index}.xml" for index in range(1, 5)),
        "ppt/embeddings/Microsoft_Excel_Worksheet.xlsx",
        "ppt/embeddings/Microsoft_Excel_Worksheet1.xlsx",
        "ppt/embeddings/Microsoft_Excel_Worksheet2.xlsx",
        "ppt/embeddings/Microsoft_Excel_Worksheet3.xlsx",
    }
    assert len(report.slot_changes) == len(bindings)
    with zipfile.ZipFile(output) as archive:
        combined = "\n".join(
            archive.read(f"ppt/slides/slide{index}.xml").decode("utf-8")
            for index in range(1, 16)
        )
        names = set(archive.namelist())
        chart3 = archive.read("ppt/charts/chart3.xml").decode("utf-8")
        embedded = archive.read(
            "ppt/embeddings/Microsoft_Excel_Worksheet2.xlsx"
        )
    assert "Window-PPTX" in combined
    assert "客户交付为唯一视觉标准" in combined
    assert "ppt/charts/chart1.xml" in names
    assert "ppt/embeddings/Microsoft_Excel_Worksheet1.xlsx" in names
    assert any(name.startswith("ppt/media/") for name in names)
    assert "结构检查" in chart3
    with zipfile.ZipFile(io.BytesIO(embedded)) as workbook:
        shared_strings = workbook.read("xl/sharedStrings.xml").decode("utf-8")
    assert "结构检查" in shared_strings


def test_adapter_rejects_unknown_over_capacity_missing_and_source_overwrite(
    tmp_path: Path,
) -> None:
    pack = load_template_pack("institutional-work-summary-v1")

    with pytest.raises(TemplatePackError, match="unknown TemplatePack slots"):
        adapt_template_pack(
            pack,
            {"not-a-slot": "x"},
            tmp_path / "unknown.pptx",
            require_all_required=False,
        )
    with pytest.raises(TemplatePackError, match="capacity is 1"):
        adapt_template_pack(
            pack,
            {"s01.title.1": "超过"},
            tmp_path / "capacity.pptx",
            require_all_required=False,
        )
    with pytest.raises(TemplatePackError, match="missing required"):
        adapt_template_pack(pack, {"s01.year": "2026年"}, tmp_path / "missing.pptx")
    with pytest.raises(TemplatePackError, match="must not overwrite"):
        adapt_template_pack(
            pack,
            {},
            pack.template_path,
            require_all_required=False,
        )


def test_v51_contract_schemas_accept_owned_pack_manifests() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    template_schema = json.loads(
        (SKILL_ROOT / "schemas" / "template-pack.v1.schema.json").read_text()
    )
    for manifest in (SKILL_ROOT / "design-packs").glob("*/pack.json"):
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        schema_name = (
            "design-pack.v2.schema.json"
            if payload["schema_version"] == "2.0"
            else "design-pack.v1.schema.json"
        )
        design_schema = json.loads(
            (SKILL_ROOT / "schemas" / schema_name).read_text()
        )
        jsonschema.Draft202012Validator(design_schema).validate(payload)
    jsonschema.Draft202012Validator(template_schema).validate(
        json.loads(
            (
                SKILL_ROOT
                / "design-packs"
                / "institutional-annual-editorial"
                / "template-pack.json"
            ).read_text(encoding="utf-8")
        )
    )


def test_template_pack_cli_is_portable_and_reports_all_dry_run_outputs(
    tmp_path: Path,
) -> None:
    args = parse_args(
        [
            "--project-dir",
            str(tmp_path),
            "--render-template-pack",
            "--template-pack",
            "institutional-work-summary-v1",
            "--template-bindings",
            str(SKILL_ROOT / "evals" / "v5.1-work-summary-bindings.json"),
            "--output",
            "output/work-summary.pptx",
            "--dry-run",
        ]
    )

    assert args.backend == "auto"
    assert args.verification == "portable"
    result = build_dry_run_result(args, tmp_path)
    assert result["would_run"] == ["render_template_pack"]
    assert str(tmp_path / "output" / "work-summary.pptx") in result["would_write"]
    assert any(
        value.endswith("template-adaptation-report.json")
        for value in result["would_write"]
    )


def test_template_pack_cli_accepts_paired_selection_sidecars_only(
    tmp_path: Path,
) -> None:
    common = [
        "--project-dir",
        str(tmp_path),
        "--render-template-pack",
        "--template-pack",
        "institutional-work-summary-v1",
        "--template-bindings",
        "bindings.json",
        "--output",
        "output/work-summary.pptx",
        "--dry-run",
    ]
    with pytest.raises(SystemExit):
        parse_args([*common, "--template-selection-plan", "selection.json"])

    args = parse_args(
        [
            *common,
            "--template-selection-plan",
            "selection.json",
            "--slide-blueprints",
            "blueprints.json",
        ]
    )
    result = build_dry_run_result(args, tmp_path)
    assert any(
        value.endswith("candidate-materialization-report.json")
        for value in result["would_write"]
    )


def test_golden_replay_is_semantically_reproducible_with_one_renderer_fingerprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeVerifier:
        dpi = 144

        def verify(
            self,
            candidate: Path,
            *,
            artifact_dir: Path,
            expected_slide_count: int,
            slide_size: object,
        ) -> LibreOfficeVerificationResult:
            artifact_dir.mkdir(parents=True, exist_ok=True)
            pngs = []
            for index in range(1, expected_slide_count + 1):
                path = artifact_dir / f"slide-{index:03d}.png"
                Image.new("RGB", (160, 90), "white").save(path)
                pngs.append(path)
            pdf = artifact_dir / "portable-proof.pdf"
            pdf.write_bytes(b"%PDF-fake")
            digest = _sha(candidate)
            return LibreOfficeVerificationResult(
                engine_version="LibreOffice test",
                poppler_version="Ghostscript test",
                page_count=expected_slide_count,
                page_width_pt=960,
                page_height_pt=540,
                pdf_path=pdf,
                png_paths=tuple(pngs),
                candidate_hash_before=digest,
                candidate_hash_after=digest,
            )

    monkeypatch.setattr(
        "window_pptx.golden_template_replay.assess_reference_grade_quality",
        lambda *args, **kwargs: SimpleNamespace(
            passed=True,
            complexity=SimpleNamespace(
                average_objects_per_slide=56.467,
                layout_signature_count=12,
                chart_count=4,
                media_count=29,
            ),
        ),
    )
    bindings = SKILL_ROOT / "evals" / "v5.1-work-summary-bindings.json"

    first = run_golden_template_replay(
        "institutional-work-summary-v1",
        bindings,
        tmp_path / "first",
        verifier=FakeVerifier(),  # type: ignore[arg-type]
    )
    second = run_golden_template_replay(
        "institutional-work-summary-v1",
        bindings,
        tmp_path / "second",
        verifier=FakeVerifier(),  # type: ignore[arg-type]
    )

    assert first.candidate_sha256 == second.candidate_sha256
    assert first.manifest == second.manifest
    assert first.similarity.passed is True
