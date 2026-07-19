"""Pure safety primitives for Windows PowerPoint automation."""

from .com_session import dispatch_powerpoint, macro_security
from .errors import ComSessionError, OutputPolicyError, WindowPptxError
from .models import OutputPolicy, PowerPointHandle
from .output_policy import calculate_export_size, validate_output_policy

__all__ = [
    "ComSessionError",
    "OutputPolicy",
    "OutputPolicyError",
    "PowerPointHandle",
    "WindowPptxError",
    "calculate_export_size",
    "dispatch_powerpoint",
    "macro_security",
    "validate_output_policy",
]
