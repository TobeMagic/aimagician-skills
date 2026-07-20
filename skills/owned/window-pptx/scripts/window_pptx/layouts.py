"""Strict component/layout registries and normalized layout resolution."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .assets import load_asset_policy
from .themes import contrast_ratio, load_themes


SKILL_ROOT = Path(__file__).resolve().parents[2]
LAYOUTS_PATH = SKILL_ROOT / "registries" / "layouts.json"
COMPONENTS_PATH = SKILL_ROOT / "registries" / "components.json"
LEGACY_PATH = SKILL_ROOT / "registries" / "legacy-templates.json"


@dataclass(frozen=True)
class SlideSize:
    width: float
    height: float


@dataclass(frozen=True)
class ComponentDefinition:
    id: str
    object_policy: str
    min_font_pt: int
    max_items: int


@dataclass(frozen=True)
class RecipeSlot:
    id: str
    component: str
    x: float
    y: float
    width: float
    height: float
    allow_overlap: bool = False


@dataclass(frozen=True)
class LayoutCapacity:
    min_items: int
    max_items: int
    densities: tuple[str, ...]

    def accepts(self, item_count: int | None, density: str) -> bool:
        return (
            density in self.densities
            and (item_count is None or self.min_items <= item_count <= self.max_items)
        )


@dataclass(frozen=True)
class LayoutVariant:
    id: str
    family_id: str
    recipe_id: str
    component_overrides: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class LayoutFamily:
    id: str
    variant_ids: tuple[str, ...]


@dataclass(frozen=True)
class LayoutRegistry:
    safe_bounds: tuple[float, float, float, float]
    recipes: dict[str, tuple[RecipeSlot, ...]]
    recipe_capacities: dict[str, LayoutCapacity]
    families: dict[str, LayoutFamily]
    variants: dict[str, LayoutVariant]
    semantic_form_map: dict[str, str]


@dataclass(frozen=True)
class ResolvedSlot:
    id: str
    component: str
    x: float
    y: float
    width: float
    height: float
    allow_overlap: bool


@dataclass(frozen=True)
class ResolvedLayout:
    id: str
    family_id: str
    recipe_id: str
    capacity: LayoutCapacity
    slide_size: SlideSize
    slots: tuple[ResolvedSlot, ...]


@dataclass(frozen=True)
class LegacyTemplate:
    id: str
    path: str
    status: str
    auto_recommend: bool


@dataclass(frozen=True)
class RegistryIssue:
    code: str
    path: str
    message: str


def _read_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "1.0":
        raise ValueError(f"unsupported registry version: {path}")
    return raw


def load_components(
    path: Path | str | None = None,
) -> dict[str, ComponentDefinition]:
    registry_path = Path(path) if path is not None else COMPONENTS_PATH
    raw = _read_json(registry_path)
    result: dict[str, ComponentDefinition] = {}
    for entry in raw["components"]:
        component = ComponentDefinition(
            id=entry["id"],
            object_policy=entry["object_policy"],
            min_font_pt=int(entry["min_font_pt"]),
            max_items=int(entry["max_items"]),
        )
        if component.id in result:
            raise ValueError(f"duplicate component id: {component.id}")
        result[component.id] = component
    return result


def load_layout_registry(path: Path | str | None = None) -> LayoutRegistry:
    registry_path = Path(path) if path is not None else LAYOUTS_PATH
    raw = _read_json(registry_path)
    safe = raw["safe_bounds"]
    safe_bounds = (safe["x"], safe["y"], safe["width"], safe["height"])
    recipes: dict[str, tuple[RecipeSlot, ...]] = {}
    recipe_capacities: dict[str, LayoutCapacity] = {}
    for entry in raw["recipes"]:
        recipe_id = entry["id"]
        if recipe_id in recipes:
            raise ValueError(f"duplicate recipe id: {recipe_id}")
        capacity = entry["capacity"]
        recipe_capacities[recipe_id] = LayoutCapacity(
            min_items=int(capacity["min_items"]),
            max_items=int(capacity["max_items"]),
            densities=tuple(capacity["densities"]),
        )
        recipes[recipe_id] = tuple(
            RecipeSlot(
                id=slot["id"],
                component=slot["component"],
                x=float(slot["x"]),
                y=float(slot["y"]),
                width=float(slot["width"]),
                height=float(slot["height"]),
                allow_overlap=bool(slot.get("allow_overlap", False)),
            )
            for slot in entry["slots"]
        )

    families: dict[str, LayoutFamily] = {}
    variants: dict[str, LayoutVariant] = {}
    for entry in raw["families"]:
        family_id = entry["id"]
        if family_id in families:
            raise ValueError(f"duplicate family id: {family_id}")
        variant_ids: list[str] = []
        for variant in entry["variants"]:
            variant_id = variant["id"]
            if variant_id in variants:
                raise ValueError(f"duplicate layout variant id: {variant_id}")
            variants[variant_id] = LayoutVariant(
                id=variant_id,
                family_id=family_id,
                recipe_id=variant["recipe"],
                component_overrides=tuple(
                    sorted(variant.get("components", {}).items())
                ),
            )
            variant_ids.append(variant_id)
        families[family_id] = LayoutFamily(family_id, tuple(variant_ids))
    return LayoutRegistry(
        safe_bounds=tuple(float(value) for value in safe_bounds),  # type: ignore[arg-type]
        recipes=recipes,
        recipe_capacities=recipe_capacities,
        families=families,
        variants=variants,
        semantic_form_map=dict(raw["semantic_form_map"]),
    )


def load_legacy_templates(
    path: Path | str | None = None,
) -> tuple[LegacyTemplate, ...]:
    registry_path = Path(path) if path is not None else LEGACY_PATH
    raw = _read_json(registry_path)
    return tuple(
        LegacyTemplate(
            id=entry["id"],
            path=entry["path"],
            status=entry["status"],
            auto_recommend=entry["auto_recommend"],
        )
        for entry in raw["templates"]
    )


def _overlap(first: RecipeSlot, second: RecipeSlot) -> bool:
    return not (
        first.x + first.width <= second.x
        or second.x + second.width <= first.x
        or first.y + first.height <= second.y
        or second.y + second.height <= first.y
    )


def validate_registry_bundle() -> list[RegistryIssue]:
    """Return stable actionable issues for every design registry contract."""

    issues: list[RegistryIssue] = []
    try:
        components = load_components()
        registry = load_layout_registry()
        legacy = load_legacy_templates()
        asset_policy = load_asset_policy()
        themes = load_themes()
    except Exception as exc:
        return [RegistryIssue("REGISTRY_LOAD", "$", str(exc))]

    for component in components.values():
        if component.object_policy not in {"native_editable", "linked_asset"}:
            issues.append(
                RegistryIssue(
                    "COMPONENT_POLICY", component.id, "unsupported object policy"
                )
            )
        if component.min_font_pt < 11 or component.max_items < 1:
            issues.append(
                RegistryIssue(
                    "COMPONENT_CAPACITY", component.id, "unsafe type or item minimum"
                )
            )

    if (
        asset_policy.crop_mode != "cover"
        or asset_policy.allow_stretch
        or set(asset_policy.required_provenance)
        != {"source", "license", "retrieved_at"}
        or asset_policy.icon_style_scope != "one-family-per-deck"
        or asset_policy.missing_asset_fallback != "native-editable-composition"
    ):
        issues.append(
            RegistryIssue("ASSET_POLICY", "asset_policy", "unsafe asset policy")
        )

    if len(themes) != 8:
        issues.append(
            RegistryIssue("THEME_COUNT", "themes", "expected eight governed themes")
        )
    for theme in themes.values():
        for foreground, background, threshold in (
            ("text", "background", 4.5),
            ("muted_text", "background", 3.0),
        ):
            if contrast_ratio(
                theme.colors[foreground], theme.colors[background]
            ) < threshold:
                issues.append(
                    RegistryIssue(
                        "THEME_CONTRAST",
                        f"themes.{theme.id}.{foreground}",
                        f"contrast below {threshold}",
                    )
                )

    safe_x, safe_y, safe_width, safe_height = registry.safe_bounds
    if (
        not all(math.isfinite(value) for value in registry.safe_bounds)
        or safe_x < 0
        or safe_y < 0
        or safe_width <= 0
        or safe_height <= 0
        or safe_x + safe_width > 1
        or safe_y + safe_height > 1
    ):
        issues.append(
            RegistryIssue(
                "INVALID_SAFE_BOUNDS", "safe_bounds", "bounds must fit normalized page"
            )
        )
    safe_right, safe_bottom = safe_x + safe_width, safe_y + safe_height
    for recipe_id, slots in registry.recipes.items():
        capacity = registry.recipe_capacities[recipe_id]
        if (
            capacity.min_items < 0
            or capacity.max_items < 1
            or capacity.min_items > capacity.max_items
            or not capacity.densities
            or not set(capacity.densities) <= {"sparse", "balanced", "dense"}
            or len(capacity.densities) != len(set(capacity.densities))
        ):
            issues.append(
                RegistryIssue(
                    "RECIPE_CAPACITY", recipe_id, "invalid capacity contract"
                )
            )
        seen: set[str] = set()
        for slot in slots:
            path = f"recipes.{recipe_id}.{slot.id}"
            if slot.id in seen:
                issues.append(RegistryIssue("DUPLICATE_SLOT", path, "duplicate slot id"))
            seen.add(slot.id)
            if slot.component not in components:
                issues.append(
                    RegistryIssue("UNKNOWN_COMPONENT", path, slot.component)
                )
            if (
                not all(
                    math.isfinite(value)
                    for value in (slot.x, slot.y, slot.width, slot.height)
                )
                or slot.width <= 0
                or slot.height <= 0
            ):
                issues.append(
                    RegistryIssue(
                        "INVALID_SLOT_GEOMETRY", path, "slot must be finite and positive"
                    )
                )
            if (
                slot.x < safe_x
                or slot.y < safe_y
                or slot.x + slot.width > safe_right + 1e-9
                or slot.y + slot.height > safe_bottom + 1e-9
            ):
                issues.append(
                    RegistryIssue("OUTSIDE_SAFE_BOUNDS", path, "slot crosses safe area")
                )
        for index, first in enumerate(slots):
            for second in slots[index + 1 :]:
                if (
                    not first.allow_overlap
                    and not second.allow_overlap
                    and _overlap(first, second)
                ):
                    issues.append(
                        RegistryIssue(
                            "UNINTENDED_OVERLAP",
                            f"recipes.{recipe_id}",
                            f"{first.id} overlaps {second.id}",
                        )
                    )

    for variant in registry.variants.values():
        if variant.recipe_id not in registry.recipes:
            issues.append(
                RegistryIssue("UNKNOWN_RECIPE", variant.id, variant.recipe_id)
            )
            continue
        recipe_slots = {slot.id for slot in registry.recipes[variant.recipe_id]}
        for slot_id, component_id in variant.component_overrides:
            if slot_id not in recipe_slots:
                issues.append(
                    RegistryIssue(
                        "UNKNOWN_OVERRIDE_SLOT", variant.id, slot_id
                    )
                )
            if component_id not in components:
                issues.append(
                    RegistryIssue(
                        "UNKNOWN_OVERRIDE_COMPONENT", variant.id, component_id
                    )
                )
    for family in registry.families.values():
        if len(family.variant_ids) < 3:
            issues.append(
                RegistryIssue("VARIANT_COUNT", family.id, "fewer than three variants")
            )
    for form, family_id in registry.semantic_form_map.items():
        if family_id not in registry.families:
            issues.append(RegistryIssue("UNKNOWN_FAMILY", form, family_id))
    for template in legacy:
        if template.status != "legacy_unverified" or template.auto_recommend:
            issues.append(
                RegistryIssue(
                    "LEGACY_NOT_QUARANTINED", template.id, "legacy template is selectable"
                )
            )
        if not (SKILL_ROOT / template.path).is_file():
            issues.append(
                RegistryIssue("LEGACY_MISSING", template.id, template.path)
            )
    return sorted(issues, key=lambda issue: (issue.code, issue.path, issue.message))


def resolve_layout(
    selector: str,
    slide_size: SlideSize,
    previous_layouts: tuple[str, ...] = (),
    *,
    item_count: int | None = None,
    density: str = "balanced",
) -> ResolvedLayout:
    """Resolve a semantic form/family/variant and scale its governed slots."""

    if slide_size.width <= 0 or slide_size.height <= 0:
        raise ValueError("slide size must be positive")
    if density not in {"sparse", "balanced", "dense"}:
        raise ValueError(f"unknown density: {density}")
    if item_count is not None and (
        isinstance(item_count, bool)
        or not isinstance(item_count, int)
        or item_count < 0
    ):
        raise ValueError("item_count must be a non-negative integer")
    registry = load_layout_registry()
    if selector in registry.variants:
        variant = registry.variants[selector]
        capacity = registry.recipe_capacities[variant.recipe_id]
        if not capacity.accepts(item_count, density):
            raise ValueError(
                f"layout {selector} cannot fit item_count={item_count}, density={density}"
            )
    else:
        family_id = registry.semantic_form_map.get(selector, selector)
        family = registry.families.get(family_id)
        if family is None:
            raise ValueError(f"unknown layout selector: {selector}")
        compatible = tuple(
            variant_id
            for variant_id in family.variant_ids
            if registry.recipe_capacities[
                registry.variants[variant_id].recipe_id
            ].accepts(item_count, density)
        )
        if not compatible:
            raise ValueError(
                f"no {family_id} layout can fit item_count={item_count}, density={density}"
            )
        previous = set(previous_layouts)
        variant_id = next(
            (item for item in compatible if item not in previous),
            compatible[0],
        )
        variant = registry.variants[variant_id]
        capacity = registry.recipe_capacities[variant.recipe_id]
    slots = tuple(
        ResolvedSlot(
            id=slot.id,
            component=dict(variant.component_overrides).get(
                slot.id, slot.component
            ),
            x=round(slot.x * slide_size.width, 6),
            y=round(slot.y * slide_size.height, 6),
            width=round(slot.width * slide_size.width, 6),
            height=round(slot.height * slide_size.height, 6),
            allow_overlap=slot.allow_overlap,
        )
        for slot in registry.recipes[variant.recipe_id]
    )
    return ResolvedLayout(
        id=variant.id,
        family_id=variant.family_id,
        recipe_id=variant.recipe_id,
        capacity=capacity,
        slide_size=slide_size,
        slots=slots,
    )
