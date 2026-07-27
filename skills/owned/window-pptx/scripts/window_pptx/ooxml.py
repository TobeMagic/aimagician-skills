"""Deterministic OOXML packaging and RenderPlan semantic inspection."""

from __future__ import annotations

import io
import hashlib
import json
import os
import posixpath
import re
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Iterable
from xml.etree import ElementTree as ET

from .render_plan import (
    ChartSpec,
    DiagramSpec,
    RenderObject,
    RenderPlan,
    RenderSlide,
    TableSpec,
    validate_render_plan,
)
from .transaction import validate_ooxml_package


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rels": "http://schemas.openxmlformats.org/package/2006/relationships",
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "types": "http://schemas.openxmlformats.org/package/2006/content-types",
}
R_ID = f"{{{NS['r']}}}id"
R_EMBED = f"{{{NS['r']}}}embed"
REL_ID = "Id"
FIXED_CORE_TIME = "2000-01-01T00:00:00Z"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
IDENTITY_PATTERN = re.compile(
    r"(?:^|;)window-pptx:id=(?P<id>[^;]+);"
    r"kind=(?P<kind>[^;]+);component=(?P<component>[^;]+);"
    r"editable=(?P<editable>true|false)(?:;group=(?P<group>[^;]*))?(?:;|$)"
)
_BOLD_COMPONENTS = {
    "title",
    "card",
    "kpi",
    "comparison-panel",
    "risk-panel",
    "recommendation-panel",
    "team-member",
    "cta",
    "process-step",
    "timeline-node",
    "matrix-cell",
    "diagram-node",
}
_ELEVATED_SHAPE_COMPONENTS = {
    "card",
    "kpi",
    "comparison-panel",
    "risk-panel",
    "recommendation-panel",
    "team-member",
    "quote",
    "process-step",
    "timeline-node",
    "matrix-cell",
}


class OoxmlSemanticError(ValueError):
    """The candidate package does not preserve its authoritative RenderPlan."""


@dataclass(frozen=True)
class OoxmlSemanticReport:
    slide_count: int
    object_ids: tuple[str, ...]
    chart_count: int
    table_count: int
    diagram_count: int
    notes_count: int
    hyperlink_count: int
    part_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "slide_count": self.slide_count,
            "object_ids": list(self.object_ids),
            "chart_count": self.chart_count,
            "table_count": self.table_count,
            "diagram_count": self.diagram_count,
            "notes_count": self.notes_count,
            "hyperlink_count": self.hyperlink_count,
            "part_count": self.part_count,
        }


@dataclass(frozen=True)
class _Relationship:
    rel_id: str
    rel_type: str
    target: str
    external: bool


def _xml(data: bytes, part: str) -> ET.Element:
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise OoxmlSemanticError(f"XML_MALFORMED: {part}: {exc}") from exc


def _safe_part_names(names: Iterable[str]) -> tuple[str, ...]:
    result = tuple(names)
    if len(result) != len(set(result)):
        raise OoxmlSemanticError("PACKAGE_DUPLICATE_PART: duplicate ZIP entry")
    for name in result:
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts or "\\" in name:
            raise OoxmlSemanticError(f"PACKAGE_UNSAFE_PART: {name}")
    return result


def _rels_part(part: str) -> str:
    directory, filename = posixpath.split(part)
    return posixpath.join(directory, "_rels", f"{filename}.rels")


def _resolve_target(source_part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target))


def _relationships(
    package: zipfile.ZipFile,
    names: set[str],
    source_part: str,
) -> dict[str, _Relationship]:
    rels_part = _rels_part(source_part)
    if rels_part not in names:
        return {}
    root = _xml(package.read(rels_part), rels_part)
    result: dict[str, _Relationship] = {}
    for element in root.findall("rels:Relationship", NS):
        rel_id = element.attrib.get("Id", "")
        if not rel_id or rel_id in result:
            raise OoxmlSemanticError(
                f"RELATIONSHIP_ID_INVALID: {rels_part}: {rel_id!r}"
            )
        external = element.attrib.get("TargetMode") == "External"
        target = element.attrib.get("Target", "")
        resolved = target if external else _resolve_target(source_part, target)
        if not external and resolved not in names:
            raise OoxmlSemanticError(
                f"RELATIONSHIP_TARGET_MISSING: {source_part}:{rel_id}->{resolved}"
            )
        result[rel_id] = _Relationship(
            rel_id,
            element.attrib.get("Type", ""),
            resolved,
            external,
        )
    return result


def _source_part_for_relationships(rels_part: str) -> str:
    if rels_part == "_rels/.rels":
        return ""
    directory, filename = posixpath.split(rels_part)
    if not directory.endswith("/_rels") or not filename.endswith(".rels"):
        raise OoxmlSemanticError(f"RELATIONSHIP_PART_INVALID: {rels_part}")
    return posixpath.join(directory.removesuffix("/_rels"), filename.removesuffix(".rels"))


def _assert_relationship_graph(package: zipfile.ZipFile, names: set[str]) -> None:
    for rels_part in sorted(
        name for name in names if name == "_rels/.rels" or "/_rels/" in name
    ):
        if not rels_part.endswith(".rels"):
            continue
        source_part = _source_part_for_relationships(rels_part)
        if source_part and source_part not in names:
            raise OoxmlSemanticError(
                f"RELATIONSHIP_SOURCE_MISSING: {rels_part}->{source_part}"
            )
        _relationships(package, names, source_part)


def _normalized_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _missing_semantic_tokens(expected: Iterable[object], actual_text: str) -> list[str]:
    normalized = _normalized_text(actual_text)
    actual_scalars = normalized.split()
    missing: list[str] = []
    for value in expected:
        token = _normalized_text(str(value))
        if token in normalized:
            continue
        try:
            numeric = float(token)
        except ValueError:
            missing.append(token)
            continue
        if not any(
            _numeric_token == numeric
            for actual in actual_scalars
            for _numeric_token in (
                [float(actual)]
                if re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", actual)
                else []
            )
        ):
            missing.append(token)
    return missing


def _object_nodes(slide_root: ET.Element) -> dict[str, ET.Element]:
    result: dict[str, ET.Element] = {}
    for tag in ("sp", "pic", "graphicFrame", "grpSp"):
        for node in slide_root.findall(f".//p:{tag}", NS):
            c_nv_pr = node.find(".//p:cNvPr", NS)
            if c_nv_pr is None:
                continue
            name = c_nv_pr.attrib.get("name", "")
            if name and name not in result:
                result[name] = node
    return result


def _ordered_object_names(slide_root: ET.Element) -> tuple[str, ...]:
    tree = slide_root.find(".//p:spTree", NS)
    if tree is None:
        raise OoxmlSemanticError("SLIDE_SHAPE_TREE_MISSING")
    names: list[str] = []
    for node in list(tree):
        c_nv_pr = node.find(".//p:cNvPr", NS)
        name = c_nv_pr.attrib.get("name", "") if c_nv_pr is not None else ""
        if name:
            names.append(name)
    return tuple(names)


