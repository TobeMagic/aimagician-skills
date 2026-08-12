"""Independent security contracts for the v6.1 physical-report validator.

This module deliberately has no dependency on the report validator or the
physical assembler.  It provides small, fail-closed APIs that the independent
validator can call without trusting producer-authored counters or locators.

The contracts cover four trust boundaries:

* a locked query bundle is parsed, schema checked, and converted into the
  authoritative set of selected text, governed-content, and media surfaces;
* fact renderings use a closed mode vocabulary with exact semantics;
* ZIP/OPC entry names are canonical and unambiguous; and
* external relationships are restricted to explicit HTTPS hyperlinks.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import posixpath
import re
import stat
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import unquote, urlsplit


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PAGE_ID_RE = re.compile(r"^([0-9a-f]{64}):([0-9]{3})$")
NUMERIC_RE = re.compile(
    r"^[-+]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?"
    r"(?:[Ee][-+]?\d+)?([%％])?$"
)
NUMERIC_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.\d+)?(?:[Ee][-+]?\d+)?(?:[%％])?(?![A-Za-z0-9])"
)
FRAME_LOCATOR_RE = re.compile(r"^(?:graphicFrame|chartFrame)\[id=([1-9][0-9]*)\]")
SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"

PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

ALLOWED_EXTERNAL_RELATIONSHIP_TYPES = frozenset(
    {
        "http://schemas.openxmlformats.org/officedocument/2006/relationships/hyperlink",
        "http://purl.oclc.org/ooxml/officedocument/relationships/hyperlink",
    }
)

EXACT_FACT_MODES = frozenset({"exact", "explicit-exact", "source-fact"})
NORMALIZED_FACT_MODES = frozenset(
    {"whitespace", "explicit-whitespace", "normalized-year"}
)
NUMERIC_FACT_MODES = frozenset(
    {"source-numeric-scalar", "source-numeric-rendering"}
)
SLICE_FACT_MODES = frozenset({"slice", "explicit-slice"})
JOIN_FACT_MODES = frozenset({"join", "explicit-join"})
SAFE_FACT_MODES = (
    EXACT_FACT_MODES
    | NORMALIZED_FACT_MODES
    | NUMERIC_FACT_MODES
    | SLICE_FACT_MODES
    | JOIN_FACT_MODES
)
SAFE_JOIN_SEPARATORS = ("", " ", "\n", " / ", " · ", "：", ": ")


@dataclass(frozen=True, order=True)
class ContractFinding:
    """One deterministic fail-closed contract finding."""

    code: str
    location: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "location": self.location,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class FragmentGroupAuthority:
    ordinal: int
    page_id: str
    group_id: str
    ordered_slot_ids: tuple[str, ...]


@dataclass(frozen=True)
class SelectedPageAuthority:
    ordinal: int
    query_id: str
    page_id: str
    package_sha256: str
    slide_number: int
    page_role: str
    text_slot_ids: tuple[str, ...]
    text_slot_shape_ids: tuple[tuple[str, int], ...]
    fragment_groups: tuple[FragmentGroupAuthority, ...]
    governed_slots: tuple[Mapping[str, Any], ...]
    media_policy: str
    minimum_asset_bindings: int
    maximum_asset_bindings: int
    structure_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class QueryCoverageAuthority:
    """Immutable coverage derived from the locked query-bundle bytes."""

    library_index_sha256: str
    selected_pages: tuple[SelectedPageAuthority, ...]
    required_text_keys: frozenset[tuple[int, str, str]]
    required_governed_keys: frozenset[tuple[int, str, str]]
    text_slot_shape_ids: Mapping[tuple[int, str, str], int]
    fragment_group_contracts: Mapping[
        tuple[int, str, str], tuple[str, ...]
    ]
    governed_slot_shape_ids: Mapping[tuple[int, str, str], int]
    governed_slot_contracts: Mapping[tuple[int, str, str], Mapping[str, Any]]
    certified_media_sha256: frozenset[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "library_index_sha256": self.library_index_sha256,
            "selected_pages": [
                {
                    "ordinal": page.ordinal,
                    "query_id": page.query_id,
                    "page_id": page.page_id,
                    "package_sha256": page.package_sha256,
                    "slide_number": page.slide_number,
                    "page_role": page.page_role,
                    "text_slot_ids": list(page.text_slot_ids),
                    "text_slot_shape_ids": {
                        slot_id: shape_id
                        for slot_id, shape_id in page.text_slot_shape_ids
                    },
                    "fragment_groups": {
                        group.group_id: list(group.ordered_slot_ids)
                        for group in page.fragment_groups
                    },
                    "governed_slot_ids": [
                        str(slot.get("slot_id", "")) for slot in page.governed_slots
                    ],
                    "media_policy": page.media_policy,
                    "minimum_asset_bindings": page.minimum_asset_bindings,
                    "maximum_asset_bindings": page.maximum_asset_bindings,
                    "structure_counts": dict(page.structure_counts),
                }
                for page in self.selected_pages
            ],
            "required_text_keys": [list(key) for key in sorted(self.required_text_keys)],
            "required_governed_keys": [
                list(key) for key in sorted(self.required_governed_keys)
            ],
            "fragment_group_contracts": {
                "|".join((str(key[0]), key[1], key[2])): list(value)
                for key, value in sorted(self.fragment_group_contracts.items())
            },
            "certified_media_sha256": sorted(self.certified_media_sha256),
        }


@dataclass(frozen=True)
class QueryCoverageResult:
    authority: QueryCoverageAuthority | None
    findings: tuple[ContractFinding, ...]

    @property
    def status(self) -> str:
        return "pass" if not self.findings and self.authority is not None else "fail"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "authority": self.authority.to_dict() if self.authority else None,
            "issue_count": len(self.findings),
            "issues": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class FragmentGroupValidationResult:
    authorized_character_keys: frozenset[tuple[int, str, str]]
    findings: tuple[ContractFinding, ...]

    @property
    def status(self) -> str:
        return "pass" if not self.findings else "fail"


@dataclass(frozen=True)
class ZipEntryAudit:
    canonical_names: tuple[str, ...]
    findings: tuple[ContractFinding, ...]

    @property
    def status(self) -> str:
        return "pass" if not self.findings else "fail"


@dataclass(frozen=True)
class ZipResourceLimits:
    """Metadata-only decompression limits for one ZIP/OPC package.

    These limits are checked from the central directory before any member is
    decompressed.  They therefore bound both aggregate allocation and the XML
    inputs passed to downstream parsers.
    """

    max_entries: int
    max_entry_uncompressed_bytes: int
    max_total_uncompressed_bytes: int
    max_compression_ratio: float
    max_xml_uncompressed_bytes: int
    max_relationship_uncompressed_bytes: int

    def validate(self) -> None:
        for name, value in (
            ("max_entries", self.max_entries),
            ("max_entry_uncompressed_bytes", self.max_entry_uncompressed_bytes),
            ("max_total_uncompressed_bytes", self.max_total_uncompressed_bytes),
            ("max_xml_uncompressed_bytes", self.max_xml_uncompressed_bytes),
            (
                "max_relationship_uncompressed_bytes",
                self.max_relationship_uncompressed_bytes,
            ),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if (
            not isinstance(self.max_compression_ratio, (int, float))
            or isinstance(self.max_compression_ratio, bool)
            or float(self.max_compression_ratio) <= 1
        ):
            raise ValueError("max_compression_ratio must be greater than 1")
        if self.max_xml_uncompressed_bytes > self.max_entry_uncompressed_bytes:
            raise ValueError(
                "max_xml_uncompressed_bytes cannot exceed the per-entry limit"
            )
        if (
            self.max_relationship_uncompressed_bytes
            > self.max_xml_uncompressed_bytes
        ):
            raise ValueError(
                "max_relationship_uncompressed_bytes cannot exceed the XML limit"
            )
        if (
            self.max_entry_uncompressed_bytes
            > self.max_total_uncompressed_bytes
        ):
            raise ValueError(
                "max_entry_uncompressed_bytes cannot exceed the aggregate limit"
            )


PPTX_ZIP_RESOURCE_LIMITS = ZipResourceLimits(
    max_entries=10_000,
    max_entry_uncompressed_bytes=256 * 1024 * 1024,
    max_total_uncompressed_bytes=1024 * 1024 * 1024,
    max_compression_ratio=200.0,
    max_xml_uncompressed_bytes=32 * 1024 * 1024,
    max_relationship_uncompressed_bytes=8 * 1024 * 1024,
)


def _finding(
    findings: list[ContractFinding],
    code: str,
    location: str,
    detail: str,
) -> None:
    findings.append(ContractFinding(code=code, location=location, detail=detail))


def _sorted_findings(findings: Iterable[ContractFinding]) -> tuple[ContractFinding, ...]:
    return tuple(sorted(findings, key=lambda item: (item.location, item.code, item.detail)))


def _schema_findings(payload: Any, schema_name: str) -> list[ContractFinding]:
    findings: list[ContractFinding] = []
    try:
        import jsonschema
        from referencing import Registry, Resource
    except ImportError as exc:
        return [
            ContractFinding(
                "QUERY_SCHEMA_VALIDATOR_UNAVAILABLE",
                "query_bundle",
                str(exc),
            )
        ]
    try:
        resources: list[tuple[str, Any]] = []
        root_schema: Mapping[str, Any] | None = None
        for path in sorted(SCHEMA_ROOT.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema_id = schema.get("$id")
            if isinstance(schema_id, str):
                resources.append((schema_id, Resource.from_contents(schema)))
            if path.name == schema_name:
                root_schema = schema
        if root_schema is None:
            raise FileNotFoundError(SCHEMA_ROOT / schema_name)
        registry = Registry().with_resources(resources)
        validator = jsonschema.Draft202012Validator(
            root_schema,
            registry=registry,
            format_checker=jsonschema.FormatChecker(),
        )
        errors = sorted(
            validator.iter_errors(payload),
            key=lambda error: tuple(str(item) for item in error.absolute_path),
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [
            ContractFinding(
                "QUERY_SCHEMA_LOAD_FAILED",
                "query_bundle",
                str(exc),
            )
        ]
    for error in errors:
        suffix = ".".join(str(item) for item in error.absolute_path)
        _finding(
            findings,
            "QUERY_BUNDLE_SCHEMA_INVALID",
            f"query_bundle.{suffix}" if suffix else "query_bundle",
            error.message,
        )
    return findings


def _unique_records(
    records: Sequence[Mapping[str, Any]],
    *,
    kind: str,
    findings: list[ContractFinding],
) -> dict[tuple[int, str, str], Mapping[str, Any]]:
    result: dict[tuple[int, str, str], Mapping[str, Any]] = {}
    for index, record in enumerate(records):
        key = (record.get("ordinal"), record.get("page_id"), record.get("slot_id"))
        location = f"{kind}.{index}"
        if (
            type(key[0]) is not int
            or not isinstance(key[1], str)
            or not isinstance(key[2], str)
            or not key[2]
        ):
            _finding(findings, "COVERAGE_KEY_INVALID", location, repr(key))
            continue
        typed_key = (int(key[0]), key[1], key[2])
        if typed_key in result:
            _finding(findings, "COVERAGE_KEY_DUPLICATE", location, repr(typed_key))
            continue
        result[typed_key] = record
    return result


def _derive_fragment_group_authority(
    slot_graph: Mapping[str, Any],
    *,
    ordinal: int,
    page_id: str,
    location: str,
    findings: list[ContractFinding],
) -> tuple[FragmentGroupAuthority, ...]:
    """Cross-check group membership with each locked slot's group metadata."""

    raw_slots = slot_graph.get("slots")
    raw_groups = slot_graph.get("fragment_groups")
    if not isinstance(raw_slots, list) or not isinstance(raw_groups, list):
        _finding(
            findings,
            "QUERY_FRAGMENT_GROUP_INVENTORY_INVALID",
            location,
            "slots/fragment_groups are not arrays",
        )
        return ()
    slot_by_id: dict[str, Mapping[str, Any]] = {}
    for index, raw_slot in enumerate(raw_slots):
        slot_id = raw_slot.get("slot_id") if isinstance(raw_slot, Mapping) else None
        if not isinstance(slot_id, str) or not slot_id or slot_id in slot_by_id:
            _finding(
                findings,
                "QUERY_FRAGMENT_SLOT_ID_INVALID",
                f"{location}.slots.{index}",
                repr(slot_id),
            )
            continue
        slot_by_id[slot_id] = raw_slot

    contracts: list[FragmentGroupAuthority] = []
    described_slots: set[str] = set()
    seen_group_ids: set[str] = set()
    for index, raw_group in enumerate(raw_groups):
        group_location = f"{location}.fragment_groups.{index}"
        if not isinstance(raw_group, Mapping):
            _finding(
                findings,
                "QUERY_FRAGMENT_GROUP_INVALID",
                group_location,
                repr(raw_group),
            )
            continue
        group_id = raw_group.get("group_id")
        slot_ids = raw_group.get("slot_ids")
        if (
            not isinstance(group_id, str)
            or not re.fullmatch(r"fragment_[0-9]{2}", group_id)
            or group_id in seen_group_ids
            or not isinstance(slot_ids, list)
            or len(slot_ids) < 2
            or not all(isinstance(slot_id, str) and slot_id for slot_id in slot_ids)
            or len(slot_ids) != len(set(slot_ids))
        ):
            _finding(
                findings,
                "QUERY_FRAGMENT_GROUP_INVALID",
                group_location,
                repr(raw_group),
            )
            continue
        seen_group_ids.add(group_id)
        declared = set(slot_ids)
        members = {
            slot_id
            for slot_id, slot in slot_by_id.items()
            if slot.get("group_id") == group_id
        }
        if declared != members or described_slots.intersection(declared):
            _finding(
                findings,
                "QUERY_FRAGMENT_GROUP_MEMBERSHIP_INVALID",
                group_location,
                f"declared={sorted(declared)!r} slots={sorted(members)!r}",
            )
            continue
        described_slots.update(declared)
        ordered: list[tuple[int, str]] = []
        slot_contract_valid = True
        for slot_id in slot_ids:
            slot = slot_by_id.get(slot_id)
            group_order = slot.get("group_order") if slot is not None else None
            allowed_modes = slot.get("allowed_binding_modes") if slot is not None else None
            if (
                slot is None
                or type(group_order) is not int
                or group_order < 1
                or slot.get("max_chars") != 1
                or slot.get("semantic_role")
                not in {"title_fragment", "label_fragment"}
                or not isinstance(allowed_modes, list)
                or set(allowed_modes) != {"character", "clear"}
            ):
                slot_contract_valid = False
                _finding(
                    findings,
                    "QUERY_FRAGMENT_SLOT_CONTRACT_INVALID",
                    f"{group_location}.{slot_id}",
                    repr(slot),
                )
                continue
            ordered.append((group_order, slot_id))
        if not slot_contract_valid:
            continue
        if sorted(order for order, _ in ordered) != list(
            range(1, len(ordered) + 1)
        ):
            _finding(
                findings,
                "QUERY_FRAGMENT_GROUP_ORDER_INVALID",
                group_location,
                repr(sorted(order for order, _ in ordered)),
            )
            continue
        contracts.append(
            FragmentGroupAuthority(
                ordinal=ordinal,
                page_id=page_id,
                group_id=group_id,
                ordered_slot_ids=tuple(
                    slot_id for _, slot_id in sorted(ordered)
                ),
            )
        )

    undeclared = sorted(
        slot_id
        for slot_id, slot in slot_by_id.items()
        if isinstance(slot.get("group_id"), str)
        and str(slot["group_id"]).startswith("fragment_")
        and slot_id not in described_slots
    )
    if undeclared:
        _finding(
            findings,
            "QUERY_FRAGMENT_SLOT_UNDECLARED",
            location,
            repr(undeclared),
        )
    return tuple(sorted(contracts, key=lambda item: item.group_id))


