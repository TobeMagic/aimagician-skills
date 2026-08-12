"""Certified page template library for physical assembly (v6.1).

Compiles the v6.1 page-template index from the Gaojie certified core, exposes
deterministic role-based queries, and resolves a private root from CLI args,
env, or the per-user config file.

The index records the physical identity of every certified page:

- ``page_id`` — package SHA-256 + slide ordinal,
- ``source_path`` — absolute path to the source ``.pptx``,
- ``source_sha256`` — SHA-256 of the source bytes,
- ``structure`` — slide/layout/master/theme/media counts,
- ``slot_graph`` — text slots discovered from the certified slide ordinal.
- ``governed_content_inventory`` — table/chart/workbook and closure content
  that must be authority-bound or proven absent before physical reuse.

The index is deterministic: identical inputs always produce identical bytes
(field order and the reproducible-build timestamp are fixed; no floating-point
keys appear in any record). Wall-clock execution time belongs in run evidence,
not in the content-addressed library.
"""

from __future__ import annotations

import colorsys
import hashlib
import io
import json
import os
import posixpath
import re
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from xml.etree import ElementTree as ET

from .workbook_security import WorkbookSecurityError, mutate_governed_xlsx

CERTIFIED_CORE_SCHEMA = "gaojie-certified-core.v2"
DEFAULT_DOMINANT_STYLE_CLUSTER = "ivory-green-gold-editorial"
DETERMINISTIC_COMPILED_AT = "1970-01-01T00:00:00Z"
# Compatibility must be explicit.  The default group contains only the
# dominant cluster, so an unregistered library can never cross style families.
DEFAULT_COMPATIBLE_STYLE_CLUSTERS: tuple[str, ...] = (
    DEFAULT_DOMINANT_STYLE_CLUSTER,
)
DEFAULT_SCORING: Mapping[str, float] = {
    "role": 0.30,
    "capacity": 0.25,
    "semantic": 0.20,
    "style": 0.15,
    "editability": 0.10,
}
CONFIG_PATH = Path("~/.config/window-pptx/library.json").expanduser()
PAGE_ID_RE = re.compile(r"^([0-9a-f]{64}):(\d{3})$")
NON_DIRECT_DECISIONS = frozenset(
    {"reference-only", "deny", "denied", "archive", "quarantine"}
)


class PageTemplateError(ValueError):
    """An index operation has failed for a documented reason."""


def _unknown_governed_content_inventory() -> dict[str, Any]:
    """Return the fail-closed value used only for legacy index loading."""

    return {
        "schema_version": "governed-content-inventory.v1",
        "peer_mapping_method": "unknown",
        "policy": "locked-authority-required",
        "complete": False,
        "content_slot_count": 0,
        "customer_data_slot_count": 0,
        "slots": [],
        "closure_metadata": {
            "table_count": 0,
            "chart_part_count": 0,
            "workbook_part_count": 0,
            "notes_part_count": 0,
            "comment_part_count": 0,
            "diagram_part_count": 0,
            "layout_master_field_count": 0,
            "layout_master_fields": [],
            "tag_part_count": 0,
            "tag_parts": [],
            "media_count": 0,
            "media_parts": [],
        },
        "scan_errors": ["inventory-missing"],
    }


def _governed_content_inventory_is_known(value: Any) -> bool:
    """Recognize the minimum complete contract before restoring eligibility."""

    if not isinstance(value, Mapping):
        return False
    required = {
        "schema_version",
        "peer_mapping_method",
        "policy",
        "complete",
        "content_slot_count",
        "customer_data_slot_count",
        "slots",
        "closure_metadata",
        "scan_errors",
    }
    if not required.issubset(value):
        return False
    if value.get("schema_version") != "governed-content-inventory.v1":
        return False
    if value.get("peer_mapping_method") != "chart-formula-range-v1":
        return False
    if value.get("policy") not in {
        "no-embedded-content",
        "locked-authority-required",
    }:
        return False
    if not isinstance(value.get("complete"), bool):
        return False
    if not isinstance(value.get("content_slot_count"), int) or isinstance(
        value.get("content_slot_count"), bool
    ):
        return False
    if not isinstance(value.get("customer_data_slot_count"), int) or isinstance(
        value.get("customer_data_slot_count"), bool
    ):
        return False
    slots = value.get("slots")
    if not isinstance(slots, list) or any(
        not isinstance(slot, Mapping)
        or not {
            "slot_id",
            "kind",
            "source_part",
            "locator",
            "source_text",
            "source_text_sha256",
            "peer_group_id",
            "semantic_role",
            "series_index",
            "point_index",
            "worksheet_ordinal",
            "cell_ref",
            "value_type",
        }.issubset(slot)
        for slot in slots
    ):
        return False
    if value.get("content_slot_count") != len(slots):
        return False
    if value.get("customer_data_slot_count") != len(slots):
        return False
    slot_ids = [str(slot["slot_id"]) for slot in slots]
    if len(slot_ids) != len(set(slot_ids)):
        return False
    peer_groups: dict[str, list[Mapping[str, Any]]] = {}
    for slot in slots:
        peer_group_id = slot.get("peer_group_id")
        if isinstance(peer_group_id, str) and peer_group_id:
            peer_groups.setdefault(peer_group_id, []).append(slot)
    coordinate_fields = (
        "semantic_role",
        "series_index",
        "point_index",
        "worksheet_ordinal",
        "cell_ref",
        "value_type",
    )
    for members in peer_groups.values():
        if len(members) != 2 or {member.get("kind") for member in members} != {
            "chart-value",
            "workbook-cell",
        }:
            return False
        if any(
            members[0].get(field_name) != members[1].get(field_name)
            for field_name in coordinate_fields
        ):
            return False
        if (
            members[0].get("series_index") is None
            or members[0].get("point_index") is None
            or members[0].get("worksheet_ordinal") is None
            or members[0].get("cell_ref") is None
        ):
            return False
    if value.get("complete") and value.get("scan_errors"):
        return False
    return isinstance(value.get("closure_metadata"), Mapping) and isinstance(
        value.get("scan_errors"), list
    )


def _is_reference_only_pool(pool: str | None) -> bool:
    return bool(pool) and (
        pool == "reference-only" or pool.startswith("reference-only/")
    )


def _is_non_direct_decision(decision: str | None) -> bool:
    return bool(decision) and decision.lower() in NON_DIRECT_DECISIONS


@dataclass(frozen=True)
class SlotRecord:
    slot_id: str
    shape_id: int
    kind: str
    max_chars: int
    text: str
    semantic_role: str
    region: str
    reading_order: int
    bbox: Mapping[str, int]
    source_char_count: int
    source_line_count: int
    source_run_count: int
    group_id: str | None
    group_order: int | None
    font_size_pt: float | None
    allowed_binding_modes: tuple[str, ...]


@dataclass(frozen=True)
class PageTemplate:
    schema_version: str
    page_id: str
    package_sha256: str
    slide_number: int
    source_path: str
    source_sha256: str
    source_slide_sha256: str
    page_role: str
    category_names: tuple[str, ...]
    style_cluster_id: str
    deck_family_id: str
    theme_palette: tuple[str, ...]
    capacity: Mapping[str, int]
    editability: str
    certification: str
    visual_quality: float
    structure: Mapping[str, Any]
    slot_graph: Mapping[str, Any]
    requires_customer_asset: bool
    media_retention_policy: str
    pool: str | None = None
    decision: str | None = None
    direct_use: bool = True
    eligibility_known: bool = True
    style_features: Mapping[str, Any] = field(default_factory=dict)
    governed_content_inventory: Mapping[str, Any] = field(
        default_factory=_unknown_governed_content_inventory
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "page_id": self.page_id,
            "package_sha256": self.package_sha256,
            "slide_number": self.slide_number,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "source_slide_sha256": self.source_slide_sha256,
            "page_role": self.page_role,
            "category_names": list(self.category_names),
            "style_cluster_id": self.style_cluster_id,
            "deck_family_id": self.deck_family_id,
            "theme_palette": list(self.theme_palette),
            "capacity": dict(self.capacity),
            "editability": self.editability,
            "certification": self.certification,
            "visual_quality": self.visual_quality,
            "structure": dict(self.structure),
            "slot_graph": dict(self.slot_graph),
            "requires_customer_asset": self.requires_customer_asset,
            "media_retention_policy": self.media_retention_policy,
            "pool": self.pool,
            "decision": self.decision,
            "direct_use": self.direct_use,
            "eligibility_known": self.eligibility_known,
            "style_features": dict(self.style_features),
            "governed_content_inventory": dict(self.governed_content_inventory),
        }


@dataclass(frozen=True)
class CandidateScores:
    """The five bounded score components and their exact weighted total."""

    role: float
    capacity: float
    semantic: float
    style: float
    editability: float
    total: float

    def to_dict(self) -> dict[str, float]:
        return {
            "role": self.role,
            "capacity": self.capacity,
            "semantic": self.semantic,
            "style": self.style,
            "editability": self.editability,
            "total": self.total,
        }


@dataclass(frozen=True)
class PageTemplateCandidate:
    """One ranked candidate plus complete deterministic selection evidence."""

    page_template: PageTemplate
    eligibility: bool
    reasons: tuple[str, ...]
    fallback_reason: str | None
    asset_fit: float
    capacity_fit: bool
    residue_risk: float
    style_compatibility: str
    scores: CandidateScores

    def to_dict(self) -> dict[str, Any]:
        # Query results are designed to be persisted in a clean client
        # project.  Keep physical lineage and slot capacity, but never export
        # the private source locator or literal commercial-template copy.
        public_template = self.page_template.to_dict()
        public_template["source_path"] = (
            f"private://{self.page_template.package_sha256}/"
            f"slide-{self.page_template.slide_number:03d}"
        )
        slot_graph = dict(public_template.get("slot_graph", {}))
        public_slots: list[dict[str, Any]] = []
        for raw_slot in slot_graph.get("slots", ()):
            slot = dict(raw_slot)
            slot["source_text"] = ""
            public_slots.append(slot)
        slot_graph["slots"] = public_slots
        public_template["slot_graph"] = slot_graph
        inventory = dict(public_template.get("governed_content_inventory", {}))
        public_content_slots: list[dict[str, Any]] = []
        for raw_slot in inventory.get("slots", ()):
            slot = dict(raw_slot)
            slot["source_text"] = ""
            public_content_slots.append(slot)
        inventory["slots"] = public_content_slots
        public_template["governed_content_inventory"] = inventory
        return {
            "schema_version": "1.0",
            "page_id": self.page_template.page_id,
            "eligibility": self.eligibility,
            "reasons": list(self.reasons),
            "fallback_reason": self.fallback_reason,
            "asset_fit": self.asset_fit,
            "capacity_fit": self.capacity_fit,
            "residue_risk": self.residue_risk,
            "style_compatibility": self.style_compatibility,
            "scores": self.scores.to_dict(),
            "weights": dict(DEFAULT_SCORING),
            "page_template": public_template,
        }


