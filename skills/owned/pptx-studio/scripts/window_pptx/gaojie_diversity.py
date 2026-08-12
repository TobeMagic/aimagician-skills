"""Deterministic preview fingerprinting and diversity-first selection."""

from __future__ import annotations

import hashlib
import io
import math
import statistics
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping


class PreviewError(ValueError):
    """Preview bytes are not a safe, usable image."""


@dataclass(frozen=True)
class PreviewFingerprint:
    sha256: str
    width: int
    height: int
    aspect_ratio: float
    dhash: str
    color_histogram: tuple[float, ...]
    entropy: float
    edge_density: float
    quality: float

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["color_histogram"] = list(self.color_histogram)
        return value


def _entropy(histogram: Iterable[int], total: int) -> float:
    return -sum(
        (count / total) * math.log2(count / total)
        for count in histogram
        if count
    )


def fingerprint_preview(payload: bytes) -> PreviewFingerprint:
    """Validate image bytes and return a compact deterministic fingerprint."""

    if not payload:
        raise PreviewError("preview is empty")
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:  # pragma: no cover - Window-PPTX requires Pillow
        raise PreviewError("Pillow is required for preview fingerprints") from exc
    try:
        with Image.open(io.BytesIO(payload)) as raw:
            raw.verify()
        with Image.open(io.BytesIO(payload)) as raw:
            width, height = raw.size
            if width < 32 or height < 32 or width * height > 40_000_000:
                raise PreviewError("preview dimensions are outside safe limits")
            rgb = raw.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise PreviewError("preview is not a valid image") from exc

    sample = rgb.resize((64, 64))
    grayscale = sample.convert("L")
    gray_histogram = grayscale.histogram()
    entropy = _entropy(gray_histogram, 64 * 64)

    dhash_image = grayscale.resize((9, 8))
    pixels = list(dhash_image.getdata())
    bits = 0
    for row in range(8):
        for column in range(8):
            bits = (bits << 1) | int(
                pixels[row * 9 + column] > pixels[row * 9 + column + 1]
            )

    histogram: list[float] = []
    channels = sample.split()
    for channel in channels:
        values = channel.histogram()
        for bucket in range(8):
            histogram.append(
                sum(values[bucket * 32 : (bucket + 1) * 32]) / (64 * 64)
            )

    edge_count = 0
    comparisons = 0
    gray_pixels = list(grayscale.getdata())
    for y in range(64):
        for x in range(64):
            current = gray_pixels[y * 64 + x]
            if x + 1 < 64:
                comparisons += 1
                edge_count += abs(current - gray_pixels[y * 64 + x + 1]) >= 24
            if y + 1 < 64:
                comparisons += 1
                edge_count += abs(current - gray_pixels[(y + 1) * 64 + x]) >= 24
    edge_density = edge_count / comparisons
    resolution_quality = min(1.0, math.log2(width * height) / 20.0)
    quality = (
        0.45 * resolution_quality
        + 0.35 * min(1.0, entropy / 8.0)
        + 0.20 * min(1.0, edge_density * 4.0)
    )
    return PreviewFingerprint(
        sha256=hashlib.sha256(payload).hexdigest(),
        width=width,
        height=height,
        aspect_ratio=round(width / height, 6),
        dhash=f"{bits:016x}",
        color_histogram=tuple(round(value, 8) for value in histogram),
        entropy=round(entropy, 8),
        edge_density=round(edge_density, 8),
        quality=round(quality, 8),
    )


def fingerprint_distance(
    left: PreviewFingerprint,
    right: PreviewFingerprint,
) -> float:
    """Return normalized visual distance in the closed interval [0, 1]."""

    hamming = (int(left.dhash, 16) ^ int(right.dhash, 16)).bit_count() / 64
    histogram = sum(
        abs(a - b) for a, b in zip(left.color_histogram, right.color_histogram)
    ) / 6
    entropy = min(1.0, abs(left.entropy - right.entropy) / 8)
    edge = min(1.0, abs(left.edge_density - right.edge_density))
    return round(
        min(1.0, 0.55 * hamming + 0.30 * histogram + 0.10 * entropy + 0.05 * edge),
        8,
    )


