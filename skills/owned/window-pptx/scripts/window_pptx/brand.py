"""Trusted BrandSpec, asset requirements, and deterministic font inventory."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .themes import BrandOverrides


HEX = re.compile(r"#[0-9A-Fa-f]{6}")
SHA256 = re.compile(r"[0-9a-f]{64}")


class BrandSpecError(ValueError):
    """Trusted brand input is malformed or ambiguous."""


@dataclass(frozen=True)
class BrandColor:
    role: str
    value: str
    source: str


@dataclass(frozen=True)
class BrandFont:
    role: str
    family: str
    source: str


@dataclass(frozen=True)
class BrandAssetRequirement:
    kind: str
    mandatory: bool


@dataclass(frozen=True)
class BrandSpec:
    schema_version: str
    name: str
    require_brand_fidelity: bool
    palette: tuple[BrandColor, ...]
    fonts: tuple[BrandFont, ...]
    required_assets: tuple[BrandAssetRequirement, ...]
    prohibited_patterns: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "require_brand_fidelity": self.require_brand_fidelity,
            "palette": [
                {"role": item.role, "value": item.value, "source": item.source}
                for item in self.palette
            ],
            "fonts": [
                {"role": item.role, "family": item.family, "source": item.source}
                for item in self.fonts
            ],
            "required_assets": [
                {"kind": item.kind, "mandatory": item.mandatory}
                for item in self.required_assets
            ],
            "prohibited_patterns": list(self.prohibited_patterns),
        }

    def to_overrides(self) -> BrandOverrides:
        colors = {item.role: item.value.upper() for item in self.palette}
        fonts = {item.role: item.family for item in self.fonts}
        return BrandOverrides(
            primary=colors.get("primary"),
            accent=colors.get("accent"),
            positive=colors.get("positive"),
            warning=colors.get("warning"),
            negative=colors.get("negative"),
            background=colors.get("background"),
            heading_font=fonts.get("heading"),
            body_font=fonts.get("body"),
        )


@dataclass(frozen=True)
class BrandFinding:
    code: str
    message: str
    hard_gate: bool
    asset_kind: str | None = None


def _object(value: Any, path: str, allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BrandSpecError(f"{path} must be an object")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise BrandSpecError(f"{path} has unknown fields: {', '.join(unknown)}")
    return value


def _string(value: Any, path: str, maximum: int = 300) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise BrandSpecError(f"{path} must be a trimmed non-empty string")
    return value


def validate_brand_spec(payload: Any) -> BrandSpec:
    raw = _object(
        payload,
        "$",
        {
            "schema_version", "name", "require_brand_fidelity", "palette", "fonts",
            "required_assets", "prohibited_patterns",
        },
    )
    if raw.get("schema_version") != "1.0":
        raise BrandSpecError("$.schema_version must equal 1.0")
    fidelity = raw.get("require_brand_fidelity", False)
    if not isinstance(fidelity, bool):
        raise BrandSpecError("$.require_brand_fidelity must be boolean")
    palette_raw = raw.get("palette", [])
    fonts_raw = raw.get("fonts", [])
    assets_raw = raw.get("required_assets", [])
    prohibited_raw = raw.get("prohibited_patterns", [])
    if not all(isinstance(value, list) for value in (palette_raw, fonts_raw, assets_raw, prohibited_raw)):
        raise BrandSpecError("brand collections must be arrays")
    palette: list[BrandColor] = []
    for index, value in enumerate(palette_raw):
        path = f"$.palette[{index}]"
        item = _object(value, path, {"role", "value", "source"})
        role = _string(item.get("role"), f"{path}.role", 30)
        if role not in {"primary", "accent", "positive", "warning", "negative", "background"}:
            raise BrandSpecError(f"{path}.role is not registered")
        color = _string(item.get("value"), f"{path}.value", 7)
        if not HEX.fullmatch(color):
            raise BrandSpecError(f"{path}.value must be #RRGGBB")
        palette.append(BrandColor(role, color.upper(), _string(item.get("source"), f"{path}.source")))
    if len({item.role for item in palette}) != len(palette):
        raise BrandSpecError("$.palette contains duplicate roles")
    fonts: list[BrandFont] = []
    for index, value in enumerate(fonts_raw):
        path = f"$.fonts[{index}]"
        item = _object(value, path, {"role", "family", "source"})
        role = _string(item.get("role"), f"{path}.role", 30)
        if role not in {"heading", "body"}:
            raise BrandSpecError(f"{path}.role is not registered")
        fonts.append(
            BrandFont(
                role,
                _string(item.get("family"), f"{path}.family", 120),
                _string(item.get("source"), f"{path}.source"),
            )
        )
    if len({item.role for item in fonts}) != len(fonts):
        raise BrandSpecError("$.fonts contains duplicate roles")
    assets: list[BrandAssetRequirement] = []
    for index, value in enumerate(assets_raw):
        path = f"$.required_assets[{index}]"
        item = _object(value, path, {"kind", "mandatory"})
        kind = _string(item.get("kind"), f"{path}.kind", 40)
        if kind not in {"logo", "product", "ui", "photo", "icon"}:
            raise BrandSpecError(f"{path}.kind is not registered")
        mandatory = item.get("mandatory")
        if not isinstance(mandatory, bool):
            raise BrandSpecError(f"{path}.mandatory must be boolean")
        assets.append(BrandAssetRequirement(kind, mandatory))
    if len({item.kind for item in assets}) != len(assets):
        raise BrandSpecError("$.required_assets contains duplicate kinds")
    prohibited = tuple(_string(value, "$.prohibited_patterns[]", 100) for value in prohibited_raw)
    if len(prohibited) != len(set(prohibited)):
        raise BrandSpecError("$.prohibited_patterns contains duplicates")
    return BrandSpec(
        "1.0",
        _string(raw.get("name"), "$.name", 160),
        fidelity,
        tuple(palette),
        tuple(fonts),
        tuple(assets),
        prohibited,
    )


def load_brand_spec(path: Path | str) -> BrandSpec:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BrandSpecError(f"cannot load BrandSpec: {exc}") from exc
    return validate_brand_spec(payload)


def assess_brand_assets(
    spec: BrandSpec,
    available_asset_kinds: frozenset[str],
    *,
    installed_fonts: Iterable[str] = (),
) -> tuple[BrandFinding, ...]:
    """Assess concrete brand dependencies before layout or COM mutation."""

    findings: list[BrandFinding] = []
    for requirement in spec.required_assets:
        if requirement.kind in available_asset_kinds:
            continue
        hard = spec.require_brand_fidelity and requirement.mandatory
        findings.append(
            BrandFinding(
                "REQUIRED_BRAND_ASSET_MISSING",
                f"required brand asset is unavailable: {requirement.kind}",
                hard,
                requirement.kind,
            )
        )
    installed = {
        family.strip().casefold()
        for family in installed_fonts
        if isinstance(family, str) and family.strip()
    }
    for font in spec.fonts:
        if font.family.casefold() in installed:
            continue
        findings.append(
            BrandFinding(
                "BRAND_FONT_MISSING",
                f"brand {font.role} font is unavailable: {font.family}",
                spec.require_brand_fidelity,
                font.role,
            )
        )
    return tuple(findings)


def font_inventory_digest(fonts: Iterable[str]) -> str:
    canonical = json.dumps(
        sorted({font.strip() for font in fonts if isinstance(font, str) and font.strip()}, key=str.casefold),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def discover_installed_fonts() -> set[str]:
    """Discover font families without starting PowerPoint or a render engine."""

    if os.name != "nt":
        fontconfig = shutil.which("fc-list")
        if fontconfig is None:
            return {"Arial"}
        try:
            result = subprocess.run(
                [fontconfig, "--format=%{family}\n"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return {"Arial"}
        if result.returncode != 0:
            return {"Arial"}
        families = {
            family.strip()
            for line in result.stdout.splitlines()
            for family in line.split(",")
            if family.strip()
        }
        return families or {"Arial"}
    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:
        return {"Arial"}
    result: set[str] = set()
    locations = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
    )
    for hive, key_path in locations:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                index = 0
                while True:
                    try:
                        display_name, _, _ = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    index += 1
                    name = re.sub(r"\s*\([^)]*\)\s*$", "", display_name).strip()
                    if name:
                        result.add(name)
        except OSError:
            continue
    return result or {"Arial"}


__all__ = [
    "BrandAssetRequirement", "BrandColor", "BrandFinding", "BrandFont", "BrandSpec",
    "BrandSpecError", "assess_brand_assets", "discover_installed_fonts",
    "font_inventory_digest", "load_brand_spec", "validate_brand_spec",
]