def _identity(node: ET.Element) -> tuple[str, str, str, str] | None:
    c_nv_pr = node.find(".//p:cNvPr", NS)
    if c_nv_pr is None:
        return None
    description = c_nv_pr.attrib.get("descr", "")
    match = IDENTITY_PATTERN.search(description)
    if match is None:
        return None
    if match.group("editable") != "true":
        return None
    return (
        match.group("id"),
        match.group("kind"),
        match.group("component"),
        match.group("group") or "",
    )


def _assert_content_types(package: zipfile.ZipFile, names: set[str]) -> None:
    root = _xml(package.read("[Content_Types].xml"), "[Content_Types].xml")
    defaults = {
        element.attrib.get("Extension", "").casefold()
        for element in root.findall("types:Default", NS)
    }
    overrides = {
        element.attrib.get("PartName", "").lstrip("/"): element.attrib.get(
            "ContentType", ""
        )
        for element in root.findall("types:Override", NS)
    }
    for part in sorted(names):
        if part.endswith("/") or part in {"[Content_Types].xml"}:
            continue
        extension = PurePosixPath(part).suffix.lstrip(".").casefold()
        if part not in overrides and extension not in defaults:
            raise OoxmlSemanticError(f"CONTENT_TYPE_MISSING: {part}")
    exact_types = {
        "ppt/presentation.xml": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
        ),
        "docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
        "docProps/app.xml": (
            "application/vnd.openxmlformats-officedocument.extended-properties+xml"
        ),
    }
    family_types = (
        ("ppt/slides/slide", "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"),
        ("ppt/slideMasters/slideMaster", "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"),
        ("ppt/slideLayouts/slideLayout", "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"),
        ("ppt/notesSlides/notesSlide", "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"),
        ("ppt/notesMasters/notesMaster", "application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"),
        ("ppt/charts/chart", "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"),
    )
    for part in sorted(names):
        expected = exact_types.get(part)
        if expected is None and part.endswith(".xml"):
            expected = next(
                (content_type for prefix, content_type in family_types if part.startswith(prefix)),
                None,
            )
        if expected is not None and overrides.get(part) != expected:
            raise OoxmlSemanticError(
                f"CONTENT_TYPE_MISSING: {part}: expected {expected}"
            )


def _assert_slide_size(presentation_root: ET.Element, plan: RenderPlan) -> None:
    size = presentation_root.find("p:sldSz", NS)
    if size is None:
        raise OoxmlSemanticError("SLIDE_SIZE_MISSING: ppt/presentation.xml")
    expected_width = round(plan.slide_size.width * 914400)
    expected_height = round(plan.slide_size.height * 914400)
    actual_width = int(size.attrib.get("cx", "0"))
    actual_height = int(size.attrib.get("cy", "0"))
    if abs(actual_width - expected_width) > 2000 or abs(actual_height - expected_height) > 2000:
        raise OoxmlSemanticError(
            "SLIDE_SIZE_MISMATCH: "
            f"expected {expected_width}x{expected_height}, "
            f"observed {actual_width}x{actual_height}"
        )


def _chart_cache_values(
    parent: ET.Element | None,
    *,
    string: bool,
) -> tuple[object | None, ...]:
    if parent is None:
        return ()
    cache = next(
        (
            node
            for node in parent.iter()
            if node.tag.rsplit("}", 1)[-1]
            in {"strCache", "numCache", "multiLvlStrCache"}
        ),
        None,
    )
    if cache is None:
        return ()
    points = cache.findall(".//c:pt", NS)
    declared = cache.find(".//c:ptCount", NS)
    size = int(declared.attrib.get("val", "0")) if declared is not None else 0
    indexed: dict[int, object | None] = {}
    for point in points:
        try:
            index = int(point.attrib.get("idx", "-1"))
        except ValueError:
            continue
        value = point.findtext("c:v", default="", namespaces=NS)
        if string:
            indexed[index] = value
        elif value == "":
            indexed[index] = None
        else:
            try:
                indexed[index] = float(value)
            except ValueError:
                indexed[index] = value
    if indexed:
        size = max(size, max(indexed) + 1)
    return tuple(indexed.get(index) for index in range(size))


def _numeric_sequence_equal(
    actual: Iterable[object | None],
    expected: Iterable[object | None],
) -> bool:
    left = tuple(actual)
    right = tuple(expected)
    if len(left) != len(right):
        return False
    for actual_value, expected_value in zip(left, right):
        if actual_value is None or expected_value is None:
            if actual_value is not expected_value:
                return False
            continue
        try:
            if abs(float(actual_value) - float(expected_value)) > 1e-9:
                return False
        except (TypeError, ValueError):
            return False
    return True


def _scalar_sequence_equal(
    actual: Iterable[object | None],
    expected: Iterable[object | None],
) -> bool:
    left = tuple(actual)
    right = tuple(expected)
    if len(left) != len(right):
        return False
    for actual_value, expected_value in zip(left, right):
        if isinstance(expected_value, (int, float)) and not isinstance(expected_value, bool):
            if not _numeric_sequence_equal((actual_value,), (expected_value,)):
                return False
        elif _normalized_text(str(actual_value or "")) != _normalized_text(
            str(expected_value or "")
        ):
            return False
    return True


def _column_index(value: str) -> int:
    result = 0
    for character in value.upper():
        result = result * 26 + ord(character) - ord("A") + 1
    return result


