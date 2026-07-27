"""Portable, source-safe adaptation of authorized physical PPTX TemplatePacks."""

from __future__ import annotations

import hashlib
import html
import io
import json
import math
import os
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


SKILL_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DESIGN_PACK_ROOT = SKILL_ROOT / "design-packs"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
_TEXT_RE = re.compile(r"(<a:t\b[^>]*>)(.*?)(</a:t>)", re.DOTALL)
_SHAPE_KINDS = ("sp", "graphicFrame", "pic", "cxnSp")


class TemplatePackError(ValueError):
    """A TemplatePack is malformed, stale, unsafe, or cannot be adapted."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _part_sort_key(name: str) -> tuple[int, int, str]:
    slide = _SLIDE_RE.fullmatch(name)
    if slide is not None:
        return (0, int(slide.group(1)), name)
    chart = re.fullmatch(r"ppt/charts/chart(\d+)\.xml", name)
    if chart is not None:
        return (1, int(chart.group(1)), name)
    return (2, 0, name)


@dataclass(frozen=True)
class TemplateSlot:
    id: str
    slide: int
    shape_id: int
    kind: str
    max_chars: int
    required: bool
    original_text_sha256: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class TemplateTextStyleRule:
    id: str
    slide_numbers: tuple[int, ...]
    kinds: tuple[str, ...]
    max_chars_lte: int | None
    font_face: str | None
    maximum_font_size_pt: float | None

    def applies_to(self, slot: TemplateSlot) -> bool:
        return (
            slot.slide in self.slide_numbers
            and slot.kind in self.kinds
            and (
                self.max_chars_lte is None
                or slot.max_chars <= self.max_chars_lte
            )
        )


@dataclass(frozen=True)
class TemplateChartSlot:
    id: str
    chart_part: str
    cache_index: int
    kind: str
    max_chars: int
    required: bool
    workbook_path: str
    workbook_shared_string_index: int | None = None
    workbook_cell: str | None = None


@dataclass(frozen=True)
class TemplatePack:
    id: str
    name: str
    manifest_path: Path
    template_path: Path
    template_sha256: str
    slide_count: int
    slots: tuple[TemplateSlot, ...]
    chart_slots: tuple[TemplateChartSlot, ...]
    text_style_rules: tuple[TemplateTextStyleRule, ...]
    supported_scenarios: tuple[str, ...]

    @property
    def slots_by_id(self) -> dict[str, TemplateSlot | TemplateChartSlot]:
        return {slot.id: slot for slot in (*self.slots, *self.chart_slots)}


@dataclass(frozen=True)
class SlotChange:
    slot_id: str
    slide: int
    shape_id: int
    original_text_sha256: str
    replacement_text_sha256: str
    replacement_chars: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "slide": self.slide,
            "shape_id": self.shape_id,
            "original_text_sha256": self.original_text_sha256,
            "replacement_text_sha256": self.replacement_text_sha256,
            "replacement_chars": self.replacement_chars,
        }


@dataclass(frozen=True)
class ChartChange:
    slot_id: str
    chart_part: str
    cache_index: int
    workbook_path: str
    original_text_sha256: str
    replacement_text_sha256: str
    replacement_chars: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "chart_part": self.chart_part,
            "cache_index": self.cache_index,
            "workbook_path": self.workbook_path,
            "original_text_sha256": self.original_text_sha256,
            "replacement_text_sha256": self.replacement_text_sha256,
            "replacement_chars": self.replacement_chars,
        }


@dataclass(frozen=True)
class TemplateAdaptationReport:
    template_pack_id: str
    source_path: Path
    output_path: Path
    source_sha256: str
    output_sha256: str
    slide_count: int
    package_entry_count: int
    changed_parts: tuple[str, ...]
    unchanged_part_count: int
    slot_changes: tuple[SlotChange | ChartChange, ...]
    source_integrity_preserved: bool
    no_op_copy: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "template_pack_id": self.template_pack_id,
            "source_path": str(self.source_path),
            "output_path": str(self.output_path),
            "source_sha256": self.source_sha256,
            "output_sha256": self.output_sha256,
            "slide_count": self.slide_count,
            "package_entry_count": self.package_entry_count,
            "changed_parts": list(self.changed_parts),
            "unchanged_part_count": self.unchanged_part_count,
            "slot_changes": [change.to_dict() for change in self.slot_changes],
            "source_integrity_preserved": self.source_integrity_preserved,
            "no_op_copy": self.no_op_copy,
        }


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TemplatePackError(f"{field} must be a non-empty string")
    return value.strip()


def _load_manifest_path(identifier: str | Path) -> Path:
    candidate = Path(identifier)
    if candidate.is_file():
        return candidate.resolve()
    matches: list[Path] = []
    if isinstance(identifier, str):
        for manifest in DEFAULT_DESIGN_PACK_ROOT.glob("*/template-pack.json"):
            try:
                payload = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if payload.get("id") == identifier:
                matches.append(manifest)
    if len(matches) != 1:
        raise TemplatePackError(
            f"template pack {identifier!r} resolved to {len(matches)} manifests"
        )
    return matches[0].resolve()


def load_template_pack(identifier: str | Path) -> TemplatePack:
    """Load a TemplatePack and fail closed when its physical source has drifted."""

    manifest_path = _load_manifest_path(identifier)
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplatePackError(f"cannot load template pack {manifest_path}: {exc}") from exc
    required = {
        "schema_version",
        "id",
        "name",
        "template_path",
        "template_sha256",
        "authorization",
        "slide_count",
        "slots",
    }
    missing = sorted(required - set(raw)) if isinstance(raw, dict) else sorted(required)
    if not isinstance(raw, dict) or missing:
        raise TemplatePackError(
            "template pack is missing required fields: " + ", ".join(missing)
        )
    if raw["schema_version"] != "1.0":
        raise TemplatePackError("unsupported TemplatePack schema_version")
    authorization = raw["authorization"]
    if not isinstance(authorization, dict) or authorization.get("status") != "user-authorized":
        raise TemplatePackError("TemplatePack must carry explicit user authorization")
    template_path = (
        manifest_path.parent / _required_string(raw["template_path"], "template_path")
    ).resolve()
    if not template_path.is_file():
        raise TemplatePackError(f"TemplatePack source is missing: {template_path}")
    expected_hash = _required_string(raw["template_sha256"], "template_sha256")
    if not _SHA256_RE.fullmatch(expected_hash):
        raise TemplatePackError("template_sha256 must be lowercase SHA-256")
    observed_hash = sha256_file(template_path)
    if observed_hash != expected_hash:
        raise TemplatePackError(
            f"TemplatePack source hash mismatch: expected {expected_hash}, observed {observed_hash}"
        )
    if type(raw["slide_count"]) is not int or raw["slide_count"] < 1:
        raise TemplatePackError("slide_count must be a positive integer")
    raw_slots = raw["slots"]
    if not isinstance(raw_slots, list) or not raw_slots:
        raise TemplatePackError("slots must be a non-empty array")
    slots: list[TemplateSlot] = []
    ids: set[str] = set()
    coordinates: set[tuple[int, int]] = set()
    for index, entry in enumerate(raw_slots):
        if not isinstance(entry, dict):
            raise TemplatePackError(f"slots[{index}] must be an object")
        slot_id = _required_string(entry.get("id"), f"slots[{index}].id")
        if slot_id in ids:
            raise TemplatePackError(f"duplicate slot id: {slot_id}")
        slide = entry.get("slide")
        shape_id = entry.get("shape_id")
        max_chars = entry.get("max_chars")
        if (
            type(slide) is not int
            or slide < 1
            or slide > raw["slide_count"]
            or type(shape_id) is not int
            or shape_id < 1
            or type(max_chars) is not int
            or max_chars < 1
        ):
            raise TemplatePackError(f"slots[{index}] has invalid coordinates or capacity")
        coordinate = (slide, shape_id)
        if coordinate in coordinates:
            raise TemplatePackError(f"multiple slots target slide {slide} shape {shape_id}")
        original_hash = entry.get("original_text_sha256")
        if original_hash is not None and (
            not isinstance(original_hash, str) or not _SHA256_RE.fullmatch(original_hash)
        ):
            raise TemplatePackError(
                f"slots[{index}].original_text_sha256 must be lowercase SHA-256"
            )
        slots.append(
            TemplateSlot(
                id=slot_id,
                slide=slide,
                shape_id=shape_id,
                kind=_required_string(entry.get("kind"), f"slots[{index}].kind"),
                max_chars=max_chars,
                required=entry.get("required") is True,
                original_text_sha256=original_hash,
                description=entry.get("description"),
            )
        )
        ids.add(slot_id)
        coordinates.add(coordinate)
    chart_slots: list[TemplateChartSlot] = []
    chart_coordinates: set[tuple[str, int]] = set()
    raw_chart_slots = raw.get("chart_slots", [])
    if not isinstance(raw_chart_slots, list):
        raise TemplatePackError("chart_slots must be an array")
    for index, entry in enumerate(raw_chart_slots):
        if not isinstance(entry, dict):
            raise TemplatePackError(f"chart_slots[{index}] must be an object")
        slot_id = _required_string(entry.get("id"), f"chart_slots[{index}].id")
        if slot_id in ids:
            raise TemplatePackError(f"duplicate slot id: {slot_id}")
        chart_part = _required_string(
            entry.get("chart_part"), f"chart_slots[{index}].chart_part"
        )
        workbook_path = _required_string(
            entry.get("workbook_path"), f"chart_slots[{index}].workbook_path"
        )
        cache_index = entry.get("cache_index")
        max_chars = entry.get("max_chars")
        shared_string_index = entry.get("workbook_shared_string_index")
        workbook_cell = entry.get("workbook_cell")
        if (
            type(cache_index) is not int
            or cache_index < 0
            or type(max_chars) is not int
            or max_chars < 1
            or (shared_string_index is None) == (workbook_cell is None)
            or (
                shared_string_index is not None
                and (type(shared_string_index) is not int or shared_string_index < 0)
            )
            or (
                workbook_cell is not None
                and (
                    not isinstance(workbook_cell, str)
                    or re.fullmatch(r"[A-Z]+[1-9][0-9]*", workbook_cell) is None
                )
            )
        ):
            raise TemplatePackError(
                f"chart_slots[{index}] has invalid cache/workbook coordinates"
            )
        chart_coordinate = (chart_part, cache_index)
        if chart_coordinate in chart_coordinates:
            raise TemplatePackError(
                f"multiple chart slots target {chart_part} cache index {cache_index}"
            )
        kind = _required_string(entry.get("kind"), f"chart_slots[{index}].kind")
        if kind not in {"chart-text", "chart-number"}:
            raise TemplatePackError(f"chart_slots[{index}].kind is unsupported")
        if kind == "chart-text" and shared_string_index is None:
            raise TemplatePackError(
                f"chart_slots[{index}] chart-text requires workbook_shared_string_index"
            )
        if kind == "chart-number" and workbook_cell is None:
            raise TemplatePackError(
                f"chart_slots[{index}] chart-number requires workbook_cell"
            )
        chart_slots.append(
            TemplateChartSlot(
                id=slot_id,
                chart_part=chart_part,
                cache_index=cache_index,
                kind=kind,
                max_chars=max_chars,
                required=entry.get("required") is True,
                workbook_path=workbook_path,
                workbook_shared_string_index=shared_string_index,
                workbook_cell=workbook_cell,
            )
        )
        ids.add(slot_id)
        chart_coordinates.add(chart_coordinate)
    text_style_rules: list[TemplateTextStyleRule] = []
    for index, entry in enumerate(raw.get("text_style_rules", [])):
        if not isinstance(entry, dict):
            raise TemplatePackError(f"text_style_rules[{index}] must be an object")
        slide_numbers = entry.get("slide_numbers")
        kinds = entry.get("kinds")
        max_chars_lte = entry.get("max_chars_lte")
        font_face = entry.get("font_face")
        maximum_font_size_pt = entry.get("maximum_font_size_pt")
        if (
            not isinstance(slide_numbers, list)
            or not slide_numbers
            or any(
                type(value) is not int
                or value < 1
                or value > raw["slide_count"]
                for value in slide_numbers
            )
        ):
            raise TemplatePackError(
                f"text_style_rules[{index}].slide_numbers is invalid"
            )
        if (
            not isinstance(kinds, list)
            or not kinds
            or any(
                not isinstance(value, str) or not value.strip()
                for value in kinds
            )
        ):
            raise TemplatePackError(f"text_style_rules[{index}].kinds is invalid")
        if max_chars_lte is not None and (
            type(max_chars_lte) is not int or max_chars_lte < 1
        ):
            raise TemplatePackError(
                f"text_style_rules[{index}].max_chars_lte is invalid"
            )
        if font_face is not None:
            font_face = _required_string(
                font_face, f"text_style_rules[{index}].font_face"
            )
        if maximum_font_size_pt is not None and (
            isinstance(maximum_font_size_pt, bool)
            or not isinstance(maximum_font_size_pt, (int, float))
            or not math.isfinite(float(maximum_font_size_pt))
            or float(maximum_font_size_pt) < 6
            or float(maximum_font_size_pt) > 240
        ):
            raise TemplatePackError(
                f"text_style_rules[{index}].maximum_font_size_pt is invalid"
            )
        if font_face is None and maximum_font_size_pt is None:
            raise TemplatePackError(
                f"text_style_rules[{index}] must change font face or size"
            )
        text_style_rules.append(
            TemplateTextStyleRule(
                id=_required_string(entry.get("id"), f"text_style_rules[{index}].id"),
                slide_numbers=tuple(slide_numbers),
                kinds=tuple(value.strip() for value in kinds),
                max_chars_lte=max_chars_lte,
                font_face=font_face,
                maximum_font_size_pt=(
                    float(maximum_font_size_pt)
                    if maximum_font_size_pt is not None
                    else None
                ),
            )
        )
    supported = raw.get("supported_scenarios", [])
    if not isinstance(supported, list) or any(
        not isinstance(value, str) or not value.strip() for value in supported
    ):
        raise TemplatePackError("supported_scenarios must be an array of strings")
    with zipfile.ZipFile(template_path) as archive:
        slide_count = sum(1 for name in archive.namelist() if _SLIDE_RE.fullmatch(name))
    if slide_count != raw["slide_count"]:
        raise TemplatePackError(
            f"TemplatePack declares {raw['slide_count']} slides but contains {slide_count}"
        )
    return TemplatePack(
        id=_required_string(raw["id"], "id"),
        name=_required_string(raw["name"], "name"),
        manifest_path=manifest_path,
        template_path=template_path,
        template_sha256=expected_hash,
        slide_count=raw["slide_count"],
        slots=tuple(slots),
        chart_slots=tuple(chart_slots),
        text_style_rules=tuple(text_style_rules),
        supported_scenarios=tuple(value.strip() for value in supported),
    )


def load_template_bindings(path: str | Path) -> tuple[str, dict[str, str]]:
    """Load a deterministic TemplatePack binding document."""

    binding_path = Path(path)
    try:
        raw = json.loads(binding_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplatePackError(f"cannot load template bindings {binding_path}: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version",
        "template_pack_id",
        "bindings",
    }:
        raise TemplatePackError(
            "binding document must contain schema_version, template_pack_id, and bindings"
        )
    if raw["schema_version"] != "1.0":
        raise TemplatePackError("unsupported template binding schema_version")
    pack_id = _required_string(raw["template_pack_id"], "template_pack_id")
    bindings = raw["bindings"]
    if not isinstance(bindings, dict):
        raise TemplatePackError("bindings must be an object")
    normalized: dict[str, str] = {}
    for slot_id, value in bindings.items():
        if not isinstance(slot_id, str) or not slot_id.strip():
            raise TemplatePackError("binding slot ids must be non-empty strings")
        if not isinstance(value, str):
            raise TemplatePackError(f"binding {slot_id} must be a string")
        normalized[slot_id.strip()] = value
    return pack_id, normalized


def _shape_bounds(xml: str, c_nv_pr_start: int) -> tuple[int, int]:
    candidates: list[tuple[int, str]] = []
    prefix = xml[:c_nv_pr_start]
    for kind in _SHAPE_KINDS:
        matches = list(re.finditer(rf"<p:{kind}(?:\s|>)", prefix))
        if matches:
            candidates.append((matches[-1].start(), kind))
    if not candidates:
        raise TemplatePackError("slot cNvPr has no supported shape ancestor")
    start, kind = max(candidates)
    end_match = re.search(rf"</p:{kind}>", xml[c_nv_pr_start:])
    if end_match is None:
        raise TemplatePackError(f"slot shape p:{kind} has no closing tag")
    end = c_nv_pr_start + end_match.end()
    return start, end


def _shape_text(segment: str) -> str:
    return "\n".join(html.unescape(match.group(2)) for match in _TEXT_RE.finditer(segment))


def _replace_shape_text(segment: str, replacement: str) -> str:
    matches = list(_TEXT_RE.finditer(segment))
    if not matches:
        raise TemplatePackError("declared text slot targets a shape without a:t nodes")
    pieces = replacement.splitlines() if "\n" in replacement else [replacement]
    if len(pieces) > len(matches):
        pieces = [*pieces[: len(matches) - 1], "\n".join(pieces[len(matches) - 1 :])]
    values = [*pieces, *([""] * (len(matches) - len(pieces)))]
    output: list[str] = []
    cursor = 0
    for match, value in zip(matches, values, strict=True):
        output.append(segment[cursor : match.start()])
        output.append(match.group(1))
        output.append(html.escape(value, quote=False))
        output.append(match.group(3))
        cursor = match.end()
    output.append(segment[cursor:])
    return "".join(output)


def _replace_xml_attribute(tag: str, attribute: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = re.compile(rf"(\s{re.escape(attribute)}=)([\"']).*?\2")
    if pattern.search(tag):
        return pattern.sub(rf'\1"{escaped}"', tag, count=1)
    insertion = tag.rfind("/>")
    if insertion < 0:
        insertion = tag.rfind(">")
    return tag[:insertion] + f' {attribute}="{escaped}"' + tag[insertion:]


def _apply_text_style(
    segment: str,
    rules: tuple[TemplateTextStyleRule, ...],
) -> str:
    if not rules:
        return segment
    font_face = next(
        (rule.font_face for rule in reversed(rules) if rule.font_face is not None),
        None,
    )
    font_size_caps = [
        rule.maximum_font_size_pt
        for rule in rules
        if rule.maximum_font_size_pt is not None
    ]
    maximum_font_size_pt = min(font_size_caps) if font_size_caps else None

    if maximum_font_size_pt is not None:
        maximum_size = str(round(maximum_font_size_pt * 100))

        def clamp_size(match: re.Match[str]) -> str:
            tag = match.group(0)
            existing = re.search(r'\ssz=([\"\'])(\d+)\1', tag)
            if existing is None or int(existing.group(2)) > int(maximum_size):
                return _replace_xml_attribute(tag, "sz", maximum_size)
            return tag

        segment = re.sub(r"<a:(?:rPr|defRPr)\b[^>]*>", clamp_size, segment)

    if font_face is not None:
        segment = re.sub(
            r"<a:(?:latin|ea|cs)\b[^>]*/>",
            lambda match: _replace_xml_attribute(
                match.group(0), "typeface", font_face
            ),
            segment,
        )
    return segment


def _replace_slot(
    xml_bytes: bytes,
    slot: TemplateSlot,
    replacement: str,
    style_rules: tuple[TemplateTextStyleRule, ...] = (),
) -> tuple[bytes, SlotChange]:
    if len(replacement) > slot.max_chars:
        raise TemplatePackError(
            f"binding {slot.id} has {len(replacement)} chars; capacity is {slot.max_chars}"
        )
    try:
        xml = xml_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TemplatePackError(f"slide {slot.slide} XML is not UTF-8") from exc
    marker = re.compile(rf"<p:cNvPr\b(?=[^>]*\bid=[\"']{slot.shape_id}[\"'])[^>]*>")
    markers = list(marker.finditer(xml))
    if len(markers) != 1:
        raise TemplatePackError(
            f"slot {slot.id} expected one cNvPr id={slot.shape_id}; found {len(markers)}"
        )
    start, end = _shape_bounds(xml, markers[0].start())
    segment = xml[start:end]
    original_text = _shape_text(segment)
    original_hash = sha256_bytes(original_text.encode("utf-8"))
    if slot.original_text_sha256 is not None and original_hash != slot.original_text_sha256:
        raise TemplatePackError(
            f"slot {slot.id} original text hash mismatch; template map is stale"
        )
    replacement_segment = _replace_shape_text(segment, replacement)
    replacement_segment = _apply_text_style(replacement_segment, style_rules)
    updated = (xml[:start] + replacement_segment + xml[end:]).encode("utf-8")
    return updated, SlotChange(
        slot_id=slot.id,
        slide=slot.slide,
        shape_id=slot.shape_id,
        original_text_sha256=original_hash,
        replacement_text_sha256=sha256_bytes(replacement.encode("utf-8")),
        replacement_chars=len(replacement),
    )


def _replace_chart_cache(
    xml_bytes: bytes,
    slot: TemplateChartSlot,
    replacement: str,
) -> tuple[bytes, ChartChange]:
    xml = xml_bytes.decode("utf-8")
    matches = list(re.finditer(r"(<c:v>)(.*?)(</c:v>)", xml, re.DOTALL))
    if slot.cache_index >= len(matches):
        raise TemplatePackError(
            f"chart slot {slot.id} cache index {slot.cache_index} is out of range"
        )
    match = matches[slot.cache_index]
    original = html.unescape(match.group(2))
    updated = (
        xml[: match.start()]
        + match.group(1)
        + html.escape(replacement, quote=False)
        + match.group(3)
        + xml[match.end() :]
    ).encode("utf-8")
    return updated, ChartChange(
        slot_id=slot.id,
        chart_part=slot.chart_part,
        cache_index=slot.cache_index,
        workbook_path=slot.workbook_path,
        original_text_sha256=sha256_bytes(original.encode("utf-8")),
        replacement_text_sha256=sha256_bytes(replacement.encode("utf-8")),
        replacement_chars=len(replacement),
    )


def _replace_shared_string(xml: str, index: int, replacement: str) -> str:
    items = list(re.finditer(r"<si\b[^>]*>.*?</si>", xml, re.DOTALL))
    if index >= len(items):
        raise TemplatePackError(f"workbook shared-string index {index} is out of range")
    item = items[index]
    segment = item.group(0)
    text = re.search(r"(<t\b[^>]*>)(.*?)(</t>)", segment, re.DOTALL)
    if text is None:
        raise TemplatePackError(f"workbook shared-string index {index} has no text")
    updated_segment = (
        segment[: text.start()]
        + text.group(1)
        + html.escape(replacement, quote=False)
        + text.group(3)
        + segment[text.end() :]
    )
    return xml[: item.start()] + updated_segment + xml[item.end() :]


def _replace_workbook_cell(xml: str, cell: str, replacement: str) -> str:
    cell_match = re.search(
        rf"<c\b(?=[^>]*\br=[\"']{re.escape(cell)}[\"'])[^>]*>.*?</c>",
        xml,
        re.DOTALL,
    )
    if cell_match is None:
        raise TemplatePackError(f"workbook cell {cell} is missing")
    segment = cell_match.group(0)
    value = re.search(r"(<v>)(.*?)(</v>)", segment, re.DOTALL)
    if value is None:
        raise TemplatePackError(f"workbook cell {cell} has no value")
    updated_segment = (
        segment[: value.start()]
        + value.group(1)
        + html.escape(replacement, quote=False)
        + value.group(3)
        + segment[value.end() :]
    )
    return xml[: cell_match.start()] + updated_segment + xml[cell_match.end() :]


def _patch_embedded_workbook(
    workbook_bytes: bytes,
    slots: list[TemplateChartSlot],
    bindings: Mapping[str, str],
) -> bytes:
    source_buffer = io.BytesIO(workbook_bytes)
    output_buffer = io.BytesIO()
    with zipfile.ZipFile(source_buffer, "r") as source_zip, zipfile.ZipFile(
        output_buffer, "w"
    ) as output_zip:
        for info in source_zip.infolist():
            data = source_zip.read(info.filename)
            if info.filename == "xl/sharedStrings.xml":
                xml = data.decode("utf-8")
                for slot in sorted(
                    (
                        item
                        for item in slots
                        if item.workbook_shared_string_index is not None
                    ),
                    key=lambda item: item.workbook_shared_string_index,
                    reverse=True,
                ):
                    xml = _replace_shared_string(
                        xml,
                        slot.workbook_shared_string_index,
                        bindings[slot.id],
                    )
                data = xml.encode("utf-8")
            elif info.filename == "xl/worksheets/sheet1.xml":
                xml = data.decode("utf-8")
                for slot in (
                    item for item in slots if item.workbook_cell is not None
                ):
                    xml = _replace_workbook_cell(
                        xml,
                        slot.workbook_cell,
                        bindings[slot.id],
                    )
                data = xml.encode("utf-8")
            output_zip.writestr(info, data)
    return output_buffer.getvalue()


def _validate_bindings(
    pack: TemplatePack,
    bindings: Mapping[str, str],
    *,
    require_all_required: bool,
) -> dict[str, str]:
    slots = pack.slots_by_id
    unknown = sorted(set(bindings) - set(slots))
    if unknown:
        raise TemplatePackError("unknown TemplatePack slots: " + ", ".join(unknown))
    if require_all_required:
        missing = sorted(
            slot.id
            for slot in (*pack.slots, *pack.chart_slots)
            if slot.required and slot.id not in bindings
        )
        if missing:
            raise TemplatePackError(
                "missing required TemplatePack bindings: " + ", ".join(missing)
            )
    normalized: dict[str, str] = {}
    for slot_id, value in bindings.items():
        if not isinstance(value, str):
            raise TemplatePackError(f"binding {slot_id} must be a string")
        slot = slots[slot_id]
        if len(value) > slot.max_chars:
            raise TemplatePackError(
                f"binding {slot_id} has {len(value)} chars; capacity is {slot.max_chars}"
            )
        if isinstance(slot, TemplateChartSlot) and slot.kind == "chart-number":
            try:
                numeric = float(value)
            except ValueError as exc:
                raise TemplatePackError(
                    f"binding {slot_id} must be a finite chart number"
                ) from exc
            if not math.isfinite(numeric):
                raise TemplatePackError(
                    f"binding {slot_id} must be a finite chart number"
                )
        normalized[slot_id] = value
    return normalized


def adapt_template_pack(
    pack: TemplatePack | str | Path,
    bindings: Mapping[str, str],
    output_path: str | Path,
    *,
    require_all_required: bool = True,
) -> TemplateAdaptationReport:
    """Adapt declared text slots and atomically promote a source-safe PPTX."""

    resolved_pack = pack if isinstance(pack, TemplatePack) else load_template_pack(pack)
    normalized = _validate_bindings(
        resolved_pack,
        bindings,
        require_all_required=require_all_required,
    )
    output = Path(output_path).expanduser().resolve(strict=False)
    source = resolved_pack.template_path.resolve()
    if output == source:
        raise TemplatePackError("TemplatePack output must not overwrite its source")
    output.parent.mkdir(parents=True, exist_ok=True)
    source_hash_before = sha256_file(source)
    candidate_fd, candidate_name = tempfile.mkstemp(
        prefix=f".{output.stem}.",
        suffix=".candidate.pptx",
        dir=output.parent,
    )
    os.close(candidate_fd)
    candidate = Path(candidate_name)
    changed_parts: set[str] = set()
    changes: list[SlotChange | ChartChange] = []
    try:
        if not normalized:
            shutil.copy2(source, candidate)
        else:
            slots_by_slide: dict[int, list[TemplateSlot]] = {}
            slots_by_chart: dict[str, list[TemplateChartSlot]] = {}
            slots_by_workbook: dict[str, list[TemplateChartSlot]] = {}
            for slot_id in normalized:
                slot = resolved_pack.slots_by_id[slot_id]
                if isinstance(slot, TemplateSlot):
                    slots_by_slide.setdefault(slot.slide, []).append(slot)
                else:
                    slots_by_chart.setdefault(slot.chart_part, []).append(slot)
                    slots_by_workbook.setdefault(slot.workbook_path, []).append(slot)
            with zipfile.ZipFile(source, "r") as source_zip, zipfile.ZipFile(
                candidate, "w"
            ) as output_zip:
                for info in source_zip.infolist():
                    data = source_zip.read(info.filename)
                    match = _SLIDE_RE.fullmatch(info.filename)
                    if match is not None:
                        slide = int(match.group(1))
                        for slot in sorted(
                            slots_by_slide.get(slide, []),
                            key=lambda value: value.shape_id,
                            reverse=True,
                        ):
                            data, change = _replace_slot(
                                data,
                                slot,
                                normalized[slot.id],
                                tuple(
                                    rule
                                    for rule in resolved_pack.text_style_rules
                                    if rule.applies_to(slot)
                                ),
                            )
                            changes.append(change)
                            changed_parts.add(info.filename)
                    elif info.filename in slots_by_chart:
                        for slot in sorted(
                            slots_by_chart[info.filename],
                            key=lambda value: value.cache_index,
                            reverse=True,
                        ):
                            data, change = _replace_chart_cache(
                                data,
                                slot,
                                normalized[slot.id],
                            )
                            changes.append(change)
                        changed_parts.add(info.filename)
                    elif info.filename in slots_by_workbook:
                        data = _patch_embedded_workbook(
                            data,
                            slots_by_workbook[info.filename],
                            normalized,
                        )
                        changed_parts.add(info.filename)
                    output_zip.writestr(info, data)
            with zipfile.ZipFile(source, "r") as source_zip, zipfile.ZipFile(
                candidate, "r"
            ) as output_zip:
                if source_zip.namelist() != output_zip.namelist():
                    raise TemplatePackError("adaptation changed the package entry inventory")
                for name in source_zip.namelist():
                    if name not in changed_parts and source_zip.read(name) != output_zip.read(name):
                        raise TemplatePackError(
                            f"adaptation unexpectedly changed unbound package part {name}"
                        )
        with zipfile.ZipFile(candidate, "r") as archive:
            names = archive.namelist()
            slide_count = sum(1 for name in names if _SLIDE_RE.fullmatch(name))
            if slide_count != resolved_pack.slide_count:
                raise TemplatePackError(
                    f"adapted package has {slide_count} slides; expected {resolved_pack.slide_count}"
                )
            package_entry_count = len(names)
        source_hash_after = sha256_file(source)
        if source_hash_after != source_hash_before:
            raise TemplatePackError("TemplatePack source changed during adaptation")
        os.replace(candidate, output)
    except Exception:
        candidate.unlink(missing_ok=True)
        raise
    return TemplateAdaptationReport(
        template_pack_id=resolved_pack.id,
        source_path=source,
        output_path=output,
        source_sha256=source_hash_before,
        output_sha256=sha256_file(output),
        slide_count=resolved_pack.slide_count,
        package_entry_count=package_entry_count,
        changed_parts=tuple(
            sorted(
                changed_parts,
                key=_part_sort_key,
            )
        ),
        unchanged_part_count=package_entry_count - len(changed_parts),
        slot_changes=tuple(sorted(changes, key=lambda item: item.slot_id)),
        source_integrity_preserved=sha256_file(source) == source_hash_before,
        no_op_copy=not normalized,
    )


def write_adaptation_report(
    report: TemplateAdaptationReport,
    path: str | Path,
) -> Path:
    """Write an atomic JSON evidence record for a completed adaptation."""

    output = Path(path).expanduser().resolve(strict=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, candidate_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".candidate",
        dir=output.parent,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(report.to_dict(), handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(candidate_name, output)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        Path(candidate_name).unlink(missing_ok=True)
        raise
    return output


__all__ = [
    "TemplateAdaptationReport",
    "TemplatePack",
    "TemplatePackError",
    "TemplateChartSlot",
    "TemplateSlot",
    "adapt_template_pack",
    "load_template_bindings",
    "load_template_pack",
    "write_adaptation_report",
]
