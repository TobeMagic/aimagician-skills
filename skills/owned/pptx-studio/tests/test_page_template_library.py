"""Regression tests for the v6.1 certified page-template compiler."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import zipfile
from dataclasses import replace
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.page_template_library import (  # noqa: E402
    DEFAULT_SCORING,
    PageTemplateError,
    compile_reference_deck,
    compile_page_templates,
    load_library_index,
    query_page_template_candidates,
    query_page_templates,
    serialize_page_template_candidates,
    write_library_index,
)
from manage_window_pptx_v61_library import run as run_library_cli  # noqa: E402


def _slide_xml(text: str, color: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr/>
    <p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody>
    </p:sp>
  </p:spTree></p:cSld>
</p:sld>"""


def _relationships(target: str, relationship_type: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="{relationship_type}" Target="{target}"/>
</Relationships>"""


def _write_package(path: Path) -> str:
    slide_rel = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
    )
    master_rel = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
    )
    theme_rel = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ppt/slides/slide1.xml", _slide_xml("FIRST-SLIDE", "FF0000"))
        archive.writestr("ppt/slides/slide2.xml", _slide_xml("SECOND-SLIDE", "0000FF"))
        archive.writestr("ppt/slides/slide3.xml", _slide_xml("THIRD-SLIDE", "00AA66"))
        for ordinal in range(1, 4):
            archive.writestr(
                f"ppt/slides/_rels/slide{ordinal}.xml.rels",
                _relationships(f"../slideLayouts/slideLayout{ordinal}.xml", slide_rel),
            )
            layout_color = ("AA1100", "1122CC", "008855")[ordinal - 1]
            archive.writestr(
                f"ppt/slideLayouts/slideLayout{ordinal}.xml",
                f'<p:sldLayout xmlns:p="urn:p" xmlns:a="urn:a"><a:srgbClr val="{layout_color}"/></p:sldLayout>',
            )
            archive.writestr(
                f"ppt/slideLayouts/_rels/slideLayout{ordinal}.xml.rels",
                _relationships("../slideMasters/slideMaster1.xml", master_rel),
            )
        archive.writestr(
            "ppt/slideMasters/slideMaster1.xml",
            '<p:sldMaster xmlns:p="urn:p" xmlns:a="urn:a"><a:srgbClr val="F0F0F0"/></p:sldMaster>',
        )
        archive.writestr(
            "ppt/slideMasters/_rels/slideMaster1.xml.rels",
            _relationships("../theme/theme1.xml", theme_rel),
        )
        archive.writestr(
            "ppt/theme/theme1.xml",
            '<a:theme xmlns:a="urn:a"><a:srgbClr val="223344"/><a:latin typeface="Aptos"/></a:theme>',
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_chart_package(
    path: Path,
    *,
    include_workbook: bool = True,
    duplicate_values: bool = False,
    formula_cell: bool = False,
    range_mismatch: bool = False,
    unsupported_reference: bool = False,
    empty_workbook: bool = False,
) -> str:
    slide_rel = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
    )
    chart_rel = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"
    )
    master_rel = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
    )
    theme_rel = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
    )
    package_rel = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/package"
    )
    slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr/>
    <p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>NORMAL TITLE</a:t></a:r></a:p></p:txBody>
    </p:sp>
    <p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="3" name="Chart 2"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>
      <p:xfrm><a:off x="0" y="0"/><a:ext cx="100" cy="100"/></p:xfrm>
      <a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart"><c:chart r:id="rId2"/></a:graphicData></a:graphic>
    </p:graphicFrame>
  </p:spTree></p:cSld>
</p:sld>"""
    category_formula = (
        "NamedCategory" if unsupported_reference else "Sheet1!$A$2:$A$3"
    )
    category_count = 3 if range_mismatch else 2
    second_category = (
        "SECRET_CHART_CATEGORY" if duplicate_values else "SECOND_CATEGORY"
    )
    chart_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
              xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">
  <c:chart><c:title><c:tx><c:rich><a:p><a:r><a:t>SECRET_CHART_TITLE</a:t></a:r></a:p></c:rich></c:tx></c:title>
    <c:plotArea><c:barChart><c:ser>
      <c:tx><c:strRef><c:f>Sheet1!$A$1</c:f><c:strCache><c:ptCount val="1"/>
        <c:pt idx="0"><c:v>SECRET_CHART_SERIES</c:v></c:pt>
      </c:strCache></c:strRef></c:tx>
      <c:cat><c:strRef><c:f>{category_formula}</c:f><c:strCache><c:ptCount val="{category_count}"/>
        <c:pt idx="0"><c:v>SECRET_CHART_CATEGORY</c:v></c:pt>
        <c:pt idx="1"><c:v>{second_category}</c:v></c:pt>
      </c:strCache></c:strRef></c:cat>
      <c:val><c:numRef><c:f>Sheet1!$B$2:$B$3</c:f><c:numCache><c:ptCount val="2"/>
        <c:pt idx="0"><c:v>424242</c:v></c:pt>
        <c:pt idx="1"><c:v>515151</c:v></c:pt>
      </c:numCache></c:numRef></c:val>
    </c:ser></c:barChart></c:plotArea>
  </c:chart>
</c:chartSpace>"""
    if empty_workbook:
        chart_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">
  <c:chart><c:plotArea/></c:chart>
</c:chartSpace>"""
    workbook_buffer = io.BytesIO()
    with zipfile.ZipFile(
        workbook_buffer, "w", compression=zipfile.ZIP_DEFLATED
    ) as workbook:
        workbook.writestr(
            "[Content_Types].xml",
            """<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>"""
            if not empty_workbook
            else """<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        )
        workbook.writestr(
            "_rels/.rels",
            """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        )
        workbook.writestr(
            "xl/workbook.xml",
            """<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>""",
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            ("""<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1"
 Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
 Target="worksheets/sheet1.xml"/></Relationships>"""
            if empty_workbook
            else """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1"
 Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
 Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2"
 Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings"
 Target="sharedStrings.xml"/></Relationships>"""),
        )
        if not empty_workbook:
            workbook.writestr(
                "xl/sharedStrings.xml",
                f"""<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<si><t>SECRET_CHART_SERIES</t></si><si><t>SECRET_CHART_CATEGORY</t></si>
<si><t>{second_category}</t></si></sst>""",
            )
        formula_xml = "<f>212121+212121</f>" if formula_cell else ""
        workbook.writestr(
            "xl/worksheets/sheet1.xml",
            (f"""<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetData><row r="1"><c r="A1" t="s"><v>0</v></c></row>
<row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2">{formula_xml}<v>424242</v></c></row>
<row r="3"><c r="A3" t="s"><v>2</v></c><c r="B3"><v>515151</v></c></row>
</sheetData></worksheet>"""
            if not empty_workbook
            else """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>"""),
        )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ppt/slides/slide1.xml", slide_xml)
        archive.writestr(
            "ppt/slides/_rels/slide1.xml.rels",
            f"""<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="{slide_rel}" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="{chart_rel}" Target="../charts/chart1.xml"/></Relationships>""",
        )
        archive.writestr("ppt/charts/chart1.xml", chart_xml)
        archive.writestr(
            "ppt/charts/_rels/chart1.xml.rels",
            f"""<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="{package_rel}" Target="../embeddings/book1.xlsx"/></Relationships>""",
        )
        if include_workbook:
            archive.writestr(
                "ppt/embeddings/book1.xlsx",
                workbook_buffer.getvalue(),
            )
        archive.writestr(
            "ppt/slideLayouts/slideLayout1.xml",
            '<p:sldLayout xmlns:p="urn:p"/>',
        )
        archive.writestr(
            "ppt/slideLayouts/_rels/slideLayout1.xml.rels",
            _relationships("../slideMasters/slideMaster1.xml", master_rel),
        )
        archive.writestr(
            "ppt/slideMasters/slideMaster1.xml",
            '<p:sldMaster xmlns:p="urn:p"/>',
        )
        archive.writestr(
            "ppt/slideMasters/_rels/slideMaster1.xml.rels",
            _relationships("../theme/theme1.xml", theme_rel),
        )
        archive.writestr(
            "ppt/theme/theme1.xml",
            '<a:theme xmlns:a="urn:a"><a:srgbClr val="223344"/><a:latin typeface="Aptos"/></a:theme>',
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _chart_private_root(
    tmp_path: Path,
    *,
    include_workbook: bool = True,
    duplicate_values: bool = False,
    formula_cell: bool = False,
    range_mismatch: bool = False,
    unsupported_reference: bool = False,
    empty_workbook: bool = False,
) -> Path:
    root = tmp_path / "private-chart"
    package_path = root / "sources" / "chart.pptx"
    package_path.parent.mkdir(parents=True)
    package_sha = _write_chart_package(
        package_path,
        include_workbook=include_workbook,
        duplicate_values=duplicate_values,
        formula_cell=formula_cell,
        range_mismatch=range_mismatch,
        unsupported_reference=unsupported_reference,
        empty_workbook=empty_workbook,
    )
    intelligence = root / "intelligence" / "gaojie"
    intelligence.mkdir(parents=True)
    (intelligence / "asset-index.json").write_text(
        json.dumps(
            {
                "packages": [
                    {
                        "package_sha256": package_sha,
                        "private_path": "sources/chart.pptx",
                        "status": "ACCEPTED",
                        "render_status": "PASS",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (intelligence / "certified-core.json").write_text(
        json.dumps(
            {
                "schema_version": "gaojie-certified-core.v2",
                "pages": [
                    {
                        "certification": "certified-private",
                        "package_sha256": package_sha,
                        "page_id": f"{package_sha}:001",
                        "slide_number": 1,
                        "page_role": "data",
                        "category_names": ["表格图表"],
                        "pool": "complete-layout",
                        "quality": 0.9,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return root


def _private_root(tmp_path: Path) -> Path:
    root = tmp_path / "private"
    package_path = root / "sources" / "catalog.pptx"
    package_path.parent.mkdir(parents=True)
    package_sha = _write_package(package_path)
    intelligence = root / "intelligence" / "gaojie"
    intelligence.mkdir(parents=True)
    (intelligence / "asset-index.json").write_text(
        json.dumps(
            {
                "packages": [
                    {
                        "package_sha256": package_sha,
                        "private_path": "sources/catalog.pptx",
                        "status": "ACCEPTED",
                        "render_status": "PASS",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    base = {
        "certification": "certified-private",
        "package_sha256": package_sha,
        "quality": 0.9,
    }
    pages = [
        {
            **base,
            "page_id": f"{package_sha}:001",
            "slide_number": 1,
            "page_role": "body",
            "category_names": ["一段内容"],
            "pool": "complete-layout",
        },
        {
            **base,
            "page_id": f"{package_sha}:002",
            "slide_number": 2,
            "page_role": "body",
            "category_names": ["样机展示"],
            "pool": "reference-only/brand-case",
            "decision": "reference-only",
            "direct_use": False,
            "auto_materialize": False,
        },
        {
            **base,
            "page_id": f"{package_sha}:003",
            "slide_number": 3,
            "page_role": "timeline",
            "category_names": ["时间轴图"],
            "pool": "component/framework-diagram",
        },
    ]
    (intelligence / "certified-core.json").write_text(
        json.dumps({"schema_version": "gaojie-certified-core.v2", "pages": pages}),
        encoding="utf-8",
    )
    return root


def test_compiler_reads_requested_slide_and_its_relationship_chain(tmp_path: Path) -> None:
    index = compile_page_templates(_private_root(tmp_path))
    by_slide = {item.slide_number: item for item in index.page_templates}

    assert "FIRST-SLIDE" in {
        slot["source_text"] for slot in by_slide[1].slot_graph["slots"]
    }
    assert "SECOND-SLIDE" in {
        slot["source_text"] for slot in by_slide[2].slot_graph["slots"]
    }
    assert "FIRST-SLIDE" not in {
        slot["source_text"] for slot in by_slide[2].slot_graph["slots"]
    }
    assert "#0000FF" in by_slide[2].theme_palette
    assert "#1122CC" in by_slide[2].theme_palette
    assert by_slide[2].structure["slide_relationship_count"] == 1
    assert by_slide[2].structure["linked_style_part_count"] == 3


def test_reference_inventory_covers_charts_workbooks_and_table_cells() -> None:
    reference_path = (
        SKILL_ROOT
        / "design-packs"
        / "institutional-annual-editorial"
        / "template.pptx"
    )
    index = compile_reference_deck(reference_path)
    by_slide = {item.slide_number: item for item in index.page_templates}

    expected_kind_counts = {
        5: {"chart-value": 11, "workbook-cell": 11},
        6: {"chart-value": 25, "workbook-cell": 27},
        7: {"table-cell": 27},
    }
    for ordinal, expected in expected_kind_counts.items():
        inventory = by_slide[ordinal].governed_content_inventory
        assert inventory["peer_mapping_method"] == "chart-formula-range-v1"
        observed: dict[str, int] = {}
        for slot in inventory["slots"]:
            observed[slot["kind"]] = observed.get(slot["kind"], 0) + 1
        assert inventory["policy"] == "locked-authority-required"
        assert inventory["complete"] is True
        assert observed == expected
        assert inventory["content_slot_count"] == sum(expected.values())

    assert by_slide[7].governed_content_inventory["closure_metadata"][
        "table_count"
    ] == 1
    assert by_slide[5].governed_content_inventory["closure_metadata"][
        "workbook_part_count"
    ] == 1
    assert by_slide[6].governed_content_inventory["closure_metadata"][
        "workbook_part_count"
    ] == 3

    for ordinal in (5, 6):
        slots = by_slide[ordinal].governed_content_inventory["slots"]
        chart_peers = {
            slot["peer_group_id"]
            for slot in slots
            if slot["kind"] == "chart-value" and slot["peer_group_id"]
        }
        workbook_peers = {
            slot["peer_group_id"]
            for slot in slots
            if slot["kind"] == "workbook-cell" and slot["peer_group_id"]
        }
        assert chart_peers
        assert chart_peers == workbook_peers
        expected_peer_count = 11 if ordinal == 5 else 25
        assert len(chart_peers) == expected_peer_count
        peer_members = {
            peer_id: [
                slot for slot in slots if slot["peer_group_id"] == peer_id
            ]
            for peer_id in chart_peers
        }
        assert all(
            sorted(member["kind"] for member in members)
            == ["chart-value", "workbook-cell"]
            for members in peer_members.values()
        )
        assert all(
            len(members) == 2
            and members[0]["cell_ref"] == members[1]["cell_ref"]
            and members[0]["worksheet_ordinal"] == members[1]["worksheet_ordinal"]
            and members[0]["semantic_role"] == members[1]["semantic_role"]
            for members in peer_members.values()
        )

    slide_six_slots = by_slide[6].governed_content_inventory["slots"]
    assert sum(
        slot["kind"] == "workbook-cell" and slot["peer_group_id"] is None
        for slot in slide_six_slots
    ) == 2

    for ordinal, template in by_slide.items():
        metadata = template.governed_content_inventory["closure_metadata"]
        assert metadata["notes_part_count"] == 0
        assert metadata["comment_part_count"] == 0
        assert metadata["diagram_part_count"] == 0
        if ordinal not in (5, 6, 7):
            assert template.governed_content_inventory["policy"] == "no-embedded-content"
            assert template.governed_content_inventory["slots"] == []


def test_synthetic_chart_secret_is_inventoried_peered_and_publicly_redacted(
    tmp_path: Path,
) -> None:
    root = _chart_private_root(tmp_path)
    index = compile_page_templates(root)
    assert index.to_dict() == compile_page_templates(root).to_dict()
    template = index.page_templates[0]
    inventory = template.governed_content_inventory

    assert inventory["complete"] is True
    assert inventory["peer_mapping_method"] == "chart-formula-range-v1"
    assert inventory["policy"] == "locked-authority-required"
    assert {slot["kind"] for slot in inventory["slots"]} == {
        "chart-text",
        "chart-value",
        "workbook-cell",
    }
    assert any(
        slot["source_text"] == "SECRET_CHART_TITLE"
        for slot in inventory["slots"]
    )
    chart_peers = {
        slot["peer_group_id"]
        for slot in inventory["slots"]
        if slot["kind"] == "chart-value" and slot["peer_group_id"]
    }
    workbook_peers = {
        slot["peer_group_id"]
        for slot in inventory["slots"]
        if slot["kind"] == "workbook-cell" and slot["peer_group_id"]
    }
    assert len(chart_peers) == 5
    assert chart_peers == workbook_peers
    for peer_id in chart_peers:
        members = [
            slot for slot in inventory["slots"] if slot["peer_group_id"] == peer_id
        ]
        assert len(members) == 2
        assert {member["kind"] for member in members} == {
            "chart-value",
            "workbook-cell",
        }
        assert len({member["cell_ref"] for member in members}) == 1
        assert len({member["worksheet_ordinal"] for member in members}) == 1
        assert len({member["semantic_role"] for member in members}) == 1
        assert members[0]["series_index"] == members[1]["series_index"] == 0
        assert members[0]["point_index"] == members[1]["point_index"]
    chart_coordinates = {
        (slot["semantic_role"], slot["point_index"]): slot["cell_ref"]
        for slot in inventory["slots"]
        if slot["kind"] == "chart-value"
    }
    assert chart_coordinates == {
        ("series-name", 0): "A1",
        ("category", 0): "A2",
        ("category", 1): "A3",
        ("value", 0): "B2",
        ("value", 1): "B3",
    }

    candidate = query_page_template_candidates(
        index,
        role="data",
        style_cluster=template.style_cluster_id,
        limit=1,
    )[0].to_dict()
    public_inventory = candidate["page_template"]["governed_content_inventory"]
    assert all(slot["source_text"] == "" for slot in public_inventory["slots"])
    serialized = json.dumps(candidate, ensure_ascii=False)
    assert "SECRET_CHART_TITLE" not in serialized
    assert "SECRET_CHART_SERIES" not in serialized
    assert all(slot["source_text_sha256"] for slot in public_inventory["slots"])
    assert all("worksheet_name" not in slot for slot in public_inventory["slots"])
    assert all(
        {
            "semantic_role",
            "series_index",
            "point_index",
            "worksheet_ordinal",
            "cell_ref",
            "value_type",
        }.issubset(slot)
        for slot in public_inventory["slots"]
    )
    assert any(slot["cell_ref"] == "B2" for slot in public_inventory["slots"])


def test_chart_peer_compilation_fails_closed_on_ambiguous_or_unsupported_data(
    tmp_path: Path,
) -> None:
    cases = (
        ("duplicate", {"duplicate_values": True}, "chart-cache-duplicate-value"),
        (
            "formula",
            {"formula_cell": True},
            "workbook-security-workbook-formula-forbidden",
        ),
        ("range", {"range_mismatch": True}, "chart-reference-point-count-mismatch"),
        ("unsupported", {"unsupported_reference": True}, "chart-reference-unsupported"),
    )
    for label, options, expected_error in cases:
        index = compile_page_templates(
            _chart_private_root(tmp_path / label, **options)
        )
        template = index.page_templates[0]
        inventory = template.governed_content_inventory
        assert inventory["complete"] is False
        assert template.direct_use is False
        assert any(
            error.startswith(expected_error) for error in inventory["scan_errors"]
        )


def test_incomplete_chart_workbook_inventory_disables_direct_use(tmp_path: Path) -> None:
    index = compile_page_templates(
        _chart_private_root(tmp_path, include_workbook=False)
    )
    template = index.page_templates[0]

    assert template.governed_content_inventory["complete"] is False
    assert template.governed_content_inventory["scan_errors"]
    assert template.direct_use is False
    assert template.eligibility_known is True


def test_empty_reachable_workbook_is_never_classified_as_no_embedded_content(
    tmp_path: Path,
) -> None:
    index = compile_page_templates(
        _chart_private_root(tmp_path, empty_workbook=True)
    )
    template = index.page_templates[0]
    inventory = template.governed_content_inventory

    assert inventory["closure_metadata"]["workbook_part_count"] == 1
    assert inventory["policy"] == "locked-authority-required"
    assert inventory["complete"] is False
    assert "workbook-present-without-governed-slots" in inventory["scan_errors"]
    assert template.direct_use is False


def test_compiler_rejects_malformed_nested_workbook_root_relationship(
    tmp_path: Path,
) -> None:
    root = _chart_private_root(tmp_path)
    package_path = root / "sources" / "chart.pptx"
    with zipfile.ZipFile(package_path, "r") as archive:
        package_parts = {name: archive.read(name) for name in archive.namelist()}
    workbook_name = "ppt/embeddings/book1.xlsx"
    with zipfile.ZipFile(io.BytesIO(package_parts[workbook_name]), "r") as archive:
        workbook_parts = {name: archive.read(name) for name in archive.namelist()}
    workbook_parts["_rels/.rels"] = b"""<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/worksheets/sheet1.xml"/>
</Relationships>"""
    corrupted_workbook = io.BytesIO()
    with zipfile.ZipFile(
        corrupted_workbook,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for name in sorted(workbook_parts):
            archive.writestr(name, workbook_parts[name])
    package_parts[workbook_name] = corrupted_workbook.getvalue()
    with zipfile.ZipFile(
        package_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for name in sorted(package_parts):
            archive.writestr(name, package_parts[name])

    # The package identity is part of the private manifest, so refresh it after
    # corrupting the nested workbook while retaining the same certification row.
    asset_index_path = root / "intelligence" / "gaojie" / "asset-index.json"
    asset_index = json.loads(asset_index_path.read_text(encoding="utf-8"))
    package_sha = hashlib.sha256(package_path.read_bytes()).hexdigest()
    asset_index["packages"][0]["package_sha256"] = package_sha
    asset_index_path.write_text(json.dumps(asset_index), encoding="utf-8")
    certified_path = root / "intelligence" / "gaojie" / "certified-core.json"
    certified = json.loads(certified_path.read_text(encoding="utf-8"))
    certified["pages"][0]["package_sha256"] = package_sha
    certified_path.write_text(json.dumps(certified), encoding="utf-8")

    template = compile_page_templates(root).page_templates[0]

    assert template.governed_content_inventory["complete"] is False
    assert any(
        error.startswith("workbook-security-")
        for error in template.governed_content_inventory["scan_errors"]
    )
    assert template.direct_use is False


def test_compiler_preserves_direct_use_eligibility_and_query_is_safe_by_default(
    tmp_path: Path,
) -> None:
    index = compile_page_templates(_private_root(tmp_path))
    by_slide = {item.slide_number: item for item in index.page_templates}

    assert by_slide[1].pool == "complete-layout"
    assert by_slide[1].decision is None
    assert by_slide[1].direct_use is True
    assert by_slide[2].pool == "reference-only/brand-case"
    assert by_slide[2].decision == "reference-only"
    assert by_slide[2].direct_use is False

    default_results = query_page_templates(index, role="body", limit=10)
    assert [item.slide_number for item in default_results] == [1]
    fallback_results = query_page_templates(index, role="cover", limit=10)
    assert fallback_results
    assert all(item.direct_use for item in fallback_results)
    assert all(item.decision != "reference-only" for item in fallback_results)

    review_results = query_page_templates(
        index,
        role="body",
        style_cluster="optimistic-technical-stage",
        limit=10,
        direct_use_only=False,
    )
    assert [item.slide_number for item in review_results] == [2]


def test_style_features_and_clusters_are_meaningful_and_deterministic(tmp_path: Path) -> None:
    root = _private_root(tmp_path)
    first = compile_page_templates(root)
    second = compile_page_templates(root)

    assert first.to_dict() == second.to_dict()
    assert first.compiled_at == "1970-01-01T00:00:00Z"

    first_projection = [
        (item.page_id, item.style_cluster_id, dict(item.style_features))
        for item in first.page_templates
    ]
    second_projection = [
        (item.page_id, item.style_cluster_id, dict(item.style_features))
        for item in second.page_templates
    ]
    assert first_projection == second_projection
    assert len({item.style_cluster_id for item in first.page_templates}) >= 2
    assert first.style_cluster_index == second.style_cluster_index
    assert first.dominant_style_cluster_id in first.style_cluster_index
    assert all(item.style_features["tone"] in {"dark", "mid", "light"} for item in first.page_templates)
    assert all(item.style_features["accent_family"] for item in first.page_templates)


def test_old_v4_index_without_new_fields_remains_loadable(tmp_path: Path) -> None:
    index = compile_page_templates(_private_root(tmp_path))
    payload = index.to_dict()
    for item in payload["page_templates"]:
        item.pop("pool", None)
        item.pop("decision", None)
        item.pop("direct_use", None)
        item.pop("eligibility_known", None)
        item.pop("style_features", None)
        item.pop("governed_content_inventory", None)
    path = tmp_path / "old-index.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_library_index(path)
    assert all(not item.direct_use for item in loaded.page_templates)
    assert all(not item.eligibility_known for item in loaded.page_templates)
    assert all(item.pool is None for item in loaded.page_templates)
    assert all(item.style_features == {} for item in loaded.page_templates)
    assert all(
        item.governed_content_inventory["complete"] is False
        for item in loaded.page_templates
    )
    assert query_page_templates(loaded, role="body", limit=10) == ()

    evidence = query_page_template_candidates(
        loaded,
        role="body",
        limit=10,
        include_ineligible=True,
    )
    assert evidence
    assert all(not candidate.eligibility for candidate in evidence)
    assert all("eligibility_unknown" in candidate.reasons for candidate in evidence)


def test_loader_fails_closed_on_malformed_governed_inventory(tmp_path: Path) -> None:
    payload = compile_page_templates(_private_root(tmp_path)).to_dict()
    payload["page_templates"][0]["governed_content_inventory"][
        "content_slot_count"
    ] = 999
    path = tmp_path / "malformed-inventory.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_library_index(path)
    affected = next(
        item
        for item in loaded.page_templates
        if item.page_id == payload["page_templates"][0]["page_id"]
    )
    assert affected.direct_use is False
    assert affected.eligibility_known is False
    assert affected.governed_content_inventory["scan_errors"] == [
        "inventory-missing"
    ]


def test_new_fields_survive_index_round_trip(tmp_path: Path) -> None:
    index = compile_page_templates(_private_root(tmp_path))
    output = tmp_path / "library.json"
    write_library_index(index, output)
    loaded = load_library_index(output)

    assert [item.to_dict() for item in loaded.page_templates] == [
        item.to_dict() for item in index.page_templates
    ]


def test_library_schema_accepts_core_and_reference_outputs(tmp_path: Path) -> None:
    jsonschema = __import__("pytest").importorskip("jsonschema")
    schema_root = SKILL_ROOT / "schemas"
    schema = json.loads(
        (schema_root / "template-library-index.v4.schema.json").read_text()
    )
    page_schema = json.loads(
        (schema_root / "page-template.v1.schema.json").read_text()
    )
    # Resolve local $refs through the validator's legacy resolver because the
    # repository schemas intentionally use sibling relative identifiers.
    resolver = jsonschema.RefResolver(
        base_uri=schema_root.as_uri() + "/",
        referrer=schema,
        store={page_schema["$id"]: page_schema},
    )
    validator = jsonschema.Draft202012Validator(schema, resolver=resolver)
    validator.validate(compile_page_templates(_private_root(tmp_path)).to_dict())

    reference_path = (
        SKILL_ROOT
        / "design-packs"
        / "institutional-annual-editorial"
        / "template.pptx"
    )
    assert reference_path.is_file()
    validator.validate(compile_reference_deck(reference_path).to_dict())


def test_library_loader_rejects_modified_score_contract(tmp_path: Path) -> None:
    payload = compile_page_templates(_private_root(tmp_path)).to_dict()
    payload["scoring"]["role"] = 0.29
    path = tmp_path / "modified-scoring.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        load_library_index(path)
    except PageTemplateError as exc:
        assert "frozen v6.1 weights" in str(exc)
    else:  # pragma: no cover - protects fail-closed behavior
        raise AssertionError("modified scoring contract was accepted")


def test_candidate_score_uses_exact_frozen_weight_math(tmp_path: Path) -> None:
    index = compile_page_templates(_private_root(tmp_path))
    template = next(item for item in index.page_templates if item.slide_number == 1)
    budget = int(template.capacity["max_text_chars"]) * 2

    candidate = query_page_template_candidates(
        index,
        role="body",
        capacity_budget=budget,
        semantic_categories=("一段内容",),
        style_cluster=template.style_cluster_id,
        limit=1,
        allow_fallback=False,
        include_ineligible=True,
    )[0]

    assert candidate.scores.role == 1.0
    assert candidate.scores.capacity == 0.5
    assert candidate.scores.semantic == 1.0
    assert candidate.scores.style == 1.0
    assert candidate.scores.editability == 1.0
    assert candidate.capacity_fit is False
    assert candidate.eligibility is False
    assert "capacity_insufficient" in candidate.reasons
    expected = round(
        1.0 * DEFAULT_SCORING["role"]
        + 0.5 * DEFAULT_SCORING["capacity"]
        + 1.0 * DEFAULT_SCORING["semantic"]
        + 1.0 * DEFAULT_SCORING["style"]
        + 1.0 * DEFAULT_SCORING["editability"],
        6,
    )
    assert expected == 0.875
    assert candidate.scores.total == expected


def test_query_candidate_view_redacts_private_locator_and_source_copy(tmp_path: Path) -> None:
    index = compile_page_templates(_private_root(tmp_path))
    candidate = query_page_template_candidates(
        index,
        role="body",
        style_cluster=index.page_templates[0].style_cluster_id,
        limit=1,
        include_ineligible=True,
    )[0].to_dict()

    page = candidate["page_template"]
    assert page["source_path"].startswith("private://")
    assert str(tmp_path) not in page["source_path"]
    assert all(
        slot["source_text"] == ""
        for slot in page["slot_graph"]["slots"]
    )
    assert all(
        slot["source_text"] == ""
        for slot in page["governed_content_inventory"]["slots"]
    )


def test_candidate_serialization_is_stable_and_cli_exposes_evidence(
    tmp_path: Path,
) -> None:
    index = compile_page_templates(_private_root(tmp_path))
    candidates = query_page_template_candidates(index, role="body", limit=10)
    first = serialize_page_template_candidates(candidates)
    second = serialize_page_template_candidates(candidates)
    assert first == second
    assert json.loads(first)["candidates"][0]["scores"]["total"] >= 0

    library_path = tmp_path / "library-v4.json"
    write_library_index(index, library_path)
    result = run_library_cli(
        [
            "query-pages",
            "--library",
            str(library_path),
            "--role",
            "body",
            "--limit",
            "10",
        ]
    )
    assert result["schema_version"] == "page-template-query-result.v1"
    assert result["weights"] == dict(DEFAULT_SCORING)
    assert result["candidates"]
    evidence = result["candidates"][0]
    assert evidence["eligibility"] is True
    assert set(evidence["scores"]) == {
        "role",
        "capacity",
        "semantic",
        "style",
        "editability",
        "total",
    }
    assert "asset_fit" in evidence
    assert "capacity_fit" in evidence

    jsonschema = __import__("pytest").importorskip("jsonschema")
    schema_root = SKILL_ROOT / "schemas"
    query_schema = json.loads(
        (schema_root / "page-template-query-result.v1.schema.json").read_text()
    )
    candidate_schema = json.loads(
        (schema_root / "page-template-candidate.v1.schema.json").read_text()
    )
    page_schema = json.loads(
        (schema_root / "page-template.v1.schema.json").read_text()
    )
    resolver = jsonschema.RefResolver(
        base_uri=schema_root.as_uri() + "/",
        referrer=query_schema,
        store={
            candidate_schema["$id"]: candidate_schema,
            page_schema["$id"]: page_schema,
        },
    )
    jsonschema.Draft202012Validator(
        query_schema,
        resolver=resolver,
    ).validate(result)
    assert "residue_risk" in evidence
    assert "style_compatibility" in evidence


def test_relative_library_and_batch_query_bundle_use_private_root(
    tmp_path: Path,
) -> None:
    root = _private_root(tmp_path)
    index = compile_page_templates(root)
    library_path = root / "v61" / "library-v4.json"
    write_library_index(index, library_path)

    single = run_library_cli(
        [
            "query-pages",
            "--private-root",
            str(root),
            "--library",
            "v61/library-v4.json",
            "--role",
            "body",
            "--capacity-budget",
            "1",
        ]
    )
    assert single["library_resolution_source"] == "explicit-private-root"
    assert single["candidates"]

    request_path = tmp_path / "query-request.json"
    request_path.write_text(
        json.dumps(
            {
                "schema_version": "page-template-query-request.v1",
                "slides": [
                    {
                        "target_ordinal": 2,
                        "query_id": "timeline",
                        "role": "timeline",
                        "capacity_budget": 1,
                        "required_source_ordinal": 3,
                        "style_cluster": "research-editorial-evidence",
                        "limit": 3,
                        "allow_fallback": True,
                    },
                    {
                        "target_ordinal": 1,
                        "query_id": "body",
                        "role": "body",
                        "capacity_budget": 1,
                        "semantic_categories": ["一段内容"],
                        "limit": 3,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    output = tmp_path / "template-query-results.v1.json"
    first = run_library_cli(
        [
            "query-bundle",
            "--private-root",
            str(root),
            "--library",
            "v61/library-v4.json",
            "--query-request",
            str(request_path),
            "--output",
            str(output),
        ]
    )
    first_bytes = output.read_bytes()
    second = run_library_cli(
        [
            "query-bundle",
            "--private-root",
            str(root),
            "--library",
            "v61/library-v4.json",
            "--query-request",
            str(request_path),
            "--output",
            str(output),
        ]
    )
    assert first == second
    assert output.read_bytes() == first_bytes
    assert [item["target_ordinal"] for item in first["queries"]] == [1, 2]
    assert first["query_count"] == 2
    assert first["library_resolution_source"] == "explicit-private-root"
    timeline_result = first["queries"][1]["result"]
    assert timeline_result["required_source_ordinal"] == 3
    assert {
        candidate["page_template"]["slide_number"]
        for candidate in timeline_result["candidates"]
    } == {3}
    serialized = output.read_text(encoding="utf-8")
    assert str(root) not in serialized
    for query in first["queries"]:
        for candidate in query["result"]["candidates"]:
            assert candidate["page_template"]["source_path"].startswith("private://")
            assert all(
                slot["source_text"] == ""
                for slot in candidate["page_template"]["slot_graph"]["slots"]
            )
            assert all(
                slot["source_text"] == ""
                for slot in candidate["page_template"][
                    "governed_content_inventory"
                ]["slots"]
            )

    jsonschema = __import__("pytest").importorskip("jsonschema")
    schema_root = SKILL_ROOT / "schemas"
    bundle_schema = json.loads(
        (schema_root / "page-template-query-bundle.v1.schema.json").read_text()
    )
    query_schema = json.loads(
        (schema_root / "page-template-query-result.v1.schema.json").read_text()
    )
    candidate_schema = json.loads(
        (schema_root / "page-template-candidate.v1.schema.json").read_text()
    )
    page_schema = json.loads(
        (schema_root / "page-template.v1.schema.json").read_text()
    )
    resolver = jsonschema.RefResolver(
        base_uri=schema_root.as_uri() + "/",
        referrer=bundle_schema,
        store={
            query_schema["$id"]: query_schema,
            candidate_schema["$id"]: candidate_schema,
            page_schema["$id"]: page_schema,
        },
    )
    jsonschema.Draft202012Validator(
        bundle_schema,
        resolver=resolver,
    ).validate(first)


def test_query_bundle_required_source_ordinal_fails_closed_without_match(
    tmp_path: Path,
) -> None:
    root = _private_root(tmp_path)
    library_path = root / "v61" / "library-v4.json"
    write_library_index(compile_page_templates(root), library_path)
    request_path = tmp_path / "query-request.json"
    request_path.write_text(
        json.dumps(
            {
                "schema_version": "page-template-query-request.v1",
                "slides": [
                    {
                        "target_ordinal": 1,
                        "role": "body",
                        "capacity_budget": 1,
                        # Slide 2 is intentionally reference-only in this
                        # fixture, so it cannot satisfy a production query.
                        "required_source_ordinal": 2,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    import pytest

    with pytest.raises(
        SystemExit,
        match="required_source_ordinal=2",
    ):
        run_library_cli(
            [
                "query-bundle",
                "--private-root",
                str(root),
                "--library",
                "v61/library-v4.json",
                "--query-request",
                str(request_path),
                "--output",
                str(tmp_path / "bundle.json"),
            ]
        )
    assert not (tmp_path / "bundle.json").exists()


def test_query_request_rejects_nonpositive_required_source_ordinal(
    tmp_path: Path,
) -> None:
    root = _private_root(tmp_path)
    library_path = root / "v61" / "library-v4.json"
    write_library_index(compile_page_templates(root), library_path)
    request_path = tmp_path / "query-request.json"
    request_path.write_text(
        json.dumps(
            {
                "schema_version": "page-template-query-request.v1",
                "slides": [
                    {
                        "target_ordinal": 1,
                        "role": "body",
                        "capacity_budget": 1,
                        "required_source_ordinal": 0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    import pytest

    with pytest.raises(SystemExit, match="schema validation failed"):
        run_library_cli(
            [
                "query-bundle",
                "--private-root",
                str(root),
                "--library",
                "v61/library-v4.json",
                "--query-request",
                str(request_path),
                "--output",
                str(tmp_path / "bundle.json"),
            ]
        )


def test_query_bundle_rejects_duplicate_ordinals(tmp_path: Path) -> None:
    root = _private_root(tmp_path)
    library_path = root / "v61" / "library-v4.json"
    write_library_index(compile_page_templates(root), library_path)
    request_path = tmp_path / "duplicate-query-request.json"
    request_path.write_text(
        json.dumps(
            {
                "schema_version": "page-template-query-request.v1",
                "slides": [
                    {"target_ordinal": 1, "role": "body", "capacity_budget": 1},
                    {"target_ordinal": 1, "role": "timeline", "capacity_budget": 1},
                ],
            }
        ),
        encoding="utf-8",
    )
    import pytest

    with pytest.raises(SystemExit, match="duplicate target_ordinal"):
        run_library_cli(
            [
                "query-bundle",
                "--private-root",
                str(root),
                "--library",
                "v61/library-v4.json",
                "--query-request",
                str(request_path),
                "--output",
                str(tmp_path / "bundle.json"),
            ]
        )


def test_asset_fit_and_residue_risk_are_fail_closed_gates(tmp_path: Path) -> None:
    index = compile_page_templates(_private_root(tmp_path))
    missing_asset = query_page_template_candidates(
        index,
        role="body",
        style_cluster=index.dominant_style_cluster_id,
        asset_requirements=("chart",),
        limit=20,
        include_ineligible=True,
    )
    body = next(
        candidate
        for candidate in missing_asset
        if candidate.page_template.slide_number == 1
    )
    assert body.asset_fit == 0.0
    assert body.scores.editability == 0.0
    assert body.eligibility is False
    assert "asset_fit_incomplete" in body.reasons

    original = next(item for item in index.page_templates if item.slide_number == 1)
    risky_slot_graph = dict(original.slot_graph)
    risky_slot_graph["slots"] = [
        {
            "slot_id": "shape_2",
            "shape_id": 2,
            "kind": "title",
            "max_chars": 1200,
            "source_text": "Brand logo " * 100,
        }
    ]
    risky = replace(original, slot_graph=risky_slot_graph)
    risky_index = replace(
        index,
        page_templates=tuple(
            risky if item.page_id == original.page_id else item
            for item in index.page_templates
        ),
    )
    residue_results = query_page_template_candidates(
        risky_index,
        role="body",
        limit=20,
        include_ineligible=True,
    )
    rejected = next(
        candidate
        for candidate in residue_results
        if candidate.page_template.page_id == risky.page_id
    )
    assert rejected.residue_risk >= 0.65
    assert rejected.eligibility is False
    assert "residue_risk_high" in rejected.reasons


def test_cross_cluster_fallback_requires_explicit_registration(tmp_path: Path) -> None:
    index = compile_page_templates(_private_root(tmp_path))
    timeline = next(item for item in index.page_templates if item.page_role == "timeline")
    requested_style = index.dominant_style_cluster_id
    assert timeline.style_cluster_id != requested_style

    blocked = query_page_template_candidates(
        index,
        role="timeline",
        style_cluster=requested_style,
        limit=20,
        include_ineligible=True,
    )
    blocked_timeline = next(
        candidate
        for candidate in blocked
        if candidate.page_template.page_id == timeline.page_id
    )
    assert blocked_timeline.style_compatibility == "incompatible"
    assert blocked_timeline.eligibility is False
    assert "style_incompatible" in blocked_timeline.reasons
    assert query_page_templates(
        index,
        role="timeline",
        style_cluster=requested_style,
        limit=10,
    ) == ()

    registered = replace(
        index,
        compatible_style_cluster_ids=(requested_style, timeline.style_cluster_id),
    )
    allowed = query_page_template_candidates(
        registered,
        role="timeline",
        style_cluster=requested_style,
        limit=10,
    )
    assert len(allowed) == 1
    assert allowed[0].page_template.page_id == timeline.page_id
    assert allowed[0].style_compatibility == "registered"
    assert allowed[0].scores.style == 0.5
    assert allowed[0].fallback_reason == "style:registered_compatible_cluster"
