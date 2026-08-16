"""Compile NarrativePlan semantics into governed VisualPlan and AssetPlan.

The compiler deliberately converts open-ended visual design into bounded,
traceable choices.  It uses role and semantic rules first, then DesignPack
capabilities, pacing constraints, density rhythm, and safe fallbacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .design_packs import DesignPack, select_design_pack
from .composition_grammar import select_composition_recipe
from .weak_model import NarrativePlan, NarrativeSlide


@dataclass(frozen=True)
class VisualSlide:
    slide_id: str
    role: str
    family: str
    variant: str
    emphasis: str
    density: str
    components: tuple[str, ...]
    asset_refs: tuple[str, ...]
    decision_rules: tuple[str, ...]
    recipe_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_id": self.slide_id,
            "role": self.role,
            "family": self.family,
            "variant": self.variant,
            "emphasis": self.emphasis,
            "density": self.density,
            "components": list(self.components),
            "asset_refs": list(self.asset_refs),
            "decision_rules": list(self.decision_rules),
            "recipe_id": self.recipe_id,
        }


@dataclass(frozen=True)
class VisualPlan:
    design_pack_id: str
    template_pack_id: str | None
    theme_id: str
    slides: tuple[VisualSlide, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "design_pack_id": self.design_pack_id,
            "template_pack_id": self.template_pack_id,
            "theme_id": self.theme_id,
            "slides": [slide.to_dict() for slide in self.slides],
        }


@dataclass(frozen=True)
class PlannedAsset:
    id: str
    slide_id: str
    purpose: str
    kind: str
    priority: tuple[str, ...]
    fallback: str
    editable: bool
    status: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "slide_id": self.slide_id,
            "purpose": self.purpose,
            "kind": self.kind,
            "priority": list(self.priority),
            "fallback": self.fallback,
            "editable": self.editable,
            "status": self.status,
        }


@dataclass(frozen=True)
class AssetPlan:
    design_pack_id: str
    assets: tuple[PlannedAsset, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "design_pack_id": self.design_pack_id,
            "assets": [asset.to_dict() for asset in self.assets],
        }


_ROLE_CANDIDATES: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    (("cover",), ("cover",), "ROLE_COVER"),
    (("agenda", "contents"), ("contents", "executive-summary"), "ROLE_CONTENTS"),
    (("section",), ("section", "cover"), "ROLE_SECTION"),
    (("executive-summary", "abstract"), ("executive-summary", "abstract", "evidence-cards"), "ROLE_SUMMARY"),
    (("market-size", "key-metrics", "year-at-a-glance", "traction", "financials"), ("big-number", "chart-story", "annotated-chart"), "ROLE_KPI"),
    (("performance", "targets", "trends", "measurement", "evidence", "findings"), ("chart-story", "annotated-chart", "small-multiples", "big-number"), "ROLE_DATA"),
    (("timeline", "milestones", "roadmap", "calendar", "next-year-priorities"), ("roadmap", "timeline", "process"), "ROLE_SEQUENCE"),
    (("process", "approach", "method", "implementation", "demo-flow", "ways-of-working"), ("process", "method", "demo-flow"), "ROLE_PROCESS"),
    (("comparison", "competition", "differentiation", "before-after", "choices"), ("comparison", "before-after", "matrix"), "ROLE_COMPARE"),
    (("matrix", "segments", "audience"), ("matrix", "quadrant", "evidence-cards", "card-grid"), "ROLE_MATRIX"),
    (("funnel", "commerce-funnel", "channel-plan"), ("funnel", "chart-story", "process"), "ROLE_FUNNEL"),
    (("product", "product-showcase", "solution", "value-proposition"), ("product-hero", "feature-bento", "comparison", "executive-summary"), "ROLE_PRODUCT"),
    (("case-study", "proof", "social-proof", "wins"), ("case-study", "social-proof", "evidence-cards"), "ROLE_CASE"),
    (("team", "roles", "governance", "workstreams"), ("team", "team-orbit", "org-map", "process"), "ROLE_ORG"),
    (("risks", "limitations", "issues"), ("risk-actions", "matrix", "comparison"), "ROLE_RISK"),
    (("recommendations", "action-plan", "next-steps", "immediate-actions"), ("recommendation", "risk-actions", "roadmap", "takeaways"), "ROLE_ACTION"),
    (("closing", "call-to-action", "cta", "funding-ask"), ("cta", "closing", "recommendation"), "ROLE_CLOSING"),
)

_SEMANTIC_CANDIDATES = {
    "trend": ("annotated-chart", "chart-story", "small-multiples"),
    "composition": ("chart-story", "distribution", "small-multiples"),
    "comparison": ("comparison", "before-after", "matrix"),
    "process": ("process", "demo-flow", "roadmap"),
    "timeline": ("timeline", "roadmap", "process"),
    "hierarchy": ("org-map", "process", "card-grid"),
    "matrix": ("matrix", "quadrant", "card-grid"),
    "metric": ("big-number", "chart-story", "evidence-cards"),
    "table": ("table", "evidence-cards", "comparison"),
    "quote": ("case-study", "social-proof", "executive-summary"),
    "image": ("product-hero", "feature-bento", "case-study"),
    "cards": ("card-grid", "evidence-cards", "feature-bento"),
}

_FAMILY_VARIANTS = {
    "cover": ("editorial-hero", "stage-hero", "minimal-brand"),
    "section": ("numbered-divider", "image-divider", "statement-divider"),
    "executive-summary": ("message-evidence", "three-proof-cards", "takeaway-rail"),
    "big-number": ("hero-metric", "metric-towers", "metric-grid"),
    "chart-story": ("chart-callout", "chart-plus-kpi", "dual-chart"),
    "annotated-chart": ("chart-callout", "small-multiple", "evidence-margin"),
    "comparison": ("split-contrast", "before-after", "comparison-table"),
    "process": ("horizontal-steps", "swimlane", "radial-process"),
    "timeline": ("milestone-lane", "phased-roadmap", "calendar-band"),
    "roadmap": ("phased-roadmap", "milestone-lane", "workstream-roadmap"),
    "matrix": ("two-axis-matrix", "prioritization-grid", "segmentation-map"),
    "card-grid": ("three-card-row", "bento-grid", "evidence-cards"),
    "evidence-cards": ("three-card-row", "metric-card-grid", "annotated-cards"),
    "risk-actions": ("risk-action-pairs", "heatmap-actions", "priority-register"),
    "closing": ("summary-close", "contact-close", "brand-close"),
    "cta": ("single-action", "action-proof", "next-step-strip"),
}

_RUNTIME_FAMILY_MAP = {
    "cover": "cover",
    "contents": "agenda",
    "section": "section",
    "executive-summary": "executive-summary",
    "abstract": "executive-summary",
    "big-number": "big-number",
    "kpi-towers": "big-number",
    "chart-story": "data-chart",
    "annotated-chart": "data-chart",
    "small-multiples": "data-chart",
    "distribution": "data-chart",
    "comparison": "comparison",
    "before-after": "comparison",
    "process": "process",
    "method": "process",
    "demo-flow": "process",
    "timeline": "timeline",
    "roadmap": "roadmap",
    "matrix": "matrix",
    "quadrant": "quadrant",
    "funnel": "funnel",
    "table": "table",
    "product-hero": "text-media",
    "feature-bento": "cards",
    "case-study": "cards",
    "social-proof": "cards",
    "evidence-cards": "cards",
    "card-grid": "cards",
    "team": "cards",
    "team-orbit": "cards",
    "org-map": "process",
    "risk-actions": "risk-recommendation",
    "recommendation": "risk-recommendation",
    "takeaways": "cards",
    "closing": "cta",
    "cta": "cta",
}


def _available_family(pack: DesignPack, candidates: Iterable[str]) -> str:
    allowed = set(pack.page_families)
    for candidate in candidates:
        if candidate in allowed:
            return candidate
    return pack.safe_fallback.family


def governed_runtime_family(family: str) -> str:
    """Map DesignPack vocabulary to a registered renderer page family."""

    return _RUNTIME_FAMILY_MAP.get(family, "structured-content")


def _family_for_slide(slide: NarrativeSlide, pack: DesignPack) -> tuple[str, str]:
    role = slide.role.casefold()
    if slide.structural and role not in {"cover", "closing"}:
        return _available_family(pack, ("section", "contents", "cover")), "STRUCTURAL_SLIDE"
    for tokens, candidates, rule in _ROLE_CANDIDATES:
        if role in tokens or any(token in role for token in tokens):
            return _available_family(pack, candidates), rule
    semantic = slide.semantic_kind.casefold()
    for token, candidates in _SEMANTIC_CANDIDATES.items():
        if token in semantic:
            return _available_family(pack, candidates), f"SEMANTIC_{token.upper()}"
    return pack.safe_fallback.family, "SAFE_FALLBACK"


def _variant_for(family: str, index: int, density: str) -> str:
    variants = _FAMILY_VARIANTS.get(
        family,
        ("hero-focus", "split-evidence", "modular-grid"),
    )
    density_offset = {"sparse": 0, "balanced": 1, "dense": 2}[density]
    return variants[(index + density_offset) % len(variants)]


def _components_for(family: str) -> tuple[str, ...]:
    if family in {"chart-story", "annotated-chart", "small-multiples", "distribution"}:
        return ("claim-title", "native-editable-chart", "chart-annotation", "source-note")
    if family in {"timeline", "roadmap", "process", "demo-flow"}:
        return ("claim-title", "native-editable-diagram", "phase-labels", "takeaway")
    if family in {"big-number", "kpi-towers"}:
        return ("claim-title", "hero-metric", "comparison-context", "source-note")
    if family in {"matrix", "quadrant"}:
        return ("claim-title", "native-editable-matrix", "axis-labels", "takeaway")
    if family in {"cover", "section", "closing", "cta", "product-hero"}:
        return ("claim-title", "visual-anchor", "brand-mark", "context-line")
    return ("claim-title", "content-modules", "visual-anchor", "takeaway")


def _asset_kind(family: str) -> tuple[str, bool, str]:
    if family in {"chart-story", "annotated-chart", "small-multiples", "distribution", "big-number"}:
        return "chart", True, "native-editable-chart"
    if family in {"timeline", "roadmap", "process", "matrix", "quadrant", "org-map", "demo-flow"}:
        return "diagram", True, "native-editable-diagram"
    if family in {
        "cover",
        "section",
        "case-study",
        "social-proof",
        "product-hero",
        "closing",
        "cta",
    }:
        return "photo", False, "branded-native-geometry"
    if family in {"feature-bento", "card-grid", "evidence-cards"}:
        return "icon", False, "consistent-native-icon-set"
    return "texture", False, "subtle-brand-field"


def compile_visual_plan(
    narrative: NarrativePlan,
    *,
    scenario_id: str | None = None,
    design_pack: DesignPack | None = None,
    preferred_pack_id: str | None = None,
) -> tuple[VisualPlan, AssetPlan]:
    pack = design_pack or select_design_pack(
        scenario_id or narrative.archetype_id,
        preferred_pack_id=preferred_pack_id,
    )
    slides: list[VisualSlide] = []
    assets: list[PlannedAsset] = []
    recent: list[str] = []
    for index, slide in enumerate(narrative.slides):
        recipe = select_composition_recipe(
            scenario_id or narrative.archetype_id,
            design_pack_id=pack.id,
            role=slide.role,
            semantic_kind=slide.semantic_kind,
        )
        structural_section = slide.structural and slide.role.casefold() in {
            "section",
            "agenda",
            "contents",
        }
        density = (
            recipe.density
            if recipe is not None and not structural_section
            else pack.pacing.density_pattern[index % len(pack.pacing.density_pattern)]
        )
        if structural_section:
            family, rule = _family_for_slide(slide, pack)
            recipe = None
        elif recipe is not None:
            family = _available_family(pack, (recipe.family,))
            rule = f"GRAMMAR_{recipe.id}"
        else:
            family, rule = _family_for_slide(slide, pack)
        if recipe is None and (
            len(recent) >= pack.pacing.max_same_family_run
            and all(item == family for item in recent[-pack.pacing.max_same_family_run :])
        ):
            alternative = _available_family(
                pack,
                ("evidence-cards", "card-grid", "comparison", "executive-summary"),
            )
            if alternative != family:
                family = alternative
                rule = f"{rule}+PACING_VARIATION"
        recent.append(family)
        critical = slide.importance in {"high", "critical"}
        hero_due = index > 0 and index % pack.pacing.hero_interval == 0
        emphasis = (
            recipe.emphasis
            if recipe is not None
            else "hero"
            if critical or hero_due
            else "quiet"
            if slide.structural
            else "standard"
        )
        asset_refs: tuple[str, ...] = ()
        asset_required = family in pack.asset_strategy.required_for
        asset_supported = family in {
            "cover",
            "section",
            "case-study",
            "social-proof",
            "product-hero",
            "feature-bento",
            "card-grid",
            "evidence-cards",
            "chart-story",
            "annotated-chart",
            "small-multiples",
            "distribution",
            "big-number",
            "timeline",
            "roadmap",
            "process",
            "matrix",
            "quadrant",
            "org-map",
            "demo-flow",
            "closing",
            "cta",
        }
        if asset_required or asset_supported:
            asset_id = f"asset-{slide.id}"
            kind, editable, fallback = _asset_kind(family)
            assets.append(
                PlannedAsset(
                    id=asset_id,
                    slide_id=slide.id,
                    purpose=f"{family} visual anchor",
                    kind=kind,
                    priority=pack.asset_strategy.priority,
                    fallback=fallback,
                    editable=editable,
                )
            )
            asset_refs = (asset_id,)
        slides.append(
            VisualSlide(
                slide_id=slide.id,
                role=slide.role,
                family=family,
                variant=(
                    recipe.variant
                    if recipe is not None
                    else _variant_for(family, index, density)
                ),
                emphasis=emphasis,
                density=density,
                components=(
                    recipe.components
                    if recipe is not None
                    else _components_for(family)
                ),
                asset_refs=asset_refs,
                decision_rules=(
                    rule,
                    f"DENSITY_PATTERN_{density.upper()}",
                    f"PACK_{pack.id}",
                    *(
                        (
                            f"CAPACITY_MAX_ITEMS_{recipe.max_items}",
                            f"CAPACITY_MAX_BODY_CHARS_{recipe.max_body_chars}",
                        )
                        if recipe is not None
                        else ()
                    ),
                ),
                recipe_id=recipe.id if recipe is not None else None,
            )
        )
    return (
        VisualPlan(
            design_pack_id=pack.id,
            template_pack_id=pack.template_pack,
            theme_id=pack.id,
            slides=tuple(slides),
        ),
        AssetPlan(design_pack_id=pack.id, assets=tuple(assets)),
    )


__all__ = [
    "AssetPlan",
    "PlannedAsset",
    "VisualPlan",
    "VisualSlide",
    "compile_visual_plan",
    "governed_runtime_family",
]