@dataclass(frozen=True)
class LibraryIndex:
    schema_version: str
    library_id: str
    compiled_at: str
    source_core_schema: str
    private_root_sha256: str
    source_package_count: int
    source_package_index: Mapping[str, Mapping[str, Any]]
    page_template_count: int
    role_index: Mapping[str, int]
    style_cluster_index: Mapping[str, int]
    deck_family_index: Mapping[str, int]
    category_index: Mapping[str, int]
    scoring: Mapping[str, float]
    dominant_style_cluster_id: str
    compatible_style_cluster_ids: tuple[str, ...]
    page_templates: tuple[PageTemplate, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "library_id": self.library_id,
            "compiled_at": self.compiled_at,
            "source_core_schema": self.source_core_schema,
            "private_root_sha256": self.private_root_sha256,
            "source_package_count": self.source_package_count,
            "source_package_index": {
                key: dict(value)
                for key, value in self.source_package_index.items()
            },
            "page_template_count": self.page_template_count,
            "role_index": dict(self.role_index),
            "style_cluster_index": dict(self.style_cluster_index),
            "deck_family_index": dict(self.deck_family_index),
            "category_index": dict(self.category_index),
            "scoring": dict(self.scoring),
            "dominant_style_cluster_id": self.dominant_style_cluster_id,
            "compatible_style_cluster_ids": list(self.compatible_style_cluster_ids),
            "page_templates": [template.to_dict() for template in self.page_templates],
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_directory(root: Path) -> str:
    """Hash the asset-index + certified-core files for fast root identity."""

    h = hashlib.sha256()
    for sub in (
        "intelligence/gaojie/asset-index.json",
        "intelligence/gaojie/certified-core.json",
    ):
        path = root / sub
        if path.is_file():
            h.update(sub.encode("utf-8"))
            h.update(b"\0")
            h.update(_sha256_file(path).encode("ascii"))
            h.update(b"\0")
    return h.hexdigest()


def resolve_private_root(
    *,
    explicit: str | os.PathLike[str] | None = None,
    env_var: str | None = "WINDOW_PPTX_PRIVATE_ROOT",
    config_path: Path | None = CONFIG_PATH,
) -> Path:
    """Resolve the private Gaojie root from CLI flag, env var, then config."""

    if explicit is not None:
        root = Path(explicit).expanduser().resolve(strict=False)
        if not (root / "intelligence" / "gaojie" / "asset-index.json").is_file():
            raise PageTemplateError(
                f"explicit private root missing asset-index: {root}"
            )
        return root
    if env_var:
        value = os.environ.get(env_var)
        if value:
            root = Path(value).expanduser().resolve(strict=False)
            if not (root / "intelligence" / "gaojie" / "asset-index.json").is_file():
                raise PageTemplateError(
                    f"{env_var} root missing asset-index: {root}"
                )
            return root
    if config_path is not None and config_path.is_file():
        try:
            raw = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PageTemplateError(f"cannot read {config_path}: {exc}") from exc
        candidate = raw.get("private_root") if isinstance(raw, dict) else None
        if candidate:
            root = Path(candidate).expanduser().resolve(strict=False)
            if not (root / "intelligence" / "gaojie" / "asset-index.json").is_file():
                raise PageTemplateError(
                    f"config private root missing asset-index: {root}"
                )
            return root
    raise PageTemplateError(
        "private root unresolved: pass --private-root, set "
        "WINDOW_PPTX_PRIVATE_ROOT, or write ~/.config/window-pptx/library.json"
    )


_SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
_LAYOUT_RE = re.compile(r"^ppt/slideLayouts/slideLayout(\d+)\.xml$")
_MASTER_RE = re.compile(r"^ppt/slideMasters/slideMaster(\d+)\.xml$")
_THEME_RE = re.compile(r"^ppt/theme/theme(\d+)\.xml$")
_CNVPR_RE = re.compile(r'<p:cNvPr\b[^>]*\bid="(\d+)"[^>]*\bname="([^"]*)"')
_TEXT_RE = re.compile(r"<a:t\b[^>]*>(.*?)</a:t>", re.DOTALL)
_NATIVE_PAGE_OBJECT_RE = re.compile(
    r"<p:(?:sp|graphicFrame|grpSp)\b",
    re.IGNORECASE,
)
_SRGB_RE = re.compile(r'(?:val|lastClr)="([0-9A-Fa-f]{6})"')
_TABLE_RE = re.compile(r"<(?:a:tbl|a:graphicData\b[^>]*\buri=\"[^\"]*/table\")")
_RELATIONSHIP_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
_OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_A1_CELL_RE = re.compile(r"^\$?([A-Za-z]{1,3})\$?([1-9][0-9]{0,6})$")
_CHART_FORMULA_RE = re.compile(
    r"^(?P<sheet>'(?:[^']|'')+'|[^!]+)!"
    r"(?P<start>\$?[A-Za-z]{1,3}\$?[1-9][0-9]{0,6})"
    r"(?::(?P<end>\$?[A-Za-z]{1,3}\$?[1-9][0-9]{0,6}))?$"
)
_EMU_PER_POINT = 12700
_DEFAULT_SLIDE_WIDTH = 12192000
_DEFAULT_SLIDE_HEIGHT = 6858000
_STYLE_PART_PREFIXES = (
    "ppt/slideLayouts/",
    "ppt/slideMasters/",
    "ppt/theme/",
)


def _relationship_part_name(owner_part: str) -> str:
    directory, filename = posixpath.split(owner_part)
    return posixpath.join(directory, "_rels", f"{filename}.rels")


def _resolve_relationship_target(owner_part: str, target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join(posixpath.dirname(owner_part), target))


def _read_relationships(
    archive: zipfile.ZipFile,
    owner_part: str,
) -> tuple[dict[str, str], ...]:
    """Read the relationship part belonging to ``owner_part``.

    Relationship targets are resolved against their immediate owner, not the
    original slide.  That distinction matters for the slide -> layout ->
    master -> theme chain and mirrors OPC target resolution.
    """

    rels_name = _relationship_part_name(owner_part)
    try:
        root = ET.fromstring(archive.read(rels_name))
    except KeyError:
        return ()
    except ET.ParseError as exc:
        raise PageTemplateError(
            f"invalid relationships XML {rels_name}: {exc}"
        ) from exc
    relationships: list[dict[str, str]] = []
    for node in root.findall(f"{{{_RELATIONSHIP_NS}}}Relationship"):
        target = node.attrib.get("Target")
        if not target:
            continue
        relationships.append(
            {
                "id": node.attrib.get("Id", ""),
                "type": node.attrib.get("Type", ""),
                "target": target,
                "target_mode": node.attrib.get("TargetMode", "Internal"),
            }
        )
    return tuple(relationships)


def _read_slide_material(
    archive: zipfile.ZipFile,
    slide_number: int,
) -> tuple[str, str, int, int, dict[str, int]]:
    """Return the selected slide XML plus its linked style XML.

    Only layout/master/theme XML is gathered for style analysis.  The direct
    slide relationship count is retained as page evidence, while traversal is
    recursive so a theme linked by the master cannot be confused with another
    slide's theme.
    """

    slide_part = f"ppt/slides/slide{slide_number}.xml"
    slide_xml = archive.read(slide_part).decode("utf-8", errors="replace")
    names = set(archive.namelist())
    direct_relationships = _read_relationships(archive, slide_part)
    page_assets = {
        "page_image_count": sum(
            relationship["type"].lower().endswith("/image")
            for relationship in direct_relationships
        ),
        "page_chart_count": sum(
            relationship["type"].lower().endswith("/chart")
            for relationship in direct_relationships
        ),
        "page_media_count": sum(
            relationship["type"].lower().endswith(
                ("/image", "/audio", "/video", "/media")
            )
            for relationship in direct_relationships
        ),
        "page_table_count": len(_TABLE_RE.findall(slide_xml)),
        "page_native_object_count": len(
            _NATIVE_PAGE_OBJECT_RE.findall(slide_xml)
        ),
    }
    queue = [slide_part]
    visited = {slide_part}
    linked_style_xml: list[str] = []
    linked_style_parts = 0
    while queue:
        owner_part = queue.pop(0)
        for relationship in _read_relationships(archive, owner_part):
            if relationship["target_mode"].lower() == "external":
                continue
            target_part = _resolve_relationship_target(
                owner_part,
                relationship["target"],
            )
            if target_part in visited or target_part not in names:
                continue
            if not target_part.startswith(_STYLE_PART_PREFIXES):
                continue
            visited.add(target_part)
            linked_style_parts += 1
            linked_style_xml.append(
                archive.read(target_part).decode("utf-8", errors="replace")
            )
            queue.append(target_part)
    return (
        slide_xml,
        "\n".join(linked_style_xml),
        len(direct_relationships),
        linked_style_parts,
        page_assets,
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _normalise_governed_value(value: str) -> str:
    return "".join(unicodedata.normalize("NFKC", value).split())


def _iter_xml_locators(root: ET.Element) -> Iterable[tuple[ET.Element, str]]:
    """Yield elements with deterministic, namespace-independent locators."""

    def visit(node: ET.Element, locator: str) -> Iterable[tuple[ET.Element, str]]:
        yield node, locator
        counts: Counter[str] = Counter()
        for child in list(node):
            local = _local_name(child.tag)
            counts[local] += 1
            yield from visit(child, f"{locator}/{local}[{counts[local]}]")

    root_name = _local_name(root.tag)
    yield from visit(root, f"/{root_name}[1]")


def _content_slot(
    *,
    kind: str,
    source_part: str,
    locator: str,
    source_text: str,
    semantic_role: str | None = None,
    series_index: int | None = None,
    point_index: int | None = None,
    worksheet_ordinal: int | None = None,
    cell_ref: str | None = None,
    value_type: str = "text",
) -> dict[str, Any]:
    stable = _sha256_bytes(
        f"{kind}\0{source_part}\0{locator}".encode("utf-8")
    )[:24]
    return {
        "slot_id": f"{kind.replace('-', '_')}_{stable}",
        "kind": kind,
        "source_part": source_part,
        "locator": locator,
        "source_text": source_text,
        "source_text_sha256": _sha256_bytes(source_text.encode("utf-8")),
        "peer_group_id": None,
        "semantic_role": semantic_role or kind,
        "series_index": series_index,
        "point_index": point_index,
        "worksheet_ordinal": worksheet_ordinal,
        "cell_ref": cell_ref,
        "value_type": value_type,
    }


def _slide_dependency_closure(
    archive: zipfile.ZipFile,
    slide_part: str,
) -> tuple[set[str], list[str]]:
    """Return the internal OPC closure used by one physical slide."""

    names = set(archive.namelist())
    visited: set[str] = {slide_part}
    queue = [slide_part]
    errors: list[str] = []
    while queue:
        owner = queue.pop(0)
        try:
            relationships = _read_relationships(archive, owner)
        except PageTemplateError:
            errors.append(
                "relationship-xml-invalid:"
                + _sha256_bytes(owner.encode("utf-8"))[:16]
            )
            continue
        for relationship in relationships:
            rel_type = relationship["type"].lower()
            if relationship["target_mode"].lower() == "external":
                if rel_type.endswith(
                    (
                        "/chart",
                        "/package",
                        "/oleobject",
                        "/notesslide",
                        "/comments",
                        "/diagramdata",
                    )
                ):
                    errors.append("external-governed-content")
                continue
            target = _resolve_relationship_target(owner, relationship["target"])
            # Internal slide-navigation links are not content dependencies of
            # the selected page and must not pull another customer page in.
            if target.startswith("ppt/slides/") and target != slide_part:
                continue
            if target not in names:
                errors.append(
                    "relationship-target-missing:"
                    + _sha256_bytes(f"{owner}\0{relationship['id']}".encode("utf-8"))[:16]
                )
                continue
            if target not in visited:
                visited.add(target)
                queue.append(target)
    return visited, errors


def _column_number(label: str) -> int:
    value = 0
    for character in label.upper():
        value = value * 26 + ord(character) - ord("A") + 1
    return value


def _column_label(number: int) -> str:
    value = number
    characters: list[str] = []
    while value:
        value, remainder = divmod(value - 1, 26)
        characters.append(chr(ord("A") + remainder))
    return "".join(reversed(characters))


def _parse_a1_cell(value: str) -> tuple[int, int, str] | None:
    match = _A1_CELL_RE.fullmatch(value.strip())
    if match is None:
        return None
    column = _column_number(match.group(1))
    row = int(match.group(2))
    if not 1 <= column <= 16384 or not 1 <= row <= 1048576:
        return None
    return column, row, f"{_column_label(column)}{row}"


def _workbook_sheet_records(
    workbook: zipfile.ZipFile,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Resolve workbook sheet names to worksheet parts in workbook order."""

    errors: list[str] = []
    names = set(workbook.namelist())
    required = {"xl/workbook.xml", "xl/_rels/workbook.xml.rels"}
    if not required.issubset(names):
        return [], ["workbook-sheet-map-missing"]
    try:
        workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
        rels_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    except ET.ParseError:
        return [], ["workbook-sheet-map-invalid"]
    relationships = {
        node.attrib.get("Id", ""): node
        for node in rels_root.findall(f"{{{_RELATIONSHIP_NS}}}Relationship")
        if node.attrib.get("Id")
    }
    records: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    seen_parts: set[str] = set()
    for ordinal, sheet in enumerate(
        workbook_root.findall(f".//{{{_SPREADSHEET_NS}}}sheet")
    ):
        sheet_name = sheet.attrib.get("name", "")
        relationship_id = sheet.attrib.get(f"{{{_OFFICE_REL_NS}}}id", "")
        relationship = relationships.get(relationship_id)
        if not sheet_name or relationship is None:
            errors.append("workbook-sheet-map-incomplete")
            continue
        if sheet_name.casefold() in seen_names:
            errors.append("workbook-sheet-name-duplicate")
            continue
        seen_names.add(sheet_name.casefold())
        target_mode = relationship.attrib.get("TargetMode", "Internal").lower()
        relationship_type = relationship.attrib.get("Type", "").lower()
        target = relationship.attrib.get("Target", "")
        if (
            target_mode == "external"
            or not relationship_type.endswith("/worksheet")
            or not target
        ):
            errors.append("workbook-sheet-relationship-unsupported")
            continue
        worksheet_part = posixpath.normpath(posixpath.join("xl", target)).lstrip("/")
        if (
            worksheet_part.startswith("../")
            or worksheet_part not in names
            or worksheet_part in seen_parts
        ):
            errors.append("workbook-sheet-target-invalid")
            continue
        seen_parts.add(worksheet_part)
        records.append(
            {
                "worksheet_name": sheet_name,
                "worksheet_ordinal": ordinal,
                "worksheet_part": worksheet_part,
            }
        )
    package_worksheets = {
        name
        for name in names
        if name.startswith("xl/worksheets/")
        and name.endswith(".xml")
        and "/_rels/" not in name
    }
    if package_worksheets != seen_parts:
        errors.append("workbook-sheet-map-incomplete")
    return records, errors


def _workbook_effective_cells(
    workbook_bytes: bytes,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Read typed non-empty XLSX cells and the exact worksheet name map."""

    cells: list[dict[str, Any]] = []
    sheet_records: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        # Compilation never trusts a workbook that production cannot sanitize.
        # Empty replacement sets still execute the complete nested-OPC audit.
        mutate_governed_xlsx(workbook_bytes, ())
    except WorkbookSecurityError as exc:
        error_code = str(exc).split(":", 1)[0].strip().lower().replace("_", "-")
        return [], [], [f"workbook-security-{error_code}"]
    try:
        with zipfile.ZipFile(io.BytesIO(workbook_bytes), "r") as workbook:
            names = set(workbook.namelist())
            sheet_records, sheet_errors = _workbook_sheet_records(workbook)
            errors.extend(sheet_errors)
            shared_strings: list[str] = []
            if "xl/sharedStrings.xml" in names:
                try:
                    shared_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
                except ET.ParseError:
                    errors.append("workbook-shared-strings-invalid")
                    shared_root = None
                if shared_root is not None:
                    for item in shared_root.findall(
                        f"{{{_SPREADSHEET_NS}}}si"
                    ):
                        shared_strings.append(
                            "".join(
                                node.text or ""
                                for node in item.iter()
                                if _local_name(node.tag) == "t"
                            ).strip()
                        )
            for sheet_record in sheet_records:
                worksheet_part = str(sheet_record["worksheet_part"])
                try:
                    sheet_root = ET.fromstring(workbook.read(worksheet_part))
                except (KeyError, ET.ParseError):
                    errors.append("workbook-sheet-invalid")
                    continue
                seen_cell_refs: set[str] = set()
                for node in sheet_root.iter(f"{{{_SPREADSHEET_NS}}}c"):
                    parsed_ref = _parse_a1_cell(node.attrib.get("r", ""))
                    if parsed_ref is None:
                        errors.append("workbook-cell-reference-invalid")
                        continue
                    cell_ref = parsed_ref[2]
                    if cell_ref in seen_cell_refs:
                        errors.append("workbook-cell-reference-duplicate")
                        continue
                    seen_cell_refs.add(cell_ref)
                    formula = node.find(f"{{{_SPREADSHEET_NS}}}f")
                    if formula is not None:
                        errors.append("workbook-formula-unsupported")
                    value_node = node.find(f"{{{_SPREADSHEET_NS}}}v")
                    cell_type = node.attrib.get("t", "")
                    value = ""
                    value_type = "number"
                    if cell_type == "inlineStr":
                        value = "".join(
                            child.text or ""
                            for child in node.iter()
                            if _local_name(child.tag) == "t"
                        )
                        value_type = "string"
                    elif value_node is not None and value_node.text is not None:
                        raw = value_node.text.strip()
                        if cell_type == "s":
                            if not raw.isdigit() or int(raw) >= len(shared_strings):
                                errors.append("workbook-shared-string-index-invalid")
                                continue
                            value = shared_strings[int(raw)]
                            value_type = "string"
                        elif cell_type == "str":
                            value = raw
                            value_type = "string"
                        elif cell_type == "b":
                            value = raw
                            value_type = "boolean"
                        elif cell_type == "d":
                            value = raw
                            value_type = "date"
                        elif cell_type == "e":
                            errors.append("workbook-error-cell-unsupported")
                            continue
                        else:
                            value = raw
                    value = value.strip()
                    if value:
                        cells.append(
                            {
                                **sheet_record,
                                "cell_ref": cell_ref,
                                "source_text": value,
                                "value_type": value_type,
                            }
                        )
    except (OSError, zipfile.BadZipFile):
        errors.append("workbook-package-invalid")
    return cells, sheet_records, errors


def _expand_chart_formula(
    formula: str,
    sheet_records: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any] | None, list[str], str | None]:
    """Resolve one supported one-dimensional chart range to exact A1 cells."""

    match = _CHART_FORMULA_RE.fullmatch(formula.strip())
    if match is None:
        return None, [], "chart-reference-unsupported"
    sheet_name = match.group("sheet")
    if sheet_name.startswith("'") and sheet_name.endswith("'"):
        sheet_name = sheet_name[1:-1].replace("''", "'")
    if "[" in sheet_name or "]" in sheet_name:
        return None, [], "chart-reference-external"
    candidates = [
        record for record in sheet_records if record.get("worksheet_name") == sheet_name
    ]
    if len(candidates) != 1:
        return None, [], "chart-reference-sheet-missing"
    start = _parse_a1_cell(match.group("start"))
    end = _parse_a1_cell(match.group("end") or match.group("start"))
    if start is None or end is None:
        return None, [], "chart-reference-cell-invalid"
    start_column, start_row, _ = start
    end_column, end_row, _ = end
    if start_column != end_column and start_row != end_row:
        return None, [], "chart-reference-two-dimensional-unsupported"
    if start_column > end_column or start_row > end_row:
        return None, [], "chart-reference-reversed-unsupported"
    if start_column == end_column:
        cell_refs = [
            f"{_column_label(start_column)}{row}"
            for row in range(start_row, end_row + 1)
        ]
    else:
        cell_refs = [
            f"{_column_label(column)}{start_row}"
            for column in range(start_column, end_column + 1)
        ]
    return dict(candidates[0]), cell_refs, None


def _governed_values_match(left: str, right: str, value_type: str) -> bool:
    if value_type == "number":
        try:
            left_number = Decimal(left)
            right_number = Decimal(right)
        except InvalidOperation:
            return False
        return left_number.is_finite() and right_number.is_finite() and left_number == right_number
    return _normalise_governed_value(left) == _normalise_governed_value(right)


def _compile_chart_governed_slots(
    archive: zipfile.ZipFile,
    *,
    shape_id: int,
    chart_part: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str], list[str]]:
    """Compile chart and workbook slots through exact formula coordinates."""

    errors: list[str] = []
    workbook_parts: set[str] = set()
    try:
        chart_root = ET.fromstring(archive.read(chart_part))
    except (KeyError, ET.ParseError):
        return [], [], workbook_parts, ["chart-xml-invalid"]
    locator_by_node = {
        id(node): locator for node, locator in _iter_xml_locators(chart_root)
    }
    parent_by_node = {
        id(child): parent for parent in chart_root.iter() for child in list(parent)
    }

    chart_slots: list[dict[str, Any]] = []
    for node in chart_root.iter(f"{{{_DML_NS}}}t"):
        source_text = (node.text or "").strip()
        if not source_text:
            continue
        locator = locator_by_node[id(node)]
        chart_slots.append(
            _content_slot(
                kind="chart-text",
                source_part=chart_part,
                locator=f"graphicFrame[id={shape_id}]{locator}",
                source_text=source_text,
                semantic_role=(
                    "chart-title" if "/title[" in locator else "chart-text"
                ),
                value_type="text",
            )
        )

    try:
        chart_relationships = _read_relationships(archive, chart_part)
    except PageTemplateError:
        chart_relationships = ()
        errors.append("chart-relationship-xml-invalid")
    workbook_relationships = []
    for relationship in chart_relationships:
        target_lower = relationship["target"].lower()
        relationship_type = relationship["type"].lower()
        if relationship_type.endswith("/package") or target_lower.endswith(
            (".xlsx", ".xlsm")
        ):
            workbook_relationships.append(relationship)
    if len(workbook_relationships) > 1:
        errors.append("chart-workbook-relationship-ambiguous")

    workbook_cells: list[dict[str, Any]] = []
    sheet_records: list[dict[str, Any]] = []
    workbook_part = ""
    for relationship in workbook_relationships:
        if relationship["target_mode"].lower() == "external":
            errors.append("chart-workbook-external")
            continue
        candidate = _resolve_relationship_target(chart_part, relationship["target"])
        workbook_parts.add(candidate)
        if candidate not in archive.namelist():
            errors.append("chart-workbook-missing")
            continue
        if workbook_part:
            continue
        workbook_part = candidate
        (
            workbook_cells,
            sheet_records,
            workbook_errors,
        ) = _workbook_effective_cells(archive.read(candidate))
        errors.extend(workbook_errors)

    workbook_slots: list[dict[str, Any]] = []
    workbook_slot_by_cell: dict[tuple[str, str], dict[str, Any]] = {}
    workbook_cell_by_cell: dict[tuple[str, str], dict[str, Any]] = {}
    for cell in workbook_cells:
        key = (str(cell["worksheet_part"]), str(cell["cell_ref"]))
        if key in workbook_slot_by_cell:
            errors.append("workbook-cell-coordinate-duplicate")
            continue
        slot = _content_slot(
            kind="workbook-cell",
            source_part=workbook_part,
            locator=(
                f"chartFrame[id={shape_id}]/{cell['worksheet_part']}!"
                f"{cell['cell_ref']}"
            ),
            source_text=str(cell["source_text"]),
            semantic_role="workbook-unreferenced",
            worksheet_ordinal=int(cell["worksheet_ordinal"]),
            cell_ref=str(cell["cell_ref"]),
            value_type=str(cell["value_type"]),
        )
        workbook_slots.append(slot)
        workbook_slot_by_cell[key] = slot
        workbook_cell_by_cell[key] = cell

    processed_value_nodes: set[int] = set()
    series_nodes = list(chart_root.iter(f"{{{_CHART_NS}}}ser"))
    role_specs = (
        ("tx", "series-name"),
        ("cat", "category"),
        ("xVal", "category"),
        ("val", "value"),
        ("yVal", "value"),
        ("bubbleSize", "value"),
    )
    reference_count = 0
    for series_index, series in enumerate(series_nodes):
        for container_name, semantic_role in role_specs:
            container = series.find(f"{{{_CHART_NS}}}{container_name}")
            if container is None:
                continue
            references = [
                node
                for node in container.iter()
                if node.tag
                in {
                    f"{{{_CHART_NS}}}strRef",
                    f"{{{_CHART_NS}}}numRef",
                }
            ]
            if not references:
                continue
            if len(references) != 1:
                errors.append("chart-reference-ambiguous")
                continue
            reference_count += 1
            reference = references[0]
            value_type = (
                "string"
                if reference.tag == f"{{{_CHART_NS}}}strRef"
                else "number"
            )
            formula_nodes = reference.findall(f"{{{_CHART_NS}}}f")
            cache_name = "strCache" if value_type == "string" else "numCache"
            cache_nodes = reference.findall(f"{{{_CHART_NS}}}{cache_name}")
            if (
                len(formula_nodes) != 1
                or not (formula_nodes[0].text or "").strip()
                or len(cache_nodes) != 1
            ):
                errors.append("chart-reference-unsupported")
                continue
            sheet_record, cell_refs, formula_error = _expand_chart_formula(
                formula_nodes[0].text or "",
                sheet_records,
            )
            if formula_error is not None or sheet_record is None:
                errors.append(formula_error or "chart-reference-unsupported")
                continue
            cache = cache_nodes[0]
            point_count_nodes = cache.findall(f"{{{_CHART_NS}}}ptCount")
            if len(point_count_nodes) != 1:
                errors.append("chart-reference-point-count-missing")
                continue
            raw_point_count = point_count_nodes[0].attrib.get("val", "")
            cache_points = cache.findall(f"{{{_CHART_NS}}}pt")
            # PowerPoint emits both conventions for sparse ranges: some
            # caches count the full formula range, while string caches often
            # count only materialized non-empty points.  Either is exact once
            # every non-empty workbook cell is checked below.
            valid_point_counts = {len(cell_refs), len(cache_points)}
            if (
                not raw_point_count.isdigit()
                or int(raw_point_count) not in valid_point_counts
            ):
                errors.append("chart-reference-point-count-mismatch")
            point_by_index: dict[int, ET.Element] = {}
            seen_reference_values: set[str] = set()
            for point in cache_points:
                raw_index = point.attrib.get("idx", "")
                value_nodes = point.findall(f"{{{_CHART_NS}}}v")
                if (
                    not raw_index.isdigit()
                    or len(value_nodes) != 1
                    or not (value_nodes[0].text or "").strip()
                ):
                    errors.append("chart-reference-point-invalid")
                    continue
                point_index = int(raw_index)
                if point_index in point_by_index or point_index >= len(cell_refs):
                    errors.append("chart-reference-point-index-invalid")
                    continue
                point_by_index[point_index] = point
                source_text = (value_nodes[0].text or "").strip()
                if value_type == "number":
                    try:
                        normalized_value = str(Decimal(source_text).normalize())
                    except InvalidOperation:
                        normalized_value = "__INVALID_NUMBER__"
                else:
                    normalized_value = _normalise_governed_value(source_text)
                if normalized_value in seen_reference_values:
                    errors.append("chart-cache-duplicate-value")
                seen_reference_values.add(normalized_value)

                cell_ref = cell_refs[point_index]
                worksheet_part = str(sheet_record["worksheet_part"])
                cell_key = (worksheet_part, cell_ref)
                workbook_cell = workbook_cell_by_cell.get(cell_key)
                workbook_slot = workbook_slot_by_cell.get(cell_key)
                if workbook_cell is None or workbook_slot is None:
                    errors.append("chart-reference-workbook-cell-missing")
                    continue
                if workbook_slot["peer_group_id"] is not None:
                    errors.append("chart-workbook-cell-reused")
                    continue
                if (
                    value_type == "number"
                    and workbook_cell["value_type"] != "number"
                ) or (
                    value_type == "string"
                    and workbook_cell["value_type"] != "string"
                ):
                    errors.append("chart-workbook-value-type-mismatch")
                    continue
                if not _governed_values_match(
                    source_text,
                    str(workbook_cell["source_text"]),
                    value_type,
                ):
                    errors.append("chart-workbook-value-mismatch")
                    continue
                value_node = value_nodes[0]
                locator = locator_by_node[id(value_node)]
                peer_group_id = "peer_" + _sha256_bytes(
                    (
                        f"{chart_part}\0{series_index}\0{semantic_role}\0"
                        f"{point_index}\0{workbook_part}\0{worksheet_part}\0"
                        f"{cell_ref}"
                    ).encode("utf-8")
                )[:24]
                chart_slot = _content_slot(
                    kind="chart-value",
                    source_part=chart_part,
                    locator=f"graphicFrame[id={shape_id}]{locator}",
                    source_text=source_text,
                    semantic_role=semantic_role,
                    series_index=series_index,
                    point_index=point_index,
                    worksheet_ordinal=int(sheet_record["worksheet_ordinal"]),
                    cell_ref=cell_ref,
                    value_type=value_type,
                )
                chart_slot["peer_group_id"] = peer_group_id
                workbook_slot.update(
                    {
                        "peer_group_id": peer_group_id,
                        "semantic_role": semantic_role,
                        "series_index": series_index,
                        "point_index": point_index,
                        "value_type": value_type,
                    }
                )
                chart_slots.append(chart_slot)
                processed_value_nodes.add(id(value_node))

            for point_index, cell_ref in enumerate(cell_refs):
                cell_key = (str(sheet_record["worksheet_part"]), cell_ref)
                if cell_key in workbook_cell_by_cell and point_index not in point_by_index:
                    errors.append("chart-reference-cache-point-missing")

    has_formula_references = any(
        node.tag in {f"{{{_CHART_NS}}}strRef", f"{{{_CHART_NS}}}numRef"}
        for node in chart_root.iter()
    )
    if has_formula_references and not workbook_relationships:
        errors.append("chart-workbook-missing")
    if has_formula_references and reference_count == 0:
        errors.append("chart-reference-unsupported")

    for value_node in chart_root.iter(f"{{{_CHART_NS}}}v"):
        if id(value_node) in processed_value_nodes:
            continue
        source_text = (value_node.text or "").strip()
        if not source_text:
            continue
        ancestor = parent_by_node.get(id(value_node))
        governed_reference_ancestor = False
        while ancestor is not None:
            if _local_name(ancestor.tag) in {
                "strRef",
                "numRef",
                "multiLvlStrRef",
            }:
                governed_reference_ancestor = True
                break
            ancestor = parent_by_node.get(id(ancestor))
        if governed_reference_ancestor:
            errors.append("chart-reference-cache-unmapped")
        chart_slots.append(
            _content_slot(
                kind="chart-value",
                source_part=chart_part,
                locator=(
                    f"graphicFrame[id={shape_id}]"
                    f"{locator_by_node[id(value_node)]}"
                ),
                source_text=source_text,
                semantic_role="chart-unreferenced",
                value_type="unknown",
            )
        )

    peer_members: Counter[str] = Counter(
        str(slot["peer_group_id"])
        for slot in (*chart_slots, *workbook_slots)
        if slot["peer_group_id"]
    )
    if any(count != 2 for count in peer_members.values()):
        errors.append("chart-peer-cardinality-invalid")
    return chart_slots, workbook_slots, workbook_parts, errors


def _compile_governed_content_inventory(
    archive: zipfile.ZipFile,
    slide_number: int,
) -> dict[str, Any]:
    """Inventory every non-shape-text content surface in a slide closure."""

    slide_part = f"ppt/slides/slide{slide_number}.xml"
    slots: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        slide_root = ET.fromstring(archive.read(slide_part))
    except (KeyError, ET.ParseError):
        return {
            **_unknown_governed_content_inventory(),
            "scan_errors": ["slide-xml-invalid"],
        }

    closure, closure_errors = _slide_dependency_closure(archive, slide_part)
    errors.extend(closure_errors)
    names = set(archive.namelist())
    workbook_parts: set[str] = {
        source_part
        for source_part in closure
        if source_part.lower().endswith((".xlsx", ".xlsm"))
    }
    for source_part in sorted(workbook_parts):
        if source_part.lower().endswith(".xlsm"):
            errors.append("workbook-xlsm-unsupported")
            continue
        _, _, workbook_errors = _workbook_effective_cells(archive.read(source_part))
        errors.extend(workbook_errors)

    # Native table cells are not ordinary p:sp text and therefore need their
    # own stable row/column slots.
    table_count = 0
    for frame in slide_root.findall(f".//{{{_PML_NS}}}graphicFrame"):
        non_visual = frame.find(f".//{{{_PML_NS}}}cNvPr")
        raw_shape_id = non_visual.attrib.get("id", "") if non_visual is not None else ""
        if not raw_shape_id.isdigit():
            shape_id = 0
        else:
            shape_id = int(raw_shape_id)
        for table_ordinal, table in enumerate(
            frame.findall(f".//{{{_DML_NS}}}tbl"),
            1,
        ):
            table_count += 1
            if shape_id < 1:
                errors.append("table-shape-id-missing")
            rows = [node for node in list(table) if _local_name(node.tag) == "tr"]
            for row_ordinal, row in enumerate(rows, 1):
                cells = [node for node in list(row) if _local_name(node.tag) == "tc"]
                for column_ordinal, cell in enumerate(cells, 1):
                    source_text = "".join(
                        node.text or ""
                        for node in cell.iter()
                        if _local_name(node.tag) == "t"
                    ).strip()
                    if not source_text:
                        continue
                    locator = (
                        f"graphicFrame[id={shape_id}]/table[{table_ordinal}]"
                        f"/row[{row_ordinal}]/cell[{column_ordinal}]"
                    )
                    slots.append(
                        _content_slot(
                            kind="table-cell",
                            source_part=slide_part,
                            locator=locator,
                            source_text=source_text,
                        )
                    )

    direct_relationships = _read_relationships(archive, slide_part)
    direct_by_id = {
        relationship["id"]: relationship
        for relationship in direct_relationships
        if relationship["id"]
    }
    chart_sources: list[tuple[int, str]] = []
    mapped_chart_relationship_ids: set[str] = set()
    for frame in slide_root.findall(f".//{{{_PML_NS}}}graphicFrame"):
        chart_ref = frame.find(f".//{{{_CHART_NS}}}chart")
        if chart_ref is None:
            continue
        non_visual = frame.find(f".//{{{_PML_NS}}}cNvPr")
        raw_shape_id = non_visual.attrib.get("id", "") if non_visual is not None else ""
        shape_id = int(raw_shape_id) if raw_shape_id.isdigit() else 0
        relationship_id = chart_ref.attrib.get(f"{{{_OFFICE_REL_NS}}}id", "")
        relationship = direct_by_id.get(relationship_id)
        if relationship is None or not relationship["type"].lower().endswith("/chart"):
            errors.append("chart-relationship-missing")
            continue
        if relationship["target_mode"].lower() == "external":
            errors.append("chart-relationship-external")
            continue
        chart_part = _resolve_relationship_target(
            slide_part,
            relationship["target"],
        )
        mapped_chart_relationship_ids.add(relationship_id)
        chart_sources.append((shape_id, chart_part))
    direct_chart_relationships = [
        relationship
        for relationship in direct_relationships
        if relationship["type"].lower().endswith("/chart")
    ]
    if len(mapped_chart_relationship_ids) != len(direct_chart_relationships):
        errors.append("chart-shape-mapping-incomplete")

    chart_workbook_parts_seen: set[str] = set()
    for shape_id, chart_part in sorted(set(chart_sources), key=lambda item: (item[1], item[0])):
        if shape_id < 1:
            errors.append("chart-shape-id-missing")
        if chart_part not in names:
            errors.append("chart-part-missing")
            continue
        (
            chart_slots,
            workbook_slots,
            chart_workbook_parts,
            chart_errors,
        ) = _compile_chart_governed_slots(
            archive,
            shape_id=shape_id,
            chart_part=chart_part,
        )
        if chart_workbook_parts_seen.intersection(chart_workbook_parts):
            errors.append("chart-workbook-reused")
        chart_workbook_parts_seen.update(chart_workbook_parts)
        workbook_parts.update(chart_workbook_parts)
        errors.extend(chart_errors)
        slots.extend(chart_slots)
        slots.extend(workbook_slots)

    content_part_specs = (
        ("ppt/notesSlides/", "notes-text", {"t"}),
        ("ppt/comments/", "comment-text", {"t", "text", "content"}),
        ("ppt/diagrams/", "diagram-text", {"t"}),
    )
    content_part_counts = {
        "notes-text": 0,
        "comment-text": 0,
        "diagram-text": 0,
    }
    for prefix, kind, allowed_names in content_part_specs:
        for source_part in sorted(
            part
            for part in closure
            if part.startswith(prefix) and part.endswith(".xml")
        ):
            content_part_counts[kind] += 1
            try:
                part_root = ET.fromstring(archive.read(source_part))
            except ET.ParseError:
                errors.append(f"{kind}-xml-invalid")
                continue
            for node, locator in _iter_xml_locators(part_root):
                if _local_name(node.tag) not in allowed_names:
                    continue
                # Date/slide-number fields in notes are runtime Office fields,
                # not authored template copy.  They are regenerated by the
                # consuming application and cannot be safely authority-bound
                # as customer facts.  Keeping them in the residue inventory
                # makes an otherwise valid deck fail after import.
                if "/fld[" in locator:
                    continue
                source_text = (node.text or "").strip()
                if source_text:
                    slots.append(
                        _content_slot(
                            kind=kind,
                            source_part=source_part,
                            locator=locator,
                            source_text=source_text,
                        )
                    )

    layout_master_fields: list[dict[str, Any]] = []
    for source_part in sorted(
        part
        for part in closure
        if part.startswith(("ppt/slideLayouts/", "ppt/slideMasters/"))
        and part.endswith(".xml")
    ):
        try:
            part_root = ET.fromstring(archive.read(source_part))
        except ET.ParseError:
            errors.append("layout-master-xml-invalid")
            continue
        for node, locator in _iter_xml_locators(part_root):
            if _local_name(node.tag) != "fld":
                continue
            cached_text = "".join(
                child.text or ""
                for child in node.iter()
                if _local_name(child.tag) == "t"
            ).strip()
            field_id = "field_" + _sha256_bytes(
                f"{source_part}\0{locator}".encode("utf-8")
            )[:24]
            layout_master_fields.append(
                {
                    "field_id": field_id,
                    "source_part": source_part,
                    "locator": locator,
                    "field_type": node.attrib.get("type", "unknown"),
                    "source_text_sha256": _sha256_bytes(
                        cached_text.encode("utf-8")
                    ),
                }
            )

    tag_parts = [
        {
            "source_part": source_part,
            "sha256": _sha256_bytes(archive.read(source_part)),
            "size_bytes": len(archive.read(source_part)),
        }
        for source_part in sorted(
            part for part in closure if part.startswith("ppt/tags/")
        )
    ]
    media_parts = [
        {
            "source_part": source_part,
            "sha256": _sha256_bytes(archive.read(source_part)),
            "size_bytes": len(archive.read(source_part)),
        }
        for source_part in sorted(
            part for part in closure if part.startswith("ppt/media/")
        )
    ]

    slots.sort(key=lambda item: (item["source_part"], item["locator"], item["slot_id"]))
    if workbook_parts and not any(slot["kind"] == "workbook-cell" for slot in slots):
        errors.append("workbook-present-without-governed-slots")
    scan_errors = sorted(set(errors))
    policy = (
        "locked-authority-required"
        if slots or scan_errors or workbook_parts
        else "no-embedded-content"
    )
    return {
        "schema_version": "governed-content-inventory.v1",
        "peer_mapping_method": "chart-formula-range-v1",
        "policy": policy,
        "complete": not scan_errors,
        "content_slot_count": len(slots),
        "customer_data_slot_count": len(slots),
        "slots": slots,
        "closure_metadata": {
            "table_count": table_count,
            "chart_part_count": len(set(part for _, part in chart_sources)),
            "workbook_part_count": len(workbook_parts),
            "notes_part_count": content_part_counts["notes-text"],
            "comment_part_count": content_part_counts["comment-text"],
            "diagram_part_count": content_part_counts["diagram-text"],
            "layout_master_field_count": len(layout_master_fields),
            "layout_master_fields": layout_master_fields,
            "tag_part_count": len(tag_parts),
            "tag_parts": tag_parts,
            "media_count": len(media_parts),
            "media_parts": media_parts,
        },
        "scan_errors": scan_errors,
    }


def _normalised_bbox(
    shape: ET.Element,
    *,
    slide_width: int,
    slide_height: int,
) -> dict[str, int]:
    xfrm = shape.find(f".//{{{_PML_NS}}}spPr/{{{_DML_NS}}}xfrm")
    if xfrm is None:
        return {"x": 0, "y": 0, "w": 0, "h": 0}
    offset = xfrm.find(f"{{{_DML_NS}}}off")
    extent = xfrm.find(f"{{{_DML_NS}}}ext")
    if offset is None or extent is None:
        return {"x": 0, "y": 0, "w": 0, "h": 0}
    try:
        x = int(offset.attrib.get("x", "0"))
        y = int(offset.attrib.get("y", "0"))
        width = int(extent.attrib.get("cx", "0"))
        height = int(extent.attrib.get("cy", "0"))
    except ValueError:
        return {"x": 0, "y": 0, "w": 0, "h": 0}
    return {
        "x": max(0, min(1000, round(x * 1000 / max(1, slide_width)))),
        "y": max(0, min(1000, round(y * 1000 / max(1, slide_height)))),
        "w": max(0, min(1000, round(width * 1000 / max(1, slide_width)))),
        "h": max(0, min(1000, round(height * 1000 / max(1, slide_height)))),
    }


def _slot_region(bbox: Mapping[str, int]) -> str:
    centre_x = int(bbox["x"]) + int(bbox["w"]) // 2
    centre_y = int(bbox["y"]) + int(bbox["h"]) // 2
    vertical = "top" if centre_y < 333 else "middle" if centre_y < 667 else "bottom"
    horizontal = "left" if centre_x < 333 else "center" if centre_x < 667 else "right"
    return f"{vertical}-{horizontal}"


def _slot_font_size(shape: ET.Element) -> float | None:
    sizes: list[int] = []
    for tag in ("rPr", "defRPr", "endParaRPr"):
        for node in shape.findall(f".//{{{_DML_NS}}}{tag}"):
            raw = node.attrib.get("sz")
            if raw and raw.isdigit():
                sizes.append(int(raw))
    return round(max(sizes) / 100.0, 2) if sizes else None


def _semantic_role(
    *,
    text: str,
    name: str,
    placeholder_type: str,
    bbox: Mapping[str, int],
    font_size_pt: float | None,
) -> str:
    lowered = name.lower()
    if placeholder_type in {"title", "ctrTitle"} or "title" in lowered or "标题" in name:
        return "title"
    if placeholder_type == "subTitle" or "subtitle" in lowered or "副标题" in name:
        return "subtitle"
    if placeholder_type in {"dt", "ftr", "sldNum"}:
        return "footer"
    if re.fullmatch(r"[\d０-９.,%％+\-—]+", text.strip()) and (font_size_pt or 0) >= 20:
        return "metric"
    if int(bbox["y"]) >= 850 and (font_size_pt or 0) <= 16:
        return "footer"
    if (font_size_pt or 0) >= 28 and int(bbox["y"]) < 550:
        return "title"
    if len(_without_slot_whitespace(text)) <= 16 and (font_size_pt or 0) >= 18:
        return "label"
    return "body"


def _without_slot_whitespace(value: str) -> str:
    return "".join(value.split())


def _slot_capacity(
    *,
    text: str,
    semantic_role: str,
    bbox: Mapping[str, int],
    font_size_pt: float | None,
) -> int:
    source_chars = max(1, len(_without_slot_whitespace(text)))
    if semantic_role == "metric":
        return max(source_chars, 16)
    font = font_size_pt or 18.0
    width_points = int(bbox["w"]) * (_DEFAULT_SLIDE_WIDTH / 1000) / _EMU_PER_POINT
    height_points = int(bbox["h"]) * (_DEFAULT_SLIDE_HEIGHT / 1000) / _EMU_PER_POINT
    if width_points <= 0 or height_points <= 0:
        fallback = 40 if semantic_role == "title" else 80
        return max(source_chars, fallback)
    chars_per_line = max(1, int(width_points / max(6.0, font * 0.9)))
    line_count = max(1, int(height_points / max(8.0, font * 1.2)))
    computed = chars_per_line * line_count
    role_cap = {"title": 48, "subtitle": 72, "label": 32, "footer": 48}.get(
        semantic_role,
        320,
    )
    return max(source_chars, min(role_cap, computed))


def _discover_slots(
    slide_xml: str,
    *,
    slide_width: int = _DEFAULT_SLIDE_WIDTH,
    slide_height: int = _DEFAULT_SLIDE_HEIGHT,
) -> tuple[SlotRecord, ...]:
    """Extract safe, spatially meaningful text-slot metadata from one slide."""

    try:
        root = ET.fromstring(slide_xml)
    except ET.ParseError as exc:
        raise PageTemplateError(f"invalid slide XML: {exc}") from exc
    discovered: list[dict[str, Any]] = []

    def visit(container: ET.Element, group_path: tuple[int, ...]) -> None:
        for child in list(container):
            local = child.tag.rsplit("}", 1)[-1]
            if local == "grpSp":
                group_node = child.find(f".//{{{_PML_NS}}}cNvPr")
                group_id = int(group_node.attrib.get("id", "0")) if group_node is not None else 0
                visit(child, (*group_path, group_id))
                continue
            if local != "sp":
                continue
            non_visual = child.find(f".//{{{_PML_NS}}}cNvPr")
            text_body = child.find(f"{{{_PML_NS}}}txBody")
            if non_visual is None or text_body is None:
                continue
            raw_shape_id = non_visual.attrib.get("id")
            if not raw_shape_id or not raw_shape_id.isdigit():
                continue
            runs = [node.text or "" for node in text_body.findall(f".//{{{_DML_NS}}}t")]
            joined = "\n".join(runs).strip()
            if not joined:
                continue
            placeholder = child.find(f".//{{{_PML_NS}}}ph")
            placeholder_type = placeholder.attrib.get("type", "") if placeholder is not None else ""
            bbox = _normalised_bbox(
                child,
                slide_width=slide_width,
                slide_height=slide_height,
            )
            font_size = _slot_font_size(child)
            semantic = _semantic_role(
                text=joined,
                name=non_visual.attrib.get("name", ""),
                placeholder_type=placeholder_type,
                bbox=bbox,
                font_size_pt=font_size,
            )
            discovered.append(
                {
                    "slot_id": f"shape_{int(raw_shape_id)}",
                    "shape_id": int(raw_shape_id),
                    "text": joined,
                    "semantic_role": semantic,
                    "bbox": bbox,
                    "region": _slot_region(bbox),
                    "source_char_count": len(_without_slot_whitespace(joined)),
                    "source_line_count": max(1, len(joined.splitlines())),
                    "source_run_count": len(runs),
                    "group_id": "group_" + "_".join(map(str, group_path)) if group_path else None,
                    "group_order": None,
                    "font_size_pt": font_size,
                }
            )

    shape_tree = root.find(f".//{{{_PML_NS}}}spTree")
    if shape_tree is not None:
        visit(shape_tree, ())
    discovered.sort(
        key=lambda item: (
            item["bbox"]["y"],
            item["bbox"]["x"],
            item["shape_id"],
        )
    )

    # Group adjacent single-character shapes into one safe semantic fragment
    # sequence. The commercial source copy remains private, while the Agent can
    # bind each character in the right order without guessing from shape IDs.
    fragments = [
        item
        for item in discovered
        if item["source_char_count"] == 1 and (item["font_size_pt"] or 0) >= 18
    ]
    fragment_groups: list[list[dict[str, Any]]] = []
    for item in fragments:
        assigned = False
        item_cx = item["bbox"]["x"] + item["bbox"]["w"] // 2
        item_cy = item["bbox"]["y"] + item["bbox"]["h"] // 2
        for group in fragment_groups:
            anchor = group[0]
            anchor_cx = anchor["bbox"]["x"] + anchor["bbox"]["w"] // 2
            anchor_cy = anchor["bbox"]["y"] + anchor["bbox"]["h"] // 2
            if abs(item_cy - anchor_cy) <= 35 or abs(item_cx - anchor_cx) <= 35:
                group.append(item)
                assigned = True
                break
        if not assigned:
            fragment_groups.append([item])
    for group_number, group in enumerate(
        (group for group in fragment_groups if len(group) >= 2),
        1,
    ):
        horizontal = (
            max(item["bbox"]["x"] for item in group)
            - min(item["bbox"]["x"] for item in group)
            >= max(item["bbox"]["y"] for item in group)
            - min(item["bbox"]["y"] for item in group)
        )
        group.sort(
            key=lambda item: (
                item["bbox"]["x"] if horizontal else item["bbox"]["y"],
                item["shape_id"],
            )
        )
        fragment_id = f"fragment_{group_number:02d}"
        for position, item in enumerate(group, 1):
            item["group_id"] = fragment_id
            item["group_order"] = position
            item["semantic_role"] = (
                "title_fragment" if item["bbox"]["y"] < 650 else "label_fragment"
            )

    slots: list[SlotRecord] = []
    for reading_order, item in enumerate(discovered, 1):
        semantic = item["semantic_role"]
        fragment = semantic in {"title_fragment", "label_fragment"}
        max_chars = 1 if fragment else _slot_capacity(
            text=item["text"],
            semantic_role=semantic,
            bbox=item["bbox"],
            font_size_pt=item["font_size_pt"],
        )
        slots.append(
            SlotRecord(
                slot_id=item["slot_id"],
                shape_id=item["shape_id"],
                kind=semantic,
                max_chars=max_chars,
                text=item["text"],
                semantic_role=semantic,
                region=item["region"],
                reading_order=reading_order,
                bbox=item["bbox"],
                source_char_count=item["source_char_count"],
                source_line_count=item["source_line_count"],
                source_run_count=item["source_run_count"],
                group_id=item["group_id"],
                group_order=item["group_order"],
                font_size_pt=item["font_size_pt"],
                allowed_binding_modes=(
                    ("character", "clear") if fragment else ("fact", "connective", "clear")
                ),
            )
        )
    return tuple(slots)


_HEX6 = re.compile(r"^[0-9A-Fa-f]{6}$")


def _scan_palette(slide_xml: str, max_colors: int = 6) -> tuple[str, ...]:
    counts = Counter(_SRGB_RE.findall(slide_xml))
    if not counts:
        return ("#F5F0E5", "#173D32", "#B79A5B")
    top = [f"#{value.upper()}" for value, _ in counts.most_common(max_colors)]
    return tuple(top)


def _scan_structure(package_path: Path) -> dict[str, Any]:
    """Return the structure summary for one source package."""

    summary: dict[str, Any] = {
        "slide_count": 0,
        "shape_count": 0,
        "layout_count": 0,
        "master_count": 0,
        "theme_count": 0,
        "media_count": 0,
        "chart_count": 0,
        "table_count": 0,
        "fonts": [],
    }
    try:
        with zipfile.ZipFile(package_path, "r") as archive:
            for name in archive.namelist():
                if _SLIDE_RE.match(name):
                    summary["slide_count"] += 1
                    summary["shape_count"] += len(
                        _CNVPR_RE.findall(archive.read(name).decode("utf-8", errors="replace"))
                    )
                elif _LAYOUT_RE.match(name):
                    summary["layout_count"] += 1
                elif _MASTER_RE.match(name):
                    summary["master_count"] += 1
                elif _THEME_RE.match(name):
                    summary["theme_count"] += 1
                elif name.startswith("ppt/media/") or name.startswith("ppt/embeddings/"):
                    summary["media_count"] += 1
                elif name.startswith("ppt/charts/"):
                    summary["chart_count"] += 1
                elif "table" in name.lower():
                    summary["table_count"] += 1
            # Probe theme for fonts
            theme_names = [
                n for n in archive.namelist() if _THEME_RE.match(n)
            ]
            if theme_names:
                theme_xml = archive.read(theme_names[0]).decode("utf-8", errors="replace")
                fonts = re.findall(r'typeface="([^"]+)"', theme_xml)
                summary["fonts"] = sorted(set(fonts))[:24]
    except (OSError, zipfile.BadZipFile) as exc:
        raise PageTemplateError(
            f"unreadable source package {package_path}: {exc}"
        ) from exc
    return summary


_RESEARCH_CATEGORIES = {
    "时间轴图",
    "架构流程",
    "商业模型",
    "表格图表",
    "地图排版",
    "数据基座",
}
_STAGE_CATEGORIES = {
    "人物介绍",
    "样机展示",
    "合作伙伴",
    "优秀作品",
}
_RESEARCH_ROLES = {
    "data",
    "data-chart",
    "table",
    "timeline",
    "process",
    "roadmap",
    "matrix",
    "map",
    "business-model",
    "kpi",
}
_STAGE_ROLES = {"mockup", "people", "team", "logo-wall", "case-study"}


def _accent_family(red: int, green: int, blue: int) -> str:
    maximum = max(red, green, blue)
    minimum = min(red, green, blue)
    if maximum - minimum < 20:
        return "neutral"
    hue, _saturation, _value = colorsys.rgb_to_hsv(
        red / 255.0,
        green / 255.0,
        blue / 255.0,
    )
    degrees = round(hue * 360) % 360
    if degrees < 20 or degrees >= 345:
        return "red"
    if degrees < 50:
        return "orange"
    if degrees < 75:
        return "yellow"
    if degrees < 165:
        return "green"
    if degrees < 200:
        return "cyan"
    if degrees < 255:
        return "blue"
    if degrees < 305:
        return "purple"
    return "magenta"


def _style_features_for(
    palette: Sequence[str],
    *,
    role: str,
    categories: Sequence[str],
    slide_xml: str,
    slot_count: int,
) -> dict[str, Any]:
    """Derive stable, inspectable style evidence for one physical page."""

    colors: list[tuple[int, int, int]] = []
    for value in palette:
        raw = value.lstrip("#")
        if _HEX6.fullmatch(raw):
            colors.append(
                tuple(
                    int(raw[offset : offset + 2], 16)
                    for offset in (0, 2, 4)
                )
            )
    if not colors:
        colors = [(245, 240, 229), (23, 61, 50), (183, 154, 91)]
    luminances = [
        (299 * red + 587 * green + 114 * blue) // 1000
        for red, green, blue in colors
    ]
    average_luminance = sum(luminances) // len(luminances)
    average_chroma = sum(max(color) - min(color) for color in colors) // len(colors)
    accent = max(colors, key=lambda color: (max(color) - min(color), color))
    tone = (
        "dark"
        if average_luminance < 92
        else "light"
        if average_luminance > 188
        else "mid"
    )
    category_set = set(categories)
    if role in _RESEARCH_ROLES or category_set.intersection(_RESEARCH_CATEGORIES):
        visual_mode = "research-evidence"
    elif role in _STAGE_ROLES or category_set.intersection(_STAGE_CATEGORIES):
        visual_mode = "visual-stage"
    else:
        visual_mode = "editorial"
    shape_count = len(_CNVPR_RE.findall(slide_xml))
    density_score = min(100, shape_count * 4 + slot_count * 8)
    density = (
        "sparse"
        if density_score < 28
        else "dense"
        if density_score > 68
        else "balanced"
    )
    return {
        "tone": tone,
        "average_luminance": average_luminance,
        "average_chroma": average_chroma,
        "accent_family": _accent_family(*accent),
        "visual_mode": visual_mode,
        "density": density,
        "density_score": density_score,
    }


def _style_cluster_for(
    role: str,
    categories: Sequence[str],
    style_features: Mapping[str, Any],
) -> str:
    """Map semantic and visual evidence to one bounded style cluster."""

    visual_mode = style_features.get("visual_mode")
    if visual_mode == "research-evidence":
        return "research-editorial-evidence"
    if visual_mode == "visual-stage":
        return "optimistic-technical-stage"
    # Generic categories are routed by bounded visual evidence rather than
    # receiving one universal label.  Dark, chromatic pages behave like a
    # stage system; dense cool-accent pages behave like research/evidence.
    if (
        style_features.get("tone") == "dark"
        and int(style_features.get("average_chroma", 0)) >= 55
    ):
        return "optimistic-technical-stage"
    if (
        style_features.get("accent_family") in {"blue", "cyan"}
        and style_features.get("density") == "dense"
    ):
        return "research-editorial-evidence"
    return DEFAULT_DOMINANT_STYLE_CLUSTER


def _deck_family_for(category: str) -> str:
    """Pick a stable deck family for a category."""

    table = {
        "封面模板": "institutional-annual-editorial",
        "目录模板": "institutional-annual-editorial",
        "章节模板": "institutional-annual-editorial",
        "标题模板": "institutional-annual-editorial",
        "结尾模板": "institutional-annual-editorial",
        "人物介绍": "campus-innovation-pitch",
        "荣誉奖项": "institutional-annual-editorial",
        "时间轴图": "data-research-editorial",
        "架构流程": "data-research-editorial",
        "商业模型": "data-research-editorial",
        "样机展示": "product-launch-stage",
        "金句模板": "institutional-annual-editorial",
        "合作伙伴": "campus-innovation-pitch",
        "图文排版": "institutional-annual-editorial",
        "表格图表": "data-research-editorial",
        "优秀作品": "product-launch-stage",
        "实用素材": "institutional-annual-editorial",
        "一段内容": "institutional-annual-editorial",
        "二段内容": "institutional-annual-editorial",
        "三段内容": "institutional-annual-editorial",
        "四段内容": "institutional-annual-editorial",
        "五段内容": "institutional-annual-editorial",
        "六段内容": "institutional-annual-editorial",
        "多段内容": "institutional-annual-editorial",
        "地图排版": "data-research-editorial",
        "数据基座": "data-research-editorial",
        "文本组件": "institutional-annual-editorial",
        "装饰形状": "institutional-annual-editorial",
        "风格配色": "institutional-annual-editorial",
    }
    return table.get(category, "institutional-annual-editorial")


def _capacity_for_slots(slots: Sequence[SlotRecord]) -> dict[str, int]:
    total_chars = sum(slot.max_chars for slot in slots)
    return {
        "max_text_chars": max(0, total_chars),
        "max_text_runs": max(1, len(slots)),
    }


def _slot_graph_for(slots: Sequence[SlotRecord]) -> dict[str, Any]:
    fragment_groups: dict[str, list[str]] = {}
    for slot in slots:
        if slot.group_id and slot.group_id.startswith("fragment_"):
            fragment_groups.setdefault(slot.group_id, []).append(slot.slot_id)
    return {
        "text_slot_ids": [slot.slot_id for slot in slots],
        "text_slot_count": len(slots),
        "reading_order": [slot.slot_id for slot in slots],
        "fragment_groups": [
            {"group_id": group_id, "slot_ids": slot_ids}
            for group_id, slot_ids in sorted(fragment_groups.items())
        ],
        "slots": [
            {
                "slot_id": slot.slot_id,
                "shape_id": slot.shape_id,
                "kind": slot.kind,
                "semantic_role": slot.semantic_role,
                "region": slot.region,
                "reading_order": slot.reading_order,
                "bbox": dict(slot.bbox),
                "max_chars": slot.max_chars,
                "source_char_count": slot.source_char_count,
                "source_line_count": slot.source_line_count,
                "source_run_count": slot.source_run_count,
                "source_text_sha256": _sha256_bytes(slot.text.encode("utf-8")),
                "source_text": slot.text,
                "group_id": slot.group_id,
                "group_order": slot.group_order,
                "font_size_pt": slot.font_size_pt,
                "allowed_binding_modes": list(slot.allowed_binding_modes),
            }
            for slot in slots
        ],
    }


def compile_page_templates(
    private_root: str | os.PathLike[str],
    *,
    library_id: str = "window-pptx-gaojie-certified-core-v4",
) -> LibraryIndex:
    """Compile the v6.1 page-template index from the certified core."""

    root = Path(private_root).expanduser().resolve(strict=False)
    asset_index_path = root / "intelligence" / "gaojie" / "asset-index.json"
    core_path = root / "intelligence" / "gaojie" / "certified-core.json"
    if not asset_index_path.is_file():
        raise PageTemplateError(f"asset-index missing: {asset_index_path}")
    if not core_path.is_file():
        raise PageTemplateError(f"certified-core missing: {core_path}")
    asset_index = json.loads(asset_index_path.read_text(encoding="utf-8"))
    certified_core = json.loads(core_path.read_text(encoding="utf-8"))
    if certified_core.get("schema_version") != CERTIFIED_CORE_SCHEMA:
        raise PageTemplateError(
            f"unexpected certified-core schema: {certified_core.get('schema_version')}"
        )
    package_lookup: dict[str, dict[str, Any]] = {}
    for package in asset_index.get("packages", []):
        if package.get("status") == "ACCEPTED" and package.get("render_status") == "PASS":
            package_lookup[str(package["package_sha256"])] = package
    templates: list[PageTemplate] = []
    compile_failures: list[str] = []
    structure_cache: dict[Path, dict[str, Any]] = {}
    source_sha_cache: dict[Path, str] = {}
    for page in certified_core.get("pages", []):
        if page.get("certification") not in ("certified", "certified-private"):
            continue
        package_sha = str(page["package_sha256"])
        package = package_lookup.get(package_sha)
        if package is None:
            compile_failures.append(f"{page.get('page_id')}:package-not-accepted")
            continue
        relative = package.get("private_path")
        if not relative:
            compile_failures.append(f"{page.get('page_id')}:private-path-missing")
            continue
        source_path = (root / relative).resolve(strict=False)
        if not source_path.is_relative_to(root):
            raise PageTemplateError(
                f"private package path escapes root: {relative}"
            )
        if not source_path.is_file():
            compile_failures.append(f"{page.get('page_id')}:source-missing")
            continue
        slide_number = int(page["slide_number"])
        try:
            with zipfile.ZipFile(source_path, "r") as archive:
                (
                    slide_xml,
                    linked_style_xml,
                    slide_relationship_count,
                    linked_style_part_count,
                    page_assets,
                ) = _read_slide_material(
                    archive,
                    slide_number,
                )
                governed_content_inventory = _compile_governed_content_inventory(
                    archive,
                    slide_number,
                )
        except (OSError, zipfile.BadZipFile, KeyError, PageTemplateError) as exc:
            compile_failures.append(f"{page.get('page_id')}:slide-unreadable:{type(exc).__name__}")
            continue
        slots = _discover_slots(slide_xml)
        palette = _scan_palette(f"{slide_xml}\n{linked_style_xml}")
        structure = structure_cache.get(source_path)
        if structure is None:
            structure = _scan_structure(source_path)
            structure_cache[source_path] = structure
        categories = tuple(page.get("category_names") or [])
        primary_category = categories[0] if categories else "未分类"
        capacity = _capacity_for_slots(slots)
        page_role = str(page.get("page_role", "body"))
        style_features = _style_features_for(
            palette,
            role=page_role,
            categories=categories,
            slide_xml=slide_xml,
            slot_count=len(slots),
        )
        style_cluster = _style_cluster_for(page_role, categories, style_features)
        deck_family = _deck_family_for(primary_category)
        try:
            source_sha = source_sha_cache.get(source_path)
            if source_sha is None:
                source_sha = _sha256_file(source_path)
                source_sha_cache[source_path] = source_sha
        except OSError:
            compile_failures.append(f"{page.get('page_id')}:source-hash-failed")
            continue
        if source_sha != package_sha:
            compile_failures.append(f"{page.get('page_id')}:package-hash-mismatch")
            continue
        pool_value = page.get("pool")
        pool = str(pool_value) if pool_value is not None else None
        decision_value = page.get("decision")
        decision = str(decision_value) if decision_value is not None else None
        explicitly_direct = page.get("direct_use")
        direct_use = (
            bool(explicitly_direct)
            if explicitly_direct is not None
            else not (
                _is_reference_only_pool(pool)
                or _is_non_direct_decision(decision)
            )
        )
        # Fail closed when the routing fields disagree.  We still preserve the
        # original values above for audit/debugging.
        if (
            _is_reference_only_pool(pool)
            or _is_non_direct_decision(decision)
        ):
            direct_use = False
        if not governed_content_inventory["complete"]:
            direct_use = False
        template = PageTemplate(
            schema_version="1.0",
            page_id=str(page["page_id"]),
            package_sha256=package_sha,
            slide_number=slide_number,
            source_path=str(source_path),
            source_sha256=source_sha,
            source_slide_sha256=_sha256_bytes(slide_xml.encode("utf-8")),
            page_role=page_role,
            category_names=categories,
            style_cluster_id=style_cluster,
            deck_family_id=deck_family,
            theme_palette=palette,
            capacity=capacity,
            editability=(
                "native_editable"
                if page_assets["page_native_object_count"] > 0
                else "image_only"
            ),
            certification="certified",
            visual_quality=float(page.get("quality", 0.0) or 0.0),
            structure={
                "slide_count": structure["slide_count"],
                "shape_count": structure["shape_count"],
                "layout_count": structure["layout_count"],
                "master_count": structure["master_count"],
                "theme_count": structure["theme_count"],
                "media_count": structure["media_count"],
                "chart_count": structure["chart_count"],
                "table_count": structure["table_count"],
                "fonts": structure["fonts"],
                "page_shape_count": len(_CNVPR_RE.findall(slide_xml)),
                "slide_relationship_count": slide_relationship_count,
                "linked_style_part_count": linked_style_part_count,
                **page_assets,
            },
            slot_graph=_slot_graph_for(slots),
            requires_customer_asset=bool(
                page.get(
                    "requires_customer_asset",
                    page_assets["page_media_count"] > 0,
                )
            ),
            media_retention_policy=(
                str(page.get("media_retention_policy"))
                if page.get("media_retention_policy")
                else (
                    "customer-replacement-required"
                    if page_assets["page_media_count"] > 0
                    else "no-page-media"
                )
            ),
            pool=pool,
            decision=decision,
            direct_use=direct_use,
            eligibility_known=True,
            style_features=style_features,
            governed_content_inventory=governed_content_inventory,
        )
        templates.append(template)
    if compile_failures:
        preview = ";".join(compile_failures[:12])
        raise PageTemplateError(
            f"certified core compilation incomplete ({len(compile_failures)} failures): {preview}"
        )
    templates.sort(key=lambda t: (t.page_role, t.package_sha256, t.slide_number))
    role_index: Counter[str] = Counter(t.page_role for t in templates)
    style_index: Counter[str] = Counter(t.style_cluster_id for t in templates)
    family_index: Counter[str] = Counter(t.deck_family_id for t in templates)
    cat_index: Counter[str] = Counter(c for t in templates for c in t.category_names)
    eligible_style_index: Counter[str] = Counter(
        template.style_cluster_id for template in templates if template.direct_use
    )
    dominant_source = eligible_style_index or style_index
    dominant_style = DEFAULT_DOMINANT_STYLE_CLUSTER
    if dominant_source:
        priority = {
            cluster_id: ordinal
            for ordinal, cluster_id in enumerate(DEFAULT_COMPATIBLE_STYLE_CLUSTERS)
        }
        dominant_style = min(
            dominant_source,
            key=lambda cluster_id: (
                -dominant_source[cluster_id],
                priority.get(cluster_id, len(priority)),
                cluster_id,
            ),
        )
    # Merely observing two styles in one catalog is not compatibility
    # evidence.  Cross-cluster fallback can be enabled only by an explicit
    # registry edit after visual certification.
    compatible_styles = (dominant_style,)
    source_package_index: dict[str, dict[str, Any]] = {}
    for template in templates:
        record = source_package_index.setdefault(
            template.package_sha256,
            {
                "page_count": 0,
                "source_sha256": template.source_sha256,
                "source_size_bytes": Path(template.source_path).stat().st_size,
            },
        )
        record["page_count"] += 1
    index = LibraryIndex(
        schema_version="4.0",
        library_id=library_id,
        # The library is a content-addressed build artifact.  Wall-clock time
        # belongs in the surrounding run evidence; embedding it here would
        # make identical inputs produce different locked library digests.
        compiled_at=DETERMINISTIC_COMPILED_AT,
        source_core_schema=CERTIFIED_CORE_SCHEMA,
        private_root_sha256=_sha256_directory(root),
        source_package_count=len(source_package_index),
        source_package_index=dict(sorted(source_package_index.items())),
        page_template_count=len(templates),
        role_index=dict(role_index),
        style_cluster_index=dict(style_index),
        deck_family_index=dict(family_index),
        category_index=dict(cat_index),
        scoring=dict(DEFAULT_SCORING),
        dominant_style_cluster_id=dominant_style,
        compatible_style_cluster_ids=compatible_styles,
        page_templates=tuple(templates),
    )
    return index


def compile_reference_deck(
    deck_path: str | os.PathLike[str],
    *,
    library_id: str = "window-pptx-reference-work-summary-v1",
) -> LibraryIndex:
    """Compile every slide of a user-certified reference deck as page templates.

    This is intentionally separate from the commercial Gaojie catalog.  The
    caller supplies the semantic role sequence; the original slide, master,
    theme, media, and editable text remain the physical source of truth.
    """

    path = Path(deck_path).expanduser().resolve(strict=False)
    if not path.is_file():
        raise PageTemplateError(f"reference deck missing: {path}")
    package_sha = _sha256_file(path)
    # The source deck contains two consecutive chapter dividers before its
    # first chart (slides 3–4), then an evidence/data run, an innovation
    # divider (10), people/content pages (11–12), and the next-year divider
    # (13).  Recording these semantics prevents an authoring Agent from
    # selecting slide 4 as a data page merely because it is adjacent to one.
    roles = (
        "cover", "contents", "section", "section", "data", "data", "table",
        "case-study", "kpi", "section", "people", "content-blocks", "section",
        "process", "closing",
    )
    categories = (
        "封面模板", "目录模板", "章节模板", "章节模板", "表格图表",
        "表格图表", "表格图表", "表格图表", "表格图表", "章节模板",
        "人物介绍", "多段内容", "章节模板", "架构流程", "结尾模板",
    )
    templates: list[PageTemplate] = []
    try:
        with zipfile.ZipFile(path, "r") as archive:
            slide_names = sorted(
                (name for name in archive.namelist() if _SLIDE_RE.match(name)),
                key=lambda name: int(_SLIDE_RE.match(name).group(1)),
            )
            if len(slide_names) < len(roles):
                raise PageTemplateError(
                    f"reference deck has {len(slide_names)} slides; expected at least {len(roles)}"
                )
            structure = _scan_structure(path)
            for ordinal, (role, category) in enumerate(zip(roles, categories, strict=True), 1):
                (
                    slide_xml,
                    linked_style_xml,
                    slide_relationship_count,
                        linked_style_part_count,
                        page_assets,
                ) = _read_slide_material(
                    archive,
                    ordinal,
                )
                governed_content_inventory = _compile_governed_content_inventory(
                    archive,
                    ordinal,
                )
                slots = _discover_slots(slide_xml)
                palette = _scan_palette(f"{slide_xml}\n{linked_style_xml}")
                style_features = _style_features_for(
                    palette,
                    role=role,
                    categories=(category,),
                    slide_xml=slide_xml,
                    slot_count=len(slots),
                )
                templates.append(
                    PageTemplate(
                        schema_version="1.0",
                        page_id=f"{package_sha}:{ordinal:03d}",
                        package_sha256=package_sha,
                        slide_number=ordinal,
                        source_path=str(path),
                        source_sha256=package_sha,
                        source_slide_sha256=_sha256_bytes(slide_xml.encode("utf-8")),
                        page_role=role,
                        category_names=(category,),
                        style_cluster_id="reference-work-summary",
                        deck_family_id="reference-work-summary",
                        theme_palette=palette,
                        capacity=_capacity_for_slots(slots),
                        editability=(
                            "native_editable"
                            if page_assets["page_native_object_count"] > 0
                            else "image_only"
                        ),
                        certification="certified",
                        visual_quality=0.98,
                        structure={
                            "slide_count": structure["slide_count"],
                            "shape_count": structure["shape_count"],
                            "layout_count": structure["layout_count"],
                            "master_count": structure["master_count"],
                            "theme_count": structure["theme_count"],
                            "media_count": structure["media_count"],
                            "chart_count": structure["chart_count"],
                            "table_count": structure["table_count"],
                            "fonts": structure["fonts"],
                            "page_shape_count": len(_CNVPR_RE.findall(slide_xml)),
                            "slide_relationship_count": slide_relationship_count,
                            "linked_style_part_count": linked_style_part_count,
                            **page_assets,
                        },
                        slot_graph=_slot_graph_for(slots),
                        requires_customer_asset=False,
                        media_retention_policy="certified-decorative-retain",
                        pool="user-certified-reference",
                        decision="direct-use",
                        direct_use=bool(governed_content_inventory["complete"]),
                        eligibility_known=True,
                        style_features=style_features,
                        governed_content_inventory=governed_content_inventory,
                    )
                )
    except (OSError, zipfile.BadZipFile, KeyError, PageTemplateError) as exc:
        raise PageTemplateError(f"unreadable reference deck {path}: {exc}") from exc
    counts = Counter(t.page_role for t in templates)
    category_index = Counter(c for t in templates for c in t.category_names)
    return LibraryIndex(
        schema_version="4.0",
        library_id=library_id,
        compiled_at=DETERMINISTIC_COMPILED_AT,
        source_core_schema="user-certified-reference-deck.v1",
        private_root_sha256=package_sha,
        source_package_count=1,
        source_package_index={
            package_sha: {
                "page_count": len(templates),
                "source_sha256": package_sha,
                "source_size_bytes": path.stat().st_size,
            }
        },
        page_template_count=len(templates),
        role_index=dict(counts),
        style_cluster_index={"reference-work-summary": len(templates)},
        deck_family_index={"reference-work-summary": len(templates)},
        category_index=dict(category_index),
        scoring=dict(DEFAULT_SCORING),
        dominant_style_cluster_id="reference-work-summary",
        compatible_style_cluster_ids=("reference-work-summary",),
        page_templates=tuple(templates),
    )


def write_library_index(index: LibraryIndex, output_path: str | os.PathLike[str]) -> str:
    """Write the library index to disk in deterministic field order."""

    path = Path(output_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = index.to_dict()
    text = json.dumps(payload, ensure_ascii=False, sort_keys=False, indent=2)
    path.write_text(text, encoding="utf-8")
    return _sha256_bytes(text.encode("utf-8"))


def load_library_index(path: str | os.PathLike[str]) -> LibraryIndex:
    """Load a previously compiled library index."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema_version") != "4.0":
        raise PageTemplateError(
            f"unsupported library index schema_version: {raw.get('schema_version')}"
        )
    if raw.get("scoring") != dict(DEFAULT_SCORING):
        raise PageTemplateError(
            "library scoring contract does not match the frozen v6.1 weights"
        )
    loaded_templates: list[PageTemplate] = []
    for item in raw.get("page_templates", []):
        raw_inventory = item.get("governed_content_inventory")
        inventory_known = _governed_content_inventory_is_known(raw_inventory)
        governed_inventory = (
            dict(raw_inventory)
            if inventory_known
            else _unknown_governed_content_inventory()
        )
        source_identity_known = bool(item.get("source_slide_sha256"))
        direct_use = bool(
            item.get("direct_use", False)
            and source_identity_known
            and inventory_known
            and governed_inventory["complete"]
        )
        eligibility_known = bool(
            item.get("eligibility_known", "direct_use" in item)
            and source_identity_known
            and inventory_known
        )
        loaded_templates.append(
            PageTemplate(
                schema_version="1.0",
                page_id=item["page_id"],
                package_sha256=item["package_sha256"],
                slide_number=int(item["slide_number"]),
                source_path=item["source_path"],
                source_sha256=item["source_sha256"],
                source_slide_sha256=item.get("source_slide_sha256", ""),
                page_role=item["page_role"],
                category_names=tuple(item.get("category_names", [])),
                style_cluster_id=item["style_cluster_id"],
                deck_family_id=item["deck_family_id"],
                theme_palette=tuple(item.get("theme_palette", [])),
                capacity=dict(item.get("capacity", {})),
                editability=item.get("editability", "native_editable"),
                certification=item.get("certification", "certified"),
                visual_quality=float(item.get("visual_quality", 0.0)),
                structure=dict(item.get("structure", {})),
                slot_graph=dict(item.get("slot_graph", {})),
                requires_customer_asset=bool(
                    item.get("requires_customer_asset", True)
                ),
                media_retention_policy=str(
                    item.get("media_retention_policy", "unknown")
                ),
                pool=item.get("pool"),
                decision=item.get("decision"),
                # Legacy v4 records without governed inventory remain
                # loadable for audit, but never regain direct-use authority.
                direct_use=direct_use,
                eligibility_known=eligibility_known,
                style_features=dict(item.get("style_features", {})),
                governed_content_inventory=governed_inventory,
            )
        )
    templates = tuple(loaded_templates)
    dominant_style = raw.get(
        "dominant_style_cluster_id", DEFAULT_DOMINANT_STYLE_CLUSTER
    )
    compatible_raw = raw.get("compatible_style_cluster_ids")
    compatible_styles = (
        tuple(compatible_raw)
        if isinstance(compatible_raw, list) and compatible_raw
        else (dominant_style,)
    )
    return LibraryIndex(
        schema_version="4.0",
        library_id=raw["library_id"],
        compiled_at=raw["compiled_at"],
        source_core_schema=raw["source_core_schema"],
        private_root_sha256=raw["private_root_sha256"],
        source_package_count=int(raw.get("source_package_count", 0)),
        source_package_index={
            str(key): dict(value)
            for key, value in raw.get("source_package_index", {}).items()
        },
        page_template_count=len(templates),
        role_index=dict(raw.get("role_index", {})),
        style_cluster_index=dict(raw.get("style_cluster_index", {})),
        deck_family_index=dict(raw.get("deck_family_index", {})),
        category_index=dict(raw.get("category_index", {})),
        scoring=dict(raw.get("scoring", DEFAULT_SCORING)),
        dominant_style_cluster_id=dominant_style,
        compatible_style_cluster_ids=compatible_styles,
        page_templates=templates,
    )


def _template_reuse_risk(template: PageTemplate) -> float:
    """Return a deterministic 0..1 risk that source semantics leak through."""

    source_slots = template.slot_graph.get("slots", ())
    source_text = " ".join(
        str(item.get("source_text", ""))
        for item in source_slots
        if isinstance(item, Mapping)
    )
    if not source_text:
        return 0.0
    risk = min(0.35, len(source_text) / 700.0)
    if re.search(r"[A-Za-z]{3,}", source_text):
        risk += 0.12
    if re.search(
        r"(logo|brand|nestle|bilibili|b站|阿迪|耐克|星巴克|erke|abbott|完美日记|蚂蚁森林)",
        source_text,
        re.I,
    ):
        risk += 0.35
    return min(1.0, risk)


def _is_direct_use_eligible(template: PageTemplate) -> bool:
    """Return the fail-closed materialization eligibility for a template."""

    return bool(template.eligibility_known and template.direct_use) and not (
        _is_reference_only_pool(template.pool)
        or _is_non_direct_decision(template.decision)
    )


def _style_compatibility(
    index: LibraryIndex,
    *,
    requested: str,
    candidate: str,
) -> str:
    if candidate == requested:
        return "exact"
    registered_group = set(index.compatible_style_cluster_ids)
    if requested in registered_group and candidate in registered_group:
        return "registered"
    return "incompatible"


def _available_asset_kinds(template: PageTemplate) -> frozenset[str]:
    available = {"text"}
    structure = template.structure
    if int(structure.get("page_media_count", 0) or 0) > 0:
        available.update(("image", "media"))
    if int(structure.get("page_chart_count", 0) or 0) > 0:
        available.add("chart")
    if int(structure.get("page_table_count", 0) or 0) > 0:
        available.add("table")
    return frozenset(available)


def _asset_fit(
    template: PageTemplate,
    asset_requirements: Iterable[str],
    *,
    customer_assets_available: bool,
) -> float:
    requested = tuple(
        dict.fromkeys(
            str(item).strip().lower()
            for item in asset_requirements
            if str(item).strip()
        )
    )
    if template.requires_customer_asset and not customer_assets_available:
        return 0.0
    if not requested:
        return 1.0
    available = _available_asset_kinds(template)
    hits = sum(1 for item in requested if item in available)
    return round(hits / len(requested), 6)


def _candidate_scores(
    template: PageTemplate,
    *,
    role: str,
    capacity_budget: int,
    semantic_categories: Iterable[str],
    style_compatibility: str,
    editability: str | None,
    asset_fit: float,
) -> CandidateScores:
    role_score = 1.0 if template.page_role == role else 0.0
    capacity = max(0, int(template.capacity.get("max_text_chars", 0) or 0))
    if capacity_budget <= 0:
        capacity_score = 1.0
    else:
        capacity_score = min(capacity, capacity_budget) / max(
            capacity, capacity_budget
        )
    requested_semantics = tuple(dict.fromkeys(semantic_categories))
    if requested_semantics:
        semantic_set = set(template.category_names)
        semantic_hits = sum(
            1 for category in requested_semantics if category in semantic_set
        )
        semantic_score = semantic_hits / len(requested_semantics)
    else:
        semantic_score = 1.0
    style_score = {
        "exact": 1.0,
        "registered": 0.5,
        "incompatible": 0.0,
    }[style_compatibility]
    editability_matches = (
        editability is None
        or editability == "any"
        or editability == template.editability
    )
    # The final 0.10 component represents both editability and required-asset
    # fit, matching the frozen v6.1 scoring contract.
    editability_score = asset_fit if editability_matches else 0.0
    components = {
        "role": round(role_score, 6),
        "capacity": round(capacity_score, 6),
        "semantic": round(semantic_score, 6),
        "style": round(style_score, 6),
        "editability": round(editability_score, 6),
    }
    total = round(
        sum(DEFAULT_SCORING[name] * components[name] for name in DEFAULT_SCORING),
        6,
    )
    return CandidateScores(total=total, **components)


def _with_ineligibility(
    candidate: PageTemplateCandidate,
    reason: str,
) -> PageTemplateCandidate:
    return PageTemplateCandidate(
        page_template=candidate.page_template,
        eligibility=False,
        reasons=(*candidate.reasons, reason),
        fallback_reason=candidate.fallback_reason,
        asset_fit=candidate.asset_fit,
        capacity_fit=candidate.capacity_fit,
        residue_risk=candidate.residue_risk,
        style_compatibility=candidate.style_compatibility,
        scores=candidate.scores,
    )


def _with_fallback(
    candidate: PageTemplateCandidate,
    reason: str,
) -> PageTemplateCandidate:
    fallback_reason = (
        reason
        if candidate.fallback_reason is None
        else f"{candidate.fallback_reason};{reason}"
    )
    return PageTemplateCandidate(
        page_template=candidate.page_template,
        eligibility=candidate.eligibility,
        reasons=candidate.reasons,
        fallback_reason=fallback_reason,
        asset_fit=candidate.asset_fit,
        capacity_fit=candidate.capacity_fit,
        residue_risk=candidate.residue_risk,
        style_compatibility=candidate.style_compatibility,
        scores=candidate.scores,
    )


def query_page_template_candidates(
    index: LibraryIndex,
    *,
    role: str,
    capacity_budget: int = 0,
    semantic_categories: Sequence[str] = (),
    style_cluster: str | None = None,
    editability: str | None = "native_editable",
    asset_requirements: Sequence[str] = (),
    customer_assets_available: bool = False,
    limit: int = 5,
    allow_fallback: bool = True,
    direct_use_only: bool = True,
    include_ineligible: bool = False,
) -> tuple[PageTemplateCandidate, ...]:
    """Return candidates with complete, deterministic selection evidence."""

    requested_style = style_cluster or index.dominant_style_cluster_id
    evaluated: list[PageTemplateCandidate] = []
    for template in index.page_templates:
        reasons: list[str] = []
        if direct_use_only:
            if not template.eligibility_known:
                reasons.append("eligibility_unknown")
            elif not template.direct_use:
                reasons.append("direct_use_disabled")
            if _is_reference_only_pool(template.pool) or _is_non_direct_decision(
                template.decision
            ):
                reasons.append("reference_only")
        if template.certification not in {"certified", "certified-private"}:
            reasons.append("certification_not_allowed")
        editability_matches = (
            editability is None
            or editability == "any"
            or editability == template.editability
        )
        if not editability_matches:
            reasons.append("editability_mismatch")
        asset_fit = _asset_fit(
            template,
            asset_requirements,
            customer_assets_available=customer_assets_available,
        )
        if asset_fit < 1.0:
            reasons.append("asset_fit_incomplete")
        if template.requires_customer_asset and not customer_assets_available:
            reasons.append("customer_asset_required")
        capacity = max(
            0, int(template.capacity.get("max_text_chars", 0) or 0)
        )
        capacity_fit = capacity_budget <= 0 or capacity >= capacity_budget
        if not capacity_fit:
            reasons.append("capacity_insufficient")
        residue_risk = round(_template_reuse_risk(template), 6)
        if residue_risk >= 0.65:
            reasons.append("residue_risk_high")
        compatibility = _style_compatibility(
            index,
            requested=requested_style,
            candidate=template.style_cluster_id,
        )
        scores = _candidate_scores(
            template,
            role=role,
            capacity_budget=capacity_budget,
            semantic_categories=semantic_categories,
            style_compatibility=compatibility,
            editability=editability,
            asset_fit=asset_fit,
        )
        evaluated.append(
            PageTemplateCandidate(
                page_template=template,
                eligibility=not reasons,
                reasons=tuple(reasons),
                fallback_reason=None,
                asset_fit=asset_fit,
                capacity_fit=capacity_fit,
                residue_risk=residue_risk,
                style_compatibility=compatibility,
                scores=scores,
            )
        )

    role_exact_exists = any(
        candidate.eligibility and candidate.page_template.page_role == role
        for candidate in evaluated
    )
    role_selected: list[PageTemplateCandidate] = []
    for candidate in evaluated:
        if not candidate.eligibility:
            role_selected.append(candidate)
        elif candidate.page_template.page_role == role:
            role_selected.append(candidate)
        elif role_exact_exists or not allow_fallback:
            role_selected.append(_with_ineligibility(candidate, "role_mismatch"))
        else:
            role_selected.append(
                _with_fallback(candidate, "role:no_exact_role_candidate")
            )

    style_gated: list[PageTemplateCandidate] = []
    for candidate in role_selected:
        if not candidate.eligibility:
            style_gated.append(candidate)
        elif candidate.style_compatibility == "incompatible":
            style_gated.append(
                _with_ineligibility(candidate, "style_incompatible")
            )
        elif (
            candidate.style_compatibility == "registered"
            and not allow_fallback
        ):
            style_gated.append(
                _with_ineligibility(candidate, "style_fallback_disabled")
            )
        else:
            style_gated.append(candidate)

    exact_style_exists = any(
        candidate.eligibility and candidate.style_compatibility == "exact"
        for candidate in style_gated
    )
    selected: list[PageTemplateCandidate] = []
    for candidate in style_gated:
        if not candidate.eligibility:
            selected.append(candidate)
        elif candidate.style_compatibility == "registered":
            if exact_style_exists:
                selected.append(
                    _with_ineligibility(candidate, "style_fallback_not_needed")
                )
            else:
                selected.append(
                    _with_fallback(
                        candidate,
                        "style:registered_compatible_cluster",
                    )
                )
        else:
            selected.append(candidate)

    final_candidates = [
        PageTemplateCandidate(
            page_template=candidate.page_template,
            eligibility=candidate.eligibility,
            reasons=("eligible",) if candidate.eligibility else candidate.reasons,
            fallback_reason=candidate.fallback_reason,
            asset_fit=candidate.asset_fit,
            capacity_fit=candidate.capacity_fit,
            residue_risk=candidate.residue_risk,
            style_compatibility=candidate.style_compatibility,
            scores=candidate.scores,
        )
        for candidate in selected
        if include_ineligible or candidate.eligibility
    ]
    final_candidates.sort(
        key=lambda candidate: (
            not candidate.eligibility,
            -candidate.scores.total,
            candidate.page_template.page_id,
        )
    )
    return tuple(final_candidates[: max(0, limit)])


def serialize_page_template_candidates(
    candidates: Sequence[PageTemplateCandidate],
) -> str:
    """Serialize ranked evidence without timestamps or unstable key order."""

    return json.dumps(
        {
            "schema_version": "1.0",
            "candidates": [candidate.to_dict() for candidate in candidates],
        },
        ensure_ascii=False,
        sort_keys=False,
        separators=(",", ":"),
    )


def query_page_templates(
    index: LibraryIndex,
    *,
    role: str,
    capacity_budget: int = 0,
    semantic_categories: Sequence[str] = (),
    style_cluster: str | None = None,
    editability: str | None = "native_editable",
    customer_assets_available: bool = False,
    limit: int = 5,
    allow_fallback: bool = True,
    direct_use_only: bool = True,
) -> tuple[PageTemplate, ...]:
    """Compatibility wrapper returning only eligible page templates.

    Reference-only and otherwise non-direct-use records are excluded by
    default.  Callers building review tools can opt in with
    ``direct_use_only=False``; the physical authoring route must not.
    """
    candidates = query_page_template_candidates(
        index,
        role=role,
        capacity_budget=capacity_budget,
        semantic_categories=semantic_categories,
        style_cluster=style_cluster,
        editability=editability,
        customer_assets_available=customer_assets_available,
        limit=limit,
        allow_fallback=allow_fallback,
        direct_use_only=direct_use_only,
    )
    return tuple(candidate.page_template for candidate in candidates)


__all__ = [
    "CERTIFIED_CORE_SCHEMA",
    "DEFAULT_COMPATIBLE_STYLE_CLUSTERS",
    "DEFAULT_DOMINANT_STYLE_CLUSTER",
    "DEFAULT_SCORING",
    "CandidateScores",
    "LibraryIndex",
    "PageTemplate",
    "PageTemplateCandidate",
    "PageTemplateError",
    "SlotRecord",
    "_template_reuse_risk",
    "compile_page_templates",
    "compile_reference_deck",
    "load_library_index",
    "query_page_template_candidates",
    "query_page_templates",
    "resolve_private_root",
    "serialize_page_template_candidates",
    "write_library_index",
]
