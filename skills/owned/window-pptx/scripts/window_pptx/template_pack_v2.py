"""Strict complete-work TemplatePack v2 contracts and v1 compatibility."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .template_pack import TemplatePack, load_template_pack, sha256_file


SKILL_ROOT = Path(__file__).resolve().parents[2]
DESIGN_PACK_ROOT = SKILL_ROOT / "design-packs"
SOURCE_MODES = {"physical_ooxml", "registered_composition"}
MATERIALIZERS = {"template_pack_v1_adapter", "registered_native_renderer"}


class TemplatePackV2Error(ValueError):
    """A complete-work pack is unsafe, stale, or not executable."""


@dataclass(frozen=True)
class ArtDirectionProfileV2:
    theme_id: str
    palette: tuple[str, ...]
    type_scale: Mapping[str, float]
    grid: Mapping[str, float]
    spacing_pt: tuple[int, ...]
    motifs: tuple[str, ...]
    forbidden: tuple[str, ...]
    max_same_family_run: int
    hero_interval: int


@dataclass(frozen=True)
class TemplatePageV2:
    id: str
    slide: int | None
    role: str
    family: str


@dataclass(frozen=True)
class TemplatePackV2:
    pack_id: str
    name: str
    manifest_path: Path
    source_mode: str
    deck_family_id: str
    style_cluster_id: str
    certification: str
    rights_basis: str
    materializer: str
    art_direction: ArtDirectionProfileV2
    pages: tuple[TemplatePageV2, ...]
    choreography: tuple[str, ...]
    source_sha256: str | None
    v1_pack: TemplatePack | None


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TemplatePackV2Error(f"{path} must be a non-empty string")
    return value.strip()


def _strings(value: Any, path: str, *, minimum: int = 0) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) < minimum:
        raise TemplatePackV2Error(f"{path} must contain at least {minimum} values")
    result = tuple(_text(item, f"{path}[{index}]") for index, item in enumerate(value))
    if len(result) != len(set(result)):
        raise TemplatePackV2Error(f"{path} contains duplicates")
    return result


def _exact(value: Any, fields: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TemplatePackV2Error(f"{path} must be an object")
    missing = sorted(fields - set(value))
    unknown = sorted(set(value) - fields)
    if missing or unknown:
        raise TemplatePackV2Error(
            f"{path} fields mismatch; missing={missing}, unknown={unknown}"
        )
    return value


def _manifest_path(identifier: str | Path) -> Path:
    path = Path(identifier)
    if path.is_file():
        return path.resolve()
    matches: list[Path] = []
    for manifest in DESIGN_PACK_ROOT.glob("*/template-pack-v2.json"):
        try:
            raw = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if raw.get("pack_id") == identifier:
            matches.append(manifest)
    if len(matches) != 1:
        raise TemplatePackV2Error(
            f"TemplatePack v2 {identifier!r} resolved to {len(matches)} manifests"
        )
    return matches[0].resolve()


def _load_art_direction(raw: Any) -> ArtDirectionProfileV2:
    fields = {
        "theme_id", "palette", "type_scale", "grid", "spacing_pt", "motifs",
        "forbidden", "max_same_family_run", "hero_interval",
    }
    value = _exact(raw, fields, "art_direction")
    palette = _strings(value["palette"], "art_direction.palette", minimum=4)
    if any(
        len(color) != 7
        or not color.startswith("#")
        or any(char not in "0123456789ABCDEFabcdef" for char in color[1:])
        for color in palette
    ):
        raise TemplatePackV2Error("art_direction.palette must contain hex colors")
    type_scale = _exact(
        value["type_scale"], {"display", "title", "body", "label"},
        "art_direction.type_scale",
    )
    if any(
        not isinstance(item, (int, float)) or isinstance(item, bool) or item < 11
        for item in type_scale.values()
    ):
        raise TemplatePackV2Error("art_direction.type_scale values must be >= 11")
    grid = _exact(
        value["grid"], {"columns", "safe_margin_x_in", "safe_margin_y_in"},
        "art_direction.grid",
    )
    if (
        type(grid["columns"]) is not int
        or grid["columns"] < 4
        or any(
            not isinstance(grid[key], (int, float))
            or isinstance(grid[key], bool)
            or grid[key] <= 0
            for key in ("safe_margin_x_in", "safe_margin_y_in")
        )
    ):
        raise TemplatePackV2Error("art_direction.grid is invalid")
    spacing = value["spacing_pt"]
    if (
        not isinstance(spacing, list)
        or not spacing
        or any(type(item) is not int or item <= 0 for item in spacing)
        or spacing != sorted(set(spacing))
    ):
        raise TemplatePackV2Error("art_direction.spacing_pt must be sorted unique integers")
    max_run = value["max_same_family_run"]
    hero_interval = value["hero_interval"]
    if type(max_run) is not int or not 1 <= max_run <= 3:
        raise TemplatePackV2Error("max_same_family_run must be 1..3")
    if type(hero_interval) is not int or hero_interval < 2:
        raise TemplatePackV2Error("hero_interval must be >= 2")
    return ArtDirectionProfileV2(
        theme_id=_text(value["theme_id"], "art_direction.theme_id"),
        palette=palette,
        type_scale=dict(type_scale),
        grid=dict(grid),
        spacing_pt=tuple(spacing),
        motifs=_strings(value["motifs"], "art_direction.motifs", minimum=1),
        forbidden=_strings(value["forbidden"], "art_direction.forbidden", minimum=1),
        max_same_family_run=max_run,
        hero_interval=hero_interval,
    )


def load_template_pack_v2(identifier: str | Path) -> TemplatePackV2:
    """Load one certified, rights-bound, executable complete-work pack."""

    manifest = _manifest_path(identifier)
    try:
        raw = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplatePackV2Error(f"cannot load {manifest}: {exc}") from exc
    common = {
        "schema_version", "pack_id", "name", "source_mode", "deck_family_id",
        "style_cluster_id", "certification", "rights", "materializer",
        "art_direction",
    }
    source_mode = raw.get("source_mode") if isinstance(raw, dict) else None
    fields = common | ({"source", "pages"} if source_mode == "physical_ooxml" else {"choreography"})
    value = _exact(raw, fields, "TemplatePackV2")
    if value["schema_version"] != "2.0":
        raise TemplatePackV2Error("schema_version must equal 2.0")
    if source_mode not in SOURCE_MODES:
        raise TemplatePackV2Error("source_mode is invalid")
    materializer = _text(value["materializer"], "materializer")
    expected_materializer = (
        "template_pack_v1_adapter"
        if source_mode == "physical_ooxml"
        else "registered_native_renderer"
    )
    if materializer not in MATERIALIZERS or materializer != expected_materializer:
        raise TemplatePackV2Error("source_mode and materializer are incompatible")
    if value["certification"] != "certified":
        raise TemplatePackV2Error("automatic selection requires certification=certified")
    rights = _exact(value["rights"], {"decision", "basis", "evidence"}, "rights")
    if rights["decision"] != "allowed":
        raise TemplatePackV2Error("certified packs require allowed rights")

    pages: tuple[TemplatePageV2, ...] = ()
    choreography: tuple[str, ...] = ()
    source_sha256: str | None = None
    v1_pack: TemplatePack | None = None
    if source_mode == "physical_ooxml":
        source = _exact(
            value["source"], {"template_pack_v1", "sha256"}, "source"
        )
        v1_manifest = (manifest.parent / _text(
            source["template_pack_v1"], "source.template_pack_v1"
        )).resolve()
        v1_pack = load_template_pack(v1_manifest)
        source_sha256 = _text(source["sha256"], "source.sha256")
        if v1_pack.template_sha256 != source_sha256:
            raise TemplatePackV2Error("v1 adapter source digest does not match v2")
        if sha256_file(v1_pack.template_path) != source_sha256:
            raise TemplatePackV2Error("physical source has drifted")
        raw_pages = value["pages"]
        if not isinstance(raw_pages, list) or len(raw_pages) != v1_pack.slide_count:
            raise TemplatePackV2Error("physical pages must enumerate every source slide")
        parsed: list[TemplatePageV2] = []
        for index, entry in enumerate(raw_pages):
            page = _exact(entry, {"id", "slide", "role", "family"}, f"pages[{index}]")
            if type(page["slide"]) is not int or page["slide"] != index + 1:
                raise TemplatePackV2Error("physical page slides must be ordered and complete")
            parsed.append(TemplatePageV2(
                _text(page["id"], f"pages[{index}].id"),
                page["slide"],
                _text(page["role"], f"pages[{index}].role"),
                _text(page["family"], f"pages[{index}].family"),
            ))
        if len({page.id for page in parsed}) != len(parsed):
            raise TemplatePackV2Error("physical page IDs must be unique")
        pages = tuple(parsed)
        choreography = tuple(page.role for page in pages)
    else:
        choreography = _strings(
            value["choreography"], "choreography", minimum=6
        )
        if choreography[0] != "cover" or "agenda" not in choreography or "closing" not in choreography:
            raise TemplatePackV2Error("registered choreography needs cover, agenda, and closing")

    return TemplatePackV2(
        pack_id=_text(value["pack_id"], "pack_id"),
        name=_text(value["name"], "name"),
        manifest_path=manifest,
        source_mode=source_mode,
        deck_family_id=_text(value["deck_family_id"], "deck_family_id"),
        style_cluster_id=_text(value["style_cluster_id"], "style_cluster_id"),
        certification=value["certification"],
        rights_basis=_text(rights["basis"], "rights.basis"),
        materializer=materializer,
        art_direction=_load_art_direction(value["art_direction"]),
        pages=pages,
        choreography=choreography,
        source_sha256=source_sha256,
        v1_pack=v1_pack,
    )


def adapt_template_pack_v1(pack: TemplatePack | str | Path) -> TemplatePackV2:
    """Resolve the owned v2 wrapper for the authorized v1 pack."""

    v1 = load_template_pack(pack) if not isinstance(pack, TemplatePack) else pack
    result = load_template_pack_v2("institutional-work-summary-v2")
    if result.v1_pack is None or result.v1_pack.id != v1.id:
        raise TemplatePackV2Error(f"no governed v2 adapter for v1 pack {v1.id!r}")
    return result
