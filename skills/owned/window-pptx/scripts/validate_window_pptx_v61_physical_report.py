#!/usr/bin/env python3
"""Independently validate a Window-PPTX v6.1 physical assembly report.

The report schema constrains local values.  This validator additionally binds
the report to the named PPTX and authority files, then recomputes cross-field
counts and uniqueness properties that JSON Schema cannot express reliably.
It is read-only and emits one deterministic JSON result to stdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import posixpath
import re
import stat
import sys
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from window_pptx.workbook_security import (
    WorkbookSecurityError,
    audit_governed_xlsx,
    read_governed_xlsx_slot,
)
from window_pptx.independent_validation_security import (
    QueryCoverageAuthority,
    audit_output_media_authority,
    audit_output_text_coverage,
    audit_zip_entries,
    validate_external_relationship,
    validate_fact_evidence_value,
    validate_fragment_group_fact_authority,
    validate_query_bundle_and_coverage,
)
from window_pptx.presentation_topology import inspect_presentation_topology
from urllib.parse import unquote


SCHEMA_VERSION = "1.0"
VALIDATOR_ID = "window-pptx-v61-physical-report-validator"
SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "physical-assembly-report.v1.schema.json"
)
FACT_STORE_SCHEMA_PATH = SCHEMA_PATH.with_name("fact-store.v1.schema.json")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
TABLE_CONTENT_LOCATOR_RE = re.compile(
    r"^graphicFrame\[id=(\d+)\]/table\[(\d+)\]/row\[(\d+)\]/cell\[(\d+)\]$"
)
FRAME_PREFIX_RE = re.compile(r"^(?:graphicFrame|chartFrame)\[id=(\d+)\]")
PACKAGE_RELATIONSHIP_NS = (
    "http://schemas.openxmlformats.org/package/2006/relationships"
)
RELATIONSHIPS_TAG = f"{{{PACKAGE_RELATIONSHIP_NS}}}Relationships"
RELATIONSHIP_TAG = f"{{{PACKAGE_RELATIONSHIP_NS}}}Relationship"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CONTENT_TYPES_TAG = f"{{{CONTENT_TYPES_NS}}}Types"
CONTENT_TYPE_DEFAULT_TAG = f"{{{CONTENT_TYPES_NS}}}Default"
CONTENT_TYPE_OVERRIDE_TAG = f"{{{CONTENT_TYPES_NS}}}Override"
PRESENTATION_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
)
SLIDE_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
)
PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
OFFICE_RELATIONSHIP_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
RELATIONSHIP_ID_ATTR = f"{{{OFFICE_RELATIONSHIP_NS}}}id"
URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
FORBIDDEN_RELATIONSHIP_TYPE_FRAGMENTS = (
    "oleobject",
    "vbaproject",
    "activex",
    "attachedtemplate",
    "externalworkbookpath",
    "javascript",
    "vbscript",
    "macro",
)
FORBIDDEN_RELATIONSHIP_TARGET_SUFFIXES = (
    ".exe",
    ".bat",
    ".cmd",
    ".scr",
    ".vbs",
    ".js",
    ".com",
    ".dll",
    ".msi",
    ".bin",
    ".ps1",
    ".jar",
    ".sh",
    ".py",
    ".hta",
    ".wsf",
    ".pptm",
    ".potm",
    ".ppsm",
    ".ppam",
    ".xlsm",
    ".xltm",
    ".xlam",
    ".docm",
    ".dotm",
)
PHASE49_LIBRARY_INDEX_SHA256 = (
    "dda45d2ad1e32dab5c3aa6d39b1ab8671d71cc380eca6a0ff7d06ad9b0f96ff6"
)
PHASE49_GOVERNED_INVENTORY_SHA256 = (
    "12ce0f96e70c84c07d3b70ec9f4a4385949ffc05981ef983ed09648c282353c2"
)
GOVERNED_IDENTITY_FIELDS = (
    "ordinal",
    "page_id",
    "slot_id",
    "kind",
    "source_part",
    "locator",
    "peer_group_id",
)


def _owner_part_from_rels_path(rels_path: str) -> str | None:
    normalised = rels_path.replace("\\", "/").lstrip("/")
    if normalised == "_rels/.rels":
        return None
    parts = normalised.split("/")
    if len(parts) < 2 or parts[-2] != "_rels" or not parts[-1].endswith(".rels"):
        return None
    return "/".join(parts[:-2] + [parts[-1][:-5]])


def _resolve_relationship_target(rels_path: str, target: str) -> str | None:
    if not target or any(ord(character) < 32 for character in target):
        return None
    decoded = unquote(target.split("#", 1)[0])
    if (
        not decoded
        or "\\" in decoded
        or decoded.startswith("//")
        or URI_SCHEME_RE.match(decoded)
    ):
        return None
    owner = _owner_part_from_rels_path(rels_path)
    base = posixpath.dirname(owner) if owner else ""
    if decoded.startswith("/"):
        return decoded.lstrip("/")
    resolved = posixpath.normpath(posixpath.join(base, decoded)).lstrip("/")
    if resolved == ".." or resolved.startswith("../"):
        return None
    return resolved


def _local_locator_element(root: ET.Element, locator: str) -> ET.Element:
    segments = re.findall(r"([^/\[]+)\[(\d+)\]", locator)
    if not segments:
        raise ValueError("empty governed locator")
    root_name, root_ordinal = segments[0]
    if root_ordinal != "1" or root.tag.rsplit("}", 1)[-1] != root_name:
        raise ValueError("governed locator root mismatch")
    current = root
    for local_name, raw_ordinal in segments[1:]:
        children = [
            child
            for child in list(current)
            if child.tag.rsplit("}", 1)[-1] == local_name
        ]
        ordinal = int(raw_ordinal)
        if ordinal < 1 or ordinal > len(children):
            raise ValueError("governed locator not found")
        current = children[ordinal - 1]
    return current


def _read_governed_xml_value(
    part_bytes: bytes,
    *,
    kind: str,
    locator: str,
) -> str:
    root = ET.fromstring(part_bytes)
    if kind == "table-cell":
        match = TABLE_CONTENT_LOCATOR_RE.fullmatch(locator)
        if match is None:
            raise ValueError("governed table locator invalid")
        shape_id, table_ordinal, row_ordinal, column_ordinal = map(
            int, match.groups()
        )
        frames = []
        for frame in root.iter():
            if frame.tag.rsplit("}", 1)[-1] != "graphicFrame":
                continue
            marker = next(
                (
                    node
                    for node in frame.iter()
                    if node.tag.rsplit("}", 1)[-1] == "cNvPr"
                    and node.attrib.get("id") == str(shape_id)
                ),
                None,
            )
            if marker is not None:
                frames.append(frame)
        if len(frames) != 1:
            raise ValueError("governed table frame not found")
        tables = [
            node
            for node in frames[0].iter()
            if node.tag.rsplit("}", 1)[-1] == "tbl"
        ]
        if not 1 <= table_ordinal <= len(tables):
            raise ValueError("governed table not found")
        rows = [
            node
            for node in list(tables[table_ordinal - 1])
            if node.tag.rsplit("}", 1)[-1] == "tr"
        ]
        if not 1 <= row_ordinal <= len(rows):
            raise ValueError("governed table row not found")
        cells = [
            node
            for node in list(rows[row_ordinal - 1])
            if node.tag.rsplit("}", 1)[-1] == "tc"
        ]
        if not 1 <= column_ordinal <= len(cells):
            raise ValueError("governed table cell not found")
        return "".join(
            node.text or ""
            for node in cells[column_ordinal - 1].iter()
            if node.tag.rsplit("}", 1)[-1] == "t"
        ).strip()
    generic_locator = FRAME_PREFIX_RE.sub("", locator, count=1)
    owner = _local_locator_element(root, generic_locator)
    return (owner.text or "").strip()


def _relationship_by_id(
    archive: zipfile.ZipFile,
    owner_part: str,
    relationship_id: str,
) -> tuple[str, str]:
    """Resolve one exact internal relationship without trusting report data."""

    rels_path = _rels_path_for_part(owner_part)
    try:
        root = ET.fromstring(archive.read(rels_path))
    except (KeyError, ET.ParseError) as exc:
        raise ValueError(f"relationship part unavailable: {rels_path}") from exc
    if root.tag != RELATIONSHIPS_TAG:
        raise ValueError(f"relationship namespace invalid: {rels_path}")
    matches = [
        node
        for node in list(root)
        if node.tag == RELATIONSHIP_TAG
        and node.attrib.get("Id") == relationship_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"relationship id is not unique: {owner_part}#{relationship_id}"
        )
    relation = matches[0]
    if relation.attrib.get("TargetMode", "").lower() == "external":
        raise ValueError(f"governed relationship is external: {relationship_id}")
    target = _resolve_relationship_target(rels_path, relation.attrib.get("Target", ""))
    if target is None or target not in archive.namelist():
        raise ValueError(f"governed relationship target missing: {relationship_id}")
    return relation.attrib.get("Type", ""), target


def _actual_governed_target(
    archive: zipfile.ZipFile,
    *,
    ordinal: int,
    kind: str,
    locator: str,
) -> dict[str, Any]:
    """Follow the final slide XML and relationships to the governed part."""

    match = FRAME_PREFIX_RE.match(locator)
    if match is None:
        raise ValueError("governed locator has no frame identity")
    shape_id = int(match.group(1))
    slide_part = f"ppt/slides/slide{ordinal}.xml"
    try:
        slide_root = ET.fromstring(archive.read(slide_part))
    except (KeyError, ET.ParseError) as exc:
        raise ValueError(f"governed slide unavailable: {slide_part}") from exc
    frames: list[ET.Element] = []
    for frame in slide_root.iter(f"{{{PRESENTATION_NS}}}graphicFrame"):
        marker = frame.find(f".//{{{PRESENTATION_NS}}}cNvPr")
        if marker is not None and marker.attrib.get("id") == str(shape_id):
            frames.append(frame)
    if len(frames) != 1:
        raise ValueError(f"governed frame is not unique: {slide_part}#{shape_id}")
    frame = frames[0]
    if kind == "table-cell":
        if len(list(frame.iter(f"{{{DRAWING_NS}}}tbl"))) != 1:
            raise ValueError("governed table frame is invalid")
        return {
            "shape_id": shape_id,
            "slide_part": slide_part,
            "slide_relationship_id": "",
            "chart_part": "",
            "chart_relationship_id": "",
            "target_part": slide_part,
            "target_part_sha256": hashlib.sha256(
                archive.read(slide_part)
            ).hexdigest(),
        }

    charts = list(frame.iter(f"{{{CHART_NS}}}chart"))
    if len(charts) != 1:
        raise ValueError("governed chart frame is invalid")
    slide_relationship_id = charts[0].attrib.get(RELATIONSHIP_ID_ATTR, "")
    if not slide_relationship_id:
        raise ValueError("governed chart relationship id is missing")
    slide_rel_type, chart_part = _relationship_by_id(
        archive,
        slide_part,
        slide_relationship_id,
    )
    if not slide_rel_type.lower().rstrip("/").endswith("/chart"):
        raise ValueError("governed slide relationship is not a chart")
    if kind != "workbook-cell":
        return {
            "shape_id": shape_id,
            "slide_part": slide_part,
            "slide_relationship_id": slide_relationship_id,
            "chart_part": chart_part,
            "chart_relationship_id": "",
            "target_part": chart_part,
            "target_part_sha256": hashlib.sha256(
                archive.read(chart_part)
            ).hexdigest(),
        }

    try:
        chart_root = ET.fromstring(archive.read(chart_part))
    except (KeyError, ET.ParseError) as exc:
        raise ValueError(f"governed chart unavailable: {chart_part}") from exc
    external_data = list(chart_root.iter(f"{{{CHART_NS}}}externalData"))
    if len(external_data) != 1:
        raise ValueError("governed chart externalData is not unique")
    chart_relationship_id = external_data[0].attrib.get(RELATIONSHIP_ID_ATTR, "")
    if not chart_relationship_id:
        raise ValueError("governed workbook relationship id is missing")
    chart_rel_type, target_part = _relationship_by_id(
        archive,
        chart_part,
        chart_relationship_id,
    )
    if not chart_rel_type.lower().rstrip("/").endswith("/package"):
        raise ValueError("governed chart relationship is not a package")
    if not target_part.lower().endswith(".xlsx"):
        raise ValueError("governed chart package is not an xlsx")
    return {
        "shape_id": shape_id,
        "slide_part": slide_part,
        "slide_relationship_id": slide_relationship_id,
        "chart_part": chart_part,
        "chart_relationship_id": chart_relationship_id,
        "target_part": target_part,
        "target_part_sha256": hashlib.sha256(
            archive.read(target_part)
        ).hexdigest(),
    }


def _rels_path_for_part(part_name: str | None) -> str:
    if part_name is None:
        return "_rels/.rels"
    normalised = part_name.replace("\\", "/").lstrip("/")
    directory, _, filename = normalised.rpartition("/")
    prefix = f"{directory}/" if directory else ""
    return f"{prefix}_rels/{filename}.rels"


def _relationship_location(rels_path: str, index: int, relationship_id: str) -> str:
    identity = relationship_id or str(index)
    return f"output.pptx!/{rels_path}#{identity}"


def _relationship_finding(
    rels_path: str,
    entry: Mapping[str, str],
    *,
    reason: str,
    resolved_target: str = "",
) -> dict[str, str]:
    return {
        "owner_rels_part": rels_path,
        "relationship_id": entry.get("Id", ""),
        "relationship_type": entry.get("Type", ""),
        "target_mode": entry.get("TargetMode", ""),
        "raw_target": entry.get("Target", ""),
        "resolved_target": resolved_target,
        "reason": reason,
    }


def _unsafe_relationship_reason(entry: Mapping[str, str]) -> str | None:
    rel_type = entry.get("Type", "").lower()
    target = entry.get("Target", "")
    target_mode = entry.get("TargetMode", "")
    decoded_target = unquote(target)
    path_only = decoded_target.split("?", 1)[0].split("#", 1)[0].lower()
    if any(
        fragment in rel_type
        for fragment in FORBIDDEN_RELATIONSHIP_TYPE_FRAGMENTS
    ):
        return "forbidden-relationship-type"
    if rel_type.rstrip("/").endswith("/script"):
        return "forbidden-relationship-type"
    if any(path_only.endswith(suffix) for suffix in FORBIDDEN_RELATIONSHIP_TARGET_SUFFIXES):
        return "forbidden-relationship-target"
    if any(
        fragment in path_only
        for fragment in ("/activex/", "/oleobject", "/vbaproject")
    ):
        return "forbidden-relationship-target"
    if target_mode.lower() == "external":
        findings = validate_external_relationship(entry)
        return findings[0].code.lower().replace("_", "-") if findings else None
    if (
        URI_SCHEME_RE.match(decoded_target)
        or decoded_target.startswith(("//", "\\\\"))
    ):
        return "external-target-mode-mismatch"
    return None


def _parse_relationship_part(
    archive: zipfile.ZipFile,
    archive_name: str,
    rels_path: str,
    issues: list[dict[str, str]],
) -> list[dict[str, str]] | None:
    """Strictly parse one OPC relationship part.

    ElementTree expands both default and prefixed namespaces to the same
    qualified name, and XML quote style is deliberately irrelevant.  Invalid
    XML, wrong namespaces, unexpected elements, duplicate IDs, and incomplete
    entries are all fail-closed findings.
    """

    try:
        root = ET.fromstring(archive.read(archive_name))
    except (KeyError, OSError, RuntimeError, zipfile.BadZipFile, ET.ParseError) as exc:
        _issue(
            issues,
            "OPC_RELATIONSHIP_XML_MALFORMED",
            f"output.pptx!/{rels_path}",
            str(exc),
        )
        return None
    if root.tag != RELATIONSHIPS_TAG:
        _issue(
            issues,
            "OPC_RELATIONSHIP_NAMESPACE_INVALID",
            f"output.pptx!/{rels_path}",
            f"expected {RELATIONSHIPS_TAG!r}, observed {root.tag!r}",
        )
        return None
    entries: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for index, relation in enumerate(list(root), start=1):
        if relation.tag != RELATIONSHIP_TAG:
            _issue(
                issues,
                "OPC_RELATIONSHIP_ELEMENT_INVALID",
                f"output.pptx!/{rels_path}",
                f"unexpected element {relation.tag!r}",
            )
            continue
        entry = {
            "Id": relation.attrib.get("Id", ""),
            "Type": relation.attrib.get("Type", ""),
            "Target": relation.attrib.get("Target", ""),
            "TargetMode": relation.attrib.get("TargetMode", ""),
        }
        location = _relationship_location(rels_path, index, entry["Id"])
        missing = [name for name in ("Id", "Type", "Target") if not entry[name]]
        structurally_valid = not missing
        if missing:
            _issue(
                issues,
                "OPC_RELATIONSHIP_ENTRY_INVALID",
                location,
                f"missing {','.join(missing)}",
            )
        if entry["Id"] in seen_ids:
            structurally_valid = False
            _issue(
                issues,
                "OPC_RELATIONSHIP_ID_DUPLICATE",
                location,
                entry["Id"],
            )
        elif entry["Id"]:
            seen_ids.add(entry["Id"])
        if entry["TargetMode"] and entry["TargetMode"].lower() != "external":
            structurally_valid = False
            _issue(
                issues,
                "OPC_RELATIONSHIP_TARGET_MODE_INVALID",
                location,
                entry["TargetMode"],
            )
        if list(relation) or (relation.text or "").strip():
            structurally_valid = False
            _issue(
                issues,
                "OPC_RELATIONSHIP_ELEMENT_INVALID",
                location,
                "Relationship elements must be empty",
            )
        entry["_structurally_valid"] = "true" if structurally_valid else "false"
        entries.append(entry)
    return entries


def _inspect_opc_relationship_graph(
    archive: zipfile.ZipFile,
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    """Recompute all relationship evidence and the root-reachable closure."""

    name_lookup: dict[str, str] = {}
    for archive_name in archive.namelist():
        normalised = archive_name.replace("\\", "/").lstrip("/")
        name_lookup.setdefault(normalised, archive_name)
    names = set(name_lookup)
    parsed_parts: dict[str, list[dict[str, str]]] = {}
    for rels_path in sorted(name for name in names if name.endswith(".rels")):
        parsed = _parse_relationship_part(
            archive,
            name_lookup[rels_path],
            rels_path,
            issues,
        )
        if parsed is not None:
            parsed_parts[rels_path] = parsed
        if rels_path != "_rels/.rels":
            owner = _owner_part_from_rels_path(rels_path)
            if owner is None or owner not in names:
                _issue(
                    issues,
                    "OPC_RELATIONSHIP_OWNER_MISSING",
                    f"output.pptx!/{rels_path}",
                    owner or "invalid relationship-part path",
                )

    if "_rels/.rels" not in names:
        _issue(
            issues,
            "OPC_ROOT_RELATIONSHIPS_MISSING",
            "output.pptx!/_rels/.rels",
            "package root relationship part is required",
        )

    unresolved: list[dict[str, str]] = []
    unsafe: list[dict[str, str]] = []
    total = 0
    internal = 0
    external = 0
    resolved_by_entry: dict[tuple[str, int], str] = {}
    safe_internal_entries: set[tuple[str, int]] = set()
    for rels_path, entries in sorted(parsed_parts.items()):
        for index, entry in enumerate(entries, start=1):
            total += 1
            is_external = entry.get("TargetMode", "").lower() == "external"
            if is_external:
                external += 1
            else:
                internal += 1
            location = _relationship_location(
                rels_path,
                index,
                entry.get("Id", ""),
            )
            unsafe_reason = _unsafe_relationship_reason(entry)
            if unsafe_reason is not None:
                finding = _relationship_finding(
                    rels_path,
                    entry,
                    reason=unsafe_reason,
                )
                unsafe.append(finding)
                _issue(
                    issues,
                    "OPC_UNSAFE_RELATIONSHIP",
                    location,
                    f"{unsafe_reason}: {entry.get('Target', '')}",
                )
            if is_external:
                continue
            target = entry.get("Target", "")
            resolved = _resolve_relationship_target(rels_path, target)
            if not target:
                reason = "empty-internal-target"
            elif resolved is None:
                reason = "invalid-internal-target"
            elif resolved not in names:
                reason = "missing-internal-target"
            else:
                reason = ""
            if reason:
                finding = _relationship_finding(
                    rels_path,
                    entry,
                    reason=reason,
                    resolved_target=resolved or "",
                )
                unresolved.append(finding)
                _issue(
                    issues,
                    "OPC_INTERNAL_TARGET_MISSING",
                    location,
                    f"{reason}: {resolved or target}",
                )
                continue
            resolved_by_entry[(rels_path, index)] = resolved
            if (
                unsafe_reason is None
                and entry.get("_structurally_valid") == "true"
            ):
                safe_internal_entries.add((rels_path, index))

    reachable_parts: set[str] = set()
    reachable_rels_parts: set[str] = set()
    reachable_targets: set[str] = set()
    queue: list[str | None] = [None]
    processed_owners: set[str | None] = set()
    while queue:
        owner = queue.pop(0)
        if owner in processed_owners:
            continue
        processed_owners.add(owner)
        rels_path = _rels_path_for_part(owner)
        entries = parsed_parts.get(rels_path)
        if entries is None:
            continue
        reachable_rels_parts.add(rels_path)
        for index, _entry in enumerate(entries, start=1):
            key = (rels_path, index)
            if key not in safe_internal_entries:
                continue
            target = resolved_by_entry[key]
            reachable_targets.add(target)
            if target in reachable_parts:
                continue
            reachable_parts.add(target)
            if _rels_path_for_part(target) in parsed_parts:
                queue.append(target)

    unreachable_slides = sorted(
        name for name in names if SLIDE_RE.fullmatch(name) and name not in reachable_parts
    )
    for slide_name in unreachable_slides:
        _issue(
            issues,
            "OPC_SLIDE_NOT_ROOT_REACHABLE",
            f"output.pptx!/{slide_name}",
            "slide is outside the closure rooted at _rels/.rels",
        )

    reachable_tag_relationship_count = 0
    for rels_path in reachable_rels_parts:
        for entry in parsed_parts[rels_path]:
            rel_type = entry.get("Type", "").lower().rstrip("/")
            target = entry.get("Target", "").lower()
            if rel_type.endswith("/tags") or "/tags/" in target:
                reachable_tag_relationship_count += 1

    package_parts = {
        name for name in names if name and not name.endswith("/")
    }
    unreachable_parts = sorted(
        package_parts
        - {"[Content_Types].xml"}
        - reachable_parts
        - reachable_rels_parts
    )
    for part_name in unreachable_parts:
        _issue(
            issues,
            "OPC_PART_NOT_ROOT_REACHABLE",
            f"output.pptx!/{part_name}",
            "part is outside the closure rooted at _rels/.rels",
        )

    return {
        "total_relationship_count": total,
        "internal_relationship_count": internal,
        "external_relationship_count": external,
        "unresolved_internal_relationship_count": len(unresolved),
        "unresolved_internal_relationships": unresolved,
        "unsafe_relationship_count": len(unsafe),
        "unsafe_relationships": unsafe,
        "reachable_part_count": len(reachable_parts),
        "reachable_relationship_part_count": len(reachable_rels_parts),
        "unreachable_slide_count": len(unreachable_slides),
        "unreachable_part_count": len(unreachable_parts),
        "unreachable_parts": unreachable_parts,
        "reachable_targets": reachable_targets,
        "reachable_tag_relationship_count": reachable_tag_relationship_count,
    }


def _inspect_content_types(
    archive: zipfile.ZipFile,
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    """Strictly parse OPC content types and bind presentation parts to safe types."""

    location = "output.pptx!/[Content_Types].xml"
    try:
        raw = archive.read("[Content_Types].xml")
    except KeyError:
        _issue(
            issues,
            "OPC_CONTENT_TYPES_MISSING",
            location,
            "[Content_Types].xml is required",
        )
        return {"default_count": 0, "override_count": 0, "missing_part_count": 0}
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        _issue(issues, "OPC_CONTENT_TYPES_MALFORMED", location, str(exc))
        return {"default_count": 0, "override_count": 0, "missing_part_count": 0}
    if root.tag != CONTENT_TYPES_TAG:
        _issue(
            issues,
            "OPC_CONTENT_TYPES_NAMESPACE_INVALID",
            location,
            f"expected {CONTENT_TYPES_TAG!r}, observed {root.tag!r}",
        )
        return {"default_count": 0, "override_count": 0, "missing_part_count": 0}

    defaults: dict[str, str] = {}
    overrides: dict[str, str] = {}
    for index, node in enumerate(list(root), start=1):
        node_location = f"{location}#{index}"
        if list(node) or (node.text or "").strip():
            _issue(
                issues,
                "OPC_CONTENT_TYPE_ENTRY_INVALID",
                node_location,
                "content-type entries must be empty",
            )
            continue
        if node.tag == CONTENT_TYPE_DEFAULT_TAG:
            if set(node.attrib) != {"Extension", "ContentType"}:
                _issue(
                    issues,
                    "OPC_CONTENT_TYPE_ENTRY_INVALID",
                    node_location,
                    "Default requires exactly Extension and ContentType",
                )
                continue
            extension = node.attrib["Extension"].lower().lstrip(".")
            content_type = node.attrib["ContentType"]
            if not extension or not content_type or extension in defaults:
                _issue(
                    issues,
                    "OPC_CONTENT_TYPE_DEFAULT_INVALID",
                    node_location,
                    extension or "empty extension",
                )
                continue
            defaults[extension] = content_type
        elif node.tag == CONTENT_TYPE_OVERRIDE_TAG:
            if set(node.attrib) != {"PartName", "ContentType"}:
                _issue(
                    issues,
                    "OPC_CONTENT_TYPE_ENTRY_INVALID",
                    node_location,
                    "Override requires exactly PartName and ContentType",
                )
                continue
            raw_part = node.attrib["PartName"]
            part = raw_part.lstrip("/")
            content_type = node.attrib["ContentType"]
            if (
                not raw_part.startswith("/")
                or not part
                or "\\" in part
                or posixpath.normpath(part) != part
                or not content_type
                or part in overrides
            ):
                _issue(
                    issues,
                    "OPC_CONTENT_TYPE_OVERRIDE_INVALID",
                    node_location,
                    raw_part,
                )
                continue
            overrides[part] = content_type
        else:
            _issue(
                issues,
                "OPC_CONTENT_TYPE_ELEMENT_INVALID",
                node_location,
                node.tag,
            )

    names = {
        name.replace("\\", "/").lstrip("/")
        for name in archive.namelist()
        if name and not name.endswith("/")
    }
    dangling = sorted(set(overrides) - names)
    for part in dangling:
        _issue(
            issues,
            "OPC_CONTENT_TYPE_OVERRIDE_DANGLING",
            location,
            part,
        )
    missing: list[str] = []
    resolved: dict[str, str] = {}
    for part in sorted(names - {"[Content_Types].xml"}):
        extension = part.rsplit(".", 1)[1].lower() if "." in part else ""
        content_type = overrides.get(part) or defaults.get(extension)
        if not content_type:
            missing.append(part)
            _issue(
                issues,
                "OPC_CONTENT_TYPE_PART_UNREGISTERED",
                f"output.pptx!/{part}",
                extension or "no extension",
            )
        else:
            resolved[part] = content_type

    _equal(
        issues,
        "OPC_PRESENTATION_CONTENT_TYPE_INVALID",
        "output.pptx!/ppt/presentation.xml",
        resolved.get("ppt/presentation.xml"),
        PRESENTATION_CONTENT_TYPE,
    )
    for part in sorted(name for name in names if SLIDE_RE.fullmatch(name)):
        _equal(
            issues,
            "OPC_SLIDE_CONTENT_TYPE_INVALID",
            f"output.pptx!/{part}",
            resolved.get(part),
            SLIDE_CONTENT_TYPE,
        )
    return {
        "default_count": len(defaults),
        "override_count": len(overrides),
        "missing_part_count": len(missing),
    }


def _inspect_native_editability(
    archive: zipfile.ZipFile,
    slide_names: Mapping[int, str],
    issues: list[dict[str, str]],
) -> dict[str, int | float]:
    """Recompute a fail-closed XML editability floor without production code."""

    text_runs = 0
    shape_count = 0
    picture_count = 0
    native_object_count = 0
    native_slide_count = 0
    for ordinal, name in sorted(slide_names.items()):
        try:
            root = ET.fromstring(archive.read(name))
        except (KeyError, ET.ParseError) as exc:
            _issue(
                issues,
                "EDITABILITY_SLIDE_XML_INVALID",
                f"output.pptx!/{name}",
                str(exc),
            )
            continue
        if root.tag.rsplit("}", 1)[-1] != "sld":
            _issue(
                issues,
                "EDITABILITY_SLIDE_ROOT_INVALID",
                f"output.pptx!/{name}",
                root.tag,
            )
            continue
        local_names = [node.tag.rsplit("}", 1)[-1] for node in root.iter()]
        slide_text_runs = sum(1 for local in local_names if local == "t")
        slide_pictures = sum(1 for local in local_names if local == "pic")
        slide_native = sum(
            1 for local in local_names if local in {"sp", "graphicFrame", "cxnSp"}
        )
        slide_shapes = sum(1 for local in local_names if local == "cNvPr")
        text_runs += slide_text_runs
        picture_count += slide_pictures
        native_object_count += slide_native
        shape_count += slide_shapes
        if slide_native > 0:
            native_slide_count += 1
        elif slide_pictures > 0:
            _issue(
                issues,
                "EDITABILITY_RASTER_ONLY_SLIDE",
                f"output.pptx!/{name}",
                f"slide {ordinal} has pictures but no native object",
            )
        else:
            _issue(
                issues,
                "EDITABILITY_EMPTY_SLIDE",
                f"output.pptx!/{name}",
                f"slide {ordinal} has no native object",
            )
    slide_count = len(slide_names)
    return {
        "slide_count": slide_count,
        "text_run_count": text_runs,
        "shape_count": shape_count,
        "native_object_count": native_object_count,
        "picture_count": picture_count,
        "native_editable_slide_count": native_slide_count,
        "native_editable_coverage": (
            round(native_slide_count / slide_count, 6) if slide_count else 0.0
        ),
    }


def _issue(
    issues: list[dict[str, str]],
    code: str,
    location: str,
    detail: str,
) -> None:
    issues.append({"code": code, "location": location, "detail": detail})


def _merge_contract_findings(
    issues: list[dict[str, str]], findings: Any
) -> None:
    seen = {(item["code"], item["location"], item["detail"]) for item in issues}
    for finding in findings:
        key = (finding.code, finding.location, finding.detail)
        if key in seen:
            continue
        seen.add(key)
        _issue(issues, *key)


def _sha256_and_size(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _read_json(
    path: Path,
    issues: list[dict[str, str]],
    location: str,
) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _issue(issues, "JSON_READ_FAILED", location, str(exc))
        return None


def _validate_schema(
    payload: Any,
    issues: list[dict[str, str]],
) -> None:
    try:
        import jsonschema
    except ImportError:
        _issue(
            issues,
            "JSONSCHEMA_UNAVAILABLE",
            "schema",
            "jsonschema is required",
        )
        return
    schema = _read_json(SCHEMA_PATH, issues, "schema")
    if schema is None:
        return
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        _issue(issues, "SCHEMA_INVALID", "schema", exc.message)
        return
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    for error in errors:
        suffix = ".".join(str(part) for part in error.absolute_path)
        _issue(
            issues,
            "SCHEMA_VALIDATION_FAILED",
            f"report.{suffix}" if suffix else "report",
            error.message,
        )


def _root_path(
    raw_root: str | os.PathLike[str],
    issues: list[dict[str, str]],
) -> Path | None:
    raw = Path(raw_root).expanduser()
    try:
        if raw.is_symlink():
            _issue(issues, "PROJECT_ROOT_SYMLINK", "project_root", str(raw))
            return None
        root = raw.resolve(strict=True)
    except OSError as exc:
        _issue(issues, "PROJECT_ROOT_INVALID", "project_root", str(exc))
        return None
    if not root.is_dir():
        _issue(issues, "PROJECT_ROOT_NOT_DIRECTORY", "project_root", str(root))
        return None
    return root


def _inside_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _reject_symlink_components(
    path: Path,
    root: Path,
    issues: list[dict[str, str]],
    location: str,
) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        _issue(issues, "PATH_OUTSIDE_PROJECT", location, str(path))
        return False
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        try:
            if cursor.is_symlink():
                _issue(issues, "PATH_SYMLINK_FORBIDDEN", location, str(cursor))
                return False
        except OSError as exc:
            _issue(issues, "PATH_INSPECTION_FAILED", location, str(exc))
            return False
    return True


def _resolve_report_argument(
    raw_path: str | os.PathLike[str],
    root: Path,
    issues: list[dict[str, str]],
) -> Path | None:
    raw = Path(raw_path).expanduser()
    candidate = raw if raw.is_absolute() else root / raw
    lexical = Path(os.path.abspath(candidate))
    if not _inside_root(lexical, root):
        _issue(issues, "REPORT_PATH_OUTSIDE_PROJECT", "report_path", str(raw))
        return None
    if not _reject_symlink_components(lexical, root, issues, "report_path"):
        return None
    try:
        mode = lexical.lstat().st_mode
    except OSError as exc:
        _issue(issues, "REPORT_FILE_MISSING", "report_path", str(exc))
        return None
    if not stat.S_ISREG(mode):
        _issue(issues, "REPORT_NOT_REGULAR", "report_path", str(lexical))
        return None
    return lexical


def _resolve_bound_absolute_file(
    raw_value: Any,
    root: Path,
    issues: list[dict[str, str]],
    location: str,
) -> Path | None:
    if not isinstance(raw_value, str) or not raw_value or "\0" in raw_value:
        _issue(issues, "BOUND_PATH_INVALID", location, str(raw_value))
        return None
    raw = Path(raw_value)
    if not raw.is_absolute():
        _issue(issues, "BOUND_PATH_NOT_ABSOLUTE", location, raw_value)
        return None
    lexical = Path(os.path.abspath(raw))
    if str(raw) != str(lexical):
        _issue(
            issues,
            "BOUND_PATH_NOT_CANONICAL",
            location,
            f"expected {lexical}",
        )
        return None
    if not _inside_root(lexical, root):
        _issue(issues, "BOUND_PATH_OUTSIDE_PROJECT", location, raw_value)
        return None
    if not _reject_symlink_components(lexical, root, issues, location):
        return None
    try:
        mode = lexical.lstat().st_mode
    except OSError as exc:
        _issue(issues, "BOUND_FILE_MISSING", location, str(exc))
        return None
    if not stat.S_ISREG(mode):
        _issue(issues, "BOUND_FILE_NOT_REGULAR", location, raw_value)
        return None
    try:
        resolved = lexical.resolve(strict=True)
    except OSError as exc:
        _issue(issues, "BOUND_PATH_RESOLUTION_FAILED", location, str(exc))
        return None
    if resolved != lexical:
        _issue(issues, "BOUND_PATH_NOT_CANONICAL", location, f"resolved to {resolved}")
        return None
    return lexical


def _verify_bound_hash(
    path: Path | None,
    expected: Any,
    issues: list[dict[str, str]],
    location: str,
) -> None:
    if path is None:
        return
    if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
        _issue(issues, "BOUND_SHA256_INVALID", location, str(expected))
        return
    try:
        actual, _ = _sha256_and_size(path)
    except OSError as exc:
        _issue(issues, "BOUND_FILE_READ_FAILED", location, str(exc))
        return
    if actual != expected:
        _issue(
            issues,
            "BOUND_SHA256_MISMATCH",
            location,
            f"expected {expected}, observed {actual}",
        )


def _read_authority_json(
    path: Path | None,
    *,
    label: str,
    issues: list[dict[str, str]],
) -> Any | None:
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _issue(
            issues,
            f"{label}_JSON_INVALID",
            f"report.authority.{label.lower()}_path",
            str(exc),
        )
        return None


def _validate_fact_store_authority(
    path: Path | None,
    issues: list[dict[str, str]],
) -> dict[str, Mapping[str, Any]]:
    payload = _read_authority_json(path, label="FACT_STORE", issues=issues)
    if payload is None:
        return {}
    try:
        import jsonschema
    except ImportError:
        _issue(
            issues,
            "JSONSCHEMA_UNAVAILABLE",
            "report.authority.fact_store_path",
            "jsonschema is required",
        )
        return {}
    schema = _read_json(
        FACT_STORE_SCHEMA_PATH,
        issues,
        "schema.fact-store.v1",
    )
    if schema is None:
        return {}
    schema_errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    for error in schema_errors:
        suffix = ".".join(str(part) for part in error.absolute_path)
        _issue(
            issues,
            "FACT_STORE_SCHEMA_INVALID",
            f"fact_store.{suffix}" if suffix else "fact_store",
            error.message,
        )
    if not isinstance(payload, Mapping):
        return {}
    sources = payload.get("sources")
    facts = payload.get("facts")
    if not isinstance(sources, list) or not isinstance(facts, list):
        return {}
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping) or not isinstance(source.get("id"), str):
            continue
        source_id = source["id"]
        if source_id in source_ids:
            _issue(
                issues,
                "FACT_STORE_SOURCE_ID_DUPLICATE",
                f"fact_store.sources.{index}.id",
                source_id,
            )
        source_ids.add(source_id)
    facts_by_id: dict[str, Mapping[str, Any]] = {}
    seen_fact_ids: set[str] = set()
    for index, fact in enumerate(facts):
        if not isinstance(fact, Mapping) or not isinstance(fact.get("id"), str):
            continue
        fact_id = fact["id"]
        if fact_id in seen_fact_ids:
            _issue(
                issues,
                "FACT_STORE_FACT_ID_DUPLICATE",
                f"fact_store.facts.{index}.id",
                fact_id,
            )
            continue
        seen_fact_ids.add(fact_id)
        source_id = fact.get("source_id")
        if source_id not in source_ids:
            _issue(
                issues,
                "FACT_STORE_SOURCE_REF_UNKNOWN",
                f"fact_store.facts.{index}.source_id",
                str(source_id),
            )
        value = fact.get("value")
        if isinstance(value, float) and not math.isfinite(value):
            _issue(
                issues,
                "FACT_STORE_VALUE_NONFINITE",
                f"fact_store.facts.{index}.value",
                str(value),
            )
        if fact.get("status", "active") == "active":
            facts_by_id[fact_id] = fact
    return facts_by_id


def _resolve_manifest_asset_path(
    raw_value: Any,
    root: Path,
    issues: list[dict[str, str]],
    location: str,
) -> Path | None:
    if not isinstance(raw_value, str) or not raw_value:
        _issue(issues, "ASSET_MANIFEST_PATH_INVALID", location, str(raw_value))
        return None
    relative = Path(raw_value)
    if (
        relative.is_absolute()
        or raw_value.startswith("~")
        or "\\" in raw_value
        or any(part in {"", ".."} for part in relative.parts)
    ):
        _issue(issues, "ASSET_MANIFEST_PATH_INVALID", location, raw_value)
        return None
    lexical = Path(os.path.abspath(root / relative))
    if not _inside_root(lexical, root):
        _issue(issues, "ASSET_MANIFEST_PATH_OUTSIDE_PROJECT", location, raw_value)
        return None
    if not _reject_symlink_components(lexical, root, issues, location):
        return None
    try:
        mode = lexical.lstat().st_mode
    except OSError as exc:
        _issue(issues, "ASSET_MANIFEST_FILE_MISSING", location, str(exc))
        return None
    if not stat.S_ISREG(mode):
        _issue(issues, "ASSET_MANIFEST_FILE_INVALID", location, raw_value)
        return None
    return lexical


def _validate_asset_manifest_authority(
    path: Path | None,
    root: Path,
    issues: list[dict[str, str]],
) -> dict[str, str]:
    payload = _read_authority_json(path, label="ASSET_MANIFEST", issues=issues)
    if payload is None:
        return {}
    if (
        not isinstance(payload, Mapping)
        or set(payload) != {"schema_version", "bindings"}
        or payload.get("schema_version") != "1.0"
        or not isinstance(payload.get("bindings"), Mapping)
    ):
        _issue(
            issues,
            "ASSET_MANIFEST_SCHEMA_INVALID",
            "asset_manifest",
            "expected schema_version 1.0 and an object-valued bindings map",
        )
        return {}
    authorized: dict[str, str] = {}
    supported_suffixes = {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".emf", ".wmf"
    }
    for asset_ref, binding in sorted(payload["bindings"].items()):
        location = f"asset_manifest.bindings.{asset_ref}"
        if not isinstance(asset_ref, str) or not asset_ref:
            _issue(issues, "ASSET_MANIFEST_REF_INVALID", location, str(asset_ref))
            continue
        if not isinstance(binding, Mapping) or set(binding) != {"path", "sha256", "record"}:
            _issue(
                issues,
                "ASSET_MANIFEST_BINDING_INVALID",
                location,
                "expected exactly path, sha256, and record",
            )
            continue
        expected_sha = binding.get("sha256")
        record = binding.get("record")
        if not isinstance(expected_sha, str) or not SHA256_RE.fullmatch(expected_sha):
            _issue(issues, "ASSET_MANIFEST_SHA256_INVALID", location, str(expected_sha))
            continue
        required_record = {"id", "kind", "quality", "source", "license", "retrieved_at"}
        if not isinstance(record, Mapping) or not required_record.issubset(record):
            _issue(issues, "ASSET_MANIFEST_PROVENANCE_INVALID", location, str(record))
            continue
        quality = record.get("quality")
        dimensions_valid = (
            type(record.get("width_px")) is int
            and record["width_px"] > 0
            and type(record.get("height_px")) is int
            and record["height_px"] > 0
        )
        provenance_valid = (
            record.get("id") == asset_ref
            and isinstance(record.get("kind"), str)
            and bool(record.get("kind"))
            and isinstance(quality, (int, float))
            and not isinstance(quality, bool)
            and 0 <= float(quality) <= 1
            and all(
                isinstance(record.get(field), str) and bool(record.get(field))
                for field in ("source", "license", "retrieved_at")
            )
            and dimensions_valid
        )
        if not provenance_valid:
            _issue(issues, "ASSET_MANIFEST_PROVENANCE_INVALID", location, str(record))
            continue
        asset_path = _resolve_manifest_asset_path(
            binding.get("path"),
            root,
            issues,
            f"{location}.path",
        )
        if asset_path is None:
            continue
        if asset_path.suffix.lower() not in supported_suffixes:
            _issue(
                issues,
                "ASSET_MANIFEST_FORMAT_UNSUPPORTED",
                f"{location}.path",
                asset_path.suffix,
            )
            continue
        try:
            actual_sha, _ = _sha256_and_size(asset_path)
        except OSError as exc:
            _issue(issues, "ASSET_MANIFEST_FILE_READ_FAILED", location, str(exc))
            continue
        if actual_sha != expected_sha:
            _issue(
                issues,
                "ASSET_MANIFEST_FILE_SHA256_MISMATCH",
                location,
                f"expected {expected_sha}, observed {actual_sha}",
            )
            continue
        authorized[asset_ref] = expected_sha
    return authorized


def _validate_connective_copy_authority(
    path: Path | None,
    issues: list[dict[str, str]],
) -> dict[str, str]:
    payload = _read_authority_json(path, label="CONNECTIVE_COPY", issues=issues)
    if payload is None:
        return {}
    if (
        not isinstance(payload, Mapping)
        or set(payload) != {"schema_version", "entries"}
        or payload.get("schema_version") != "1.0"
        or not isinstance(payload.get("entries"), list)
    ):
        _issue(
            issues,
            "CONNECTIVE_COPY_SCHEMA_INVALID",
            "connective_copy",
            "expected schema_version 1.0 and an entries array",
        )
        return {}
    by_id: dict[str, str] = {}
    by_text: dict[str, str] = {}
    for index, entry in enumerate(payload["entries"]):
        location = f"connective_copy.entries.{index}"
        if not isinstance(entry, Mapping) or set(entry) != {"id", "text"}:
            _issue(issues, "CONNECTIVE_COPY_ENTRY_INVALID", location, str(entry))
            continue
        connective_id = entry.get("id")
        text = entry.get("text")
        if not isinstance(connective_id, str) or not connective_id or not isinstance(text, str):
            _issue(issues, "CONNECTIVE_COPY_ENTRY_INVALID", location, str(entry))
            continue
        if connective_id in by_id:
            _issue(issues, "CONNECTIVE_COPY_ID_DUPLICATE", location, connective_id)
            continue
        if text in by_text:
            _issue(
                issues,
                "CONNECTIVE_COPY_TEXT_DUPLICATE",
                location,
                connective_id,
            )
            continue
        by_id[connective_id] = text
        by_text[text] = connective_id
    return by_id


def _normalise_authority_text(value: str) -> str:
    return "".join(value.split()).replace("％", "%")


def _decimal_literal(value: str) -> tuple[Decimal, bool] | None:
    candidate = _normalise_authority_text(value).replace(",", "")
    is_percent = candidate.endswith("%")
    if is_percent:
        candidate = candidate[:-1]
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?", candidate):
        return None
    try:
        return Decimal(candidate), is_percent
    except InvalidOperation:
        return None


def _validate_binding_value_authority(
    evidence: Mapping[str, Any],
    actual: str,
    authority: Mapping[str, Any],
    issues: list[dict[str, str]],
    location: str,
) -> None:
    actual_sha = hashlib.sha256(actual.encode("utf-8")).hexdigest()
    if actual_sha != evidence.get("replacement_sha256"):
        _issue(
            issues,
            "BINDING_OUTPUT_VALUE_SHA256_MISMATCH",
            location,
            f"expected {evidence.get('replacement_sha256')}, observed {actual_sha}",
        )
        return
    fact_refs = evidence.get("fact_refs")
    connective_ref = evidence.get("connective_ref")
    if not isinstance(fact_refs, list):
        fact_refs = []
    facts = authority.get("facts", {})
    connectives = authority.get("connectives", {})
    if fact_refs and connective_ref:
        _issue(
            issues,
            "BINDING_AUTHORITY_AMBIGUOUS",
            location,
            "binding claims both fact and connective authority",
        )
        return
    if fact_refs:
        missing = [ref for ref in fact_refs if ref not in facts]
        if missing:
            _issue(
                issues,
                "AUTHORITY_FACT_REF_UNKNOWN",
                location,
                ",".join(missing),
            )
            return
        fact_findings = validate_fact_evidence_value(
            actual,
            evidence_mode=str(evidence.get("mode", "")),
            fact_refs=fact_refs,
            facts_by_id=facts,
            render_contract=None,
            location=location,
        )
        if fact_findings:
            _issue(
                issues,
                "BINDING_VALUE_NOT_FACT_AUTHORIZED",
                location,
                actual_sha,
            )
        for finding in fact_findings:
            _issue(
                issues,
                finding.code,
                finding.location,
                finding.detail,
            )
        return
    if isinstance(connective_ref, str) and connective_ref:
        approved = connectives.get(connective_ref)
        if approved is None:
            _issue(
                issues,
                "AUTHORITY_CONNECTIVE_REF_UNKNOWN",
                location,
                connective_ref,
            )
        elif actual != approved:
            _issue(
                issues,
                "BINDING_VALUE_NOT_CONNECTIVE_AUTHORIZED",
                location,
                actual_sha,
            )
        return
    _issue(
        issues,
        "BINDING_AUTHORITY_MISSING",
        location,
        "text/embedded binding has neither fact_refs nor connective_ref",
    )


def _validate_binding_authority_metadata(
    report: Mapping[str, Any],
    authority: Mapping[str, Any],
    issues: list[dict[str, str]],
) -> None:
    evidence = report.get("binding_evidence")
    if not isinstance(evidence, list):
        return
    assets = authority.get("assets", {})
    for index, item in enumerate(evidence):
        if not isinstance(item, Mapping):
            continue
        location = f"report.binding_evidence.{index}"
        kind = item.get("binding_kind")
        asset_refs = item.get("asset_refs")
        if kind == "asset":
            if not isinstance(asset_refs, list) or len(asset_refs) != 1:
                _issue(
                    issues,
                    "AUTHORITY_ASSET_REF_INVALID",
                    location,
                    str(asset_refs),
                )
                continue
            asset_ref = asset_refs[0]
            expected_sha = assets.get(asset_ref)
            if expected_sha is None:
                _issue(issues, "AUTHORITY_ASSET_REF_UNKNOWN", location, str(asset_ref))
            elif item.get("replacement_sha256") != expected_sha:
                _issue(
                    issues,
                    "AUTHORITY_ASSET_SHA256_MISMATCH",
                    location,
                    f"manifest {expected_sha}, evidence {item.get('replacement_sha256')}",
                )
        elif asset_refs:
            _issue(
                issues,
                "AUTHORITY_ASSET_REF_UNEXPECTED",
                location,
                str(asset_refs),
            )


def _read_slide_shape_text(slide_bytes: bytes, shape_id: int) -> str:
    root = ET.fromstring(slide_bytes)
    matches: list[ET.Element] = []
    for candidate in root.iter():
        if candidate.tag.rsplit("}", 1)[-1] not in {"sp", "graphicFrame", "cxnSp"}:
            continue
        marker = next(
            (
                node
                for node in candidate.iter()
                if node.tag.rsplit("}", 1)[-1] == "cNvPr"
                and node.attrib.get("id") == str(shape_id)
            ),
            None,
        )
        if marker is not None:
            matches.append(candidate)
    if len(matches) != 1:
        raise ValueError("bound text shape not found uniquely")
    return "\n".join(
        node.text or ""
        for node in matches[0].iter()
        if node.tag.rsplit("}", 1)[-1] == "t"
    ).strip()


def _equal(
    issues: list[dict[str, str]],
    code: str,
    location: str,
    actual: Any,
    expected: Any,
) -> None:
    if actual != expected:
        _issue(
            issues,
            code,
            location,
            f"expected {expected!r}, observed {actual!r}",
        )


def _normalise_duplicate_records(value: Any) -> list[tuple[str, tuple[int, ...]]] | None:
    if not isinstance(value, list):
        return None
    records: list[tuple[str, tuple[int, ...]]] = []
    for entry in value:
        if not isinstance(entry, Mapping):
            return None
        page_id = entry.get("page_id")
        ordinals = entry.get("ordinals")
        if (
            not isinstance(page_id, str)
            or not isinstance(ordinals, list)
            or not all(type(item) is int for item in ordinals)
        ):
            return None
        records.append((page_id, tuple(sorted(ordinals))))
    return sorted(records)


def _governed_inventory_identity_sha256(records: list[Any]) -> str:
    """Hash only immutable certified slot identity, never output values."""

    identities: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            identities.append({field: None for field in GOVERNED_IDENTITY_FIELDS})
            continue
        identity = {field: record.get(field) for field in GOVERNED_IDENTITY_FIELDS}
        identity["peer_group_id"] = identity["peer_group_id"] or ""
        identities.append(identity)
    identities.sort(
        key=lambda item: (
            item.get("ordinal") if type(item.get("ordinal")) is int else -1,
            item.get("slot_id") if isinstance(item.get("slot_id"), str) else "",
        )
    )
    return hashlib.sha256(
        json.dumps(
            identities,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _report_duplicate_keys(
    issues: list[dict[str, str]],
    *,
    code: str,
    location: str,
    records: list[Any],
    fields: tuple[str, ...],
) -> None:
    counts: dict[tuple[Any, ...], int] = {}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        key = tuple(record.get(field) for field in fields)
        counts[key] = counts.get(key, 0) + 1
    duplicates = sorted(
        (repr(key), count) for key, count in counts.items() if count != 1
    )
    if duplicates:
        _issue(issues, code, location, repr(duplicates))


def _inspect_query_authoritative_structure(
    archive: zipfile.ZipFile,
    authority: QueryCoverageAuthority,
    issues: list[dict[str, str]],
) -> None:
    """Bind final slide structure to immutable selected-template counts."""

    for page in authority.selected_pages:
        slide_part = f"ppt/slides/slide{page.ordinal}.xml"
        location = f"output.pptx!/{slide_part}"
        try:
            root = ET.fromstring(archive.read(slide_part))
        except (KeyError, ET.ParseError) as exc:
            _issue(issues, "QUERY_STRUCTURE_SLIDE_INVALID", location, str(exc))
            continue
        observed = {
            "page_shape_count": sum(
                1
                for node in root.iter()
                if node.tag == f"{{{PRESENTATION_NS}}}cNvPr"
            ),
            "page_native_object_count": sum(
                1
                for node in root.iter()
                if node.tag
                in {
                    f"{{{PRESENTATION_NS}}}sp",
                    f"{{{PRESENTATION_NS}}}graphicFrame",
                    f"{{{PRESENTATION_NS}}}grpSp",
                }
            ),
        }
        rels_path = _rels_path_for_part(slide_part)
        relationships = _parse_relationship_part(
            archive,
            rels_path,
            rels_path,
            issues,
        )
        if relationships is None:
            relationships = []
        observed["page_image_count"] = sum(
            1
            for relation in relationships
            if relation.get("Type", "").lower().rstrip("/").endswith("/image")
        )
        observed["page_chart_count"] = sum(
            1
            for relation in relationships
            if relation.get("Type", "").lower().rstrip("/").endswith("/chart")
        )
        actual_table_count = sum(
            1 for node in root.iter() if node.tag == f"{{{DRAWING_NS}}}tbl"
        )
        expected = dict(page.structure_counts)
        for field in (
            "page_shape_count",
            "page_native_object_count",
            "page_image_count",
            "page_chart_count",
        ):
            _equal(
                issues,
                "QUERY_STRUCTURE_COUNT_MISMATCH",
                f"{location}#{field}",
                observed[field],
                expected.get(field),
            )
        expected_table_markers = expected.get("page_table_count", 0)
        if (expected_table_markers == 0) != (actual_table_count == 0):
            _issue(
                issues,
                "QUERY_STRUCTURE_TABLE_PRESENCE_MISMATCH",
                f"{location}#page_table_count",
                (
                    f"certified_markers={expected_table_markers} "
                    f"actual_tables={actual_table_count}"
                ),
            )


def _validate_cross_fields(
    report: Mapping[str, Any],
    output_path: Path | None,
    output_sha256: str | None,
    output_size: int | None,
    authority_context: Mapping[str, Any],
    query_authority: QueryCoverageAuthority | None,
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    observed: dict[str, Any] = {
        "output_sha256": output_sha256,
        "output_size_bytes": output_size,
    }
    if report.get("status") != "pass":
        _issue(
            issues,
            "REPORT_NOT_PASS",
            "report.status",
            str(report.get("status")),
        )

    lineage_raw = report.get("lineage_records")
    lineage = lineage_raw if isinstance(lineage_raw, list) else []
    target_count = report.get("target_slide_count")
    if type(target_count) is int:
        _equal(
            issues,
            "TARGET_LINEAGE_COUNT_MISMATCH",
            "report.target_slide_count",
            target_count,
            len(lineage),
        )
    else:
        target_count = None

    ordinals: list[int] = []
    page_ids: list[str] = []
    for index, record in enumerate(lineage):
        location = f"report.lineage_records.{index}"
        if not isinstance(record, Mapping):
            continue
        ordinal = record.get("ordinal")
        page_id = record.get("page_id")
        if type(ordinal) is int:
            ordinals.append(ordinal)
        if isinstance(page_id, str):
            page_ids.append(page_id)
        for key, expected in (
            ("status", "pass"),
            ("source_package_verified", True),
            ("source_slide_verified", True),
            ("structure_match", True),
        ):
            _equal(
                issues,
                "LINEAGE_NOT_VERIFIED",
                f"{location}.{key}",
                record.get(key),
                expected,
            )
    if target_count is not None:
        _equal(
            issues,
            "LINEAGE_ORDINAL_SET_MISMATCH",
            "report.lineage_records",
            sorted(ordinals),
            list(range(1, target_count + 1)),
        )
    distinct_page_ids = len(set(page_ids))
    observed["lineage_count"] = len(lineage)
    observed["distinct_page_id_count"] = distinct_page_ids
    _equal(
        issues,
        "DISTINCT_PAGE_COUNT_MISMATCH",
        "report.distinct_page_id_count",
        report.get("distinct_page_id_count"),
        distinct_page_ids,
    )
    page_ordinals: dict[str, list[int]] = {}
    for ordinal, page_id in zip(ordinals, page_ids):
        page_ordinals.setdefault(page_id, []).append(ordinal)
    expected_duplicates = sorted(
        (page_id, tuple(sorted(values)))
        for page_id, values in page_ordinals.items()
        if len(values) > 1
    )
    reported_duplicates = _normalise_duplicate_records(
        report.get("duplicate_page_records")
    )
    _equal(
        issues,
        "DUPLICATE_PAGE_RECORDS_MISMATCH",
        "report.duplicate_page_records",
        reported_duplicates,
        expected_duplicates,
    )

    opc = report.get("opc_integrity")
    if isinstance(opc, Mapping):
        unresolved = opc.get("unresolved_internal_relationships")
        unsafe = opc.get("unsafe_relationships")
        unresolved_count = len(unresolved) if isinstance(unresolved, list) else None
        unsafe_count = len(unsafe) if isinstance(unsafe, list) else None
        _equal(
            issues,
            "OPC_UNRESOLVED_COUNT_MISMATCH",
            "report.opc_integrity.unresolved_internal_relationship_count",
            opc.get("unresolved_internal_relationship_count"),
            unresolved_count,
        )
        _equal(
            issues,
            "OPC_UNSAFE_COUNT_MISMATCH",
            "report.opc_integrity.unsafe_relationship_count",
            opc.get("unsafe_relationship_count"),
            unsafe_count,
        )
        internal = opc.get("internal_relationship_count")
        external = opc.get("external_relationship_count")
        if type(internal) is int and type(external) is int:
            _equal(
                issues,
                "OPC_RELATIONSHIP_TOTAL_MISMATCH",
                "report.opc_integrity.total_relationship_count",
                opc.get("total_relationship_count"),
                internal + external,
            )

    editability = report.get("editability")
    if isinstance(editability, Mapping) and target_count is not None:
        slide_count = editability.get("slide_count")
        native_count = editability.get("native_editable_slide_count")
        _equal(
            issues,
            "EDITABILITY_SLIDE_COUNT_MISMATCH",
            "report.editability.slide_count",
            slide_count,
            target_count,
        )
        _equal(
            issues,
            "EDITABILITY_NATIVE_COUNT_MISMATCH",
            "report.editability.native_editable_slide_count",
            native_count,
            target_count,
        )
        if type(slide_count) is int and slide_count > 0 and type(native_count) is int:
            expected_coverage = round(native_count / slide_count, 6)
            _equal(
                issues,
                "EDITABILITY_COVERAGE_MISMATCH",
                "report.editability.native_editable_coverage",
                editability.get("native_editable_coverage"),
                expected_coverage,
            )

    style = report.get("style_cluster_adherence")
    if isinstance(style, Mapping) and target_count is not None:
        _equal(
            issues,
            "STYLE_TOTAL_MISMATCH",
            "report.style_cluster_adherence.total",
            style.get("total"),
            target_count,
        )

    binding_evidence = report.get("binding_evidence")
    if isinstance(binding_evidence, list):
        _report_duplicate_keys(
            issues,
            code="BINDING_EVIDENCE_KEY_DUPLICATE",
            location="report.binding_evidence",
            records=binding_evidence,
            fields=("ordinal", "page_id", "slot_id"),
        )
        binding_counts: dict[int, int] = {}
        embedded_count = 0
        for item in binding_evidence:
            if not isinstance(item, Mapping):
                continue
            ordinal = item.get("ordinal")
            if type(ordinal) is int:
                binding_counts[ordinal] = binding_counts.get(ordinal, 0) + 1
            if item.get("binding_kind") == "embedded":
                embedded_count += 1
        for index, record in enumerate(lineage):
            if not isinstance(record, Mapping):
                continue
            ordinal = record.get("ordinal")
            if type(ordinal) is int:
                _equal(
                    issues,
                    "LINEAGE_BINDING_COUNT_MISMATCH",
                    f"report.lineage_records.{index}.binding_count",
                    record.get("binding_count"),
                    binding_counts.get(ordinal, 0),
                )
        residue = report.get("source_residue")
        if isinstance(residue, Mapping):
            _equal(
                issues,
                "GOVERNED_BINDING_EVIDENCE_COUNT_MISMATCH",
                "report.source_residue.governed_content_binding_count",
                residue.get("governed_content_binding_count"),
                embedded_count,
            )
            _equal(
                issues,
                "GOVERNED_SLOT_BINDING_COUNT_MISMATCH",
                "report.source_residue.governed_content_slot_count",
                residue.get("governed_content_slot_count"),
                embedded_count,
            )
            _equal(
                issues,
                "GOVERNED_VERIFIED_COUNT_MISMATCH",
                "report.source_residue.verified_governed_content_count",
                residue.get("verified_governed_content_count"),
                embedded_count,
            )
            mutations = residue.get("governed_mutations")
            mutation_records = mutations if isinstance(mutations, list) else []
            _report_duplicate_keys(
                issues,
                code="GOVERNED_MUTATION_KEY_DUPLICATE",
                location="report.source_residue.governed_mutations",
                records=mutation_records,
                fields=("ordinal", "page_id", "slot_id"),
            )
            _report_duplicate_keys(
                issues,
                code="GOVERNED_MUTATION_LOCATOR_DUPLICATE",
                location="report.source_residue.governed_mutations",
                records=mutation_records,
                fields=("ordinal", "source_part", "locator"),
            )
            _equal(
                issues,
                "GOVERNED_MUTATION_COUNT_MISMATCH",
                "report.source_residue.governed_mutations",
                len(mutation_records),
                embedded_count,
            )
            expected_manifest_sha = hashlib.sha256(
                json.dumps(
                    mutation_records,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            _equal(
                issues,
                "GOVERNED_MUTATION_MANIFEST_SHA256_MISMATCH",
                "report.source_residue.mutation_manifest_sha256",
                residue.get("mutation_manifest_sha256"),
                expected_manifest_sha,
            )
            evidence_keys = {
                (item.get("ordinal"), item.get("page_id"), item.get("slot_id"))
                for item in binding_evidence
                if isinstance(item, Mapping)
                and item.get("binding_kind") == "embedded"
            }
            mutation_keys = {
                (item.get("ordinal"), item.get("page_id"), item.get("slot_id"))
                for item in mutation_records
                if isinstance(item, Mapping)
            }
            _equal(
                issues,
                "GOVERNED_MUTATION_EVIDENCE_KEYS_MISMATCH",
                "report.source_residue.governed_mutations",
                sorted(mutation_keys),
                sorted(evidence_keys),
            )
        _equal(
            issues,
            "STYLE_MATCH_COUNT_MISMATCH",
            "report.style_cluster_adherence.matches",
            style.get("matches"),
            target_count,
        )

    metrics = report.get("assembly_metrics")
    if isinstance(metrics, Mapping):
        imported_parts = metrics.get("imported_parts")
        imported_count = len(imported_parts) if isinstance(imported_parts, list) else None
        _equal(
            issues,
            "IMPORTED_PART_COUNT_MISMATCH",
            "report.assembly_metrics.imported_part_count",
            metrics.get("imported_part_count"),
            imported_count,
        )
        if output_size is not None:
            _equal(
                issues,
                "ASSEMBLY_OUTPUT_SIZE_MISMATCH",
                "report.assembly_metrics.output_size_bytes",
                metrics.get("output_size_bytes"),
                output_size,
            )
        if isinstance(opc, Mapping):
            _equal(
                issues,
                "ASSEMBLY_OPC_UNRESOLVED_MISMATCH",
                "report.assembly_metrics.unresolved_internal_relationship_count",
                metrics.get("unresolved_internal_relationship_count"),
                opc.get("unresolved_internal_relationship_count"),
            )

    size_check = report.get("size_check")
    if isinstance(size_check, Mapping) and output_size is not None:
        _equal(
            issues,
            "SIZE_CHECK_OUTPUT_MISMATCH",
            "report.size_check.output_size_bytes",
            size_check.get("output_size_bytes"),
            output_size,
        )
        maximum = size_check.get("max_output_size_bytes")
        if type(maximum) is int and output_size > maximum:
            _issue(
                issues,
                "OUTPUT_EXCEEDS_SIZE_LIMIT",
                "report.size_check.max_output_size_bytes",
                f"output {output_size} exceeds {maximum}",
            )

    selection = report.get("selection_authority")
    if isinstance(selection, Mapping):
        if selection.get("mode") == "locked" and target_count is not None:
            for key in ("query_count", "selected_count", "distinct_query_id_count"):
                _equal(
                    issues,
                    "SELECTION_COUNT_MISMATCH",
                    f"report.selection_authority.{key}",
                    selection.get(key),
                    target_count,
                )
            _equal(
                issues,
                "SELECTION_PAGE_COUNT_MISMATCH",
                "report.selection_authority.distinct_page_id_count",
                selection.get("distinct_page_id_count"),
                distinct_page_ids,
            )
        elif selection.get("mode") == "not_required":
            for key in (
                "query_count",
                "selected_count",
                "distinct_query_id_count",
                "distinct_page_id_count",
            ):
                _equal(
                    issues,
                    "SELECTION_NOT_REQUIRED_NONZERO",
                    f"report.selection_authority.{key}",
                    selection.get(key),
                    0,
                )

    if report.get("acceptance_profile") == "phase49-work-report-15":
        _equal(
            issues,
            "PHASE49_EXPECTED_COUNT_MISMATCH",
            "report.expected_slide_count",
            report.get("expected_slide_count"),
            15,
        )
        _equal(
            issues,
            "PHASE49_TARGET_COUNT_MISMATCH",
            "report.target_slide_count",
            target_count,
            15,
        )
        _equal(
            issues,
            "PHASE49_LINEAGE_COUNT_MISMATCH",
            "report.lineage_records",
            len(lineage),
            15,
        )
        _equal(
            issues,
            "PHASE49_ORDINALS_MISMATCH",
            "report.lineage_records",
            sorted(ordinals),
            list(range(1, 16)),
        )
        _equal(
            issues,
            "PHASE49_PAGE_IDS_NOT_UNIQUE",
            "report.lineage_records",
            distinct_page_ids,
            15,
        )
        residue = report.get("source_residue")
        mutations = (
            residue.get("governed_mutations")
            if isinstance(residue, Mapping)
            else None
        )
        mutation_records = mutations if isinstance(mutations, list) else []
        if isinstance(selection, Mapping):
            _equal(
                issues,
                "PHASE49_LIBRARY_INDEX_SHA256_MISMATCH",
                "report.selection_authority.library_index_sha256",
                selection.get("library_index_sha256"),
                PHASE49_LIBRARY_INDEX_SHA256,
            )
        _equal(
            issues,
            "PHASE49_GOVERNED_INVENTORY_SHA256_MISMATCH",
            "report.source_residue.governed_mutations",
            _governed_inventory_identity_sha256(mutation_records),
            PHASE49_GOVERNED_INVENTORY_SHA256,
        )
        distribution: dict[int, int] = {}
        for record in mutation_records:
            if isinstance(record, Mapping) and type(record.get("ordinal")) is int:
                ordinal = int(record["ordinal"])
                distribution[ordinal] = distribution.get(ordinal, 0) + 1
        _equal(
            issues,
            "PHASE49_GOVERNED_MUTATION_COUNT_MISMATCH",
            "report.source_residue.governed_mutations",
            len(mutation_records),
            101,
        )
        _equal(
            issues,
            "PHASE49_GOVERNED_MUTATION_DISTRIBUTION_MISMATCH",
            "report.source_residue.governed_mutations",
            distribution,
            {5: 22, 6: 52, 7: 27},
        )
    else:
        residue = report.get("source_residue")
        mutation_records = (
            residue.get("governed_mutations")
            if isinstance(residue, Mapping)
            and isinstance(residue.get("governed_mutations"), list)
            else []
        )
        if mutation_records:
            _issue(
                issues,
                "GOVERNED_INVENTORY_PROFILE_UNTRUSTED",
                "report.acceptance_profile",
                "governed embedded mutations require a registered immutable inventory",
            )

    if output_path is not None:
        topology = inspect_presentation_topology(output_path)
        _merge_contract_findings(issues, topology.issues)
        if topology.statistics is not None:
            topology_stats = topology.statistics.to_dict()
            observed["strict_presentation_topology"] = {
                key: value
                for key, value in topology_stats.items()
                if key != "slides"
            }
            if isinstance(editability, Mapping):
                for field, code in (
                    ("slide_count", "EDITABILITY_TOPOLOGY_SLIDE_COUNT_MISMATCH"),
                    ("text_run_count", "EDITABILITY_TOPOLOGY_TEXT_COUNT_MISMATCH"),
                    ("shape_count", "EDITABILITY_TOPOLOGY_SHAPE_COUNT_MISMATCH"),
                    (
                        "native_object_count",
                        "EDITABILITY_TOPOLOGY_NATIVE_OBJECT_COUNT_MISMATCH",
                    ),
                    ("picture_count", "EDITABILITY_TOPOLOGY_PICTURE_COUNT_MISMATCH"),
                    (
                        "native_editable_slide_count",
                        "EDITABILITY_TOPOLOGY_NATIVE_SLIDE_COUNT_MISMATCH",
                    ),
                    (
                        "full_slide_raster_count",
                        "EDITABILITY_TOPOLOGY_FULL_RASTER_COUNT_MISMATCH",
                    ),
                    (
                        "raster_dominant_slide_count",
                        "EDITABILITY_TOPOLOGY_RASTER_DOMINANCE_COUNT_MISMATCH",
                    ),
                    (
                        "native_editable_coverage",
                        "EDITABILITY_TOPOLOGY_COVERAGE_MISMATCH",
                    ),
                ):
                    _equal(
                        issues,
                        code,
                        f"report.editability.{field}",
                        editability.get(field),
                        topology_stats[field],
                    )
            if target_count is not None:
                _equal(
                    issues,
                    "PRESENTATION_TOPOLOGY_TARGET_COUNT_MISMATCH",
                    "output.pptx!/ppt/presentation.xml",
                    topology.statistics.slide_count,
                    target_count,
                )
        if query_authority is not None:
            _merge_contract_findings(
                issues,
                audit_output_text_coverage(
                    output_path,
                    authority=query_authority,
                ),
            )
            _merge_contract_findings(
                issues,
                audit_output_media_authority(
                    output_path,
                    authority=query_authority,
                    asset_sha256_by_ref=(
                        authority_context.get("assets", {})
                        if isinstance(authority_context.get("assets"), Mapping)
                        else {}
                    ),
                    binding_evidence=(
                        binding_evidence
                        if isinstance(binding_evidence, list)
                        else []
                    ),
                ),
            )
            observed["query_authoritative_text_slot_count"] = len(
                query_authority.required_text_keys
            )
            observed["query_authoritative_governed_slot_count"] = len(
                query_authority.required_governed_keys
            )
        try:
            with zipfile.ZipFile(output_path, "r") as archive:
                zip_entry_audit = audit_zip_entries(archive)
                _merge_contract_findings(issues, zip_entry_audit.findings)
                names = archive.namelist()
                relationship_graph = _inspect_opc_relationship_graph(
                    archive,
                    issues,
                )
                reachable_xlsx_parts = sorted(
                    part
                    for part in relationship_graph["reachable_targets"]
                    if isinstance(part, str) and part.lower().endswith(".xlsx")
                )
                for workbook_part in reachable_xlsx_parts:
                    try:
                        audit_governed_xlsx(archive.read(workbook_part))
                    except (KeyError, WorkbookSecurityError, zipfile.BadZipFile) as exc:
                        _issue(
                            issues,
                            "NESTED_WORKBOOK_SECURITY_FAILED",
                            f"output.pptx!/{workbook_part}",
                            str(exc),
                        )
                observed["reachable_xlsx_audited_count"] = len(
                    reachable_xlsx_parts
                )
                content_type_evidence = _inspect_content_types(archive, issues)
                if query_authority is not None:
                    _inspect_query_authoritative_structure(
                        archive,
                        query_authority,
                        issues,
                    )
                observed.update(
                    {
                        "opc_total_relationship_count": relationship_graph[
                            "total_relationship_count"
                        ],
                        "opc_internal_relationship_count": relationship_graph[
                            "internal_relationship_count"
                        ],
                        "opc_external_relationship_count": relationship_graph[
                            "external_relationship_count"
                        ],
                        "opc_unresolved_internal_relationship_count": relationship_graph[
                            "unresolved_internal_relationship_count"
                        ],
                        "opc_unsafe_relationship_count": relationship_graph[
                            "unsafe_relationship_count"
                        ],
                        "opc_reachable_part_count": relationship_graph[
                            "reachable_part_count"
                        ],
                        "opc_unreachable_slide_count": relationship_graph[
                            "unreachable_slide_count"
                        ],
                        "opc_unreachable_part_count": relationship_graph[
                            "unreachable_part_count"
                        ],
                        "opc_content_type_default_count": content_type_evidence[
                            "default_count"
                        ],
                        "opc_content_type_override_count": content_type_evidence[
                            "override_count"
                        ],
                        "opc_content_type_missing_part_count": content_type_evidence[
                            "missing_part_count"
                        ],
                    }
                )
                slide_names = {
                    int(match.group(1)): name
                    for name in names
                    if (match := SLIDE_RE.fullmatch(name))
                }
                observed["pptx_slide_count"] = len(slide_names)
                try:
                    presentation_root = ET.fromstring(
                        archive.read("ppt/presentation.xml")
                    )
                except (KeyError, ET.ParseError) as exc:
                    _issue(
                        issues,
                        "EDITABILITY_PRESENTATION_XML_INVALID",
                        "output.pptx!/ppt/presentation.xml",
                        str(exc),
                    )
                else:
                    if presentation_root.tag.rsplit("}", 1)[-1] != "presentation":
                        _issue(
                            issues,
                            "EDITABILITY_PRESENTATION_ROOT_INVALID",
                            "output.pptx!/ppt/presentation.xml",
                            presentation_root.tag,
                        )
                native_editability = _inspect_native_editability(
                    archive,
                    slide_names,
                    issues,
                )
                observed["native_editability"] = native_editability
                if isinstance(editability, Mapping):
                    for field, code in (
                        ("slide_count", "EDITABILITY_ACTUAL_SLIDE_COUNT_MISMATCH"),
                        (
                            "native_editable_slide_count",
                            "EDITABILITY_ACTUAL_NATIVE_SLIDE_COUNT_MISMATCH",
                        ),
                        (
                            "native_editable_coverage",
                            "EDITABILITY_ACTUAL_COVERAGE_MISMATCH",
                        ),
                        ("picture_count", "EDITABILITY_ACTUAL_PICTURE_COUNT_MISMATCH"),
                    ):
                        _equal(
                            issues,
                            code,
                            f"report.editability.{field}",
                            editability.get(field),
                            native_editability[field],
                        )
                if target_count is not None:
                    _equal(
                        issues,
                        "PPTX_SLIDE_ORDINALS_MISMATCH",
                        "output.pptx",
                        sorted(slide_names),
                        list(range(1, target_count + 1)),
                    )
                for index, record in enumerate(lineage):
                    if not isinstance(record, Mapping):
                        continue
                    ordinal = record.get("ordinal")
                    if type(ordinal) is not int or ordinal not in slide_names:
                        continue
                    actual_slide_sha = hashlib.sha256(
                        archive.read(slide_names[ordinal])
                    ).hexdigest()
                    _equal(
                        issues,
                        "TARGET_SLIDE_SHA256_MISMATCH",
                        f"report.lineage_records.{index}.target_slide_sha256",
                        record.get("target_slide_sha256"),
                        actual_slide_sha,
                    )
                actual_text_by_key: dict[tuple[int, str, str], str] = {}
                validated_text_records: list[
                    tuple[int, Mapping[str, Any], str, tuple[int, str, str]]
                ] = []
                for index, item in enumerate(
                    binding_evidence if isinstance(binding_evidence, list) else []
                ):
                    if not isinstance(item, Mapping) or item.get("binding_kind") != "text":
                        continue
                    ordinal = item.get("ordinal")
                    shape_id = item.get("shape_id")
                    page_id = item.get("page_id")
                    slot_id = item.get("slot_id")
                    if (
                        type(ordinal) is not int
                        or ordinal not in slide_names
                        or type(shape_id) is not int
                        or not isinstance(page_id, str)
                        or not isinstance(slot_id, str)
                    ):
                        _issue(
                            issues,
                            "BINDING_OUTPUT_TEXT_SLOT_INVALID",
                            f"report.binding_evidence.{index}",
                            f"ordinal={ordinal}, shape_id={shape_id}",
                        )
                        continue
                    try:
                        actual_text = _read_slide_shape_text(
                            archive.read(slide_names[ordinal]),
                            shape_id,
                        )
                    except (KeyError, ValueError, ET.ParseError) as exc:
                        _issue(
                            issues,
                            "BINDING_OUTPUT_TEXT_SLOT_INVALID",
                            f"report.binding_evidence.{index}",
                            str(exc),
                        )
                        continue
                    key = (ordinal, page_id, slot_id)
                    actual_text_by_key[key] = actual_text
                    validated_text_records.append(
                        (index, item, actual_text, key)
                    )
                authorized_character_keys: frozenset[
                    tuple[int, str, str]
                ] = frozenset()
                if query_authority is not None:
                    fragment_result = validate_fragment_group_fact_authority(
                        query_authority,
                        binding_evidence=(
                            binding_evidence
                            if isinstance(binding_evidence, list)
                            else []
                        ),
                        actual_text_by_key=actual_text_by_key,
                        facts_by_id=authority_context.get("facts", {}),
                        connectives_by_id=authority_context.get("connectives", {}),
                    )
                    for finding in fragment_result.findings:
                        _issue(
                            issues,
                            finding.code,
                            finding.location,
                            finding.detail,
                        )
                    authorized_character_keys = (
                        fragment_result.authorized_character_keys
                    )
                for index, item, actual_text, key in validated_text_records:
                    if key in authorized_character_keys:
                        continue
                    _validate_binding_value_authority(
                        item,
                        actual_text,
                        authority_context,
                        issues,
                        f"report.binding_evidence.{index}",
                    )
                if isinstance(opc, Mapping):
                    _equal(
                        issues,
                        "PACKAGE_ENTRY_COUNT_MISMATCH",
                        "report.opc_integrity.package_entry_count",
                        opc.get("package_entry_count"),
                        len(names),
                    )
                    _equal(
                        issues,
                        "PACKAGE_MEDIA_COUNT_MISMATCH",
                        "report.opc_integrity.media_count",
                        opc.get("media_count"),
                        sum(1 for name in names if "media/" in name),
                    )
                    for field, code in (
                        (
                            "total_relationship_count",
                            "OPC_TOTAL_RELATIONSHIP_COUNT_ACTUAL_MISMATCH",
                        ),
                        (
                            "internal_relationship_count",
                            "OPC_INTERNAL_RELATIONSHIP_COUNT_ACTUAL_MISMATCH",
                        ),
                        (
                            "external_relationship_count",
                            "OPC_EXTERNAL_RELATIONSHIP_COUNT_ACTUAL_MISMATCH",
                        ),
                        (
                            "unresolved_internal_relationship_count",
                            "OPC_UNRESOLVED_COUNT_ACTUAL_MISMATCH",
                        ),
                        (
                            "unsafe_relationship_count",
                            "OPC_UNSAFE_COUNT_ACTUAL_MISMATCH",
                        ),
                    ):
                        _equal(
                            issues,
                            code,
                            f"report.opc_integrity.{field}",
                            opc.get(field),
                            relationship_graph[field],
                        )
                residue = report.get("source_residue")
                if isinstance(residue, Mapping):
                    _equal(
                        issues,
                        "TAG_PART_COUNT_MISMATCH",
                        "report.source_residue.tag_part_count",
                        residue.get("tag_part_count"),
                        sum(1 for name in names if "/tags/" in name.lower()),
                    )
                    _equal(
                        issues,
                        "TAG_RELATIONSHIP_COUNT_MISMATCH",
                        "report.source_residue.tag_relationship_count",
                        residue.get("tag_relationship_count"),
                        relationship_graph["reachable_tag_relationship_count"],
                    )
                    media_names = {
                        name.replace("\\", "/")
                        for name in names
                        if name.replace("\\", "/").startswith("ppt/")
                        and "/media/" in name.replace("\\", "/")
                    }
                    _equal(
                        issues,
                        "ORPHAN_MEDIA_COUNT_MISMATCH",
                        "report.source_residue.orphan_media_count",
                        residue.get("orphan_media_count"),
                        len(
                            media_names
                            - relationship_graph["reachable_targets"]
                        ),
                    )
                    embedded_by_key = {
                        (
                            item.get("ordinal"),
                            item.get("page_id"),
                            item.get("slot_id"),
                        ): item
                        for item in (
                            binding_evidence
                            if isinstance(binding_evidence, list)
                            else []
                        )
                        if isinstance(item, Mapping)
                        and item.get("binding_kind") == "embedded"
                    }
                    governed_output_mismatches = 0
                    peer_values: dict[tuple[int, str], set[tuple[str, str]]] = {}
                    peer_counts: dict[tuple[int, str], int] = {}
                    mutations = residue.get("governed_mutations")
                    mutation_records = mutations if isinstance(mutations, list) else []
                    for index, mutation in enumerate(mutation_records):
                        if not isinstance(mutation, Mapping):
                            governed_output_mismatches += 1
                            continue
                        target_part = mutation.get("target_part")
                        locator = mutation.get("locator")
                        kind = mutation.get("kind")
                        key = (
                            mutation.get("ordinal"),
                            mutation.get("page_id"),
                            mutation.get("slot_id"),
                        )
                        evidence = embedded_by_key.get(key)
                        if (
                            not isinstance(target_part, str)
                            or target_part not in names
                            or target_part not in relationship_graph["reachable_targets"]
                            or not isinstance(locator, str)
                            or not isinstance(kind, str)
                            or evidence is None
                        ):
                            governed_output_mismatches += 1
                            continue
                        try:
                            ordinal = mutation.get("ordinal")
                            if type(ordinal) is not int:
                                raise ValueError("governed ordinal is invalid")
                            relationship_lineage = _actual_governed_target(
                                archive,
                                ordinal=ordinal,
                                kind=kind,
                                locator=locator,
                            )
                            lineage_fields = (
                                "slide_part",
                                "shape_id",
                                "slide_relationship_id",
                                "chart_part",
                                "chart_relationship_id",
                                "target_part",
                                "target_part_sha256",
                            )
                            lineage_mismatches = [
                                field
                                for field in lineage_fields
                                if mutation.get(field) != relationship_lineage[field]
                            ]
                            if relationship_lineage["shape_id"] != evidence.get(
                                "shape_id"
                            ):
                                lineage_mismatches.append("binding_evidence.shape_id")
                            if lineage_mismatches:
                                governed_output_mismatches += 1
                                _issue(
                                    issues,
                                    "GOVERNED_ACTUAL_TARGET_MISMATCH",
                                    f"report.source_residue.governed_mutations.{index}",
                                    (
                                        f"reported={target_part} "
                                        f"actual={relationship_lineage['target_part']} "
                                        f"fields={','.join(lineage_mismatches)}"
                                    ),
                                )
                                continue
                            part_bytes = archive.read(target_part)
                            actual = (
                                read_governed_xlsx_slot(part_bytes, locator)
                                if kind == "workbook-cell"
                                else _read_governed_xml_value(
                                    part_bytes,
                                    kind=kind,
                                    locator=locator,
                                )
                            )
                        except (
                            KeyError,
                            ValueError,
                            ET.ParseError,
                            WorkbookSecurityError,
                        ):
                            governed_output_mismatches += 1
                            continue
                        actual_sha = hashlib.sha256(actual.encode("utf-8")).hexdigest()
                        if (
                            actual_sha != mutation.get("actual_sha256")
                            or actual_sha != evidence.get("replacement_sha256")
                        ):
                            governed_output_mismatches += 1
                            _issue(
                                issues,
                                "GOVERNED_OUTPUT_VALUE_MISMATCH",
                                f"report.source_residue.governed_mutations.{index}",
                                str(target_part),
                            )
                        _validate_binding_value_authority(
                            evidence,
                            actual,
                            authority_context,
                            issues,
                            f"report.source_residue.governed_mutations.{index}",
                        )
                        peer_group_id = mutation.get("peer_group_id")
                        ordinal = mutation.get("ordinal")
                        if (
                            isinstance(peer_group_id, str)
                            and peer_group_id
                            and type(ordinal) is int
                        ):
                            peer_key = (ordinal, peer_group_id)
                            numeric = _decimal_literal(actual)
                            peer_value = (
                                (
                                    "number",
                                    format(
                                        (
                                            numeric[0] / Decimal(100)
                                            if numeric[1]
                                            else numeric[0]
                                        ).normalize(),
                                        "f",
                                    ),
                                )
                                if numeric is not None
                                else ("text", _normalise_authority_text(actual))
                            )
                            peer_values.setdefault(peer_key, set()).add(peer_value)
                            peer_counts[peer_key] = peer_counts.get(peer_key, 0) + 1
                    _equal(
                        issues,
                        "GOVERNED_OUTPUT_MISMATCH_COUNT",
                        "report.source_residue.governed_content_mismatch_count",
                        residue.get("governed_content_mismatch_count"),
                        governed_output_mismatches,
                    )
                    peer_group_mismatches = sum(
                        1
                        for key, values in peer_values.items()
                        if len(values) != 1 or peer_counts.get(key) != 2
                    )
                    if peer_group_mismatches:
                        _issue(
                            issues,
                            "GOVERNED_PEER_GROUP_ACTUAL_MISMATCH",
                            "report.source_residue.governed_mutations",
                            str(peer_group_mismatches),
                        )
                    _equal(
                        issues,
                        "GOVERNED_PEER_GROUP_MISMATCH_COUNT",
                        "report.source_residue.peer_group_mismatch_count",
                        residue.get("peer_group_mismatch_count"),
                        peer_group_mismatches,
                    )
                    asset_slot_mismatches = 0
                    asset_hash_mismatches = 0
                    asset_items = [
                        item
                        for item in (
                            binding_evidence
                            if isinstance(binding_evidence, list)
                            else []
                        )
                        if isinstance(item, Mapping)
                        and item.get("binding_kind") == "asset"
                    ]
                    for index, item in enumerate(asset_items):
                        ordinal = item.get("ordinal")
                        slot_id = item.get("slot_id")
                        shape_id = item.get("shape_id")
                        expected_rid = item.get("relationship_id")
                        expected_target = item.get("target_part")
                        expected_sha = item.get("replacement_sha256")
                        slide_name = (
                            f"ppt/slides/slide{ordinal}.xml"
                            if type(ordinal) is int
                            else ""
                        )
                        rels_name = (
                            f"ppt/slides/_rels/slide{ordinal}.xml.rels"
                            if type(ordinal) is int
                            else ""
                        )
                        slot_binding: tuple[int, str] | None = None
                        try:
                            slide_root = ET.fromstring(archive.read(slide_name))
                            for picture in slide_root.iter():
                                if picture.tag.rsplit("}", 1)[-1] != "pic":
                                    continue
                                marker = next(
                                    (
                                        node
                                        for node in picture.iter()
                                        if node.tag.rsplit("}", 1)[-1] == "cNvPr"
                                    ),
                                    None,
                                )
                                blip = next(
                                    (
                                        node
                                        for node in picture.iter()
                                        if node.tag.rsplit("}", 1)[-1] == "blip"
                                    ),
                                    None,
                                )
                                if marker is None or blip is None:
                                    continue
                                raw_id = marker.attrib.get("id", "")
                                embed = next(
                                    (
                                        value
                                        for key, value in blip.attrib.items()
                                        if key.rsplit("}", 1)[-1] == "embed"
                                    ),
                                    "",
                                )
                                if f"shape_{raw_id}" == slot_id and raw_id.isdigit():
                                    slot_binding = (int(raw_id), embed)
                                    break
                        except (KeyError, ET.ParseError):
                            slot_binding = None
                        parsed_rels = (
                            _parse_relationship_part(
                                archive,
                                rels_name,
                                rels_name,
                                issues,
                            )
                            if rels_name in names
                            else None
                        )
                        relation = next(
                            (
                                entry
                                for entry in (parsed_rels or [])
                                if entry.get("Id") == expected_rid
                            ),
                            None,
                        )
                        actual_target = (
                            _resolve_relationship_target(
                                rels_name,
                                relation.get("Target", ""),
                            )
                            if relation is not None
                            else None
                        )
                        if (
                            slot_binding != (shape_id, expected_rid)
                            or relation is None
                            or not relation.get("Type", "").lower().endswith("/image")
                            or actual_target != expected_target
                            or actual_target not in names
                        ):
                            asset_slot_mismatches += 1
                            _issue(
                                issues,
                                "ASSET_SLOT_BINDING_MISMATCH",
                                f"report.binding_evidence.asset.{index}",
                                f"{slide_name}:{slot_id}",
                            )
                            continue
                        if hashlib.sha256(archive.read(actual_target)).hexdigest() != expected_sha:
                            asset_hash_mismatches += 1
                            _issue(
                                issues,
                                "ASSET_TARGET_SHA256_MISMATCH",
                                f"report.binding_evidence.asset.{index}",
                                str(actual_target),
                            )
                    _equal(
                        issues,
                        "ASSET_SLOT_MISMATCH_COUNT",
                        "report.source_residue.asset_slot_mismatch_count",
                        residue.get("asset_slot_mismatch_count"),
                        asset_slot_mismatches,
                    )
                    _equal(
                        issues,
                        "ASSET_HASH_MISMATCH_COUNT",
                        "report.source_residue.replacement_asset_hash_mismatch_count",
                        residue.get("replacement_asset_hash_mismatch_count"),
                        asset_hash_mismatches,
                    )
                    cached_fields = 0
                    for name in names:
                        if not (
                            name.endswith(".xml")
                            and (
                                "/slideLayouts/" in name
                                or "/slideMasters/" in name
                            )
                        ):
                            continue
                        try:
                            root = ET.fromstring(archive.read(name))
                        except ET.ParseError:
                            cached_fields += 1
                            continue
                        for field in root.iter():
                            if field.tag.rsplit("}", 1)[-1] != "fld":
                                continue
                            if any(
                                node.tag.rsplit("}", 1)[-1] == "t"
                                and bool((node.text or "").strip())
                                for node in field.iter()
                            ):
                                cached_fields += 1
                    _equal(
                        issues,
                        "LAYOUT_MASTER_CACHE_COUNT_MISMATCH",
                        "report.source_residue.layout_master_cached_field_count",
                        residue.get("layout_master_cached_field_count"),
                        cached_fields,
                    )
                if isinstance(metrics, Mapping) and isinstance(
                    metrics.get("imported_parts"), list
                ):
                    _equal(
                        issues,
                        "ASSEMBLY_OPC_UNRESOLVED_ACTUAL_MISMATCH",
                        "report.assembly_metrics.unresolved_internal_relationship_count",
                        metrics.get("unresolved_internal_relationship_count"),
                        relationship_graph[
                            "unresolved_internal_relationship_count"
                        ],
                    )
                    missing_parts = sorted(set(metrics["imported_parts"]) - set(names))
                    if missing_parts:
                        _issue(
                            issues,
                            "IMPORTED_PART_MISSING",
                            "report.assembly_metrics.imported_parts",
                            ",".join(missing_parts),
                        )
        except (OSError, zipfile.BadZipFile) as exc:
            _issue(issues, "OUTPUT_NOT_VALID_ZIP", "output.pptx", str(exc))

    return observed


def validate_physical_report(
    report_path: str | os.PathLike[str],
    project_root: str | os.PathLike[str],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    root = _root_path(project_root, issues)
    resolved_report: Path | None = None
    payload: Any | None = None
    output_path: Path | None = None
    output_sha256: str | None = None
    output_size: int | None = None
    authority_context: dict[str, Any] = {
        "facts": {},
        "assets": {},
        "connectives": {},
    }
    query_authority: QueryCoverageAuthority | None = None
    observed: dict[str, Any] = {}
    if root is not None:
        resolved_report = _resolve_report_argument(report_path, root, issues)
    if resolved_report is not None:
        payload = _read_json(resolved_report, issues, "report")
    if payload is not None:
        _validate_schema(payload, issues)
    if root is not None and isinstance(payload, Mapping):
        output_path = _resolve_bound_absolute_file(
            payload.get("output_path"),
            root,
            issues,
            "report.output_path",
        )
        if output_path is not None:
            try:
                output_sha256, output_size = _sha256_and_size(output_path)
            except OSError as exc:
                _issue(issues, "OUTPUT_READ_FAILED", "report.output_path", str(exc))
            else:
                _equal(
                    issues,
                    "OUTPUT_SHA256_MISMATCH",
                    "report.output_sha256",
                    payload.get("output_sha256"),
                    output_sha256,
                )

        authority = payload.get("authority")
        if isinstance(authority, Mapping) and authority.get("mode") == "locked":
            authority_paths: dict[str, Path | None] = {}
            for name in ("fact_store", "asset_manifest", "connective_copy"):
                bound_path = _resolve_bound_absolute_file(
                    authority.get(f"{name}_path"),
                    root,
                    issues,
                    f"report.authority.{name}_path",
                )
                authority_paths[name] = bound_path
                _verify_bound_hash(
                    bound_path,
                    authority.get(f"{name}_sha256"),
                    issues,
                    f"report.authority.{name}_sha256",
                )
            authority_context = {
                "facts": _validate_fact_store_authority(
                    authority_paths.get("fact_store"),
                    issues,
                ),
                "assets": _validate_asset_manifest_authority(
                    authority_paths.get("asset_manifest"),
                    root,
                    issues,
                ),
                "connectives": _validate_connective_copy_authority(
                    authority_paths.get("connective_copy"),
                    issues,
                ),
            }
            _validate_binding_authority_metadata(
                payload,
                authority_context,
                issues,
            )

        selection = payload.get("selection_authority")
        if isinstance(selection, Mapping) and selection.get("mode") == "locked":
            query_path = _resolve_bound_absolute_file(
                selection.get("query_bundle_path"),
                root,
                issues,
                "report.selection_authority.query_bundle_path",
            )
            _verify_bound_hash(
                query_path,
                selection.get("query_bundle_sha256"),
                issues,
                "report.selection_authority.query_bundle_sha256",
            )
            query_payload = (
                _read_json(query_path, issues, "query_bundle")
                if query_path is not None
                else None
            )
            if isinstance(query_payload, Mapping):
                residue = payload.get("source_residue")
                mutations = (
                    residue.get("governed_mutations")
                    if isinstance(residue, Mapping)
                    and isinstance(residue.get("governed_mutations"), list)
                    else []
                )
                coverage = validate_query_bundle_and_coverage(
                    query_payload,
                    lineage_records=(
                        payload.get("lineage_records")
                        if isinstance(payload.get("lineage_records"), list)
                        else []
                    ),
                    binding_evidence=(
                        payload.get("binding_evidence")
                        if isinstance(payload.get("binding_evidence"), list)
                        else []
                    ),
                    governed_mutations=mutations,
                    expected_library_index_sha256=(
                        selection.get("library_index_sha256")
                        if isinstance(selection.get("library_index_sha256"), str)
                        else None
                    ),
                )
                for finding in coverage.findings:
                    _issue(
                        issues,
                        finding.code,
                        finding.location,
                        finding.detail,
                    )
                query_authority = coverage.authority

        observed = _validate_cross_fields(
            payload,
            output_path,
            output_sha256,
            output_size,
            authority_context,
            query_authority,
            issues,
        )

    issues.sort(key=lambda item: (item["location"], item["code"], item["detail"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "validator_id": VALIDATOR_ID,
        "status": "pass" if not issues else "fail",
        "project_root": str(root) if root is not None else "",
        "report_path": str(resolved_report) if resolved_report is not None else "",
        "observed": observed,
        "issue_count": len(issues),
        "issues": issues,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = validate_physical_report(args.report, args.project_root)
    except Exception as exc:  # pragma: no cover - final fail-closed boundary
        result = {
            "schema_version": SCHEMA_VERSION,
            "validator_id": VALIDATOR_ID,
            "status": "fail",
            "project_root": "",
            "report_path": "",
            "observed": {},
            "issue_count": 1,
            "issues": [
                {
                    "code": "VALIDATOR_INTERNAL_ERROR",
                    "location": "validator",
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            ],
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
