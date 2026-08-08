"""Fail-closed bridge from certified selection to observable materialization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .render_plan import RenderPlan
from .template_intelligence import (
    RegistryV3,
    SlideBlueprint,
    TemplateSelectionPlan,
    load_registry_v3,
)
from .template_pack import TemplateAdaptationReport, adapt_template_pack


class SelectionMaterializationError(ValueError):
    """A selected candidate cannot be proven by its declared materializer."""


@dataclass(frozen=True)
class CandidateMaterializationEvidence:
    slide_id: str
    candidate_id: str
    spine_id: str
    source_mode: str
    materializer: str
    expected_variant_id: str | None
    expected_physical_slide: int | None
    observed_layout_id: str | None
    observed_output_slide: int | None
    source_sha256: str | None
    output_sha256: str | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_id": self.slide_id,
            "candidate_id": self.candidate_id,
            "spine_id": self.spine_id,
            "source_mode": self.source_mode,
            "materializer": self.materializer,
            "expected_variant_id": self.expected_variant_id,
            "expected_physical_slide": self.expected_physical_slide,
            "observed_layout_id": self.observed_layout_id,
            "observed_output_slide": self.observed_output_slide,
            "source_sha256": self.source_sha256,
            "output_sha256": self.output_sha256,
            "status": self.status,
        }


@dataclass(frozen=True)
class CandidateMaterializationReport:
    schema_version: str
    selection_brief_id: str
    spine_id: str
    materializer: str
    status: str
    evidence: tuple[CandidateMaterializationEvidence, ...]
    adaptation_report: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "selection_brief_id": self.selection_brief_id,
            "spine_id": self.spine_id,
            "materializer": self.materializer,
            "status": self.status,
            "evidence": [item.to_dict() for item in self.evidence],
            "adaptation_report": (
                dict(self.adaptation_report)
                if self.adaptation_report is not None
                else None
            ),
        }


def _uniform_context(
    plan: TemplateSelectionPlan,
    blueprints: Sequence[SlideBlueprint],
    registry: RegistryV3,
) -> tuple[str, str]:
    if len(blueprints) != len(plan.selections):
        raise SelectionMaterializationError(
            "MATERIALIZER_EVIDENCE_INCOMPLETE: blueprint cardinality differs"
        )
    selection_ids = [item.slide_id for item in plan.selections]
    blueprint_ids = [item.slide_id for item in blueprints]
    if selection_ids != blueprint_ids or len(selection_ids) != len(set(selection_ids)):
        raise SelectionMaterializationError(
            "MATERIALIZER_EVIDENCE_INCOMPLETE: slide identities differ"
        )
    if any(item.spine_id != plan.spine_id for item in blueprints):
        raise SelectionMaterializationError(
            "MATERIALIZER_MIXED_PLAN: blueprint spines differ"
        )
    materials = {item.materializer for item in blueprints}
    if len(materials) != 1:
        raise SelectionMaterializationError(
            "MATERIALIZER_MIXED_PLAN: more than one materializer"
        )
    spine = registry.spines.get(plan.spine_id)
    if spine is None:
        raise SelectionMaterializationError(
            f"MATERIALIZER_SPINE_UNKNOWN: {plan.spine_id}"
        )
    materializer = next(iter(materials), "")
    if not materializer or materializer != spine.materializer:
        raise SelectionMaterializationError(
            "MATERIALIZER_KIND_MISMATCH: blueprint and spine differ"
        )
    for blueprint, selection in zip(blueprints, plan.selections):
        candidate = registry.candidates.get(blueprint.candidate_id)
        if (
            candidate is None
            or candidate.certification != "certified"
            or selection.candidate_id != blueprint.candidate_id
            or candidate.materializer != materializer
            or candidate.source_mode != spine.source_mode
            or spine.deck_family_id not in candidate.deck_family_ids
            or spine.style_cluster_id not in candidate.style_cluster_ids
            or candidate.family != blueprint.family
            or blueprint.token_profile_id != spine.art_direction_id
            or selection.fact_refs != blueprint.fact_refs
            or selection.asset_refs != blueprint.asset_refs
        ):
            raise SelectionMaterializationError(
                f"MATERIALIZER_CANDIDATE_INVALID: {blueprint.candidate_id}"
            )
    return spine.source_mode, materializer


def registered_layout_bindings(
    plan: TemplateSelectionPlan,
    blueprints: Sequence[SlideBlueprint],
    registry: RegistryV3 | None = None,
) -> dict[str, str]:
    """Return exact registered layout bindings or fail before compilation."""

    available = registry or load_registry_v3()
    _, materializer = _uniform_context(plan, blueprints, available)
    if materializer != "registered_native_renderer":
        raise SelectionMaterializationError(
            "MATERIALIZER_KIND_MISMATCH: native binding requires registered renderer"
        )
    bindings: dict[str, str] = {}
    for item in blueprints:
        candidate = available.candidates[item.candidate_id]
        if (
            item.base_variant_id is None
            or item.base_variant_id != candidate.base_variant_id
        ):
            raise SelectionMaterializationError(
                f"MATERIALIZER_VARIANT_UNKNOWN: {item.candidate_id}"
            )
        bindings[item.slide_id] = item.base_variant_id
    return bindings


def planned_materialization_report(
    plan: TemplateSelectionPlan,
    blueprints: Sequence[SlideBlueprint],
    registry: RegistryV3 | None = None,
) -> CandidateMaterializationReport:
    available = registry or load_registry_v3()
    source_mode, materializer = _uniform_context(plan, blueprints, available)
    spine = available.spines[plan.spine_id]
    return CandidateMaterializationReport(
        "1.0",
        plan.brief_id,
        plan.spine_id,
        materializer,
        "planned",
        tuple(
            CandidateMaterializationEvidence(
                item.slide_id,
                item.candidate_id,
                item.spine_id,
                source_mode,
                item.materializer,
                item.base_variant_id,
                item.physical_slide,
                None,
                None,
                spine.pack.source_sha256,
                None,
                "planned",
            )
            for item in blueprints
        ),
    )


def verify_registered_materialization(
    plan: TemplateSelectionPlan,
    blueprints: Sequence[SlideBlueprint],
    render_plan: RenderPlan,
    registry: RegistryV3 | None = None,
) -> CandidateMaterializationReport:
    """Promote a native plan only when every observed layout is exact."""

    available = registry or load_registry_v3()
    bindings = registered_layout_bindings(plan, blueprints, available)
    observed = {slide.source_id: slide for slide in render_plan.slides}
    if set(observed) != set(bindings) or len(render_plan.slides) != len(bindings):
        raise SelectionMaterializationError(
            "MATERIALIZER_EVIDENCE_INCOMPLETE: rendered slide identities differ"
        )
    evidence: list[CandidateMaterializationEvidence] = []
    spine = available.spines[plan.spine_id]
    for index, item in enumerate(blueprints, start=1):
        rendered = observed[item.slide_id]
        expected = bindings[item.slide_id]
        if rendered.layout_id != expected:
            raise SelectionMaterializationError(
                "MATERIALIZER_VARIANT_MISMATCH: "
                f"{item.slide_id} expected {expected}, observed {rendered.layout_id}"
            )
        evidence.append(
            CandidateMaterializationEvidence(
                item.slide_id,
                item.candidate_id,
                item.spine_id,
                spine.source_mode,
                item.materializer,
                expected,
                None,
                rendered.layout_id,
                index,
                spine.pack.source_sha256,
                None,
                "pass",
            )
        )
    return CandidateMaterializationReport(
        "1.0", plan.brief_id, plan.spine_id,
        "registered_native_renderer", "pass", tuple(evidence)
    )


def materialize_physical_selection(
    plan: TemplateSelectionPlan,
    blueprints: Sequence[SlideBlueprint],
    bindings: Mapping[str, str],
    output_path: str | Path,
    registry: RegistryV3 | None = None,
) -> tuple[CandidateMaterializationReport, TemplateAdaptationReport]:
    """Execute and prove one uniform physical TemplatePack selection."""

    available = registry or load_registry_v3()
    source_mode, materializer = _uniform_context(plan, blueprints, available)
    if source_mode != "physical_ooxml" or materializer != "template_pack_v1_adapter":
        raise SelectionMaterializationError(
            "MATERIALIZER_KIND_MISMATCH: physical route requires TemplatePack"
        )
    spine = available.spines[plan.spine_id]
    for item in blueprints:
        candidate = available.candidates[item.candidate_id]
        if (
            item.physical_slide is None
            or item.physical_slide != candidate.physical_slide
            or not 1 <= item.physical_slide <= spine.pack.v1_pack.slide_count
        ):
            raise SelectionMaterializationError(
                f"MATERIALIZER_PHYSICAL_SLIDE_UNKNOWN: {item.candidate_id}"
            )
    try:
        adaptation = adapt_template_pack(
            spine.pack.v1_pack, bindings, output_path
        )
    except Exception as exc:
        raise SelectionMaterializationError(
            f"MATERIALIZER_ADAPTATION_FAILED: {exc}"
        ) from exc
    if (
        adaptation.source_sha256 != spine.pack.source_sha256
        or not adaptation.source_integrity_preserved
        or adaptation.slide_count != spine.pack.v1_pack.slide_count
    ):
        raise SelectionMaterializationError(
            "MATERIALIZER_SOURCE_DRIFT: physical source proof differs"
        )
    evidence = tuple(
        CandidateMaterializationEvidence(
            item.slide_id,
            item.candidate_id,
            item.spine_id,
            source_mode,
            materializer,
            None,
            item.physical_slide,
            None,
            item.physical_slide,
            adaptation.source_sha256,
            adaptation.output_sha256,
            "pass",
        )
        for item in blueprints
    )
    return (
        CandidateMaterializationReport(
            "1.0",
            plan.brief_id,
            plan.spine_id,
            materializer,
            "pass",
            evidence,
            adaptation.to_dict(),
        ),
        adaptation,
    )


__all__ = [
    "CandidateMaterializationEvidence",
    "CandidateMaterializationReport",
    "SelectionMaterializationError",
    "materialize_physical_selection",
    "planned_materialization_report",
    "registered_layout_bindings",
    "verify_registered_materialization",
]
