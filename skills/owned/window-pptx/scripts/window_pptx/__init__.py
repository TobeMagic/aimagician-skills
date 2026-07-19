"""Pure safety primitives for Windows PowerPoint automation."""

from .com_session import dispatch_powerpoint, macro_security
from .cli import build_dry_run_result, collect_requested_actions, emit_result, parse_args
from .errors import ComSessionError, OutputPolicyError, WindowPptxError
from .models import OutputPolicy, PowerPointHandle
from .output_policy import calculate_export_size, validate_output_policy

__all__ = [
    "ComSessionError",
    "OutputPolicy",
    "OutputPolicyError",
    "PowerPointHandle",
    "WindowPptxError",
    "build_dry_run_result",
    "calculate_export_size",
    "collect_requested_actions",
    "dispatch_powerpoint",
    "emit_result",
    "macro_security",
    "parse_args",
    "validate_output_policy",
]
