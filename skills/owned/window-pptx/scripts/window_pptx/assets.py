"""Deterministic asset-policy and safe asset selection."""

from __future__ import annotations

import json
import math
from datetime import date
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


COMPONENTS_PATH = (
    Path(__file__).resolve().parents[2] / "registries" / "components.json"
)


@dataclass(frozen=True)
class AssetPolicy:
    crop_mode: str
    allow_stretch: bool
    required_provenance: tuple[str, ...]
    icon_style_scope: str
    missing_asset_fallback: str
    minimum_quality: float
    minimum_raster_short_edge_px: int


@dataclass(frozen=True)
class AssetIntent:
    kind: str
    style: str | None = None
    aspect_ratio: float | None = None


@dataclass(frozen=True)
class AssetRecord:
    id: str
    kind: str
    style: str | None
    aspect_ratio: float | None
    quality: float
    source: str | None
    license: str | None
    retrieved_at: str | None
    width_px: int | None = None
    height_px: int | None = None
    icon_family: str | None = None


@dataclass(frozen=True)
class AssetChoice:
    asset_id: str | None
    crop_mode: str
    fallback: str | None
    reason: str | None
    rejected: dict[str, str]
    icon_family: str | None


@dataclass
class AssetSession:
    """Deck-scoped selector that locks one icon family after first use."""

    icon_family: str | None = None

    def choose(
        self, intent: AssetIntent, records: Iterable[AssetRecord]
    ) -> AssetChoice:
        choice = choose_asset(
            intent, records, active_icon_family=self.icon_family
        )
        if intent.kind == "icon" and choice.icon_family is not None:
            self.icon_family = choice.icon_family
        return choice


def load_asset_policy(path: Path | str | None = None) -> AssetPolicy:
    registry_path = Path(path) if path is not None else COMPONENTS_PATH
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        raise ValueError("unsupported component registry version")
    raw = payload["asset_policy"]
    return AssetPolicy(
        crop_mode=raw["crop_mode"],
        allow_stretch=raw["allow_stretch"],
        required_provenance=tuple(raw["required_provenance"]),
        icon_style_scope=raw["icon_style_scope"],
        missing_asset_fallback=raw["missing_asset_fallback"],
        minimum_quality=float(raw["minimum_quality"]),
        minimum_raster_short_edge_px=int(raw["minimum_raster_short_edge_px"]),
    )


def choose_asset(
    intent: AssetIntent,
    records: Iterable[AssetRecord],
    *,
    active_icon_family: str | None = None,
) -> AssetChoice:
    """Choose the best safe asset with stable quality/aspect/ID ordering."""

    policy = load_asset_policy()
    if intent.aspect_ratio is not None and (
        not math.isfinite(intent.aspect_ratio) or intent.aspect_ratio <= 0
    ):
        raise ValueError("intent aspect_ratio must be finite and positive")
    materialized = tuple(records)
    id_counts: dict[str, int] = {}
    for record in materialized:
        id_counts[record.id] = id_counts.get(record.id, 0) + 1
    accepted: list[AssetRecord] = []
    rejected: dict[str, str] = {}
    for record in materialized:
        if not record.id.strip():
            rejected[record.id] = "MISSING_ID"
        elif id_counts[record.id] > 1:
            rejected[record.id] = "DUPLICATE_ID"
        elif not math.isfinite(record.quality) or record.quality < policy.minimum_quality:
            rejected[record.id] = "INVALID_QUALITY"
        elif not all(
            isinstance(value, str) and bool(value.strip())
            for value in (record.source, record.license, record.retrieved_at)
        ):
            rejected[record.id] = "MISSING_PROVENANCE"
        elif not _valid_date(record.retrieved_at):
            rejected[record.id] = "INVALID_RETRIEVED_AT"
        elif record.license.casefold().strip() in {"unknown", "unverified"}:
            rejected[record.id] = "UNVERIFIED_LICENSE"
        elif record.kind != intent.kind:
            rejected[record.id] = "KIND_MISMATCH"
        elif intent.style is not None and record.style != intent.style:
            rejected[record.id] = "STYLE_MISMATCH"
        elif record.aspect_ratio is not None and (
            not math.isfinite(record.aspect_ratio) or record.aspect_ratio <= 0
        ):
            rejected[record.id] = "INVALID_ASPECT"
        elif intent.aspect_ratio is not None and record.aspect_ratio is None:
            rejected[record.id] = "MISSING_ASPECT"
        elif record.kind == "photo" and (
            not isinstance(record.width_px, int)
            or not isinstance(record.height_px, int)
            or min(record.width_px, record.height_px)
            < policy.minimum_raster_short_edge_px
        ):
            rejected[record.id] = "INSUFFICIENT_RESOLUTION"
        elif record.kind == "icon" and not (
            isinstance(record.icon_family, str) and record.icon_family.strip()
        ):
            rejected[record.id] = "MISSING_ICON_FAMILY"
        elif (
            record.kind == "icon"
            and active_icon_family is not None
            and record.icon_family != active_icon_family
        ):
            rejected[record.id] = "ICON_FAMILY_MISMATCH"
        else:
            accepted.append(record)
    if not accepted:
        return AssetChoice(
            asset_id=None,
            crop_mode=policy.crop_mode,
            fallback=policy.missing_asset_fallback,
            reason="NO_SAFE_ASSET",
            rejected=rejected,
            icon_family=active_icon_family,
        )

    def rank(record: AssetRecord) -> tuple[float, float, str]:
        aspect_delta = (
            abs(record.aspect_ratio - intent.aspect_ratio)
            if record.aspect_ratio is not None and intent.aspect_ratio is not None
            else float("inf")
        )
        return (-record.quality, aspect_delta, record.id)

    selected = min(accepted, key=rank)
    return AssetChoice(
        asset_id=selected.id,
        crop_mode=policy.crop_mode,
        fallback=None,
        reason=None,
        rejected=rejected,
        icon_family=selected.icon_family,
    )


def _valid_date(value: str | None) -> bool:
    if value is None:
        return False
    try:
        return date.fromisoformat(value.strip()).isoformat() == value.strip()
    except ValueError:
        return False
