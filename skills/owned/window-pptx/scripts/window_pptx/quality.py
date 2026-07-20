"""Stable five-layer quality inspection and bounded candidate-only repair."""

from __future__ import annotations

import json
import math
import os
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable

from .models import CandidateResult, OutputPolicy
from .render_plan import (
    ChartSpec,
    DiagramSpec,
    RenderObject,
    RenderPlan,
    TableSpec,
    inches_to_points,
)
from .renderer import RenderReport


QUALITY_REPORT_VERSION = "1.0"
REPAIR_LOG_VERSION = "1.0"
QUALITY_LAYERS = ("package", "com", "geometry", "visual", "deck")
SEVERITY_WEIGHTS = {"critical": 100, "error": 25, "warning": 5, "info": 0}
HARD_GATE_CODES = frozenset(
    {
        "PACKAGE_NOT_PROMOTED",
        "PACKAGE_VALIDATION_MISSING",
        "PDF_VALIDATION_MISSING",
        "SOURCE_INTEGRITY_FAILURE",
        "CLEANUP_FAILURE",
        "PAGE_SIZE_MISMATCH",
        "SLIDE_COUNT_MISMATCH",
        "OBJECT_MISSING",
        "NATIVE_OBJECT_MISSING",
        "CHART_DATA_MISMATCH",
        "TABLE_DATA_MISMATCH",
        "DIAGRAM_NODE_MISMATCH",
        "TABLE_LABELS_UNREADABLE",
        "TEXT_CONTENT_MISMATCH",
        "TEXT_OVERFLOW_RISK",
        "OBJECT_OUT_OF_BOUNDS",
        "OBJECT_OVERLAP_DRIFT",
        "PLACEHOLDER_CONTENT",
        "EDITABLE_COVERAGE_LOW",
        "FULL_SLIDE_RASTER",
        "COM_GEOMETRY_DRIFT",
        "FONT_DRIFT",
        "EDITABLE_TAG_MISSING",
        "OBJECT_TAG_DRIFT",
        "OBJECT_NAME_DRIFT",
    }
)


Scalar = str | int | float | bool | None


class QualityGateError(RuntimeError):
    """A customer-delivery hard gate failed before candidate saving."""

    def __init__(
        self,
        message: str,
        *,
        report: QualityReport | None = None,
        repair: RepairLog | None = None,
        candidate_result: CandidateResult | None = None,
        artifacts: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.report = report
        self.repair = repair
        self.candidate_result = candidate_result
        self.artifacts = dict(artifacts or {})


@dataclass(frozen=True)
class QualityFinding:
    code: str
    layer: str
    severity: str
    message: str
    slide_id: str | None = None
    object_name: str | None = None
    repairable: bool = False
    details: tuple[tuple[str, Scalar], ...] = ()

    def details_dict(self) -> dict[str, Scalar]:
        return dict(self.details)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "layer": self.layer,
            "severity": self.severity,
            "message": self.message,
            "slide_id": self.slide_id,
            "object_name": self.object_name,
            "repairable": self.repairable,
            "details": self.details_dict(),
        }


@dataclass(frozen=True)
class LayerSnapshot:
    layer: str
    status: str
    metrics: tuple[tuple[str, Scalar], ...]

    def metrics_dict(self) -> dict[str, Scalar]:
        return dict(self.metrics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "status": self.status,
            "metrics": self.metrics_dict(),
        }


@dataclass(frozen=True)
class QualityReport:
    schema_version: str
    layers: tuple[LayerSnapshot, ...]
    findings: tuple[QualityFinding, ...]
    weighted_score: int
    hard_gate_failures: tuple[str, ...]
    passed: bool
    transaction_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "layers": [layer.to_dict() for layer in self.layers],
            "findings": [finding.to_dict() for finding in self.findings],
            "weighted_score": self.weighted_score,
            "hard_gate_failures": list(self.hard_gate_failures),
            "passed": self.passed,
            "transaction_status": self.transaction_status,
        }


@dataclass(frozen=True)
class RepairAction:
    code: str
    target: str
    values: tuple[tuple[str, Scalar], ...]

    def values_dict(self) -> dict[str, Scalar]:
        return dict(self.values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "target": self.target,
            "values": self.values_dict(),
        }


@dataclass(frozen=True)
class RepairPass:
    index: int
    actions: tuple[RepairAction, ...]
    before_score: int
    after_score: int
    accepted: bool
    rolled_back: bool
    hard_gate_failures_before: tuple[str, ...]
    hard_gate_failures_after: tuple[str, ...]
    failure_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "actions": [action.to_dict() for action in self.actions],
            "before_score": self.before_score,
            "after_score": self.after_score,
            "accepted": self.accepted,
            "rolled_back": self.rolled_back,
            "hard_gate_failures_before": list(self.hard_gate_failures_before),
            "hard_gate_failures_after": list(self.hard_gate_failures_after),
            "failure_code": self.failure_code,
        }


@dataclass(frozen=True)
class RepairLog:
    schema_version: str
    max_passes: int
    passes: tuple[RepairPass, ...]
    changed: bool
    final_report: QualityReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "max_passes": self.max_passes,
            "passes": [item.to_dict() for item in self.passes],
            "changed": self.changed,
            "final_report": self.final_report.to_dict(),
        }


