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
from .deck_plan import DeckPlan, compile_deck_plan
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


def _object_kind(component: str, has_image: bool) -> str:
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
    if not isinstance(plan.locale, str) or not plan.locale.strip():
        raise RenderPlanError("render plan locale is invalid")
    if not isinstance(plan.installed_fonts, tuple) or not all(
        isinstance(font, str) and font.strip() for font in plan.installed_fonts
    ):
        raise RenderPlanError("render plan font inventory is invalid")
    governed_theme = resolve_theme(
        plan.theme_id,
        brand=plan.brand,
        installed_fonts=set(plan.installed_fonts),
        locale=plan.locale,
    )
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
            if item.kind not in {"text", "shape", "image"}:
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
                None if slot.component == "footer" else f"wp_s{slide.index:03d}_content"
            )
            expected_kind = _object_kind(
                slot.component, item.source_path is not None
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
    locale = project.get("language", "en-US")
    font_inventory = tuple(sorted(installed_fonts, key=str.casefold))
    theme = resolve_theme(
        selected_theme,
        brand=resolved_brand,
        installed_fonts=set(font_inventory),
        locale=locale,
    )
    governed_assets = dict(asset_bindings or {})
    findings: list[RenderFinding] = []
    render_slides: list[RenderSlide] = []
    previous_layouts: tuple[str, ...] = ()
    density = compiled.get("preferences", {}).get("density", "balanced")
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
        available_sources = iter(source_refs.values())
        content_group = f"wp_s{slide_index:03d}_content"
        objects: list[RenderObject] = []
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

            if slot.component == "title":
                text = slide.get("title") or slide["role"].replace("-", " ").title()
            elif slot.component == "footer":
                text = f"{slide_index} / {slide_total}"
            elif slot.component == "image-frame":
                text = None if source_path else "Visual asset unavailable"
            else:
                text = slot_texts.get(slot.id)
            if slot.component in ADVANCED_COMPONENTS:
                findings.append(
                    RenderFinding(
                        "DEFERRED_ADVANCED_COMPONENT",
                        f"slides.{slide['id']}.{slot.id}",
                        f"{slot.component} uses an editable native fallback until Phase 26",
                        "info",
                    )
                )
            group_id = None if slot.component == "footer" else content_group
            objects.append(
                RenderObject(
                    id=object_id,
                    name=name,
                    component=slot.component,
                    kind=_object_kind(slot.component, source_path is not None),
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
    "RenderFinding",
    "RenderObject",
    "RenderPlan",
    "RenderPlanError",
    "RenderSlide",
    "build_render_plan",
    "compile_render_plan",
    "inches_to_points",
    "load_asset_bindings",
    "validate_render_plan",
]
