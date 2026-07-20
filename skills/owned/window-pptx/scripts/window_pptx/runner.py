"""Governed validate/compile/render/hook/transaction orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .deck_plan import DeckPlan
from .layouts import SlideSize
from .errors import OutputPolicyError
from .models import CandidateResult, OutputPolicy
from .output_policy import validate_output_policy
from .renderer import PowerPointRenderer, RenderReport
from .render_plan import (
    AssetBinding,
    RenderPlan,
    compile_render_plan,
    validate_render_plan,
)
from .themes import BrandOverrides
from .transaction import save_candidate


Inspector = Callable[[RenderPlan, RenderReport], Any]
Repairer = Callable[[RenderPlan, Any], Any]
Saver = Callable[..., CandidateResult]


@dataclass(frozen=True)
class PipelineResult:
    compiled_deck: dict[str, Any]
    render_plan: RenderPlan
    render_report: RenderReport | None
    inspection: Any
    repair: Any
    candidate_result: CandidateResult | None
    stages: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        candidate = self.candidate_result
        return {
            "compiled_deck": self.compiled_deck,
            "render_plan": self.render_plan.to_dict(),
            "render_report": (
                self.render_report.to_dict() if self.render_report else None
            ),
            "inspection": self.inspection,
            "repair": self.repair,
            "candidate_result": (
                {
                    "output_path": str(candidate.output_path),
                    "promoted": candidate.promoted,
                    "candidate_path": (
                        str(candidate.candidate_path)
                        if candidate.candidate_path is not None
                        else None
                    ),
                    "source_hash_before": candidate.source_hash_before,
                    "source_hash_after": candidate.source_hash_after,
                    "validation_steps": list(candidate.validation_steps),
                    "cleanup_errors": list(candidate.cleanup_errors),
                }
                if candidate is not None
                else None
            ),
            "stages": list(self.stages),
        }


def _default_inspector(plan: RenderPlan, report: RenderReport) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "rendered_slides": report.slide_count,
        "native_editable_objects": report.native_editable_count,
        "plan_findings": [finding.to_dict() for finding in plan.findings],
    }


def _default_repairer(plan: RenderPlan, inspection: Any) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "changed": False,
        "reason": "PHASE_27_REPAIR_NOT_CONFIGURED",
    }


def run_render_pipeline(
    payload: DeckPlan | Mapping[str, Any],
    *,
    presentation: Any,
    app: Any,
    output_policy: OutputPolicy,
    slide_size: SlideSize,
    installed_fonts: set[str],
    theme_id: str | None = None,
    brand: BrandOverrides | None = None,
    asset_bindings: Mapping[str, AssetBinding] | None = None,
    renderer: PowerPointRenderer | None = None,
    inspector: Inspector | None = None,
    repairer: Repairer | None = None,
    saver: Saver = save_candidate,
    export_pdf: bool = False,
) -> PipelineResult:
    """Run the single governed renderer lifecycle without bypassing dry-run."""

    validate_output_policy(output_policy)
    if (
        output_policy.source_path is not None
        and output_policy.output_path is not None
        and output_policy.source_path.resolve(strict=False)
        == output_policy.output_path.resolve(strict=False)
    ):
        raise OutputPolicyError(
            "The renderer cannot use a same-path source/output transaction."
        )
    compiled, plan = compile_render_plan(
        payload,
        slide_size=slide_size,
        installed_fonts=installed_fonts,
        theme_id=theme_id,
        brand=brand,
        asset_bindings=asset_bindings,
    )
    return execute_render_plan(
        compiled,
        plan,
        presentation=presentation,
        app=app,
        output_policy=output_policy,
        renderer=renderer,
        inspector=inspector,
        repairer=repairer,
        saver=saver,
        export_pdf=export_pdf,
    )


def execute_render_plan(
    compiled_deck: Mapping[str, Any],
    render_plan: RenderPlan,
    *,
    presentation: Any,
    app: Any,
    output_policy: OutputPolicy,
    renderer: PowerPointRenderer | None = None,
    inspector: Inspector | None = None,
    repairer: Repairer | None = None,
    saver: Saver = save_candidate,
    export_pdf: bool = False,
) -> PipelineResult:
    """Execute a preflighted plan without compiling model input a second time."""

    validate_output_policy(output_policy)
    if (
        output_policy.source_path is not None
        and output_policy.output_path is not None
        and output_policy.source_path.resolve(strict=False)
        == output_policy.output_path.resolve(strict=False)
    ):
        raise OutputPolicyError(
            "The renderer cannot use a same-path source/output transaction."
        )
    validate_render_plan(render_plan)
    if not isinstance(compiled_deck, Mapping):
        raise ValueError("compiled deck must be a mapping")
    compiled = dict(compiled_deck)
    plan = render_plan
    stages = ["validate-compile", "build-render-plan"]

    if output_policy.dry_run:
        stages.append("dry-run")
        return PipelineResult(
            compiled_deck=compiled,
            render_plan=plan,
            render_report=None,
            inspection=None,
            repair=None,
            candidate_result=None,
            stages=tuple(stages),
        )

    render_report = (renderer or PowerPointRenderer()).render(plan, presentation)
    stages.append("render")
    inspection = (inspector or _default_inspector)(plan, render_report)
    stages.append("inspect")
    repair = (repairer or _default_repairer)(plan, inspection)
    stages.append("repair")
    candidate_result = saver(
        presentation,
        app,
        output_policy,
        export_pdf=export_pdf,
    )
    stages.append("transactional-save")
    return PipelineResult(
        compiled_deck=compiled,
        render_plan=plan,
        render_report=render_report,
        inspection=inspection,
        repair=repair,
        candidate_result=candidate_result,
        stages=tuple(stages),
    )


__all__ = ["PipelineResult", "execute_render_plan", "run_render_pipeline"]
