"""Portable render-evidence completion for active source packages only."""

from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path
from typing import Any, Mapping, Sequence
from xml.etree import ElementTree as ET

from window_pptx.gaojie_diversity import fingerprint_preview
from window_pptx.layouts import SlideSize
from window_pptx.libreoffice import LibreOfficeVerifier

from .curation import ACTIVE_GAOJIE_CATEGORIES


class RenderEvidenceError(ValueError):
    """Raised when a package cannot gain portable rendering evidence."""


_SLIDE_RE = re.compile(r"^ppt/slides/slide([1-9][0-9]*)\.xml$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _geometry(path: Path) -> tuple[int, SlideSize]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if _SLIDE_RE.fullmatch(name)]
            root = ET.fromstring(archive.read("ppt/presentation.xml"))
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
        raise RenderEvidenceError("PPTX_INSPECTION_FAILED") from exc
    size = next((item for item in root.iter() if item.tag.rsplit("}", 1)[-1] == "sldSz"), None)
    if size is None or not names:
        raise RenderEvidenceError("PPTX_GEOMETRY_MISSING")
    try:
        return len(names), SlideSize(width=int(size.attrib["cx"]) / 914400, height=int(size.attrib["cy"]) / 914400)
    except (KeyError, ValueError) as exc:
        raise RenderEvidenceError("PPTX_GEOMETRY_MISSING") from exc


def complete_render_index(
    source_root: Path | str,
    *,
    existing_index: Mapping[str, Mapping[str, Any]],
    evidence_root: Path | str,
    active_categories: Sequence[str] = ACTIVE_GAOJIE_CATEGORIES,
) -> dict[str, Any]:
    """Render only package/slide keys absent from validated existing evidence."""

    source = Path(source_root).expanduser().resolve(strict=False)
    evidence = Path(evidence_root).expanduser().resolve(strict=False)
    if not source.is_dir() or source.is_symlink():
        raise RenderEvidenceError("ROOT_INVALID")
    # Evidence is a private derived artifact.  Creating this explicit target is
    # safe and keeps rendering independent from pre-existing directory layout.
    evidence.mkdir(parents=True, exist_ok=True)
    if evidence.is_symlink() or not evidence.is_dir():
        raise RenderEvidenceError("EVIDENCE_ROOT_INVALID")
    result: dict[str, dict[str, Any]] = {}
    rendered_packages = 0
    for category in active_categories:
        directory = source / category
        if not directory.is_dir() or directory.is_symlink():
            raise RenderEvidenceError("SOURCE_SCOPE_INVALID")
        for package in sorted(directory.rglob("*.pptx"), key=lambda item: item.as_posix()):
            digest = _sha256(package)
            page_count, size = _geometry(package)
            keys = [f"{digest}:{number:03d}" for number in range(1, page_count + 1)]
            usable = all(
                isinstance(existing_index.get(key), Mapping)
                and isinstance(existing_index[key].get("image_sha256"), str)
                for key in keys
            )
            if usable:
                result.update({key: dict(existing_index[key]) for key in keys})
                continue
            proof = LibreOfficeVerifier(dpi=96).verify(
                package,
                artifact_dir=evidence / "rendered" / digest[:24],
                expected_slide_count=page_count,
                slide_size=size,
            )
            if len(proof.png_paths) != page_count:
                raise RenderEvidenceError("RENDER_PAGE_COUNT_MISMATCH")
            rendered_packages += 1
            for number, png in enumerate(proof.png_paths, start=1):
                fingerprint = fingerprint_preview(png.read_bytes())
                result[f"{digest}:{number:03d}"] = {
                    "image_sha256": fingerprint.sha256,
                    "width": fingerprint.width,
                    "height": fingerprint.height,
                    "visual_quality": fingerprint.quality,
                    "png_locator": png.relative_to(evidence).as_posix(),
                }
    return {
        "schema_version": "1.0",
        "status": "PASS",
        "source_kind": "gaojie",
        "rendered_package_count": rendered_packages,
        "page_count": len(result),
        "pages": dict(sorted(result.items())),
    }
