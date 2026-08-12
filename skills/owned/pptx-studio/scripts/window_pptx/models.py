"""Data models shared by the window-pptx safety primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OutputPolicy:
    """Immutable description of permitted deck output behavior."""

    source_path: Path | None
    output_path: Path | None
    dry_run: bool = False
    no_output_deck: bool = False
    allow_overwrite: bool = False


@dataclass(frozen=True)
class CandidateResult:
    """Evidence produced by a transactional presentation save."""

    output_path: Path
    promoted: bool
    candidate_path: Path | None
    source_hash_before: str | None
    source_hash_after: str | None
    validation_steps: tuple[str, ...]
    cleanup_errors: tuple[str, ...]


@dataclass
class PowerPointHandle:
    """A PowerPoint application together with its proven ownership."""

    app: Any
    owned: bool
    dispatch_mode: str
    cleanup_errors: list[str] = field(default_factory=list)

    def close_presentation(self, presentation: Any, keep_open: bool = False) -> None:
        """Close a presentation unless requested otherwise, recording failures."""

        if keep_open:
            return
        try:
            presentation.Close()
        except Exception as exc:
            self.cleanup_errors.append(f"Presentation close failed: {exc}")

    def quit(self, keep_open: bool = False) -> None:
        """Quit PowerPoint only when this handle owns the application."""

        if keep_open or not self.owned:
            return
        try:
            self.app.Quit()
        except Exception as exc:
            self.cleanup_errors.append(f"PowerPoint quit failed: {exc}")
