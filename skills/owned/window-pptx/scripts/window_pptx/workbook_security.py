"""Fail-closed sanitizer for editable chart-data XLSX packages.

Embedded workbooks are nested OPC packages.  Treating their bytes as an
opaque chart dependency leaves a second relationship graph, stale shared
strings, and potentially active content outside the presentation-level audit.
This module accepts only the small, native-editable data-workbook subset that
PowerPoint charts need, converts every string cell to inline text, applies a
complete governed-cell replacement set, removes metadata/shared-string/calculation
residue, and rebuilds a root-reachable deterministic package.
"""

from __future__ import annotations

import hashlib
import io
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import deque
from decimal import Decimal, InvalidOperation
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence

from .independent_validation_security import (
    ZipResourceLimits,
    audit_zip_resources,
)


REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
SS_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
OFFICE_REL_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
ET.register_namespace("", REL_NS)

_LOCATOR_RE = re.compile(
    r"^chartFrame\[id=(\d+)\]/(xl/worksheets/[^!]+\.xml)!([^!]+)$"
)
_CELL_RE = re.compile(r"^[A-Za-z]{1,3}[1-9][0-9]{0,6}$")
_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?")
_FORBIDDEN_PART_FRAGMENTS = (
    "vbaproject",
    "activex",
    "oleobjects",
    "externallinks",
    "connections.xml",
    "customui",
    "webextensions",
    "embeddings/",
    "macrosheets/",
    "dialogsheets/",
    "ctrlprops/",
    "model/",
    "slicercaches/",
)
_FORBIDDEN_REL_TYPE_FRAGMENTS = (
    "vbaproject",
    "activex",
    "oleobject",
    "externallink",
    "connection",
    "attachedtemplate",
    "control",
)
_REMOVABLE_REL_TYPE_SUFFIXES = (
    "/metadata/core-properties",
    "/extended-properties",
    "/custom-properties",
    "/thumbnail",
    "/calcchain",
)
_EXPECTED_CONTENT_TYPES = {
    "xl/workbook.xml": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
    ),
    "xl/styles.xml": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"
    ),
    "xl/sharedStrings.xml": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"
    ),
    "docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
    "docProps/app.xml": (
        "application/vnd.openxmlformats-officedocument.extended-properties+xml"
    ),
    "docProps/custom.xml": (
        "application/vnd.openxmlformats-officedocument.custom-properties+xml"
    ),
}
_WORKSHEET_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"
)
_TABLE_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml"
)
_THEME_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.theme+xml"
_RELS_CONTENT_TYPE = "application/vnd.openxmlformats-package.relationships+xml"

WORKBOOK_ZIP_RESOURCE_LIMITS = ZipResourceLimits(
    max_entries=2_048,
    max_entry_uncompressed_bytes=32 * 1024 * 1024,
    max_total_uncompressed_bytes=128 * 1024 * 1024,
    max_compression_ratio=100.0,
    max_xml_uncompressed_bytes=16 * 1024 * 1024,
    max_relationship_uncompressed_bytes=4 * 1024 * 1024,
)


