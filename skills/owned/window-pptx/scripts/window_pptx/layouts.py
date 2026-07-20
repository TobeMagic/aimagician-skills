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

EXPECTED_FAMILIES = {
    "agenda",
    "big-number",
    "cards",
    "case-study",
    "comparison",
    "cover",
    "cta",
    "data-chart",
    "executive-summary",
    "focal-statement",
    "funnel",
    "image-story",
    "matrix",
    "process",
    "product-showcase",
    "quadrant",
    "risk-recommendation",
    "roadmap",
    "section",
    "summary",
    "table",
    "team",
    "text-media",
    "timeline",
}
EXPECTED_SEMANTIC_FORMS = {
    "area-chart",
    "bar-chart",
    "before-after",
    "big-number",
    "bubble-chart",
    "cards",
    "comparison",
    "composition-chart",
    "distribution-chart",
    "dot-plot",
    "focal-statement",
    "image-story",
    "kpi-dashboard",
    "line-chart",
    "matrix",
    "modular-grid",
    "process",
    "product-showcase",
    "quadrant",
    "recommendation",
    "risk-recommendation",
    "roadmap",
    "scatter-plot",
    "stacked-bar",
    "structured-content",
    "table",
    "text-media",
    "timeline",
}
EXPECTED_THEMES = {
    "executive-light",
    "executive-dark",
    "technology",
    "finance-investor",
    "marketing-vibrant",
    "ecommerce-editorial",
    "education-training",
    "public-enterprise",
}
EXPECTED_COMPONENTS = {
    "title",
    "body-text",
    "card",
    "kpi",
    "image-frame",
    "icon",
    "chart",
    "table",
    "process-step",
    "timeline-node",
    "matrix-cell",
    "comparison-panel",
    "risk-panel",
    "recommendation-panel",
    "footer",
    "decoration",
    "quote",
    "team-member",
    "cta",
}
FAMILY_COMPONENT_REQUIREMENTS = {
    "big-number": {"kpi"},
    "cards": {"card"},
    "comparison": {"comparison-panel"},
    "timeline": {"timeline-node"},
    "process": {"process-step"},
    "matrix": {"matrix-cell"},
    "quadrant": {"matrix-cell", "chart"},
    "funnel": {"process-step", "chart"},
    "roadmap": {"timeline-node", "process-step"},
    "data-chart": {"chart"},
    "table": {"table"},
    "product-showcase": {"image-frame"},
    "team": {"team-member"},
    "risk-recommendation": {
        "risk-panel",
        "recommendation-panel",
        "matrix-cell",
    },
    "cta": {"cta"},
    "image-story": {"image-frame"},
}
PHASE23_SERVICE_MAX = {
    "structured-content": 8,
    "focal-statement": 1,
    "text-media": 4,
    "cards": 5,
    "modular-grid": 5,
    "process": 6,
    "timeline": 6,
    "roadmap": 6,
    "comparison": 5,
    "before-after": 5,
    "table": 9,
    "big-number": 5,
    "kpi-dashboard": 5,
    "line-chart": 10,
    "area-chart": 10,
    "bar-chart": 10,
    "composition-chart": 9,
    "stacked-bar": 9,
    "distribution-chart": 10,
    "dot-plot": 10,
    "scatter-plot": 10,
    "bubble-chart": 10,
    "matrix": 9,
    "quadrant": 9,
    "risk-recommendation": 5,
    "recommendation": 5,
    "image-story": 4,
    "product-showcase": 4,
}


@dataclass(frozen=True)
class SlideSize:
    width: float
    height: float


