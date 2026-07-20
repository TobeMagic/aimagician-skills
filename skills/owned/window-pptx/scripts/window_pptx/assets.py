"""Deterministic asset-policy and safe asset selection."""

from __future__ import annotations

import json
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


@dataclass(frozen=True)
class AssetChoice:
    asset_id: str | None
    crop_mode: str
    fallback: str | None
    reason: str | None
    rejected: dict[str, str]


def load_asset_policy(path: Path | str | None = None) -> AssetPolicy:
    registry_path = Path(path) if path is not None else COMPONENTS_PATH
    raw = json.loads(registry_path.read_text(encoding="utf-8"))["asset_policy"]
    return AssetPolicy(
        crop_mode=raw["crop_mode"],
        allow_stretch=raw["allow_stretch"],
        required_provenance=tuple(raw["required_provenance"]),
        icon_style_scope=raw["icon_style_scope"],
        missing_asset_fallback=raw["missing_asset_fallback"],
    )


def choose_asset(
    intent: AssetIntent, records: Iterable[AssetRecord]
) -> AssetChoice:
    """Choose the best safe asset with stable quality/aspect/ID ordering."""

    policy = load_asset_policy()
    accepted: list[AssetRecord] = []
    rejected: dict[str, str] = {}
    for record in records:
        if not record.source or not record.license or not record.retrieved_at:
            rejected[record.id] = "MISSING_PROVENANCE"
        elif record.kind != intent.kind:
            rejected[record.id] = "KIND_MISMATCH"
        elif intent.style is not None and record.style != intent.style:
            rejected[record.id] = "STYLE_MISMATCH"
        else:
            accepted.append(record)
    if not accepted:
        return AssetChoice(
            asset_id=None,
            crop_mode=policy.crop_mode,
            fallback=policy.missing_asset_fallback,
            reason="NO_SAFE_ASSET",
            rejected=rejected,
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
    )
