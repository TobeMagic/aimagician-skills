"""Portable governed PPTX generation and cross-engine verification pipeline."""

from __future__ import annotations

import json
import os
import shutil
import struct
import tempfile
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .backends import BackendSelection, negotiate_backend
from .libreoffice import (
    LibreOfficeVerificationError,
    LibreOfficeVerificationResult,
    LibreOfficeVerifier,
    inspect_pdf_geometry,
)
from .models import CandidateResult, OutputPolicy
from .ooxml import (
    OoxmlSemanticReport,
    inspect_rendered_pptx,
    normalize_pptx_package,
    write_ooxml_report,
)
from .output_policy import validate_output_policy
from .portable_renderer import BackendRenderResult, PptxGenJSRenderer
from .preview_quality import inspect_preview_images, inspect_render_plan_delivery
from .quality_v2 import (
    QualityFindingV2,
    QualityReportV2,
    QualityV2GateError,
    adapt_render_findings,
    build_quality_report_v2,
    write_quality_report_v2,
)
from .reference_quality import assess_generated_visual_quality
from .render_plan import RenderPlan, validate_render_plan
from .transaction import TransactionError, candidate_path_for, sha256_file


@dataclass(frozen=True)
class VerificationResult:
    level: str
    ooxml: OoxmlSemanticReport
    libreoffice: LibreOfficeVerificationResult
    quality: QualityReportV2
    powerpoint: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "ooxml": self.ooxml.to_dict(),
            "libreoffice": self.libreoffice.to_dict(),
            "quality": self.quality.to_dict(),
            "powerpoint": dict(self.powerpoint) if self.powerpoint else None,
        }


@dataclass(frozen=True)
class PortablePipelineResult:
    compiled_deck: Mapping[str, Any]
    render_plan: RenderPlan
    backend: BackendSelection
    render_report: BackendRenderResult | None
    verification: VerificationResult | None
    candidate_result: CandidateResult | None
    stages: tuple[str, ...]
    artifacts: Mapping[str, str] = field(default_factory=dict)
    artifact_sha256: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        candidate = self.candidate_result
        return {
            "compiled_deck": dict(self.compiled_deck),
            "render_plan": self.render_plan.to_dict(),
            "backend": self.backend.to_dict(),
            "render_report": (
                self.render_report.to_dict() if self.render_report is not None else None
            ),
            "verification": (
                self.verification.to_dict() if self.verification is not None else None
            ),
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
            "artifacts": dict(self.artifacts),
            "artifact_sha256": dict(self.artifact_sha256),
        }