def median_nearest_neighbor(
    fingerprints: Iterable[PreviewFingerprint],
) -> float:
    values = tuple(fingerprints)
    if len(values) < 2:
        return 0.0
    nearest = [
        min(
            fingerprint_distance(value, other)
            for other in values
            if other is not value
        )
        for value in values
    ]
    return round(statistics.median(nearest), 8)


def select_diverse(
    items: Mapping[str, PreviewFingerprint],
    *,
    limit: int = 12,
    near_duplicate_distance: float = 0.08,
) -> dict[str, object]:
    """Select a deterministic farthest-first subset and report baseline gain."""

    if type(limit) is not int or limit < 1:
        raise PreviewError("selection limit must be a positive integer")
    if not 0 <= near_duplicate_distance <= 1:
        raise PreviewError("near-duplicate distance must be between zero and one")

    canonical: dict[str, tuple[str, PreviewFingerprint]] = {}
    for item_id, fingerprint in sorted(items.items()):
        current = canonical.get(fingerprint.sha256)
        if current is None or item_id < current[0]:
            canonical[fingerprint.sha256] = (item_id, fingerprint)
    candidates = sorted(canonical.values(), key=lambda value: value[0])
    if not candidates:
        return {
            "selected_item_ids": [],
            "exact_duplicate_count": 0,
            "near_duplicate_suppressed_count": 0,
            "baseline_median_nearest_neighbor": 0.0,
            "selected_median_nearest_neighbor": 0.0,
            "selection_gain": 0.0,
            "seed_candidates_evaluated": 0,
            "rule_version": "gaojie-diversity.v2",
        }

    cache: dict[tuple[str, str], float] = {}

    def distance(
        left: tuple[str, PreviewFingerprint],
        right: tuple[str, PreviewFingerprint],
    ) -> float:
        key = tuple(sorted((left[0], right[0])))
        if key not in cache:
            cache[key] = fingerprint_distance(left[1], right[1])
        return cache[key]

    baseline = candidates[: min(limit, len(candidates))]
    seed_pool = sorted(
        candidates,
        key=lambda value: (-value[1].quality, value[0]),
    )[: min(12, len(candidates))]
    first = candidates[0]
    if first not in seed_pool:
        seed_pool.append(first)

    alternatives: list[tuple[
        float,
        float,
        float,
        list[tuple[str, PreviewFingerprint]],
        int,
    ]] = []
    for seed in seed_pool:
        selected = [seed]
        remaining = [value for value in candidates if value[0] != seed[0]]
        suppressed = 0
        while remaining and len(selected) < limit:
            ranked = sorted(
                (
                    (
                        min(distance(candidate, chosen) for chosen in selected),
                        candidate,
                    )
                    for candidate in remaining
                ),
                key=lambda value: (-value[0], value[1][0]),
            )
            best_distance, best = ranked[0]
            remaining.remove(best)
            if best_distance < near_duplicate_distance:
                suppressed += 1 + len(remaining)
                break
            selected.append(best)
        nearest = median_nearest_neighbor(value[1] for value in selected)
        pairwise = sum(
            distance(selected[left], selected[right])
            for left in range(len(selected))
            for right in range(left + 1, len(selected))
        )
        mean_quality = statistics.fmean(value[1].quality for value in selected)
        alternatives.append(
            (nearest, pairwise, mean_quality, selected, suppressed)
        )

    _, _, _, selected, suppressed = max(
        alternatives,
        key=lambda value: (
            value[0],
            value[1],
            value[2],
            tuple(item[0] for item in value[3]),
        ),
    )
    selected_metric = median_nearest_neighbor(value[1] for value in selected)
    baseline_metric = median_nearest_neighbor(value[1] for value in baseline)
    return {
        "selected_item_ids": [value[0] for value in selected],
        "exact_duplicate_count": len(items) - len(candidates),
        "near_duplicate_suppressed_count": suppressed,
        "baseline_median_nearest_neighbor": baseline_metric,
        "selected_median_nearest_neighbor": selected_metric,
        "selection_gain": round(selected_metric - baseline_metric, 8),
        "seed_candidates_evaluated": len(seed_pool),
        "rule_version": "gaojie-diversity.v2",
    }