class WorkbookSecurityError(ValueError):
    """Raised when a nested workbook is outside the governed safe subset."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalise_part_name(name: str) -> str:
    if not name or "\\" in name or name.startswith("/") or "\0" in name:
        raise WorkbookSecurityError(f"WORKBOOK_PART_NAME_INVALID: {name!r}")
    path = PurePosixPath(name)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise WorkbookSecurityError(f"WORKBOOK_PART_NAME_INVALID: {name!r}")
    normalised = path.as_posix()
    if posixpath.normpath(normalised) != normalised:
        raise WorkbookSecurityError(f"WORKBOOK_PART_NAME_INVALID: {name!r}")
    return normalised


def _owner_part(rels_path: str) -> str | None:
    if rels_path == "_rels/.rels":
        return None
    parts = rels_path.split("/")
    if len(parts) < 2 or parts[-2] != "_rels" or not parts[-1].endswith(".rels"):
        raise WorkbookSecurityError(f"WORKBOOK_RELS_PATH_INVALID: {rels_path}")
    return "/".join(parts[:-2] + [parts[-1][:-5]])


def _rels_path(owner: str) -> str:
    folder, filename = posixpath.split(owner)
    return posixpath.join(folder, "_rels", f"{filename}.rels")


def _resolve_target(rels_path: str, target: str) -> str:
    if not target or target.startswith("/") or "\\" in target or "\0" in target:
        raise WorkbookSecurityError(
            f"WORKBOOK_RELATIONSHIP_TARGET_INVALID: {rels_path}->{target!r}"
        )
    owner = _owner_part(rels_path)
    base = posixpath.dirname(owner) if owner else ""
    resolved = posixpath.normpath(posixpath.join(base, target)).lstrip("/")
    if resolved == ".." or resolved.startswith("../"):
        raise WorkbookSecurityError(
            f"WORKBOOK_RELATIONSHIP_TARGET_ESCAPE: {rels_path}->{target}"
        )
    return resolved


def _parse_relationships(data: bytes, rels_path: str) -> list[dict[str, str]]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise WorkbookSecurityError(
            f"WORKBOOK_RELATIONSHIPS_XML_INVALID: {rels_path}"
        ) from exc
    if root.tag != f"{{{REL_NS}}}Relationships":
        raise WorkbookSecurityError(
            f"WORKBOOK_RELATIONSHIPS_NAMESPACE_INVALID: {rels_path}"
        )
    entries: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for child in list(root):
        if child.tag != f"{{{REL_NS}}}Relationship":
            raise WorkbookSecurityError(
                f"WORKBOOK_RELATIONSHIP_ELEMENT_INVALID: {rels_path}"
            )
        unknown = set(child.attrib) - {"Id", "Type", "Target", "TargetMode"}
        if unknown:
            raise WorkbookSecurityError(
                f"WORKBOOK_RELATIONSHIP_ATTRIBUTE_INVALID: {rels_path}"
            )
        entry = {
            "Id": child.attrib.get("Id", ""),
            "Type": child.attrib.get("Type", ""),
            "Target": child.attrib.get("Target", ""),
            "TargetMode": child.attrib.get("TargetMode", "Internal"),
        }
        if not entry["Id"] or not entry["Type"] or not entry["Target"]:
            raise WorkbookSecurityError(
                f"WORKBOOK_RELATIONSHIP_REQUIRED_ATTRIBUTE_MISSING: {rels_path}"
            )
        if entry["Id"] in seen_ids:
            raise WorkbookSecurityError(
                f"WORKBOOK_RELATIONSHIP_ID_DUPLICATE: {rels_path}:{entry['Id']}"
            )
        seen_ids.add(entry["Id"])
        if entry["TargetMode"].lower() not in {"internal", "external"}:
            raise WorkbookSecurityError(
                f"WORKBOOK_RELATIONSHIP_MODE_INVALID: {rels_path}:{entry['Id']}"
            )
        entries.append(entry)
    return entries


def _serialize_relationships(entries: Sequence[Mapping[str, str]]) -> bytes:
    root = ET.Element(f"{{{REL_NS}}}Relationships")
    for entry in sorted(entries, key=lambda value: value["Id"]):
        attributes = {
            "Id": entry["Id"],
            "Type": entry["Type"],
            "Target": entry["Target"],
        }
        if entry.get("TargetMode", "Internal").lower() == "external":
            attributes["TargetMode"] = "External"
        ET.SubElement(root, f"{{{REL_NS}}}Relationship", attributes)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _load_parts(package_bytes: bytes) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(io.BytesIO(package_bytes), "r") as archive:
            resource_findings = audit_zip_resources(
                archive,
                limits=WORKBOOK_ZIP_RESOURCE_LIMITS,
            )
            if resource_findings:
                raise WorkbookSecurityError(
                    "WORKBOOK_PACKAGE_RESOURCE_LIMIT: "
                    + ";".join(
                        f"{finding.code}@{finding.location}:{finding.detail}"
                        for finding in resource_findings
                    )
                )
            raw_names = archive.namelist()
            if len(raw_names) != len(set(raw_names)):
                raise WorkbookSecurityError("WORKBOOK_DUPLICATE_ZIP_ENTRY")
            parts = {
                _normalise_part_name(name): archive.read(name)
                for name in raw_names
            }
    except WorkbookSecurityError:
        raise
    except (OSError, zipfile.BadZipFile) as exc:
        raise WorkbookSecurityError("WORKBOOK_PACKAGE_INVALID") from exc
    required = {"[Content_Types].xml", "_rels/.rels", "xl/workbook.xml"}
    missing = sorted(required - set(parts))
    if missing:
        raise WorkbookSecurityError(
            "WORKBOOK_REQUIRED_PART_MISSING: " + ",".join(missing)
        )
    for name in parts:
        lower = name.lower()
        if lower.endswith((".bin", ".vba", ".exe", ".dll", ".js", ".vbs")) or any(
            fragment in lower for fragment in _FORBIDDEN_PART_FRAGMENTS
        ):
            raise WorkbookSecurityError(f"WORKBOOK_ACTIVE_PART_FORBIDDEN: {name}")
        allowed = (
            name in {
                "[Content_Types].xml",
                "_rels/.rels",
                "xl/workbook.xml",
                "xl/_rels/workbook.xml.rels",
                "xl/styles.xml",
                "xl/sharedStrings.xml",
                "xl/calcChain.xml",
                "docProps/core.xml",
                "docProps/app.xml",
                "docProps/custom.xml",
            }
            or re.fullmatch(r"xl/worksheets/sheet[1-9][0-9]*\.xml", name)
            or re.fullmatch(r"xl/tables/table[1-9][0-9]*\.xml", name)
            or re.fullmatch(r"xl/theme/theme[1-9][0-9]*\.xml", name)
            or re.fullmatch(r"(?:docProps|xl/worksheets|xl/theme)/_rels/[^/]+\.rels", name)
        )
        if not allowed:
            raise WorkbookSecurityError(f"WORKBOOK_PART_UNSUPPORTED: {name}")
    return parts


def _audit_relationship_graph(parts: Mapping[str, bytes]) -> None:
    for rels_path in sorted(name for name in parts if name.endswith(".rels")):
        for entry in _parse_relationships(parts[rels_path], rels_path):
            rel_type = entry["Type"].lower()
            target = entry["Target"]
            if (
                any(fragment in rel_type for fragment in _FORBIDDEN_REL_TYPE_FRAGMENTS)
                or rel_type.rstrip("/").endswith("/package")
            ):
                raise WorkbookSecurityError(
                    f"WORKBOOK_RELATIONSHIP_TYPE_FORBIDDEN: {rels_path}:{entry['Id']}"
                )
            if entry["TargetMode"].lower() == "external" or "://" in target or target.lower().startswith("file:"):
                raise WorkbookSecurityError(
                    f"WORKBOOK_EXTERNAL_RELATIONSHIP_FORBIDDEN: {rels_path}:{entry['Id']}"
                )
            resolved = _resolve_target(rels_path, target)
            if resolved not in parts:
                raise WorkbookSecurityError(
                    f"WORKBOOK_RELATIONSHIP_TARGET_MISSING: {rels_path}->{resolved}"
                )


def _content_type_map(parts: Mapping[str, bytes]) -> dict[str, str]:
    try:
        root = ET.fromstring(parts["[Content_Types].xml"])
    except (KeyError, ET.ParseError) as exc:
        raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPES_INVALID") from exc
    if root.tag != f"{{{CT_NS}}}Types":
        raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPES_NAMESPACE_INVALID")
    defaults: dict[str, str] = {}
    overrides: dict[str, str] = {}
    for child in list(root):
        if child.tag == f"{{{CT_NS}}}Default":
            if set(child.attrib) != {"Extension", "ContentType"}:
                raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPE_ATTRIBUTE_INVALID")
            extension = child.attrib["Extension"].lower().lstrip(".")
            content_type = child.attrib["ContentType"]
            if not extension or not content_type or extension in defaults:
                raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPE_DEFAULT_INVALID")
            defaults[extension] = content_type
            continue
        if child.tag == f"{{{CT_NS}}}Override":
            if set(child.attrib) != {"PartName", "ContentType"}:
                raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPE_ATTRIBUTE_INVALID")
            raw_part = child.attrib["PartName"]
            if not raw_part.startswith("/") or raw_part.startswith("//"):
                raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPE_OVERRIDE_INVALID")
            part = _normalise_part_name(raw_part[1:])
            content_type = child.attrib["ContentType"]
            if not content_type or part in overrides:
                raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPE_OVERRIDE_INVALID")
            overrides[part] = content_type
            continue
        raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPE_ELEMENT_INVALID")
    if defaults.get("rels") != _RELS_CONTENT_TYPE:
        raise WorkbookSecurityError("WORKBOOK_RELATIONSHIP_CONTENT_TYPE_INVALID")
    result: dict[str, str] = {}
    for part in parts:
        if part in {"[Content_Types].xml"}:
            continue
        content_type = overrides.get(part)
        if content_type is None:
            extension = part.rsplit(".", 1)[-1].lower() if "." in part else ""
            content_type = defaults.get(extension, "")
        if not content_type:
            raise WorkbookSecurityError(
                f"WORKBOOK_CONTENT_TYPE_MISSING: {part}"
            )
        lowered = content_type.lower()
        if "macroenabled" in lowered or "vbaproject" in lowered:
            raise WorkbookSecurityError("WORKBOOK_MACRO_CONTENT_TYPE_FORBIDDEN")
        result[part] = content_type
    stale = sorted(set(overrides) - set(parts))
    if stale:
        raise WorkbookSecurityError(
            "WORKBOOK_CONTENT_TYPE_TARGET_MISSING: " + ",".join(stale)
        )
    return result


def _validate_content_types(parts: Mapping[str, bytes]) -> None:
    content_types = _content_type_map(parts)
    for part, expected in _EXPECTED_CONTENT_TYPES.items():
        if part in parts and content_types.get(part) != expected:
            raise WorkbookSecurityError(
                f"WORKBOOK_CONTENT_TYPE_INVALID: {part}"
            )
    for part in parts:
        if re.fullmatch(r"xl/worksheets/sheet[1-9][0-9]*\.xml", part):
            expected = _WORKSHEET_CONTENT_TYPE
        elif re.fullmatch(r"xl/tables/table[1-9][0-9]*\.xml", part):
            expected = _TABLE_CONTENT_TYPE
        elif re.fullmatch(r"xl/theme/theme[1-9][0-9]*\.xml", part):
            expected = _THEME_CONTENT_TYPE
        else:
            continue
        if content_types.get(part) != expected:
            raise WorkbookSecurityError(
                f"WORKBOOK_CONTENT_TYPE_INVALID: {part}"
            )


def _xml_root(parts: Mapping[str, bytes], part: str) -> ET.Element:
    try:
        return ET.fromstring(parts[part])
    except (KeyError, ET.ParseError) as exc:
        raise WorkbookSecurityError(f"WORKBOOK_XML_PART_INVALID: {part}") from exc


def _validate_xml_roots(parts: Mapping[str, bytes]) -> None:
    expected_roots: dict[str, str] = {
        "xl/workbook.xml": f"{{{SS_NS}}}workbook",
        "xl/styles.xml": f"{{{SS_NS}}}styleSheet",
        "xl/sharedStrings.xml": f"{{{SS_NS}}}sst",
    }
    for part in parts:
        if re.fullmatch(r"xl/worksheets/sheet[1-9][0-9]*\.xml", part):
            expected_roots[part] = f"{{{SS_NS}}}worksheet"
        elif re.fullmatch(r"xl/tables/table[1-9][0-9]*\.xml", part):
            expected_roots[part] = f"{{{SS_NS}}}table"
        elif re.fullmatch(r"xl/theme/theme[1-9][0-9]*\.xml", part):
            expected_roots[part] = f"{{{DML_NS}}}theme"
    for part, expected_root in expected_roots.items():
        if part in parts and _xml_root(parts, part).tag != expected_root:
            raise WorkbookSecurityError(f"WORKBOOK_XML_ROOT_INVALID: {part}")


def _validate_package_root(parts: Mapping[str, bytes]) -> None:
    relationships = _parse_relationships(parts["_rels/.rels"], "_rels/.rels")
    office_documents = [
        entry
        for entry in relationships
        if entry["Type"].rstrip("/") == f"{OFFICE_REL_NS}/officeDocument"
    ]
    if len(office_documents) != 1:
        raise WorkbookSecurityError("WORKBOOK_ROOT_OFFICE_DOCUMENT_COUNT_INVALID")
    relationship = office_documents[0]
    if relationship["TargetMode"].lower() != "internal":
        raise WorkbookSecurityError("WORKBOOK_ROOT_OFFICE_DOCUMENT_EXTERNAL")
    if _resolve_target("_rels/.rels", relationship["Target"]) != "xl/workbook.xml":
        raise WorkbookSecurityError("WORKBOOK_ROOT_OFFICE_DOCUMENT_TARGET_INVALID")


def _validate_sheet_relationships(parts: Mapping[str, bytes]) -> None:
    workbook_root = _xml_root(parts, "xl/workbook.xml")
    if workbook_root.tag != f"{{{SS_NS}}}workbook":
        raise WorkbookSecurityError("WORKBOOK_XML_ROOT_INVALID: xl/workbook.xml")
    sheets_nodes = workbook_root.findall(f"{{{SS_NS}}}sheets")
    if len(sheets_nodes) != 1:
        raise WorkbookSecurityError("WORKBOOK_SHEETS_CONTAINER_INVALID")
    sheets = list(sheets_nodes[0])
    if not sheets or any(sheet.tag != f"{{{SS_NS}}}sheet" for sheet in sheets):
        raise WorkbookSecurityError("WORKBOOK_SHEET_ELEMENT_INVALID")

    rels_path = "xl/_rels/workbook.xml.rels"
    if rels_path not in parts:
        raise WorkbookSecurityError("WORKBOOK_RELATIONSHIPS_PART_MISSING")
    relationships = _parse_relationships(parts[rels_path], rels_path)
    relationship_by_id = {entry["Id"]: entry for entry in relationships}
    worksheet_relationships = {
        entry["Id"]: entry
        for entry in relationships
        if entry["Type"].rstrip("/") == f"{OFFICE_REL_NS}/worksheet"
    }
    seen_names: set[str] = set()
    seen_sheet_ids: set[str] = set()
    seen_relationship_ids: set[str] = set()
    seen_targets: set[str] = set()
    for sheet in sheets:
        name = sheet.attrib.get("name", "")
        sheet_id = sheet.attrib.get("sheetId", "")
        relationship_id = sheet.attrib.get(f"{{{OFFICE_REL_NS}}}id", "")
        if (
            not name
            or name.casefold() in seen_names
            or not sheet_id.isdigit()
            or int(sheet_id) < 1
            or sheet_id in seen_sheet_ids
            or not relationship_id
            or relationship_id in seen_relationship_ids
        ):
            raise WorkbookSecurityError("WORKBOOK_SHEET_BINDING_INVALID")
        seen_names.add(name.casefold())
        seen_sheet_ids.add(sheet_id)
        seen_relationship_ids.add(relationship_id)
        relationship = relationship_by_id.get(relationship_id)
        if relationship is None or relationship_id not in worksheet_relationships:
            raise WorkbookSecurityError("WORKBOOK_SHEET_RELATIONSHIP_INVALID")
        if relationship["TargetMode"].lower() != "internal":
            raise WorkbookSecurityError("WORKBOOK_SHEET_RELATIONSHIP_EXTERNAL")
        target = _resolve_target(rels_path, relationship["Target"])
        if (
            not re.fullmatch(r"xl/worksheets/sheet[1-9][0-9]*\.xml", target)
            or target not in parts
            or target in seen_targets
        ):
            raise WorkbookSecurityError("WORKBOOK_SHEET_TARGET_INVALID")
        seen_targets.add(target)
    package_worksheets = {
        part
        for part in parts
        if re.fullmatch(r"xl/worksheets/sheet[1-9][0-9]*\.xml", part)
    }
    if seen_relationship_ids != set(worksheet_relationships):
        raise WorkbookSecurityError("WORKBOOK_WORKSHEET_RELATIONSHIP_1_TO_1_INVALID")
    if seen_targets != package_worksheets:
        raise WorkbookSecurityError("WORKBOOK_WORKSHEET_PART_1_TO_1_INVALID")

    for relationship_suffix, part_name in (
        ("/sharedStrings", "xl/sharedStrings.xml"),
        ("/styles", "xl/styles.xml"),
        ("/theme", "xl/theme/theme1.xml"),
    ):
        matching = [
            entry
            for entry in relationships
            if entry["Type"].rstrip("/").endswith(relationship_suffix)
        ]
        present = part_name in parts
        if present != (len(matching) == 1):
            raise WorkbookSecurityError(
                f"WORKBOOK_REQUIRED_RELATIONSHIP_INVALID: {part_name}"
            )
        if matching and _resolve_target(rels_path, matching[0]["Target"]) != part_name:
            raise WorkbookSecurityError(
                f"WORKBOOK_REQUIRED_RELATIONSHIP_TARGET_INVALID: {part_name}"
            )

    shared_present = "xl/sharedStrings.xml" in parts
    for worksheet in package_worksheets:
        root = _xml_root(parts, worksheet)
        if any(
            cell.attrib.get("t") == "s"
            for cell in root.iter(f"{{{SS_NS}}}c")
        ) and not shared_present:
            raise WorkbookSecurityError("WORKBOOK_SHARED_STRINGS_PART_MISSING")


def _validate_workbook_structure(parts: Mapping[str, bytes]) -> None:
    _validate_content_types(parts)
    _validate_xml_roots(parts)
    _validate_package_root(parts)
    _validate_sheet_relationships(parts)


def _shared_strings(parts: Mapping[str, bytes]) -> tuple[str, ...]:
    data = parts.get("xl/sharedStrings.xml")
    if data is None:
        return ()
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise WorkbookSecurityError("WORKBOOK_SHARED_STRINGS_INVALID") from exc
    return tuple(
        "".join(
            node.text or ""
            for node in item.iter()
            if node.tag.rsplit("}", 1)[-1] == "t"
        )
        for item in root
        if item.tag.rsplit("}", 1)[-1] == "si"
    )


def _cell_text(cell: ET.Element, shared: Sequence[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        return "".join(
            node.text or ""
            for node in cell.iter()
            if node.tag.rsplit("}", 1)[-1] == "t"
        )
    value = next(
        (node for node in list(cell) if node.tag.rsplit("}", 1)[-1] == "v"),
        None,
    )
    raw = value.text or "" if value is not None else ""
    if cell_type == "s":
        if not raw.isdigit() or int(raw) >= len(shared):
            raise WorkbookSecurityError("WORKBOOK_SHARED_STRING_INDEX_INVALID")
        return shared[int(raw)]
    return raw


def _set_cell(cell: ET.Element, value: str) -> None:
    for child in list(cell):
        cell.remove(child)
    namespace = cell.tag.split("}", 1)[0] + "}" if "}" in cell.tag else ""
    try:
        Decimal(value)
        numeric = bool(_NUMBER_RE.fullmatch(value))
    except InvalidOperation:
        numeric = False
    if numeric:
        cell.attrib.pop("t", None)
        node = ET.SubElement(cell, f"{namespace}v")
        node.text = value
        return
    cell.attrib["t"] = "inlineStr"
    inline = ET.SubElement(cell, f"{namespace}is")
    text = ET.SubElement(inline, f"{namespace}t")
    text.text = value


def _set_shared_string_index(cell: ET.Element, index: int) -> None:
    for child in list(cell):
        cell.remove(child)
    namespace = cell.tag.split("}", 1)[0] + "}" if "}" in cell.tag else ""
    cell.attrib["t"] = "s"
    value = ET.SubElement(cell, f"{namespace}v")
    value.text = str(index)


def _replacement_map(
    replacements: Sequence[tuple[Mapping[str, Any], str]],
) -> dict[tuple[str, str], tuple[Mapping[str, Any], str]]:
    result: dict[tuple[str, str], tuple[Mapping[str, Any], str]] = {}
    for record, replacement in replacements:
        match = _LOCATOR_RE.fullmatch(str(record.get("locator", "")))
        if match is None:
            raise WorkbookSecurityError("WORKBOOK_GOVERNED_LOCATOR_INVALID")
        _, worksheet, cell_ref = match.groups()
        if not _CELL_RE.fullmatch(cell_ref):
            raise WorkbookSecurityError("WORKBOOK_GOVERNED_CELL_INVALID")
        key = (worksheet, cell_ref.upper())
        if key in result:
            raise WorkbookSecurityError(
                f"WORKBOOK_GOVERNED_CELL_DUPLICATE: {worksheet}!{cell_ref}"
            )
        result[key] = (record, replacement)
    return result


def _sanitize_worksheets(
    parts: dict[str, bytes],
    replacements: Sequence[tuple[Mapping[str, Any], str]],
) -> None:
    shared = _shared_strings(parts)
    replacement_map = _replacement_map(replacements)
    applied: set[tuple[str, str]] = set()
    worksheet_roots: dict[str, ET.Element] = {}
    retained_shared_cells: list[tuple[ET.Element, str]] = []
    for worksheet in sorted(
        name for name in parts if re.fullmatch(r"xl/worksheets/sheet[1-9][0-9]*\.xml", name)
    ):
        try:
            root = ET.fromstring(parts[worksheet])
        except ET.ParseError as exc:
            raise WorkbookSecurityError(
                f"WORKBOOK_WORKSHEET_XML_INVALID: {worksheet}"
            ) from exc
        if any(node.tag.rsplit("}", 1)[-1] == "f" for node in root.iter()):
            raise WorkbookSecurityError(f"WORKBOOK_FORMULA_FORBIDDEN: {worksheet}")
        for parent in root.iter():
            for child in list(parent):
                if child.tag.rsplit("}", 1)[-1] == "tableParts":
                    parent.remove(child)
        cells = [
            node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "c"
        ]
        for cell in cells:
            cell_ref = cell.attrib.get("r", "").upper()
            if not _CELL_RE.fullmatch(cell_ref):
                raise WorkbookSecurityError(
                    f"WORKBOOK_CELL_REFERENCE_INVALID: {worksheet}!{cell_ref}"
                )
            source_value = _cell_text(cell, shared)
            replacement_entry = replacement_map.get((worksheet, cell_ref))
            if replacement_entry is not None:
                record, replacement = replacement_entry
                if _sha256(source_value.encode("utf-8")) != record.get(
                    "source_text_sha256"
                ):
                    raise WorkbookSecurityError(
                        f"WORKBOOK_GOVERNED_SOURCE_DRIFT: {worksheet}!{cell_ref}"
                    )
                _set_cell(cell, replacement)
                applied.add((worksheet, cell_ref))
            elif cell.attrib.get("t") == "s":
                if source_value.strip():
                    retained_shared_cells.append((cell, source_value))
                else:
                    _set_cell(cell, "")
        worksheet_roots[worksheet] = root
    if set(replacement_map) != applied:
        missing = sorted(set(replacement_map) - applied)
        raise WorkbookSecurityError(
            "WORKBOOK_GOVERNED_CELL_MISSING: "
            + ",".join(f"{sheet}!{cell}" for sheet, cell in missing)
        )
    retained_values: list[str] = []
    retained_indices: dict[str, int] = {}
    for cell, value in retained_shared_cells:
        index = retained_indices.get(value)
        if index is None:
            index = len(retained_values)
            retained_indices[value] = index
            retained_values.append(value)
        _set_shared_string_index(cell, index)
    for worksheet, root in worksheet_roots.items():
        parts[worksheet] = ET.tostring(
            root,
            encoding="utf-8",
            xml_declaration=True,
        )
    if retained_values:
        shared_root = ET.Element(
            f"{{{SS_NS}}}sst",
            {
                "count": str(len(retained_shared_cells)),
                "uniqueCount": str(len(retained_values)),
            },
        )
        for value in retained_values:
            item = ET.SubElement(shared_root, f"{{{SS_NS}}}si")
            text = ET.SubElement(item, f"{{{SS_NS}}}t")
            text.text = value
        parts["xl/sharedStrings.xml"] = ET.tostring(
            shared_root,
            encoding="utf-8",
            xml_declaration=True,
        )
    else:
        parts.pop("xl/sharedStrings.xml", None)


def _sanitize_workbook_xml(parts: dict[str, bytes]) -> None:
    try:
        root = ET.fromstring(parts["xl/workbook.xml"])
    except ET.ParseError as exc:
        raise WorkbookSecurityError("WORKBOOK_XML_INVALID") from exc
    if any(
        node.tag.rsplit("}", 1)[-1] == "definedName"
        and bool((node.text or "").strip())
        for node in root.iter()
    ):
        raise WorkbookSecurityError("WORKBOOK_DEFINED_NAME_FORMULA_FORBIDDEN")


def _remove_residue_and_rewrite_relationships(parts: dict[str, bytes]) -> None:
    removed = {
        name
        for name in parts
        if name in {
            "xl/calcChain.xml",
            "docProps/core.xml",
            "docProps/app.xml",
            "docProps/custom.xml",
        }
        or re.fullmatch(r"xl/tables/table[1-9][0-9]*\.xml", name)
    }
    for name in removed:
        parts.pop(name, None)
    for rels_path in sorted(name for name in parts if name.endswith(".rels")):
        retained: list[dict[str, str]] = []
        for entry in _parse_relationships(parts[rels_path], rels_path):
            rel_type = entry["Type"].lower().rstrip("/")
            target = _resolve_target(rels_path, entry["Target"])
            if target in removed or target not in parts or any(
                rel_type.endswith(suffix) for suffix in _REMOVABLE_REL_TYPE_SUFFIXES
            ):
                continue
            retained.append(entry)
        parts[rels_path] = _serialize_relationships(retained)


def _prune_unreachable(parts: dict[str, bytes]) -> None:
    reachable = {"[Content_Types].xml", "_rels/.rels"}
    owners: set[str] = set()
    queue: deque[str] = deque()

    def enqueue(rels_path: str) -> None:
        data = parts.get(rels_path)
        if data is None:
            return
        reachable.add(rels_path)
        for entry in _parse_relationships(data, rels_path):
            if entry["TargetMode"].lower() == "external":
                raise WorkbookSecurityError("WORKBOOK_EXTERNAL_RELATIONSHIP_FORBIDDEN")
            target = _resolve_target(rels_path, entry["Target"])
            if target not in parts:
                raise WorkbookSecurityError(
                    f"WORKBOOK_RELATIONSHIP_TARGET_MISSING: {rels_path}->{target}"
                )
            queue.append(target)

    enqueue("_rels/.rels")
    while queue:
        owner = queue.popleft()
        if owner in owners:
            continue
        owners.add(owner)
        reachable.add(owner)
        enqueue(_rels_path(owner))
    for name in set(parts) - reachable:
        parts.pop(name, None)


def _sanitize_content_types(parts: dict[str, bytes]) -> None:
    try:
        root = ET.fromstring(parts["[Content_Types].xml"])
    except ET.ParseError as exc:
        raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPES_INVALID") from exc
    if root.tag != f"{{{CT_NS}}}Types":
        raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPES_NAMESPACE_INVALID")
    for child in list(root):
        local = child.tag.rsplit("}", 1)[-1]
        if local == "Override":
            target = child.attrib.get("PartName", "").lstrip("/")
            if target not in parts:
                root.remove(child)
        elif local != "Default":
            raise WorkbookSecurityError("WORKBOOK_CONTENT_TYPE_ELEMENT_INVALID")
        content_type = child.attrib.get("ContentType", "").lower()
        if "macroenabled" in content_type or "vbaproject" in content_type:
            raise WorkbookSecurityError("WORKBOOK_MACRO_CONTENT_TYPE_FORBIDDEN")
    parts["[Content_Types].xml"] = ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True,
    )


def _write_deterministic(parts: Mapping[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(parts):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, parts[name])
    return output.getvalue()


def mutate_governed_xlsx(
    source_bytes: bytes,
    replacements: Sequence[tuple[Mapping[str, Any], str]],
) -> bytes:
    """Return a deterministic, passive XLSX with complete governed cell data."""

    parts = _load_parts(source_bytes)
    _audit_relationship_graph(parts)
    _validate_workbook_structure(parts)
    _sanitize_workbook_xml(parts)
    _sanitize_worksheets(parts, replacements)
    _remove_residue_and_rewrite_relationships(parts)
    _prune_unreachable(parts)
    _sanitize_content_types(parts)
    _audit_relationship_graph(parts)
    _validate_workbook_structure(parts)
    return _write_deterministic(parts)


def audit_governed_xlsx(package_bytes: bytes) -> None:
    """Read-only audit of a final passive embedded XLSX package."""

    parts = _load_parts(package_bytes)
    _validate_workbook_structure(parts)
    _audit_relationship_graph(parts)
    _sanitize_workbook_xml(parts)
    forbidden_residue = sorted(
        name
        for name in parts
        if name in {
            "xl/calcChain.xml",
            "docProps/core.xml",
            "docProps/app.xml",
            "docProps/custom.xml",
        }
        or re.fullmatch(r"xl/tables/table[1-9][0-9]*\.xml", name)
    )
    if forbidden_residue:
        raise WorkbookSecurityError(
            "WORKBOOK_SANITIZED_RESIDUE_PRESENT: " + ",".join(forbidden_residue)
        )
    for worksheet in sorted(
        name
        for name in parts
        if re.fullmatch(r"xl/worksheets/sheet[1-9][0-9]*\.xml", name)
    ):
        root = _xml_root(parts, worksheet)
        if any(node.tag.rsplit("}", 1)[-1] == "f" for node in root.iter()):
            raise WorkbookSecurityError(f"WORKBOOK_FORMULA_FORBIDDEN: {worksheet}")
        if any(
            node.tag.rsplit("}", 1)[-1] == "tableParts"
            for node in root.iter()
        ):
            raise WorkbookSecurityError(
                f"WORKBOOK_TABLE_REFERENCE_RESIDUE: {worksheet}"
            )
    reachable = dict(parts)
    _prune_unreachable(reachable)
    if set(reachable) != set(parts):
        raise WorkbookSecurityError(
            "WORKBOOK_UNREACHABLE_PART_PRESENT: "
            + ",".join(sorted(set(parts) - set(reachable)))
        )


def read_governed_xlsx_slot(package_bytes: bytes, locator: str) -> str:
    """Read one governed worksheet cell from an already-sanitized XLSX."""

    match = _LOCATOR_RE.fullmatch(locator)
    if match is None:
        raise WorkbookSecurityError("WORKBOOK_GOVERNED_LOCATOR_INVALID")
    _, worksheet, cell_ref = match.groups()
    parts = _load_parts(package_bytes)
    _audit_relationship_graph(parts)
    try:
        root = ET.fromstring(parts[worksheet])
    except (KeyError, ET.ParseError) as exc:
        raise WorkbookSecurityError(
            f"WORKBOOK_WORKSHEET_XML_INVALID: {worksheet}"
        ) from exc
    matches = [
        node
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "c"
        and node.attrib.get("r", "").upper() == cell_ref.upper()
    ]
    if len(matches) != 1:
        raise WorkbookSecurityError(
            f"WORKBOOK_GOVERNED_CELL_MISSING: {worksheet}!{cell_ref}"
        )
    return _cell_text(matches[0], _shared_strings(parts))


__all__ = [
    "WORKBOOK_ZIP_RESOURCE_LIMITS",
    "WorkbookSecurityError",
    "audit_governed_xlsx",
    "mutate_governed_xlsx",
    "read_governed_xlsx_slot",
]
