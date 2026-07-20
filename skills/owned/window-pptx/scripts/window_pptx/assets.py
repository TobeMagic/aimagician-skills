"""Deterministic asset-policy and safe asset selection."""

from __future__ import annotations

import json
import math
import struct
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
    allowed_kinds: tuple[str, ...]
    raster_kinds: tuple[str, ...]


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
        if (
            isinstance(intent.kind, str)
            and intent.kind.strip().casefold() == "icon"
            and choice.icon_family is not None
        ):
            self.icon_family = choice.icon_family
        return choice


def read_raster_dimensions(path: Path | str) -> tuple[int, int]:
    """Read trusted PNG/JPEG dimensions and reject mislabeled or corrupt files."""

    asset_path = Path(path)
    try:
        payload = asset_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"asset cannot be read: {asset_path}") from exc
    suffix = asset_path.suffix.casefold()
    if suffix == ".png":
        if len(payload) < 24 or payload[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"asset is not a valid PNG: {asset_path}")
        width_px, height_px = struct.unpack(">II", payload[16:24])
    elif suffix in {".jpg", ".jpeg"}:
        width_px, height_px = _jpeg_dimensions(payload, asset_path)
    else:
        raise ValueError(f"asset type is unsupported: {asset_path.suffix}")
    if width_px <= 0 or height_px <= 0:
        raise ValueError(f"asset has invalid dimensions: {asset_path}")
    return width_px, height_px


def _jpeg_dimensions(payload: bytes, path: Path) -> tuple[int, int]:
    if len(payload) < 4 or payload[:2] != b"\xff\xd8":
        raise ValueError(f"asset is not a valid JPEG: {path}")
    offset = 2
    start_of_frame = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while offset + 4 <= len(payload):
        while offset < len(payload) and payload[offset] != 0xFF:
            offset += 1
        while offset < len(payload) and payload[offset] == 0xFF:
            offset += 1
        if offset >= len(payload):
            break
        marker = payload[offset]
        offset += 1
        if marker in {0xD8, 0xD9}:
            continue
        if marker == 0xDA:
            break
        if offset + 2 > len(payload):
            break
        segment_length = struct.unpack(">H", payload[offset : offset + 2])[0]
        if segment_length < 2 or offset + segment_length > len(payload):
            break
        if marker in start_of_frame and segment_length >= 7:
            height_px, width_px = struct.unpack(
                ">HH", payload[offset + 3 : offset + 7]
            )
            return width_px, height_px
        offset += segment_length
    raise ValueError(f"asset has no JPEG dimensions: {path}")


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
        allowed_kinds=tuple(raw["allowed_kinds"]),
        raster_kinds=tuple(raw["raster_kinds"]),
    )


def _normalized_token(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip().casefold()


def choose_asset(
    intent: AssetIntent,
    records: Iterable[AssetRecord],
    *,
    active_icon_family: str | None = None,
) -> AssetChoice:
    """Choose the best safe asset with stable quality/aspect/ID ordering."""

    policy = load_asset_policy()
    intent_kind = _normalized_token(intent.kind, "asset kind")
    if intent_kind not in policy.allowed_kinds:
        raise ValueError(f"unsupported asset kind: {intent_kind}")
    intent_style = (
        _normalized_token(intent.style, "asset style")
        if intent.style is not None
        else None
    )
    if intent.aspect_ratio is not None and (
        not math.isfinite(intent.aspect_ratio) or intent.aspect_ratio <= 0
    ):
        raise ValueError("intent aspect_ratio must be finite and positive")
    materialized = tuple(records)
    id_counts: dict[str, int] = {}
    for record in materialized:
        if isinstance(record.id, str) and record.id.strip():
            id_counts[record.id] = id_counts.get(record.id, 0) + 1
    accepted: list[AssetRecord] = []
    rejected: dict[str, str] = {}
    for index, record in enumerate(materialized):
        record_key = (
            record.id
            if isinstance(record.id, str) and record.id.strip()
            else f"@record-{index}"
        )
        record_kind = (
            record.kind.strip().casefold()
            if isinstance(record.kind, str) and record.kind.strip()
            else None
        )
        record_style = (
            record.style.strip().casefold()
            if isinstance(record.style, str) and record.style.strip()
            else None
        )
        if not isinstance(record.id, str) or not record.id.strip():
            rejected[record_key] = "INVALID_ID"
        elif id_counts[record.id] > 1:
            rejected[record_key] = "DUPLICATE_ID"
        elif (
            isinstance(record.quality, bool)
            or not isinstance(record.quality, (int, float))
            or not math.isfinite(record.quality)
            or not policy.minimum_quality <= record.quality <= 100
        ):
            rejected[record_key] = "INVALID_QUALITY"
        elif not all(
            isinstance(value, str) and bool(value.strip())
            for value in (record.source, record.license, record.retrieved_at)
        ):
            rejected[record_key] = "MISSING_PROVENANCE"
        elif not _valid_date(record.retrieved_at):
            rejected[record_key] = "INVALID_RETRIEVED_AT"
        elif record.license.casefold().strip() in {"unknown", "unverified"}:
            rejected[record_key] = "UNVERIFIED_LICENSE"
        elif record_kind is None or record_kind not in policy.allowed_kinds:
            rejected[record_key] = "INVALID_KIND"
        elif record.style is not None and record_style is None:
            rejected[record_key] = "INVALID_STYLE"
        elif record_kind != intent_kind:
            rejected[record_key] = "KIND_MISMATCH"
        elif intent_style is not None and record_style != intent_style:
            rejected[record_key] = "STYLE_MISMATCH"
        elif record.aspect_ratio is not None and (
            isinstance(record.aspect_ratio, bool)
            or not isinstance(record.aspect_ratio, (int, float))
            or not math.isfinite(record.aspect_ratio)
            or record.aspect_ratio <= 0
        ):
            rejected[record_key] = "INVALID_ASPECT"
        elif intent.aspect_ratio is not None and record.aspect_ratio is None:
            rejected[record_key] = "MISSING_ASPECT"
        elif record_kind in policy.raster_kinds and (
            type(record.width_px) is not int
            or type(record.height_px) is not int
            or min(record.width_px, record.height_px)
            < policy.minimum_raster_short_edge_px
        ):
            rejected[record_key] = "INSUFFICIENT_RESOLUTION"
        elif record_kind == "icon" and not (
            isinstance(record.icon_family, str) and record.icon_family.strip()
        ):
            rejected[record_key] = "MISSING_ICON_FAMILY"
        elif (
            record_kind == "icon"
            and active_icon_family is not None
            and record.icon_family != active_icon_family
        ):
            rejected[record_key] = "ICON_FAMILY_MISMATCH"
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