def _validate_template_semantics(
    template: Mapping[str, Any],
    *,
    ordinal: int,
    query_id: str,
    findings: list[ContractFinding],
) -> SelectedPageAuthority | None:
    location = f"query_bundle.queries[{ordinal}].selected.page_template"
    page_id = template.get("page_id")
    package_sha = template.get("package_sha256")
    slide_number = template.get("slide_number")
    match = PAGE_ID_RE.fullmatch(page_id) if isinstance(page_id, str) else None
    if (
        match is None
        or not isinstance(package_sha, str)
        or match.group(1) != package_sha
        or type(slide_number) is not int
        or int(match.group(2)) != slide_number
        or template.get("source_sha256") != package_sha
    ):
        _finding(findings, "QUERY_SELECTED_PAGE_IDENTITY_INVALID", location, str(page_id))
        return None
    for key, expected in (
        ("certification", "certified"),
        ("editability", "native_editable"),
        ("direct_use", True),
        ("eligibility_known", True),
    ):
        if template.get(key) != expected:
            _finding(
                findings,
                "QUERY_SELECTED_PAGE_NOT_DIRECT_USE",
                f"{location}.{key}",
                f"expected {expected!r}, observed {template.get(key)!r}",
            )

    slot_graph = template.get("slot_graph")
    text_slot_ids: tuple[str, ...] = ()
    text_slot_shape_ids: tuple[tuple[str, int], ...] = ()
    fragment_groups: tuple[FragmentGroupAuthority, ...] = ()
    if isinstance(slot_graph, Mapping):
        raw_ids = slot_graph.get("text_slot_ids")
        slots = slot_graph.get("slots")
        if isinstance(raw_ids, list) and all(isinstance(item, str) for item in raw_ids):
            text_slot_ids = tuple(raw_ids)
        slot_records = [
            slot
            for slot in slots
            if isinstance(slot, Mapping) and isinstance(slot.get("slot_id"), str)
        ] if isinstance(slots, list) else []
        slot_ids = [slot.get("slot_id") for slot in slot_records]
        shape_pairs = [
            (str(slot["slot_id"]), slot.get("shape_id")) for slot in slot_records
        ]
        if (
            len(text_slot_ids) != len(set(text_slot_ids))
            or slot_graph.get("text_slot_count") != len(text_slot_ids)
            or set(slot_ids) != set(text_slot_ids)
            or len(slot_ids) != len(text_slot_ids)
            or any(type(shape_id) is not int or shape_id < 1 for _, shape_id in shape_pairs)
            or len({shape_id for _, shape_id in shape_pairs}) != len(shape_pairs)
        ):
            _finding(
                findings,
                "QUERY_TEXT_SLOT_INVENTORY_INVALID",
                f"{location}.slot_graph",
                "text slot ids/count/records are not one-to-one",
            )
        else:
            text_slot_shape_ids = tuple(
                sorted((slot_id, int(shape_id)) for slot_id, shape_id in shape_pairs)
            )
        fragment_groups = _derive_fragment_group_authority(
            slot_graph,
            ordinal=ordinal,
            page_id=str(page_id),
            location=f"{location}.slot_graph",
            findings=findings,
        )
    else:
        _finding(
            findings,
            "QUERY_TEXT_SLOT_INVENTORY_INVALID",
            f"{location}.slot_graph",
            "slot_graph is not an object",
        )

    inventory = template.get("governed_content_inventory")
    governed_slots: tuple[Mapping[str, Any], ...] = ()
    if isinstance(inventory, Mapping):
        raw_slots = inventory.get("slots")
        governed_slots = tuple(
            item for item in raw_slots if isinstance(item, Mapping)
        ) if isinstance(raw_slots, list) else ()
        governed_ids = [item.get("slot_id") for item in governed_slots]
        if (
            inventory.get("complete") is not True
            or inventory.get("scan_errors") != []
            or inventory.get("content_slot_count") != len(governed_slots)
            or inventory.get("customer_data_slot_count") != len(governed_slots)
            or len(governed_ids) != len(set(governed_ids))
            or not all(isinstance(item, str) and item for item in governed_ids)
        ):
            _finding(
                findings,
                "QUERY_GOVERNED_SLOT_INVENTORY_INVALID",
                f"{location}.governed_content_inventory",
                "governed slots are incomplete, duplicated, or count-drifted",
            )
        peer_members: dict[str, list[Mapping[str, Any]]] = {}
        for record in governed_slots:
            peer_id = record.get("peer_group_id")
            if isinstance(peer_id, str) and peer_id:
                peer_members.setdefault(peer_id, []).append(record)
        for peer_id, members in peer_members.items():
            kinds = {str(member.get("kind", "")) for member in members}
            if len(members) != 2 or kinds != {"chart-value", "workbook-cell"}:
                _finding(
                    findings,
                    "QUERY_GOVERNED_PEER_CONTRACT_INVALID",
                    f"{location}.governed_content_inventory.{peer_id}",
                    f"expected chart-value/workbook-cell pair, observed {sorted(kinds)}",
                )
    else:
        _finding(
            findings,
            "QUERY_GOVERNED_SLOT_INVENTORY_INVALID",
            f"{location}.governed_content_inventory",
            "inventory is not an object",
        )

    structure = template.get("structure")
    page_image_count = (
        structure.get("page_image_count") if isinstance(structure, Mapping) else None
    )
    if type(page_image_count) is not int or page_image_count < 0:
        _finding(
            findings,
            "QUERY_MEDIA_INVENTORY_INVALID",
            f"{location}.structure.page_image_count",
            repr(page_image_count),
        )
        page_image_count = 0
    immutable_structure_fields = (
        "page_shape_count",
        "page_native_object_count",
        "page_image_count",
        "page_chart_count",
        "page_table_count",
    )
    structure_counts: list[tuple[str, int]] = []
    for field in immutable_structure_fields:
        value = structure.get(field) if isinstance(structure, Mapping) else None
        if type(value) is not int or value < 0:
            _finding(
                findings,
                "QUERY_STRUCTURE_COUNT_INVALID",
                f"{location}.structure.{field}",
                repr(value),
            )
            value = 0
        structure_counts.append((field, int(value)))
    policy = str(template.get("media_retention_policy", ""))
    if policy == "customer-replacement-required":
        minimum_assets = maximum_assets = page_image_count
        if page_image_count < 1 or template.get("requires_customer_asset") is not True:
            _finding(
                findings,
                "QUERY_MEDIA_POLICY_INVALID",
                location,
                "customer replacement requires at least one image and customer asset",
            )
    elif policy == "certified-decorative-retain":
        minimum_assets, maximum_assets = 0, page_image_count
    elif policy == "no-page-media":
        minimum_assets = maximum_assets = 0
        if page_image_count != 0:
            _finding(
                findings,
                "QUERY_MEDIA_POLICY_INVALID",
                location,
                "no-page-media conflicts with page_image_count",
            )
    else:
        minimum_assets = maximum_assets = 0
        _finding(findings, "QUERY_MEDIA_POLICY_INVALID", location, policy)

    return SelectedPageAuthority(
        ordinal=ordinal,
        query_id=query_id,
        page_id=page_id,
        package_sha256=package_sha,
        slide_number=slide_number,
        page_role=str(template.get("page_role", "")),
        text_slot_ids=text_slot_ids,
        text_slot_shape_ids=text_slot_shape_ids,
        fragment_groups=fragment_groups,
        governed_slots=governed_slots,
        media_policy=policy,
        minimum_asset_bindings=minimum_assets,
        maximum_asset_bindings=maximum_assets,
        structure_counts=tuple(structure_counts),
    )


