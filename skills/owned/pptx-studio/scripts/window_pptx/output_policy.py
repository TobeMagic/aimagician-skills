"""Validation and export sizing for safe PowerPoint output."""

from __future__ import annotations

from pathlib import Path

from .errors import OutputPolicyError
from .models import OutputPolicy


POWERPOINT_EXTENSIONS = frozenset({".pptx", ".pptm", ".potx", ".potm"})


def _validate_extension(path: Path, label: str) -> None:
    suffix = path.suffix.lower()
    if suffix not in POWERPOINT_EXTENSIONS:
        allowed = ", ".join(sorted(POWERPOINT_EXTENSIONS))
        raise OutputPolicyError(
            f"{label} must have a supported PowerPoint extension ({allowed})."
        )


def validate_output_policy(policy: OutputPolicy) -> None:
    """Reject missing or unsafe PowerPoint output destinations."""

    if policy.dry_run and policy.allow_overwrite:
        raise OutputPolicyError("A dry-run cannot allow overwrite.")

    if policy.source_path is not None:
        _validate_extension(policy.source_path, "Source path")

    if policy.output_path is None:
        if policy.dry_run or policy.no_output_deck:
            return
        raise OutputPolicyError(
            "An output path is required unless dry-run or no-output-deck is enabled."
        )

    _validate_extension(policy.output_path, "Output path")

    if policy.source_path is None:
        return

    source = policy.source_path.resolve(strict=False)
    output = policy.output_path.resolve(strict=False)
    if source == output and not policy.allow_overwrite:
        raise OutputPolicyError(
            "Output path resolves to the source path; explicit overwrite permission is required."
        )


def calculate_export_size(
    page_width: float,
    page_height: float,
    target_long_edge: int = 1600,
) -> tuple[int, int]:
    """Scale page dimensions while keeping the longest output edge exact."""

    if page_width <= 0 or page_height <= 0:
        raise ValueError("Page dimensions must be positive.")
    if target_long_edge <= 0:
        raise ValueError("Target long edge must be positive.")

    if page_width >= page_height:
        scaled_height = max(1, round(target_long_edge * page_height / page_width))
        return target_long_edge, scaled_height

    scaled_width = max(1, round(target_long_edge * page_width / page_height))
    return scaled_width, target_long_edge
