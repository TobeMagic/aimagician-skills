"""Pure compilation from semantic DeckPlan input to governed render commands."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .assets import (
    AssetIntent,
    AssetRecord,
    choose_asset,
    read_raster_dimensions,
    read_svg_aspect_ratio,
)
from .deck_plan import (
    CHART_INTENTS,
    CONTENT_KINDS,
    DATA_ITEM_FIELDS,
    EXTERNAL_HYPERLINK,
    IDENTIFIER,
    DeckPlan,
    compile_deck_plan,
)
from .layouts import (
    ResolvedLayout,
    ResolvedSlot,
    SlideSize,
    load_components,
    load_layout_registry,
    resolve_layout,
    validate_registry_bundle,
)
from .themes import (
    HEX_COLOR,
    THEME_IDS,
    BrandOverrides,
    ResolutionEvent,
    contrast_ratio,
    mix_color,
    resolve_theme,
    select_theme,
)
from .text_layout import estimate_text_layout


RENDER_PLAN_VERSION = "1.0"
MIN_POWERPOINT_SLIDE_IN = 1.0
MAX_POWERPOINT_SLIDE_IN = 56.0
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg"}
ADVANCED_COMPONENTS = {
    "chart",
    "table",
    "process-step",
    "timeline-node",
    "matrix-cell",
}
ADVANCED_KINDS = {"chart", "table", "diagram"}
CHART_TYPES = {"line", "column", "bar", "doughnut", "stacked-column", "scatter"}
CHART_TYPE_BY_SEMANTIC_FORM = {
    "line-chart": "line",
    "area-chart": "line",
    "bar-chart": "bar",
    "composition-chart": "doughnut",
    "stacked-bar": "stacked-column",
    "distribution-chart": "column",
    "dot-plot": "column",
    "scatter-plot": "scatter",
    "bubble-chart": "scatter",
}
INTERNAL_SELECTED_FORM_FIELD = "_selected_form"
DIAGRAM_TYPES = {"process", "timeline", "matrix", "quadrant", "funnel", "roadmap"}
TEXT_COMPONENTS = {"title", "body-text", "footer", "statement"}
LAYER_BY_COMPONENT = {
    "decoration": 10,
    "accent": 10,
    "image-frame": 20,
    "card": 30,
    "kpi": 30,
    "chart": 30,
    "table": 30,
    "process-step": 30,
    "timeline-node": 30,
    "matrix-cell": 30,
    "comparison-panel": 30,
    "risk-panel": 30,
    "recommendation-panel": 30,
    "team-member": 30,
    "body-text": 40,
    "statement": 40,
    "quote": 40,
    "cta": 40,
    "title": 50,
    "footer": 90,
}


class RenderPlanError(ValueError):
    """A governed render plan could not be built safely."""


@dataclass(frozen=True)
class AssetBinding:
    """A local file paired with the Phase 24 evidence used to select it."""

    path: Path
    record: AssetRecord


@dataclass(frozen=True)
class RenderFinding:
    code: str
    path: str
    message: str
    severity: str = "warning"

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class ChartSeries:
    name: str
    values: tuple[float | None, ...]
    x_values: tuple[float, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "values": list(self.values),
        }
        if self.x_values:
            result["x_values"] = list(self.x_values)
        return result


@dataclass(frozen=True)
class ChartSpec:
    chart_type: str
    categories: tuple[str, ...]
    series: tuple[ChartSeries, ...]
    value_unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "kind": "chart",
            "chart_type": self.chart_type,
            "categories": list(self.categories),
            "series": [item.to_dict() for item in self.series],
        }
        if self.value_unit is not None:
            result["value_unit"] = self.value_unit
        return result


@dataclass(frozen=True)
class TableSpec:
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "table",
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
        }


@dataclass(frozen=True)
class DiagramNode:
    label: str
    detail: str | None = None

    def to_dict(self) -> dict[str, str]:
        result = {"label": self.label}
        if self.detail is not None:
            result["detail"] = self.detail
        return result


@dataclass(frozen=True)
class DiagramSpec:
    diagram_type: str
    nodes: tuple[DiagramNode, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "diagram",
            "diagram_type": self.diagram_type,
            "nodes": [node.to_dict() for node in self.nodes],
        }


AdvancedSpec = ChartSpec | TableSpec | DiagramSpec


@dataclass(frozen=True)
class TextRun:
    text: str
    font_size_pt: int
    text_color: str
    bold: bool
    italic: bool = False
    break_after: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "font_size_pt": self.font_size_pt,
            "text_color": self.text_color,
            "bold": self.bold,
            "italic": self.italic,
            "break_after": self.break_after,
        }


@dataclass(frozen=True)
class RenderObject:
    id: str
    name: str
    component: str
    kind: str
    x: float
    y: float
    width: float
    height: float
    layer: int
    group_id: str | None
    native_editable: bool
    text: str | None
    source_path: Path | None
    asset_record: AssetRecord | None
    font_name: str
    font_size_pt: int
    text_color: str
    fill_color: str
    line_color: str
    advanced: AdvancedSpec | None
    semantic_source: str | None
    hyperlink: str | None
    text_runs: tuple[TextRun, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "component": self.component,
            "kind": self.kind,
            "bounds_in": {
                "x": self.x,
                "y": self.y,
                "width": self.width,
                "height": self.height,
            },
            "layer": self.layer,
            "group_id": self.group_id,
            "native_editable": self.native_editable,
            "text": self.text,
            "source_path": str(self.source_path) if self.source_path else None,
            "asset_record": (
                {
                    "id": self.asset_record.id,
                    "kind": self.asset_record.kind,
                    "style": self.asset_record.style,
                    "aspect_ratio": self.asset_record.aspect_ratio,
                    "quality": self.asset_record.quality,
                    "source": self.asset_record.source,
                    "license": self.asset_record.license,
                    "retrieved_at": self.asset_record.retrieved_at,
                    "width_px": self.asset_record.width_px,
                    "height_px": self.asset_record.height_px,
                    "icon_family": self.asset_record.icon_family,
                }
                if self.asset_record is not None
                else None
            ),
            "font_name": self.font_name,
            "font_size_pt": self.font_size_pt,
            "text_color": self.text_color,
            "fill_color": self.fill_color,
            "line_color": self.line_color,
            "advanced": self.advanced.to_dict() if self.advanced is not None else None,
            "semantic_source": self.semantic_source,
            "hyperlink": self.hyperlink,
            **(
                {"text_runs": [run.to_dict() for run in self.text_runs]}
                if self.text_runs is not None
                else {}
            ),
        }


@dataclass(frozen=True)
class RenderSlide:
    source_id: str
    index: int
    role: str
    title: str | None
    family_id: str
    layout_id: str
    item_count: int
    requested_density: str
    resolved_density: str
    background_color: str
    objects: tuple[RenderObject, ...]
    speaker_notes: str | None
    motion: str
    composition_id: str | None = None
    variant_id: str | None = None
    emphasis: str = "standard"
    energy: str = "flow"
    fact_refs: tuple[str, ...] = ()
    component_intents: tuple[str, ...] = ()
    asset_intents: tuple[str, ...] = ()
    motif_id: str | None = None
    motif_variant: str | None = None
    motif_intensity: str | None = None
    direction_annotation: tuple[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "index": self.index,
            "role": self.role,
            "title": self.title,
            "family_id": self.family_id,
            "layout_id": self.layout_id,
            "item_count": self.item_count,
            "requested_density": self.requested_density,
            "resolved_density": self.resolved_density,
            "background_color": self.background_color,
            "objects": [item.to_dict() for item in self.objects],
            "speaker_notes": self.speaker_notes,
            "motion": self.motion,
            "composition_id": self.composition_id,
            "variant_id": self.variant_id,
            "emphasis": self.emphasis,
            "energy": self.energy,
            "fact_refs": list(self.fact_refs),
            "component_intents": list(self.component_intents),
            "asset_intents": list(self.asset_intents),
            "motif_id": self.motif_id,
            "motif_variant": self.motif_variant,
            "motif_intensity": self.motif_intensity,
            "direction_annotation": (
                list(self.direction_annotation)
                if self.direction_annotation is not None
                else None
            ),
        }


@dataclass(frozen=True)
class RenderPlan:
    schema_version: str
    compiler_version: str
    project_title: str
    theme_id: str
    brand: BrandOverrides
    locale: str
    installed_fonts: tuple[str, ...]
    slide_size: SlideSize
    background_color: str
    slides: tuple[RenderSlide, ...]
    findings: tuple[RenderFinding, ...]
    theme_events: tuple[ResolutionEvent, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "compiler_version": self.compiler_version,
            "project_title": self.project_title,
            "theme_id": self.theme_id,
            "brand": {
                "primary": self.brand.primary,
                "accent": self.brand.accent,
                "positive": self.brand.positive,
                "warning": self.brand.warning,
                "negative": self.brand.negative,
                "background": self.brand.background,
                "heading_font": self.brand.heading_font,
                "body_font": self.brand.body_font,
            },
            "locale": self.locale,
            "installed_fonts": list(self.installed_fonts),
            "slide_size": {
                "width_in": self.slide_size.width,
                "height_in": self.slide_size.height,
            },
            "background_color": self.background_color,
            "slides": [slide.to_dict() for slide in self.slides],
            "findings": [finding.to_dict() for finding in self.findings],
            "theme_events": [
                {
                    "code": item.code,
                    "field": item.field,
                    "requested": item.requested,
                    "resolved": item.resolved,
                }
                for item in self.theme_events
            ],
        }


def inches_to_points(value: float | int) -> float:
    """Convert governed inches to PowerPoint points at the single unit boundary."""

    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise RenderPlanError("geometry must be finite and non-negative")
    return float(value) * 72


def _safe_identifier(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return normalized[:40] or "object"


def _format_item(value: Any) -> str:
    if isinstance(value, dict):
        labels = ["title", "label", "name", "description", "text"]
        heading_key = next((key for key in labels if key in value), None)
        heading = str(value[heading_key]) if heading_key is not None else ""
        metric = ""
        if "value" in value:
            raw_metric = value["value"]
            metric = (
                f"{raw_metric:,}"
                if isinstance(raw_metric, int)
                and not isinstance(raw_metric, bool)
                and abs(raw_metric) >= 10_000
                else str(raw_metric)
            )
            if value.get("unit") is not None:
                unit = str(value["unit"])
                metric += unit if unit in {"%", "°", "℃", "℉"} else f" {unit}"
        remaining = [
            str(value[key])
            for key in sorted(value)
            if key not in {heading_key, "value", "unit"}
            and str(value[key]).strip()
            and str(value[key]).strip().casefold()
            not in {heading.strip().casefold(), metric.strip().casefold()}
        ]
        return "\n".join(part for part in (heading, metric, *remaining) if part)
    return str(value)


def _rich_text_runs(
    component: str,
    text: str | None,
    *,
    value_font_size_pt: int,
    typography: Mapping[str, int],
    colors: Mapping[str, str],
) -> tuple[TextRun, ...] | None:
    """Create an editable label/value/context hierarchy for metric panels."""

    if (
        component == "cta"
        and text
        and "→" in text
        and re.search(r"\n\s*\n", text) is None
    ):
        match = re.search(r"\d+(?:\s*→\s*\d+)+", text)
        if match is not None:
            runs: list[TextRun] = []
            before = text[: match.start()]
            metric = match.group(0)
            after = text[match.end() :]
            first_suffix, separator, remainder = after.partition("\n")
            if before:
                runs.append(
                    TextRun(
                        text=before,
                        font_size_pt=typography["body"],
                        text_color=colors["text"],
                        bold=False,
                        break_after=False,
                    )
                )
            runs.append(
                TextRun(
                    text=metric,
                    font_size_pt=value_font_size_pt,
                    text_color=colors["primary"],
                    bold=True,
                    break_after=not bool(first_suffix),
                )
            )
            if first_suffix:
                runs.append(
                    TextRun(
                        text=first_suffix,
                        font_size_pt=typography["body"],
                        text_color=colors["text"],
                        bold=False,
                        break_after=bool(separator),
                    )
                )
            if separator and remainder:
                runs.append(
                    TextRun(
                        text=remainder,
                        font_size_pt=typography["body"],
                        text_color=colors["muted_text"],
                        bold=False,
                        break_after=False,
                    )
                )
            return tuple(runs)
    if component not in {"kpi", "comparison-panel", "recommendation-panel"} or not text:
        return None
    lines = text.split("\n")
    if len(lines) < 2 or any(not line.strip() for line in lines):
        return None
    runs: list[TextRun] = []
    for index, line in enumerate(lines):
        is_value = index == 1
        runs.append(
            TextRun(
                text=line,
                font_size_pt=(
                    value_font_size_pt if is_value else typography["body"]
                ),
                text_color=(
                    colors["primary"] if is_value else colors["muted_text"]
                ),
                bold=is_value,
                break_after=index < len(lines) - 1,
            )
        )
    return tuple(runs)


def _canonical_semantic_block(block: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(block),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _load_semantic_block(source: str) -> dict[str, Any]:
    try:
        value = json.loads(source)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RenderPlanError("advanced semantic source is not canonical JSON") from exc
    if not isinstance(value, dict) or _canonical_semantic_block(value) != source:
        raise RenderPlanError("advanced semantic source is not canonical JSON")
    allowed = {
        "id",
        "kind",
        "title",
        "text",
        "items",
        "role_hint",
        "chart_intent",
        "source_ref",
        "hyperlink",
        INTERNAL_SELECTED_FORM_FIELD,
    }
    if set(value) - allowed or not isinstance(value.get("id"), str):
        raise RenderPlanError("advanced semantic source crossed the governed boundary")
    if not isinstance(value.get("kind"), str):
        raise RenderPlanError("advanced semantic source has no registered kind")
    if value["kind"] not in CONTENT_KINDS:
        raise RenderPlanError("advanced semantic source has an unregistered kind")
    chart_intent = value.get("chart_intent")
    if chart_intent is not None and chart_intent not in CHART_INTENTS:
        raise RenderPlanError("advanced semantic source has an unregistered chart intent")
    selected_form = value.get(INTERNAL_SELECTED_FORM_FIELD)
    if (
        selected_form is not None
        and selected_form not in CHART_TYPE_BY_SEMANTIC_FORM
    ):
        raise RenderPlanError("advanced semantic source has an unregistered selected form")
    hyperlink = value.get("hyperlink")
    if hyperlink is not None:
        if not isinstance(hyperlink, str) or len(hyperlink) > 2048:
            raise RenderPlanError("advanced semantic source hyperlink is invalid")
        if hyperlink.startswith("slide:"):
            if not IDENTIFIER.fullmatch(hyperlink.removeprefix("slide:")):
                raise RenderPlanError("advanced semantic source hyperlink is invalid")
        elif not EXTERNAL_HYPERLINK.fullmatch(hyperlink):
            raise RenderPlanError("advanced semantic source hyperlink is unsafe")
    items = value.get("items", [])
    if not isinstance(items, list):
        raise RenderPlanError("advanced semantic source items must be an array")
    for item in items:
        if isinstance(item, dict):
            if not item or len(item) > 5 or set(item) - DATA_ITEM_FIELDS:
                raise RenderPlanError(
                    "advanced semantic source contains an ungoverned data item"
                )
            if any(
                nested is not None
                and not isinstance(nested, (str, int, float, bool))
                for nested in item.values()
            ):
                raise RenderPlanError(
                    "advanced semantic source data items must contain scalars"
                )
        elif item is not None and not isinstance(item, (str, int, float, bool)):
            raise RenderPlanError(
                "advanced semantic source items must be scalar or controlled data"
            )
        numeric_values = item.values() if isinstance(item, dict) else (item,)
        if any(
            isinstance(nested, float) and not math.isfinite(nested)
            for nested in numeric_values
        ):
            raise RenderPlanError("advanced semantic source contains a non-finite number")
    return value


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _item_label(item: Any, index: int) -> str:
    if isinstance(item, dict):
        for field in ("category", "date", "label", "title", "name", "id"):
            value = item.get(field)
            if isinstance(value, str) and value:
                return value
    if isinstance(item, str) and item:
        return item
    return f"Item {index + 1}"


def _chart_value(item: Mapping[str, Any]) -> float | None:
    for field in (
        "value",
        "actual",
        "primary",
        "secondary",
        "target",
        "before",
        "after",
        "probability",
        "impact",
        "start",
        "end",
    ):
        value = _numeric(item.get(field))
        if value is not None:
            return value
    return None


def semantic_form_chart_type(
    selected_form: str | None,
    intent: str | None,
) -> str:
    """Map a semantic form to the closest supported native PowerPoint chart."""

    if selected_form in CHART_TYPE_BY_SEMANTIC_FORM:
        return CHART_TYPE_BY_SEMANTIC_FORM[selected_form]
    return {
        "trend": "line",
        "comparison": "column",
        "composition": "doughnut",
        "distribution": "column",
        "relationship": "scatter",
    }.get(intent or "", "column")


def _chart_spec(
    block: Mapping[str, Any],
    selected_form: str | None = None,
) -> ChartSpec | None:
    raw_items = block.get("items", [])
    if not isinstance(raw_items, list):
        return None
    intent = block.get("chart_intent") or block.get("kind")
    chart_type = semantic_form_chart_type(selected_form, intent)
    if chart_type == "scatter":
        points: list[tuple[str, float, float]] = []
        for index, item in enumerate(raw_items):
            if not isinstance(item, dict):
                continue
            x_value = next(
                (
                    value
                    for field in ("primary", "actual", "start", "before", "value")
                    if (value := _numeric(item.get(field))) is not None
                ),
                None,
            )
            y_value = next(
                (
                    value
                    for field in ("secondary", "target", "end", "after", "impact")
                    if (value := _numeric(item.get(field))) is not None
                ),
                None,
            )
            if x_value is not None and y_value is not None:
                points.append((_item_label(item, index), x_value, y_value))
        if not points:
            return None
        return ChartSpec(
            chart_type="scatter",
            categories=tuple(point[0] for point in points),
            series=(
                ChartSeries(
                    name=str(block.get("title") or "Relationship"),
                    values=tuple(point[2] for point in points),
                    x_values=tuple(point[1] for point in points),
                ),
            ),
        )

    categories: list[str] = []
    series_order: list[str] = []
    values_by_series: dict[str, dict[str, float]] = {}
    plotted_units: list[str | None] = []
    default_series = str(block.get("title") or "Value")
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        value = _chart_value(item)
        if value is None:
            continue
        category = _item_label(item, index)
        series_name = str(item.get("series") or default_series)
        raw_unit = item.get("unit")
        plotted_units.append(
            raw_unit.strip()
            if isinstance(raw_unit, str) and raw_unit.strip()
            else None
        )
        if category not in categories:
            categories.append(category)
        if series_name not in series_order:
            series_order.append(series_name)
        values_by_series.setdefault(series_name, {})[category] = value
    if not categories or not series_order:
        return None
    if chart_type == "doughnut" and len(series_order) > 1:
        chart_type = "stacked-column"
    value_unit = None
    if plotted_units and all(unit is not None for unit in plotted_units):
        normalized_units = {str(unit).casefold() for unit in plotted_units}
        if len(normalized_units) == 1:
            value_unit = str(plotted_units[0])
    return ChartSpec(
        chart_type=chart_type,
        categories=tuple(categories),
        series=tuple(
            ChartSeries(
                name=name,
                values=tuple(values_by_series[name].get(category) for category in categories),
            )
            for name in series_order
        ),
        value_unit=value_unit,
    )


_TABLE_FIELD_ORDER = (
    "label",
    "title",
    "name",
    "category",
    "series",
    "value",
    "unit",
    "actual",
    "target",
    "before",
    "after",
    "status",
    "date",
    "owner",
    "probability",
    "impact",
    "primary",
    "secondary",
    "start",
    "end",
    "group",
    "source",
    "description",
    "text",
    "id",
)


def _display_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _table_spec(block: Mapping[str, Any]) -> TableSpec | None:
    items = block.get("items", [])
    if not isinstance(items, list) or not items:
        return None
    if all(isinstance(item, dict) for item in items):
        fields = tuple(
            field
            for field in _TABLE_FIELD_ORDER
            if any(field in item for item in items)
        )[:5]
        if not fields:
            return None
        return TableSpec(
            columns=tuple(field.replace("_", " ").title() for field in fields),
            rows=tuple(
                tuple(_display_scalar(item.get(field)) for field in fields)
                for item in items
            ),
        )
    return TableSpec(
        columns=("Value",),
        rows=tuple((_display_scalar(item),) for item in items),
    )


def _diagram_nodes(block: Mapping[str, Any]) -> tuple[DiagramNode, ...]:
    items = block.get("items", [])
    result: list[DiagramNode] = []
    for index, item in enumerate(items if isinstance(items, list) else []):
        label = _item_label(item, index)
        detail: str | None = None
        if isinstance(item, dict):
            for field in ("description", "text", "status", "date", "owner"):
                value = item.get(field)
                if value is not None and str(value) != label:
                    detail = str(value)
                    break
        result.append(DiagramNode(label=label, detail=detail))
    if not result:
        text = block.get("text") or block.get("title")
        if isinstance(text, str) and text:
            result.append(DiagramNode(label=text))
    return tuple(result)


def _diagram_node_partition(
    nodes: tuple[DiagramNode, ...], index: int, count: int
) -> tuple[DiagramNode, ...]:
    if count <= 1:
        return nodes
    start = len(nodes) * index // count
    end = len(nodes) * (index + 1) // count
    return nodes[start:end]


def _advanced_spec(
    component: str,
    family_id: str,
    block: Mapping[str, Any],
    *,
    advanced_index: int,
    advanced_count: int,
    selected_form: str | None = None,
) -> AdvancedSpec | None:
    if selected_form is None:
        preserved_form = block.get(INTERNAL_SELECTED_FORM_FIELD)
        if isinstance(preserved_form, str):
            selected_form = preserved_form
    if family_id in DIAGRAM_TYPES:
        nodes = _diagram_nodes(block)
        if advanced_count > 1:
            nodes = _diagram_node_partition(nodes, advanced_index, advanced_count)
        return DiagramSpec(family_id, nodes) if nodes else None
    if component == "chart":
        return _chart_spec(block, selected_form)
    if component == "table":
        return _table_spec(block)
    if component in {"process-step", "timeline-node", "matrix-cell"}:
        diagram_type = {
            "process-step": "process",
            "timeline-node": "timeline",
            "matrix-cell": "matrix",
        }[component]
        nodes = _diagram_nodes(block)
        if advanced_count > 1:
            nodes = _diagram_node_partition(nodes, advanced_index, advanced_count)
        return DiagramSpec(diagram_type, nodes) if nodes else None
    return None


def _bounded_existing_text(value: object, limit: int) -> str | None:
    if not isinstance(value, str) or not value.strip() or limit < 1:
        return None
    text = re.sub(r"\s+", " ", value).strip()
    if len("".join(text.split())) <= limit:
        return text
    complete = tuple(re.finditer(r"[.!?。！？;；]", text))
    for match in reversed(complete):
        candidate = text[: match.end()].strip()
        if (
            len(candidate) >= 10
            and len("".join(candidate.split())) <= limit
        ):
            return candidate
    return None


def _existing_support_text(
    block: Mapping[str, Any], limit: int
) -> str | None:
    """Select only bounded text already present in the governed semantic block."""

    for field in ("title", "text"):
        candidate = _bounded_existing_text(block.get(field), limit)
        if candidate is not None:
            return candidate
    items = block.get("items", [])
    if not isinstance(items, list):
        return None
    accepted: list[str] = []
    for item in items:
        candidate = _bounded_existing_text(_format_item(item), limit)
        if candidate is None:
            continue
        combined = " · ".join((*accepted, candidate))
        if len("".join(combined.split())) > limit:
            break
        accepted.append(candidate)
    return " · ".join(accepted) if accepted else None


def _advanced_focus_selector(family_id: str) -> str | None:
    return {
        "data-chart": "data-chart.full",
        "table": "table.summary",
        "process": "process.focus",
        "timeline": "timeline.focus",
        "matrix": "matrix.focus",
        "quadrant": "quadrant.focus",
        "funnel": "funnel.compact",
        "roadmap": "roadmap.focus",
    }.get(family_id)


def _resolve_advanced_focus_layout(
    family_id: str,
    *,
    title: str,
    slide_size: SlideSize,
    previous_layouts: tuple[str, ...],
    item_count: int,
    density: str,
    forbidden_components: frozenset[str],
    component_limits: Mapping[str, int] | None,
    typography: Mapping[str, int],
) -> ResolvedLayout | None:
    """Choose an evidence-safe advanced composition without repeating a page.

    Advanced layouts may reserve a governed support-text slot.  When the
    source block contains no bounded support copy, only variants whose native
    advanced object can stand alone are eligible.  The preferred focus
    variant remains the stable default, but an immediately repeated variant
    is rotated to another same-family composition when one exists.
    """

    preferred_id = _advanced_focus_selector(family_id)
    if preferred_id is None:
        return None
    registry = load_layout_registry()
    family = registry.families.get(family_id)
    if family is None:
        return None
    recent = previous_layouts[-2:]
    candidates: list[tuple[int, int, int, int, ResolvedLayout]] = []
    for index, variant_id in enumerate(family.variant_ids):
        try:
            candidate = resolve_layout(
                variant_id,
                slide_size,
                previous_layouts,
                item_count=item_count,
                density=density,
                forbidden_components=forbidden_components,
                component_limits=component_limits,
            )
        except ValueError:
            continue
        if not any(
            slot.component in ADVANCED_COMPONENTS for slot in candidate.slots
        ):
            continue
        if _governed_text_slots(candidate):
            continue
        if len("".join(title.split())) > _title_capacity(candidate, typography):
            continue
        candidates.append(
            (
                int(bool(previous_layouts) and candidate.id == previous_layouts[-1]),
                recent.count(candidate.id),
                int(candidate.id != preferred_id),
                index,
                candidate,
            )
        )
    if not candidates:
        return None
    return min(candidates, key=lambda item: item[:4])[4]


def _block_content(block: Mapping[str, Any]) -> list[str]:
    items = block.get("items", [])
    if items:
        return [_format_item(item) for item in items]
    for key in ("text", "title"):
        if block.get(key):
            return [str(block[key])]
    return []


def _slide_content(slide: Mapping[str, Any]) -> tuple[list[str], dict[str, str]]:
    fragments: list[str] = []
    sources: dict[str, str] = {}
    for block in slide["blocks"]:
        block_id = block["id"]
        if block.get("kind") == "image" and block.get("source_ref"):
            sources[block_id] = block["source_ref"]
        fragments.extend(_block_content(block))
    return fragments, sources


def _without_title_duplication(
    fragments: list[str], slide_title: str | None
) -> list[str]:
    """Remove exact title echoes while preserving every distinct detail."""

    if not isinstance(slide_title, str) or not slide_title.strip():
        return fragments
    if len(fragments) > 1:
        return fragments
    normalized_title = re.sub(r"\s+", " ", slide_title).strip().casefold()
    result: list[str] = []
    for fragment in fragments:
        normalized_fragment = re.sub(r"\s+", " ", fragment).strip()
        folded = normalized_fragment.casefold()
        if folded == normalized_title:
            continue
        if folded.startswith(normalized_title):
            remainder = normalized_fragment[len(slide_title.strip()) :].lstrip(
                " \t\r\n:：,，;；-–—"
            )
            if remainder:
                result.append(remainder)
            continue
        result.append(fragment)
    return result


def _item_count(slide: Mapping[str, Any]) -> int:
    basis_id = slide["semantic_basis"]["block_id"]
    block = next(item for item in slide["blocks"] if item["id"] == basis_id)
    semantic_type = str(slide["semantic_basis"].get("semantic_type", ""))
    basis_count = sum(
        len(candidate.get("items", []))
        or int(bool(candidate.get("text") or candidate.get("title")))
        for candidate in slide["blocks"]
        if (
            "categorical-comparison"
            if candidate.get("kind") == "comparison"
            and candidate.get("chart_intent") == "comparison"
            else str(candidate.get("chart_intent") or candidate.get("kind"))
        )
        == semantic_type
    ) or (len(block.get("items", [])) or 1)
    referenced_assets = sum(
        1
        for item in slide["blocks"]
        if item.get("kind") == "image" and item.get("source_ref")
    )
    return max(basis_count, referenced_assets)


def _uses_compact_three_cards(block: Mapping[str, Any]) -> bool:
    """Select the compact tile recipe only for three short authored labels."""

    items = block.get("items")
    if block.get("kind") != "bullets" or not isinstance(items, list) or len(items) != 3:
        return False
    return all(
        isinstance(item, str)
        and bool(item.strip())
        and "\n" not in item
        and len("".join(item.split())) <= 40
        for item in items
    )


def _slot_texts(slots: tuple[ResolvedSlot, ...], fragments: list[str]) -> dict[str, str]:
    content_slots = [
        slot
        for slot in slots
        if slot.component
        not in {
            "title",
            "footer",
            "image-frame",
            "decoration",
            "accent",
            *ADVANCED_COMPONENTS,
        }
    ]
    if not content_slots or not fragments:
        return {}
    if len(content_slots) == 1:
        return {content_slots[0].id: "\n\n".join(fragments)}
    result: dict[str, str] = {}
    loads = [0 for _ in content_slots]
    for index, fragment in enumerate(fragments):
        target_index = (
            index
            if index < len(content_slots)
            else min(range(len(content_slots)), key=lambda item: (loads[item], item))
        )
        slot = content_slots[target_index]
        result[slot.id] = (
            result[slot.id] + "\n\n" + fragment
            if slot.id in result
            else fragment
        )
        loads[target_index] = len("".join(result[slot.id].split()))
    return result


def _governed_text_slots(layout: ResolvedLayout) -> tuple[ResolvedSlot, ...]:
    return tuple(
        slot
        for slot in layout.slots
        if slot.component
        not in {
            "title",
            "footer",
            "image-frame",
            "decoration",
            "accent",
            *ADVANCED_COMPONENTS,
        }
    )


def _complete_slot_texts(
    layout: ResolvedLayout,
    fragments: list[str],
    slide: Mapping[str, Any],
    project: Mapping[str, Any],
) -> dict[str, str]:
    poster_close = (
        _poster_closing_slot_texts("\n\n".join(fragments))
        if layout.id == "cta.poster-editorial"
        else None
    )
    decision_close = (
        _decision_three_slot_texts(
            "\n\n".join(fragments),
            scenario=str(project.get("scenario", "")),
        )
        if layout.id == "cta.decision-three"
        else None
    )
    result = poster_close or decision_close or _slot_texts(layout.slots, fragments)
    if layout.id == "cta.decision-three":
        scenario = str(project.get("scenario", "")).casefold()
        labels = (
            ("01 · DECIDE", "02 · EVIDENCE", "03 · NEXT TEST")
            if scenario == "data-analysis"
            else ("01 · APPROVE", "02 · OPEN RISK", "03 · CEILING")
        )
        if decision_close is None:
            for slot_id, label in zip(("one", "two", "three"), labels, strict=True):
                if result.get(slot_id):
                    result[slot_id] = f"{label}\n{result[slot_id]}"
    empty = tuple(
        slot for slot in _governed_text_slots(layout) if not result.get(slot.id)
    )
    if len(empty) > 1:
        raise RenderPlanError(
            f"layout {layout.id} leaves multiple governed text slots unfilled"
        )
    if empty:
        result[empty[0].id] = _supporting_slot_text(slide, project)
    return result


def _decision_three_slot_texts(
    text: str,
    *,
    scenario: str,
) -> dict[str, str] | None:
    """Preserve a proof line plus three explicit decisions in three CTA cards."""

    parsed = _poster_closing_slot_texts(text)
    if parsed is None:
        return None
    labels = (
        ("01 · DECIDE", "02 · EVIDENCE", "03 · NEXT TEST")
        if scenario.casefold() == "data-analysis"
        else ("01 · APPROVE", "02 · OWNER", "03 · START")
    )
    return {
        "one": (
            f"{labels[0]}\n{parsed['decision-one']}\n"
            f"{parsed['primary']}"
        ),
        "two": f"{labels[1]}\n{parsed['decision-two']}",
        "three": f"{labels[2]}\n{parsed['decision-three']}",
    }


def _poster_closing_slot_texts(text: str) -> dict[str, str] | None:
    """Parse the governed consulting close into one proof line and three chips."""

    paragraphs = [
        item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()
    ]
    if len(paragraphs) != 2:
        return None
    decision_line = re.sub(
        r"^(?:决策|decision)\s*[:：]\s*",
        "",
        paragraphs[1],
        flags=re.IGNORECASE,
    )
    decisions = [
        item.strip()
        for item in re.split(r"[｜|]", decision_line)
        if item.strip()
    ]
    if len(decisions) != 3:
        return None
    primary = paragraphs[0]
    if len("".join(primary.split())) > 18 and " · " in primary:
        lead, tail = primary.rsplit(" · ", 1)
        primary = f"{lead}\n{tail}"
    return {
        "primary": primary,
        "decision-one": decisions[0],
        "decision-two": decisions[1],
        "decision-three": decisions[2],
    }


def _supporting_slot_text(
    slide: Mapping[str, Any], project: Mapping[str, Any]
) -> str:
    title = str(slide.get("title") or "").strip().casefold()
    raw_role = str(slide.get("role") or "")
    language = str(project.get("language") or "").casefold()
    localized_roles = {
        "cover": "提案概览",
        "section": "章节导读",
        "closing": "决策事项",
        "next-steps": "下一步行动",
        "recommendations": "建议行动",
        "risks": "风险与应对",
        "team": "治理机制",
        "timeline": "关键里程碑",
    }
    role = (
        localized_roles.get(raw_role, raw_role.replace("-", " "))
        if language.startswith("zh")
        else raw_role.replace("-", " ").title()
    )
    contextual = [
        str(project.get("objective") or "").strip(),
        (
            f"For {str(project.get('audience')).strip()}"
            if project.get("audience")
            else ""
        ),
        str(project.get("scenario") or "").replace("-", " ").title(),
    ]
    candidates = (
        contextual + [role]
        if slide.get("role") in {"cover", "closing"}
        else [role, *contextual]
    )
    return next(
        (
            candidate
            for candidate in candidates
            if candidate and candidate.casefold() != title
        ),
        "Key takeaway",
    )


def _poster_title_text(title: str, *, layout_id: str) -> str:
    """Add a deliberate CJK line break for oversized editorial poster titles.

    PowerPoint's renderer can otherwise leave a one-character orphan even when
    the governed capacity estimate passes.  Known business-title suffixes are
    kept intact; the content itself is unchanged.
    """

    compact = "".join(title.split())
    if (
        layout_id in {"cover.editorial", "cover.hero-left", "cover.hero-right"}
        and "\n" not in title
        and 22 <= len(compact) <= 52
        and re.search(r"[A-Za-z]", title)
    ):
        words = title.split()
        best = min(
            range(1, len(words)),
            key=lambda index: abs(
                len(" ".join(words[:index])) - len(" ".join(words[index:]))
            ),
            default=0,
        )
        if best:
            return f"{' '.join(words[:best])}\n{' '.join(words[best:])}"
    if (
        layout_id != "cover.poster-editorial"
        or "\n" in title
        or not 10 <= len(compact) <= 20
        or re.fullmatch(r"[\u3400-\u9fff]+", compact) is None
    ):
        return title
    suffixes = (
        "建设提案",
        "项目提案",
        "年度总结",
        "战略规划",
        "市场分析",
        "数据报告",
        "研究报告",
        "产品发布",
        "营销方案",
        "销售提案",
    )
    for suffix in suffixes:
        if compact.endswith(suffix) and len(compact) - len(suffix) >= 5:
            return f"{compact[:-len(suffix)]}\n{suffix}"
    split_at = max(5, min(len(compact) - 4, round(len(compact) * 0.58)))
    return f"{compact[:split_at]}\n{compact[split_at:]}"


def _preflight_image_sources(
    source_refs: Mapping[str, str],
    governed_assets: Mapping[str, AssetBinding],
) -> tuple[frozenset[str], dict[str, str]]:
    """Validate image evidence before choosing a layout that requires imagery."""

    valid: set[str] = set()
    rejected: dict[str, str] = {}
    for source_ref in source_refs.values():
        binding = governed_assets.get(source_ref)
        if binding is None:
            continue
        ratio = (
            binding.record.aspect_ratio
            if isinstance(binding, AssetBinding)
            and isinstance(binding.record, AssetRecord)
            and isinstance(binding.record.aspect_ratio, (int, float))
            and not isinstance(binding.record.aspect_ratio, bool)
            and math.isfinite(binding.record.aspect_ratio)
            and binding.record.aspect_ratio > 0
            else 1.0
        )
        probe = ResolvedSlot(
            id="asset-preflight",
            component="image-frame",
            x=0.0,
            y=0.0,
            width=float(ratio),
            height=1.0,
            allow_overlap=False,
        )
        source_path, _, rejection = _resolve_asset_binding(binding, probe)
        if source_path is not None and rejection is None:
            valid.add(source_ref)
        else:
            rejected[source_ref] = rejection or "asset evidence is invalid"
    return frozenset(valid), rejected


def _slot_text_capacity_at_font(slot: ResolvedSlot, font_size: int) -> int:
    return estimate_text_layout(
        "",
        width_in=slot.width,
        height_in=slot.height,
        font_size_pt=font_size,
    ).approximate_character_capacity


def _text_fits_slot_at_font(
    text: str,
    slot: ResolvedSlot,
    font_size: int,
) -> bool:
    """Estimate wrapping while honoring source-present line breaks.

    A compressed character count can incorrectly accept six explicit KPI
    lines in a shallow card.  Count every authored line and its estimated
    wraps instead; this stays deterministic and deliberately conservative.
    """

    return estimate_text_layout(
        text,
        width_in=slot.width,
        height_in=slot.height,
        font_size_pt=font_size,
    ).fits


def _font_size(
    component: str,
    typography: Mapping[str, int],
    *,
    text: str | None = None,
    slot: ResolvedSlot | None = None,
    role: str | None = None,
    family_id: str | None = None,
) -> int:
    if component == "title":
        role_label = (role or "").replace("-", " ").strip().casefold()
        if (
            family_id == "focal-statement"
            and text
            and text.strip().casefold() == role_label
        ):
            return typography["subtitle"]
        if (
            role == "cover"
            and text
            and slot is not None
            and len("".join(text.split())) <= 34
        ):
            for candidate in range(
                typography["display"], typography["title"] - 1, -2
            ):
                if _text_fits_slot_at_font(text, slot, candidate):
                    return candidate
        if (
            (role in {"cover", "section", "closing"} or family_id == "focal-statement")
            and text
            and slot is not None
            and len("".join(text.split()))
            <= _slot_text_capacity_at_font(slot, typography["display"])
        ):
            return typography["display"]
        if text and slot is not None:
            for level in ("title", "subtitle", "body"):
                candidate = typography[level]
                if _text_fits_slot_at_font(text, slot, candidate):
                    return candidate
        return typography["body"]
    if component == "footer":
        return typography["footnote"]
    if component == "kpi":
        if text and slot is not None:
            for level in ("display", "title", "subtitle"):
                candidate = typography[level]
                if _text_fits_slot_at_font(text, slot, candidate):
                    return candidate
        return typography["subtitle"]
    if component == "comparison-panel":
        if text and slot is not None:
            compact_length = len("".join(text.split()))
            levels = (
                ("display", "title", "subtitle", "body")
                if compact_length <= 12
                else ("title", "subtitle", "body")
                if compact_length <= 24
                else ("body",)
            )
            for level in levels:
                candidate = typography[level]
                if _text_fits_slot_at_font(text, slot, candidate):
                    return candidate
        return typography["body"]
    if component in {"risk-panel", "recommendation-panel"}:
        if text and slot is not None:
            for level in ("title", "subtitle", "body"):
                candidate = typography[level]
                if _text_fits_slot_at_font(text, slot, candidate):
                    return candidate
        return typography["body"]
    if component in {"quote", "statement"}:
        if text and slot is not None:
            for level in ("title", "subtitle", "body"):
                candidate = typography[level]
                if _text_fits_slot_at_font(text, slot, candidate):
                    return candidate
        return typography["body"]
    if component == "body-text" and role == "cover":
        return typography["body"]
    if component == "body-text" and role == "section":
        return typography["subtitle"]
    if component == "cta":
        if text and slot is not None:
            compact_length = len("".join(text.split()))
            levels = (
                ("title", "subtitle", "body")
                if compact_length <= 52 and "\n" not in text
                else ("subtitle", "body")
                if compact_length <= 72 and "\n" not in text
                else ("body",)
            )
            for level in levels:
                candidate = typography[level]
                if _text_fits_slot_at_font(text, slot, candidate):
                    return candidate
        return typography["body"]
    if component in {"decoration", "icon", "image-frame"}:
        return typography["label"]
    return typography["body"]


def _slot_text_capacity(
    slot: ResolvedSlot, typography: Mapping[str, int]
) -> int:
    font_size = _font_size(slot.component, typography)
    return _slot_text_capacity_at_font(slot, font_size)


def _overflowing_text_slots(
    layout: ResolvedLayout,
    slot_texts: Mapping[str, str],
    typography: Mapping[str, int],
) -> tuple[str, ...]:
    return tuple(
        slot.id
        for slot in _governed_text_slots(layout)
        if not _text_fits_slot_at_font(
            slot_texts.get(slot.id, ""),
            slot,
            _font_size(
                slot.component,
                typography,
                text=slot_texts.get(slot.id, ""),
                slot=slot,
                family_id=layout.family_id,
            ),
        )
    )


def _title_capacity(layout: ResolvedLayout, typography: Mapping[str, int]) -> int:
    title_slot = next(
        (slot for slot in layout.slots if slot.component == "title"), None
    )
    if title_slot is None:
        return 0
    # Title objects use the governed title/subtitle/body ladder.  Capacity
    # selection therefore needs to admit any title that fits at the minimum
    # professional title fallback, otherwise the resolver can reject a full
    # source sentence before `_font_size` is allowed to select 22pt or 18pt.
    return _slot_text_capacity_at_font(title_slot, typography["body"])


def _resolve_title_safe_layout(
    layout: ResolvedLayout,
    title: str,
    *,
    slide_size: SlideSize,
    previous_layouts: tuple[str, ...],
    item_count: int,
    density: str,
    variant_seed: str | None,
    forbidden_components: frozenset[str],
    component_limits: Mapping[str, int] | None,
    typography: Mapping[str, int],
) -> ResolvedLayout:
    """Choose a same-family composition whose title slot fits before render.

    Title text is deliberately excluded from body-slot allocation, so it needs
    its own pre-render capacity decision.  The alternative remains in the same
    semantic family and prefers a recipe not used on either of the last two
    slides; this prevents a one-character overflow from reaching Quality-v2
    without weakening the delivery gate.
    """

    normalized_length = len("".join(title.split()))
    if normalized_length <= _title_capacity(layout, typography):
        return layout
    registry = load_layout_registry()
    family = registry.families.get(layout.family_id)
    if family is None:
        raise RenderPlanError(f"layout family is not registered: {layout.family_id}")
    recent_recipes = tuple(
        variant.recipe_id
        for layout_id in previous_layouts[-2:]
        if (variant := registry.variants.get(layout_id)) is not None
    )
    candidates: list[tuple[int, int, int, ResolvedLayout]] = []
    for index, variant_id in enumerate(family.variant_ids):
        try:
            candidate = resolve_layout(
                variant_id,
                slide_size,
                previous_layouts,
                item_count=item_count,
                density=density,
                variant_seed=variant_seed,
                forbidden_components=forbidden_components,
                component_limits=component_limits,
            )
        except ValueError:
            continue
        capacity = _title_capacity(candidate, typography)
        if normalized_length > capacity:
            continue
        candidates.append(
            (
                recent_recipes.count(candidate.recipe_id),
                capacity - normalized_length,
                index,
                candidate,
            )
        )
    if not candidates:
        raise RenderPlanError(
            f"slide title exceeds every governed {layout.family_id} composition"
        )
    return min(candidates, key=lambda item: item[:3])[3]


def _resolve_text_safe_layout(
    layout: ResolvedLayout,
    fragments: list[str],
    *,
    title: str,
    slide: Mapping[str, Any],
    project: Mapping[str, Any],
    slide_size: SlideSize,
    previous_layouts: tuple[str, ...],
    item_count: int,
    density: str,
    variant_seed: str | None,
    forbidden_components: frozenset[str],
    component_limits: Mapping[str, int] | None,
    typography: Mapping[str, int],
) -> tuple[ResolvedLayout, dict[str, str]] | None:
    """Find a capacity-safe same-family composition before semantic fallback.

    Adding a new visual variant must not make a previously serviceable KPI,
    statement, or card page collapse into generic body text merely because
    the seeded first choice is too small.  Try every registered variant in
    the same semantic family, keep the source text unchanged, and prefer the
    tightest composition that does not repeat a recent recipe.
    """

    registry = load_layout_registry()
    family = registry.families.get(layout.family_id)
    if family is None:
        return None
    recent_recipes = tuple(
        variant.recipe_id
        for layout_id in previous_layouts[-2:]
        if (variant := registry.variants.get(layout_id)) is not None
    )
    normalized_length = sum(len("".join(fragment.split())) for fragment in fragments)
    normalized_title_length = len("".join(title.split()))
    candidates: list[
        tuple[int, int, int, int, ResolvedLayout, dict[str, str]]
    ] = []
    for index, variant_id in enumerate(family.variant_ids):
        try:
            candidate = resolve_layout(
                variant_id,
                slide_size,
                previous_layouts,
                item_count=item_count,
                density=density,
                variant_seed=variant_seed,
                forbidden_components=forbidden_components,
                component_limits=component_limits,
            )
        except ValueError:
            continue
        if any(
            slot.component in ADVANCED_COMPONENTS for slot in candidate.slots
        ):
            continue
        if normalized_title_length > _title_capacity(candidate, typography):
            continue
        try:
            candidate_texts = _complete_slot_texts(
                candidate, fragments, slide, project
            )
        except RenderPlanError:
            continue
        if _overflowing_text_slots(candidate, candidate_texts, typography):
            continue
        text_slots = _governed_text_slots(candidate)
        if not text_slots:
            continue
        total_capacity = sum(
            _slot_text_capacity(slot, typography)
            for slot in text_slots
        )
        resolved_font_floor = min(
            _font_size(
                slot.component,
                typography,
                text=candidate_texts.get(slot.id, ""),
                slot=slot,
                family_id=candidate.family_id,
            )
            for slot in text_slots
        )
        candidates.append(
            (
                recent_recipes.count(candidate.recipe_id),
                -resolved_font_floor,
                max(0, total_capacity - normalized_length),
                index,
                candidate,
                candidate_texts,
            )
        )
    if not candidates:
        return None
    selected = min(candidates, key=lambda item: item[:4])
    return selected[4], selected[5]


def _advanced_mixed_layout_fits(
    layout: ResolvedLayout,
    fragments: list[str],
    *,
    title: str,
    slide: Mapping[str, Any],
    project: Mapping[str, Any],
    typography: Mapping[str, int],
) -> bool:
    if not any(slot.component in ADVANCED_COMPONENTS for slot in layout.slots):
        return False
    if not _governed_text_slots(layout):
        return False
    if len("".join(title.split())) > _title_capacity(layout, typography):
        return False
    try:
        slot_texts = _complete_slot_texts(layout, fragments, slide, project)
    except RenderPlanError:
        return False
    return not _overflowing_text_slots(layout, slot_texts, typography)


def _resolve_advanced_mixed_layout(
    layout: ResolvedLayout,
    fragments: list[str],
    *,
    title: str,
    slide: Mapping[str, Any],
    project: Mapping[str, Any],
    slide_size: SlideSize,
    previous_layouts: tuple[str, ...],
    item_count: int,
    density: str,
    variant_seed: str | None,
    forbidden_components: frozenset[str],
    component_limits: Mapping[str, int] | None,
    typography: Mapping[str, int],
) -> ResolvedLayout:
    """Keep every non-basis fact visible beside an advanced native object."""

    if _advanced_mixed_layout_fits(
        layout,
        fragments,
        title=title,
        slide=slide,
        project=project,
        typography=typography,
    ):
        return layout
    registry = load_layout_registry()
    family = registry.families.get(layout.family_id)
    if family is None:
        raise RenderPlanError(f"layout family is not registered: {layout.family_id}")
    recent_recipes = tuple(
        variant.recipe_id
        for layout_id in previous_layouts[-2:]
        if (variant := registry.variants.get(layout_id)) is not None
    )
    candidates: list[tuple[int, int, ResolvedLayout]] = []
    for index, variant_id in enumerate(family.variant_ids):
        try:
            candidate = resolve_layout(
                variant_id,
                slide_size,
                previous_layouts,
                item_count=item_count,
                density=density,
                variant_seed=variant_seed,
                forbidden_components=forbidden_components,
                component_limits=component_limits,
            )
        except ValueError:
            continue
        if not _advanced_mixed_layout_fits(
            candidate,
            fragments,
            title=title,
            slide=slide,
            project=project,
            typography=typography,
        ):
            continue
        candidates.append(
            (recent_recipes.count(candidate.recipe_id), index, candidate)
        )
    if not candidates:
        raise RenderPlanError(
            f"slide {slide['id']} needs a split: no governed {layout.family_id} "
            "composition can retain all supplemental facts"
        )
    return min(candidates, key=lambda item: item[:2])[2]


def _object_kind(
    component: str, has_image: bool, advanced: AdvancedSpec | None = None
) -> str:
    if isinstance(advanced, ChartSpec):
        return "chart"
    if isinstance(advanced, TableSpec):
        return "table"
    if isinstance(advanced, DiagramSpec):
        return "diagram"
    if component == "image-frame" and has_image:
        return "image"
    if component in TEXT_COMPONENTS:
        return "text"
    return "shape"


def _valid_number(value: object, *, positive: bool = False) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and (value > 0 if positive else value >= 0)
    )


def _validate_slide_size(slide_size: SlideSize) -> None:
    if not isinstance(slide_size, SlideSize) or not all(
        _valid_number(value, positive=True)
        for value in (slide_size.width, slide_size.height)
    ):
        raise RenderPlanError("render plan slide geometry must be finite and positive")
    if not all(
        MIN_POWERPOINT_SLIDE_IN <= value <= MAX_POWERPOINT_SLIDE_IN
        for value in (slide_size.width, slide_size.height)
    ):
        raise RenderPlanError("PowerPoint slide dimensions must be between 1 and 56 inches")


def _expected_fill(
    component: str,
    background: str,
    surface: str,
    primary: str,
) -> str:
    # A decoration is an intentional color field, never an empty image-like
    # outline.  The backend applies governed transparency while preserving the
    # primary color in OOXML for exact semantic inspection.
    if component in {"decoration", "accent"}:
        return primary
    if component == "cta":
        return primary
    if component in {"card", "quote", "timeline-node", "recommendation-panel"}:
        return mix_color(surface, primary, 0.06)
    return surface if component not in {"title", "body-text", "footer"} else background


def _expected_text_color(component: str, colors: Mapping[str, str]) -> str:
    if component == "cta":
        return max(
            ("#000000", "#FFFFFF"),
            key=lambda candidate: contrast_ratio(candidate, colors["primary"]),
        )
    if component in {"title", "kpi"}:
        return colors["primary"]
    if component == "footer":
        return colors["muted_text"]
    return colors["text"]


def _slot_style(
    *,
    component: str,
    slot_id: str,
    layout_id: str,
    colors: Mapping[str, str],
    motif_id: str | None = None,
) -> tuple[str, str]:
    """Return deterministic editorial fill/text pairs for semantic slots.

    Layout geometry alone does not create art direction.  These bounded
    treatments turn the most common executive compositions into a deliberate
    hierarchy while retaining native editable shapes and governed tokens.
    """

    default_fill = _expected_fill(
        component,
        colors["background"],
        colors["surface"],
        colors["primary"],
    )
    default_text = _expected_text_color(component, colors)
    if (
        motif_id in {"knowledge-wayfinding", "evidence-margin"}
        and layout_id in {
            "cta.image-stage",
            "cta.editorial-left",
            "cta.centered",
        }
        and component == "cta"
    ):
        return (
            mix_color(colors["background"], colors["primary"], 0.10),
            colors["text"],
        )
    if (
        motif_id == "luminous-product-stage"
        and layout_id == "cta.image-stage"
        and component == "cta"
    ):
        return colors["surface"], colors["text"]
    if layout_id.endswith(".editorial-three"):
        if slot_id == "one":
            return colors["primary"], colors["background"]
        if slot_id == "two":
            return mix_color(colors["background"], colors["accent"], 0.18), colors["text"]
        if slot_id == "three":
            return mix_color(colors["background"], colors["positive"], 0.14), colors["text"]
    if layout_id == "agenda.grid-four":
        if slot_id == "one":
            return colors["primary"], colors["background"]
        if slot_id == "two":
            return mix_color(colors["background"], colors["accent"], 0.22), colors["text"]
        if slot_id in {"three", "four"}:
            return mix_color(colors["background"], colors["positive"], 0.10), colors["text"]
    if layout_id == "cta.decision-three":
        if slot_id == "one":
            return colors["primary"], colors["background"]
        if slot_id == "two":
            return (
                mix_color(colors["background"], colors["primary"], 0.16),
                colors["text"],
            )
        if slot_id == "three":
            return (
                mix_color(colors["background"], colors["primary"], 0.26),
                colors["text"],
            )
    if layout_id == "big-number.editorial-left":
        if slot_id == "metric":
            return colors["primary"], colors["background"]
    if layout_id == "big-number.split":
        if slot_id == "primary":
            return colors["primary"], colors["background"]
        if slot_id == "secondary":
            return mix_color(colors["background"], colors["accent"], 0.24), colors["text"]
    if layout_id == "big-number.centered":
        if slot_id == "metric":
            return colors["primary"], colors["background"]
        if slot_id == "accent":
            return colors["accent"], colors["accent"]
    if layout_id == "recommendation.dual":
        if slot_id == "primary":
            return colors["primary"], colors["background"]
        if slot_id == "secondary":
            return mix_color(colors["background"], colors["positive"], 0.18), colors["text"]
    if layout_id == "comparison.split":
        if slot_id == "primary":
            return colors["primary"], colors["background"]
        if slot_id == "secondary":
            return mix_color(colors["background"], colors["positive"], 0.14), colors["text"]
    if layout_id == "risk-recommendation.split":
        if slot_id == "primary":
            return (
                mix_color(colors["background"], colors["warning"], 0.34),
                colors["text"],
            )
        if slot_id == "secondary":
            return mix_color(colors["background"], colors["positive"], 0.15), colors["text"]
    if layout_id.startswith("process.") and component == "process-step":
        if motif_id == "knowledge-wayfinding":
            if slot_id in {"one", "primary"}:
                return colors["primary"], colors["background"]
            if slot_id in {"two", "secondary"}:
                return mix_color(
                    colors["background"], colors["accent"], 0.18
                ), colors["text"]
            if slot_id == "three":
                return mix_color(
                    colors["background"], colors["positive"], 0.16
                ), colors["text"]
            return mix_color(
                colors["background"], colors["primary"], 0.11
            ), colors["text"]
        return colors["primary"], colors["background"]
    if layout_id.startswith("timeline.") and component == "timeline-node":
        return colors["primary"], colors["background"]
    if layout_id.startswith("matrix.") and component == "matrix-cell":
        return mix_color(colors["background"], colors["positive"], 0.13), colors["text"]
    if layout_id in {
        "cover.full-visual",
        "section.full-visual",
        "cta.full-visual-stage",
    } and slot_id in {
        "title",
        "body",
        "footer",
    }:
        return default_fill, colors["background"]
    if layout_id in {"cover.poster-editorial", "cta.poster-editorial"}:
        if slot_id == "title":
            return default_fill, colors["positive"]
        if slot_id in {"body", "primary"}:
            return colors["background"], colors["text"]
        if slot_id == "decision-one":
            return colors["positive"], colors["background"]
        if slot_id == "decision-two":
            return mix_color(colors["background"], colors["accent"], 0.18), colors["text"]
        if slot_id == "decision-three":
            return mix_color(colors["background"], colors["positive"], 0.12), colors["text"]
        if slot_id == "footer":
            return default_fill, colors["muted_text"]
    return default_fill, default_text


def _governed_slide_background(
    colors: Mapping[str, str],
    *,
    motif_id: str | None,
    role: str,
    slide_index: int,
) -> str:
    if (
        motif_id == "luminous-product-stage"
        and role not in {"cover", "closing"}
        and slide_index % 3 == 0
    ):
        return mix_color(colors["background"], colors["surface"], 0.62)
    if (
        motif_id == "evidence-margin"
        and role not in {"cover", "closing"}
        and slide_index % 3 == 0
    ):
        return mix_color(colors["background"], colors["surface"], 0.58)
    return colors["background"]


def _expected_font(component: str, heading: str, body: str) -> str:
    return (
        heading
        if component
        in {
            "title",
            "kpi",
            "comparison-panel",
            "recommendation-panel",
            "statement",
            "quote",
            "cta",
        }
        else body
    )


def _direction_annotation(slide: Mapping[str, Any]) -> tuple[str, str] | None:
    preserved = slide.get("direction_annotation")
    if (
        isinstance(preserved, (list, tuple))
        and len(preserved) == 2
        and all(isinstance(item, str) and item for item in preserved)
    ):
        return preserved[0], preserved[1]
    source_text = " ".join(
        str(block.get("text") or "")
        for block in slide.get("blocks", ())
        if isinstance(block, Mapping)
    )
    trend_match = re.search(
        r"\b(?P<direction>declined|decreased|dropped|fell|increased|grew|rose)"
        r"\s+(?:by\s+)?(?P<value>\d+(?:\.\d+)?|one|two|three|four|five|six|"
        r"seven|eight|nine|ten|eleven|twelve)\s+percentage points?\s+from\s+"
        r"(?P<start>January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+(?:through|to)\s+"
        r"(?P<end>January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\b",
        source_text,
        flags=re.IGNORECASE,
    )
    number_words = {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
        "eleven": "11",
        "twelve": "12",
    }
    if trend_match is not None:
        raw_value = trend_match.group("value")
        value = number_words.get(raw_value.casefold(), raw_value)
        sign = (
            "−"
            if trend_match.group("direction").casefold()
            in {"declined", "decreased", "dropped", "fell"}
            else "+"
        )
        return (
            (
                f"{trend_match.group('start')[:3].upper()} → "
                f"{trend_match.group('end')[:3].upper()}"
            ),
            f"Δ {sign}{value} PP",
        )
    if str(slide.get("role") or "").casefold() in {
        "timeline",
        "roadmap",
        "milestones",
    }:
        timeline_match = re.search(
            r"\b(?P<start>[A-Za-z][A-Za-z -]{1,30}?)\s+and\s+"
            r"(?P<end>[A-Za-z][A-Za-z -]{1,30}?)\s+will\s+run\s+for\s+"
            r"(?P<duration>\d+|one|two|three|four|five|six|seven|eight|nine|"
            r"ten|eleven|twelve)\s+weeks?\b",
            source_text,
            flags=re.IGNORECASE,
        )
        if timeline_match is not None:
            raw_duration = timeline_match.group("duration")
            duration = number_words.get(
                raw_duration.casefold(), raw_duration
            )
            return (
                (
                    f"{timeline_match.group('start').strip().upper()} → "
                    f"{timeline_match.group('end').strip().upper()}"
                ),
                f"{duration} WEEKS",
            )
    return None


def _art_direction_objects(
    *,
    slide: Mapping[str, Any],
    slide_index: int,
    slide_size: SlideSize,
    family_id: str,
    theme: Any,
) -> tuple[RenderObject, ...]:
    """Compile deterministic, editable editorial rhythm into every slide."""

    primary = theme.colors["primary"]
    group_id = f"wp_s{slide_index:03d}_art"
    family_offset = sum(ord(char) for char in family_id) % 3
    specs: list[tuple[str, float, float, float, float, str | None]] = [
        ("top-rule", 0.62, 0.26, 0.58 + family_offset * 0.22, 0.055, None),
        (
            "bottom-rule",
            0.62,
            slide_size.height - 0.27,
            slide_size.width - 1.24,
            0.02,
            None,
        ),
    ]
    role = str(slide["role"])
    resolved_layout_id = str(slide.get("resolved_layout_id") or "")
    motif = slide.get("composition_motif")
    motif_id = (
        motif.get("motif_id")
        if isinstance(motif, Mapping)
        else slide.get("motif_id")
    )
    motif_variant = (
        motif.get("variant")
        if isinstance(motif, Mapping)
        else slide.get("motif_variant")
    )
    motif_intensity = (
        motif.get("intensity")
        if isinstance(motif, Mapping)
        else slide.get("motif_intensity")
    )
    direction_annotation = _direction_annotation(slide)
    if role == "cover":
        if resolved_layout_id == "cover.poster-editorial":
            cover_specs = [
                (
                    "cover-title-field-cutout",
                    6.30,
                    1.22,
                    slide_size.width - 6.72,
                    5.38,
                    None,
                ),
                (
                    "hero-eyebrow",
                    slide_size.width - 3.32,
                    0.88,
                    2.40,
                    0.30,
                    "KNOWLEDGE / PILOT",
                )
            ]
        elif resolved_layout_id == "cover.full-visual":
            cover_specs = [
                (
                    "cover-title-field",
                    0.62,
                    1.06,
                    8.45,
                    4.36,
                    None,
                ),
                (
                    "hero-eyebrow",
                    0.92,
                    0.88,
                    2.74,
                    0.30,
                    "KNOWLEDGE / PILOT",
                ),
            ]
        elif resolved_layout_id == "cover.editorial":
            cover_specs = [
                (
                    "cover-kicker",
                    slide_size.width - 3.28,
                    1.00,
                    2.54,
                    0.34,
                    (
                        "RETENTION / ANALYSIS"
                        if motif_id == "evidence-margin"
                        else "ATLAS / MODERNIZATION"
                    ),
                ),
                (
                    "cover-band-1",
                    slide_size.width - 3.18,
                    2.36,
                    2.42,
                    0.12,
                    None,
                ),
                (
                    "cover-band-2",
                    slide_size.width - 2.70,
                    2.86,
                    1.94,
                    0.12,
                    None,
                ),
                (
                    "cover-band-3",
                    slide_size.width - 2.22,
                    3.36,
                    1.46,
                    0.12,
                    None,
                ),
                (
                    "cover-seal",
                    slide_size.width - 2.66,
                    4.06,
                    1.76,
                    1.76,
                    "2026" if motif_id == "evidence-margin" else "12W",
                ),
            ]
        elif motif_id == "institutional-beacon":
            cover_specs = [
                (
                    "institutional-panel",
                    slide_size.width - 4.02,
                    0.68,
                    3.36,
                    slide_size.height - 1.36,
                    None,
                ),
                (
                    "institutional-kicker",
                    slide_size.width - 3.68,
                    1.02,
                    2.70,
                    0.32,
                    "REVIEW / DECIDE",
                ),
                (
                    "institutional-band-1",
                    slide_size.width - 3.54,
                    2.04,
                    2.46,
                    0.10,
                    None,
                ),
                (
                    "institutional-band-2",
                    slide_size.width - 3.06,
                    2.40,
                    1.98,
                    0.10,
                    None,
                ),
                (
                    "institutional-band-3",
                    slide_size.width - 2.58,
                    2.76,
                    1.50,
                    0.10,
                    None,
                ),
                (
                    "institutional-seal",
                    slide_size.width - 2.20,
                    4.18,
                    1.14,
                    1.14,
                    None,
                ),
            ]
        elif motif_id == "luminous-product-stage":
            cover_specs = [
                (
                    "stage-panel",
                    slide_size.width - 4.28,
                    0.70,
                    3.62,
                    slide_size.height - 1.40,
                    None,
                ),
                (
                    "stage-kicker",
                    slide_size.width - 3.86,
                    1.04,
                    2.82,
                    0.32,
                    "PRODUCT / LAUNCH",
                ),
                (
                    "stage-beam-1",
                    slide_size.width - 3.70,
                    2.12,
                    2.64,
                    0.12,
                    None,
                ),
                (
                    "stage-beam-2",
                    slide_size.width - 3.12,
                    2.58,
                    2.06,
                    0.12,
                    None,
                ),
                (
                    "stage-device",
                    slide_size.width - 2.96,
                    3.18,
                    1.88,
                    2.12,
                    None,
                ),
                (
                    "stage-orbit",
                    slide_size.width - 3.30,
                    5.62,
                    2.24,
                    0.08,
                    None,
                ),
            ]
        elif motif_id == "evidence-margin":
            cover_specs = [
                (
                    "evidence-panel",
                    slide_size.width - 3.70,
                    0.72,
                    3.04,
                    slide_size.height - 1.44,
                    None,
                ),
                (
                    "evidence-kicker",
                    slide_size.width - 3.36,
                    1.02,
                    2.38,
                    0.32,
                    "EVIDENCE / DECISION",
                ),
                (
                    "evidence-bracket-top",
                    slide_size.width - 3.18,
                    2.06,
                    1.96,
                    0.08,
                    None,
                ),
                (
                    "evidence-bracket-side",
                    slide_size.width - 3.18,
                    2.06,
                    0.08,
                    2.78,
                    None,
                ),
                (
                    "evidence-datum-1",
                    slide_size.width - 2.74,
                    2.56,
                    1.52,
                    0.08,
                    None,
                ),
                (
                    "evidence-datum-2",
                    slide_size.width - 2.74,
                    3.30,
                    1.12,
                    0.08,
                    None,
                ),
                (
                    "evidence-datum-3",
                    slide_size.width - 2.74,
                    4.04,
                    1.72,
                    0.08,
                    None,
                ),
                (
                    "evidence-stage-1",
                    slide_size.width - 2.74,
                    2.72,
                    1.72,
                    0.28,
                    "01 SCOPE",
                ),
                (
                    "evidence-stage-2",
                    slide_size.width - 2.74,
                    3.46,
                    1.72,
                    0.28,
                    "02 RETENTION",
                ),
                (
                    "evidence-stage-3",
                    slide_size.width - 2.74,
                    4.20,
                    1.72,
                    0.28,
                    "03 ACTION",
                ),
            ]
        else:
            cover_specs = [
                (
                    "hero-panel",
                    slide_size.width - 4.15,
                    0.76,
                    3.52,
                    slide_size.height - 1.52,
                    None,
                ),
                (
                    "hero-eyebrow",
                    slide_size.width - 3.88,
                    0.98,
                    2.74,
                    0.30,
                    "STRATEGY / ACTION",
                ),
                (
                    "hero-stair-1",
                    slide_size.width - 1.34,
                    slide_size.height - 1.18,
                    1.02,
                    0.08,
                    None,
                ),
                (
                    "hero-stair-2",
                    slide_size.width - 1.68,
                    slide_size.height - 1.00,
                    1.36,
                    0.08,
                    None,
                ),
                (
                    "hero-stair-3",
                    slide_size.width - 2.02,
                    slide_size.height - 0.82,
                    1.70,
                    0.08,
                    None,
                ),
            ]
        specs.extend(cover_specs)
    elif role in {"section", "agenda"}:
        section_kicker = {
            "section-why-now": "WHY / NOW",
            "section-what-built": "BUILD / WHAT",
            "section-how-delivery": "DELIVER / HOW",
        }.get(str(slide["id"]), "CHAPTER")
        specs.extend(
            [
                *(
                    [
                        (
                            "section-title-field",
                            0.62,
                            1.42,
                            7.46,
                            3.74,
                            None,
                        )
                    ]
                    if resolved_layout_id == "section.full-visual"
                    else []
                ),
                (
                    "section-kicker",
                    slide_size.width - 4.52,
                    1.34,
                    3.86,
                    0.56,
                    section_kicker,
                ),
                (
                    "section-beam",
                    0.62,
                    2.34,
                    slide_size.width - 1.28,
                    0.09,
                    None,
                ),
                (
                    "section-number",
                    slide_size.width - 1.68,
                    slide_size.height - 1.72,
                    1.02,
                    1.02,
                    str(slide_index).zfill(2),
                ),
                (
                    "section-rule",
                    slide_size.width - 4.12,
                    slide_size.height - 0.80,
                    3.46,
                    0.08,
                    None,
                ),
                (
                    "section-marker",
                    slide_size.width - 0.82,
                    1.68,
                    0.18,
                    1.18,
                    None,
                ),
            ]
        )
    else:
        specs.append(
            (
                "page-number",
                slide_size.width - 1.08,
                slide_size.height - 0.76,
                0.42,
                0.28,
                str(slide_index).zfill(2),
            )
        )
        tick_count = 1 + ((slide_index + family_offset) % 3)
        for offset in range(tick_count):
            specs.append(
                (
                    f"tick-{offset + 1}",
                    slide_size.width - 0.64,
                    2.04 + offset * 0.28,
                    0.12 + offset * 0.07,
                    0.055,
                    None,
                )
            )
        if role == "closing":
            specs.extend(
                [
                    *(
                        [
                            (
                                (
                                    "closing-title-field-cutout"
                                    if resolved_layout_id
                                    == "cta.poster-editorial"
                                    else "closing-title-field"
                                ),
                                5.02,
                                1.02,
                                slide_size.width - 5.66,
                                2.12,
                                None,
                            )
                        ]
                        if resolved_layout_id
                        in {"cta.full-visual-stage", "cta.poster-editorial"}
                        else []
                    ),
                    (
                        "closing-rule",
                        0.62,
                        slide_size.height - 1.02,
                        2.26,
                        0.11,
                        None,
                    ),
                ]
            )
    if family_id in {"process", "timeline", "roadmap"}:
        specs.append(
            (
                "content-rail",
                0.92,
                slide_size.height * 0.53,
                slide_size.width - 1.84,
                0.09,
                None,
            )
        )
        if family_id == "process":
            specs.append(
                (
                    "process-title-anchor",
                    0.50,
                    1.52,
                    slide_size.width - 1.00,
                    0.06,
                    None,
                )
            )
            if role == "solution":
                for offset, x in enumerate((4.36, 8.68, 10.88), start=1):
                    specs.append(
                        (
                            f"process-connector-{offset}",
                            x,
                            3.56,
                            0.42,
                            0.42,
                            "→",
                        )
                    )
    elif family_id == "comparison":
        specs.append(
            (
                "comparison-arrow",
                slide_size.width * 0.48,
                slide_size.height * 0.48,
                0.54,
                0.54,
                "→",
            )
        )
    elif family_id == "big-number":
        if resolved_layout_id == "big-number.split":
            specs.append(
                (
                    "metric-bridge",
                    slide_size.width * 0.472,
                    slide_size.height * 0.55,
                    0.76,
                    0.64,
                    ">",
                )
            )
        elif resolved_layout_id == "big-number.centered":
            specs.extend(
                [
                    (
                        "metric-status-mark",
                        slide_size.width - 3.36,
                        3.28,
                        1.06,
                        1.06,
                        "◎",
                    ),
                    (
                        "metric-status-label",
                        slide_size.width - 2.18,
                        3.62,
                        1.52,
                        0.38,
                        "KEY METRIC",
                    ),
                ]
            )
    elif family_id == "focal-statement" and role in {
        "trend",
        "trends",
        "market-trends",
    }:
        # A prose-only trend claim without a chartable series still needs a
        # semantic visual cue.  The editable staircase communicates direction
        # without inventing values, ticks, or a false quantitative scale.
        specs.extend(
            [
                ("trend-axis", 7.52, 4.22, 4.60, 0.05, None),
                ("trend-step-1", 7.66, 2.28, 1.08, 0.09, None),
                ("trend-drop-1", 8.65, 2.28, 0.09, 0.62, None),
                ("trend-step-2", 8.65, 2.81, 1.08, 0.09, None),
                ("trend-drop-2", 9.64, 2.81, 0.09, 0.62, None),
                ("trend-step-3", 9.64, 3.34, 1.08, 0.09, None),
                ("trend-drop-3", 10.63, 3.34, 0.09, 0.62, None),
                ("trend-step-4", 10.63, 3.87, 1.30, 0.09, None),
                ("trend-node-1", 7.58, 2.17, 0.23, 0.23, None),
                ("trend-node-2", 8.57, 2.70, 0.23, 0.23, None),
                ("trend-node-3", 9.56, 3.23, 0.23, 0.23, None),
                ("trend-terminal-node", 11.82, 3.76, 0.26, 0.26, None),
                ("trend-y-label", 7.44, 2.02, 1.66, 0.32, "RETENTION"),
                (
                    "trend-start-label",
                    7.58,
                    4.38,
                    1.76,
                    0.32,
                    "JAN · BASELINE",
                ),
                (
                    "trend-end-label",
                    10.18,
                    4.38,
                    2.62,
                    0.32,
                    "JUN · BASELINE −4 PP",
                ),
            ]
        )
        if direction_annotation is not None:
            specs.extend(
                [
                    ("trend-period", 7.66, 1.62, 2.02, 0.42, direction_annotation[0]),
                    ("trend-delta", 10.06, 1.62, 2.02, 0.42, direction_annotation[1]),
                ]
            )
    elif (
        family_id == "focal-statement"
        and role in {"timeline", "roadmap", "milestones"}
        and direction_annotation is not None
    ):
        stage_labels = tuple(
            part.strip()
            for part in direction_annotation[0].split("→", maxsplit=1)
        )
        start_label = stage_labels[0]
        end_label = stage_labels[1] if len(stage_labels) == 2 else "END"
        specs.extend(
            [
                ("timeline-track", 6.22, 4.42, 5.48, 0.08, None),
                ("timeline-start-node", 6.12, 4.31, 0.30, 0.30, None),
                ("timeline-end-node", 11.58, 4.31, 0.30, 0.30, None),
                ("timeline-start-label", 6.12, 3.78, 1.72, 0.38, start_label),
                ("timeline-end-label", 10.16, 3.78, 1.72, 0.38, end_label),
                ("timeline-duration", 8.23, 4.82, 1.56, 0.40, direction_annotation[1]),
            ]
        )
    if motif_variant == "portal" and role not in {"cover", "closing"}:
        portal_width = 1.48 if motif_intensity == "strong" else 1.08
        for offset in range(3):
            specs.append(
                (
                    f"wayfinding-portal-{offset + 1}",
                    slide_size.width - 0.72 - portal_width + offset * 0.18,
                    1.08 + offset * 0.22,
                    portal_width - offset * 0.36,
                    2.68 - offset * 0.44,
                    None,
                )
            )
    elif motif_variant == "path" and not (
        family_id == "focal-statement"
        and role in {"timeline", "roadmap", "milestones"}
    ):
        for offset in range(4):
            specs.append(
                (
                    f"wayfinding-path-{offset + 1}",
                    0.72 + offset * 0.62,
                    slide_size.height - 0.68 - offset * 0.18,
                    0.48,
                    0.06,
                    None,
                )
            )
    elif motif_variant == "node" and family_id not in {
        "process",
        "big-number",
        "focal-statement",
    }:
        for offset in range(3):
            specs.append(
                (
                    f"wayfinding-node-{offset + 1}",
                    slide_size.width - 2.24 + offset * 0.52,
                    0.86 + (offset % 2) * 0.34,
                    0.18 + (0.06 if motif_intensity == "strong" else 0),
                    0.18 + (0.06 if motif_intensity == "strong" else 0),
                    None,
                )
            )
        specs.append(
            (
                "wayfinding-node-rail",
                slide_size.width - 2.18,
                1.44,
                1.42,
                0.045,
                None,
            )
        )
    elif motif_variant == "frame":
        specs.extend(
            [
                (
                    "wayfinding-frame-top",
                    slide_size.width - 2.56,
                    0.86,
                    1.86,
                    0.05,
                    None,
                ),
                (
                    "wayfinding-frame-side",
                    slide_size.width - 0.75,
                    0.86,
                    0.05,
                    1.38,
                    None,
                ),
            ]
        )
    elif motif_variant == "beacon-ring":
        for offset in range(3):
            specs.append(
                (
                    f"beacon-ring-{offset + 1}",
                    slide_size.width - 2.34 + offset * 0.26,
                    0.90 + offset * 0.22,
                    1.58 - offset * 0.38,
                    0.08,
                    None,
                )
            )
    elif motif_variant == "ceremonial-band":
        specs.extend(
            [
                (
                    "ceremonial-band-primary",
                    0.72,
                    slide_size.height - 0.76,
                    2.34,
                    0.10,
                    None,
                ),
                (
                    "ceremonial-band-accent",
                    3.14,
                    slide_size.height - 0.76,
                    0.64,
                    0.10,
                    None,
                ),
            ]
        )
    elif motif_variant == "milestone-seal":
        specs.append(
            (
                "milestone-seal",
                slide_size.width - 1.72,
                0.86,
                0.86,
                0.86,
                str(slide_index).zfill(2),
            )
        )
    elif motif_variant == "horizon-line":
        specs.append(
            (
                "horizon-line",
                0.72,
                slide_size.height * 0.54,
                slide_size.width - 1.44,
                0.06,
                None,
            )
        )
    elif motif_variant in {"stage-arc", "orbit", "beam"}:
        for offset in range(3):
            specs.append(
                (
                    f"stage-{motif_variant}-{offset + 1}",
                    slide_size.width - 3.08 + offset * 0.42,
                    0.82 + offset * 0.32,
                    2.24 - offset * 0.54,
                    0.08,
                    None,
                )
            )
    elif motif_variant == "device-glow":
        specs.extend(
            [
                (
                    "device-glow-frame",
                    slide_size.width - 2.62,
                    0.84,
                    1.76,
                    1.18,
                    None,
                ),
                (
                    "device-glow-line",
                    slide_size.width - 2.34,
                    1.58,
                    1.20,
                    0.08,
                    None,
                ),
            ]
        )
    elif motif_variant == "datum-line":
        specs.append(
            (
                "datum-line",
                slide_size.width - 3.14,
                1.04,
                2.30,
                0.07,
                None,
            )
        )
    elif motif_variant == "evidence-bracket":
        specs.extend(
            [
                (
                    "evidence-bracket-top",
                    slide_size.width - 2.66,
                    0.86,
                    1.84,
                    0.07,
                    None,
                ),
                (
                    "evidence-bracket-side",
                    slide_size.width - 0.89,
                    0.86,
                    0.07,
                    1.20,
                    None,
                ),
            ]
        )
    elif motif_variant == "annotation-dot":
        specs.extend(
            [
                (
                    "annotation-dot",
                    slide_size.width - 1.30,
                    0.92,
                    0.22,
                    0.22,
                    None,
                ),
                (
                    "annotation-rail",
                    slide_size.width - 3.00,
                    1.38,
                    1.92,
                    0.06,
                    None,
                ),
            ]
        )
    elif motif_variant == "editorial-rule":
        specs.append(
            (
                "editorial-rule",
                0.72,
                1.30,
                3.18,
                0.07,
                None,
            )
        )
    fact_refs = slide.get("composition_fact_refs") or slide.get("fact_refs") or ()
    if role != "cover" and motif_id in {
        "evidence-margin",
        "knowledge-wayfinding",
    }:
        specs.append(
            (
                "brand-kicker",
                slide_size.width - 3.86,
                0.26,
                2.72,
                0.28,
                (
                    "RETENTION / ANALYSIS"
                    if motif_id == "evidence-margin"
                    else "ATLAS / MODERNIZATION"
                ),
            )
        )
    if fact_refs:
        explicit_input_source = motif_id == "evidence-margin"
        specs.append(
            (
                "evidence-tag",
                (
                    slide_size.width - 4.45
                    if explicit_input_source
                    else slide_size.width - 4.08
                    if motif_id == "knowledge-wayfinding"
                    else slide_size.width - 3.00
                ),
                slide_size.height - 0.67,
                3.15
                if explicit_input_source
                else 2.80
                if motif_id == "knowledge-wayfinding"
                else 1.72,
                0.30,
                (
                    f"SOURCE {len(fact_refs):02d} · ANALYSIS INPUT"
                    if explicit_input_source
                    else "SOURCE · PROJECT BRIEF"
                    if motif_id == "knowledge-wayfinding"
                    else f"SOURCE • {len(fact_refs):02d}"
                    if motif_id == "institutional-beacon"
                    else f"EVIDENCE • {len(fact_refs):02d}"
                ),
            )
        )

    result: list[RenderObject] = []
    for offset, (token, x, y, width, height, text) in enumerate(specs, start=1):
        art_component = (
            "statement"
            if text is not None
            and token
            in {
                    "hero-panel",
                    "institutional-seal",
                    "milestone-seal",
                    "section-number",
                    "section-kicker",
                    "comparison-arrow",
                    "metric-bridge",
                    "metric-status-mark",
                    "metric-status-label",
                    "trend-period",
                    "trend-delta",
                    "trend-y-label",
                    "trend-start-label",
                    "trend-end-label",
                    "brand-kicker",
                    "evidence-stage-1",
                    "evidence-stage-2",
                    "evidence-stage-3",
                    "cover-kicker",
                    "cover-seal",
                    "timeline-start-label",
                    "timeline-end-label",
                    "timeline-duration",
                    "process-connector-1",
                    "process-connector-2",
                    "process-connector-3",
                }
            else "footer"
            if token == "evidence-tag"
            else "accent"
            if any(
                marker in token
                for marker in (
                    "node",
                    "eyebrow",
                    "kicker",
                    "marker",
                    "stair",
                    "beam",
                    "rail",
                    "axis",
                    "field",
                    "datum",
                    "bracket",
                    "orbit",
                    "glow",
                    "seal",
                )
            )
            else "decoration"
        )
        art_color = (
            theme.colors["background"]
            if "cutout" in token
            else primary
            if token in {"brand-kicker", "cover-kicker", "cover-seal"}
            else theme.colors["accent"]
            if token == "timeline-end-label"
            else theme.colors["positive"]
            if any(
                marker in token
                for marker in (
                    "path",
                    "rail",
                    "beam",
                    "axis",
                    "datum",
                    "horizon",
                    "editorial-rule",
                )
            )
            else theme.colors["accent"]
            if any(
                marker in token
                for marker in (
                    "node",
                    "eyebrow",
                    "kicker",
                    "marker",
                    "stair",
                    "seal",
                    "orbit",
                    "bracket",
                    "glow",
                )
            )
            else primary
        )
        result.append(
            RenderObject(
                id=f"{slide['id']}.art.{token}",
                name=f"wp_s{slide_index:03d}_art_{offset:02d}_{_safe_identifier(token)}",
                component=art_component,
                kind="shape",
                x=x,
                y=y,
                width=width,
                height=height,
                layer=25
                if token
                in {
                    "cover-title-field",
                    "cover-title-field-cutout",
                    "section-title-field",
                    "closing-title-field",
                    "closing-title-field-cutout",
                    "metric-bridge",
                    "comparison-arrow",
                    "process-connector-1",
                    "process-connector-2",
                    "process-connector-3",
                }
                or token in {"evidence-tag", "page-number"}
                else 10,
                group_id=group_id,
                native_editable=True,
                text=text,
                source_path=None,
                asset_record=None,
                font_name=theme.fonts["heading"],
                font_size_pt=(
                    30
                    if token in {"section-number", "institutional-seal", "milestone-seal"}
                    else 26
                    if token == "hero-panel"
                    else 22
                    if token == "section-kicker"
                    else 30
                    if token
                    in {"comparison-arrow", "metric-bridge", "metric-status-mark"}
                    else 15
                    if token in {
                        "metric-status-label",
                        "trend-period",
                        "timeline-start-label",
                        "timeline-end-label",
                    }
                    else 18
                    if token in {"trend-delta", "timeline-duration"}
                    else 22
                    if token.startswith("process-connector-")
                    else 9
                    if token in {"hero-eyebrow", "cover-kicker"}
                    else 24
                    if token == "cover-seal"
                    else 10
                    if token == "brand-kicker"
                    else 9
                    if token.startswith("evidence-stage-")
                    else 11
                ),
                text_color=(
                    theme.colors["background"]
                    if art_component == "statement" or token == "evidence-tag"
                    else theme.colors["text"]
                ),
                fill_color=art_color,
                line_color=art_color,
                advanced=None,
                semantic_source=None,
                hyperlink=None,
                text_runs=None,
            )
        )
    return tuple(result)


def _validate_brand_context(brand: BrandOverrides) -> None:
    for field in (
        "primary", "accent", "positive", "warning", "negative", "background"
    ):
        value = getattr(brand, field)
        if value is not None and (
            not isinstance(value, str) or not HEX_COLOR.fullmatch(value)
        ):
            raise RenderPlanError(f"brand {field} color is invalid")
    for field in ("heading_font", "body_font"):
        value = getattr(brand, field)
        if value is not None and (
            not isinstance(value, str) or not value.strip()
        ):
            raise RenderPlanError(
                f"brand {field.replace('_', ' ')} is invalid"
            )


def _resolve_asset_binding(
    binding: object,
    slot: ResolvedSlot,
) -> tuple[Path | None, AssetRecord | None, str | None]:
    if not isinstance(binding, AssetBinding) or not isinstance(binding.record, AssetRecord):
        return None, None, "binding is not a governed AssetBinding"
    path = Path(binding.path).expanduser().resolve(strict=False)
    if not path.is_file() or path.suffix.casefold() not in SUPPORTED_IMAGE_SUFFIXES:
        return None, None, "asset path is missing or not a supported image file"
    record = binding.record
    suffix = path.suffix.casefold()
    if suffix == ".svg":
        record_kind = (
            record.kind.strip().casefold()
            if isinstance(record.kind, str)
            else ""
        )
        if record_kind not in {"icon", "vector", "logo"}:
            return None, None, "SVG assets are limited to icon, vector, or logo kinds"
        try:
            actual_ratio = read_svg_aspect_ratio(path)
        except ValueError as exc:
            return None, None, str(exc)
        if record.aspect_ratio is None or not math.isclose(
            record.aspect_ratio, actual_ratio, rel_tol=0.01
        ):
            return None, None, "asset aspect ratio does not match governed evidence"
    else:
        try:
            actual_width, actual_height = read_raster_dimensions(path)
        except ValueError as exc:
            return None, None, str(exc)
        if (record.width_px, record.height_px) != (actual_width, actual_height):
            return None, None, "asset dimensions do not match governed evidence"
        if record.aspect_ratio is None or not math.isclose(
            record.aspect_ratio,
            actual_width / actual_height,
            rel_tol=0.01,
        ):
            return None, None, "asset aspect ratio does not match governed evidence"
    try:
        choice = choose_asset(
            AssetIntent(
                kind=record.kind,
                style=record.style,
                aspect_ratio=slot.width / slot.height,
            ),
            (record,),
        )
    except ValueError as exc:
        return None, None, str(exc)
    if choice.asset_id != record.id:
        reason = choice.rejected.get(record.id, choice.reason or "asset rejected")
        return None, None, reason
    return path, record, None


def load_asset_bindings(path: Path | str) -> dict[str, AssetBinding]:
    """Load the strict renderer-only asset manifest and its Phase 24 evidence."""

    manifest_path = Path(path).expanduser().resolve(strict=False)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RenderPlanError(
            f"cannot load governed asset manifest {manifest_path}: {exc}"
        ) from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise RenderPlanError("governed asset manifest schema_version must be 1.0")
    raw_bindings = payload.get("bindings")
    if not isinstance(raw_bindings, dict):
        raise RenderPlanError("governed asset manifest bindings must be an object")
    result: dict[str, AssetBinding] = {}
    record_fields = {
        "id",
        "kind",
        "style",
        "aspect_ratio",
        "quality",
        "source",
        "license",
        "retrieved_at",
        "width_px",
        "height_px",
        "icon_family",
    }
    required_record_fields = {
        "id",
        "kind",
        "quality",
        "source",
        "license",
        "retrieved_at",
    }
    for source_ref, raw_binding in raw_bindings.items():
        location = f"bindings.{source_ref}"
        if not isinstance(source_ref, str) or not source_ref.strip():
            raise RenderPlanError("asset manifest source references must be non-empty")
        if not isinstance(raw_binding, dict) or set(raw_binding) != {"path", "record"}:
            raise RenderPlanError(f"{location} must contain only path and record")
        raw_path = raw_binding["path"]
        raw_record = raw_binding["record"]
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise RenderPlanError(f"{location}.path must be a non-empty string")
        if not isinstance(raw_record, dict):
            raise RenderPlanError(f"{location}.record must be an object")
        unknown = set(raw_record) - record_fields
        missing = required_record_fields - set(raw_record)
        if unknown or missing:
            details = []
            if missing:
                details.append("missing " + ", ".join(sorted(missing)))
            if unknown:
                details.append("unknown " + ", ".join(sorted(unknown)))
            raise RenderPlanError(f"{location}.record is invalid: {'; '.join(details)}")
        record_payload = {field: raw_record.get(field) for field in record_fields}
        record = AssetRecord(**record_payload)
        asset_path = Path(raw_path).expanduser()
        if not asset_path.is_absolute():
            asset_path = manifest_path.parent / asset_path
        result[source_ref] = AssetBinding(
            path=asset_path.resolve(strict=False),
            record=record,
        )
    return result


def validate_render_plan(plan: RenderPlan) -> RenderPlan:
    """Revalidate publicly constructed render models before any COM mutation."""

    if not isinstance(plan, RenderPlan):
        raise RenderPlanError("render plan must be a RenderPlan")
    registry_issues = validate_registry_bundle()
    if registry_issues:
        summary = "; ".join(
            f"{issue.code}:{issue.path}" for issue in registry_issues[:5]
        )
        raise RenderPlanError(f"design registry validation failed: {summary}")
    if plan.schema_version != RENDER_PLAN_VERSION:
        raise RenderPlanError("render plan schema version is unsupported")
    if plan.theme_id not in THEME_IDS:
        raise RenderPlanError(f"render plan theme is not governed: {plan.theme_id}")
    if not isinstance(plan.brand, BrandOverrides):
        raise RenderPlanError("render plan brand context is invalid")
    _validate_brand_context(plan.brand)
    if not isinstance(plan.locale, str) or not plan.locale.strip():
        raise RenderPlanError("render plan locale is invalid")
    if not isinstance(plan.installed_fonts, tuple) or not all(
        isinstance(font, str) and font.strip() for font in plan.installed_fonts
    ):
        raise RenderPlanError("render plan font inventory is invalid")
    try:
        governed_theme = resolve_theme(
            plan.theme_id,
            brand=plan.brand,
            installed_fonts=set(plan.installed_fonts),
            locale=plan.locale,
        )
    except ValueError as exc:
        raise RenderPlanError(f"render plan theme context is invalid: {exc}") from exc
    if plan.background_color != governed_theme.colors["background"]:
        raise RenderPlanError("render plan background diverges from governed theme")
    if plan.theme_events != governed_theme.events:
        raise RenderPlanError("render plan theme resolution evidence diverges")
    if not isinstance(plan.project_title, str) or not plan.project_title.strip():
        raise RenderPlanError("render plan project title is invalid")
    _validate_slide_size(plan.slide_size)
    if not isinstance(plan.slides, tuple) or not plan.slides:
        raise RenderPlanError("render plan must contain slides")

    layout_registry = load_layout_registry()
    components = load_components()
    slide_ids: set[str] = set()
    object_ids: set[str] = set()
    object_names: set[str] = set()
    known_slide_ids = {
        slide.source_id
        for slide in plan.slides
        if isinstance(slide, RenderSlide) and isinstance(slide.source_id, str)
    }
    for expected_index, slide in enumerate(plan.slides, start=1):
        if not isinstance(slide, RenderSlide):
            raise RenderPlanError(
                f"render slide {expected_index} must be a RenderSlide"
            )
        if slide.index != expected_index:
            raise RenderPlanError("render slide indices must be sequential")
        if not isinstance(slide.source_id, str) or not slide.source_id.strip():
            raise RenderPlanError("render slide source id is invalid")
        if slide.source_id in slide_ids:
            raise RenderPlanError(f"duplicate render slide id: {slide.source_id}")
        slide_ids.add(slide.source_id)
        variant = layout_registry.variants.get(slide.layout_id)
        if variant is None or variant.family_id != slide.family_id:
            raise RenderPlanError(
                f"render slide {slide.source_id} has an unknown or mismatched layout"
            )
        expected_slide_background = _governed_slide_background(
            governed_theme.colors,
            motif_id=slide.motif_id,
            role=slide.role,
            slide_index=slide.index,
        )
        if slide.background_color != expected_slide_background:
            raise RenderPlanError(
                f"render slide {slide.source_id} diverges from governed theme"
            )
        if slide.speaker_notes is not None and (
            not isinstance(slide.speaker_notes, str)
            or not slide.speaker_notes.strip()
            or slide.speaker_notes != slide.speaker_notes.strip()
            or len(slide.speaker_notes) > 5000
        ):
            raise RenderPlanError(
                f"render slide {slide.source_id} speaker notes are invalid"
            )
        if slide.motion not in {"off", "subtle-fade", "step-reveal"}:
            raise RenderPlanError(
                f"render slide {slide.source_id} motion preset is not governed"
            )
        if (
            type(slide.item_count) is not int
            or slide.item_count < 0
            or slide.requested_density not in {"sparse", "balanced", "dense"}
        ):
            raise RenderPlanError(
                f"render slide {slide.source_id} capacity context is invalid"
            )
        try:
            governed_layout = resolve_layout(
                slide.layout_id,
                plan.slide_size,
                item_count=slide.item_count,
                density=slide.requested_density,
            )
        except ValueError as exc:
            raise RenderPlanError(
                f"render slide {slide.source_id} layout cannot be re-resolved: {exc}"
            ) from exc
        if governed_layout.resolved_density != slide.resolved_density:
            raise RenderPlanError(
                f"render slide {slide.source_id} density diverges from governed layout"
            )
        if not isinstance(slide.objects, tuple) or not slide.objects:
            raise RenderPlanError(f"render slide {slide.source_id} has no objects")
        if slide.direction_annotation is not None and (
            not isinstance(slide.direction_annotation, tuple)
            or len(slide.direction_annotation) != 2
            or not all(
                isinstance(item, str) and item
                for item in slide.direction_annotation
            )
        ):
            raise RenderPlanError(
                f"render slide {slide.source_id} trend annotation is invalid"
            )
        expected_art = _art_direction_objects(
            slide={
                "id": slide.source_id,
                "role": slide.role,
                "motif_id": slide.motif_id,
                "motif_variant": slide.motif_variant,
                "motif_intensity": slide.motif_intensity,
                "fact_refs": slide.fact_refs,
                "resolved_layout_id": slide.layout_id,
                "direction_annotation": slide.direction_annotation,
            },
            slide_index=slide.index,
            slide_size=plan.slide_size,
            family_id=slide.family_id,
            theme=governed_theme,
        )
        content_objects = slide.objects[: len(governed_layout.slots)]
        if slide.objects[len(governed_layout.slots) :] != expected_art:
            raise RenderPlanError(
                f"render slide {slide.source_id} art direction layer diverges"
            )
        for art in expected_art:
            if art.id in object_ids or art.name in object_names:
                raise RenderPlanError(
                    f"render slide {slide.source_id} art identity is duplicated"
                )
            object_ids.add(art.id)
            object_names.add(art.name)
        if len(content_objects) != len(governed_layout.slots):
            raise RenderPlanError(
                f"render slide {slide.source_id} object count diverges from governed layout"
            )
        advanced_slots = tuple(
            slot
            for slot in governed_layout.slots
            if slot.component in ADVANCED_COMPONENTS
        )
        linked_slots = advanced_slots or tuple(
            slot
            for slot in governed_layout.slots
            if slot.component not in {"title", "footer", "decoration", "accent"}
        )
        hyperlink_slot_ids = (
            {slot.id for slot in advanced_slots}
            if advanced_slots
            else ({linked_slots[0].id} if linked_slots else set())
        )
        governed_semantic_source: str | None = None
        for object_index, (item, slot) in enumerate(
            zip(content_objects, governed_layout.slots), start=1
        ):
            if not isinstance(item, RenderObject):
                raise RenderPlanError(
                    f"render slide {slide.source_id} object {object_index} "
                    "must be a RenderObject"
                )
            path = f"slides.{slide.source_id}.{getattr(item, 'name', '?')}"
            if not isinstance(item.id, str) or not item.id.strip():
                raise RenderPlanError(f"{path} has an invalid object id")
            if item.id in object_ids:
                raise RenderPlanError(f"duplicate object id: {item.id}")
            object_ids.add(item.id)
            if not isinstance(item.name, str) or not re.fullmatch(
                r"wp_s\d{3}_[a-zA-Z0-9_]+", item.name
            ):
                raise RenderPlanError(f"{path} has an invalid object name")
            if item.name in object_names:
                raise RenderPlanError(f"duplicate object name: {item.name}")
            object_names.add(item.name)
            if item.component not in components:
                raise RenderPlanError(f"{path} has an unknown component")
            if item.kind not in {"text", "shape", "image", *ADVANCED_KINDS}:
                raise RenderPlanError(f"{path} has an invalid object kind")
            if item.native_editable is not True:
                raise RenderPlanError(f"{path} violates the editable object policy")
            if not all(
                _valid_number(value, positive=field in {"width", "height"})
                for field, value in (
                    ("x", item.x),
                    ("y", item.y),
                    ("width", item.width),
                    ("height", item.height),
                )
            ):
                raise RenderPlanError(f"{path} has invalid geometry")
            if (
                item.x + item.width > plan.slide_size.width + 1e-9
                or item.y + item.height > plan.slide_size.height + 1e-9
            ):
                raise RenderPlanError(f"{path} geometry crosses the slide boundary")
            if (
                isinstance(item.font_size_pt, bool)
                or not isinstance(item.font_size_pt, (int, float))
                or not math.isfinite(item.font_size_pt)
                or item.font_size_pt < 11
            ):
                raise RenderPlanError(f"{path} font size is below the governed minimum")
            if not isinstance(item.font_name, str) or not item.font_name.strip():
                raise RenderPlanError(f"{path} font name is invalid")
            if not all(
                isinstance(color, str) and HEX_COLOR.fullmatch(color)
                for color in (item.text_color, item.fill_color, item.line_color)
            ):
                raise RenderPlanError(f"{path} color is invalid")
            if type(item.layer) is not int or item.layer < 0:
                raise RenderPlanError(f"{path} layer is invalid")
            if item.group_id is not None and (
                not isinstance(item.group_id, str) or not item.group_id.strip()
            ):
                raise RenderPlanError(f"{path} group id is invalid")
            if item.text is not None and not isinstance(item.text, str):
                raise RenderPlanError(f"{path} text is invalid")
            _validation_fill, validation_text = _slot_style(
                component=slot.component,
                slot_id=slot.id,
                layout_id=slide.layout_id,
                colors=governed_theme.colors,
                motif_id=slide.motif_id,
            )
            validation_rich_colors = dict(governed_theme.colors)
            if validation_text == governed_theme.colors["background"]:
                validation_rich_colors["muted_text"] = governed_theme.colors[
                    "background"
                ]
                validation_rich_colors["primary"] = (
                    governed_theme.colors["background"]
                    if slot.component == "comparison-panel"
                    else governed_theme.colors["accent"]
                )
            elif (
                slide.layout_id == "cta.poster-editorial"
                and slot.id == "primary"
            ):
                validation_rich_colors["primary"] = governed_theme.colors["accent"]
            expected_text_runs = _rich_text_runs(
                item.component,
                item.text,
                value_font_size_pt=(
                    governed_theme.typography["title"]
                    if (
                        slide.layout_id == "cta.poster-editorial"
                        and slot.id == "primary"
                    )
                    else int(item.font_size_pt)
                ),
                typography=governed_theme.typography,
                colors=validation_rich_colors,
            )
            if item.text_runs is not None:
                if (
                    item.component
                    not in {
                        "kpi",
                        "comparison-panel",
                        "recommendation-panel",
                        "cta",
                    }
                    or item.kind not in {"text", "shape"}
                    or item.text is None
                    or not isinstance(item.text_runs, tuple)
                    or not item.text_runs
                ):
                    raise RenderPlanError(f"{path} rich text hierarchy is invalid")
                reconstructed: list[str] = []
                for run_index, run in enumerate(item.text_runs):
                    if not isinstance(run, TextRun) or not run.text:
                        raise RenderPlanError(
                            f"{path} text run {run_index + 1} is invalid"
                        )
                    if (
                        type(run.font_size_pt) is not int
                        or run.font_size_pt < 11
                        or run.font_size_pt
                        > max(governed_theme.typography.values())
                        or run.font_size_pt
                        not in set(governed_theme.typography.values())
                        or not HEX_COLOR.fullmatch(run.text_color)
                        or run.text_color not in set(governed_theme.colors.values())
                        or type(run.bold) is not bool
                        or type(run.italic) is not bool
                        or type(run.break_after) is not bool
                    ):
                        raise RenderPlanError(
                            f"{path} text run {run_index + 1} style is invalid"
                        )
                    reconstructed.append(run.text)
                    if run.break_after:
                        reconstructed.append("\n")
                if item.text_runs[-1].break_after or "".join(reconstructed) != item.text:
                    raise RenderPlanError(
                        f"{path} rich text does not reconstruct canonical text"
                    )
            if item.text_runs != expected_text_runs:
                raise RenderPlanError(
                    f"{path} rich text diverges from the governed hierarchy"
                )
            is_advanced_slot = slot.component in ADVANCED_COMPONENTS
            carries_semantics = is_advanced_slot or slot.id in hyperlink_slot_ids
            semantic_block: dict[str, Any] | None = None
            if carries_semantics:
                if not isinstance(item.semantic_source, str):
                    raise RenderPlanError(
                        f"{path} is missing its governed semantic source"
                    )
                semantic_block = _load_semantic_block(item.semantic_source)
                if governed_semantic_source is None:
                    governed_semantic_source = item.semantic_source
                elif item.semantic_source != governed_semantic_source:
                    raise RenderPlanError(
                        f"{path} advanced semantics diverge within the slide"
                    )
            elif item.semantic_source is not None:
                raise RenderPlanError(f"{path} has an unexpected semantic source")

            expected_advanced: AdvancedSpec | None = None
            if is_advanced_slot:
                assert semantic_block is not None
                advanced_index = advanced_slots.index(slot)
                expected_advanced = _advanced_spec(
                    slot.component,
                    governed_layout.family_id,
                    semantic_block,
                    advanced_index=advanced_index,
                    advanced_count=len(advanced_slots),
                )
            if item.advanced != expected_advanced:
                raise RenderPlanError(
                    f"{path} advanced semantics diverge from governed derivation"
                )
            if item.advanced is not None and item.text is not None:
                raise RenderPlanError(
                    f"{path} advanced native object must not carry fallback text"
                )
            expected_hyperlink = (
                semantic_block.get("hyperlink")
                if slot.id in hyperlink_slot_ids and semantic_block is not None
                else None
            )
            if expected_hyperlink is not None:
                if not isinstance(expected_hyperlink, str):
                    raise RenderPlanError(f"{path} hyperlink is invalid")
                if expected_hyperlink.startswith("slide:"):
                    target_id = expected_hyperlink.removeprefix("slide:")
                    if target_id not in known_slide_ids:
                        raise RenderPlanError(
                            f"{path} hyperlink targets an unknown slide"
                        )
                elif not re.fullmatch(
                    r"(?:https?://[^\s]+|mailto:[^\s@]+@[^\s@]+)",
                    expected_hyperlink,
                    re.IGNORECASE,
                ):
                    raise RenderPlanError(f"{path} hyperlink is unsafe")
            if item.hyperlink != expected_hyperlink:
                raise RenderPlanError(
                    f"{path} hyperlink diverges from governed semantics"
                )
            if item.kind == "image":
                if item.component != "image-frame":
                    raise RenderPlanError(f"{path} image component is invalid")
                if not isinstance(item.source_path, Path) or not item.source_path.is_file():
                    raise RenderPlanError(f"{path} image source is missing")
                if not isinstance(item.asset_record, AssetRecord):
                    raise RenderPlanError(f"{path} image asset evidence is missing")
            elif item.source_path is not None:
                raise RenderPlanError(f"{path} has an unexpected image source")
            elif item.asset_record is not None:
                raise RenderPlanError(f"{path} has unexpected asset evidence")

            expected_name = (
                f"wp_s{slide.index:03d}_{object_index:02d}_"
                f"{_safe_identifier(slot.id)}"
            )
            expected_group = (
                None
                if slot.component == "footer" or slide.motion == "step-reveal"
                else f"wp_s{slide.index:03d}_content"
            )
            expected_kind = _object_kind(
                slot.component, item.source_path is not None, expected_advanced
            )
            exact_geometry = all(
                math.isclose(actual, expected, abs_tol=1e-9)
                for actual, expected in (
                    (item.x, slot.x),
                    (item.y, slot.y),
                    (item.width, slot.width),
                    (item.height, slot.height),
                )
            )
            if (
                item.id != f"{slide.source_id}.{slot.id}"
                or item.name != expected_name
                or not exact_geometry
            ):
                raise RenderPlanError(f"{path} diverges from governed layout")
            if (
                item.component != slot.component
                or item.kind != expected_kind
                or item.layer != LAYER_BY_COMPONENT.get(slot.component, 30)
                or item.group_id != expected_group
            ):
                raise RenderPlanError(f"{path} diverges from governed component rules")
            expected_fill, expected_text = _slot_style(
                component=slot.component,
                slot_id=slot.id,
                layout_id=slide.layout_id,
                colors=governed_theme.colors,
                motif_id=slide.motif_id,
            )
            expected_font_size = _font_size(
                slot.component,
                governed_theme.typography,
                text=item.text,
                slot=slot,
                role=slide.role,
                family_id=slide.family_id,
            )
            if (
                slide.layout_id == "cta.poster-editorial"
                and slot.component == "card"
            ):
                expected_font_size = governed_theme.typography["subtitle"]
            if (
                item.font_name
                != _expected_font(
                    slot.component,
                    governed_theme.fonts["heading"],
                    governed_theme.fonts["body"],
                )
                or item.font_size_pt != expected_font_size
                or item.text_color != expected_text
                or item.fill_color != expected_fill
                or item.line_color != governed_theme.colors["primary"]
            ):
                raise RenderPlanError(f"{path} diverges from governed theme")
            if item.kind == "image":
                resolved_path, resolved_record, reason = _resolve_asset_binding(
                    AssetBinding(item.source_path, item.asset_record),
                    slot,
                )
                if reason is not None or resolved_path != item.source_path.resolve():
                    raise RenderPlanError(
                        f"{path} asset evidence violates policy: {reason}"
                    )
                if resolved_record != item.asset_record:
                    raise RenderPlanError(f"{path} asset evidence changed")
    return plan


def _build_render_plan_from_compiled(
    compiled: Mapping[str, Any],
    *,
    slide_size: SlideSize,
    installed_fonts: set[str],
    theme_id: str | None = None,
    brand: BrandOverrides | None = None,
    asset_bindings: Mapping[str, AssetBinding] | None = None,
    art_direction_id: str | None = None,
) -> RenderPlan:
    """Join one compiler-owned document to governed render commands."""

    _validate_slide_size(slide_size)
    project = compiled["project"]
    selected_theme = theme_id or select_theme(
        project["scenario"], audience=project.get("audience")
    )
    resolved_brand = brand or BrandOverrides()
    if not isinstance(resolved_brand, BrandOverrides):
        raise RenderPlanError("render plan brand context is invalid")
    _validate_brand_context(resolved_brand)
    locale = project.get("language", "en-US")
    font_inventory = tuple(sorted(installed_fonts, key=str.casefold))
    try:
        theme = resolve_theme(
            selected_theme,
            brand=resolved_brand,
            installed_fonts=set(font_inventory),
            locale=locale,
        )
    except ValueError as exc:
        raise RenderPlanError(f"render plan theme context is invalid: {exc}") from exc
    governed_assets = dict(asset_bindings or {})
    findings: list[RenderFinding] = []
    render_slides: list[RenderSlide] = []
    previous_layouts: tuple[str, ...] = ()
    deck_density = compiled.get("preferences", {}).get("density", "balanced")
    motion = compiled.get("preferences", {}).get("motion", "off")
    slide_total = len(compiled["slides"])

    for slide_index, slide in enumerate(compiled["slides"], start=1):
        density = slide.get("composition_density", deck_density)
        slide_variant_seed = (
            slide.get("composition_variant_id")
            or slide.get("layout_variant_seed")
            or art_direction_id
        )
        basis_id = slide["semantic_basis"]["block_id"]
        basis_block = next(block for block in slide["blocks"] if block["id"] == basis_id)
        linked_secondary_blocks = tuple(
            block["id"]
            for block in slide["blocks"]
            if block["id"] != basis_id and block.get("hyperlink")
        )
        if linked_secondary_blocks:
            raise RenderPlanError(
                f"slide {slide['id']} needs a split: supplemental hyperlinks "
                "cannot be merged into the basis object's click target"
            )
        item_count = _item_count(slide)
        fragments, source_refs = _slide_content(slide)
        for index, binding in enumerate(
            slide.get("composition_asset_bindings", ())
        ):
            if (
                isinstance(binding, dict)
                and binding.get("status") in {"resolved", "generated"}
                and binding.get("asset_id") in governed_assets
            ):
                source_refs[f"composition-asset-{index}"] = binding["asset_id"]
        secondary_fragments = [
            fragment
            for block in slide["blocks"]
            if block["id"] != basis_id
            for fragment in _block_content(block)
        ]
        valid_image_sources, rejected_image_sources = _preflight_image_sources(
            source_refs, governed_assets
        )
        # A purely decorative empty frame is indistinguishable from a missing
        # image placeholder in customer output.  Until a decoration carries a
        # governed semantic or brand asset binding, keep it out of automatic
        # layout selection.  Real image frames remain available only after
        # source/evidence preflight.
        forbidden = set()
        if slide.get("composition_motif") is None:
            forbidden.add("decoration")
        if not valid_image_sources:
            forbidden.add("image-frame")
        if slide["page_family"] == "focal-statement":
            forbidden.add(
                "statement" if basis_block.get("kind") == "quote" else "quote"
            )
        forbidden_components = frozenset(forbidden)
        for source_ref, rejection in rejected_image_sources.items():
            findings.append(
                RenderFinding(
                    "ASSET_POLICY_REJECTED",
                    f"slides.{slide['id']}",
                    f"asset {source_ref} rejected before layout selection: {rejection}",
                )
            )
        if source_refs and not valid_image_sources:
            findings.append(
                RenderFinding(
                    "ASSET_NATIVE_FALLBACK",
                    f"slides.{slide['id']}",
                    "no valid governed image was available; using an assetless native composition",
                )
            )
        if basis_block.get("kind") == "image" and valid_image_sources:
            item_count = len(valid_image_sources)
        component_limits = (
            {"image-frame": len(valid_image_sources)}
            if valid_image_sources
            else None
        )
        if slide.get("materializer_layout_id"):
            layout_selector = slide["materializer_layout_id"]
        elif slide.get("composition_layout_enforced"):
            layout_selector = slide["composition_layout_id"]
        elif (
            slide["page_family"] == "cards"
            and _uses_compact_three_cards(basis_block)
        ):
            layout_selector = "cards.compact-three"
        else:
            layout_selector = slide["page_family"]
        resolved_item_count = (
            None
            if slide.get("composition_layout_enforced")
            or slide.get("materializer_layout_id")
            else item_count
        )
        try:
            layout = resolve_layout(
                layout_selector,
                slide_size,
                previous_layouts,
                item_count=resolved_item_count,
                density=density,
                variant_seed=slide_variant_seed,
                forbidden_components=forbidden_components,
                component_limits=component_limits,
            )
        except ValueError as exc:
            if (
                slide.get("composition_layout_enforced")
                and slide.get("materializer_layout_id") is None
                and slide.get("composition_layout_id") is not None
                and layout_selector != slide["page_family"]
            ):
                try:
                    layout = resolve_layout(
                        slide["page_family"],
                        slide_size,
                        previous_layouts,
                        item_count=item_count,
                        density=density,
                        variant_seed=slide_variant_seed,
                        forbidden_components=forbidden_components,
                        component_limits=component_limits,
                    )
                except ValueError:
                    pass
                else:
                    findings.append(
                        RenderFinding(
                            "COMPOSITION_LAYOUT_FALLBACK",
                            f"slides.{slide['id']}",
                            (
                                f"{layout_selector} was not serviceable ({exc}); "
                                f"using registered family fallback {layout.id}"
                            ),
                        )
                    )
                    exc = None
            if exc is None:
                pass
            elif not forbidden_components or not (
                "forbidden component" in str(exc)
                or str(exc).startswith("no ")
            ):
                raise
            else:
                fallback_selector = "structured-content"
                layout = resolve_layout(
                    fallback_selector,
                    slide_size,
                    previous_layouts,
                    item_count=item_count,
                    density=density,
                    variant_seed=slide_variant_seed,
                    forbidden_components=forbidden_components,
                    component_limits=component_limits,
                )
                findings.append(
                    RenderFinding(
                        "ASSETLESS_LAYOUT_FALLBACK",
                        f"slides.{slide['id']}",
                        (
                            f"{slide['page_family']} had no serviceable assetless variant; "
                            f"using {layout.family_id}"
                        ),
                    )
                )
        slide_title = str(
            slide.get("title") or slide["role"].replace("-", " ").title()
        )
        title_safe_layout = _resolve_title_safe_layout(
            layout,
            slide_title,
            slide_size=slide_size,
            previous_layouts=previous_layouts,
            item_count=item_count,
            density=density,
            variant_seed=slide_variant_seed,
            forbidden_components=forbidden_components,
            component_limits=component_limits,
            typography=theme.typography,
        )
        if title_safe_layout.id != layout.id:
            findings.append(
                RenderFinding(
                    "TITLE_CAPACITY_LAYOUT_FALLBACK",
                    f"slides.{slide['id']}",
                    (
                        f"{layout.id} could not fit the governed title; "
                        f"using {title_safe_layout.id}"
                    ),
                )
            )
            layout = title_safe_layout
        fragments = _without_title_duplication(fragments, slide.get("title"))
        secondary_fragments = _without_title_duplication(
            secondary_fragments, slide.get("title")
        )
        if (
            layout.id == "cta.poster-editorial"
            and _poster_closing_slot_texts("\n\n".join(fragments)) is None
        ):
            poster_layout = layout
            layout = resolve_layout(
                "cta.full-visual-stage",
                slide_size,
                previous_layouts,
                item_count=item_count,
                density=density,
                variant_seed=slide_variant_seed,
                forbidden_components=forbidden_components,
                component_limits=component_limits,
            )
            findings.append(
                RenderFinding(
                    "POSTER_CTA_SEMANTIC_FALLBACK",
                    f"slides.{slide['id']}",
                    (
                        f"{poster_layout.id} requires one proof line and exactly "
                        f"three decision chips; using {layout.id} for the "
                        "source-preserving single-action close"
                    ),
                )
            )
        if (
            layout.id == "cta.decision-three"
            and _decision_three_slot_texts(
                "\n\n".join(fragments),
                scenario=str(project.get("scenario", "")),
            )
            is None
        ):
            decision_layout = layout
            fallback_id = (
                "cta.full-visual-stage"
                if valid_image_sources
                else "cta.top-band"
            )
            layout = resolve_layout(
                fallback_id,
                slide_size,
                previous_layouts,
                item_count=item_count,
                density=density,
                variant_seed=slide_variant_seed,
                forbidden_components=forbidden_components,
                component_limits=component_limits,
            )
            findings.append(
                RenderFinding(
                    "DECISION_CTA_SEMANTIC_FALLBACK",
                    f"slides.{slide['id']}",
                    (
                        f"{decision_layout.id} requires exactly three explicit "
                        f"decision chips; using {layout.id} to preserve the "
                        "single evidence-backed action"
                    ),
                )
            )
        advanced_slots = tuple(
            slot
            for slot in layout.slots
            if slot.component in ADVANCED_COMPONENTS
        )
        if advanced_slots and secondary_fragments:
            mixed_layout = _resolve_advanced_mixed_layout(
                layout,
                secondary_fragments,
                title=slide_title,
                slide=slide,
                project=project,
                slide_size=slide_size,
                previous_layouts=previous_layouts,
                item_count=item_count,
                density=density,
                variant_seed=slide_variant_seed,
                forbidden_components=forbidden_components,
                component_limits=component_limits,
                typography=theme.typography,
            )
            if mixed_layout.id != layout.id:
                findings.append(
                    RenderFinding(
                        "ADVANCED_MULTI_BLOCK_LAYOUT_FALLBACK",
                        f"slides.{slide['id']}",
                        (
                            f"{layout.id} had no safe supplemental fact slot; "
                            f"using {mixed_layout.id}"
                        ),
                    )
                )
                layout = mixed_layout
                advanced_slots = tuple(
                    slot
                    for slot in layout.slots
                    if slot.component in ADVANCED_COMPONENTS
                )
        advanced_support: str | None = None
        if advanced_slots and _governed_text_slots(layout):
            support_limit = min(
                _slot_text_capacity(slot, theme.typography)
                for slot in _governed_text_slots(layout)
            )
            advanced_support = _existing_support_text(basis_block, support_limit)
            if all(
                slot.component
                in {"process-step", "timeline-node", "matrix-cell"}
                for slot in advanced_slots
            ):
                # Native diagram children already render every governed node
                # label/detail.  Repeating the basis sentence in a support
                # slot creates a false note and wastes the lower page band.
                advanced_support = None
            if (
                advanced_support is not None
                and "".join(advanced_support.casefold().split())
                == "".join(str(slide.get("title") or "").casefold().split())
            ):
                advanced_support = None
            if advanced_support is None and not secondary_fragments:
                focus_layout = _resolve_advanced_focus_layout(
                    layout.family_id,
                    title=slide_title,
                    slide_size=slide_size,
                    previous_layouts=previous_layouts,
                    item_count=item_count,
                    density=density,
                    forbidden_components=forbidden_components,
                    component_limits=component_limits,
                    typography=theme.typography,
                )
                if focus_layout is None:
                    raise RenderPlanError(
                        f"layout {layout.id} requires unsupported supplemental text"
                    )
                if _governed_text_slots(focus_layout):
                    raise RenderPlanError(
                        f"advanced focus layout {focus_layout.id} still requires supplemental text"
                    )
                findings.append(
                    RenderFinding(
                        "ADVANCED_FOCUS_LAYOUT_FALLBACK",
                        f"slides.{slide['id']}",
                        (
                            f"{layout.id} had no bounded evidence-backed support text; "
                            f"using {focus_layout.id}"
                        ),
                    )
                )
                layout = focus_layout
                advanced_slots = tuple(
                    slot
                    for slot in layout.slots
                    if slot.component in ADVANCED_COMPONENTS
                )
        if advanced_slots:
            display_fragments = list(secondary_fragments)
            normalized_secondary = {
                "".join(fragment.casefold().split())
                for fragment in secondary_fragments
            }
            if (
                advanced_support
                and "".join(advanced_support.casefold().split())
                not in normalized_secondary
            ):
                display_fragments.append(advanced_support)
        else:
            display_fragments = fragments
        slot_texts = _complete_slot_texts(
            layout, display_fragments, slide, project
        )
        overflowing_slots = _overflowing_text_slots(
            layout, slot_texts, theme.typography
        )
        if (
            overflowing_slots
            and advanced_slots
            and advanced_support is not None
            and secondary_fragments
        ):
            # The basis is already represented by the native chart/table/diagram.
            # Supplemental facts are mandatory; the optional extractive basis
            # summary is the first thing removed when the governed slot is full.
            slot_texts = _complete_slot_texts(
                layout, secondary_fragments, slide, project
            )
            overflowing_slots = _overflowing_text_slots(
                layout, slot_texts, theme.typography
            )
        if overflowing_slots and not advanced_slots:
            same_family_repair = _resolve_text_safe_layout(
                layout,
                fragments,
                title=slide_title,
                slide=slide,
                project=project,
                slide_size=slide_size,
                previous_layouts=previous_layouts,
                item_count=item_count,
                density=density,
                variant_seed=slide_variant_seed,
                forbidden_components=forbidden_components,
                component_limits=component_limits,
                typography=theme.typography,
            )
            if same_family_repair is None:
                repaired_layout = resolve_layout(
                    "executive-summary.top-band",
                    slide_size,
                    previous_layouts,
                    item_count=item_count,
                    density=density,
                    forbidden_components=forbidden_components,
                    component_limits=component_limits,
                )
                repaired_slot_texts = _complete_slot_texts(
                    repaired_layout, fragments, slide, project
                )
                if _overflowing_text_slots(
                    repaired_layout, repaired_slot_texts, theme.typography
                ):
                    raise RenderPlanError(
                        f"slide {slide['id']} exceeds the largest governed text composition"
                    )
            else:
                repaired_layout, repaired_slot_texts = same_family_repair
            findings.append(
                RenderFinding(
                    "TEXT_CAPACITY_LAYOUT_FALLBACK",
                    f"slides.{slide['id']}",
                    (
                        f"{layout.id} could not fit governed text in slots "
                        f"{', '.join(overflowing_slots)}; using {repaired_layout.id}"
                    ),
                )
            )
            layout = repaired_layout
            slot_texts = repaired_slot_texts
            advanced_slots = ()
        elif overflowing_slots:
            raise RenderPlanError(
                f"slide {slide['id']} advanced support text exceeds governed capacity"
            )
        previous_layouts += (layout.id,)
        semantic_payload = dict(basis_block)
        selected_form = slide.get("decision_trace", {}).get("selected")
        if (
            any(slot.component == "chart" for slot in advanced_slots)
            and selected_form in CHART_TYPE_BY_SEMANTIC_FORM
        ):
            semantic_payload[INTERNAL_SELECTED_FORM_FIELD] = selected_form
        semantic_source = _canonical_semantic_block(semantic_payload)
        linked_slots = advanced_slots or tuple(
            slot
            for slot in layout.slots
            if slot.component not in {"title", "footer", "decoration", "accent"}
        )
        hyperlink_slot_ids = (
            {slot.id for slot in advanced_slots}
            if advanced_slots
            else ({linked_slots[0].id} if linked_slots else set())
        )
        available_sources = iter(
            source_ref
            for source_ref in source_refs.values()
            if source_ref in valid_image_sources
        )
        content_group = f"wp_s{slide_index:03d}_content"
        objects: list[RenderObject] = []
        advanced_index = 0
        for object_index, slot in enumerate(layout.slots, start=1):
            object_id = f"{slide['id']}.{slot.id}"
            name = (
                f"wp_s{slide_index:03d}_{object_index:02d}_"
                f"{_safe_identifier(slot.id)}"
            )
            source_path: Path | None = None
            asset_record: AssetRecord | None = None
            source_ref = next(available_sources, None) if slot.component == "image-frame" else None
            if source_ref is not None and source_ref in governed_assets:
                source_path, asset_record, rejection = _resolve_asset_binding(
                    governed_assets.get(source_ref),
                    slot,
                )
                if rejection is not None:
                    findings.append(
                        RenderFinding(
                            "ASSET_POLICY_REJECTED",
                            f"slides.{slide['id']}.{slot.id}",
                            f"asset {source_ref} rejected: {rejection}",
                        )
                    )
            elif slot.component == "image-frame":
                raise RenderPlanError(
                    f"layout {layout.id} has an unresolved image-frame slot {slot.id}"
                )

            advanced: AdvancedSpec | None = None
            is_advanced_slot = slot.component in ADVANCED_COMPONENTS
            if is_advanced_slot:
                advanced = _advanced_spec(
                    slot.component,
                    layout.family_id,
                    basis_block,
                    advanced_index=advanced_index,
                    advanced_count=len(advanced_slots),
                    selected_form=slide.get("decision_trace", {}).get("selected"),
                )
                advanced_index += 1
                if advanced is None:
                    findings.append(
                        RenderFinding(
                            "ADVANCED_NATIVE_FALLBACK",
                            f"slides.{slide['id']}.{slot.id}",
                            (
                                f"{slot.component} semantic data is incomplete; "
                                "using a native editable fallback"
                            ),
                        )
                    )

            if slot.component == "title":
                text = _poster_title_text(
                    slide.get("title") or slide["role"].replace("-", " ").title(),
                    layout_id=layout.id,
                )
            elif slot.component == "footer":
                text = f"{slide_index} / {slide_total}"
            elif slot.component == "image-frame":
                text = None
            else:
                text = (
                    _existing_support_text(
                        basis_block,
                        _slot_text_capacity(slot, theme.typography),
                    )
                    if is_advanced_slot and advanced is None
                    else slot_texts.get(slot.id)
                )
                if is_advanced_slot and advanced is None and text is None:
                    raise RenderPlanError(
                        f"slides.{slide['id']}.{slot.id} has no bounded evidence-backed fallback"
                    )
            if advanced is not None:
                text = None
            group_id = (
                None
                if slot.component == "footer" or motion == "step-reveal"
                else content_group
            )
            carries_semantics = is_advanced_slot or slot.id in hyperlink_slot_ids
            font_size_pt = _font_size(
                slot.component,
                theme.typography,
                text=text,
                slot=slot,
                role=slide["role"],
                family_id=layout.family_id,
            )
            if (
                layout.id == "cta.poster-editorial"
                and slot.component == "card"
            ):
                font_size_pt = theme.typography["subtitle"]
            motif_value = slide.get("composition_motif")
            slide_motif_id = (
                motif_value.get("motif_id")
                if isinstance(motif_value, Mapping)
                else None
            )
            fill_color, text_color = _slot_style(
                component=slot.component,
                slot_id=slot.id,
                layout_id=layout.id,
                colors=theme.colors,
                motif_id=slide_motif_id,
            )
            rich_text_colors = dict(theme.colors)
            if text_color == theme.colors["background"]:
                rich_text_colors["muted_text"] = theme.colors["background"]
                rich_text_colors["primary"] = (
                    theme.colors["background"]
                    if slot.component == "comparison-panel"
                    else theme.colors["accent"]
                )
            elif layout.id == "cta.poster-editorial" and slot.id == "primary":
                rich_text_colors["primary"] = theme.colors["accent"]
            text_runs = _rich_text_runs(
                slot.component,
                text,
                value_font_size_pt=(
                    theme.typography["title"]
                    if (
                        layout.id == "cta.poster-editorial"
                        and slot.id == "primary"
                    )
                    else font_size_pt
                ),
                typography=theme.typography,
                colors=rich_text_colors,
            )
            objects.append(
                RenderObject(
                    id=object_id,
                    name=name,
                    component=slot.component,
                    kind=_object_kind(
                        slot.component, source_path is not None, advanced
                    ),
                    x=slot.x,
                    y=slot.y,
                    width=slot.width,
                    height=slot.height,
                    layer=LAYER_BY_COMPONENT.get(slot.component, 30),
                    group_id=group_id,
                    native_editable=True,
                    text=text,
                    source_path=source_path,
                    asset_record=asset_record,
                    font_name=(
                        theme.fonts["heading"]
                        if slot.component
                        in {
                            "title",
                            "kpi",
                            "comparison-panel",
                            "recommendation-panel",
                            "statement",
                            "quote",
                            "cta",
                        }
                        else theme.fonts["body"]
                    ),
                    font_size_pt=font_size_pt,
                    text_color=text_color,
                    fill_color=fill_color,
                    line_color=theme.colors["primary"],
                    advanced=advanced,
                    semantic_source=semantic_source if carries_semantics else None,
                    hyperlink=(
                        basis_block.get("hyperlink")
                        if slot.id in hyperlink_slot_ids
                        else None
                    ),
                    text_runs=text_runs,
                )
            )
        for unused_source in available_sources:
            findings.append(
                RenderFinding(
                    "ASSET_SOURCE_UNUSED",
                    f"slides.{slide['id']}",
                    (
                        f"asset source {unused_source} exceeds the selected layout "
                        "capacity and was not rendered"
                    ),
                )
            )
        objects.extend(
            _art_direction_objects(
                slide={**slide, "resolved_layout_id": layout.id},
                slide_index=slide_index,
                slide_size=slide_size,
                family_id=layout.family_id,
                theme=theme,
            )
        )
        render_item_count = max(
            layout.capacity.min_items,
            min(item_count, layout.capacity.max_items),
        )
        motif_value = slide.get("composition_motif")
        slide_motif_id = (
            motif_value.get("motif_id")
            if isinstance(motif_value, Mapping)
            else None
        )
        background_color = _governed_slide_background(
            theme.colors,
            motif_id=slide_motif_id,
            role=slide["role"],
            slide_index=slide_index,
        )
        render_slides.append(
            RenderSlide(
                source_id=slide["id"],
                index=slide_index,
                role=slide["role"],
                title=slide.get("title"),
                family_id=layout.family_id,
                layout_id=layout.id,
                item_count=render_item_count,
                requested_density=density,
                resolved_density=layout.resolved_density,
                background_color=background_color,
                objects=tuple(objects),
                speaker_notes=slide.get("speaker_notes"),
                motion=motion,
                composition_id=slide.get("composition_id"),
                variant_id=slide.get("composition_variant_id"),
                emphasis=slide.get("composition_emphasis", "standard"),
                energy=slide.get("composition_energy", "flow"),
                fact_refs=tuple(slide.get("composition_fact_refs", ())),
                component_intents=tuple(
                    item["component_id"]
                    for item in slide.get("composition_slot_bindings", ())
                ),
                asset_intents=tuple(
                    item["asset_id"]
                    for item in slide.get("composition_asset_bindings", ())
                ),
                motif_id=(
                    slide.get("composition_motif", {}).get("motif_id")
                    if isinstance(slide.get("composition_motif"), dict)
                    else None
                ),
                motif_variant=(
                    slide.get("composition_motif", {}).get("variant")
                    if isinstance(slide.get("composition_motif"), dict)
                    else None
                ),
                motif_intensity=(
                    slide.get("composition_motif", {}).get("intensity")
                    if isinstance(slide.get("composition_motif"), dict)
                    else None
                ),
                direction_annotation=_direction_annotation(slide),
            )
        )

    plan = RenderPlan(
        schema_version=RENDER_PLAN_VERSION,
        compiler_version=compiled["compiler_version"],
        project_title=project["title"],
        theme_id=theme.id,
        brand=resolved_brand,
        locale=locale,
        installed_fonts=font_inventory,
        slide_size=slide_size,
        background_color=theme.colors["background"],
        slides=tuple(render_slides),
        findings=tuple(findings),
        theme_events=theme.events,
    )
    return validate_render_plan(plan)


def compile_render_plan(
    payload: DeckPlan | Mapping[str, Any],
    *,
    slide_size: SlideSize,
    installed_fonts: set[str],
    theme_id: str | None = None,
    brand: BrandOverrides | None = None,
    asset_bindings: Mapping[str, AssetBinding] | None = None,
    preferred_families: tuple[str, ...] = (),
    visual_family_by_slide: Mapping[str, str] | None = None,
    visual_recipe_by_slide: Mapping[str, str] | None = None,
    composition_by_slide: Mapping[str, Mapping[str, Any]] | None = None,
    template_layout_by_slide: Mapping[str, str] | None = None,
    art_direction_id: str | None = None,
) -> tuple[dict[str, Any], RenderPlan]:
    """Compile semantic input exactly once and build its governed render plan."""

    compiled = compile_deck_plan(
        payload,
        preferred_families=preferred_families,
        visual_family_by_slide=visual_family_by_slide,
        visual_recipe_by_slide=visual_recipe_by_slide,
        composition_by_slide=composition_by_slide,
        template_layout_by_slide=template_layout_by_slide,
    )
    plan = _build_render_plan_from_compiled(
        compiled,
        slide_size=slide_size,
        installed_fonts=installed_fonts,
        theme_id=theme_id,
        brand=brand,
        asset_bindings=asset_bindings,
        art_direction_id=art_direction_id,
    )
    return compiled, plan


def build_render_plan(
    payload: DeckPlan | Mapping[str, Any],
    *,
    slide_size: SlideSize,
    installed_fonts: set[str],
    theme_id: str | None = None,
    brand: BrandOverrides | None = None,
    asset_bindings: Mapping[str, AssetBinding] | None = None,
    preferred_families: tuple[str, ...] = (),
    visual_family_by_slide: Mapping[str, str] | None = None,
    visual_recipe_by_slide: Mapping[str, str] | None = None,
    composition_by_slide: Mapping[str, Mapping[str, Any]] | None = None,
    template_layout_by_slide: Mapping[str, str] | None = None,
    art_direction_id: str | None = None,
) -> RenderPlan:
    """Compile semantic input and join it to exact governed render commands."""

    return compile_render_plan(
        payload,
        slide_size=slide_size,
        installed_fonts=installed_fonts,
        theme_id=theme_id,
        brand=brand,
        asset_bindings=asset_bindings,
        preferred_families=preferred_families,
        visual_family_by_slide=visual_family_by_slide,
        visual_recipe_by_slide=visual_recipe_by_slide,
        composition_by_slide=composition_by_slide,
        template_layout_by_slide=template_layout_by_slide,
        art_direction_id=art_direction_id,
    )[1]


__all__ = [
    "AssetBinding",
    "ChartSeries",
    "ChartSpec",
    "DiagramNode",
    "DiagramSpec",
    "RenderFinding",
    "RenderObject",
    "RenderPlan",
    "RenderPlanError",
    "RenderSlide",
    "TableSpec",
    "TextRun",
    "build_render_plan",
    "compile_render_plan",
    "inches_to_points",
    "load_asset_bindings",
    "semantic_form_chart_type",
    "validate_render_plan",
]