def validate_query_bundle_and_coverage(
    query_bundle: Mapping[str, Any],
    *,
    lineage_records: Sequence[Mapping[str, Any]],
    binding_evidence: Sequence[Mapping[str, Any]],
    governed_mutations: Sequence[Mapping[str, Any]],
    expected_library_index_sha256: str | None = None,
) -> QueryCoverageResult:
    """Validate a locked query bundle and derive exact final coverage.

    Selection is anchored by ``(ordinal, page_id)`` from physical lineage.  The
    selected page must occur exactly once as an eligible candidate in the
    corresponding query.  Text and governed mutation keys are then compared to
    the selected candidate's certified inventories, rather than to report
    counters.
    """

    findings = _schema_findings(
        query_bundle,
        "page-template-query-bundle.v1.schema.json",
    )
    if not isinstance(query_bundle, Mapping):
        return QueryCoverageResult(None, _sorted_findings(findings))
    library_sha = query_bundle.get("library_index_sha256")
    if not isinstance(library_sha, str) or not SHA256_RE.fullmatch(library_sha):
        _finding(findings, "QUERY_LIBRARY_SHA256_INVALID", "query_bundle", repr(library_sha))
        library_sha = ""
    if expected_library_index_sha256 is not None and library_sha != expected_library_index_sha256:
        _finding(
            findings,
            "QUERY_LIBRARY_SHA256_MISMATCH",
            "query_bundle.library_index_sha256",
            f"expected {expected_library_index_sha256}, observed {library_sha}",
        )

    lineage_by_ordinal: dict[int, Mapping[str, Any]] = {}
    for index, record in enumerate(lineage_records):
        ordinal = record.get("ordinal")
        page_id = record.get("page_id")
        if type(ordinal) is not int or not isinstance(page_id, str) or not page_id:
            _finding(findings, "QUERY_LINEAGE_INVALID", f"lineage_records.{index}", repr(record))
            continue
        if ordinal in lineage_by_ordinal:
            _finding(findings, "QUERY_LINEAGE_ORDINAL_DUPLICATE", f"lineage_records.{index}", str(ordinal))
            continue
        lineage_by_ordinal[ordinal] = record
    if sorted(lineage_by_ordinal) != list(range(1, len(lineage_by_ordinal) + 1)):
        _finding(
            findings,
            "QUERY_LINEAGE_ORDINAL_SET_INVALID",
            "lineage_records",
            repr(sorted(lineage_by_ordinal)),
        )

    queries = query_bundle.get("queries")
    raw_queries = queries if isinstance(queries, list) else []
    if query_bundle.get("query_count") != len(raw_queries):
        _finding(
            findings,
            "QUERY_BUNDLE_COUNT_MISMATCH",
            "query_bundle.query_count",
            f"reported {query_bundle.get('query_count')!r}, actual {len(raw_queries)}",
        )
    query_by_ordinal: dict[int, Mapping[str, Any]] = {}
    query_ids: set[str] = set()
    for index, query in enumerate(raw_queries):
        if not isinstance(query, Mapping):
            _finding(findings, "QUERY_ENTRY_INVALID", f"query_bundle.queries.{index}", repr(query))
            continue
        ordinal = query.get("target_ordinal")
        query_id = query.get("query_id")
        if type(ordinal) is not int or ordinal in query_by_ordinal:
            _finding(findings, "QUERY_ORDINAL_DUPLICATE_OR_INVALID", f"query_bundle.queries.{index}", repr(ordinal))
            continue
        if not isinstance(query_id, str) or not query_id or query_id in query_ids:
            _finding(findings, "QUERY_ID_DUPLICATE_OR_INVALID", f"query_bundle.queries.{index}", repr(query_id))
            continue
        query_ids.add(query_id)
        query_by_ordinal[ordinal] = query
    if set(query_by_ordinal) != set(lineage_by_ordinal):
        _finding(
            findings,
            "QUERY_ORDINAL_SET_MISMATCH",
            "query_bundle.queries",
            f"queries={sorted(query_by_ordinal)} lineage={sorted(lineage_by_ordinal)}",
        )

    selected_pages: list[SelectedPageAuthority] = []
    certified_media: set[str] = set()
    seen_selected_page_ids: set[str] = set()
    for ordinal, lineage in sorted(lineage_by_ordinal.items()):
        query = query_by_ordinal.get(ordinal)
        if query is None:
            continue
        query_id = str(query.get("query_id", ""))
        result = query.get("result")
        if not isinstance(result, Mapping):
            _finding(findings, "QUERY_RESULT_INVALID", f"query_bundle.queries.{ordinal}.result", repr(result))
            continue
        if result.get("library_index_sha256") != library_sha:
            _finding(
                findings,
                "QUERY_RESULT_LIBRARY_SHA256_MISMATCH",
                f"query_bundle.queries.{ordinal}.result.library_index_sha256",
                repr(result.get("library_index_sha256")),
            )
        candidates = result.get("candidates")
        raw_candidates = candidates if isinstance(candidates, list) else []
        if result.get("count") != len(raw_candidates):
            _finding(findings, "QUERY_RESULT_COUNT_MISMATCH", f"query_bundle.queries.{ordinal}.result.count", repr(result.get("count")))
        eligible_count = sum(
            1 for candidate in raw_candidates
            if isinstance(candidate, Mapping) and candidate.get("eligibility") is True
        )
        if result.get("eligible_count") != eligible_count:
            _finding(findings, "QUERY_RESULT_ELIGIBLE_COUNT_MISMATCH", f"query_bundle.queries.{ordinal}.result.eligible_count", repr(result.get("eligible_count")))
        candidate_ids = [
            candidate.get("page_id")
            for candidate in raw_candidates
            if isinstance(candidate, Mapping)
        ]
        if len(candidate_ids) != len(set(candidate_ids)):
            _finding(findings, "QUERY_RESULT_PAGE_ID_DUPLICATE", f"query_bundle.queries.{ordinal}.result.candidates", repr(candidate_ids))
        selected_page_id = lineage.get("page_id")
        matches = [
            candidate
            for candidate in raw_candidates
            if isinstance(candidate, Mapping)
            and candidate.get("page_id") == selected_page_id
        ]
        if len(matches) != 1:
            _finding(
                findings,
                "QUERY_SELECTED_CANDIDATE_NOT_UNIQUE",
                f"query_bundle.queries.{ordinal}.result.candidates",
                str(selected_page_id),
            )
            continue
        candidate = matches[0]
        template = candidate.get("page_template")
        if (
            candidate.get("eligibility") is not True
            or candidate.get("capacity_fit") is not True
            or candidate.get("style_compatibility") == "incompatible"
            or not isinstance(template, Mapping)
            or template.get("page_id") != selected_page_id
        ):
            _finding(
                findings,
                "QUERY_SELECTED_CANDIDATE_INELIGIBLE",
                f"query_bundle.queries.{ordinal}.selected",
                str(selected_page_id),
            )
            continue
        if result.get("role") != template.get("page_role"):
            _finding(
                findings,
                "QUERY_SELECTED_ROLE_MISMATCH",
                f"query_bundle.queries.{ordinal}.result.role",
                f"result={result.get('role')!r} template={template.get('page_role')!r}",
            )
        selected = _validate_template_semantics(
            template,
            ordinal=ordinal,
            query_id=query_id,
            findings=findings,
        )
        if selected is None:
            continue
        if selected.page_id in seen_selected_page_ids:
            _finding(findings, "QUERY_SELECTED_PAGE_ID_DUPLICATE", f"lineage_records.{ordinal}", selected.page_id)
        seen_selected_page_ids.add(selected.page_id)
        selected_pages.append(selected)
        inventory = template.get("governed_content_inventory")
        metadata = inventory.get("closure_metadata") if isinstance(inventory, Mapping) else None
        media_parts = metadata.get("media_parts") if isinstance(metadata, Mapping) else None
        raw_media = media_parts if isinstance(media_parts, list) else []
        if isinstance(metadata, Mapping) and metadata.get("media_count") != len(raw_media):
            _finding(findings, "QUERY_MEDIA_COUNT_MISMATCH", f"query_bundle.queries.{ordinal}.selected.media_parts", repr(metadata.get("media_count")))
        seen_source_parts: set[str] = set()
        for media_index, media in enumerate(raw_media):
            if not isinstance(media, Mapping):
                _finding(findings, "QUERY_MEDIA_RECORD_INVALID", f"query_bundle.queries.{ordinal}.selected.media_parts.{media_index}", repr(media))
                continue
            source_part = media.get("source_part")
            digest = media.get("sha256")
            if (
                not isinstance(source_part, str)
                or not source_part
                or source_part in seen_source_parts
                or not isinstance(digest, str)
                or not SHA256_RE.fullmatch(digest)
            ):
                _finding(findings, "QUERY_MEDIA_RECORD_INVALID", f"query_bundle.queries.{ordinal}.selected.media_parts.{media_index}", repr(media))
                continue
            seen_source_parts.add(source_part)
            certified_media.add(digest)

    required_text = frozenset(
        (page.ordinal, page.page_id, slot_id)
        for page in selected_pages
        for slot_id in page.text_slot_ids
    )
    text_slot_shape_ids = {
        (page.ordinal, page.page_id, slot_id): shape_id
        for page in selected_pages
        for slot_id, shape_id in page.text_slot_shape_ids
    }
    governed_contracts: dict[tuple[int, str, str], Mapping[str, Any]] = {}
    governed_shape_ids: dict[tuple[int, str, str], int] = {}
    for page in selected_pages:
        for slot in page.governed_slots:
            slot_id = slot.get("slot_id")
            if isinstance(slot_id, str):
                key = (page.ordinal, page.page_id, slot_id)
                governed_contracts[key] = slot
                match = FRAME_LOCATOR_RE.match(str(slot.get("locator", "")))
                governed_shape_ids[key] = int(match.group(1)) if match else 0
    required_governed = frozenset(governed_contracts)

    text_records = [item for item in binding_evidence if item.get("binding_kind") == "text"]
    embedded_records = [item for item in binding_evidence if item.get("binding_kind") == "embedded"]
    asset_records = [item for item in binding_evidence if item.get("binding_kind") == "asset"]
    text_by_key = _unique_records(text_records, kind="binding_evidence.text", findings=findings)
    embedded_by_key = _unique_records(embedded_records, kind="binding_evidence.embedded", findings=findings)
    mutation_by_key = _unique_records(governed_mutations, kind="governed_mutations", findings=findings)
    for actual, expected, code, location in (
        (set(text_by_key), set(required_text), "QUERY_TEXT_COVERAGE_MISMATCH", "binding_evidence.text"),
        (set(embedded_by_key), set(required_governed), "QUERY_GOVERNED_BINDING_COVERAGE_MISMATCH", "binding_evidence.embedded"),
        (set(mutation_by_key), set(required_governed), "QUERY_GOVERNED_MUTATION_COVERAGE_MISMATCH", "governed_mutations"),
    ):
        if actual != expected:
            _finding(findings, code, location, f"missing={sorted(expected - actual)!r} extra={sorted(actual - expected)!r}")
    for key, expected_shape_id in text_slot_shape_ids.items():
        evidence = text_by_key.get(key)
        if evidence is not None and evidence.get("shape_id") != expected_shape_id:
            _finding(
                findings,
                "QUERY_TEXT_SHAPE_ID_MISMATCH",
                f"binding_evidence.text.{key}.shape_id",
                f"expected {expected_shape_id}, observed {evidence.get('shape_id')!r}",
            )
    for key, contract in governed_contracts.items():
        mutation = mutation_by_key.get(key)
        evidence = embedded_by_key.get(key)
        if mutation is None:
            continue
        for field in ("kind", "source_part", "locator", "peer_group_id"):
            expected = contract.get(field)
            reported = mutation.get(field)
            if reported != (expected or ""):
                _finding(
                    findings,
                    "QUERY_GOVERNED_MUTATION_CONTRACT_MISMATCH",
                    f"governed_mutations.{key}.{field}",
                    f"expected {(expected or '')!r}, observed {reported!r}",
                )
        expected_shape_id = governed_shape_ids[key]
        for record_kind, record in (("mutation", mutation), ("evidence", evidence)):
            if record is not None and record.get("shape_id") != expected_shape_id:
                _finding(
                    findings,
                    "QUERY_GOVERNED_SHAPE_ID_MISMATCH",
                    f"governed.{key}.{record_kind}.shape_id",
                    f"expected {expected_shape_id}, observed {record.get('shape_id')!r}",
                )

    asset_counts: dict[int, int] = {}
    asset_slots: set[tuple[int, str, str]] = set()
    selected_by_ordinal = {page.ordinal: page for page in selected_pages}
    for index, item in enumerate(asset_records):
        ordinal = item.get("ordinal")
        page_id = item.get("page_id")
        slot_id = item.get("slot_id")
        if type(ordinal) is not int or ordinal not in selected_by_ordinal:
            _finding(findings, "QUERY_ASSET_BINDING_PAGE_UNKNOWN", f"binding_evidence.asset.{index}", repr(ordinal))
            continue
        page = selected_by_ordinal[ordinal]
        if page_id != page.page_id or not isinstance(slot_id, str) or not slot_id:
            _finding(findings, "QUERY_ASSET_BINDING_KEY_INVALID", f"binding_evidence.asset.{index}", repr((ordinal, page_id, slot_id)))
            continue
        asset_key = (ordinal, page_id, slot_id)
        if asset_key in asset_slots:
            _finding(findings, "QUERY_ASSET_BINDING_KEY_DUPLICATE", f"binding_evidence.asset.{index}", repr(asset_key))
            continue
        asset_slots.add(asset_key)
        asset_counts[ordinal] = asset_counts.get(ordinal, 0) + 1
    for page in selected_pages:
        observed = asset_counts.get(page.ordinal, 0)
        if not page.minimum_asset_bindings <= observed <= page.maximum_asset_bindings:
            _finding(
                findings,
                "QUERY_ASSET_BINDING_COUNT_MISMATCH",
                f"binding_evidence.asset.ordinal.{page.ordinal}",
                f"expected {page.minimum_asset_bindings}..{page.maximum_asset_bindings}, observed {observed}",
            )

    fragment_group_contracts = {
        (group.ordinal, group.page_id, group.group_id): group.ordered_slot_ids
        for page in selected_pages
        for group in page.fragment_groups
    }
    authority = QueryCoverageAuthority(
        library_index_sha256=library_sha,
        selected_pages=tuple(sorted(selected_pages, key=lambda page: page.ordinal)),
        required_text_keys=required_text,
        required_governed_keys=required_governed,
        text_slot_shape_ids=dict(text_slot_shape_ids),
        fragment_group_contracts=fragment_group_contracts,
        governed_slot_shape_ids=dict(governed_shape_ids),
        governed_slot_contracts=dict(governed_contracts),
        certified_media_sha256=frozenset(certified_media),
    )
    return QueryCoverageResult(authority, _sorted_findings(findings))


