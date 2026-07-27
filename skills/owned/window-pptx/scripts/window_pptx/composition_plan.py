"""Compile visual intent into a registered, fact-safe composition contract.

VisualPlan deliberately stays semantic.  CompositionPlan is the missing
compiler seam that turns those semantics into bounded layout, component,
asset, motif, and repair choices before exact geometry is resolved.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .design_packs import DesignPack
from .layouts import load_components, load_layout_registry
from .visual_plan import AssetPlan, VisualPlan, VisualSlide, governed_runtime_family
from .weak_model import NarrativePlan
from .consulting_choreography import CHOREOGRAPHY_SOURCE_SLIDES


class CompositionPlanError(ValueError):
    """Narrative, visual, asset, or registry contracts cannot be composed."""


@dataclass(frozen=True)
class SlotBinding:
    semantic_slot: str
    component_id: str
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_slot": self.semantic_slot,
            "component_id": self.component_id,
            "required": self.required,
        }


@dataclass(frozen=True)
class AssetIntentBinding:
    asset_id: str
    status: str
    fallback: str
    required: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "status": self.status,
            "fallback": self.fallback,
            "required": self.required,
        }


@dataclass(frozen=True)
class AnchorPlan:
    kind: str
    target_area_ratio: float
    fallback: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "target_area_ratio": self.target_area_ratio,
            "fallback": self.fallback,
        }


@dataclass(frozen=True)
class MotifInstance:
    motif_id: str
    variant: str
    region: str
    intensity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "motif_id": self.motif_id,
            "variant": self.variant,
            "region": self.region,
            "intensity": self.intensity,
        }


@dataclass(frozen=True)
class CompositionSlide:
    source_slide_ids: tuple[str, ...]
    slide_id: str
    fact_refs: tuple[str, ...]
    derived_fact_refs: tuple[str, ...]
    role: str
    composition_id: str
    variant_id: str
    layout_id: str
    background_mode: str
    emphasis: str
    density: str
    energy: str
    slot_bindings: tuple[SlotBinding, ...]
    anchor_plan: AnchorPlan
    motif: MotifInstance
    asset_bindings: tuple[AssetIntentBinding, ...]
    repair_variant_ids: tuple[str, ...]
    decision_trace: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_slide_ids": list(self.source_slide_ids),
            "slide_id": self.slide_id,
            "fact_refs": list(self.fact_refs),
            "derived_fact_refs": list(self.derived_fact_refs),
            "role": self.role,
            "composition_id": self.composition_id,
            "variant_id": self.variant_id,
            "layout_id": self.layout_id,
            "background_mode": self.background_mode,
            "emphasis": self.emphasis,
            "density": self.density,
            "energy": self.energy,
            "slot_bindings": [item.to_dict() for item in self.slot_bindings],
            "anchor_plan": self.anchor_plan.to_dict(),
            "motif": self.motif.to_dict(),
            "asset_bindings": [item.to_dict() for item in self.asset_bindings],
            "repair_variant_ids": list(self.repair_variant_ids),
            "decision_trace": list(self.decision_trace),
        }

    def to_compiler_dict(self) -> dict[str, Any]:
        """Return the governed fields consumed by DeckPlan and RenderPlan."""

        return self.to_dict()


@dataclass(frozen=True)
class CompositionPlan:
    design_pack_id: str
    theme_id: str
    fact_store_digest: str
    slides: tuple[CompositionSlide, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "design_pack_id": self.design_pack_id,
            "theme_id": self.theme_id,
            "fact_store_digest": self.fact_store_digest,
            "slides": [slide.to_dict() for slide in self.slides],
        }

    def by_slide(self) -> dict[str, dict[str, Any]]:
        return {
            slide.slide_id: slide.to_compiler_dict() for slide in self.slides
        }


_CONSULTING_LAYOUTS = {
    "proposal.cover": "cover.editorial",
    "proposal.executive-summary": "cards.compact-three",
    "proposal.problem": "comparison.split",
    "proposal.outcomes": "big-number.three-column",
    "proposal.approach": "process.focus",
    "proposal.workstreams": "matrix.grid",
    "proposal.timeline": "timeline.focus",
    "proposal.governance": "process.focus",
    "proposal.risks": "risk-recommendation.split",
    "proposal.next-step": "recommendation.columns",
    "proposal.close": "cta.top-band",
    "proposal.safe-evidence": "executive-summary.top-band",
}


def _stable_index(value: str, length: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % length


def _layout_id(slide: VisualSlide, role: str) -> str:
    registry = load_layout_registry()
    if role in {"section", "agenda"}:
        return "executive-summary.top-band"
    preferred = _CONSULTING_LAYOUTS.get(slide.recipe_id or "")
    if preferred is not None and preferred in registry.variants:
        return preferred
    family_id = governed_runtime_family(slide.family)
    family = registry.families.get(family_id)
    if family is None:
        family = registry.families["executive-summary"]
    return family.variant_ids[
        _stable_index(
            f"{slide.slide_id}|{slide.variant}|{slide.density}",
            len(family.variant_ids),
        )
    ]


def _layout_slot_bindings(layout_id: str) -> tuple[SlotBinding, ...]:
    """Bind CompositionPlan to the exact registered slots the renderer emits."""

    registry = load_layout_registry()
    variant = registry.variants[layout_id]
    overrides = dict(variant.component_overrides)
    return tuple(
        SlotBinding(
            semantic_slot=slot.id,
            component_id=overrides.get(slot.id, slot.component),
            required=True,
        )
        for slot in registry.recipes[variant.recipe_id]
    )


def _repair_variants(layout_id: str) -> tuple[str, ...]:
    registry = load_layout_registry()
    family_id = registry.variants[layout_id].family_id
    candidates = tuple(
        item for item in registry.families[family_id].variant_ids if item != layout_id
    )
    if candidates:
        return candidates[:2]
    return ("executive-summary.top-band",)


def compile_composition_plan(
    narrative: NarrativePlan,
    visual_plan: VisualPlan,
    asset_plan: AssetPlan,
    design_pack: DesignPack,
) -> CompositionPlan:
    """Compile one deterministic CompositionPlan without inventing facts."""

    narrative_ids = tuple(slide.id for slide in narrative.slides)
    visual_ids = tuple(slide.slide_id for slide in visual_plan.slides)
    if narrative_ids != visual_ids:
        raise CompositionPlanError(
            "NarrativePlan and VisualPlan slide ids must match in order"
        )
    if visual_plan.design_pack_id != design_pack.id:
        raise CompositionPlanError("VisualPlan DesignPack identity drifted")
    if asset_plan.design_pack_id != design_pack.id:
        raise CompositionPlanError("AssetPlan DesignPack identity drifted")

    registered_components = set(load_components())
    assets_by_slide: dict[str, list[Any]] = {}
    for asset in asset_plan.assets:
        if asset.slide_id not in narrative_ids:
            raise CompositionPlanError(
                f"AssetPlan references unknown slide id: {asset.slide_id}"
            )
        assets_by_slide.setdefault(asset.slide_id, []).append(asset)

    slides: list[CompositionSlide] = []
    for index, (narrative_slide, visual_slide) in enumerate(
        zip(narrative.slides, visual_plan.slides, strict=True)
    ):
        layout_id = _layout_id(visual_slide, narrative_slide.role)
        bindings = _layout_slot_bindings(layout_id)
        unknown = sorted(
            {
                binding.component_id
                for binding in bindings
                if binding.component_id not in registered_components
            }
        )
        if unknown:
            raise CompositionPlanError(
                "CompositionPlan contains unregistered components: "
                + ", ".join(unknown)
            )
        asset_bindings = tuple(
            AssetIntentBinding(
                asset_id=asset.id,
                status=(
                    "native-materialized"
                    if asset.status == "planned" and asset.fallback
                    else asset.status
                ),
                fallback=asset.fallback,
                required=visual_slide.family in design_pack.asset_strategy.required_for,
            )
            for asset in assets_by_slide.get(narrative_slide.id, ())
        )
        intensity = (
            "strong"
            if visual_slide.emphasis == "hero"
            else "quiet"
            if narrative_slide.structural
            else "standard"
        )
        background_mode = (
            "navy-stage"
            if visual_slide.emphasis == "hero"
            and narrative_slide.role in {"cover", "closing"}
            else "warm-ivory"
        )
        art_direction = design_pack.art_direction
        motif_variants = (
            art_direction.motif_variants
            if art_direction is not None
            else ("portal", "path", "node", "frame")
        )
        energy_pattern = (
            art_direction.energy_pattern
            if art_direction is not None
            else ("peak", "flow", "flow", "pause")
        )
        slides.append(
            CompositionSlide(
                source_slide_ids=CHOREOGRAPHY_SOURCE_SLIDES.get(
                    narrative_slide.id, (narrative_slide.id,)
                ),
                slide_id=narrative_slide.id,
                fact_refs=narrative_slide.fact_refs,
                derived_fact_refs=(
                    ("derived-cycle-reduction-50pct",)
                    if narrative_slide.id == "transformation-bridge"
                    else ()
                ),
                role=narrative_slide.role,
                composition_id=visual_slide.recipe_id
                or f"{design_pack.id}.{governed_runtime_family(visual_slide.family)}",
                variant_id=visual_slide.variant,
                layout_id=layout_id,
                background_mode=background_mode,
                emphasis=visual_slide.emphasis,
                density=visual_slide.density,
                energy=(
                    "peak"
                    if visual_slide.emphasis == "hero"
                    else "pause"
                    if narrative_slide.structural
                    else energy_pattern[index % len(energy_pattern)]
                ),
                slot_bindings=bindings,
                anchor_plan=AnchorPlan(
                    kind=(
                        "asset-or-native"
                        if asset_bindings
                        else "native-geometry"
                    ),
                    target_area_ratio=0.32 if intensity == "strong" else 0.20,
                    fallback="branded-native-geometry",
                ),
                motif=MotifInstance(
                    motif_id=(
                        art_direction.id
                        if art_direction is not None
                        else "knowledge-wayfinding"
                        if design_pack.id == "consulting-executive"
                        else "governed-accent-field"
                    ),
                    variant=motif_variants[index % len(motif_variants)],
                    region=("right", "bottom", "left", "top")[index % 4],
                    intensity=intensity,
                ),
                asset_bindings=asset_bindings,
                repair_variant_ids=_repair_variants(layout_id),
                decision_trace=(
                    *(visual_slide.decision_rules),
                    *(
                        "SEMANTIC_INTENT_" + semantic.upper().replace("-", "_")
                        for semantic in visual_slide.components
                    ),
                    f"LAYOUT_{layout_id}",
                    "FACT_REFS_PRESERVED",
                    "REGISTERED_COMPONENTS_ONLY",
                ),
            )
        )

    return CompositionPlan(
        design_pack_id=design_pack.id,
        theme_id=visual_plan.theme_id,
        fact_store_digest=narrative.fact_store_digest,
        slides=tuple(slides),
    )


__all__ = [
    "AnchorPlan",
    "AssetIntentBinding",
    "CompositionPlan",
    "CompositionPlanError",
    "CompositionSlide",
    "MotifInstance",
    "SlotBinding",
    "compile_composition_plan",
]