@dataclass(frozen=True)
class GridDefinition:
    columns: int
    rows: int
    column_gap: float
    row_gap: float
    reference_width_in: float
    reference_height_in: float
    spacing_base_pt: int

    def box(
        self,
        safe_bounds: tuple[float, float, float, float],
        col: int,
        row: int,
        col_span: int,
        row_span: int,
    ) -> tuple[float, float, float, float]:
        safe_x, safe_y, safe_width, safe_height = safe_bounds
        column_width = (
            safe_width - (self.columns - 1) * self.column_gap
        ) / self.columns
        row_height = (
            safe_height - (self.rows - 1) * self.row_gap
        ) / self.rows
        x = safe_x + col * (column_width + self.column_gap)
        y = safe_y + row * (row_height + self.row_gap)
        width = col_span * column_width + (col_span - 1) * self.column_gap
        height = row_span * row_height + (row_span - 1) * self.row_gap
        return x, y, width, height


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
    col: int
    row: int
    col_span: int
    row_span: int
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
    grid: GridDefinition
    recipes: dict[str, tuple[RecipeSlot, ...]]
    recipe_capacities: dict[str, LayoutCapacity]
    recipe_capacity_slots: dict[str, tuple[str, ...]]
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
    requested_density: str
    resolved_density: str
    fallback_reason: str | None
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
    grid_raw = raw["grid"]
    reference = grid_raw["reference_slide"]
    grid = GridDefinition(
        columns=int(grid_raw["columns"]),
        rows=int(grid_raw["rows"]),
        column_gap=float(grid_raw["column_gap"]),
        row_gap=float(grid_raw["row_gap"]),
        reference_width_in=float(reference["width_in"]),
        reference_height_in=float(reference["height_in"]),
        spacing_base_pt=int(grid_raw["spacing_base_pt"]),
    )
    recipes: dict[str, tuple[RecipeSlot, ...]] = {}
    recipe_capacities: dict[str, LayoutCapacity] = {}
    recipe_capacity_slots: dict[str, tuple[str, ...]] = {}
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
        recipe_capacity_slots[recipe_id] = tuple(entry["capacity_slots"])
        parsed_slots: list[RecipeSlot] = []
        for slot in entry["slots"]:
            col = int(slot["col"])
            row = int(slot["row"])
            col_span = int(slot["col_span"])
            row_span = int(slot["row_span"])
            x, y, width, height = grid.box(
                tuple(float(value) for value in safe_bounds),  # type: ignore[arg-type]
                col,
                row,
                col_span,
                row_span,
            )
            parsed_slots.append(
                RecipeSlot(
                    id=slot["id"],
                    component=slot["component"],
                    col=col,
                    row=row,
                    col_span=col_span,
                    row_span=row_span,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    allow_overlap=bool(slot.get("allow_overlap", False)),
                )
            )
        recipes[recipe_id] = tuple(parsed_slots)

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
        grid=grid,
        recipes=recipes,
        recipe_capacities=recipe_capacities,
        recipe_capacity_slots=recipe_capacity_slots,
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


def _effective_capacity(
    registry: LayoutRegistry,
    components: dict[str, ComponentDefinition],
    variant: LayoutVariant,
) -> LayoutCapacity:
    declared = registry.recipe_capacities[variant.recipe_id]
    slots = {slot.id: slot for slot in registry.recipes[variant.recipe_id]}
    overrides = dict(variant.component_overrides)
    component_limit = sum(
        components[overrides.get(slot_id, slots[slot_id].component)].max_items
        for slot_id in registry.recipe_capacity_slots[variant.recipe_id]
    )
    return LayoutCapacity(
        min_items=declared.min_items,
        max_items=min(declared.max_items, component_limit),
        densities=declared.densities,
    )


