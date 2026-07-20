"""Pure compilation from semantic DeckPlan input to governed render commands."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

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
            "background_color": self.background_color,
            "objects": [item.to_dict() for item in self.objects],
        }


@dataclass(frozen=True)
class RenderPlan:
    schema_version: str
    compiler_version: str
    project_title: str
    theme_id: str
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
    return len(block.get("items", [])) or 1


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
    if not HEX_COLOR.fullmatch(plan.background_color):
        raise RenderPlanError("render plan background color is invalid")
    if not isinstance(plan.project_title, str) or not plan.project_title.strip():
        raise RenderPlanError("render plan project title is invalid")
    if not isinstance(plan.slide_size, SlideSize) or not all(
        _valid_number(value, positive=True)
        for value in (plan.slide_size.width, plan.slide_size.height)
    ):
        raise RenderPlanError("render plan slide geometry must be finite and positive")
    if not isinstance(plan.slides, tuple) or not plan.slides:
        raise RenderPlanError("render plan must contain slides")

    layout_registry = load_layout_registry()
    components = load_components()
    slide_ids: set[str] = set()
    object_ids: set[str] = set()
    object_names: set[str] = set()
    for expected_index, slide in enumerate(plan.slides, start=1):
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
        if not HEX_COLOR.fullmatch(slide.background_color):
            raise RenderPlanError(f"render slide {slide.source_id} color is invalid")
        if not isinstance(slide.objects, tuple) or not slide.objects:
            raise RenderPlanError(f"render slide {slide.source_id} has no objects")
        for item in slide.objects:
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
            elif item.source_path is not None:
                raise RenderPlanError(f"{path} has an unexpected image source")
    return plan


def build_render_plan(
    payload: DeckPlan | Mapping[str, Any],
    *,
    slide_size: SlideSize,
    installed_fonts: set[str],
    theme_id: str | None = None,
    brand: BrandOverrides | None = None,
    asset_paths: Mapping[str, Path | str] | None = None,
) -> RenderPlan:
    """Compile semantic input and join it to exact theme/layout/component commands."""

    compiled = compile_deck_plan(payload)
    project = compiled["project"]
    selected_theme = theme_id or select_theme(
        project["scenario"], audience=project.get("audience")
    )
    theme = resolve_theme(
        selected_theme,
        brand=brand,
        installed_fonts=installed_fonts,
        locale=project.get("language", "en-US"),
    )
    trusted_assets = dict(asset_paths or {})
    findings: list[RenderFinding] = []
    render_slides: list[RenderSlide] = []
    previous_layouts: tuple[str, ...] = ()
    density = compiled.get("preferences", {}).get("density", "balanced")
    slide_total = len(compiled["slides"])

    for slide_index, slide in enumerate(compiled["slides"], start=1):
        layout = resolve_layout(
            slide["page_family"],
            slide_size,
            previous_layouts,
            item_count=_item_count(slide),
            density=density,
        )
        previous_layouts += (layout.id,)
        fragments, source_refs = _slide_content(slide)
        slot_texts = _slot_texts(layout.slots, fragments)
        available_sources = tuple(source_refs.values())
        content_group = f"wp_s{slide_index:03d}_content"
        objects: list[RenderObject] = []
        for object_index, slot in enumerate(layout.slots, start=1):
            object_id = f"{slide['id']}.{slot.id}"
            name = (
                f"wp_s{slide_index:03d}_{object_index:02d}_"
                f"{_safe_identifier(slot.id)}"
            )
            source_path: Path | None = None
            if slot.component == "image-frame" and available_sources:
                source_ref = available_sources[0]
                candidate = trusted_assets.get(source_ref)
                if candidate is not None:
                    resolved = Path(candidate).expanduser().resolve(strict=False)
                    if resolved.is_file():
                        source_path = resolved
                if source_path is None:
                    findings.append(
                        RenderFinding(
                            "ASSET_NATIVE_FALLBACK",
                            f"slides.{slide['id']}.{slot.id}",
                            f"trusted local asset unavailable for {source_ref}",
                        )
                    )
            elif slot.component == "image-frame":
                findings.append(
                    RenderFinding(
                        "ASSET_NATIVE_FALLBACK",
                        f"slides.{slide['id']}.{slot.id}",
                        "no governed asset was supplied; using native composition",
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
                    font_name=(
                        theme.fonts["heading"]
                        if slot.component in {"title", "kpi", "quote", "cta"}
                        else theme.fonts["body"]
                    ),
                    font_size_pt=_font_size(slot.component, theme.typography),
                    text_color=theme.colors["text"],
                    fill_color=(
                        theme.colors["surface"]
                        if slot.component not in {"title", "body-text", "footer"}
                        else theme.colors["background"]
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
                background_color=theme.colors["background"],
                objects=tuple(objects),
            )
        )

    plan = RenderPlan(
        schema_version=RENDER_PLAN_VERSION,
        compiler_version=compiled["compiler_version"],
        project_title=project["title"],
        theme_id=theme.id,
        slide_size=slide_size,
        background_color=theme.colors["background"],
        slides=tuple(render_slides),
        findings=tuple(findings),
    )
    return validate_render_plan(plan)


__all__ = [
    "RenderFinding",
    "RenderObject",
    "RenderPlan",
    "RenderPlanError",
    "RenderSlide",
    "build_render_plan",
    "inches_to_points",
    "validate_render_plan",
]
