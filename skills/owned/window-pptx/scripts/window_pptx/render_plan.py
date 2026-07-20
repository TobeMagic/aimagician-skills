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
    ResolvedSlot,
    SlideSize,
    load_components,
    load_layout_registry,
    resolve_layout,
    validate_registry_bundle,
)
from .themes import HEX_COLOR, THEME_IDS, BrandOverrides, resolve_theme, select_theme


RENDER_PLAN_VERSION = "1.0"
MIN_POWERPOINT_SLIDE_IN = 1.0
MAX_POWERPOINT_SLIDE_IN = 56.0
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
ADVANCED_COMPONENTS = {
    "chart",
    "table",
    "process-step",
    "timeline-node",
    "matrix-cell",
}
ADVANCED_KINDS = {"chart", "table", "diagram"}
CHART_TYPES = {"line", "column", "bar", "doughnut", "stacked-column", "scatter"}
DIAGRAM_TYPES = {"process", "timeline", "matrix", "quadrant", "funnel", "roadmap"}
TEXT_COMPONENTS = {"title", "body-text", "footer", "quote", "cta"}
LAYER_BY_COMPONENT = {
    "decoration": 10,
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "chart",
            "chart_type": self.chart_type,
            "categories": list(self.categories),
            "series": [item.to_dict() for item in self.series],
        }


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "compiler_version": self.compiler_version,
            "project_title": self.project_title,
            "theme_id": self.theme_id,
            "brand": {
                "primary": self.brand.primary,
                "accent": self.brand.accent,
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
        heading = next((str(value[key]) for key in labels if key in value), "")
        metric = ""
        if "value" in value:
            metric = str(value["value"])
            if value.get("unit") is not None:
                metric += str(value["unit"])
        remaining = [
            str(value[key])
            for key in sorted(value)
            if key not in {*labels, "value", "unit"}
        ]
        return "\n".join(part for part in (heading, metric, *remaining) if part)
    return str(value)


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


def _chart_spec(block: Mapping[str, Any]) -> ChartSpec | None:
    raw_items = block.get("items", [])
    if not isinstance(raw_items, list):
        return None
    intent = block.get("chart_intent") or block.get("kind")
    chart_type = {
        "trend": "line",
        "comparison": "column",
        "composition": "doughnut",
        "distribution": "column",
        "relationship": "scatter",
    }.get(intent, "column")
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
    default_series = str(block.get("title") or "Value")
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        value = _chart_value(item)
        if value is None:
            continue
        category = _item_label(item, index)
        series_name = str(item.get("series") or default_series)
        if category not in categories:
            categories.append(category)
        if series_name not in series_order:
            series_order.append(series_name)
        values_by_series.setdefault(series_name, {})[category] = value
    if not categories or not series_order:
        return None
    if chart_type == "doughnut" and len(series_order) > 1:
        chart_type = "stacked-column"
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


def _advanced_spec(
    component: str,
    family_id: str,
    block: Mapping[str, Any],
    *,
    advanced_index: int,
    advanced_count: int,
) -> AdvancedSpec | None:
    if family_id in DIAGRAM_TYPES:
        nodes = _diagram_nodes(block)
        if advanced_count > 1:
            nodes = nodes[advanced_index : advanced_index + 1]
        return DiagramSpec(family_id, nodes) if nodes else None
    if component == "chart":
        return _chart_spec(block)
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
            nodes = nodes[advanced_index : advanced_index + 1]
        return DiagramSpec(diagram_type, nodes) if nodes else None
    return None


def _slide_content(slide: Mapping[str, Any]) -> tuple[list[str], dict[str, str]]:
    fragments: list[str] = []
    sources: dict[str, str] = {}
    for block in slide["blocks"]:
        block_id = block["id"]
        if block.get("source_ref"):
            sources[block_id] = block["source_ref"]
        items = block.get("items", [])
        if items:
            fragments.extend(_format_item(item) for item in items)
        else:
            for key in ("text", "title"):
                if block.get(key):
                    fragments.append(str(block[key]))
                    break
    return fragments, sources


def _item_count(slide: Mapping[str, Any]) -> int:
    basis_id = slide["semantic_basis"]["block_id"]
    block = next(item for item in slide["blocks"] if item["id"] == basis_id)
    basis_count = len(block.get("items", [])) or 1
    referenced_assets = sum(
        1 for item in slide["blocks"] if item.get("source_ref")
    )
    return max(basis_count, referenced_assets)


def _slot_texts(slots: tuple[ResolvedSlot, ...], fragments: list[str]) -> dict[str, str]:
    content_slots = [
        slot
        for slot in slots
        if slot.component not in {"title", "footer", "image-frame", "decoration"}
    ]
    if not content_slots or not fragments:
        return {}
    if len(content_slots) == 1:
        return {content_slots[0].id: "\n\n".join(fragments)}
    result: dict[str, str] = {}
    for index, fragment in enumerate(fragments):
        slot = content_slots[min(index, len(content_slots) - 1)]
        result[slot.id] = (
            result[slot.id] + "\n\n" + fragment
            if slot.id in result
            else fragment
        )
    return result


def _font_size(component: str, typography: Mapping[str, int]) -> int:
    if component == "title":
        return typography["title"]
    if component == "footer":
        return typography["footnote"]
    if component in {"kpi", "quote"}:
        return typography["subtitle"]
    if component in {"decoration", "icon", "image-frame"}:
        return typography["label"]
    return typography["body"]


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


def _expected_fill(component: str, background: str, surface: str) -> str:
    return surface if component not in {"title", "body-text", "footer"} else background


def _expected_font(component: str, heading: str, body: str) -> str:
    return heading if component in {"title", "kpi", "quote", "cta"} else body


def _validate_brand_context(brand: BrandOverrides) -> None:
    for field in ("primary", "accent"):
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
        if slide.background_color != governed_theme.colors["background"]:
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
        if len(slide.objects) != len(governed_layout.slots):
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
            if slot.component not in {"title", "footer", "decoration"}
        )
        hyperlink_slot_id = linked_slots[0].id if linked_slots else None
        governed_semantic_source: str | None = None
        for object_index, (item, slot) in enumerate(
            zip(slide.objects, governed_layout.slots), start=1
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
            is_advanced_slot = slot.component in ADVANCED_COMPONENTS
            carries_semantics = is_advanced_slot or slot.id == hyperlink_slot_id
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
                if slot.id == hyperlink_slot_id and semantic_block is not None
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
            if (
                item.font_name
                != _expected_font(
                    slot.component,
                    governed_theme.fonts["heading"],
                    governed_theme.fonts["body"],
                )
                or item.font_size_pt
                != _font_size(slot.component, governed_theme.typography)
                or item.text_color != governed_theme.colors["text"]
                or item.fill_color
                != _expected_fill(
                    slot.component,
                    governed_theme.colors["background"],
                    governed_theme.colors["surface"],
                )
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
    density = compiled.get("preferences", {}).get("density", "balanced")
    motion = compiled.get("preferences", {}).get("motion", "off")
    slide_total = len(compiled["slides"])

    for slide_index, slide in enumerate(compiled["slides"], start=1):
        item_count = _item_count(slide)
        layout = resolve_layout(
            slide["page_family"],
            slide_size,
            previous_layouts,
            item_count=item_count,
            density=density,
        )
        previous_layouts += (layout.id,)
        fragments, source_refs = _slide_content(slide)
        slot_texts = _slot_texts(layout.slots, fragments)
        basis_id = slide["semantic_basis"]["block_id"]
        basis_block = next(block for block in slide["blocks"] if block["id"] == basis_id)
        semantic_source = _canonical_semantic_block(basis_block)
        advanced_slots = tuple(
            slot
            for slot in layout.slots
            if slot.component in ADVANCED_COMPONENTS
        )
        linked_slots = advanced_slots or tuple(
            slot
            for slot in layout.slots
            if slot.component not in {"title", "footer", "decoration"}
        )
        hyperlink_slot_id = linked_slots[0].id if linked_slots else None
        available_sources = iter(source_refs.values())
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
                findings.append(
                    RenderFinding(
                        "ASSET_NATIVE_FALLBACK",
                        f"slides.{slide['id']}.{slot.id}",
                        (
                            f"no governed asset was supplied for {source_ref}; "
                            "using native composition"
                            if source_ref is not None
                            else "no asset reference was supplied; using native composition"
                        ),
                    )
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
                text = slide.get("title") or slide["role"].replace("-", " ").title()
            elif slot.component == "footer":
                text = f"{slide_index} / {slide_total}"
            elif slot.component == "image-frame":
                text = None if source_path else "Visual asset unavailable"
            else:
                text = slot_texts.get(slot.id)
            if advanced is not None:
                text = None
            group_id = (
                None
                if slot.component == "footer" or motion == "step-reveal"
                else content_group
            )
            carries_semantics = is_advanced_slot or slot.id == hyperlink_slot_id
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
                        if slot.component in {"title", "kpi", "quote", "cta"}
                        else theme.fonts["body"]
                    ),
                    font_size_pt=_font_size(slot.component, theme.typography),
                    text_color=theme.colors["text"],
                    fill_color=_expected_fill(
                        slot.component,
                        theme.colors["background"],
                        theme.colors["surface"],
                    ),
                    line_color=theme.colors["primary"],
                    advanced=advanced,
                    semantic_source=semantic_source if carries_semantics else None,
                    hyperlink=(
                        basis_block.get("hyperlink")
                        if slot.id == hyperlink_slot_id
                        else None
                    ),
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
        render_slides.append(
            RenderSlide(
                source_id=slide["id"],
                index=slide_index,
                role=slide["role"],
                title=slide.get("title"),
                family_id=layout.family_id,
                layout_id=layout.id,
                item_count=item_count,
                requested_density=density,
                resolved_density=layout.resolved_density,
                background_color=theme.colors["background"],
                objects=tuple(objects),
                speaker_notes=slide.get("speaker_notes"),
                motion=motion,
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
) -> tuple[dict[str, Any], RenderPlan]:
    """Compile semantic input exactly once and build its governed render plan."""

    compiled = compile_deck_plan(payload)
    plan = _build_render_plan_from_compiled(
        compiled,
        slide_size=slide_size,
        installed_fonts=installed_fonts,
        theme_id=theme_id,
        brand=brand,
        asset_bindings=asset_bindings,
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
) -> RenderPlan:
    """Compile semantic input and join it to exact governed render commands."""

    return compile_render_plan(
        payload,
        slide_size=slide_size,
        installed_fonts=installed_fonts,
        theme_id=theme_id,
        brand=brand,
        asset_bindings=asset_bindings,
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
    "build_render_plan",
    "compile_render_plan",
    "inches_to_points",
    "load_asset_bindings",
    "validate_render_plan",
]
