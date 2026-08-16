"""Deterministic PNG preview checks for density, crop risk, and repetition."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Any, Iterable

try:
    from PIL import Image, ImageChops, ImageStat
except ImportError:  # Optional: COM/package QA remains available without Pillow.
    Image = ImageChops = ImageStat = None  # type: ignore[assignment]

from .quality_v2 import QualityFindingV2
from .render_plan import RenderPlan, RenderObject
from .text_layout import estimate_text_layout


def inspect_render_plan_delivery(plan: RenderPlan) -> tuple[QualityFindingV2, ...]:
    """Reject deterministic text/layout defects before candidate promotion.

    These checks deliberately target defects that a weak model should never be
    allowed to pass downstream: empty governed text slots, fixed-length title
    truncation, unresolved placeholder language, estimated overflow, and exact
    duplicate text blocks on one slide.  Layout compilation is the automatic
    repair stage; an unresolved defect therefore fails closed.
    """

    findings: list[QualityFindingV2] = []
    placeholders = re.compile(r"\b(?:lorem ipsum|placeholder|tbd|todo)\b", re.I)
    for slide in plan.slides:
        seen: dict[str, str] = {}
        for item in slide.objects:
            if item.kind not in {"text", "shape"} or item.component in {
                "decoration",
                "accent",
            }:
                continue
            text = (item.text or "").strip()
            if not text:
                findings.append(
                    QualityFindingV2(
                        "render",
                        "EMPTY_GOVERNED_TEXT_SLOT",
                        "hard-gate",
                        slide.source_id,
                        item.id,
                        "a governed native text slot has no meaningful content",
                        repairable=True,
                        source_stage="render-plan-delivery",
                    )
                )
                continue
            if item.component == "title" and re.search(r"(?:…|\.\.\.)\s*$", text):
                findings.append(
                    QualityFindingV2(
                        "render",
                        "TITLE_TRUNCATED",
                        "hard-gate",
                        slide.source_id,
                        item.id,
                        "title ends with a truncation marker instead of a complete claim",
                        metric=len(text),
                        repairable=True,
                        source_stage="render-plan-delivery",
                    )
                )
            if placeholders.search(text):
                findings.append(
                    QualityFindingV2(
                        "render",
                        "UNRESOLVED_PLACEHOLDER_CONTENT",
                        "hard-gate",
                        slide.source_id,
                        item.id,
                        "native editable text contains unresolved placeholder language",
                        repairable=True,
                        source_stage="render-plan-delivery",
                    )
                )
            normalized = "".join(text.casefold().split())
            estimate = estimate_text_layout(
                text,
                width_in=item.width,
                height_in=item.height,
                font_size_pt=item.font_size_pt,
            )
            if not estimate.fits:
                findings.append(
                    QualityFindingV2(
                        "render",
                        "TEXT_CAPACITY_EXCEEDED",
                        "hard-gate",
                        slide.source_id,
                        item.id,
                        "text exceeds the deterministic editable-slot capacity estimate",
                        metric=estimate.required_lines,
                        threshold=estimate.available_lines,
                        repairable=True,
                        source_stage="render-plan-delivery",
                    )
                )
            if item.component != "footer" and len(normalized) >= 6:
                previous = seen.get(normalized)
                if previous is not None:
                    findings.append(
                        QualityFindingV2(
                            "render",
                            "DUPLICATE_SLIDE_TEXT",
                            "hard-gate",
                            slide.source_id,
                            item.id,
                            "the same text is repeated in multiple governed objects",
                            path=previous,
                            repairable=True,
                            source_stage="render-plan-delivery",
                        )
                    )
                else:
                    seen[normalized] = item.id
    return tuple(findings)


def _normalized_preview(path: Path) -> Any:
    with Image.open(path) as image:
        return image.convert("RGB").resize((160, 90))


def _background(image: Any) -> tuple[int, int, int]:
    """Estimate the page field from the perimeter, not four fragile pixels.

    Branded masters often place a one-pixel rule or accent bar on a page edge.
    The old four-corner median could therefore select the accent as the
    background and classify an almost-empty white page as 99% foreground.
    Quantized perimeter voting is stable for both light and dark masters while
    treating narrow edge decoration as decoration.
    """

    width, height = image.size
    pixels = image.load()
    perimeter = [
        *(pixels[x, 0] for x in range(width)),
        *(pixels[x, height - 1] for x in range(width)),
        *(pixels[0, y] for y in range(1, height - 1)),
        *(pixels[width - 1, y] for y in range(1, height - 1)),
    ]
    bins = [tuple(channel // 8 for channel in color) for color in perimeter]
    selected_bin, _count = Counter(bins).most_common(1)[0]
    selected = [
        color
        for color, quantized in zip(perimeter, bins)
        if quantized == selected_bin
    ]
    return tuple(
        round(sum(color[channel] for color in selected) / len(selected))
        for channel in range(3)
    )


def _content_mask(image: Any) -> Any:
    background = Image.new("RGB", image.size, _background(image))
    difference = ImageChops.difference(image, background).convert("L")
    return difference.point(lambda value: 255 if value >= 18 else 0)


def _foreground_components(mask: Any) -> tuple[tuple[int, tuple[int, int, int, int]], ...]:
    """Return 4-connected foreground component areas and exclusive bounds."""

    width, height = mask.size
    pixels = mask.load()
    visited = bytearray(width * height)
    components: list[tuple[int, tuple[int, int, int, int]]] = []
    for y in range(height):
        for x in range(width):
            offset = y * width + x
            if visited[offset] or not pixels[x, y]:
                continue
            visited[offset] = 1
            stack = [(x, y)]
            area = 0
            left = right = x
            top = bottom = y
            while stack:
                current_x, current_y = stack.pop()
                area += 1
                left = min(left, current_x)
                right = max(right, current_x)
                top = min(top, current_y)
                bottom = max(bottom, current_y)
                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if not (0 <= next_x < width and 0 <= next_y < height):
                        continue
                    next_offset = next_y * width + next_x
                    if visited[next_offset] or not pixels[next_x, next_y]:
                        continue
                    visited[next_offset] = 1
                    stack.append((next_x, next_y))
            components.append((area, (left, top, right + 1, bottom + 1)))
    return tuple(components)


def _component_edge_distance(
    bounds: tuple[int, int, int, int],
    *,
    width: int,
    height: int,
) -> int:
    left, top, right, bottom = bounds
    return min(left, top, width - right, height - bottom)


def _is_thin_edge_decoration(
    area: int,
    bounds: tuple[int, int, int, int],
    *,
    width: int,
    height: int,
) -> bool:
    """Recognize only solid, line-like perimeter rails and ticks.

    The preview cannot recover RenderPlan component identity, so this
    exception is intentionally geometric.  It admits a component only when
    it is a nearly solid line no more than two normalized pixels thick.  Text,
    images, and filled panels that reach the edge extend farther inward (or
    have irregular glyph geometry) and remain reportable.
    """

    if _component_edge_distance(bounds, width=width, height=height) > 1:
        return False
    left, top, right, bottom = bounds
    component_width = right - left
    component_height = bottom - top
    short_edge = min(component_width, component_height)
    long_edge = max(component_width, component_height)
    if short_edge > 2 or long_edge < 6 or long_edge < short_edge * 3:
        return False
    rectangularity = area / (component_width * component_height)
    return rectangularity >= 0.9


def _non_decorative_edge_distance(mask: Any) -> int | None:
    width, height = mask.size
    distances = []
    for area, bounds in _foreground_components(mask):
        distance = _component_edge_distance(
            bounds,
            width=width,
            height=height,
        )
        if distance > 1:
            continue
        if _is_thin_edge_decoration(
            area,
            bounds,
            width=width,
            height=height,
        ):
            continue
        distances.append(distance)
    return min(distances) if distances else None


def inspect_preview_images(
    paths: Iterable[Path | str],
    *,
    slide_ids: Iterable[str] = (),
    expected_slide_count: int | None = None,
) -> tuple[QualityFindingV2, ...]:
    """Inspect exported previews without changing the rendered candidate."""

    image_paths = tuple(Path(path) for path in paths)
    ids = tuple(slide_ids)
    expected = len(ids) if expected_slide_count is None and ids else (
        len(image_paths) if expected_slide_count is None else expected_slide_count
    )
    if expected < 0:
        raise ValueError("expected_slide_count cannot be negative")
    missing_findings = [
        QualityFindingV2(
            "preview",
            "PREVIEW_EXPORT_MISSING",
            "hard-gate",
            ids[index] if index < len(ids) else str(index + 1),
            None,
            "an expected slide preview was not exported",
            path=None,
            metric=len(image_paths),
            threshold=expected,
            repairable=False,
            source_stage="png-preview",
        )
        for index in range(len(image_paths), expected)
    ]
    if Image is None or ImageChops is None or ImageStat is None:
        unavailable = QualityFindingV2(
            "preview",
            "PREVIEW_INSPECTOR_UNAVAILABLE",
            "hard-gate" if expected else "info",
            None,
            None,
            "Pillow is not installed; expected PNG previews cannot be inspected"
            if expected
            else "Pillow is not installed; no preview inspection was requested",
            repairable=False,
            source_stage="png-preview",
        )
        return (*missing_findings, unavailable)
    findings: list[QualityFindingV2] = list(missing_findings)
    previews: list[tuple[int, Any]] = []
    for index, path in enumerate(image_paths):
        slide_id = ids[index] if index < len(ids) else str(index + 1)
        try:
            preview = _normalized_preview(path)
        except (OSError, ValueError) as exc:
            findings.append(
                QualityFindingV2(
                    "preview",
                    "PREVIEW_UNREADABLE",
                    "hard-gate",
                    slide_id,
                    None,
                    f"preview cannot be inspected: {exc}",
                    path=str(path),
                    repairable=False,
                    source_stage="png-preview",
                )
            )
            continue
        previews.append((index, preview))
        mask = _content_mask(preview)
        histogram = mask.histogram()
        content_ratio = histogram[255] / (preview.width * preview.height)
        if content_ratio < 0.015:
            findings.append(
                QualityFindingV2(
                    "preview",
                    "PAGE_VISUALLY_EMPTY",
                    "hard-gate",
                    slide_id,
                    None,
                    "preview contains almost no foreground information",
                    path=str(path),
                    metric=round(content_ratio, 4),
                    threshold=0.015,
                    repairable=True,
                    source_stage="png-preview",
                )
            )
        elif content_ratio > 0.72:
            findings.append(
                QualityFindingV2(
                    "preview",
                    "PAGE_VISUALLY_DENSE",
                    "warning",
                    slide_id,
                    None,
                    "foreground coverage is unusually high",
                    path=str(path),
                    metric=round(content_ratio, 4),
                    threshold=0.72,
                    repairable=True,
                    source_stage="png-preview",
                )
            )
        edge = _non_decorative_edge_distance(mask)
        if edge is not None and content_ratio > 0.02:
            findings.append(
                QualityFindingV2(
                    "preview",
                    "FOREGROUND_TOUCHES_EDGE",
                    "warning",
                    slide_id,
                    None,
                    "non-background content reaches the preview edge",
                    path=str(path),
                    metric=edge,
                    threshold=2,
                    repairable=True,
                    source_stage="png-preview",
                )
            )
    for preview_index in range(1, len(previews)):
        previous_source_index, previous = previews[preview_index - 1]
        source_index, current = previews[preview_index]
        if source_index != previous_source_index + 1:
            continue
        difference = ImageChops.difference(previous, current)
        mean = sum(ImageStat.Stat(difference).mean) / (3 * 255)
        if mean < 0.008:
            slide_id = (
                ids[source_index]
                if source_index < len(ids)
                else str(source_index + 1)
            )
            findings.append(
                QualityFindingV2(
                    "preview",
                    "ADJACENT_SLIDES_NEAR_DUPLICATE",
                    "hard-gate",
                    slide_id,
                    None,
                    "adjacent slide previews are nearly identical",
                    path=str(image_paths[source_index]),
                    metric=round(mean, 5),
                    threshold=0.008,
                    repairable=True,
                    source_stage="png-preview",
                )
            )
    return tuple(findings)


__all__ = ["inspect_preview_images", "inspect_render_plan_delivery"]
