"""Governed theme, brand-color, contrast, and font resolution."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


THEMES_PATH = Path(__file__).resolve().parents[2] / "registries" / "themes.json"
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
THEME_IDS = {
    "executive-light",
    "executive-dark",
    "technology",
    "finance-investor",
    "marketing-vibrant",
    "ecommerce-editorial",
    "education-training",
    "public-enterprise",
}
SCRIPT_PROFILE_IDS = {"zh-hans", "zh-hant", "ja", "ko"}


@dataclass(frozen=True)
class BrandOverrides:
    primary: str | None = None
    accent: str | None = None
    heading_font: str | None = None
    body_font: str | None = None


@dataclass(frozen=True)
class ResolutionEvent:
    code: str
    field: str
    requested: str | None
    resolved: str


@dataclass(frozen=True)
class ThemeDefinition:
    id: str
    mode: str
    audiences: tuple[str, ...]
    colors: dict[str, str]
    fonts: dict[str, Any]
    foundation: dict[str, Any]


@dataclass(frozen=True)
class ResolvedTheme:
    id: str
    mode: str
    colors: dict[str, str]
    fonts: dict[str, str]
    grid: dict[str, float | int]
    spacing: tuple[int, ...]
    typography: dict[str, int]
    effects: dict[str, Any]
    events: tuple[ResolutionEvent, ...]


def _normalize_color(value: str, field: str) -> str:
    if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
        raise ValueError(f"{field} color must use #RRGGBB")
    return value.upper()


def _rgb(value: str) -> tuple[float, float, float]:
    normalized = _normalize_color(value, "theme")
    channels = tuple(
        int(normalized[index : index + 2], 16) / 255 for index in (1, 3, 5)
    )
    return channels  # type: ignore[return-value]


def _relative_luminance(value: str) -> float:
    channels = []
    for channel in _rgb(value):
        channels.append(
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(first: str, second: str) -> float:
    """Return WCAG contrast for two #RRGGBB colors."""

    high, low = sorted(
        (_relative_luminance(first), _relative_luminance(second)), reverse=True
    )
    return (high + 0.05) / (low + 0.05)


def _on_color(background: str) -> str:
    candidates = ("#000000", "#FFFFFF")
    return max(candidates, key=lambda color: contrast_ratio(color, background))


def load_themes(path: Path | str | None = None) -> dict[str, ThemeDefinition]:
    registry_path = Path(path) if path is not None else THEMES_PATH
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    if set(raw) != {"schema_version", "foundation", "themes"}:
        raise ValueError("theme registry has unexpected fields")
    if raw["schema_version"] != "1.0":
        raise ValueError("unsupported theme registry version")
    foundation = raw["foundation"]
    result: dict[str, ThemeDefinition] = {}
    for entry in raw["themes"]:
        theme_id = entry["id"]
        if theme_id in result:
            raise ValueError(f"duplicate theme id: {theme_id}")
        colors = {
            key: _normalize_color(value, f"{theme_id}.{key}")
            for key, value in entry["colors"].items()
        }
        required_colors = {
            "background",
            "surface",
            "text",
            "muted_text",
            "primary",
            "accent",
            "positive",
            "warning",
            "negative",
        }
        if set(colors) != required_colors:
            raise ValueError(f"theme {theme_id} has incomplete semantic colors")
        required_fonts = {
            "heading",
            "body",
            "fallbacks",
            "scripts",
        }
        if set(entry["fonts"]) != required_fonts:
            raise ValueError(f"theme {theme_id} has incomplete font profiles")
        scripts = entry["fonts"]["scripts"]
        if set(scripts) != SCRIPT_PROFILE_IDS or any(
            set(profile) != {"heading", "body", "fallbacks"}
            for profile in scripts.values()
        ):
            raise ValueError(f"theme {theme_id} has incomplete script profiles")
        result[theme_id] = ThemeDefinition(
            id=theme_id,
            mode=entry["mode"],
            audiences=tuple(entry["audiences"]),
            colors=colors,
            fonts=entry["fonts"],
            foundation=foundation,
        )
    return result


def select_theme(
    scenario: str,
    *,
    audience: str | None = None,
    industry: str | None = None,
    prefer_dark: bool = False,
) -> str:
    """Choose a governed theme from project context using stable priorities."""

    normalized_scenario = re.sub(
        r"[\s_]+", "-", scenario.casefold()
    ).strip("-")
    if normalized_scenario in THEME_IDS:
        return normalized_scenario

    context = " ".join(
        re.sub(r"[\s_]+", "-", value.casefold()).strip("-")
        for value in (scenario, audience, industry)
        if value
    )
    if any(
        token in context
        for token in (
            "government",
            "public-sector",
            "public-enterprise",
            "state-owned",
        )
    ):
        return "public-enterprise"
    if any(
        token in context
        for token in (
            "investor",
            "fundraising",
            "investment",
            "finance",
            "financial",
            "fintech",
            "banking",
        )
    ):
        return "finance-investor"
    if any(token in context for token in ("training", "learner", "education", "course")):
        return "education-training"
    if any(token in context for token in ("ecommerce", "e-commerce", "retail")):
        return "ecommerce-editorial"
    if any(
        token in context
        for token in (
            "brand",
            "marketing",
            "campaign",
            "sales-proposal",
            "product-launch",
        )
    ):
        return "marketing-vibrant"
    if any(token in context for token in ("technology", "software", "saas", "digital")):
        return "technology"
    return "executive-dark" if prefer_dark else "executive-light"


