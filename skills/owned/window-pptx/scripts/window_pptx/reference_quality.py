"""Reference-grade OOXML and preview quality gates.

Traditional overflow checks can approve a deck made of a title and three text
boxes.  This module adds a structural visual floor: editable charts, embedded
data, grouped/vector composition, media depth, page-level object richness, and
layout variation must survive generation.  PNG preview checks remain the
independent rendered-view gate.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

from .preview_quality import inspect_preview_images
from .transaction import sha256_file


PML = "http://schemas.openxmlformats.org/presentationml/2006/main"
AML = "http://schemas.openxmlformats.org/drawingml/2006/main"
CHART = "http://schemas.openxmlformats.org/drawingml/2006/chart"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_SLIDE = re.compile(r"ppt/slides/slide(\d+)\.xml")


class ReferenceQualityError(ValueError):
    """A reference-grade package or quality profile is invalid."""


@dataclass(frozen=True)
class ReferenceQualityProfile:
    minimum_average_objects: float = 12.0
    minimum_layout_signatures: int = 5
    minimum_media_count: int = 4
    minimum_media_bytes: int = 250_000
    minimum_chart_count: int = 1
    minimum_group_count: int = 1
    minimum_decorative_primitives: int = 12


@dataclass(frozen=True)
class GeneratedVisualQualityProfile:
    minimum_average_objects: float = 9.0
    minimum_layout_signatures: int = 5
    rich_slide_object_floor: int = 8
    minimum_rich_slide_ratio: float = 0.60


@dataclass(frozen=True)
class ReferenceComplexity:
    slide_count: int
    shape_count: int
    picture_count: int
    graphic_frame_count: int
    group_count: int
    connector_count: int
    chart_count: int
    embedded_workbook_count: int
    media_count: int
    media_bytes: int
    gradient_count: int
    crop_count: int
    average_objects_per_slide: float
    layout_signature_count: int
    layout_signatures: tuple[str, ...]
    objects_per_slide: tuple[int, ...]

    @property
    def decorative_primitives(self) -> int:
        return self.group_count + self.connector_count + self.gradient_count + self.crop_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_count": self.slide_count,
            "shape_count": self.shape_count,
            "picture_count": self.picture_count,
            "graphic_frame_count": self.graphic_frame_count,
            "group_count": self.group_count,
            "connector_count": self.connector_count,
            "chart_count": self.chart_count,
            "embedded_workbook_count": self.embedded_workbook_count,
            "media_count": self.media_count,
            "media_bytes": self.media_bytes,
            "gradient_count": self.gradient_count,
            "crop_count": self.crop_count,
            "average_objects_per_slide": self.average_objects_per_slide,
            "layout_signature_count": self.layout_signature_count,
            "layout_signatures": list(self.layout_signatures),
            "objects_per_slide": list(self.objects_per_slide),
            "decorative_primitives": self.decorative_primitives,
        }


@dataclass(frozen=True)
class ReferenceQualityFinding:
    code: str
    severity: str
    message: str
    metric: float | int | str | None
    threshold: float | int | str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "metric": self.metric,
            "threshold": self.threshold,
        }


@dataclass(frozen=True)
class ReferenceQualityReport:
    pptx_path: Path
    pptx_sha256: str
    profile: ReferenceQualityProfile
    complexity: ReferenceComplexity
    findings: tuple[ReferenceQualityFinding, ...]
    preview_findings: tuple[dict[str, Any], ...]
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "pptx_path": str(self.pptx_path),
            "pptx_sha256": self.pptx_sha256,
            "profile": {
                "minimum_average_objects": self.profile.minimum_average_objects,
                "minimum_layout_signatures": self.profile.minimum_layout_signatures,
                "minimum_media_count": self.profile.minimum_media_count,
                "minimum_media_bytes": self.profile.minimum_media_bytes,
                "minimum_chart_count": self.profile.minimum_chart_count,
                "minimum_group_count": self.profile.minimum_group_count,
                "minimum_decorative_primitives": self.profile.minimum_decorative_primitives,
            },
            "complexity": self.complexity.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
            "preview_findings": list(self.preview_findings),
            "passed": self.passed,
        }


def _parse_xml(payload: bytes, path: str) -> ET.Element:
    try:
        return ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ReferenceQualityError(f"invalid XML part {path}: {exc}") from exc


def inspect_reference_complexity(pptx_path: Path | str) -> ReferenceComplexity:
    source = Path(pptx_path).resolve()
    if not source.is_file():
        raise ReferenceQualityError(f"PPTX does not exist: {source}")
    try:
        archive = zipfile.ZipFile(source)
    except zipfile.BadZipFile as exc:
        raise ReferenceQualityError(f"PPTX is not a valid OOXML package: {source}") from exc
    with archive:
        names = set(archive.namelist())
        slide_names = sorted(
            (name for name in names if _SLIDE.fullmatch(name)),
            key=lambda name: int(_SLIDE.fullmatch(name).group(1)),  # type: ignore[union-attr]
        )
        if not slide_names:
            raise ReferenceQualityError("PPTX contains no slide parts")
        shape_count = picture_count = graphic_frame_count = 0
        group_count = connector_count = gradient_count = crop_count = 0
        signatures: list[str] = []
        objects_per_slide: list[int] = []
        for slide_name in slide_names:
            root = _parse_xml(archive.read(slide_name), slide_name)
            counts = (
                len(root.findall(f".//{{{PML}}}sp")),
                len(root.findall(f".//{{{PML}}}pic")),
                len(root.findall(f".//{{{PML}}}graphicFrame")),
                len(root.findall(f".//{{{PML}}}grpSp")),
                len(root.findall(f".//{{{PML}}}cxnSp")),
            )
            shape_count += counts[0]
            picture_count += counts[1]
            graphic_frame_count += counts[2]
            group_count += counts[3]
            connector_count += counts[4]
            gradient_count += len(root.findall(f".//{{{AML}}}gradFill"))
            crop_count += len(root.findall(f".//{{{AML}}}srcRect"))
            signatures.append(":".join(str(value) for value in counts))
            objects_per_slide.append(sum(counts))
        chart_count = sum(
            1 for name in names if re.fullmatch(r"ppt/charts/chart\d+\.xml", name)
        )
        embedded_workbook_count = sum(
            1
            for name in names
            if name.startswith("ppt/embeddings/") and name.casefold().endswith(".xlsx")
        )
        media_names = [
            name
            for name in names
            if name.startswith("ppt/media/") and not name.endswith("/")
        ]
        media_bytes = sum(archive.getinfo(name).file_size for name in media_names)
    total_objects = (
        shape_count
        + picture_count
        + graphic_frame_count
        + group_count
        + connector_count
    )
    return ReferenceComplexity(
        slide_count=len(slide_names),
        shape_count=shape_count,
        picture_count=picture_count,
        graphic_frame_count=graphic_frame_count,
        group_count=group_count,
        connector_count=connector_count,
        chart_count=chart_count,
        embedded_workbook_count=embedded_workbook_count,
        media_count=len(media_names),
        media_bytes=media_bytes,
        gradient_count=gradient_count,
        crop_count=crop_count,
        average_objects_per_slide=round(total_objects / len(slide_names), 3),
        layout_signature_count=len(set(signatures)),
        layout_signatures=tuple(signatures),
        objects_per_slide=tuple(objects_per_slide),
    )


def assess_generated_visual_quality(
    pptx_path: Path | str,
    *,
    profile: GeneratedVisualQualityProfile = GeneratedVisualQualityProfile(),
) -> tuple[ReferenceComplexity, tuple[ReferenceQualityFinding, ...]]:
    """Measure a generated deck's visual floor without requiring specific media.

    The generated route may legitimately use charts, diagrams, images, or pure
    editable vector composition.  Its gate therefore measures page richness,
    layout variation, and how broadly that richness is distributed, rather
    than requiring the exact asset mix of a physical TemplatePack.
    """

    complexity = inspect_reference_complexity(pptx_path)
    rich_slide_count = sum(
        value >= profile.rich_slide_object_floor
        for value in complexity.objects_per_slide
    )
    rich_slide_ratio = round(rich_slide_count / complexity.slide_count, 3)
    checks = (
        (
            "GENERATED_VISUAL_OBJECT_FLOOR",
            complexity.average_objects_per_slide,
            profile.minimum_average_objects,
            "average editable/visual object count against the generated-deck floor",
        ),
        (
            "GENERATED_LAYOUT_VARIATION_FLOOR",
            complexity.layout_signature_count,
            profile.minimum_layout_signatures,
            "distinct page-composition count against the generated-deck floor",
        ),
        (
            "GENERATED_RICH_SLIDE_RATIO_FLOOR",
            rich_slide_ratio,
            profile.minimum_rich_slide_ratio,
            "rich-slide coverage against the generated-deck floor",
        ),
    )
    findings = tuple(
        ReferenceQualityFinding(
            code=code,
            severity=("hard-gate" if metric < threshold else "info"),
            message=message,
            metric=metric,
            threshold=threshold,
        )
        for code, metric, threshold, message in checks
    )
    return complexity, findings


def assess_reference_grade_quality(
    pptx_path: Path | str,
    *,
    png_paths: Iterable[Path | str] = (),
    expected_slide_count: int | None = None,
    profile: ReferenceQualityProfile = ReferenceQualityProfile(),
) -> ReferenceQualityReport:
    source = Path(pptx_path).resolve()
    complexity = inspect_reference_complexity(source)
    checks = (
        (
            "VISUAL_OBJECT_FLOOR",
            complexity.average_objects_per_slide,
            profile.minimum_average_objects,
            "average editable/visual object count is below the reference-grade floor",
        ),
        (
            "LAYOUT_VARIATION_FLOOR",
            complexity.layout_signature_count,
            profile.minimum_layout_signatures,
            "too few distinct page-composition signatures",
        ),
        (
            "MEDIA_COUNT_FLOOR",
            complexity.media_count,
            profile.minimum_media_count,
            "too few packaged visual media assets",
        ),
        (
            "MEDIA_DEPTH_FLOOR",
            complexity.media_bytes,
            profile.minimum_media_bytes,
            "packaged visual assets are too shallow for the selected reference profile",
        ),
        (
            "EDITABLE_CHART_FLOOR",
            complexity.chart_count,
            profile.minimum_chart_count,
            "editable chart count is below the selected reference profile",
        ),
        (
            "GROUP_COMPOSITION_FLOOR",
            complexity.group_count,
            profile.minimum_group_count,
            "no meaningful grouped/vector composition survived generation",
        ),
        (
            "DECORATIVE_PRIMITIVE_FLOOR",
            complexity.decorative_primitives,
            profile.minimum_decorative_primitives,
            "decorative/vector/crop primitives are below the reference-grade floor",
        ),
    )
    findings = tuple(
        ReferenceQualityFinding(code, "hard-gate", message, metric, threshold)
        for code, metric, threshold, message in checks
        if metric < threshold
    )
    preview_paths = tuple(Path(path) for path in png_paths)
    preview = tuple(
        item.to_dict()
        for item in inspect_preview_images(
            preview_paths,
            expected_slide_count=(
                complexity.slide_count
                if expected_slide_count is None
                else expected_slide_count
            ),
        )
    ) if preview_paths else ()
    preview_hard_gates = any(item["severity"] == "hard-gate" for item in preview)
    return ReferenceQualityReport(
        pptx_path=source,
        pptx_sha256=sha256_file(source),
        profile=profile,
        complexity=complexity,
        findings=findings,
        preview_findings=preview,
        passed=not findings and not preview_hard_gates,
    )


def write_reference_quality_report(
    report: ReferenceQualityReport,
    path: Path | str,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, candidate_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(report.to_dict(), handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(candidate_name, output)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        Path(candidate_name).unlink(missing_ok=True)
        raise
    return output


__all__ = [
    "ReferenceComplexity",
    "GeneratedVisualQualityProfile",
    "ReferenceQualityError",
    "ReferenceQualityFinding",
    "ReferenceQualityProfile",
    "ReferenceQualityReport",
    "assess_reference_grade_quality",
    "assess_generated_visual_quality",
    "inspect_reference_complexity",
    "write_reference_quality_report",
]
