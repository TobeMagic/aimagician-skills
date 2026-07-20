"""Pure safety primitives for Windows PowerPoint automation."""

from .com_session import dispatch_powerpoint, macro_security
from .cli import build_dry_run_result, collect_requested_actions, emit_result, parse_args
from .errors import ComSessionError, OutputPolicyError, WindowPptxError
from .models import CandidateResult, OutputPolicy, PowerPointHandle
from .output_policy import calculate_export_size, validate_output_policy
from .transaction import (
    PartialSaveError,
    SourceIntegrityError,
    TransactionError,
    candidate_path_for,
    save_candidate,
    sha256_file,
    validate_ooxml_package,
)

__all__ = [
    "ComSessionError",
    "CandidateResult",
    "OutputPolicy",
    "OutputPolicyError",
    "PowerPointHandle",
    "PartialSaveError",
    "SourceIntegrityError",
    "TransactionError",
    "WindowPptxError",
    "build_dry_run_result",
    "calculate_export_size",
    "candidate_path_for",
    "collect_requested_actions",
    "dispatch_powerpoint",
    "emit_result",
    "macro_security",
    "parse_args",
    "save_candidate",
    "sha256_file",
    "validate_ooxml_package",
    "validate_output_policy",
]