def _workbook_formula_values(
    workbook: zipfile.ZipFile,
    names: set[str],
    formula: str,
    workbook_label: str,
) -> tuple[object | None, ...]:
    match = re.fullmatch(
        r"(?:'((?:[^']|'')+)'|([^!]+))!\$?([A-Z]+)\$?(\d+)"
        r"(?::\$?([A-Z]+)\$?(\d+))?",
        formula,
    )
    if match is None:
        raise OoxmlSemanticError(
            f"CHART_WORKBOOK_FORMULA_INVALID: {workbook_label}: {formula}"
        )
    sheet_name = (match.group(1) or match.group(2)).replace("''", "'")
    start_col, start_row = _column_index(match.group(3)), int(match.group(4))
    end_col = _column_index(match.group(5) or match.group(3))
    end_row = int(match.group(6) or match.group(4))
    workbook_root = _xml(workbook.read("xl/workbook.xml"), f"{workbook_label}!xl/workbook.xml")
    workbook_rels_part = "xl/_rels/workbook.xml.rels"
    if workbook_rels_part not in names:
        raise OoxmlSemanticError(
            f"CHART_WORKBOOK_INVALID: {workbook_label}: workbook relationships missing"
        )
    rel_root = _xml(
        workbook.read(workbook_rels_part),
        f"{workbook_label}!{workbook_rels_part}",
    )
    relationships = {
        item.attrib.get("Id", ""): item.attrib.get("Target", "")
        for item in rel_root.findall("rels:Relationship", NS)
    }
    sheet_part = ""
    for sheet in workbook_root.findall("s:sheets/s:sheet", NS):
        if sheet.attrib.get("name") == sheet_name:
            target = relationships.get(sheet.attrib.get(R_ID, ""), "")
            sheet_part = posixpath.normpath(posixpath.join("xl", target))
            break
    if not sheet_part or sheet_part not in names:
        raise OoxmlSemanticError(
            f"CHART_WORKBOOK_INVALID: {workbook_label}: sheet {sheet_name!r} missing"
        )
    shared_strings: tuple[str, ...] = ()
    if "xl/sharedStrings.xml" in names:
        shared_root = _xml(
            workbook.read("xl/sharedStrings.xml"),
            f"{workbook_label}!xl/sharedStrings.xml",
        )
        shared_strings = tuple(
            _normalized_text(
                " ".join(value.text or "" for value in item.findall(".//s:t", NS))
            )
            for item in shared_root.findall("s:si", NS)
        )
    sheet_root = _xml(workbook.read(sheet_part), f"{workbook_label}!{sheet_part}")
    cells: dict[tuple[int, int], object | None] = {}
    for cell in sheet_root.findall(".//s:c", NS):
        reference = cell.attrib.get("r", "")
        cell_match = re.fullmatch(r"([A-Z]+)(\d+)", reference)
        if cell_match is None:
            continue
        location = (_column_index(cell_match.group(1)), int(cell_match.group(2)))
        cell_type = cell.attrib.get("t", "")
        raw = cell.findtext("s:v", default="", namespaces=NS)
        if cell_type == "s":
            try:
                cells[location] = shared_strings[int(raw)]
            except (ValueError, IndexError):
                cells[location] = None
        elif cell_type in {"str", "inlineStr"}:
            inline = cell.findtext("s:is/s:t", default=raw, namespaces=NS)
            cells[location] = inline
        elif raw == "":
            cells[location] = None
        else:
            try:
                cells[location] = float(raw)
            except ValueError:
                cells[location] = raw
    values: list[object | None] = []
    if start_col == end_col:
        for row in range(start_row, end_row + 1):
            values.append(cells.get((start_col, row)))
    elif start_row == end_row:
        for column in range(start_col, end_col + 1):
            values.append(cells.get((column, start_row)))
    else:
        raise OoxmlSemanticError(
            f"CHART_WORKBOOK_FORMULA_INVALID: {workbook_label}: 2D range {formula}"
        )
    return tuple(values)


def _assert_chart_data(
    package: zipfile.ZipFile,
    relationship: _Relationship,
    spec: ChartSpec,
) -> None:
    root = _xml(package.read(relationship.target), relationship.target)
    chart_tags = {
        "line": "lineChart",
        "column": "barChart",
        "bar": "barChart",
        "stacked-column": "barChart",
        "doughnut": "doughnutChart",
        "scatter": "scatterChart",
    }
    chart_node = root.find(f".//c:{chart_tags[spec.chart_type]}", NS)
    if chart_node is None:
        raise OoxmlSemanticError(
            f"CHART_TYPE_MISMATCH: {relationship.target}: {spec.chart_type}"
        )
    if spec.chart_type in {"column", "bar", "stacked-column"}:
        bar_dir = chart_node.find("c:barDir", NS)
        grouping = chart_node.find("c:grouping", NS)
        expected_dir = "bar" if spec.chart_type == "bar" else "col"
        expected_grouping = (
            "stacked" if spec.chart_type == "stacked-column" else "clustered"
        )
        if (
            bar_dir is None
            or bar_dir.attrib.get("val") != expected_dir
            or grouping is None
            or grouping.attrib.get("val") != expected_grouping
        ):
            raise OoxmlSemanticError(
                f"CHART_TYPE_MISMATCH: {relationship.target}: {spec.chart_type}"
            )
    series_nodes = chart_node.findall("c:ser", NS)
    if len(series_nodes) != len(spec.series):
        raise OoxmlSemanticError(
            f"CHART_SERIES_COUNT_MISMATCH: {relationship.target}: "
            f"expected {len(spec.series)}, observed {len(series_nodes)}"
        )
    chart_formulas: list[tuple[str, tuple[object | None, ...]]] = []
    for index, (series_node, expected_series) in enumerate(
        zip(series_nodes, spec.series), start=1
    ):
        name_values = _chart_cache_values(series_node.find("c:tx", NS), string=True)
        if tuple(_normalized_text(str(value)) for value in name_values) != (
            _normalized_text(expected_series.name),
        ):
            raise OoxmlSemanticError(
                f"CHART_SERIES_NAME_MISMATCH: {relationship.target}: series {index}"
            )
        name_formula = series_node.findtext("c:tx/c:strRef/c:f", default="", namespaces=NS)
        if name_formula:
            chart_formulas.append((name_formula, (expected_series.name,)))
        if spec.chart_type == "scatter":
            x_values = _chart_cache_values(series_node.find("c:xVal", NS), string=False)
            y_values = _chart_cache_values(series_node.find("c:yVal", NS), string=False)
            if not _numeric_sequence_equal(x_values, expected_series.x_values):
                raise OoxmlSemanticError(
                    f"CHART_X_DATA_MISMATCH: {relationship.target}: series {index}"
                )
            if not _numeric_sequence_equal(y_values, expected_series.values):
                raise OoxmlSemanticError(
                    f"CHART_DATA_MISMATCH: {relationship.target}: series {index}"
                )
            x_formula = series_node.findtext("c:xVal/c:numRef/c:f", default="", namespaces=NS)
            y_formula = series_node.findtext("c:yVal/c:numRef/c:f", default="", namespaces=NS)
            if x_formula:
                chart_formulas.append((x_formula, tuple(expected_series.x_values)))
            if y_formula:
                chart_formulas.append((y_formula, tuple(expected_series.values)))
        else:
            categories = _chart_cache_values(series_node.find("c:cat", NS), string=True)
            values = _chart_cache_values(series_node.find("c:val", NS), string=False)
            if tuple(_normalized_text(str(value)) for value in categories) != tuple(
                _normalized_text(value) for value in spec.categories
            ):
                raise OoxmlSemanticError(
                    f"CHART_CATEGORY_MISMATCH: {relationship.target}: series {index}"
                )
            if not _numeric_sequence_equal(values, expected_series.values):
                raise OoxmlSemanticError(
                    f"CHART_DATA_MISMATCH: {relationship.target}: series {index}"
                )
            category_formula = next(
                (
                    value.text or ""
                    for value in series_node.findall("c:cat//c:f", NS)
                    if value.text
                ),
                "",
            )
            value_formula = series_node.findtext("c:val/c:numRef/c:f", default="", namespaces=NS)
            if category_formula:
                chart_formulas.append((category_formula, tuple(spec.categories)))
            if value_formula:
                chart_formulas.append((value_formula, tuple(expected_series.values)))
    if (spec.value_unit or "").strip().casefold() in {"%", "percent", "percentage"}:
        value_axis = root.find(".//c:valAx", NS)
        minimum = (
            value_axis.find("c:scaling/c:min", NS)
            if value_axis is not None
            else None
        )
        maximum = (
            value_axis.find("c:scaling/c:max", NS)
            if value_axis is not None
            else None
        )
        major = value_axis.find("c:majorUnit", NS) if value_axis is not None else None
        number_format = value_axis.find("c:numFmt", NS) if value_axis is not None else None
        label_format = chart_node.find("c:dLbls/c:numFmt", NS)
        axis_title = " ".join(
            value.text or ""
            for value in (
                value_axis.findall("c:title//a:t", NS)
                if value_axis is not None
                else []
            )
        ).strip()
        if (
            minimum is None
            or minimum.attrib.get("val") not in {"0", "0.0"}
            or maximum is None
            or maximum.attrib.get("val") not in {"100", "100.0"}
            or major is None
            or major.attrib.get("val") not in {"20", "20.0"}
        ):
            raise OoxmlSemanticError(
                f"CHART_PERCENT_AXIS_MISMATCH: {relationship.target}"
            )
        if (
            number_format is None
            or number_format.attrib.get("formatCode") != '0"%"'
            or label_format is None
            or label_format.attrib.get("formatCode") != '0"%"'
            or _normalized_text(axis_title).casefold() != "percent"
        ):
            raise OoxmlSemanticError(
                f"CHART_PERCENT_FORMAT_MISMATCH: {relationship.target}"
            )
    chart_relationships = _relationships(
        package,
        set(package.namelist()),
        relationship.target,
    )
    external_data = root.find(".//c:externalData", NS)
    workbook_rel_id = external_data.attrib.get(R_ID, "") if external_data is not None else ""
    workbook_rel = chart_relationships.get(workbook_rel_id)
    if (
        workbook_rel is None
        or workbook_rel.external
        or not workbook_rel.rel_type.endswith("/package")
        or not workbook_rel.target.casefold().endswith(".xlsx")
    ):
        raise OoxmlSemanticError(
            f"CHART_WORKBOOK_RELATIONSHIP_MISSING: {relationship.target}"
        )
    try:
        with zipfile.ZipFile(io.BytesIO(package.read(workbook_rel.target))) as workbook:
            workbook_names = _safe_part_names(workbook.namelist())
            required = {"[Content_Types].xml", "xl/workbook.xml"}
            if not required.issubset(workbook_names):
                raise OoxmlSemanticError(
                    f"CHART_WORKBOOK_INVALID: {workbook_rel.target}"
                )
            for formula, expected_values in chart_formulas:
                workbook_values = _workbook_formula_values(
                    workbook,
                    set(workbook_names),
                    formula,
                    workbook_rel.target,
                )
                if not _scalar_sequence_equal(workbook_values, expected_values):
                    raise OoxmlSemanticError(
                        f"CHART_WORKBOOK_DATA_MISMATCH: {workbook_rel.target}: {formula}"
                    )
    except (KeyError, OSError, zipfile.BadZipFile) as exc:
        raise OoxmlSemanticError(
            f"CHART_WORKBOOK_INVALID: {workbook_rel.target}: {exc}"
        ) from exc


