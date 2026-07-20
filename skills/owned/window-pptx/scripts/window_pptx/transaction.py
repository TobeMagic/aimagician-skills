"""Transactional PowerPoint output helpers.

Final output paths are touched only after a candidate has passed structural and
PowerPoint reopen validation.  This module deliberately does not attempt an
in-process same-path overwrite: the source presentation is necessarily open
while ``SaveCopyAs`` runs, so that operation cannot be proven safe here.
"""

from __future__ import annotations

import hashlib
import os
import re
import uuid
import zipfile
from pathlib import Path
from typing import Any, Callable

from .com_session import macro_security
from .errors import OutputPolicyError, WindowPptxError
from .models import CandidateResult, OutputPolicy
from .output_policy import validate_output_policy


MSO_FALSE = 0
MSO_TRUE = -1
PP_FIXED_FORMAT_TYPE_PDF = 2
PP_FIXED_FORMAT_INTENT_PRINT = 2
REQUIRED_OOXML_PARTS = frozenset(
    {
        "[Content_Types].xml",
        "_rels/.rels",
        "ppt/presentation.xml",
    }
)


class TransactionError(WindowPptxError):
    """A candidate save failed before a complete delivery was promoted."""

    def __init__(self, message: str, *, cleanup_errors: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.cleanup_errors = cleanup_errors


class PartialSaveError(TransactionError):
    """The PPTX was promoted but an optional follow-up output failed."""

    def __init__(
        self,
        message: str,
        *,
        pptx_result: CandidateResult,
        cleanup_errors: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message, cleanup_errors=cleanup_errors)
        self.pptx_result = pptx_result


class SourceIntegrityError(PartialSaveError):
    """An output was promoted but the distinct source failed its final hash check."""


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it all into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _ascii_token(token: str | None) -> str:
    if token is None:
        return uuid.uuid4().hex
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", token.encode("ascii", "ignore").decode())
    cleaned = cleaned.strip("-_")
    return cleaned or hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def candidate_path_for(output_path: Path, token: str | None = None) -> Path:
    """Build an ASCII-safe hidden candidate beside ``output_path``."""

    resolved_text = str(output_path.resolve(strict=False)).encode("utf-8")
    path_key = hashlib.sha256(resolved_text).hexdigest()[:10]
    candidate = output_path.parent / (
        f".window-pptx-{path_key}-{_ascii_token(token)}{output_path.suffix}"
    )
    if candidate.resolve(strict=False) == output_path.resolve(strict=False):
        candidate = output_path.parent / (
            f".window-pptx-{path_key}-{_ascii_token(token)}-candidate{output_path.suffix}"
        )
    return candidate


def validate_ooxml_package(path: Path) -> None:
    """Require a readable, uncorrupted PowerPoint OOXML package."""

    try:
        with zipfile.ZipFile(path, "r") as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise WindowPptxError(
                    f"OOXML ZIP contains a corrupt member: {bad_member}"
                )
            missing = REQUIRED_OOXML_PARTS.difference(archive.namelist())
            if missing:
                raise WindowPptxError(
                    "OOXML package is missing required parts: "
                    + ", ".join(sorted(missing))
                )
    except WindowPptxError:
        raise
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise WindowPptxError(f"OOXML ZIP is unreadable or corrupt: {exc}") from exc


def _cleanup_candidates(paths: tuple[Path | None, ...]) -> tuple[str, ...]:
    errors: list[str] = []
    for path in paths:
        if path is None or not path.exists():
            continue
        try:
            path.unlink()
        except Exception as exc:  # cleanup evidence must survive the original failure
            errors.append(f"Candidate cleanup failed for {path}: {exc}")
    return tuple(errors)


def _raise_transaction_error(
    exc: Exception,
    *,
    cleanup_errors: tuple[str, ...],
    pptx_result: CandidateResult | None,
) -> None:
    cleanup_suffix = ""
    if cleanup_errors:
        cleanup_suffix = "; cleanup errors: " + " | ".join(cleanup_errors)
    if pptx_result is not None:
        raise PartialSaveError(
            f"PPTX promoted to {pptx_result.output_path}, but PDF delivery failed: "
            f"{exc}{cleanup_suffix}",
            pptx_result=pptx_result,
            cleanup_errors=cleanup_errors,
        ) from exc
    raise TransactionError(
        f"Transactional save failed: {exc}{cleanup_suffix}",
        cleanup_errors=cleanup_errors,
    ) from exc


def save_candidate(
    presentation: Any,
    app: Any,
    policy: OutputPolicy,
    *,
    export_pdf: bool = False,
    reopen: Callable[[Path], Any] | None = None,
    replace: Callable[[str | Path, str | Path], None] = os.replace,
) -> CandidateResult:
    """Save, validate, and atomically promote a PowerPoint candidate."""

    validate_output_policy(policy)
    output_path = policy.output_path or Path()

    if policy.dry_run or policy.no_output_deck:
        return CandidateResult(
            output_path=output_path,
            promoted=False,
            candidate_path=None,
            source_hash_before=None,
            source_hash_after=None,
            validation_steps=(),
            cleanup_errors=(),
        )

    if policy.output_path is None:  # guarded by validate_output_policy
        raise OutputPolicyError("A transactional save requires an output path.")

    source = policy.source_path
    if source is not None and (
        source.resolve(strict=False) == output_path.resolve(strict=False)
    ):
        raise OutputPolicyError(
            "A same-path overwrite is unsafe while the source presentation is open; "
            "close the presentation and use a separately verified external promotion flow."
        )

    source_hash_before = sha256_file(source) if source is not None and source.exists() else None
    source_hash_after: str | None = source_hash_before
    candidate = candidate_path_for(output_path)
    pdf_output = output_path.with_suffix(".pdf") if export_pdf else None
    pdf_candidate = candidate_path_for(pdf_output) if pdf_output is not None else None
    steps: list[str] = []
    pptx_result: CandidateResult | None = None

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        presentation.SaveCopyAs(str(candidate))
        steps.append("save-copy")

        validate_ooxml_package(candidate)
        steps.append("ooxml-package")

        open_validation_copy = reopen
        if open_validation_copy is None:
            open_validation_copy = lambda path: app.Presentations.Open(
                str(path), MSO_TRUE, MSO_FALSE, MSO_FALSE
            )
        validation_presentation = None
        with macro_security(app):
            validation_presentation = open_validation_copy(candidate)
        steps.append("macro-disabled-reopen")
        try:
            validation_presentation.Close()
        except Exception as exc:
            raise WindowPptxError(
                f"Validation presentation could not be closed: {exc}"
            ) from exc
        steps.append("validation-copy-closed")

        if source_hash_before is not None and source is not None:
            source_hash_after = sha256_file(source)
            if source_hash_after != source_hash_before:
                raise WindowPptxError(
                    "The source presentation changed during candidate validation; "
                    "promotion was aborted."
                )

        replace(candidate, output_path)
        steps.append("atomic-promote")
        pptx_result = CandidateResult(
            output_path=output_path,
            promoted=True,
            candidate_path=None,
            source_hash_before=source_hash_before,
            source_hash_after=source_hash_after,
            validation_steps=tuple(steps),
            cleanup_errors=(),
        )

        if export_pdf:
            assert pdf_candidate is not None and pdf_output is not None
            presentation.ExportAsFixedFormat(
                str(pdf_candidate),
                PP_FIXED_FORMAT_TYPE_PDF,
                PP_FIXED_FORMAT_INTENT_PRINT,
            )
            steps.append("pdf-export")
            try:
                pdf_header = pdf_candidate.read_bytes()[:5]
            except OSError as exc:
                raise WindowPptxError(f"PDF candidate is unreadable: {exc}") from exc
            if pdf_header != b"%PDF-":
                raise WindowPptxError(
                    "PDF candidate is empty or does not begin with the %PDF- header."
                )
            steps.append("pdf-header")
            replace(pdf_candidate, pdf_output)
            steps.append("pdf-atomic-promote")

        if source_hash_before is not None and source is not None:
            try:
                source_hash_after = sha256_file(source)
            except Exception as exc:
                steps.append("source-integrity-postcheck-failed")
                failed_result = CandidateResult(
                    output_path=output_path,
                    promoted=True,
                    candidate_path=None,
                    source_hash_before=source_hash_before,
                    source_hash_after=None,
                    validation_steps=tuple(steps),
                    cleanup_errors=(),
                )
                raise SourceIntegrityError(
                    f"Output was promoted to {output_path}, but the final source "
                    f"integrity check could not read {source}: {exc}",
                    pptx_result=failed_result,
                ) from exc
            if source_hash_after != source_hash_before:
                steps.append("source-integrity-postcheck-failed")
                failed_result = CandidateResult(
                    output_path=output_path,
                    promoted=True,
                    candidate_path=None,
                    source_hash_before=source_hash_before,
                    source_hash_after=source_hash_after,
                    validation_steps=tuple(steps),
                    cleanup_errors=(),
                )
                raise SourceIntegrityError(
                    f"Output was promoted to {output_path}, but the distinct source "
                    f"failed its final source integrity check: {source} changed.",
                    pptx_result=failed_result,
                )
            steps.append("source-integrity-postcheck")

        return CandidateResult(
            output_path=output_path,
            promoted=True,
            candidate_path=None,
            source_hash_before=source_hash_before,
            source_hash_after=source_hash_after,
            validation_steps=tuple(steps),
            cleanup_errors=(),
        )
    except SourceIntegrityError:
        _cleanup_candidates((candidate, pdf_candidate))
        raise
    except Exception as exc:
        cleanup_errors = _cleanup_candidates((candidate, pdf_candidate))
        _raise_transaction_error(
            exc,
            cleanup_errors=cleanup_errors,
            pptx_result=pptx_result,
        )
        raise AssertionError("unreachable")
