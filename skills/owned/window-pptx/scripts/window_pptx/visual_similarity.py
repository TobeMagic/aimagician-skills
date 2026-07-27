"""Fail-closed masked rendered similarity for TemplatePack preservation."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .template_geometry import VisualMask, masks_for_slide


class VisualSimilarityError(ValueError):
    """Rendered similarity inputs are incomparable or unsafe."""


@dataclass(frozen=True)
class SlideVisualSimilarity:
    slide: int
    similarity: float
    changed_pixel_ratio: float
    mask_coverage: float
    unmasked_pixels: int
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "slide": self.slide,
            "similarity": self.similarity,
            "changed_pixel_ratio": self.changed_pixel_ratio,
            "mask_coverage": self.mask_coverage,
            "unmasked_pixels": self.unmasked_pixels,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class VisualSimilarityReport:
    source_renderer_fingerprint: str
    candidate_renderer_fingerprint: str
    minimum_similarity: float
    maximum_changed_pixel_ratio: float
    channel_tolerance: int
    maximum_mask_coverage: float
    slides: tuple[SlideVisualSimilarity, ...]
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "source_renderer_fingerprint": self.source_renderer_fingerprint,
            "candidate_renderer_fingerprint": self.candidate_renderer_fingerprint,
            "profile": {
                "minimum_similarity": self.minimum_similarity,
                "maximum_changed_pixel_ratio": self.maximum_changed_pixel_ratio,
                "channel_tolerance": self.channel_tolerance,
                "maximum_mask_coverage": self.maximum_mask_coverage,
            },
            "slides": [slide.to_dict() for slide in self.slides],
            "passed": self.passed,
        }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def _validate_profile(
    minimum_similarity: float,
    maximum_changed_pixel_ratio: float,
    channel_tolerance: int,
    maximum_mask_coverage: float,
) -> None:
    for name, value in (
        ("minimum_similarity", minimum_similarity),
        ("maximum_changed_pixel_ratio", maximum_changed_pixel_ratio),
        ("maximum_mask_coverage", maximum_mask_coverage),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or not 0 <= float(value) <= 1
        ):
            raise VisualSimilarityError(f"{name} must be between 0 and 1")
    if type(channel_tolerance) is not int or not 0 <= channel_tolerance <= 255:
        raise VisualSimilarityError("channel_tolerance must be an integer from 0 to 255")


def _mask_bitmap(
    size: tuple[int, int],
    masks: Iterable[VisualMask],
    *,
    maximum_mask_coverage: float,
):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:  # pragma: no cover - dependency is environment-specific
        raise VisualSimilarityError("Pillow is required for visual similarity") from exc
    width, height = size
    bitmap = Image.new("1", size, 0)
    draw = ImageDraw.Draw(bitmap)
    count = 0
    for mask in masks:
        values = (mask.x, mask.y, mask.width, mask.height, mask.padding)
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in values
        ):
            raise VisualSimilarityError("mask geometry must be finite")
        if (
            mask.x < 0
            or mask.y < 0
            or mask.width <= 0
            or mask.height <= 0
            or mask.padding < 0
            or mask.x + mask.width > 1
            or mask.y + mask.height > 1
        ):
            raise VisualSimilarityError("mask geometry must be normalized")
        left = max(0, math.floor((mask.x - mask.padding) * width))
        top = max(0, math.floor((mask.y - mask.padding) * height))
        right = min(width - 1, math.ceil((mask.x + mask.width + mask.padding) * width) - 1)
        bottom = min(
            height - 1,
            math.ceil((mask.y + mask.height + mask.padding) * height) - 1,
        )
        draw.rectangle((left, top, right, bottom), fill=1)
        count += 1
    if count == 0:
        raise VisualSimilarityError("missing trusted masks")
    masked_pixels = sum(1 for value in bitmap.getdata() if value)
    coverage = masked_pixels / (width * height)
    if coverage > maximum_mask_coverage:
        raise VisualSimilarityError(
            f"trusted mask coverage {coverage:.6f} exceeds "
            f"{maximum_mask_coverage:.6f}"
        )
    return bitmap, coverage


def compare_masked_previews(
    source_pages: Sequence[Path],
    candidate_pages: Sequence[Path],
    masks: Iterable[VisualMask],
    *,
    source_renderer_fingerprint: str,
    candidate_renderer_fingerprint: str,
    minimum_similarity: float = 0.98,
    maximum_changed_pixel_ratio: float = 0.02,
    channel_tolerance: int = 8,
    maximum_mask_coverage: float = 0.80,
) -> VisualSimilarityReport:
    """Compare same-renderer pages outside trusted, source-derived masks."""

    _validate_profile(
        minimum_similarity,
        maximum_changed_pixel_ratio,
        channel_tolerance,
        maximum_mask_coverage,
    )
    if (
        not source_renderer_fingerprint
        or source_renderer_fingerprint != candidate_renderer_fingerprint
    ):
        raise VisualSimilarityError("renderer fingerprint mismatch")
    if not source_pages or len(source_pages) != len(candidate_pages):
        raise VisualSimilarityError("page count mismatch")
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise VisualSimilarityError("Pillow is required for visual similarity") from exc
    mask_values = tuple(masks)
    slides: list[SlideVisualSimilarity] = []
    for index, (source_path, candidate_path) in enumerate(
        zip(source_pages, candidate_pages),
        start=1,
    ):
        with Image.open(source_path) as raw_source, Image.open(candidate_path) as raw_candidate:
            source = raw_source.convert("RGB")
            candidate = raw_candidate.convert("RGB")
            if source.size != candidate.size:
                raise VisualSimilarityError(
                    f"page dimensions mismatch on slide {index}: "
                    f"{source.size} != {candidate.size}"
                )
            bitmap, coverage = _mask_bitmap(
                source.size,
                masks_for_slide(mask_values, index),
                maximum_mask_coverage=maximum_mask_coverage,
            )
            source_pixels = source.load()
            candidate_pixels = candidate.load()
            mask_pixels = bitmap.load()
            total_difference = 0
            changed = 0
            unmasked = 0
            width, height = source.size
            for y in range(height):
                for x in range(width):
                    if mask_pixels[x, y]:
                        continue
                    unmasked += 1
                    source_pixel = source_pixels[x, y]
                    candidate_pixel = candidate_pixels[x, y]
                    differences = tuple(
                        abs(source_pixel[channel] - candidate_pixel[channel])
                        for channel in range(3)
                    )
                    total_difference += sum(differences)
                    if any(value > channel_tolerance for value in differences):
                        changed += 1
            if unmasked == 0:
                raise VisualSimilarityError(f"slide {index} has no unmasked pixels")
            similarity = 1.0 - total_difference / (255 * 3 * unmasked)
            changed_ratio = changed / unmasked
            passed = (
                similarity >= minimum_similarity
                and changed_ratio <= maximum_changed_pixel_ratio
            )
            slides.append(
                SlideVisualSimilarity(
                    slide=index,
                    similarity=round(similarity, 9),
                    changed_pixel_ratio=round(changed_ratio, 9),
                    mask_coverage=round(coverage, 9),
                    unmasked_pixels=unmasked,
                    passed=passed,
                )
            )
    return VisualSimilarityReport(
        source_renderer_fingerprint=source_renderer_fingerprint,
        candidate_renderer_fingerprint=candidate_renderer_fingerprint,
        minimum_similarity=float(minimum_similarity),
        maximum_changed_pixel_ratio=float(maximum_changed_pixel_ratio),
        channel_tolerance=channel_tolerance,
        maximum_mask_coverage=float(maximum_mask_coverage),
        slides=tuple(slides),
        passed=all(slide.passed for slide in slides),
    )
