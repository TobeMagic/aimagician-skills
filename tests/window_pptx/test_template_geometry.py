from __future__ import annotations

import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.template_geometry import propose_visual_masks  # noqa: E402
from window_pptx.template_pack import (  # noqa: E402
    TemplateChartSlot,
    TemplatePack,
    TemplateSlot,
)


def _write_nested_template(path: Path) -> None:
    presentation = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldSz cx="1000" cy="1000"/>
</p:presentation>"""
    slide = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name="root"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="1000" cy="1000"/>
      <a:chOff x="0" y="0"/><a:chExt cx="1000" cy="1000"/></a:xfrm></p:grpSpPr>
    <p:grpSp>
      <p:nvGrpSpPr><p:cNvPr id="2" name="scaled"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="100" y="200"/><a:ext cx="400" cy="200"/>
        <a:chOff x="0" y="0"/><a:chExt cx="200" cy="100"/></a:xfrm></p:grpSpPr>
      <p:sp>
        <p:nvSpPr><p:cNvPr id="5" name="editable"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="25" y="10"/><a:ext cx="50" cy="20"/></a:xfrm></p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>old</a:t></a:r></a:p></p:txBody>
      </p:sp>
    </p:grpSp>
    <p:graphicFrame>
      <p:nvGraphicFramePr><p:cNvPr id="9" name="chart"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>
      <p:xfrm><a:off x="500" y="100"/><a:ext cx="200" cy="300"/></p:xfrm>
      <a:graphic><a:graphicData><c:chart r:id="rId9"/></a:graphicData></a:graphic>
    </p:graphicFrame>
  </p:spTree></p:cSld>
</p:sld>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId9"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"
    Target="../charts/chart1.xml"/>
</Relationships>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/presentation.xml", presentation)
        archive.writestr("ppt/slides/slide1.xml", slide)
        archive.writestr("ppt/slides/_rels/slide1.xml.rels", rels)
        archive.writestr("ppt/charts/chart1.xml", "<c:chartSpace xmlns:c=\"http://schemas.openxmlformats.org/drawingml/2006/chart\"/>")


def test_nested_group_and_chart_masks_are_relationship_resolved_and_deterministic(
    tmp_path: Path,
) -> None:
    template = tmp_path / "nested.pptx"
    _write_nested_template(template)
    pack = TemplatePack(
        id="nested",
        name="Nested",
        manifest_path=tmp_path / "template-pack.json",
        template_path=template,
        template_sha256="0" * 64,
        slide_count=1,
        slots=(
            TemplateSlot(
                id="body",
                slide=1,
                shape_id=5,
                kind="body",
                max_chars=20,
                required=True,
            ),
        ),
        chart_slots=(
            TemplateChartSlot(
                id="chart",
                chart_part="ppt/charts/chart1.xml",
                cache_index=0,
                kind="chart-number",
                max_chars=8,
                required=True,
                workbook_path="ppt/embeddings/data.xlsx",
                workbook_cell="A1",
            ),
        ),
        text_style_rules=(),
        supported_scenarios=(),
    )

    first = propose_visual_masks(pack)
    second = propose_visual_masks(pack)

    assert first == second
    assert len(first) == 2
    shape = next(mask for mask in first if mask.target_kind == "shape")
    chart = next(mask for mask in first if mask.target_kind == "chart")
    assert (shape.slide, shape.target_id) == (1, "5")
    assert (shape.x, shape.y, shape.width, shape.height) == (
        0.15,
        0.22,
        0.1,
        0.04,
    )
    assert (chart.slide, chart.target_id) == (1, "ppt/charts/chart1.xml")
    assert (chart.x, chart.y, chart.width, chart.height) == (0.5, 0.1, 0.2, 0.3)


def test_institutional_pack_inventory_covers_every_declared_target() -> None:
    from window_pptx.template_pack import load_template_pack

    pack = load_template_pack("institutional-work-summary-v1")
    masks = propose_visual_masks(pack)

    shape_targets = {
        (mask.slide, int(mask.target_id))
        for mask in masks
        if mask.target_kind == "shape"
    }
    chart_targets = {
        mask.target_id for mask in masks if mask.target_kind == "chart"
    }
    assert shape_targets == {(slot.slide, slot.shape_id) for slot in pack.slots}
    assert chart_targets == {slot.chart_part for slot in pack.chart_slots}