def _details(**values: Scalar) -> tuple[tuple[str, Scalar], ...]:
    return tuple(sorted(values.items()))


def _finding(
    code: str,
    layer: str,
    severity: str,
    message: str,
    *,
    slide_id: str | None = None,
    object_name: str | None = None,
    repairable: bool = False,
    **details: Scalar,
) -> QualityFinding:
    if layer not in QUALITY_LAYERS or severity not in SEVERITY_WEIGHTS:
        raise ValueError("quality finding crossed the registered vocabulary")
    return QualityFinding(
        code=code,
        layer=layer,
        severity=severity,
        message=message,
        slide_id=slide_id,
        object_name=object_name,
        repairable=repairable,
        details=_details(**details),
    )


def _layer_status(layer: str, findings: Iterable[QualityFinding]) -> str:
    severities = {
        finding.severity for finding in findings if finding.layer == layer
    }
    if severities & {"critical", "error"}:
        return "fail"
    if "warning" in severities:
        return "warn"
    return "pass"


def _build_report(
    snapshots: Iterable[LayerSnapshot],
    findings: Iterable[QualityFinding],
    *,
    transaction_status: str,
) -> QualityReport:
    ordered_findings = tuple(
        sorted(
            findings,
            key=lambda item: (
                QUALITY_LAYERS.index(item.layer),
                -SEVERITY_WEIGHTS[item.severity],
                item.slide_id or "",
                item.object_name or "",
                item.code,
            ),
        )
    )
    score = sum(SEVERITY_WEIGHTS[item.severity] for item in ordered_findings)
    hard = tuple(
        sorted({item.code for item in ordered_findings if item.code in HARD_GATE_CODES})
    )
    snapshots_by_layer = {snapshot.layer: snapshot for snapshot in snapshots}
    layers: list[LayerSnapshot] = []
    for layer in QUALITY_LAYERS:
        snapshot = snapshots_by_layer[layer]
        status = snapshot.status
        if status not in {"pending", "skipped"}:
            status = _layer_status(layer, ordered_findings)
        layers.append(replace(snapshot, status=status))
    return QualityReport(
        schema_version=QUALITY_REPORT_VERSION,
        layers=tuple(layers),
        findings=ordered_findings,
        weighted_score=score,
        hard_gate_failures=hard,
        passed=not hard,
        transaction_status=transaction_status,
    )


def _collection_items(collection: Any) -> list[Any]:
    items = getattr(collection, "items", None)
    if isinstance(items, list):
        return list(items)
    count = int(collection.Count)
    return [collection.Item(index) for index in range(1, count + 1)]


def _group_items(shape: Any) -> list[Any]:
    group = getattr(shape, "GroupItems", None)
    if isinstance(group, tuple):
        return list(group)
    if group is None or not hasattr(group, "Count"):
        return []
    return [group.Item(index) for index in range(1, int(group.Count) + 1)]


def _walk_shape(shape: Any) -> Iterable[Any]:
    yield shape
    for child in _group_items(shape):
        yield from _walk_shape(child)


def _slide_shapes(slide: Any) -> list[Any]:
    result: list[Any] = []
    for shape in _collection_items(slide.Shapes):
        result.extend(_walk_shape(shape))
    return result


def _tag_values(shape: Any) -> dict[str, str]:
    tags = getattr(shape, "Tags", None)
    values = getattr(tags, "values", None)
    if isinstance(values, dict):
        return dict(values)
    if tags is None:
        return {}
    result: dict[str, str] = {}
    try:
        for index in range(1, int(tags.Count) + 1):
            name = str(tags.Name(index))
            result[name] = str(tags.Value(index))
    except Exception:
        return result
    return result


def _shape_kind(shape: Any) -> str:
    recorded = getattr(shape, "kind", None)
    if isinstance(recorded, str):
        return recorded
    try:
        if bool(shape.HasChart):
            return "chart"
    except Exception:
        pass
    try:
        if bool(shape.HasTable):
            return "table"
    except Exception:
        pass
    tags = _tag_values(shape)
    if "window-pptx:diagram" in tags:
        return "diagram"
    try:
        if int(shape.Type) == 13:
            return "image"
        if int(shape.Type) == 6:
            return "group"
    except Exception:
        pass
    return "shape"


def _shape_font(shape: Any) -> Any | None:
    try:
        return shape.TextFrame.TextRange.Font
    except Exception:
        return None


