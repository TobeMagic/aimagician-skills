"""Deterministic DesignPack loading and scenario selection.

DesignPack is the governed visual-policy layer above themes and layout
registries.  Weak models choose a business scenario; this module chooses the
pack, font fallbacks, pacing rules, asset priorities, and safe layout fallback.
No model is asked to invent a style from scratch.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


SKILL_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = SKILL_ROOT / "registries" / "design-packs.json"
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]+$")
_HEX_COLOR = re.compile(r"^[0-9A-Fa-f]{6}$")
_MODES = {"light", "dark", "mixed"}
_DENSITIES = {"sparse", "balanced", "dense"}
_ASSET_SOURCES = {"user", "template", "licensed", "generated", "native"}

SCENARIO_ALIASES = {
    "strategic-plan": "strategy-planning",
    "training": "training-deck",
}

SCENARIO_DEFAULT_PACK = {
    "business-report": "institutional-annual-editorial",
    "project-proposal": "consulting-executive",
    "product-launch": "product-launch-stage",
    "market-analysis": "data-research-editorial",
    "sales-proposal": "consulting-executive",
    "investor-pitch": "product-launch-stage",
    "annual-review": "institutional-annual-editorial",
    "strategy-planning": "consulting-executive",
    "data-analysis": "data-research-editorial",
    "research-report": "data-research-editorial",
    "training-deck": "data-research-editorial",
    "brand-introduction": "product-launch-stage",
    "project-kickoff": "institutional-annual-editorial",
    "operations-review": "institutional-annual-editorial",
    "ecommerce-marketing": "product-launch-stage",
}


class DesignPackError(ValueError):
    """A DesignPack registry or manifest is invalid."""


@dataclass(frozen=True)
class DesignTheme:
    mode: str
    primary: str
    accent: str
    background: str
    heading_font: tuple[str, ...]
    body_font: tuple[str, ...]


@dataclass(frozen=True)
class PacingPolicy:
    max_same_family_run: int
    hero_interval: int
    density_pattern: tuple[str, ...]


@dataclass(frozen=True)
class AssetStrategy:
    priority: tuple[str, ...]
    required_for: tuple[str, ...]


@dataclass(frozen=True)
class SafeFallback:
    family: str
    max_body_chars: int
    max_items: int


@dataclass(frozen=True)
class DesignPack:
    id: str
    name: str
    runtime_theme_id: str
    manifest_path: Path
    scenarios: tuple[str, ...]
    theme: DesignTheme
    page_families: tuple[str, ...]
    pacing: PacingPolicy
    asset_strategy: AssetStrategy
    safe_fallback: SafeFallback
    template_pack: str | None = None


def canonical_scenario_id(scenario_id: str) -> str:
    result = scenario_id.strip().casefold().replace("_", "-")
    return SCENARIO_ALIASES.get(result, result)


def _strict_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DesignPackError(f"{path} must be a trimmed non-empty string")
    return value


def _strict_object(
    value: Any,
    path: str,
    *,
    required: set[str],
    optional: set[str] = frozenset(),
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise DesignPackError(f"{path} must be an object")
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required - optional)
    if missing:
        raise DesignPackError(f"{path} missing fields: {', '.join(missing)}")
    if unknown:
        raise DesignPackError(f"{path} unknown fields: {', '.join(unknown)}")
    return value


def _string_tuple(
    value: Any,
    path: str,
    *,
    minimum: int = 1,
    allowed: set[str] | None = None,
    unique: bool = True,
) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) < minimum:
        raise DesignPackError(f"{path} must contain at least {minimum} strings")
    result = tuple(_strict_string(item, f"{path}[{index}]") for index, item in enumerate(value))
    if unique and len(set(result)) != len(result):
        raise DesignPackError(f"{path} cannot contain duplicates")
    if allowed is not None and any(item not in allowed for item in result):
        raise DesignPackError(f"{path} contains an unsupported value")
    return result


def load_design_pack(path: Path | str) -> DesignPack:
    manifest_path = Path(path).resolve()
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DesignPackError(f"cannot read DesignPack {manifest_path}: {exc}") from exc
    root = _strict_object(
        raw,
        "$",
        required={
            "schema_version",
            "id",
            "name",
            "runtime_theme_id",
            "scenarios",
            "theme",
            "page_families",
            "pacing",
            "asset_strategy",
            "safe_fallback",
        },
        optional={"template_pack"},
    )
    if root["schema_version"] != "1.0":
        raise DesignPackError("$.schema_version must equal 1.0")
    pack_id = _strict_string(root["id"], "$.id")
    if _IDENTIFIER.fullmatch(pack_id) is None:
        raise DesignPackError("$.id must be a lowercase semantic identifier")
    theme_raw = _strict_object(
        root["theme"],
        "$.theme",
        required={
            "mode",
            "primary",
            "accent",
            "background",
            "heading_font",
            "body_font",
        },
    )
    mode = _strict_string(theme_raw["mode"], "$.theme.mode")
    if mode not in _MODES:
        raise DesignPackError("$.theme.mode is unsupported")
    colors = []
    for field in ("primary", "accent", "background"):
        color = _strict_string(theme_raw[field], f"$.theme.{field}")
        if _HEX_COLOR.fullmatch(color) is None:
            raise DesignPackError(f"$.theme.{field} must be a six-digit hex color")
        colors.append(color.upper())
    pacing_raw = _strict_object(
        root["pacing"],
        "$.pacing",
        required={"max_same_family_run", "hero_interval", "density_pattern"},
    )
    max_same = pacing_raw["max_same_family_run"]
    hero_interval = pacing_raw["hero_interval"]
    if type(max_same) is not int or not 1 <= max_same <= 3:
        raise DesignPackError("$.pacing.max_same_family_run must be 1..3")
    if type(hero_interval) is not int or not 2 <= hero_interval <= 8:
        raise DesignPackError("$.pacing.hero_interval must be 2..8")
    asset_raw = _strict_object(
        root["asset_strategy"],
        "$.asset_strategy",
        required={"priority", "required_for"},
    )
    fallback_raw = _strict_object(
        root["safe_fallback"],
        "$.safe_fallback",
        required={"family", "max_body_chars", "max_items"},
    )
    max_body_chars = fallback_raw["max_body_chars"]
    max_items = fallback_raw["max_items"]
    if type(max_body_chars) is not int or max_body_chars < 40:
        raise DesignPackError("$.safe_fallback.max_body_chars must be >= 40")
    if type(max_items) is not int or max_items < 2:
        raise DesignPackError("$.safe_fallback.max_items must be >= 2")
    template_pack = root.get("template_pack")
    if template_pack is not None:
        template_pack = _strict_string(template_pack, "$.template_pack")
    return DesignPack(
        id=pack_id,
        name=_strict_string(root["name"], "$.name"),
        runtime_theme_id=_strict_string(
            root["runtime_theme_id"], "$.runtime_theme_id"
        ),
        manifest_path=manifest_path,
        scenarios=tuple(
            canonical_scenario_id(value)
            for value in _string_tuple(root["scenarios"], "$.scenarios")
        ),
        theme=DesignTheme(
            mode=mode,
            primary=colors[0],
            accent=colors[1],
            background=colors[2],
            heading_font=_string_tuple(theme_raw["heading_font"], "$.theme.heading_font"),
            body_font=_string_tuple(theme_raw["body_font"], "$.theme.body_font"),
        ),
        page_families=_string_tuple(root["page_families"], "$.page_families", minimum=8),
        pacing=PacingPolicy(
            max_same_family_run=max_same,
            hero_interval=hero_interval,
            density_pattern=_string_tuple(
                pacing_raw["density_pattern"],
                "$.pacing.density_pattern",
                minimum=3,
                allowed=_DENSITIES,
                unique=False,
            ),
        ),
        asset_strategy=AssetStrategy(
            priority=_string_tuple(
                asset_raw["priority"],
                "$.asset_strategy.priority",
                minimum=3,
                allowed=_ASSET_SOURCES,
            ),
            required_for=_string_tuple(
                asset_raw["required_for"],
                "$.asset_strategy.required_for",
                minimum=0,
            ),
        ),
        safe_fallback=SafeFallback(
            family=_strict_string(fallback_raw["family"], "$.safe_fallback.family"),
            max_body_chars=max_body_chars,
            max_items=max_items,
        ),
        template_pack=template_pack,
    )


def load_design_packs(
    registry_path: Path | str = DEFAULT_REGISTRY_PATH,
) -> dict[str, DesignPack]:
    registry = Path(registry_path).resolve()
    try:
        raw = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DesignPackError(f"cannot read DesignPack registry {registry}: {exc}") from exc
    root = _strict_object(raw, "$", required={"schema_version", "packs"})
    if root["schema_version"] != "1.0" or not isinstance(root["packs"], list):
        raise DesignPackError("DesignPack registry must use schema 1.0 and list packs")
    packs: dict[str, DesignPack] = {}
    for index, entry in enumerate(root["packs"]):
        item = _strict_object(
            entry,
            f"$.packs[{index}]",
            required={"id", "manifest"},
        )
        declared_id = _strict_string(item["id"], f"$.packs[{index}].id")
        manifest = (SKILL_ROOT / _strict_string(
            item["manifest"], f"$.packs[{index}].manifest"
        )).resolve()
        pack = load_design_pack(manifest)
        if declared_id != pack.id:
            raise DesignPackError(
                f"registry id {declared_id} does not match manifest id {pack.id}"
            )
        if pack.id in packs:
            raise DesignPackError(f"duplicate DesignPack id: {pack.id}")
        packs[pack.id] = pack
    if not packs:
        raise DesignPackError("DesignPack registry cannot be empty")
    return packs


def select_design_pack(
    scenario_id: str,
    *,
    preferred_pack_id: str | None = None,
    packs: Mapping[str, DesignPack] | None = None,
) -> DesignPack:
    available = dict(load_design_packs() if packs is None else packs)
    scenario = canonical_scenario_id(scenario_id)
    if preferred_pack_id is not None:
        try:
            preferred = available[preferred_pack_id]
        except KeyError as exc:
            raise DesignPackError(f"unknown preferred DesignPack: {preferred_pack_id}") from exc
        if scenario not in preferred.scenarios:
            raise DesignPackError(
                f"DesignPack {preferred_pack_id} does not support scenario {scenario}"
            )
        return preferred
    default_id = SCENARIO_DEFAULT_PACK.get(scenario)
    if default_id in available and scenario in available[default_id].scenarios:
        return available[default_id]
    candidates = sorted(
        (pack for pack in available.values() if scenario in pack.scenarios),
        key=lambda pack: pack.id,
    )
    if not candidates:
        raise DesignPackError(f"no DesignPack supports scenario: {scenario}")
    return candidates[0]


__all__ = [
    "AssetStrategy",
    "DesignPack",
    "DesignPackError",
    "DesignTheme",
    "PacingPolicy",
    "SafeFallback",
    "SCENARIO_DEFAULT_PACK",
    "canonical_scenario_id",
    "load_design_pack",
    "load_design_packs",
    "select_design_pack",
]