def _assert_table_data(node: ET.Element, spec: TableSpec, item: RenderObject) -> None:
    if node.find(".//a:tbl", NS) is None:
        raise OoxmlSemanticError(f"TABLE_NATIVE_OBJECT_MISSING: {item.id}")
    actual = tuple(
        _normalized_text(value.text)
        for value in node.findall(".//a:t", NS)
    )
    expected = tuple(
        _normalized_text(value)
        for value in (*spec.columns, *(cell for row in spec.rows for cell in row))
    )
    if actual != expected:
        raise OoxmlSemanticError(
            f"TABLE_DATA_MISMATCH: {item.id}: expected {expected!r}, observed {actual!r}"
        )


def _assert_hyperlink(
    node: ET.Element,
    relationships: dict[str, _Relationship],
    expected: str,
    slide_parts_by_id: dict[str, str],
    item: RenderObject,
) -> None:
    rel_ids = [
        element.attrib.get(R_ID, "")
        for element in node.findall(".//a:hlinkClick", NS)
    ]
    if len(rel_ids) != 1 or rel_ids[0] not in relationships:
        raise OoxmlSemanticError(f"HYPERLINK_TARGET_MISMATCH: {item.id}")
    rels = [relationships[rel_id] for rel_id in rel_ids if rel_id in relationships]
    if expected.startswith("slide:"):
        target = slide_parts_by_id[expected.removeprefix("slide:")]
        if not any(
            not rel.external
            and rel.rel_type.endswith("/slide")
            and rel.target == target
            for rel in rels
        ):
            raise OoxmlSemanticError(f"HYPERLINK_TARGET_MISMATCH: {item.id}")
    elif not any(
        rel.external
        and rel.rel_type.endswith("/hyperlink")
        and rel.target == expected
        for rel in rels
    ):
        raise OoxmlSemanticError(f"HYPERLINK_TARGET_MISMATCH: {item.id}")


def _assert_no_hyperlink(node: ET.Element, item: RenderObject) -> None:
    if node.findall(".//a:hlinkClick", NS):
        raise OoxmlSemanticError(f"HYPERLINK_UNEXPECTED: {item.id}")


def _assert_object_kind(node: ET.Element, item: RenderObject) -> None:
    tag = node.tag.rsplit("}", 1)[-1]
    expected = {
        "text": "sp",
        "shape": "sp",
        "image": "pic",
        "table": "graphicFrame",
        "chart": "graphicFrame",
        "diagram": "sp",
    }[item.kind]
    if tag != expected:
        raise OoxmlSemanticError(
            f"OBJECT_NATIVE_TYPE_MISMATCH: {item.id}: expected {expected}, observed {tag}"
        )


def _assert_object_geometry(node: ET.Element, item: RenderObject) -> None:
    transform = node.find(".//a:xfrm", NS)
    if transform is None:
        transform = node.find(".//p:xfrm", NS)
    if transform is None:
        raise OoxmlSemanticError(f"OBJECT_GEOMETRY_MISSING: {item.id}")
    offset = transform.find("a:off", NS)
    extent = transform.find("a:ext", NS)
    if offset is None or extent is None:
        raise OoxmlSemanticError(f"OBJECT_GEOMETRY_MISSING: {item.id}")
    actual = tuple(
        int(value)
        for value in (
            offset.attrib.get("x", "0"),
            offset.attrib.get("y", "0"),
            extent.attrib.get("cx", "0"),
            extent.attrib.get("cy", "0"),
        )
    )
    expected = tuple(
        round(value * 914400)
        for value in (item.x, item.y, item.width, item.height)
    )
    if any(abs(left - right) > 2500 for left, right in zip(actual, expected)):
        raise OoxmlSemanticError(
            f"OBJECT_GEOMETRY_MISMATCH: {item.id}: expected {expected}, observed {actual}"
        )