def _resolve_density(capacity: LayoutCapacity, requested: str) -> str | None:
    orders = {
        "sparse": ("sparse", "balanced", "dense"),
        "balanced": ("balanced", "sparse", "dense"),
        "dense": ("dense", "balanced", "sparse"),
    }
    return next(
        (candidate for candidate in orders[requested] if candidate in capacity.densities),
        None,
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
    if set(components) != EXPECTED_COMPONENTS:
        issues.append(
            RegistryIssue(
                "COMPONENT_SET",
                "components",
                "component set is incomplete or unexpected",
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
        or not math.isfinite(asset_policy.minimum_quality)
        or asset_policy.minimum_quality < 0
        or asset_policy.minimum_raster_short_edge_px < 1
    ):
        issues.append(
            RegistryIssue("ASSET_POLICY", "asset_policy", "unsafe asset policy")
        )

    if set(themes) != EXPECTED_THEMES:
        issues.append(
            RegistryIssue("THEME_COUNT", "themes", "expected eight governed themes")
        )
    for theme in themes.values():
        typography = theme.foundation.get("typography", {})
        if (
            typography.get("body", 0) < 16
            or typography.get("label", 0) < 11
            or typography.get("footnote", 0) < 11
            or any(value < 11 for value in typography.values())
        ):
            issues.append(
                RegistryIssue(
                    "THEME_TYPOGRAPHY",
                    f"themes.{theme.id}.typography",
                    "type hierarchy falls below governed minima",
                )
            )
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

    if set(registry.families) != EXPECTED_FAMILIES:
        issues.append(
            RegistryIssue(
                "FAMILY_SET", "families", "registered family set is incomplete or unexpected"
            )
        )
    if set(registry.semantic_form_map) != EXPECTED_SEMANTIC_FORMS:
        issues.append(
            RegistryIssue(
                "SEMANTIC_FORM_SET",
                "semantic_form_map",
                "Phase 23 semantic form coverage is incomplete or unexpected",
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
    foundation = next(iter(themes.values())).foundation
    theme_grid = foundation["grid"]
    spacing = foundation["spacing"]
    if (
        registry.grid.columns != theme_grid["columns"]
        or registry.grid.spacing_base_pt != next(
            (value for value in spacing if value > 0), None
        )
        or abs(
            safe_x
            - theme_grid["safe_margin_x_in"] / registry.grid.reference_width_in
        )
        > 0.005
        or abs(
            safe_y
            - theme_grid["safe_margin_y_in"] / registry.grid.reference_height_in
        )
        > 0.005
    ):
        issues.append(
            RegistryIssue(
                "GRID_TOKEN_DRIFT",
                "grid",
                "layout grid diverges from governed theme foundation",
            )
        )
    if (
        not all(
            math.isfinite(value)
            for value in (
                registry.grid.column_gap,
                registry.grid.row_gap,
                registry.grid.reference_width_in,
                registry.grid.reference_height_in,
            )
        )
        or registry.grid.columns < 1
        or registry.grid.rows < 1
        or registry.grid.column_gap < 0
        or registry.grid.row_gap < 0
        or registry.grid.reference_width_in <= 0
        or registry.grid.reference_height_in <= 0
    ):
        issues.append(
            RegistryIssue("INVALID_GRID", "grid", "grid values must be finite and positive")
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
        capacity_slots = registry.recipe_capacity_slots[recipe_id]
        slot_ids = {slot.id for slot in slots}
        if (
            not capacity_slots
            or len(capacity_slots) != len(set(capacity_slots))
            or not set(capacity_slots) <= slot_ids
        ):
            issues.append(
                RegistryIssue(
                    "CAPACITY_SLOTS", recipe_id, "invalid capacity slot allocation"
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
                slot.col < 0
                or slot.row < 0
                or slot.col_span < 1
                or slot.row_span < 1
                or slot.col + slot.col_span > registry.grid.columns
                or slot.row + slot.row_span > registry.grid.rows
            ):
                issues.append(
                    RegistryIssue(
                        "GRID_PLACEMENT", path, "slot crosses governed grid"
                    )
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
        if all(
            slot_id in recipe_slots and component_id in components
            for slot_id, component_id in variant.component_overrides
        ):
            effective = _effective_capacity(registry, components, variant)
            if effective.max_items < effective.min_items:
                issues.append(
                    RegistryIssue(
                        "VARIANT_CAPACITY",
                        variant.id,
                        "component capacity is below declared minimum",
                    )
                )
    for family in registry.families.values():
        if len(family.variant_ids) < 3:
            issues.append(
                RegistryIssue("VARIANT_COUNT", family.id, "fewer than three variants")
            )
        signatures: set[tuple[tuple[object, ...], ...]] = set()
        required_components = FAMILY_COMPONENT_REQUIREMENTS.get(family.id)
        for variant_id in family.variant_ids:
            variant = registry.variants[variant_id]
            overrides = dict(variant.component_overrides)
            slots = registry.recipes[variant.recipe_id]
            signatures.add(
                tuple(
                    (
                        overrides.get(slot.id, slot.component),
                        slot.col,
                        slot.row,
                        slot.col_span,
                        slot.row_span,
                    )
                    for slot in slots
                )
            )
            if required_components is not None and not required_components & {
                overrides.get(slot.id, slot.component) for slot in slots
            }:
                issues.append(
                    RegistryIssue(
                        "SEMANTIC_COMPONENT",
                        variant.id,
                        "variant lacks its family semantic component",
                    )
                )
        if len(signatures) < 3:
            issues.append(
                RegistryIssue(
                    "VARIANT_DIVERSITY",
                    family.id,
                    "family has fewer than three distinct compositions",
                )
            )
    for form, family_id in registry.semantic_form_map.items():
        if family_id not in registry.families:
            issues.append(RegistryIssue("UNKNOWN_FAMILY", form, family_id))
    for form, maximum in PHASE23_SERVICE_MAX.items():
        family_id = registry.semantic_form_map.get(form)
        family = registry.families.get(family_id or "")
        if family is None:
            continue
        for density in ("sparse", "balanced", "dense"):
            for item_count in {1, maximum}:
                serviceable = False
                for variant_id in family.variant_ids:
                    variant = registry.variants[variant_id]
                    try:
                        capacity = _effective_capacity(
                            registry, components, variant
                        )
                    except KeyError:
                        continue
                    if (
                        capacity.min_items <= item_count <= capacity.max_items
                        and _resolve_density(capacity, density) is not None
                    ):
                        serviceable = True
                        break
                if not serviceable:
                    issues.append(
                        RegistryIssue(
                            "LAYOUT_SERVICE_GAP",
                            f"{form}.{density}.{item_count}",
                            "no variant can service a valid Phase 23 output",
                        )
                    )
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

    if (
        not math.isfinite(slide_size.width)
        or not math.isfinite(slide_size.height)
        or slide_size.width <= 0
        or slide_size.height <= 0
    ):
        raise ValueError("slide size must be finite and positive")
    if density not in {"sparse", "balanced", "dense"}:
        raise ValueError(f"unknown density: {density}")
    if item_count is not None and (
        isinstance(item_count, bool)
        or not isinstance(item_count, int)
        or item_count < 0
    ):
        raise ValueError("item_count must be a non-negative integer")
    registry = load_layout_registry()
    components = load_components()
    if selector in registry.variants:
        variant = registry.variants[selector]
        capacity = _effective_capacity(registry, components, variant)
        resolved_density = _resolve_density(capacity, density)
        if (
            resolved_density is None
            or item_count is not None
            and not capacity.min_items <= item_count <= capacity.max_items
        ):
            raise ValueError(
                f"layout {selector} cannot fit item_count={item_count}, density={density}"
            )
    else:
        family_id = registry.semantic_form_map.get(selector, selector)
        family = registry.families.get(family_id)
        if family is None:
            raise ValueError(f"unknown layout selector: {selector}")
        candidates: list[tuple[str, LayoutCapacity, str]] = []
        for variant_id in family.variant_ids:
            candidate = registry.variants[variant_id]
            candidate_capacity = _effective_capacity(
                registry, components, candidate
            )
            candidate_density = _resolve_density(candidate_capacity, density)
            item_fits = item_count is None or (
                candidate_capacity.min_items
                <= item_count
                <= candidate_capacity.max_items
            )
            if candidate_density is not None and item_fits:
                candidates.append(
                    (variant_id, candidate_capacity, candidate_density)
                )
        compatible = tuple(candidate[0] for candidate in candidates)
        if not compatible:
            raise ValueError(
                f"no {family_id} layout can fit item_count={item_count}, density={density}"
            )
        last_compatible = next(
            (item for item in reversed(previous_layouts) if item in compatible),
            None,
        )
        if last_compatible is None:
            variant_id = compatible[0]
        else:
            variant_id = compatible[
                (compatible.index(last_compatible) + 1) % len(compatible)
            ]
        variant = registry.variants[variant_id]
        _, capacity, resolved_density = next(
            candidate for candidate in candidates if candidate[0] == variant_id
        )
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
        requested_density=density,
        resolved_density=resolved_density,
        fallback_reason=(
            None
            if density == resolved_density
            else "DENSITY_COMPATIBILITY_FALLBACK"
        ),
        slide_size=slide_size,
        slots=slots,
    )