def _remove_artifact(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _promote_bundle(
    pairs: Iterable[tuple[Path, Path]],
) -> tuple[str, ...]:
    """Promote files/directories with best-effort rollback of every target.

    Each source must be staged on the same filesystem as its target.  Existing
    targets are moved to unique sibling backups before any new target is
    installed.  A failure restores all backups and raises TransactionError.
    """

    items = tuple(pairs)
    backups: dict[Path, Path] = {}
    installed: list[Path] = []
    cleanup_errors: list[str] = []
    try:
        for source, target in items:
            if not source.exists():
                raise OSError(f"promotion source is missing: {source}")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() or target.is_symlink():
                backup = target.with_name(
                    f".{target.name}.pptx-studio-backup-{uuid.uuid4().hex}"
                )
                os.replace(target, backup)
                backups[target] = backup
        for source, target in items:
            os.replace(source, target)
            installed.append(target)
    except Exception as exc:
        for target in reversed(installed):
            try:
                _remove_artifact(target)
            except Exception as cleanup_exc:
                cleanup_errors.append(
                    f"could not remove partially promoted {target}: {cleanup_exc}"
                )
        for target, backup in reversed(tuple(backups.items())):
            if not backup.exists() and not backup.is_symlink():
                continue
            try:
                os.replace(backup, target)
            except Exception as restore_exc:
                cleanup_errors.append(
                    f"could not restore {target} from {backup}: {restore_exc}"
                )
        suffix = (
            "; rollback errors: " + " | ".join(cleanup_errors)
            if cleanup_errors
            else ""
        )
        raise TransactionError(
            f"portable bundle promotion failed: {exc}{suffix}",
            cleanup_errors=tuple(cleanup_errors),
        ) from exc
    for backup in backups.values():
        try:
            _remove_artifact(backup)
        except Exception as exc:
            cleanup_errors.append(f"could not remove promotion backup {backup}: {exc}")
    return tuple(cleanup_errors)


_POWERPOINT_CERTIFICATION_FIELDS = {
    "powerpoint_version",
    "pdf_path",
    "png_paths",
    "candidate_hash_before",
    "candidate_hash_after",
    "owned_pid",
}


def _certification_artifact_path(value: object, root: Path, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise TransactionError(f"PowerPoint certification {field} must be a path")
    path = Path(value).resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    if path.parent != resolved_root or not path.is_file():
        raise TransactionError(
            f"PowerPoint certification {field} is missing or outside its staging directory"
        )
    return path


def _validate_powerpoint_certification_result(
    payload: Mapping[str, Any],
    *,
    expected_sha256: str,
    artifact_dir: Path,
    expected_slide_count: int,
    slide_size: Any,
) -> dict[str, Any]:
    """Fail closed unless certification returns complete, confined real proof."""

    raw = dict(payload)
    if set(raw) != _POWERPOINT_CERTIFICATION_FIELDS:
        missing = sorted(_POWERPOINT_CERTIFICATION_FIELDS - set(raw))
        extra = sorted(set(raw) - _POWERPOINT_CERTIFICATION_FIELDS)
        raise TransactionError(
            "PowerPoint certification result fields are incomplete or unexpected: "
            f"missing={missing}, extra={extra}"
        )
    version = raw["powerpoint_version"]
    if (
        not isinstance(version, str)
        or not version.strip()
        or version.casefold() == "unknown"
    ):
        raise TransactionError("PowerPoint certification version is invalid")
    owned_pid = raw["owned_pid"]
    if isinstance(owned_pid, bool) or not isinstance(owned_pid, int) or owned_pid <= 0:
        raise TransactionError("PowerPoint certification owned_pid is invalid")
    for field in ("candidate_hash_before", "candidate_hash_after"):
        if raw[field] != expected_sha256:
            raise TransactionError(
                f"PowerPoint certification reported a mismatched {field}"
            )
    pdf_path = _certification_artifact_path(
        raw["pdf_path"], artifact_dir, "pdf_path"
    )
    png_values = raw["png_paths"]
    if (
        not isinstance(png_values, list)
        or len(png_values) != expected_slide_count
        or not all(isinstance(value, str) for value in png_values)
    ):
        raise TransactionError(
            "PowerPoint certification PNG count does not match the RenderPlan"
        )
    png_paths = tuple(
        _certification_artifact_path(value, artifact_dir, f"png_paths[{index}]")
        for index, value in enumerate(png_values)
    )
    if len(set(png_paths)) != len(png_paths):
        raise TransactionError("PowerPoint certification PNG paths are duplicated")
    try:
        inspect_pdf_geometry(
            pdf_path,
            expected_slide_count=expected_slide_count,
            slide_size=slide_size,
        )
    except LibreOfficeVerificationError as exc:
        raise TransactionError(
            f"PowerPoint certification PDF evidence is invalid: {exc}"
        ) from exc
    expected_ratio = slide_size.width / slide_size.height
    for png_path in png_paths:
        data = png_path.read_bytes()
        if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 24:
            raise TransactionError(
                f"PowerPoint certification PNG evidence is unreadable: {png_path.name}"
            )
        width, height = struct.unpack(">II", data[16:24])
        if width < 100 or height < 100 or abs(width / height - expected_ratio) > 0.02:
            raise TransactionError(
                f"PowerPoint certification PNG geometry is invalid: {png_path.name}"
            )
    raw["pdf_path"] = str(pdf_path)
    raw["png_paths"] = [str(path) for path in png_paths]
    return raw


def execute_portable_render_plan(
    compiled_deck: Mapping[str, Any],
    render_plan: RenderPlan,
    *,
    output_policy: OutputPolicy,
    audit_dir: Path,
    requested_backend: str = "auto",
    verification_level: str = "portable",
    renderer: PptxGenJSRenderer | None = None,
    verifier: LibreOfficeVerifier | None = None,
    export_pdf: bool = False,
    quality_v2_findings: Iterable[QualityFindingV2] = (),
    powerpoint_certifier: Callable[[Path, Path], Mapping[str, Any]] | None = None,
) -> PortablePipelineResult:
    """Generate, prove, and atomically promote one portable PPTX candidate."""

    validate_output_policy(output_policy)
    validate_render_plan(render_plan)
    if verification_level not in {"portable", "powerpoint"}:
        raise ValueError(f"unknown verification level: {verification_level}")
    selection = negotiate_backend(
        requested_backend,
        render_plan,
        output_path=output_policy.output_path,
        require_physical_template=output_policy.source_path is not None,
    )
    if selection.backend_id != "pptxgenjs":
        raise ValueError("portable runner only accepts the pptxgenjs backend")
    if output_policy.output_path is not None and output_policy.output_path.suffix.casefold() != ".pptx":
        raise ValueError("portable backend only supports .pptx output")
    stages = ["validate-render-plan", "negotiate-backend"]
    if output_policy.dry_run:
        stages.append("dry-run")
        return PortablePipelineResult(
            dict(compiled_deck),
            render_plan,
            selection,
            None,
            None,
            None,
            tuple(stages),
        )
    if output_policy.output_path is None:
        raise ValueError("portable rendering requires an output path")

    output = output_policy.output_path
    output.parent.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_staging = Path(
        tempfile.mkdtemp(prefix=".portable-run-", dir=audit_dir)
    )
    proof_dir = audit_staging / "portable-proof"
    final_proof_dir = audit_dir / "portable-proof"
    source = output_policy.source_path
    source_hash_before = sha256_file(source) if source is not None and source.exists() else None
    source_hash_after = source_hash_before
    candidate = candidate_path_for(output)
    pdf_candidate = candidate_path_for(output.with_suffix(".pdf")) if export_pdf else None
    artifacts: dict[str, str] = {}

    try:
        render_report = (renderer or PptxGenJSRenderer()).render(render_plan, candidate)
        stages.append("backend-render")
        normalize_pptx_package(candidate)
        stages.extend(("deterministic-ooxml", "ooxml-package"))
        semantic_report = inspect_rendered_pptx(candidate, render_plan)
        staged_ooxml_report = Path(write_ooxml_report(
            semantic_report,
            audit_staging / "ooxml-report.json",
        ))
        artifacts["ooxml_report"] = str(audit_dir / "ooxml-report.json")
        stages.append("ooxml-semantic")
        _, generated_visual_findings = assess_generated_visual_quality(candidate)
        stages.append("generated-visual-floor")
        proof = (verifier or LibreOfficeVerifier()).verify(
            candidate,
            artifact_dir=proof_dir,
            expected_slide_count=len(render_plan.slides),
            slide_size=render_plan.slide_size,
        )
        stages.extend(("libreoffice-pdf", "poppler-png"))
        findings = [
            *quality_v2_findings,
            *adapt_render_findings(render_plan.findings),
            *inspect_render_plan_delivery(render_plan),
            *(
                QualityFindingV2(
                    namespace="render",
                    code=item.code,
                    severity=item.severity,
                    slide_id=None,
                    object_id=None,
                    message=item.message,
                    metric=item.metric,
                    threshold=item.threshold,
                    source_stage="generated-visual-floor",
                )
                for item in generated_visual_findings
            ),
        ]
        findings.extend(
            (
                QualityFindingV2(
                    "package",
                    "OOXML_SEMANTIC_VALIDATED",
                    "info",
                    None,
                    None,
                    "candidate package matches the authoritative RenderPlan",
                    metric=semantic_report.part_count,
                    source_stage="ooxml-semantic",
                ),
                QualityFindingV2(
                    "preview",
                    "LIBREOFFICE_RENDER_VALIDATED",
                    "info",
                    None,
                    None,
                    "LibreOffice PDF and Poppler PNG proof completed",
                    metric=proof.page_count,
                    source_stage="libreoffice-proof",
                ),
            )
        )
        findings.extend(
            inspect_preview_images(
                proof.png_paths,
                slide_ids=(slide.source_id for slide in render_plan.slides),
                expected_slide_count=len(render_plan.slides),
            )
        )
        quality_report = build_quality_report_v2(
            findings,
            transaction_status="portable-pre-promotion",
        )
        staged_quality_path = Path(
            write_quality_report_v2(quality_report, audit_staging)
        )
        artifacts.update(
            {
                "quality_report_v2": str(audit_dir / staged_quality_path.name),
                "portable_pdf": str(final_proof_dir / proof.pdf_path.name),
                "portable_png_dir": str(final_proof_dir),
            }
        )
        stages.append("quality-v2-gate")
        if quality_report.hard_gate_failures:
            raise QualityV2GateError(
                "portable candidate failed quality gates: "
                + ", ".join(quality_report.hard_gate_failures),
                quality_report_v2=quality_report,
                artifacts=artifacts,
            )

        powerpoint_result: Mapping[str, Any] | None = None
        powerpoint_stage_dir: Path | None = None
        powerpoint_final_dir: Path | None = None
        if verification_level == "powerpoint":
            if powerpoint_certifier is None:
                raise TransactionError(
                    "powerpoint verification requested without a certification adapter"
                )
            powerpoint_stage_dir = audit_staging / "powerpoint-certification"
            powerpoint_final_dir = audit_dir / "powerpoint-certification"
            certification_input = audit_staging / ".powerpoint-certification-input.pptx"
            certified_candidate_sha256 = sha256_file(candidate)
            if certified_candidate_sha256 != proof.candidate_hash_after:
                raise TransactionError(
                    "portable candidate changed before PowerPoint certification"
                )
            shutil.copyfile(candidate, certification_input)
            raw_powerpoint_result = dict(
                powerpoint_certifier(
                    certification_input,
                    powerpoint_stage_dir,
                )
            )
            if sha256_file(certification_input) != certified_candidate_sha256:
                raise TransactionError(
                    "isolated PowerPoint certification input changed during certification"
                )
            if sha256_file(candidate) != certified_candidate_sha256:
                raise TransactionError(
                    "portable candidate changed during PowerPoint certification"
                )
            raw_powerpoint_result = _validate_powerpoint_certification_result(
                raw_powerpoint_result,
                expected_sha256=certified_candidate_sha256,
                artifact_dir=powerpoint_stage_dir,
                expected_slide_count=len(render_plan.slides),
                slide_size=render_plan.slide_size,
            )
            # Treat the adapter as an untrusted post-verification boundary.  A
            # second semantic inspection prevents any closure/global side effect
            # from bypassing the already completed OOXML gate.
            inspect_rendered_pptx(candidate, render_plan)
            certification_input.unlink()
            powerpoint_result = dict(raw_powerpoint_result)
            pdf_value = raw_powerpoint_result.get("pdf_path")
            if isinstance(pdf_value, str):
                powerpoint_result["pdf_path"] = str(
                    powerpoint_final_dir / Path(pdf_value).name
                )
            png_values = raw_powerpoint_result.get("png_paths")
            if isinstance(png_values, list) and all(
                isinstance(value, str) for value in png_values
            ):
                powerpoint_result["png_paths"] = [
                    str(powerpoint_final_dir / Path(value).name)
                    for value in png_values
                ]
            stages.append("powerpoint-certification")

        final_candidate_sha256 = sha256_file(candidate)
        if final_candidate_sha256 != proof.candidate_hash_after:
            raise TransactionError(
                "portable candidate changed after cross-engine verification"
            )
        inspect_rendered_pptx(candidate, render_plan)
        stages.append("post-verification-integrity")

        if source_hash_before is not None and source is not None:
            source_hash_after = sha256_file(source)
            if source_hash_after != source_hash_before:
                raise TransactionError(
                    "source presentation changed during portable verification"
                )
        stages.append("source-integrity")
        if export_pdf:
            assert pdf_candidate is not None
            shutil.copyfile(proof.pdf_path, pdf_candidate)
            if not pdf_candidate.read_bytes().startswith(b"%PDF-"):
                raise TransactionError("portable PDF candidate is unreadable")
        promoted = not output_policy.no_output_deck
        if output_policy.no_output_deck:
            candidate.unlink(missing_ok=True)
            if pdf_candidate is not None:
                pdf_candidate.unlink(missing_ok=True)
            stages.append("no-output-cleanup")
        final_quality = build_quality_report_v2(
            list(quality_report.findings),
            transaction_status=(
                "transaction-promoted" if promoted else "transaction-skipped"
            ),
        )
        staged_quality_path = Path(
            write_quality_report_v2(final_quality, audit_staging)
        )
        proof_result = replace(
            proof,
            pdf_path=final_proof_dir / proof.pdf_path.name,
            png_paths=tuple(
                final_proof_dir / path.name for path in proof.png_paths
            ),
        )
        verification = VerificationResult(
            verification_level,
            semantic_report,
            proof_result,
            final_quality,
            powerpoint_result,
        )
        artifacts["portable_verification"] = str(
            audit_dir / "portable-verification.json"
        )
        artifact_sha256: dict[str, str] = {
            "ooxml_report": sha256_file(staged_ooxml_report),
            "quality_report_v2": sha256_file(staged_quality_path),
            "portable_pdf": sha256_file(proof.pdf_path),
        }
        artifact_files: dict[str, str] = {
            "ooxml_report": "ooxml-report.json",
            "quality_report_v2": staged_quality_path.name,
            "portable_pdf": f"portable-proof/{proof.pdf_path.name}",
        }
        for index, path in enumerate(proof.png_paths, start=1):
            key = f"portable_png_{index:03d}"
            artifact_sha256[key] = sha256_file(path)
            artifact_files[key] = f"portable-proof/{path.name}"
        if promoted:
            artifact_sha256["output_pptx"] = final_candidate_sha256
            if export_pdf:
                artifact_sha256["output_pdf"] = sha256_file(proof.pdf_path)
        if powerpoint_stage_dir is not None and powerpoint_stage_dir.is_dir():
            for path in sorted(
                item for item in powerpoint_stage_dir.iterdir() if item.is_file()
            ):
                key = f"powerpoint_{path.name}"
                artifact_sha256[key] = sha256_file(path)
                artifact_files[key] = f"powerpoint-certification/{path.name}"

        staged_verification_manifest = audit_staging / "portable-verification.json"
        staged_verification_manifest.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "candidate_path": str(output),
                    "candidate_sha256": final_candidate_sha256,
                    "backend": selection.to_dict(),
                    "verification": verification.to_dict(),
                    "artifact_sha256": dict(sorted(artifact_sha256.items())),
                    "artifact_files": dict(sorted(artifact_files.items())),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        artifact_sha256["portable_verification"] = sha256_file(
            staged_verification_manifest
        )

        promotions: list[tuple[Path, Path]] = [
            (staged_ooxml_report, audit_dir / "ooxml-report.json"),
            (staged_quality_path, audit_dir / staged_quality_path.name),
            (staged_verification_manifest, audit_dir / "portable-verification.json"),
            (proof_dir, final_proof_dir),
        ]
        if (
            powerpoint_stage_dir is not None
            and powerpoint_final_dir is not None
            and powerpoint_stage_dir.exists()
        ):
            promotions.append((powerpoint_stage_dir, powerpoint_final_dir))
        if promoted:
            if export_pdf:
                assert pdf_candidate is not None
                promotions.append((pdf_candidate, output.with_suffix(".pdf")))
            promotions.append((candidate, output))
        cleanup_errors = list(_promote_bundle(promotions))
        stages.append("atomic-promote" if promoted else "audit-promote")
        if promoted and export_pdf:
            stages.append("pdf-atomic-promote")
        try:
            _remove_artifact(audit_staging)
        except Exception as exc:
            cleanup_errors.append(
                f"could not remove portable audit staging {audit_staging}: {exc}"
            )

        result = CandidateResult(
            output_path=output,
            promoted=promoted,
            candidate_path=None,
            source_hash_before=source_hash_before,
            source_hash_after=source_hash_after,
            validation_steps=tuple(stages[2:]),
            cleanup_errors=tuple(cleanup_errors),
        )
        final_render_report = (
            replace(render_report, output_path=output)
            if promoted
            else render_report
        )
        return PortablePipelineResult(
            dict(compiled_deck),
            render_plan,
            selection,
            final_render_report,
            verification,
            result,
            tuple(stages),
            artifacts,
            artifact_sha256,
        )
    except Exception:
        candidate.unlink(missing_ok=True)
        if pdf_candidate is not None:
            pdf_candidate.unlink(missing_ok=True)
        try:
            _remove_artifact(audit_staging)
        except Exception:
            # Preserve the primary rendering/verification failure.  The hidden,
            # run-scoped staging path is never referenced by stable evidence.
            pass
        raise


__all__ = [
    "PortablePipelineResult",
    "VerificationResult",
    "execute_portable_render_plan",
]