def _normalise_fact_text(value: str) -> str:
    return "".join(value.split()).replace("％", "%")


def _fact_renderings(fact: Mapping[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    if isinstance(fact.get("text"), str):
        values.append(str(fact["text"]))
    if isinstance(fact.get("allowed_renderings"), list):
        values.extend(
            item for item in fact["allowed_renderings"] if isinstance(item, str)
        )
    value = fact.get("value")
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        scalar = str(value)
        values.extend((scalar, scalar + str(fact.get("unit") or "")))
    return tuple(dict.fromkeys(values))


def validate_fragment_group_fact_authority(
    authority: QueryCoverageAuthority,
    *,
    binding_evidence: Sequence[Mapping[str, Any]],
    actual_text_by_key: Mapping[tuple[int, str, str], str],
    facts_by_id: Mapping[str, Mapping[str, Any]],
    connectives_by_id: Mapping[str, str],
) -> FragmentGroupValidationResult:
    """Validate character fragments as complete, query-authoritative groups.

    The report supplies neither membership nor order.  Both are derived from
    the already hash-locked query bundle in ``authority``.  A group is
    authorized only when all of its non-empty one-character slots cite the
    same sole locked fact and their ordered concatenation is a complete
    registered rendering of that fact.  Empty remainder slots must be the
    exact locked ``connective-clear`` binding.
    """

    findings: list[ContractFinding] = []
    evidence_by_key: dict[tuple[int, str, str], Mapping[str, Any]] = {}
    for index, evidence in enumerate(binding_evidence):
        if not isinstance(evidence, Mapping) or evidence.get("binding_kind") != "text":
            continue
        key = (
            evidence.get("ordinal"),
            evidence.get("page_id"),
            evidence.get("slot_id"),
        )
        if (
            type(key[0]) is not int
            or not isinstance(key[1], str)
            or not isinstance(key[2], str)
        ):
            continue
        typed_key = (int(key[0]), key[1], key[2])
        if typed_key in evidence_by_key:
            _finding(
                findings,
                "FRAGMENT_GROUP_EVIDENCE_DUPLICATE",
                f"binding_evidence.{index}",
                repr(typed_key),
            )
            continue
        evidence_by_key[typed_key] = evidence

    governed_character_slots = {
        (ordinal, page_id, slot_id)
        for (ordinal, page_id, _), slot_ids in authority.fragment_group_contracts.items()
        for slot_id in slot_ids
    }
    for key, evidence in evidence_by_key.items():
        if evidence.get("mode") == "character" and key not in governed_character_slots:
            _finding(
                findings,
                "FACT_CHARACTER_OUTSIDE_FRAGMENT_GROUP",
                f"binding_evidence.{key}",
                "character mode is not present in a locked fragment group",
            )

    authorized: set[tuple[int, str, str]] = set()
    for group_key, ordered_slot_ids in sorted(
        authority.fragment_group_contracts.items()
    ):
        ordinal, page_id, group_id = group_key
        group_location = f"query_fragment_group.{ordinal}.{page_id}.{group_id}"
        finding_count_before = len(findings)
        nonempty: list[tuple[tuple[int, str, str], str, str]] = []
        for slot_id in ordered_slot_ids:
            key = (ordinal, page_id, slot_id)
            evidence = evidence_by_key.get(key)
            actual = actual_text_by_key.get(key)
            location = f"{group_location}.{slot_id}"
            if evidence is None or not isinstance(actual, str):
                _finding(
                    findings,
                    "FRAGMENT_GROUP_EVIDENCE_MISSING",
                    location,
                    repr(key),
                )
                continue
            expected_sha = hashlib.sha256(actual.encode("utf-8")).hexdigest()
            if evidence.get("replacement_sha256") != expected_sha:
                _finding(
                    findings,
                    "FRAGMENT_GROUP_OUTPUT_SHA256_MISMATCH",
                    location,
                    expected_sha,
                )
            fact_refs = evidence.get("fact_refs")
            connective_ref = evidence.get("connective_ref")
            asset_refs = evidence.get("asset_refs")
            if actual:
                if (
                    len(actual) != 1
                    or actual.isspace()
                    or evidence.get("mode") != "character"
                    or not isinstance(fact_refs, list)
                    or len(fact_refs) != 1
                    or not isinstance(fact_refs[0], str)
                    or not fact_refs[0]
                    or connective_ref not in {"", None}
                    or asset_refs not in ([], None)
                ):
                    _finding(
                        findings,
                        "FRAGMENT_GROUP_CHARACTER_INVALID",
                        location,
                        hashlib.sha256(actual.encode("utf-8")).hexdigest(),
                    )
                    continue
                nonempty.append((key, actual, fact_refs[0]))
            else:
                if (
                    evidence.get("mode") != "connective"
                    or fact_refs != []
                    or connective_ref != "connective-clear"
                    or connectives_by_id.get("connective-clear") != ""
                    or asset_refs not in ([], None)
                ):
                    _finding(
                        findings,
                        "FRAGMENT_GROUP_CLEAR_INVALID",
                        location,
                        repr(
                            {
                                "mode": evidence.get("mode"),
                                "fact_refs": fact_refs,
                                "connective_ref": connective_ref,
                            }
                        ),
                    )

        if nonempty:
            fact_refs = {fact_ref for _, _, fact_ref in nonempty}
            if len(fact_refs) != 1:
                _finding(
                    findings,
                    "FRAGMENT_GROUP_FACT_REF_DRIFT",
                    group_location,
                    repr(sorted(fact_refs)),
                )
            else:
                fact_ref = next(iter(fact_refs))
                fact = facts_by_id.get(fact_ref)
                if not isinstance(fact, Mapping) or fact.get("status", "active") != "active":
                    _finding(
                        findings,
                        "FRAGMENT_GROUP_FACT_REF_UNKNOWN",
                        group_location,
                        fact_ref,
                    )
                else:
                    assembled = "".join(character for _, character, _ in nonempty)
                    if not any(
                        assembled == rendering
                        or "".join(assembled.split())
                        == "".join(rendering.split())
                        for rendering in _fact_renderings(fact)
                    ):
                        _finding(
                            findings,
                            "FRAGMENT_GROUP_RENDERING_MISMATCH",
                            group_location,
                            hashlib.sha256(assembled.encode("utf-8")).hexdigest(),
                        )
        if len(findings) == finding_count_before:
            authorized.update(key for key, _, _ in nonempty)

    return FragmentGroupValidationResult(
        authorized_character_keys=frozenset(authorized),
        findings=_sorted_findings(findings),
    )


def _numeric_literal(value: str) -> tuple[Decimal, bool] | None:
    compact = _normalise_fact_text(value)
    match = NUMERIC_RE.fullmatch(compact)
    if match is None:
        return None
    is_percent = bool(match.group(1))
    if is_percent:
        compact = compact[:-1]
    compact = compact.replace(",", "")
    try:
        return Decimal(compact), is_percent
    except InvalidOperation:
        return None


def _numeric_tokens(value: str) -> tuple[str, ...]:
    """Extract complete numeric tokens from one registered fact rendering.

    The actual governed value must still be a complete numeric literal.  Token
    extraction is restricted to immutable FactStore renderings and rejects
    fragments of malformed comma/decimal sequences or alphanumeric IDs.
    """

    tokens: list[str] = []
    for match in NUMERIC_TOKEN_RE.finditer(value):
        start, end = match.span()
        if (
            start >= 2
            and value[start - 1] in {",", "."}
            and value[start - 2].isdigit()
        ):
            continue
        if (
            end + 1 < len(value)
            and value[end] in {",", "."}
            and value[end + 1].isdigit()
        ):
            continue
        token = match.group(0)
        if _numeric_literal(token) is not None:
            tokens.append(token)
    return tuple(dict.fromkeys(tokens))


def _numeric_rendering_matches(
    source: str,
    candidate: str,
    *,
    allow_percent_scale: bool,
) -> bool:
    """Match one governed literal to an authoritative numeric rendering.

    This is an independent implementation of the producer contract: percent
    and decimal forms may be equivalent only for a percent-aware fact, and
    native chart/workbook caches may round to the precision explicitly present
    in the governed source literal.
    """

    source_number = _numeric_literal(source)
    candidate_number = _numeric_literal(candidate)
    if source_number is None or candidate_number is None:
        return False
    source_value, source_percent = source_number
    candidate_value, candidate_percent = candidate_number
    if source_percent != candidate_percent:
        if not allow_percent_scale:
            return False
        if source_percent:
            candidate_value *= Decimal(100)
        else:
            source_value *= Decimal(100)
    if abs(source_value - candidate_value) <= Decimal("0.000000000001"):
        return True

    compact_source = _normalise_fact_text(source).replace(",", "").rstrip("%")
    decimal_places = (
        len(compact_source.split(".", 1)[1]) if "." in compact_source else 0
    )
    quantum = Decimal(1).scaleb(-decimal_places)
    try:
        return source_value == candidate_value.quantize(quantum)
    except InvalidOperation:
        return False


def _fact_numeric_candidates(
    fact: Mapping[str, Any],
    *,
    scalar_only: bool,
) -> tuple[str, ...]:
    """Return numeric candidates governed by immutable FactStore fields."""

    values: list[str] = []
    value = fact.get("value")
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        scalar = str(value)
        values.extend((scalar, scalar + str(fact.get("unit") or "")))
    if not scalar_only:
        for rendering in _fact_renderings(fact):
            values.extend(_numeric_tokens(rendering))
    return tuple(dict.fromkeys(values))


def _fact_allows_percent_scale(fact: Mapping[str, Any]) -> bool:
    return fact.get("unit") == "%" or any(
        "%" in rendering or "％" in rendering
        for rendering in _fact_renderings(fact)
    )


def _matching_numeric_fact_refs(
    actual: str,
    *,
    facts_by_id: Mapping[str, Mapping[str, Any]],
    scalar_only: bool,
) -> frozenset[str]:
    """Recompute numeric authority across all active facts, fail-closed."""

    if _numeric_literal(actual) is None:
        return frozenset()
    matches: set[str] = set()
    for fact_ref, fact in facts_by_id.items():
        if (
            not isinstance(fact_ref, str)
            or not isinstance(fact, Mapping)
            or fact.get("status", "active") != "active"
        ):
            continue
        if any(
            _numeric_rendering_matches(
                actual,
                candidate,
                allow_percent_scale=_fact_allows_percent_scale(fact),
            )
            for candidate in _fact_numeric_candidates(
                fact,
                scalar_only=scalar_only,
            )
        ):
            matches.add(fact_ref)
    return frozenset(matches)


def _joined_rendering_matches(
    actual: str,
    rendering_sets: Sequence[Sequence[str]],
) -> bool:
    """Match a complete multi-fact rendering without a Cartesian explosion."""

    if len(rendering_sets) < 2 or any(not values for values in rendering_sets):
        return False

    def exact_for(
        target: str,
        choices: Sequence[Sequence[str]],
        separator: str,
    ) -> bool:
        positions = {0}
        for index, renderings in enumerate(choices):
            next_positions: set[int] = set()
            prefix = "" if index == 0 else separator
            for position in positions:
                for rendering in renderings:
                    token = prefix + rendering
                    if target.startswith(token, position):
                        next_positions.add(position + len(token))
            positions = next_positions
            if not positions:
                return False
        return len(target) in positions

    compact_sets = tuple(
        tuple(dict.fromkeys(_normalise_fact_text(value) for value in values))
        for values in rendering_sets
    )
    compact_actual = _normalise_fact_text(actual)
    for separator in SAFE_JOIN_SEPARATORS:
        if exact_for(actual, rendering_sets, separator):
            return True
        if exact_for(
            compact_actual,
            compact_sets,
            _normalise_fact_text(separator),
        ):
            return True
    return False


def validate_fact_evidence_value(
    actual: str,
    *,
    evidence_mode: str,
    fact_refs: Sequence[str],
    facts_by_id: Mapping[str, Mapping[str, Any]],
    render_contract: Mapping[str, Any] | None = None,
    location: str = "binding_evidence",
) -> tuple[ContractFinding, ...]:
    """Authorize a fact-backed value under a closed rendering vocabulary.

    ``slice`` deliberately requires an external render contract containing the
    source field and exact bounds.  The report's mode string alone is not an
    authority.  Character and arbitrary substring modes are intentionally not
    accepted.
    """

    findings: list[ContractFinding] = []
    if evidence_mode not in SAFE_FACT_MODES:
        _finding(findings, "FACT_EVIDENCE_MODE_FORBIDDEN", f"{location}.mode", evidence_mode)
        return _sorted_findings(findings)
    if len(fact_refs) != len(set(fact_refs)) or not fact_refs:
        _finding(findings, "FACT_EVIDENCE_REFS_INVALID", f"{location}.fact_refs", repr(list(fact_refs)))
        return _sorted_findings(findings)
    facts: list[Mapping[str, Any]] = []
    for ref in fact_refs:
        fact = facts_by_id.get(ref)
        if not isinstance(fact, Mapping) or fact.get("status", "active") != "active":
            _finding(findings, "FACT_EVIDENCE_REF_UNKNOWN", f"{location}.fact_refs", ref)
        else:
            facts.append(fact)
    if findings:
        return _sorted_findings(findings)

    if evidence_mode in EXACT_FACT_MODES:
        if len(facts) != 1 or actual not in _fact_renderings(facts[0]):
            _finding(findings, "FACT_EXACT_RENDERING_MISMATCH", location, hashlib.sha256(actual.encode()).hexdigest())
    elif evidence_mode in NORMALIZED_FACT_MODES:
        if evidence_mode == "normalized-year":
            fact = facts[0] if len(facts) == 1 else {}
            value = fact.get("value")
            allowed = {str(value), f"{value}年"} if value is not None else set()
            matches = len(facts) == 1 and actual in allowed
        else:
            matches = len(facts) == 1 and any(
                _normalise_fact_text(actual) == _normalise_fact_text(rendering)
                for rendering in _fact_renderings(facts[0])
            )
        if not matches:
            _finding(findings, "FACT_NORMALIZED_RENDERING_MISMATCH", location, hashlib.sha256(actual.encode()).hexdigest())
    elif evidence_mode in NUMERIC_FACT_MODES:
        matching_refs = _matching_numeric_fact_refs(
            actual,
            facts_by_id=facts_by_id,
            scalar_only=evidence_mode == "source-numeric-scalar",
        )
        expected_refs = frozenset(fact_refs)
        if len(matching_refs) > 1:
            _finding(
                findings,
                "FACT_NUMERIC_AUTHORITY_AMBIGUOUS",
                location,
                repr(sorted(matching_refs)),
            )
        elif len(facts) != 1 or matching_refs != expected_refs:
            _finding(findings, "FACT_NUMERIC_RENDERING_MISMATCH", location, hashlib.sha256(actual.encode()).hexdigest())
    elif evidence_mode in JOIN_FACT_MODES:
        rendering_sets = [_fact_renderings(fact) for fact in facts]
        if len(facts) < 2 or not _joined_rendering_matches(actual, rendering_sets):
            _finding(
                findings,
                "FACT_JOIN_RENDERING_MISMATCH",
                location,
                hashlib.sha256(actual.encode()).hexdigest(),
            )
    else:
        contract = render_contract if isinstance(render_contract, Mapping) else {}
        field = contract.get("field")
        start = contract.get("slice_start")
        end = contract.get("slice_end")
        contract_ref = contract.get("fact_ref")
        if (
            len(facts) != 1
            or contract_ref != fact_refs[0]
            or field not in {"text", "value", "value_unit"}
            or type(start) is not int
            or type(end) is not int
            or start < 0
            or end <= start
        ):
            _finding(findings, "FACT_SLICE_CONTRACT_INVALID", location, repr(render_contract))
        else:
            fact = facts[0]
            if field == "text":
                canonical = fact.get("text")
            else:
                value = fact.get("value")
                canonical = None if value is None else str(value)
                if canonical is not None and field == "value_unit":
                    canonical += str(fact.get("unit") or "")
            if not isinstance(canonical, str) or end > len(canonical) or actual != canonical[start:end]:
                _finding(findings, "FACT_SLICE_RENDERING_MISMATCH", location, hashlib.sha256(actual.encode()).hexdigest())
    return _sorted_findings(findings)


def audit_zip_resources(
    archive: zipfile.ZipFile,
    *,
    limits: ZipResourceLimits = PPTX_ZIP_RESOURCE_LIMITS,
) -> tuple[ContractFinding, ...]:
    """Reject ZIP bombs and oversized parser inputs without reading members."""

    limits.validate()
    findings: list[ContractFinding] = []
    infos = archive.infolist()
    if len(infos) > limits.max_entries:
        _finding(
            findings,
            "ZIP_RESOURCE_ENTRY_COUNT_EXCEEDED",
            "package.entries",
            f"observed={len(infos)} limit={limits.max_entries}",
        )

    total_uncompressed = 0
    for index, info in enumerate(infos):
        location = f"package.entries.{index}"
        size = int(info.file_size)
        compressed_size = int(info.compress_size)
        total_uncompressed += size
        if size > limits.max_entry_uncompressed_bytes:
            _finding(
                findings,
                "ZIP_RESOURCE_ENTRY_SIZE_EXCEEDED",
                location,
                (
                    f"{info.filename}: observed={size} "
                    f"limit={limits.max_entry_uncompressed_bytes}"
                ),
            )
        lower_name = info.filename.casefold()
        if (
            lower_name.endswith(".rels")
            and size > limits.max_relationship_uncompressed_bytes
        ):
            _finding(
                findings,
                "ZIP_RESOURCE_RELATIONSHIP_SIZE_EXCEEDED",
                location,
                (
                    f"{info.filename}: observed={size} "
                    f"limit={limits.max_relationship_uncompressed_bytes}"
                ),
            )
        elif (
            lower_name.endswith(".xml")
            and size > limits.max_xml_uncompressed_bytes
        ):
            _finding(
                findings,
                "ZIP_RESOURCE_XML_SIZE_EXCEEDED",
                location,
                (
                    f"{info.filename}: observed={size} "
                    f"limit={limits.max_xml_uncompressed_bytes}"
                ),
            )
        if size:
            if compressed_size <= 0:
                ratio_detail = "infinite"
                ratio_exceeded = True
            else:
                ratio = size / compressed_size
                ratio_detail = f"{ratio:.6f}"
                ratio_exceeded = ratio > float(limits.max_compression_ratio)
            if ratio_exceeded:
                _finding(
                    findings,
                    "ZIP_RESOURCE_COMPRESSION_RATIO_EXCEEDED",
                    location,
                    (
                        f"{info.filename}: observed={ratio_detail} "
                        f"limit={float(limits.max_compression_ratio):.6f}"
                    ),
                )
    if total_uncompressed > limits.max_total_uncompressed_bytes:
        _finding(
            findings,
            "ZIP_RESOURCE_TOTAL_SIZE_EXCEEDED",
            "package.entries",
            (
                f"observed={total_uncompressed} "
                f"limit={limits.max_total_uncompressed_bytes}"
            ),
        )
    return _sorted_findings(findings)


def audit_zip_entries(
    archive: zipfile.ZipFile,
    *,
    limits: ZipResourceLimits = PPTX_ZIP_RESOURCE_LIMITS,
) -> ZipEntryAudit:
    """Reject resource abuse and ambiguous or active ZIP entries."""

    findings: list[ContractFinding] = list(
        audit_zip_resources(archive, limits=limits)
    )
    canonical_names: list[str] = []
    exact_seen: set[str] = set()
    portable_seen: dict[str, str] = {}
    for index, info in enumerate(archive.infolist()):
        name = info.filename
        location = f"package.entries.{index}"
        if name in exact_seen:
            _finding(findings, "ZIP_ENTRY_DUPLICATE", location, name)
        exact_seen.add(name)
        if info.is_dir() or name.endswith("/"):
            _finding(findings, "ZIP_DIRECTORY_ENTRY_FORBIDDEN", location, name)
            continue
        if not name or name.startswith(("/", "\\")) or "\\" in name:
            _finding(findings, "ZIP_ENTRY_NAME_NONCANONICAL", location, name)
            continue
        if any(ord(character) < 32 for character in name):
            _finding(findings, "ZIP_ENTRY_NAME_NONCANONICAL", location, repr(name))
            continue
        if unicodedata.normalize("NFC", name) != name:
            _finding(findings, "ZIP_ENTRY_NAME_UNICODE_NONCANONICAL", location, name)
            continue
        parts = name.split("/")
        if any(part in {"", ".", ".."} for part in parts) or posixpath.normpath(name) != name:
            _finding(findings, "ZIP_ENTRY_NAME_NONCANONICAL", location, name)
            continue
        portable_key = name.casefold()
        previous = portable_seen.get(portable_key)
        if previous is not None and previous != name:
            _finding(findings, "ZIP_ENTRY_PORTABLE_COLLISION", location, f"{previous} vs {name}")
            continue
        portable_seen[portable_key] = name
        mode = (info.external_attr >> 16) & 0o170000
        if mode == stat.S_IFLNK:
            _finding(findings, "ZIP_ENTRY_SYMLINK_FORBIDDEN", location, name)
            continue
        if info.flag_bits & 0x1:
            _finding(findings, "ZIP_ENTRY_ENCRYPTED_FORBIDDEN", location, name)
            continue
        canonical_names.append(name)
    return ZipEntryAudit(tuple(sorted(canonical_names)), _sorted_findings(findings))


def audit_zip_package(
    path: str | os.PathLike[str],
    *,
    limits: ZipResourceLimits = PPTX_ZIP_RESOURCE_LIMITS,
) -> ZipEntryAudit:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            return audit_zip_entries(archive, limits=limits)
    except (OSError, zipfile.BadZipFile) as exc:
        return ZipEntryAudit(
            (),
            (ContractFinding("ZIP_PACKAGE_INVALID", "package", str(exc)),),
        )


def validate_external_relationship(
    entry: Mapping[str, str],
    *,
    location: str = "relationship",
) -> tuple[ContractFinding, ...]:
    """Allow only explicit HTTPS hyperlink relationships as external targets."""

    findings: list[ContractFinding] = []
    rel_type = str(entry.get("Type", "")).rstrip("/").lower()
    target_mode = entry.get("TargetMode", "")
    target = entry.get("Target", "")
    if target_mode != "External":
        _finding(findings, "EXTERNAL_RELATIONSHIP_MODE_INVALID", location, str(target_mode))
        return _sorted_findings(findings)
    if rel_type not in ALLOWED_EXTERNAL_RELATIONSHIP_TYPES:
        _finding(findings, "EXTERNAL_RELATIONSHIP_TYPE_FORBIDDEN", location, rel_type)
    try:
        parsed = urlsplit(target)
    except ValueError as exc:
        _finding(findings, "EXTERNAL_RELATIONSHIP_TARGET_INVALID", location, str(exc))
        return _sorted_findings(findings)
    decoded = unquote(target)
    if (
        parsed.scheme.lower() != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or target != target.strip()
        or "\\" in target
        or any(ord(character) < 32 for character in decoded)
    ):
        _finding(findings, "EXTERNAL_RELATIONSHIP_TARGET_INVALID", location, target)
    return _sorted_findings(findings)


def _non_visual_shape_id(element: Any) -> int | None:
    markers = list(element.iter(f"{{{PRESENTATION_NS}}}cNvPr"))
    if len(markers) != 1:
        return None
    raw = markers[0].get("id", "")
    return int(raw) if raw.isdigit() and int(raw) > 0 else None


def audit_output_text_coverage(
    package: str | os.PathLike[str] | bytes,
    *,
    authority: QueryCoverageAuthority,
) -> tuple[ContractFinding, ...]:
    """Reject nonempty slide text outside query-authoritative native shapes.

    The audit intentionally covers ordinary ``p:sp`` leaves (including leaves
    nested under ``p:grpSp``) and native table ``p:graphicFrame`` objects.  Text
    cached in chart parts remains governed by the exact mutation contracts.
    """

    findings: list[ContractFinding] = []
    text_shapes_by_ordinal: dict[int, set[int]] = {}
    for (ordinal, _page_id, _slot_id), shape_id in authority.text_slot_shape_ids.items():
        text_shapes_by_ordinal.setdefault(ordinal, set()).add(shape_id)
    table_shapes_by_ordinal: dict[int, set[int]] = {}
    for key, contract in authority.governed_slot_contracts.items():
        if contract.get("kind") != "table-cell":
            continue
        shape_id = authority.governed_slot_shape_ids.get(key, 0)
        if shape_id > 0:
            table_shapes_by_ordinal.setdefault(key[0], set()).add(shape_id)

    try:
        stream: Any = io.BytesIO(package) if isinstance(package, bytes) else package
        with zipfile.ZipFile(stream, "r") as archive:
            entry_audit = audit_zip_entries(archive)
            findings.extend(entry_audit.findings)
            if entry_audit.status != "pass":
                return _sorted_findings(findings)
            canonical = set(entry_audit.canonical_names)
            for page in authority.selected_pages:
                slide_part = f"ppt/slides/slide{page.ordinal}.xml"
                if slide_part not in canonical:
                    _finding(
                        findings,
                        "OUTPUT_TEXT_SLIDE_MISSING",
                        f"package!/{slide_part}",
                        page.page_id,
                    )
                    continue
                try:
                    root = ET.fromstring(archive.read(slide_part))
                except (KeyError, ET.ParseError) as exc:
                    _finding(
                        findings,
                        "OUTPUT_TEXT_SLIDE_XML_INVALID",
                        f"package!/{slide_part}",
                        str(exc),
                    )
                    continue
                allowed_text_shapes = text_shapes_by_ordinal.get(page.ordinal, set())
                seen_nonempty_text_shapes: set[int] = set()
                for shape in root.iter(f"{{{PRESENTATION_NS}}}sp"):
                    text = "".join(
                        node.text or ""
                        for node in shape.iter(f"{{{DRAWING_NS}}}t")
                    )
                    if not text.strip():
                        continue
                    shape_id = _non_visual_shape_id(shape)
                    if shape_id is None:
                        _finding(
                            findings,
                            "OUTPUT_TEXT_SHAPE_ID_INVALID",
                            f"package!/{slide_part}",
                            hashlib.sha256(text.encode()).hexdigest(),
                        )
                        continue
                    if shape_id in seen_nonempty_text_shapes:
                        _finding(
                            findings,
                            "OUTPUT_TEXT_SHAPE_ID_DUPLICATE",
                            f"package!/{slide_part}#shape-{shape_id}",
                            "duplicate nonempty p:sp shape id",
                        )
                    seen_nonempty_text_shapes.add(shape_id)
                    if shape_id not in allowed_text_shapes:
                        _finding(
                            findings,
                            "OUTPUT_TEXT_SHAPE_UNAUTHORIZED",
                            f"package!/{slide_part}#shape-{shape_id}",
                            hashlib.sha256(text.encode()).hexdigest(),
                        )

                allowed_table_shapes = table_shapes_by_ordinal.get(page.ordinal, set())
                for frame in root.iter(f"{{{PRESENTATION_NS}}}graphicFrame"):
                    tables = list(frame.iter(f"{{{DRAWING_NS}}}tbl"))
                    if not tables:
                        continue
                    text = "".join(
                        node.text or ""
                        for table in tables
                        for node in table.iter(f"{{{DRAWING_NS}}}t")
                    )
                    if not text.strip():
                        continue
                    shape_id = _non_visual_shape_id(frame)
                    if shape_id is None or shape_id not in allowed_table_shapes:
                        identity = shape_id if shape_id is not None else "invalid"
                        _finding(
                            findings,
                            "OUTPUT_TABLE_TEXT_SHAPE_UNAUTHORIZED",
                            f"package!/{slide_part}#shape-{identity}",
                            hashlib.sha256(text.encode()).hexdigest(),
                        )
    except (OSError, zipfile.BadZipFile) as exc:
        _finding(findings, "ZIP_PACKAGE_INVALID", "package", str(exc))
    return _sorted_findings(findings)


def audit_output_media_authority(
    package: str | os.PathLike[str] | bytes,
    *,
    authority: QueryCoverageAuthority,
    asset_sha256_by_ref: Mapping[str, str],
    binding_evidence: Sequence[Mapping[str, Any]],
) -> tuple[ContractFinding, ...]:
    """Require every final PPT media byte stream to have locked provenance."""

    findings: list[ContractFinding] = []
    asset_hashes: set[str] = set()
    for index, item in enumerate(binding_evidence):
        if item.get("binding_kind") != "asset":
            continue
        refs = item.get("asset_refs")
        location = f"binding_evidence.asset.{index}"
        if not isinstance(refs, list) or len(refs) != 1:
            _finding(findings, "MEDIA_ASSET_REF_INVALID", location, repr(refs))
            continue
        expected = asset_sha256_by_ref.get(refs[0])
        if expected is None or item.get("replacement_sha256") != expected:
            _finding(findings, "MEDIA_ASSET_SHA256_UNAUTHORIZED", location, str(refs[0]))
            continue
        asset_hashes.add(expected)
    allowed_hashes = set(authority.certified_media_sha256) | asset_hashes

    try:
        stream: Any = io.BytesIO(package) if isinstance(package, bytes) else package
        with zipfile.ZipFile(stream, "r") as archive:
            entry_audit = audit_zip_entries(archive)
            findings.extend(entry_audit.findings)
            if entry_audit.status != "pass":
                return _sorted_findings(findings)
            actual_hashes: set[str] = set()
            for info in archive.infolist():
                name = info.filename
                if name not in entry_audit.canonical_names:
                    continue
                normalised = name.replace("\\", "/")
                if not normalised.startswith("ppt/") or "/media/" not in normalised:
                    continue
                digest = hashlib.sha256(archive.read(info)).hexdigest()
                actual_hashes.add(digest)
                if digest not in allowed_hashes:
                    _finding(findings, "OUTPUT_MEDIA_SHA256_UNAUTHORIZED", f"package!/{name}", digest)
            for digest in sorted(asset_hashes - actual_hashes):
                _finding(findings, "OUTPUT_ASSET_MEDIA_MISSING", "package.media", digest)
    except (OSError, zipfile.BadZipFile) as exc:
        _finding(findings, "ZIP_PACKAGE_INVALID", "package", str(exc))
    return _sorted_findings(findings)


__all__ = [
    "ALLOWED_EXTERNAL_RELATIONSHIP_TYPES",
    "ContractFinding",
    "QueryCoverageAuthority",
    "QueryCoverageResult",
    "SelectedPageAuthority",
    "ZipEntryAudit",
    "ZipResourceLimits",
    "PPTX_ZIP_RESOURCE_LIMITS",
    "audit_output_media_authority",
    "audit_output_text_coverage",
    "audit_zip_entries",
    "audit_zip_package",
    "audit_zip_resources",
    "validate_external_relationship",
    "validate_fact_evidence_value",
    "validate_query_bundle_and_coverage",
]