def _resolve_font(
    role: str,
    preferred: str,
    override: str | None,
    fallbacks: tuple[str, ...],
    installed: dict[str, str],
    *,
    required_script: str,
    script_fonts: set[str],
    font_scripts: dict[str, set[str]],
) -> tuple[str, tuple[ResolutionEvent, ...]]:
    events: list[ResolutionEvent] = []
    candidates = tuple(
        candidate
        for candidate in (override, preferred, *fallbacks)
        if candidate is not None
    )
    chosen: str | None = None
    for candidate in candidates:
        installed_name = installed.get(candidate.casefold())
        supports_script = (
            required_script == "latin"
            or required_script in font_scripts.get(candidate.casefold(), set())
            or candidate.casefold() in script_fonts
        )
        if installed_name is not None and supports_script:
            chosen = installed_name
            break
    if chosen is None:
        chosen = "Arial"
        events.append(
            ResolutionEvent("FONT_SAFE_DEFAULT_UNVERIFIED", role, override or preferred, chosen)
        )
    elif override is not None and chosen.casefold() == override.casefold():
        events.append(ResolutionEvent("FONT_OVERRIDE_APPLIED", role, override, chosen))
    elif override is not None:
        events.append(ResolutionEvent("FONT_FALLBACK", role, override, chosen))
    elif chosen.casefold() != preferred.casefold():
        events.append(ResolutionEvent("FONT_FALLBACK", role, override or preferred, chosen))
    return chosen, tuple(events)


def resolve_theme(
    theme_id: str,
    brand: BrandOverrides | None = None,
    installed_fonts: set[str] | None = None,
    *,
    locale: str = "en-US",
    font_scripts: dict[str, set[str]] | None = None,
) -> ResolvedTheme:
    """Resolve one immutable theme and report every brand/font substitution."""

    themes = load_themes()
    if theme_id not in themes:
        raise ValueError(f"unknown theme: {theme_id}")
    definition = themes[theme_id]
    brand = brand or BrandOverrides()
    colors = dict(definition.colors)
    events: list[ResolutionEvent] = []
    for field, requested in (("primary", brand.primary), ("accent", brand.accent)):
        if requested is None:
            continue
        resolved = _normalize_color(requested, field)
        minimum_contrast = 3.0
        if min(
            contrast_ratio(resolved, colors["background"]),
            contrast_ratio(resolved, colors["surface"]),
        ) < minimum_contrast:
            events.append(
                ResolutionEvent(
                    "BRAND_COLOR_CONTRAST_FALLBACK",
                    field,
                    requested,
                    colors[field],
                )
            )
        else:
            colors[field] = resolved
            events.append(
                ResolutionEvent("BRAND_COLOR_OVERRIDE", field, requested, resolved)
            )
    colors["on_primary"] = _on_color(colors["primary"])

    available = {font.casefold(): font for font in (installed_fonts or set())}
    normalized_locale = locale.casefold().replace("_", "-")
    language = normalized_locale.split("-", 1)[0]
    if language == "zh":
        script = (
            "zh-hant"
            if any(
                token in normalized_locale.split("-")
                for token in ("hant", "tw", "hk", "mo")
            )
            else "zh-hans"
        )
    elif language in {"ja", "ko"}:
        script = language
    else:
        script = "latin"
    if script != "latin":
        profile = definition.fonts["scripts"][script]
        heading_preferred = profile["heading"]
        body_preferred = profile["body"]
        fallbacks = tuple(profile["fallbacks"])
        script_fonts = {
            name.casefold()
            for name in (heading_preferred, body_preferred, *fallbacks)
        }
        events.append(
            ResolutionEvent("FONT_SCRIPT_PROFILE", "profile", locale, script)
        )
    else:
        heading_preferred = definition.fonts["heading"]
        body_preferred = definition.fonts["body"]
        fallbacks = tuple(definition.fonts["fallbacks"])
        script_fonts = set()
    capabilities = {
        name.casefold(): {script_name.casefold() for script_name in scripts}
        for name, scripts in (font_scripts or {}).items()
    }
    heading, heading_events = _resolve_font(
        "heading",
        heading_preferred,
        brand.heading_font,
        fallbacks,
        available,
        required_script=script,
        script_fonts=script_fonts,
        font_scripts=capabilities,
    )
    body, body_events = _resolve_font(
        "body",
        body_preferred,
        brand.body_font,
        fallbacks,
        available,
        required_script=script,
        script_fonts=script_fonts,
        font_scripts=capabilities,
    )
    events.extend(heading_events)
    events.extend(body_events)
    foundation = definition.foundation
    return ResolvedTheme(
        id=definition.id,
        mode=definition.mode,
        colors=colors,
        fonts={"heading": heading, "body": body},
        grid=dict(foundation["grid"]),
        spacing=tuple(foundation["spacing"]),
        typography=dict(foundation["typography"]),
        effects=dict(foundation["effects"]),
        events=tuple(events),
    )