def _srgb_value(node: ET.Element | None, path: str) -> str | None:
    if node is None:
        return None
    value = node.find(path, NS)
    return value.attrib.get("val") if value is not None else None


def _alpha_value(node: ET.Element, path: str) -> int:
    value = node.find(path, NS)
    if value is None:
        return 100_000
    try:
        return int(value.attrib.get("val", ""))
    except ValueError:
        return -1


def _assert_text_run_style(
    properties: ET.Element,
    item: RenderObject,
    *,
    expected_size_pt: int,
    expected_color_hex: str,
    expected_bold: bool,
    expected_italic: bool,
) -> None:
    try:
        size = int(properties.attrib.get("sz", "0"))
    except ValueError:
        size = 0
    expected_size = round(expected_size_pt * 100)
    if size != expected_size:
        raise OoxmlSemanticError(
            f"OBJECT_FONT_SIZE_MISMATCH: {item.id}: "
            f"expected {expected_size}, observed {size}"
        )
    color = _srgb_value(properties, "./a:solidFill/a:srgbClr")
    if color is None or color.casefold() != expected_color_hex.lstrip("#").casefold():
        raise OoxmlSemanticError(f"OBJECT_TEXT_COLOR_MISMATCH: {item.id}")
    faces = [
        face.attrib.get("typeface", "")
        for tag in ("latin", "ea", "cs")
        if (face := properties.find(f"a:{tag}", NS)) is not None
    ]
    if not faces or any(face != item.font_name for face in faces):
        raise OoxmlSemanticError(f"OBJECT_FONT_FACE_MISMATCH: {item.id}")
    if (properties.attrib.get("b") == "1") != expected_bold:
        raise OoxmlSemanticError(f"OBJECT_FONT_WEIGHT_MISMATCH: {item.id}")
    if (properties.attrib.get("i") == "1") != expected_italic:
        raise OoxmlSemanticError(f"OBJECT_FONT_STYLE_MISMATCH: {item.id}")


def _assert_object_style(node: ET.Element, item: RenderObject) -> None:
    if item.kind in {"text", "shape", "diagram"}:
        fill = _srgb_value(node, "./p:spPr/a:solidFill/a:srgbClr")
        line = _srgb_value(node, "./p:spPr/a:ln/a:solidFill/a:srgbClr")
        if fill is None or fill.casefold() != item.fill_color.lstrip("#").casefold():
            raise OoxmlSemanticError(f"OBJECT_FILL_MISMATCH: {item.id}")
        if line is None or line.casefold() != item.line_color.lstrip("#").casefold():
            raise OoxmlSemanticError(f"OBJECT_LINE_MISMATCH: {item.id}")
        fill_alpha = _alpha_value(
            node, "./p:spPr/a:solidFill/a:srgbClr/a:alpha"
        )
        line_alpha = _alpha_value(
            node, "./p:spPr/a:ln/a:solidFill/a:srgbClr/a:alpha"
        )
        if item.kind == "diagram":
            if fill_alpha != 0 or line_alpha != 0:
                raise OoxmlSemanticError(
                    f"DIAGRAM_FRAME_VISIBILITY_MISMATCH: {item.id}"
                )
        elif item.kind == "text":
            if fill_alpha != 0 or line_alpha != 0:
                raise OoxmlSemanticError(
                    f"TEXT_FRAME_VISIBILITY_MISMATCH: {item.id}"
                )
        elif item.component == "decoration":
            strong_decoration = bool(
                item.group_id
                and item.group_id.endswith("_art")
                and re.search(
                    r"(?:top_rule|bottom_rule|section_rule|closing_rule|"
                    r"wayfinding_path|content_rail|matrix_axis)",
                    item.name,
                )
            )
            expected_alpha = 80_000 if strong_decoration else 12_000
            if fill_alpha != expected_alpha or line_alpha != 0:
                raise OoxmlSemanticError(
                    f"DECORATION_ALPHA_MISMATCH: {item.id}"
                )
        elif item.component == "accent":
            expected_alpha = (
                85_000
                if item.group_id and item.group_id.endswith("_art")
                else 18_000
            )
            if fill_alpha != expected_alpha or line_alpha != 0:
                raise OoxmlSemanticError(
                    f"ACCENT_ALPHA_MISMATCH: {item.id}"
                )
        elif item.component == "diagram-node":
            if fill_alpha != 100_000 or line_alpha != 100_000:
                raise OoxmlSemanticError(
                    f"DIAGRAM_NODE_ALPHA_MISMATCH: {item.id}"
                )
        elif item.kind == "shape" and (
            fill_alpha != 100_000 or line_alpha != 38_000
        ):
            raise OoxmlSemanticError(f"SHAPE_ALPHA_MISMATCH: {item.id}")
        if (
            item.kind == "shape"
            and item.component in _ELEVATED_SHAPE_COMPONENTS
            and node.find("./p:spPr/a:effectLst/a:outerShdw", NS) is None
        ):
            raise OoxmlSemanticError(f"OBJECT_SHADOW_MISSING: {item.id}")
    if item.kind not in {"text", "shape"} or item.text is None:
        return
    if item.text_runs is not None:
        actual_runs = [
            run
            for run in node.findall(".//a:r", NS)
            if run.find("./a:t", NS) is not None
        ]
        if len(actual_runs) != len(item.text_runs):
            raise OoxmlSemanticError(f"OBJECT_TEXT_RUN_COUNT_MISMATCH: {item.id}")
        for actual, expected in zip(actual_runs, item.text_runs):
            actual_text = actual.find("./a:t", NS)
            properties = actual.find("./a:rPr", NS)
            if actual_text is None or (actual_text.text or "") != expected.text:
                raise OoxmlSemanticError(f"OBJECT_TEXT_RUN_MISMATCH: {item.id}")
            if properties is None:
                raise OoxmlSemanticError(f"OBJECT_TEXT_STYLE_MISSING: {item.id}")
            _assert_text_run_style(
                properties,
                item,
                expected_size_pt=expected.font_size_pt,
                expected_color_hex=expected.text_color,
                expected_bold=expected.bold,
                expected_italic=expected.italic,
            )
        return
    run_properties = node.findall(".//a:rPr", NS)
    if item.text and not run_properties:
        raise OoxmlSemanticError(f"OBJECT_TEXT_STYLE_MISSING: {item.id}")
    for properties in run_properties:
        _assert_text_run_style(
            properties,
            item,
            expected_size_pt=item.font_size_pt,
            expected_color_hex=item.text_color,
            expected_bold=item.component in _BOLD_COMPONENTS,
            expected_italic=item.component == "quote",
        )


