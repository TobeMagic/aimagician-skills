"""Errors raised by the window-pptx safety layer."""


class WindowPptxError(RuntimeError):
    """Base error for safe PowerPoint automation."""


class OutputPolicyError(WindowPptxError):
    """Raised when an output policy permits an unsafe operation."""


class ComSessionError(WindowPptxError):
    """Raised when a safe PowerPoint COM session cannot be established."""