def _shape_maps(slide: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    by_name: dict[str, Any] = {}
    by_id: dict[str, Any] = {}
    for shape in _slide_shapes(slide):
        name = getattr(shape, "Name", None)
        if isinstance(name, str) and name:
            by_name[name] = shape
        object_id = _tag_values(shape).get("window-pptx:id")
        if object_id:
            by_id[object_id] = shape
    return by_name, by_id


def _native_matches(expected: RenderObject, shape: Any) -> bool:
    actual = _shape_kind(shape)
    if expected.kind == "diagram":
        return actual in {"diagram", "group"} and bool(
            _tag_values(shape).get("window-pptx:diagram")
        )
    return expected.kind == actual or (
        expected.kind == "shape" and actual == "shape"
    ) or (expected.kind == "text" and actual == "text")


def _com_collection_item(collection: Any, index: int) -> Any:
    try:
        return collection(index)
    except Exception:
        return collection.Item(index)


def _com_values(value: Any) -> tuple[Any, ...]:
    range_value = getattr(value, "Value", value)
    if isinstance(range_value, (tuple, list)):
        flattened: list[Any] = []
        for item in range_value:
            if isinstance(item, (tuple, list)):
                flattened.extend(item)
            else:
                flattened.append(item)
        return tuple(flattened)
    return (range_value,)


def _data_values_match(actual: tuple[Any, ...], expected: tuple[Any, ...]) -> bool:
    if len(actual) != len(expected):
        return False
    for actual_value, expected_value in zip(actual, expected):
        if expected_value is None:
            if actual_value not in {None, ""}:
                return False
        elif isinstance(expected_value, (int, float)) and not isinstance(
            expected_value, bool
        ):
            try:
                if not math.isclose(
                    float(actual_value), float(expected_value), rel_tol=1e-9, abs_tol=1e-9
                ):
                    return False
            except (TypeError, ValueError):
                return False
        elif str(actual_value) != str(expected_value):
            return False
    return True


def _chart_data_mismatch(chart: Any, expected: ChartSpec) -> bool:
    """Fail closed when native series names, categories, or values cannot be verified."""

    try:
        collection = chart.SeriesCollection()
        if int(collection.Count) != len(expected.series):
            return True
        for index, expected_series in enumerate(expected.series, start=1):
            actual_series = _com_collection_item(collection, index)
            if str(actual_series.Name) != expected_series.name:
                return True
            if not _data_values_match(
                _com_values(actual_series.Values), expected_series.values
            ):
                return True
            expected_x_values: tuple[Any, ...] = (
                expected_series.x_values
                if expected_series.x_values
                else expected.categories
            )
            if expected_x_values and not _data_values_match(
                _com_values(actual_series.XValues), expected_x_values
            ):
                return True
        return False
    except Exception:
        return True


def _advanced_data_findings(
    item: RenderObject,
    shape: Any,
    slide_id: str,
) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    if isinstance(item.advanced, ChartSpec):
        recorded_spec = getattr(getattr(shape, "Chart", None), "spec", None)
        mismatch = recorded_spec is not None and recorded_spec != item.advanced
        if recorded_spec is None:
            mismatch = _chart_data_mismatch(shape.Chart, item.advanced)
        if mismatch:
            findings.append(
                _finding(
                    "CHART_DATA_MISMATCH",
                    "com",
                    "critical",
                    "native chart series/categories diverge from the governed data",
                    slide_id=slide_id,
                    object_name=item.name,
                )
            )
    elif isinstance(item.advanced, TableSpec):
        mismatch = False
        unreadable = False
        try:
            table = shape.Table
            expected_rows = (item.advanced.columns, *item.advanced.rows)
            actual_row_count = getattr(table, "rows", None)
            actual_column_count = getattr(table, "columns", None)
            if actual_row_count is None:
                actual_row_count = int(table.Rows.Count)
            if actual_column_count is None:
                actual_column_count = int(table.Columns.Count)
            if actual_row_count != len(expected_rows) or actual_column_count != len(
                item.advanced.columns
            ):
                mismatch = True
            for row_index, row in enumerate(expected_rows, start=1):
                for column_index, value in enumerate(row, start=1):
                    cell_shape = table.Cell(row_index, column_index).Shape
                    if str(cell_shape.TextFrame.TextRange.Text) != value:
                        mismatch = True
                    if float(cell_shape.TextFrame.TextRange.Font.Size) < 11:
                        unreadable = True
        except Exception:
            mismatch = True
        if mismatch:
            findings.append(
                _finding(
                    "TABLE_DATA_MISMATCH",
                    "com",
                    "critical",
                    "native table cells diverge from the governed rows/columns",
                    slide_id=slide_id,
                    object_name=item.name,
                )
            )
        if unreadable:
            findings.append(
                _finding(
                    "TABLE_LABELS_UNREADABLE",
                    "visual",
                    "critical",
                    "native table labels are below the 11pt readability floor",
                    slide_id=slide_id,
                    object_name=item.name,
                )
            )
    elif isinstance(item.advanced, DiagramSpec):
        diagram_tags = _tag_values(shape)
        node_shapes = sorted(
            (
                child
                for child in _group_items(shape)
                if "window-pptx:diagram" in _tag_values(child)
            ),
            key=lambda child: str(getattr(child, "Name", "")),
        )
        actual_nodes = len(node_shapes)
        expected_texts = tuple(
            node.label if node.detail is None else f"{node.label}\n{node.detail}"
            for node in item.advanced.nodes
        )
        actual_texts: tuple[str, ...] = ()
        try:
            actual_texts = tuple(
                str(child.TextFrame.TextRange.Text)
                .replace("\r", "\n")
                .replace("\v", "\n")
                for child in node_shapes
            )
        except Exception:
            pass
        if (
            diagram_tags.get("window-pptx:diagram") != item.advanced.diagram_type
            or actual_nodes != len(item.advanced.nodes)
            or actual_texts != expected_texts
        ):
            findings.append(
                _finding(
                    "DIAGRAM_NODE_MISMATCH",
                    "com",
                    "critical",
                    "native diagram node count diverges from governed semantics",
                    slide_id=slide_id,
                    object_name=item.name,
                    expected_nodes=len(item.advanced.nodes),
                    actual_nodes=actual_nodes,
                )
            )
    return findings


def _intersection_ratio(first: Any, second: Any) -> float:
    left = max(float(first.Left), float(second.Left))
    top = max(float(first.Top), float(second.Top))
    right = min(
        float(first.Left) + float(first.Width),
        float(second.Left) + float(second.Width),
    )
    bottom = min(
        float(first.Top) + float(first.Height),
        float(second.Top) + float(second.Height),
    )
    if right <= left or bottom <= top:
        return 0.0
    intersection = (right - left) * (bottom - top)
    smaller = min(
        float(first.Width) * float(first.Height),
        float(second.Width) * float(second.Height),
    )
    return 0.0 if smaller <= 0 else intersection / smaller


def _text_capacity(item: RenderObject) -> int:
    usable_width = max(1.0, inches_to_points(item.width) - 16)
    usable_height = max(1.0, inches_to_points(item.height) - 12)
    lines = max(1, int(usable_height / (item.font_size_pt * 1.25)))
    chars_per_line = max(1, int(usable_width / (item.font_size_pt * 0.58)))
    return lines * chars_per_line


def _max_run(values: Iterable[str]) -> int:
    maximum = 0
    current = 0
    previous: str | None = None
    for value in values:
        if value == previous:
            current += 1
        else:
            previous = value
            current = 1
        maximum = max(maximum, current)
    return maximum


def inspect_quality(
    plan: RenderPlan,
    render_report: RenderReport,
    presentation: Any,
) -> QualityReport:
    """Inspect a rendered in-memory candidate without writing output files."""

    findings: list[QualityFinding] = []
    expected_width = inches_to_points(plan.slide_size.width)
    expected_height = inches_to_points(plan.slide_size.height)
    actual_width = float(presentation.PageSetup.SlideWidth)
    actual_height = float(presentation.PageSetup.SlideHeight)
    if not math.isclose(actual_width, expected_width, abs_tol=0.5) or not math.isclose(
        actual_height, expected_height, abs_tol=0.5
    ):
        findings.append(
            _finding(
                "PAGE_SIZE_MISMATCH",
                "com",
                "critical",
                "candidate page size diverges from the governed render plan",
                repairable=True,
                expected_width=expected_width,
                expected_height=expected_height,
            )
        )

    actual_slide_count = int(presentation.Slides.Count)
    if actual_slide_count != len(plan.slides):
        findings.append(
            _finding(
                "SLIDE_COUNT_MISMATCH",
                "com",
                "critical",
                "candidate slide count diverges from the render plan",
            )
        )

    expected_count = sum(len(slide.objects) for slide in plan.slides)
    found_count = 0
    native_expected = 0
    native_found = 0
    overlap_count = 0
    text_count = 0
    image_count = 0
    text_utilizations: list[float] = []
    content_area_ratios: list[float] = []

    for slide_index, render_slide in enumerate(plan.slides, start=1):
        if slide_index > actual_slide_count:
            continue
        slide = presentation.Slides.Item(slide_index)
        by_name, by_id = _shape_maps(slide)
        located: dict[str, Any] = {}
        slide_text_length = 0
        slide_text_capacity = 0
        for item in render_slide.objects:
            if item.kind in {"chart", "table", "diagram"}:
                native_expected += 1
            shape = by_name.get(item.name)
            if shape is None:
                shape = by_id.get(item.id)
                if shape is not None:
                    findings.append(
                        _finding(
                            "OBJECT_NAME_DRIFT",
                            "com",
                            "error",
                            "editable object name diverges from the render plan",
                            slide_id=render_slide.source_id,
                            object_name=str(getattr(shape, "Name", "")),
                            repairable=True,
                            expected_name=item.name,
                        )
                    )
            if shape is None:
                code = (
                    "NATIVE_OBJECT_MISSING"
                    if item.kind in {"chart", "table", "diagram"}
                    else "OBJECT_MISSING"
                )
                findings.append(
                    _finding(
                        code,
                        "com",
                        "critical" if code == "NATIVE_OBJECT_MISSING" else "error",
                        "expected editable object is missing from the candidate",
                        slide_id=render_slide.source_id,
                        object_name=item.name,
                    )
                )
                continue
            found_count += 1
            located[item.name] = shape
            if item.kind in {"chart", "table", "diagram"}:
                if _native_matches(item, shape):
                    native_found += 1
                else:
                    findings.append(
                        _finding(
                            "NATIVE_OBJECT_MISSING",
                            "com",
                            "critical",
                            "advanced content is not represented by its required native object",
                            slide_id=render_slide.source_id,
                            object_name=item.name,
                        )
                    )
                findings.extend(
                    _advanced_data_findings(item, shape, render_slide.source_id)
                )

            expected_geometry = {
                "left": inches_to_points(item.x),
                "top": inches_to_points(item.y),
                "width": inches_to_points(item.width),
                "height": inches_to_points(item.height),
            }
            actual_geometry = {
                "left": float(shape.Left),
                "top": float(shape.Top),
                "width": float(shape.Width),
                "height": float(shape.Height),
            }
            if (
                actual_geometry["left"] < -0.5
                or actual_geometry["top"] < -0.5
                or actual_geometry["left"] + actual_geometry["width"]
                > actual_width + 0.5
                or actual_geometry["top"] + actual_geometry["height"]
                > actual_height + 0.5
            ):
                findings.append(
                    _finding(
                        "OBJECT_OUT_OF_BOUNDS",
                        "geometry",
                        "critical",
                        "candidate object crosses the page boundary",
                        slide_id=render_slide.source_id,
                        object_name=item.name,
                    )
                )
            if any(
                not math.isclose(actual_geometry[key], expected, abs_tol=0.5)
                for key, expected in expected_geometry.items()
            ):
                findings.append(
                    _finding(
                        "COM_GEOMETRY_DRIFT",
                        "geometry",
                        "error",
                        "candidate object geometry diverges from the governed slot",
                        slide_id=render_slide.source_id,
                        object_name=item.name,
                        repairable=True,
                        **expected_geometry,
                    )
                )

            tags = _tag_values(shape)
            expected_tags = {
                "window-pptx:id": item.id,
                "window-pptx:component": item.component,
                "window-pptx:editable": "true",
            }
            for key, expected_value in expected_tags.items():
                if tags.get(key) != expected_value:
                    code = (
                        "EDITABLE_TAG_MISSING"
                        if key == "window-pptx:editable"
                        else "OBJECT_TAG_DRIFT"
                    )
                    findings.append(
                        _finding(
                            code,
                            "com",
                            "error",
                            "candidate object is missing a governed identity/editability tag",
                            slide_id=render_slide.source_id,
                            object_name=item.name,
                            repairable=True,
                            tag_key=key,
                            tag_value=expected_value,
                        )
                    )

            if item.text:
                text_count += 1
                font = _shape_font(shape)
                if font is not None and (
                    str(font.Name) != item.font_name
                    or not math.isclose(float(font.Size), item.font_size_pt, abs_tol=0.1)
                ):
                    findings.append(
                        _finding(
                            "FONT_DRIFT",
                            "geometry",
                            "error",
                            "candidate typography diverges from the governed theme",
                            slide_id=render_slide.source_id,
                            object_name=item.name,
                            repairable=True,
                            font_name=item.font_name,
                            font_size=float(item.font_size_pt),
                        )
                    )
                try:
                    actual_text = str(shape.TextFrame.TextRange.Text)
                except Exception:
                    actual_text = ""
                if actual_text != item.text:
                    findings.append(
                        _finding(
                            "TEXT_CONTENT_MISMATCH",
                            "com",
                            "critical",
                            "editable text content diverges from the governed render plan",
                            slide_id=render_slide.source_id,
                            object_name=item.name,
                        )
                    )
                normalized_text = "".join(actual_text.split())
                capacity = _text_capacity(item)
                slide_text_length += len(normalized_text)
                slide_text_capacity += capacity
                if len(normalized_text) > capacity:
                    findings.append(
                        _finding(
                            "TEXT_OVERFLOW_RISK",
                            "geometry",
                            "error",
                            "text length exceeds the deterministic slot capacity estimate",
                            slide_id=render_slide.source_id,
                            object_name=item.name,
                            text_length=len(normalized_text),
                            estimated_capacity=capacity,
                        )
                    )
                lowered = actual_text.casefold()
                if actual_text == "Visual asset unavailable" or any(
                    token in lowered for token in ("lorem ipsum", "placeholder", "tbd")
                ):
                    findings.append(
                        _finding(
                            "PLACEHOLDER_CONTENT",
                            "visual",
                            "critical",
                            "candidate contains unresolved placeholder content",
                            slide_id=render_slide.source_id,
                            object_name=item.name,
                        )
                    )
                try:
                    bound_height = float(shape.TextFrame2.TextRange.BoundHeight)
                    available_height = max(
                        1.0,
                        float(shape.Height)
                        - float(shape.TextFrame.MarginTop)
                        - float(shape.TextFrame.MarginBottom),
                    )
                    if bound_height > available_height + 0.5 and not any(
                        finding.code == "TEXT_OVERFLOW_RISK"
                        and finding.object_name == item.name
                        for finding in findings
                    ):
                        findings.append(
                            _finding(
                                "TEXT_OVERFLOW_RISK",
                                "geometry",
                                "error",
                                "PowerPoint reports text taller than its available frame",
                                slide_id=render_slide.source_id,
                                object_name=item.name,
                                bound_height=bound_height,
                                available_height=available_height,
                            )
                        )
                except Exception:
                    pass
            if item.kind == "image":
                image_count += 1

        text_utilization = (
            0.0 if slide_text_capacity == 0 else slide_text_length / slide_text_capacity
        )
        text_utilizations.append(text_utilization)
        content_area = sum(
            item.width * item.height
            for item in render_slide.objects
            if item.component not in {"title", "footer", "decoration"}
        )
        content_area_ratio = min(
            1.0,
            content_area / (plan.slide_size.width * plan.slide_size.height),
        )
        content_area_ratios.append(content_area_ratio)
        if text_utilization > 0.85:
            findings.append(
                _finding(
                    "PAGE_TEXT_DENSITY_HIGH",
                    "visual",
                    "warning",
                    "page text density is close to the deterministic capacity ceiling",
                    slide_id=render_slide.source_id,
                    utilization=round(text_utilization, 4),
                )
            )
        if content_area_ratio > 0.93:
            findings.append(
                _finding(
                    "PAGE_OBJECT_DENSITY_HIGH",
                    "visual",
                    "warning",
                    "page object area leaves too little visual breathing room",
                    slide_id=render_slide.source_id,
                    area_ratio=round(content_area_ratio, 4),
                )
            )
        if render_slide.item_count >= 3 and content_area_ratio < 0.18:
            findings.append(
                _finding(
                    "PAGE_OBJECT_DENSITY_LOW",
                    "visual",
                    "warning",
                    "page has multiple semantic items but unusually low occupied area",
                    slide_id=render_slide.source_id,
                    area_ratio=round(content_area_ratio, 4),
                )
            )

        for first_index, first in enumerate(render_slide.objects):
            first_shape = located.get(first.name)
            if first_shape is None or first.component == "footer":
                continue
            for second in render_slide.objects[first_index + 1 :]:
                second_shape = located.get(second.name)
                if second_shape is None or second.component == "footer":
                    continue
                if _intersection_ratio(first_shape, second_shape) > 0.10:
                    # Exact governed slots are already registry-validated. Any
                    # significant overlap here therefore comes from COM drift.
                    expected_overlap = not (
                        first.x + first.width <= second.x
                        or second.x + second.width <= first.x
                        or first.y + first.height <= second.y
                        or second.y + second.height <= first.y
                    )
                    if not expected_overlap:
                        overlap_count += 1
                        findings.append(
                            _finding(
                                "OBJECT_OVERLAP_DRIFT",
                                "geometry",
                                "error",
                                "candidate objects overlap outside the governed layout",
                                slide_id=render_slide.source_id,
                                object_name=f"{first.name}|{second.name}",
                            )
                        )

        full_images = [
            item
            for item in render_slide.objects
            if item.kind == "image"
            and item.width * item.height
            >= plan.slide_size.width * plan.slide_size.height * 0.88
        ]
        editable_content = [
            item
            for item in render_slide.objects
            if item.text and item.component not in {"title", "footer"}
        ]
        if full_images and not editable_content:
            findings.append(
                _finding(
                    "FULL_SLIDE_RASTER",
                    "visual",
                    "critical",
                    "slide is effectively a full-slide raster without editable content",
                    slide_id=render_slide.source_id,
                    object_name=full_images[0].name,
                )
            )

    editable_coverage = 1.0 if expected_count == 0 else found_count / expected_count
    if editable_coverage < 0.90:
        findings.append(
            _finding(
                "EDITABLE_COVERAGE_LOW",
                "com",
                "critical",
                "editable native object coverage is below the delivery threshold",
                expected_objects=expected_count,
                found_objects=found_count,
                coverage=round(editable_coverage, 4),
            )
        )

    family_run = _max_run(slide.family_id for slide in plan.slides)
    layout_run = _max_run(slide.layout_id for slide in plan.slides)
    if family_run >= 3:
        findings.append(
            _finding(
                "DECK_FAMILY_REPETITION",
                "deck",
                "warning",
                "three or more consecutive slides use the same page family",
                max_run=family_run,
            )
        )
    if layout_run >= 3:
        findings.append(
            _finding(
                "DECK_LAYOUT_REPETITION",
                "deck",
                "warning",
                "three or more consecutive slides use the same layout variant",
                max_run=layout_run,
            )
        )

    native_coverage = 1.0 if native_expected == 0 else native_found / native_expected
    snapshots = (
        LayerSnapshot(
            "package",
            "pending",
            _details(candidate_promoted=False, transaction_evidence="pending"),
        ),
        LayerSnapshot(
            "com",
            "pass",
            _details(
                actual_slides=actual_slide_count,
                expected_slides=len(plan.slides),
                expected_objects=expected_count,
                found_objects=found_count,
                editable_coverage=round(editable_coverage, 4),
                native_expected=native_expected,
                native_found=native_found,
                native_coverage=round(native_coverage, 4),
                renderer_native_count=render_report.native_editable_count,
            ),
        ),
        LayerSnapshot(
            "geometry",
            "pass",
            _details(
                page_width_pt=round(actual_width, 3),
                page_height_pt=round(actual_height, 3),
                overlap_count=overlap_count,
            ),
        ),
        LayerSnapshot(
            "visual",
            "pass",
            _details(
                text_objects=text_count,
                image_objects=image_count,
                max_text_utilization=round(max(text_utilizations, default=0.0), 4),
                min_content_area_ratio=round(min(content_area_ratios, default=0.0), 4),
                max_content_area_ratio=round(max(content_area_ratios, default=0.0), 4),
            ),
        ),
        LayerSnapshot(
            "deck",
            "pass",
            _details(
                slide_count=len(plan.slides),
                max_family_run=family_run,
                max_layout_run=layout_run,
                unique_families=len({slide.family_id for slide in plan.slides}),
                unique_layouts=len({slide.layout_id for slide in plan.slides}),
            ),
        ),
    )
    return _build_report(snapshots, findings, transaction_status="pending")


def finalize_quality_report(
    report: QualityReport,
    candidate: CandidateResult,
    policy: OutputPolicy,
    *,
    export_pdf: bool,
) -> QualityReport:
    """Join transaction/package evidence to a preliminary candidate report."""

    findings = [item for item in report.findings if item.layer != "package"]
    required_steps = {
        "save-copy",
        "ooxml-package",
        "macro-disabled-reopen",
        "validation-copy-closed",
        "atomic-promote",
    }
    status = "pass"
    transaction_status = "promoted"
    if policy.no_output_deck:
        status = "skipped"
        transaction_status = "skipped"
    else:
        steps = set(candidate.validation_steps)
        if not candidate.promoted:
            findings.append(
                _finding(
                    "PACKAGE_NOT_PROMOTED",
                    "package",
                    "critical",
                    "transaction did not promote a customer deliverable",
                )
            )
        if not required_steps <= steps:
            findings.append(
                _finding(
                    "PACKAGE_VALIDATION_MISSING",
                    "package",
                    "critical",
                    "transaction evidence is missing OOXML or reopen validation",
                    missing_steps=",".join(sorted(required_steps - steps)),
                )
            )
        if export_pdf and not {"pdf-export", "pdf-header", "pdf-atomic-promote"} <= steps:
            findings.append(
                _finding(
                    "PDF_VALIDATION_MISSING",
                    "package",
                    "critical",
                    "PDF transaction evidence is incomplete",
                )
            )
        if (
            candidate.source_hash_before is not None
            and candidate.source_hash_before != candidate.source_hash_after
        ):
            findings.append(
                _finding(
                    "SOURCE_INTEGRITY_FAILURE",
                    "package",
                    "critical",
                    "source hash changed during the candidate transaction",
                )
            )
        if candidate.cleanup_errors:
            findings.append(
                _finding(
                    "CLEANUP_FAILURE",
                    "package",
                    "error",
                    "candidate transaction reported cleanup failures",
                    cleanup_count=len(candidate.cleanup_errors),
                )
            )
        if any(item.layer == "package" for item in findings):
            status = "fail"
            transaction_status = "failed"

    package = LayerSnapshot(
        "package",
        status,
        _details(
            candidate_promoted=candidate.promoted,
            validation_step_count=len(candidate.validation_steps),
            source_hash_checked=candidate.source_hash_before is not None,
            pdf_requested=export_pdf,
            cleanup_error_count=len(candidate.cleanup_errors),
        ),
    )
    snapshots = tuple(
        package if snapshot.layer == "package" else snapshot
        for snapshot in report.layers
    )
    return _build_report(
        snapshots,
        findings,
        transaction_status=transaction_status,
    )


def _propose_repair_actions(report: QualityReport) -> tuple[RepairAction, ...]:
    actions: list[RepairAction] = []
    for finding in report.findings:
        if not finding.repairable:
            continue
        values = finding.details
        if finding.code == "PAGE_SIZE_MISMATCH":
            actions.append(RepairAction("RESTORE_PAGE_SIZE", "presentation", values))
        elif finding.code == "COM_GEOMETRY_DRIFT" and finding.object_name:
            actions.append(RepairAction("RESTORE_GEOMETRY", finding.object_name, values))
        elif finding.code == "FONT_DRIFT" and finding.object_name:
            actions.append(RepairAction("RESTORE_FONT", finding.object_name, values))
        elif finding.code in {"EDITABLE_TAG_MISSING", "OBJECT_TAG_DRIFT"} and finding.object_name:
            actions.append(RepairAction("RESTORE_TAG", finding.object_name, values))
        elif finding.code == "OBJECT_NAME_DRIFT" and finding.object_name:
            actions.append(RepairAction("RESTORE_NAME", finding.object_name, values))
    # A rename invalidates all actions that still address the current COM name,
    # so it is deliberately the final write for a shape in a repair pass.
    priority = {"RESTORE_NAME": 99}
    return tuple(
        sorted(
            actions,
            key=lambda item: (
                priority.get(item.code, 10),
                item.target,
                item.code,
                item.values,
            ),
        )
    )


def _find_shape(presentation: Any, plan: RenderPlan, target: str) -> Any:
    expected_ids = {
        item.id
        for slide in plan.slides
        for item in slide.objects
        if item.name == target
    }
    for slide in _collection_items(presentation.Slides):
        by_name, by_id = _shape_maps(slide)
        if target in by_name:
            return by_name[target]
        for object_id in expected_ids:
            if object_id in by_id:
                return by_id[object_id]
    raise KeyError(f"repair target is missing: {target}")


def _apply_repair_action(
    presentation: Any, plan: RenderPlan, action: RepairAction
) -> None:
    """Apply one reversible structural action to the in-memory candidate."""

    values = action.values_dict()
    if action.code == "RESTORE_PAGE_SIZE":
        presentation.PageSetup.SlideWidth = float(values["expected_width"])
        presentation.PageSetup.SlideHeight = float(values["expected_height"])
        return
    shape = _find_shape(presentation, plan, action.target)
    if action.code == "RESTORE_GEOMETRY":
        shape.Left = float(values["left"])
        shape.Top = float(values["top"])
        shape.Width = float(values["width"])
        shape.Height = float(values["height"])
    elif action.code == "RESTORE_FONT":
        font = shape.TextFrame.TextRange.Font
        font.Name = str(values["font_name"])
        font.Size = float(values["font_size"])
    elif action.code == "RESTORE_TAG":
        shape.Tags.Add(str(values["tag_key"]), str(values["tag_value"]))
    elif action.code == "RESTORE_NAME":
        shape.Name = str(values["expected_name"])
    else:
        raise ValueError(f"unregistered repair action: {action.code}")


@dataclass
class _ShapeState:
    shape: Any
    name: str
    left: float
    top: float
    width: float
    height: float
    tags: dict[str, str]
    font_name: str | None
    font_size: float | None


@dataclass
class _CandidateState:
    page_width: float
    page_height: float
    shapes: list[_ShapeState]


def _capture_state(presentation: Any) -> _CandidateState:
    shapes: list[_ShapeState] = []
    for slide in _collection_items(presentation.Slides):
        for shape in _slide_shapes(slide):
            font = _shape_font(shape)
            shapes.append(
                _ShapeState(
                    shape=shape,
                    name=str(getattr(shape, "Name", "")),
                    left=float(shape.Left),
                    top=float(shape.Top),
                    width=float(shape.Width),
                    height=float(shape.Height),
                    tags=_tag_values(shape),
                    font_name=str(font.Name) if font is not None else None,
                    font_size=float(font.Size) if font is not None else None,
                )
            )
    return _CandidateState(
        page_width=float(presentation.PageSetup.SlideWidth),
        page_height=float(presentation.PageSetup.SlideHeight),
        shapes=shapes,
    )


def _restore_state(presentation: Any, state: _CandidateState) -> None:
    presentation.PageSetup.SlideWidth = state.page_width
    presentation.PageSetup.SlideHeight = state.page_height
    for item in state.shapes:
        shape = item.shape
        shape.Name = item.name
        shape.Left = item.left
        shape.Top = item.top
        shape.Width = item.width
        shape.Height = item.height
        values = getattr(shape.Tags, "values", None)
        if isinstance(values, dict):
            values.clear()
            values.update(item.tags)
        else:
            current = _tag_values(shape)
            for key in current:
                if key not in item.tags:
                    try:
                        shape.Tags.Delete(key)
                    except Exception:
                        pass
            for key, value in item.tags.items():
                shape.Tags.Add(key, value)
        font = _shape_font(shape)
        if font is not None and item.font_name is not None and item.font_size is not None:
            font.Name = item.font_name
            font.Size = item.font_size


def repair_quality(
    plan: RenderPlan,
    render_report: RenderReport,
    presentation: Any,
    report: QualityReport,
    *,
    max_passes: int = 2,
) -> RepairLog:
    """Run at most two monotonic, reversible repair passes on the candidate."""

    if isinstance(max_passes, bool) or not isinstance(max_passes, int) or max_passes < 1:
        raise ValueError("max_passes must be a positive integer")
    bounded_passes = min(max_passes, 2)
    current = report
    passes: list[RepairPass] = []
    changed = False
    for pass_index in range(1, bounded_passes + 1):
        actions = _propose_repair_actions(current)
        if not actions:
            break
        state = _capture_state(presentation)
        before_score = current.weighted_score
        before_hard = current.hard_gate_failures
        failure_code: str | None = None
        try:
            for action in actions:
                _apply_repair_action(presentation, plan, action)
            candidate = inspect_quality(plan, render_report, presentation)
        except Exception:
            try:
                _restore_state(presentation, state)
            except Exception as rollback_error:
                raise QualityGateError(
                    "candidate repair failed and its in-memory rollback also failed"
                ) from rollback_error
            candidate = current
            failure_code = "REPAIR_ACTION_FAILED"
        new_hard = set(candidate.hard_gate_failures) - set(before_hard)
        accepted = (
            failure_code is None
            and candidate.weighted_score < current.weighted_score
            and not new_hard
        )
        rolled_back = failure_code is not None
        if accepted:
            changed = True
            current = candidate
        elif failure_code is None:
            _restore_state(presentation, state)
            rolled_back = True
        passes.append(
            RepairPass(
                index=pass_index,
                actions=actions,
                before_score=before_score,
                after_score=candidate.weighted_score,
                accepted=accepted,
                rolled_back=rolled_back,
                hard_gate_failures_before=before_hard,
                hard_gate_failures_after=candidate.hard_gate_failures,
                failure_code=failure_code,
            )
        )
        if not accepted:
            break
    return RepairLog(
        schema_version=REPAIR_LOG_VERSION,
        max_passes=bounded_passes,
        passes=tuple(passes),
        changed=changed,
        final_report=current,
    )


def write_quality_artifacts(
    report: QualityReport,
    repair: RepairLog,
    audit_dir: Path | str,
) -> dict[str, str]:
    """Atomically persist the stable report and repair log after the pipeline."""

    target_dir = Path(audit_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "quality_report": target_dir / "quality-report.json",
        "repair_log": target_dir / "repair-log.json",
    }
    payloads = {
        "quality_report": report.to_dict(),
        "repair_log": repair.to_dict(),
    }
    result: dict[str, str] = {}
    for key, target in outputs.items():
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target_dir,
                prefix=f".{target.stem}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                json.dump(payloads[key], handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
                temporary_path = Path(handle.name)
            os.replace(temporary_path, target)
            result[key] = str(target)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
    return result


__all__ = [
    "HARD_GATE_CODES",
    "QUALITY_LAYERS",
    "LayerSnapshot",
    "QualityFinding",
    "QualityGateError",
    "QualityReport",
    "RepairAction",
    "RepairLog",
    "RepairPass",
    "finalize_quality_report",
    "inspect_quality",
    "repair_quality",
    "write_quality_artifacts",
]