def _assert_image_payload(
    package: zipfile.ZipFile,
    node: ET.Element,
    relationships: dict[str, _Relationship],
    item: RenderObject,
) -> None:
    rel_ids = [
        element.attrib.get(R_EMBED, "")
        for element in node.findall(".//a:blip", NS)
    ]
    image_rels = [
        relationships[rel_id]
        for rel_id in rel_ids
        if rel_id in relationships
        and not relationships[rel_id].external
        and relationships[rel_id].rel_type.endswith("/image")
    ]
    if not image_rels:
        raise OoxmlSemanticError(f"IMAGE_RELATIONSHIP_MISSING: {item.id}")
    payload = package.read(image_rels[0].target)
    if not payload or not (
        payload.startswith(b"\x89PNG\r\n\x1a\n")
        or payload.startswith(b"\xff\xd8\xff")
        or payload.startswith((b"GIF87a", b"GIF89a"))
        or b"<svg" in payload[:1024].lower()
    ):
        raise OoxmlSemanticError(f"IMAGE_PAYLOAD_UNREADABLE: {item.id}")
    if item.source_path is None:
        raise OoxmlSemanticError(f"IMAGE_SOURCE_MISSING: {item.id}")
    try:
        expected_payload = item.source_path.read_bytes()
    except OSError as exc:
        raise OoxmlSemanticError(
            f"IMAGE_SOURCE_UNREADABLE: {item.id}: {exc}"
        ) from exc
    if hashlib.sha256(payload).digest() != hashlib.sha256(expected_payload).digest():
        raise OoxmlSemanticError(f"IMAGE_PAYLOAD_MISMATCH: {item.id}")
    aspect_ratio = item.asset_record.aspect_ratio if item.asset_record else None
    if aspect_ratio and abs(aspect_ratio - (item.width / item.height)) > 0.01:
        if node.find(".//a:srcRect", NS) is None:
            raise OoxmlSemanticError(f"IMAGE_CROP_MISSING: {item.id}")


