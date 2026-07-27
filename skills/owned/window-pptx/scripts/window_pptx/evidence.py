"""Deterministic visual-evidence helpers for portable PPTX delivery."""

from __future__ import annotations

import os
import re
import struct
import tempfile
from pathlib import Path
from typing import Iterable


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_SLIDE_PNG_PATTERN = re.compile(r"^slide-(?P<index>[0-9]{3})\.png$")


def _validate_expected_count(expected_count: int | None) -> None:
    if expected_count is None:
        return
    if (
        isinstance(expected_count, bool)
        or not isinstance(expected_count, int)
        or expected_count < 1
    ):
        raise ValueError("expected_count must be a positive integer")


def _validate_png_file(path: Path) -> None:
    try:
        with path.open("rb") as stream:
            header = stream.read(24)
    except OSError as exc:
        raise ValueError(f"portable slide PNG is unreadable: {path}") from exc
    if len(header) < 24 or not header.startswith(_PNG_SIGNATURE):
        raise ValueError(f"portable slide PNG has an invalid signature: {path}")
    width, height = struct.unpack(">II", header[16:24])
    if width < 1 or height < 1:
        raise ValueError(f"portable slide PNG has invalid geometry: {path}")


def select_portable_slide_pngs(
    paths: Iterable[Path | str],
    *,
    proof_dir: Path | str | None = None,
    expected_count: int | None = None,
) -> tuple[Path, ...]:
    """Select and validate the exact, continuous Poppler slide-page sequence.

    Non-page images are deliberately ignored.  A selected page must be a real
    file named ``portable-proof/slide-NNN.png``.  All selected pages must share
    one proof directory, start at 001, and contain no gaps or duplicates.
    Supplying ``proof_dir`` confines a repository-wide artifact scan to one
    trial and prevents pages from another portable proof being mixed in.
    """

    _validate_expected_count(expected_count)
    candidates = tuple(Path(value) for value in paths)
    resolved_proof: Path | None = None
    if proof_dir is not None:
        candidate_proof = Path(proof_dir)
        try:
            resolved_proof = candidate_proof.resolve(strict=True)
        except OSError as exc:
            raise ValueError(
                f"portable proof directory is missing: {candidate_proof}"
            ) from exc
        if not resolved_proof.is_dir() or resolved_proof.name != "portable-proof":
            raise ValueError(
                "proof_dir must be an existing directory named portable-proof"
            )

    selected: dict[int, Path] = {}
    for candidate in candidates:
        match = _SLIDE_PNG_PATTERN.fullmatch(candidate.name)
        if match is None or candidate.parent.name != "portable-proof":
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"portable slide PNG is missing: {candidate}") from exc
        if not resolved.is_file():
            raise ValueError(f"portable slide PNG is not a file: {candidate}")
        parent = resolved.parent
        if resolved_proof is not None and parent != resolved_proof:
            continue
        if resolved_proof is None:
            resolved_proof = parent
        elif parent != resolved_proof:
            raise ValueError("portable slide PNGs span multiple proof directories")
        index = int(match.group("index"))
        if index < 1:
            raise ValueError("portable slide PNG numbering must start at 001")
        if index in selected:
            raise ValueError(f"duplicate portable slide PNG index: {index:03d}")
        _validate_png_file(resolved)
        selected[index] = resolved

    if not selected:
        raise ValueError("no portable-proof/slide-NNN.png pages were found")
    indexes = sorted(selected)
    expected_indexes = list(range(1, len(indexes) + 1))
    if indexes != expected_indexes:
        raise ValueError(
            "portable slide PNG numbering is not continuous: "
            f"expected={expected_indexes}, observed={indexes}"
        )
    if expected_count is not None and len(indexes) != expected_count:
        raise ValueError(
            "portable slide PNG count mismatch: "
            f"expected={expected_count}, observed={len(indexes)}"
        )
    return tuple(selected[index] for index in indexes)


def validate_portable_slide_pngs(
    paths: Iterable[Path | str],
    *,
    proof_dir: Path | str | None = None,
    expected_count: int | None = None,
) -> tuple[Path, ...]:
    """Strictly validate a declared list containing slide pages and nothing else."""

    declared = tuple(Path(value) for value in paths)
    selected = select_portable_slide_pngs(
        declared,
        proof_dir=proof_dir,
        expected_count=expected_count,
    )
    if len(selected) != len(declared):
        raise ValueError(
            "declared portable slide PNGs contain a non-page image or path"
        )
    return selected


def write_contact_sheet(
    png_paths: Iterable[Path | str],
    target: Path | str,
) -> Path:
    """Atomically build a deterministic contact sheet from real slide pages."""

    pages = validate_portable_slide_pngs(png_paths)
    destination = Path(target)
    if destination.resolve(strict=False) in pages:
        raise ValueError("contact sheet target must not replace a slide page")
    try:
        from PIL import Image, ImageDraw, ImageOps
    except ImportError as exc:  # pragma: no cover - runtime fingerprint includes Pillow
        raise RuntimeError("Pillow is required for portable contact sheets") from exc

    columns = min(3, len(pages))
    rows = (len(pages) + columns - 1) // columns
    thumbnail_size = (480, 270)
    label_height = 32
    gutter = 18
    canvas = Image.new(
        "RGB",
        (
            gutter + columns * (thumbnail_size[0] + gutter),
            gutter + rows * (thumbnail_size[1] + label_height + gutter),
        ),
        "#E5E7EB",
    )
    draw = ImageDraw.Draw(canvas)
    for index, path in enumerate(pages):
        with Image.open(path) as opened:
            opened.verify()
        with Image.open(path) as opened:
            page = opened.convert("RGB")
            fitted = ImageOps.contain(
                page,
                thumbnail_size,
                method=Image.Resampling.LANCZOS,
            )
        cell_x = gutter + (index % columns) * (thumbnail_size[0] + gutter)
        cell_y = gutter + (index // columns) * (
            thumbnail_size[1] + label_height + gutter
        )
        draw.rectangle(
            (
                cell_x,
                cell_y,
                cell_x + thumbnail_size[0],
                cell_y + thumbnail_size[1],
            ),
            fill="#FFFFFF",
            outline="#94A3B8",
            width=1,
        )
        image_x = cell_x + (thumbnail_size[0] - fitted.width) // 2
        image_y = cell_y + (thumbnail_size[1] - fitted.height) // 2
        canvas.paste(fitted, (image_x, image_y))
        draw.text(
            (cell_x + 8, cell_y + thumbnail_size[1] + 8),
            f"Slide {index + 1:02d}",
            fill="#111827",
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
        canvas.save(
            temporary,
            format="PNG",
            optimize=False,
            compress_level=9,
        )
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        canvas.close()
    return destination


__all__ = [
    "select_portable_slide_pngs",
    "validate_portable_slide_pngs",
    "write_contact_sheet",
]
