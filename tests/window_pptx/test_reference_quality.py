from __future__ import annotations

import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.reference_quality import (  # noqa: E402
    assess_generated_visual_quality,
    assess_reference_grade_quality,
    inspect_reference_complexity,
)


def _write_sparse_pptx(path: Path) -> None:
    slide = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
 <p:cSld><p:spTree>
  <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
  <p:grpSpPr/>
  <p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
   <p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>Title only</a:t></a:r></a:p></p:txBody>
  </p:sp>
 </p:spTree></p:cSld>
</p:sld>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", slide)


def test_reference_template_passes_structural_visual_floor() -> None:
    source = (
        SKILL_ROOT
        / "design-packs"
        / "institutional-annual-editorial"
        / "template.pptx"
    )
    complexity = inspect_reference_complexity(source)
    report = assess_reference_grade_quality(source)
    assert report.passed is True
    assert complexity.slide_count == 15
    assert complexity.chart_count == 4
    assert complexity.embedded_workbook_count == 4
    assert complexity.average_objects_per_slide > 50
    assert complexity.layout_signature_count >= 10


def test_sparse_text_only_deck_fails_visual_floor(tmp_path: Path) -> None:
    source = tmp_path / "sparse.pptx"
    _write_sparse_pptx(source)
    report = assess_reference_grade_quality(source)
    codes = {finding.code for finding in report.findings}
    assert report.passed is False
    assert "VISUAL_OBJECT_FLOOR" in codes
    assert "MEDIA_COUNT_FLOOR" in codes
    assert "EDITABLE_CHART_FLOOR" in codes
    assert "GROUP_COMPOSITION_FLOOR" in codes


def test_sparse_text_only_deck_fails_generated_visual_floor(tmp_path: Path) -> None:
    source = tmp_path / "sparse-generated.pptx"
    _write_sparse_pptx(source)

    complexity, findings = assess_generated_visual_quality(source)
    hard_codes = {
        finding.code for finding in findings if finding.severity == "hard-gate"
    }

    assert complexity.objects_per_slide == (1,)
    assert hard_codes == {
        "GENERATED_VISUAL_OBJECT_FLOOR",
        "GENERATED_LAYOUT_VARIATION_FLOOR",
        "GENERATED_RICH_SLIDE_RATIO_FLOOR",
    }