def _diagram_child_geometry(
    item: RenderObject,
    *,
    node_count: int,
    index: int,
) -> tuple[float, float, float, float]:
    gap = 0.12
    if item.advanced is None or not isinstance(item.advanced, DiagramSpec):
        raise OoxmlSemanticError(f"DIAGRAM_SPEC_MISSING: {item.id}")
    diagram_type = item.advanced.diagram_type
    if diagram_type in {"matrix", "quadrant"}:
        columns = 2
        rows = (node_count + columns - 1) // columns
        width = (item.width - gap) / columns
        height = (item.height - gap * (rows - 1)) / rows
        return (
            item.x + (index % columns) * (width + gap),
            item.y + (index // columns) * (height + gap),
            width,
            height,
        )
    if diagram_type == "funnel":
        height = (item.height - gap * (node_count - 1)) / node_count
        ratio = 1 - (index / max(1, node_count)) * 0.35
        width = item.width * ratio
        return (
            item.x + (item.width - width) / 2,
            item.y + index * (height + gap),
            width,
            height,
        )
    width = (item.width - gap * (node_count - 1)) / node_count
    if diagram_type in {"timeline", "roadmap"}:
        if node_count == 1:
            width = item.width * 0.62
            height = item.height * 0.45
            return (
                item.x + (item.width - width) / 2,
                item.y + (item.height - height) / 2,
                width,
                height,
            )
        height = item.height * (0.55 if diagram_type == "timeline" else 0.58)
        return (
            item.x + index * (width + gap),
            item.y + (0 if index % 2 == 0 else item.height - height),
            width,
            height,
        )
    if diagram_type == "process":
        height = item.height * 0.58
        return (
            item.x + index * (width + gap),
            item.y + (item.height - height) / 2,
            width,
            height,
        )
    return (
        item.x + index * (width + gap),
        item.y,
        width,
        item.height,
    )


def _assert_diagram_children(nodes: dict[str, ET.Element], item: RenderObject) -> None:
    if not isinstance(item.advanced, DiagramSpec):
        raise OoxmlSemanticError(f"DIAGRAM_SPEC_MISSING: {item.id}")
    expected_group = item.group_id or item.id
    for index, expected_node in enumerate(item.advanced.nodes, start=1):
        name = f"{item.name}__node_{index:02d}"
        child = nodes.get(name)
        if child is None:
            raise OoxmlSemanticError(
                f"DIAGRAM_CHILD_MISSING: {item.id}: {name}"
            )
        identity = _identity(child)
        expected_identity = (
            f"{item.id}.node.{index}",
            "shape",
            "diagram-node",
            expected_group,
        )
        if identity != expected_identity:
            raise OoxmlSemanticError(
                f"DIAGRAM_CHILD_METADATA_MISMATCH: {item.id}: {name}"
            )
        if child.tag.rsplit("}", 1)[-1] != "sp":
            raise OoxmlSemanticError(
                f"DIAGRAM_CHILD_NATIVE_TYPE_MISMATCH: {item.id}: {name}"
            )
        expected_text = expected_node.label
        if expected_node.detail:
            expected_text += "\n" + expected_node.detail
        actual_text = _normalized_text(
            " ".join(value.text or "" for value in child.findall(".//a:t", NS))
        )
        if actual_text != _normalized_text(expected_text):
            raise OoxmlSemanticError(
                f"DIAGRAM_CHILD_TEXT_MISMATCH: {item.id}: {name}"
            )
        x, y, width, height = _diagram_child_geometry(
            item,
            node_count=len(item.advanced.nodes),
            index=index - 1,
        )
        governed_child = replace(
            item,
            id=f"{item.id}.node.{index}",
            kind="shape",
            component="diagram-node",
            x=x,
            y=y,
            width=width,
            height=height,
            text=expected_text,
            font_size_pt=max(9, item.font_size_pt - 1),
            advanced=None,
        )
        _assert_object_geometry(child, governed_child)
        _assert_object_style(child, governed_child)


def _expected_visual_order(slide_objects: Iterable[RenderObject]) -> tuple[str, ...]:
    names: list[str] = []
    for item in sorted(slide_objects, key=lambda value: (value.layer, value.name)):
        names.append(item.name)
        if item.kind == "diagram" and isinstance(item.advanced, DiagramSpec):
            names.extend(
                f"{item.name}__node_{index:02d}"
                for index in range(1, len(item.advanced.nodes) + 1)
            )
    return tuple(names)


def _assert_slide_background(
    slide_root: ET.Element,
    expected_hex: str,
    slide_id: str,
) -> None:
    color = slide_root.find("./p:cSld/p:bg/p:bgPr/a:solidFill/a:srgbClr", NS)
    actual = color.attrib.get("val", "") if color is not None else ""
    if actual.casefold() != expected_hex.lstrip("#").casefold():
        raise OoxmlSemanticError(
            f"SLIDE_BACKGROUND_MISMATCH: {slide_id}: "
            f"expected {expected_hex}, observed {actual or 'missing'}"
        )


def _notes_body_text(notes_root: ET.Element) -> str:
    for shape in notes_root.findall(".//p:sp", NS):
        placeholder = shape.find("./p:nvSpPr/p:nvPr/p:ph", NS)
        if placeholder is not None and placeholder.attrib.get("type") == "body":
            return _normalized_text(
                " ".join(value.text or "" for value in shape.findall(".//a:t", NS))
            )
    return ""


def _assert_master_chain(
    package: zipfile.ZipFile,
    names: set[str],
    presentation_rels: dict[str, _Relationship],
    slide_part: str,
    slide_relationships: dict[str, _Relationship],
    slide: RenderSlide,
    plan: RenderPlan,
) -> None:
    if not any(rel.rel_type.endswith("/slideMaster") for rel in presentation_rels.values()):
        raise OoxmlSemanticError("SLIDE_MASTER_RELATIONSHIP_MISSING: ppt/presentation.xml")
    layout_rels = [
        rel for rel in slide_relationships.values()
        if rel.rel_type.endswith("/slideLayout") and not rel.external
    ]
    if len(layout_rels) != 1:
        raise OoxmlSemanticError(f"SLIDE_LAYOUT_RELATIONSHIP_MISSING: {slide_part}")
    layout_relationships = _relationships(package, names, layout_rels[0].target)
    if not any(
        rel.rel_type.endswith("/slideMaster") and not rel.external
        for rel in layout_relationships.values()
    ):
        raise OoxmlSemanticError(
            f"SLIDE_MASTER_CHAIN_MISSING: {layout_rels[0].target}"
        )
    _assert_role_layout_system(
        package,
        layout_rels[0].target,
        slide,
        plan,
    )


def _role_layout_geometry(
    role: str,
    width: float,
    height: float,
) -> tuple[tuple[float, float, float, float, int], ...]:
    rail_width = 0.14 if role in {"cover", "closing"} else 0.07
    rail = (0.0, 0.0, rail_width, height, 100_000)
    if role == "cover":
        return (
            rail,
            (width - 1.35, 0.0, 1.35, 0.08, 100_000),
            (width - 0.60, height - 1.72, 0.60, 0.10, 24_000),
            (width - 1.00, height - 1.37, 1.00, 0.10, 16_000),
            (width - 1.40, height - 1.02, 1.40, 0.10, 9_000),
        )
    if role in {"agenda", "section"}:
        return (
            rail,
            (0.0, 0.0, width, 1.28, 6_000),
            (width - 1.05, 0.0, 1.05, 0.08, 100_000),
        )
    if role == "closing":
        return (
            rail,
            (0.0, height - 1.12, width, 1.12, 7_000),
            (width - 1.35, 0.0, 1.35, 0.08, 100_000),
        )
    return (
        rail,
        (width - 1.05, 0.0, 1.05, 0.08, 100_000),
    )


def _assert_role_layout_system(
    package: zipfile.ZipFile,
    layout_part: str,
    slide: RenderSlide,
    plan: RenderPlan,
) -> None:
    root = _xml(package.read(layout_part), layout_part)
    role = (
        slide.role
        if slide.role in {"cover", "agenda", "section", "closing"}
        else "content"
    )
    content = root.find("./p:cSld", NS)
    expected_name = f"WINDOW_PPTX_MASTER_{role.upper()}"
    if content is None or content.attrib.get("name") != expected_name:
        raise OoxmlSemanticError(
            f"ROLE_LAYOUT_MISMATCH: {slide.source_id}: expected {expected_name}"
        )
    background = _srgb_value(
        content, "./p:bg/p:bgPr/a:solidFill/a:srgbClr"
    )
    if (
        background is None
        or background.casefold()
        != slide.background_color.lstrip("#").casefold()
    ):
        raise OoxmlSemanticError(
            f"ROLE_LAYOUT_BACKGROUND_MISMATCH: {slide.source_id}"
        )
    shapes = content.findall("./p:spTree/p:sp", NS)
    expected = _role_layout_geometry(
        role,
        plan.slide_size.width,
        plan.slide_size.height,
    )
    if len(shapes) != len(expected):
        raise OoxmlSemanticError(
            f"ROLE_LAYOUT_OBJECT_COUNT_MISMATCH: {slide.source_id}: "
            f"expected {len(expected)}, observed {len(shapes)}"
        )
    primary = slide.objects[0].line_color.lstrip("#").casefold()
    for index, (shape, geometry) in enumerate(zip(shapes, expected), start=1):
        transform = shape.find("./p:spPr/a:xfrm", NS)
        offset = transform.find("a:off", NS) if transform is not None else None
        extent = transform.find("a:ext", NS) if transform is not None else None
        if offset is None or extent is None:
            raise OoxmlSemanticError(
                f"ROLE_LAYOUT_GEOMETRY_MISSING: {slide.source_id}:{index}"
            )
        actual_geometry = tuple(
            int(value)
            for value in (
                offset.attrib.get("x", "0"),
                offset.attrib.get("y", "0"),
                extent.attrib.get("cx", "0"),
                extent.attrib.get("cy", "0"),
            )
        )
        expected_geometry = tuple(round(value * 914_400) for value in geometry[:4])
        if any(
            abs(left - right) > 2_500
            for left, right in zip(actual_geometry, expected_geometry)
        ):
            raise OoxmlSemanticError(
                f"ROLE_LAYOUT_GEOMETRY_MISMATCH: {slide.source_id}:{index}"
            )
        fill = _srgb_value(shape, "./p:spPr/a:solidFill/a:srgbClr")
        line = _srgb_value(shape, "./p:spPr/a:ln/a:solidFill/a:srgbClr")
        fill_alpha = _alpha_value(
            shape, "./p:spPr/a:solidFill/a:srgbClr/a:alpha"
        )
        line_alpha = _alpha_value(
            shape, "./p:spPr/a:ln/a:solidFill/a:srgbClr/a:alpha"
        )
        if (
            fill is None
            or fill.casefold() != primary
            or line is None
            or line.casefold() != primary
            or fill_alpha != geometry[4]
            or line_alpha != 0
        ):
            raise OoxmlSemanticError(
                f"ROLE_LAYOUT_STYLE_MISMATCH: {slide.source_id}:{index}"
            )


def inspect_rendered_pptx(path: Path, plan: RenderPlan) -> OoxmlSemanticReport:
    """Fail closed unless *path* preserves the complete governed RenderPlan."""

    validate_render_plan(plan)
    validate_ooxml_package(path)
    try:
        package = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise OoxmlSemanticError(f"PACKAGE_UNREADABLE: {exc}") from exc
    with package:
        part_names = _safe_part_names(package.namelist())
        names = set(part_names)
        _assert_content_types(package, names)
        _assert_relationship_graph(package, names)
        presentation_part = "ppt/presentation.xml"
        presentation_root = _xml(package.read(presentation_part), presentation_part)
        _assert_slide_size(presentation_root, plan)
        presentation_rels = _relationships(package, names, presentation_part)
        slide_parts: list[str] = []
        for sld_id in presentation_root.findall(".//p:sldIdLst/p:sldId", NS):
            rel_id = sld_id.attrib.get(R_ID, "")
            relation = presentation_rels.get(rel_id)
            if relation is None or not relation.rel_type.endswith("/slide"):
                raise OoxmlSemanticError(
                    f"SLIDE_RELATIONSHIP_MISSING: {presentation_part}:{rel_id}"
                )
            slide_parts.append(relation.target)
        if len(slide_parts) != len(plan.slides):
            raise OoxmlSemanticError(
                f"SLIDE_COUNT_MISMATCH: expected {len(plan.slides)}, "
                f"observed {len(slide_parts)}"
            )
        slide_parts_by_id = {
            slide.source_id: slide_parts[index]
            for index, slide in enumerate(plan.slides)
        }

        object_ids: list[str] = []
        chart_count = 0
        table_count = 0
        diagram_count = 0
        notes_count = 0
        hyperlink_count = 0
        for slide, slide_part in zip(plan.slides, slide_parts):
            slide_root = _xml(package.read(slide_part), slide_part)
            _assert_slide_background(
                slide_root,
                slide.background_color,
                slide.source_id,
            )
            relationships = _relationships(package, names, slide_part)
            _assert_master_chain(
                package,
                names,
                presentation_rels,
                slide_part,
                relationships,
                slide,
                plan,
            )
            nodes = _object_nodes(slide_root)
            expected_order = _expected_visual_order(slide.objects)
            actual_order = _ordered_object_names(slide_root)
            notes_rels = [
                rel for rel in relationships.values()
                if rel.rel_type.endswith("/notesSlide") and not rel.external
            ]
            if not notes_rels:
                raise OoxmlSemanticError(f"NOTES_MISSING: {slide.source_id}")
            if len(notes_rels) != 1:
                raise OoxmlSemanticError(
                    f"NOTES_RELATIONSHIP_INVALID: {slide.source_id}: "
                    f"expected 1, observed {len(notes_rels)}"
                )
            notes_root = _xml(
                package.read(notes_rels[0].target), notes_rels[0].target
            )
            notes_text = _notes_body_text(notes_root)
            notes_relationships = _relationships(
                package,
                names,
                notes_rels[0].target,
            )
            if not any(
                rel.rel_type.endswith("/slide")
                and not rel.external
                and rel.target == slide_part
                for rel in notes_relationships.values()
            ):
                raise OoxmlSemanticError(
                    f"NOTES_SLIDE_BACKLINK_MISSING: {slide.source_id}"
                )
            if slide.speaker_notes:
                if _normalized_text(slide.speaker_notes) != notes_text:
                    raise OoxmlSemanticError(
                        f"NOTES_TEXT_MISMATCH: {slide.source_id}"
                    )
                notes_count += 1
            elif notes_text:
                raise OoxmlSemanticError(
                    f"NOTES_UNEXPECTED: {slide.source_id}"
                )

            for item in slide.objects:
                node = nodes.get(item.name)
                if node is None:
                    raise OoxmlSemanticError(
                        f"OBJECT_IDENTITY_MISSING: {slide.source_id}:{item.name}"
                    )
                identity = _identity(node)
                if identity != (
                    item.id,
                    item.kind,
                    item.component,
                    item.group_id or "",
                ):
                    raise OoxmlSemanticError(
                        f"OBJECT_METADATA_MISMATCH: {slide.source_id}:{item.name}"
                    )
                _assert_object_kind(node, item)
                _assert_object_geometry(node, item)
                _assert_object_style(node, item)
                object_ids.append(item.id)
                if item.text is not None:
                    actual_text = _normalized_text(
                        " ".join(value.text or "" for value in node.findall(".//a:t", NS))
                    )
                    if _normalized_text(item.text) != actual_text:
                        raise OoxmlSemanticError(
                            f"OBJECT_TEXT_MISMATCH: {item.id}"
                        )
                if item.kind == "image":
                    _assert_image_payload(
                        package,
                        node,
                        relationships,
                        item,
                    )
                elif item.kind == "chart":
                    chart_elements = node.findall(".//c:chart", NS)
                    if not chart_elements:
                        raise OoxmlSemanticError(f"CHART_NATIVE_OBJECT_MISSING: {item.id}")
                    chart_rel = relationships.get(chart_elements[0].attrib.get(R_ID, ""))
                    if chart_rel is None:
                        raise OoxmlSemanticError(f"CHART_RELATIONSHIP_MISSING: {item.id}")
                    if isinstance(item.advanced, ChartSpec):
                        _assert_chart_data(package, chart_rel, item.advanced)
                    chart_count += 1
                elif item.kind == "table":
                    if not isinstance(item.advanced, TableSpec):
                        raise OoxmlSemanticError(f"TABLE_SPEC_MISSING: {item.id}")
                    _assert_table_data(node, item.advanced, item)
                    table_count += 1
                elif item.kind == "diagram":
                    _assert_diagram_children(nodes, item)
                    diagram_count += 1
                if item.hyperlink:
                    _assert_hyperlink(
                        node,
                        relationships,
                        item.hyperlink,
                        slide_parts_by_id,
                        item,
                    )
                    hyperlink_count += 1
                else:
                    _assert_no_hyperlink(node, item)
            if actual_order != expected_order:
                raise OoxmlSemanticError(
                    f"OBJECT_Z_ORDER_MISMATCH: {slide.source_id}"
                )

        return OoxmlSemanticReport(
            slide_count=len(slide_parts),
            object_ids=tuple(object_ids),
            chart_count=chart_count,
            table_count=table_count,
            diagram_count=diagram_count,
            notes_count=notes_count,
            hyperlink_count=hyperlink_count,
            part_count=len(part_names),
        )


def _normalized_core_properties(data: bytes) -> bytes:
    root = _xml(data, "docProps/core.xml")
    for tag in ("dcterms:created", "dcterms:modified"):
        element = root.find(tag, NS)
        if element is not None:
            element.text = FIXED_CORE_TIME
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def normalize_pptx_package(path: Path) -> Path:
    """Rewrite a newly generated package with stable metadata and ZIP fields."""

    validate_ooxml_package(path)
    temporary = path.with_name(f".{path.stem}.normalized.tmp{path.suffix}")
    try:
        with zipfile.ZipFile(path, "r") as source:
            names = _safe_part_names(source.namelist())
            parts = {name: source.read(name) for name in names}
        if "docProps/core.xml" in parts:
            parts["docProps/core.xml"] = _normalized_core_properties(
                parts["docProps/core.xml"]
            )
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as target:
            for name in sorted(parts):
                info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o600 << 16
                target.writestr(info, parts[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        validate_ooxml_package(temporary)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return path


def write_ooxml_report(report: OoxmlSemanticReport, output: Path) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return str(output)


__all__ = [
    "FIXED_CORE_TIME",
    "OoxmlSemanticError",
    "OoxmlSemanticReport",
    "inspect_rendered_pptx",
    "normalize_pptx_package",
    "write_ooxml_report",
]
