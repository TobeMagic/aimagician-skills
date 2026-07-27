"""Governed validate/compile/render/hook/transaction orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .deck_plan import DeckPlan
from .layouts import SlideSize
from .errors import OutputPolicyError
from .models import CandidateResult, OutputPolicy
from .output_policy import validate_output_policy
from .quality import (
    QualityGateError,
    QualityReport,
    RepairLog,
    finalize_quality_report,
    inspect_quality,
    repair_quality,
    write_quality_artifacts,
)
from .preview_quality import inspect_preview_images
from .quality_v2 import (
    QualityFindingV2,
    QualityReportV2,
    QualityV2GateError,
    StageRepairPass,
    adapt_legacy_quality_report,
    adapt_render_findings,
    build_quality_report_v2,
    defect_vector,
    write_quality_report_v2,
)
from .renderer import PowerPointRenderer, RenderReport
from .render_plan import (
    AssetBinding,
    RenderPlan,
    compile_render_plan,
    validate_render_plan,
)
from .themes import BrandOverrides
from .transaction import TransactionError, save_candidate


Inspector = Callable[[RenderPlan, RenderReport], Any]
Repairer = Callable[[RenderPlan, Any], Any]
Saver = Callable[..., CandidateResult]
PreviewExporter = Callable[[Any], Mapping[str, Any]]


@dataclass(frozen=True)
class PipelineResult:
    compiled_deck: dict[str, Any]
    render_plan: RenderPlan
    render_report: RenderReport | None
    inspection: Any
    repair: Any
    candidate_result: CandidateResult | None
    stages: tuple[str, ...]
    post_render_repair_passes: tuple[StageRepairPass, ...]
    quality_report_v2: QualityReportV2 | None = None
    preview_export: Mapping[str, Any] | None = None
    quality_v2_artifacts: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        candidate = self.candidate_result
        return {
            "compiled_deck": self.compiled_deck,
            "render_plan": self.render_plan.to_dict(),
            "render_report": (
                self.render_report.to_dict() if self.render_report else None
            ),
            "inspection": (
                self.inspection.to_dict()
                if hasattr(self.inspection, "to_dict")
                else self.inspection
            ),
            "repair": (
                self.repair.to_dict()
                if hasattr(self.repair, "to_dict")
                else self.repair
            ),
            "quality_report_v2": (
                self.quality_report_v2.to_dict()
                if self.quality_report_v2 is not None
                else None
            ),
            "preview_export": (
                dict(self.preview_export)
                if self.preview_export is not None
                else None
            ),
            "quality_v2_artifacts": dict(self.quality_v2_artifacts),
            "post_render_repair_passes": [
                {
                    "stage": item.stage,
                    "before_vector": list(item.before_vector),
                    "after_vector": list(item.after_vector),
                    "accepted": item.accepted,
                    "rolled_back": item.rolled_back,
                    "failure_code": item.failure_code,
                }
                for item in self.post_render_repair_passes
            ],
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
    audit_dir: Path | None = None,
    quality_v2_findings: Iterable[QualityFindingV2] | None = None,
    preview_exporter: PreviewExporter | None = None,
    quality_v2_slide_ids: Iterable[str] | None = None,
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
        audit_dir=audit_dir,
        quality_v2_findings=quality_v2_findings,
        preview_exporter=preview_exporter,
        quality_v2_slide_ids=quality_v2_slide_ids,
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
    audit_dir: Path | None = None,
    max_repair_passes: int = 2,
    quality_v2_findings: Iterable[QualityFindingV2] | None = None,
    preview_exporter: PreviewExporter | None = None,
    quality_v2_slide_ids: Iterable[str] | None = None,
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
    v2_enabled = quality_v2_findings is not None
    if v2_enabled and audit_dir is None:
        raise ValueError("quality v2 production gating requires an audit directory")
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
            quality_report_v2=None,
            preview_export=None,
            quality_v2_artifacts={},
            candidate_result=None,
            stages=tuple(stages),
            post_render_repair_passes=(),
        )

    render_report = (renderer or PowerPointRenderer()).render(plan, presentation)
    stages.append("render")
    default_quality = inspector is None
    inspection = (
        inspect_quality(plan, render_report, presentation)
        if default_quality
        else inspector(plan, render_report)
    )
    initial_quality_report = (
        inspection if isinstance(inspection, QualityReport) else None
    )
    stages.append("inspect")
    if repairer is not None:
        repair = repairer(plan, inspection)
    elif default_quality:
        assert isinstance(inspection, QualityReport)
        repair = repair_quality(
            plan,
            render_report,
            presentation,
            inspection,
            max_passes=max_repair_passes,
        )
        inspection = repair.final_report
    else:
        repair = _default_repairer(plan, inspection)
    stages.append("repair")
    post_render_repair_passes: tuple[StageRepairPass, ...] = ()
    if (
        initial_quality_report is not None
        and isinstance(repair, RepairLog)
        and repair.passes
    ):
        before_v2 = build_quality_report_v2(
            list(adapt_legacy_quality_report(initial_quality_report)),
            transaction_status="post-render-before-repair",
        )
        after_v2 = build_quality_report_v2(
            list(adapt_legacy_quality_report(repair.final_report)),
            transaction_status="post-render-after-repair",
        )
        repair_pass = repair.passes[0]
        post_render_repair_passes = (
            StageRepairPass(
                "post-render",
                defect_vector(before_v2),
                defect_vector(after_v2),
                repair_pass.accepted,
                repair_pass.rolled_back,
                repair_pass.failure_code,
            ),
        )
    if (
        not v2_enabled
        and isinstance(inspection, QualityReport)
        and inspection.hard_gate_failures
    ):
        artifacts = (
            write_quality_artifacts(inspection, repair, audit_dir)
            if audit_dir is not None and isinstance(repair, RepairLog)
            else {}
        )
        raise QualityGateError(
            "candidate failed customer-delivery gates before save: "
            + ", ".join(inspection.hard_gate_failures),
            report=inspection,
            repair=repair if isinstance(repair, RepairLog) else None,
            artifacts=artifacts,
        )

    quality_report_v2: QualityReportV2 | None = None
    preview_export: Mapping[str, Any] | None = None
    quality_v2_artifacts: dict[str, str] = {}
    if v2_enabled:
        v2_findings = list(quality_v2_findings or ())
        v2_findings.extend(adapt_render_findings(plan.findings))
        if isinstance(inspection, QualityReport):
            v2_findings.extend(adapt_legacy_quality_report(inspection))

        slide_ids = tuple(
            quality_v2_slide_ids
            if quality_v2_slide_ids is not None
            else (slide.source_id for slide in plan.slides)
        )
        preview_files: tuple[str, ...] = ()
        if preview_exporter is not None:
            try:
                exported = preview_exporter(presentation)
                if not isinstance(exported, Mapping):
                    raise TypeError("preview exporter must return a mapping")
                preview_export = dict(exported)
                raw_files = preview_export.get("files", ())
                if isinstance(raw_files, (str, bytes)) or not isinstance(
                    raw_files, Iterable
                ):
                    raise TypeError("preview exporter files must be an iterable")
                preview_files = tuple(str(path) for path in raw_files)
            except Exception as exc:
                preview_export = {"files": [], "error": str(exc)}
                v2_findings.append(
                    QualityFindingV2(
                        namespace="preview",
                        code="PREVIEW_EXPORT_FAILED",
                        severity="hard-gate",
                        slide_id=None,
                        object_id=None,
                        message=f"PNG preview export failed: {exc}",
                        repairable=False,
                        source_stage="png-preview-export",
                    )
                )
        else:
            preview_export = {"files": []}
        stages.append("quality-v2-preview")
        v2_findings.extend(
            inspect_preview_images(
                preview_files,
                slide_ids=slide_ids,
                expected_slide_count=len(slide_ids),
            )
        )
        quality_report_v2 = build_quality_report_v2(
            v2_findings,
            transaction_status="pre-save",
        )
        assert audit_dir is not None
        quality_v2_artifacts["quality_report_v2"] = write_quality_report_v2(
            quality_report_v2,
            audit_dir,
        )
        stages.append("quality-v2-gate")
        if quality_report_v2.hard_gate_failures:
            if isinstance(inspection, QualityReport) and isinstance(repair, RepairLog):
                quality_v2_artifacts.update(
                    write_quality_artifacts(inspection, repair, audit_dir)
                )
            raise QualityV2GateError(
                "candidate failed cross-stage quality v2 gates before save: "
                + ", ".join(quality_report_v2.hard_gate_failures),
                quality_report_v2=quality_report_v2,
                legacy_report=(
                    inspection if isinstance(inspection, QualityReport) else None
                ),
                repair=repair if isinstance(repair, RepairLog) else None,
                artifacts=quality_v2_artifacts,
            )

    reopened_inspection: QualityReport | None = None

    def validate_reopened_candidate(candidate_presentation: Any) -> None:
        nonlocal reopened_inspection, quality_report_v2
        reopened_inspection = inspect_quality(
            plan,
            render_report,
            candidate_presentation,
        )
        if quality_report_v2 is not None:
            quality_report_v2 = build_quality_report_v2(
                [
                    *quality_report_v2.findings,
                    *adapt_legacy_quality_report(reopened_inspection),
                ],
                transaction_status="reopened-candidate-validated",
            )
            assert audit_dir is not None
            quality_v2_artifacts["quality_report_v2"] = write_quality_report_v2(
                quality_report_v2,
                audit_dir,
            )
        if reopened_inspection.hard_gate_failures:
            if audit_dir is not None and isinstance(repair, RepairLog):
                write_quality_artifacts(
                    reopened_inspection,
                    replace(repair, final_report=reopened_inspection),
                    audit_dir,
                )
            raise QualityGateError(
                "reopened candidate diverged from the governed render plan: "
                + ", ".join(reopened_inspection.hard_gate_failures),
                report=reopened_inspection,
                repair=repair if isinstance(repair, RepairLog) else None,
            )

    saver_kwargs: dict[str, Any] = {"export_pdf": export_pdf}
    if not (output_policy.dry_run or output_policy.no_output_deck):
        saver_kwargs["candidate_validator"] = validate_reopened_candidate
    try:
        candidate_result = saver(
            presentation,
            app,
            output_policy,
            **saver_kwargs,
        )
    except TransactionError as exc:
        if quality_report_v2 is not None:
            quality_report_v2 = build_quality_report_v2(
                [
                    *quality_report_v2.findings,
                    QualityFindingV2(
                        namespace="package",
                        code="TRANSACTION_FAILED",
                        severity="hard-gate",
                        slide_id=None,
                        object_id=None,
                        message=str(exc),
                        repairable=False,
                        source_stage="transaction",
                    ),
                ],
                transaction_status="transaction-failed",
            )
            assert audit_dir is not None
            quality_v2_artifacts["quality_report_v2"] = write_quality_report_v2(
                quality_report_v2,
                audit_dir,
            )
        raise
    if (
        not (output_policy.dry_run or output_policy.no_output_deck)
        and reopened_inspection is None
        and "reopened-content-validation" in candidate_result.validation_steps
    ):
        # A custom transaction adapter cannot self-attest that it invoked the
        # governed semantic validator.  Retain only evidence observed by this
        # orchestration layer so finalization fails closed.
        candidate_result = replace(
            candidate_result,
            validation_steps=tuple(
                step
                for step in candidate_result.validation_steps
                if step != "reopened-content-validation"
            ),
        )
    stages.append("transactional-save")
    if reopened_inspection is not None:
        inspection = reopened_inspection
        stages.append("reopened-content-validation")
    if isinstance(inspection, QualityReport):
        inspection = finalize_quality_report(
            inspection,
            candidate_result,
            output_policy,
            export_pdf=export_pdf,
        )
        if isinstance(repair, RepairLog):
            repair = replace(repair, final_report=inspection)
        if quality_report_v2 is not None:
            quality_report_v2 = build_quality_report_v2(
                [
                    *quality_report_v2.findings,
                    *adapt_legacy_quality_report(inspection),
                ],
                transaction_status=(
                    "transaction-promoted"
                    if candidate_result.promoted
                    else "transaction-skipped"
                ),
            )
            assert audit_dir is not None
            quality_v2_artifacts["quality_report_v2"] = write_quality_report_v2(
                quality_report_v2,
                audit_dir,
            )
        if inspection.hard_gate_failures:
            artifacts = (
                write_quality_artifacts(inspection, repair, audit_dir)
                if audit_dir is not None and isinstance(repair, RepairLog)
                else {}
            )
            raise QualityGateError(
                "candidate failed customer-delivery gates after transaction: "
                + ", ".join(inspection.hard_gate_failures),
                report=inspection,
                repair=repair if isinstance(repair, RepairLog) else None,
                candidate_result=candidate_result,
                artifacts=artifacts,
            )
    return PipelineResult(
        compiled_deck=compiled,
        render_plan=plan,
        render_report=render_report,
        inspection=inspection,
        repair=repair,
        quality_report_v2=quality_report_v2,
        preview_export=preview_export,
        quality_v2_artifacts=quality_v2_artifacts,
        candidate_result=candidate_result,
        stages=tuple(stages),
        post_render_repair_passes=post_render_repair_passes,
    )


__all__ = ["PipelineResult", "execute_render_plan", "run_render_pipeline"]
