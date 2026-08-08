"""Passive, non-extracting quarantine inspection for OOXML template packages."""

from __future__ import annotations

import hashlib
import io
import posixpath
import stat
import zipfile
from pathlib import PurePosixPath
from typing import Any
from xml.etree import ElementTree


MAX_ENTRIES = 10_000
MAX_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250.0
MAX_RELATIONSHIP_XML_BYTES = 4 * 1024 * 1024


def _finding(code: str, path: str | None = None) -> dict[str, str]:
    result = {"code": code}
    if path is not None:
        result["path"] = path
    return result


def _unsafe_path(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    return (
        not normalized
        or normalized.startswith("/")
        or (len(normalized) >= 2 and normalized[1] == ":")
        or any(part in {"", ".", ".."} for part in path.parts)
        or posixpath.normpath(normalized).startswith("../")
    )


def validate_quarantine_report(value: Any) -> dict[str, Any]:
    """Validate the runtime evidence needed by the certification boundary."""

    if not isinstance(value, dict):
        raise ValueError("quarantine report must be an object")
    required = {
        "schema_version",
        "status",
        "disposition",
        "package_sha256",
        "package_size_bytes",
        "entry_count",
        "compressed_bytes",
        "uncompressed_bytes",
        "findings",
    }
    if set(value) != required:
        raise ValueError("quarantine report fields do not match v1")
    report = dict(value)
    if report["schema_version"] != "1.0":
        raise ValueError("quarantine report schema_version must be 1.0")
    if report["disposition"] not in {"ACCEPT", "QUARANTINED", "REJECTED"}:
        raise ValueError("quarantine report disposition is invalid")
    expected_status = "PASS" if report["disposition"] == "ACCEPT" else "QUARANTINED"
    if report["status"] != expected_status:
        raise ValueError("quarantine report status contradicts disposition")
    digest = report["package_sha256"]
    if (
        not isinstance(digest, str)
        or not digest.startswith("sha256:")
        or len(digest) != 71
    ):
        raise ValueError("quarantine report package_sha256 is invalid")
    for key in (
        "package_size_bytes",
        "entry_count",
        "compressed_bytes",
        "uncompressed_bytes",
    ):
        if not isinstance(report[key], int) or report[key] < 0:
            raise ValueError(f"quarantine report {key} is invalid")
    if not isinstance(report["findings"], list):
        raise ValueError("quarantine report findings must be an array")
    if report["disposition"] == "ACCEPT" and report["findings"]:
        raise ValueError("ACCEPT quarantine report cannot contain findings")
    if report["disposition"] != "ACCEPT" and not report["findings"]:
        raise ValueError("unsafe quarantine report requires findings")
    return report


def inspect_package_bytes(payload: bytes) -> dict[str, Any]:
    """Classify a package without extracting or executing its contents."""

    digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    findings: list[dict[str, str]] = []
    compressed_total = 0
    uncompressed_total = 0
    entry_count = 0
    try:
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            infos = archive.infolist()
            entry_count = len(infos)
            if entry_count > MAX_ENTRIES:
                findings.append(_finding("ENTRY_COUNT_LIMIT"))
            seen: set[str] = set()
            for info in infos:
                name = info.filename.replace("\\", "/")
                key = name.casefold()
                if _unsafe_path(name):
                    findings.append(_finding("TRAVERSAL_PATH", name))
                if key in seen:
                    findings.append(_finding("DUPLICATE_ENTRY", name))
                seen.add(key)
                compressed_total += info.compress_size
                uncompressed_total += info.file_size
                if info.flag_bits & 0x1:
                    findings.append(_finding("ENCRYPTED_ENTRY", name))
                unix_mode = (info.external_attr >> 16) & 0xFFFF
                if unix_mode and stat.S_ISLNK(unix_mode):
                    findings.append(_finding("SYMLINK_ENTRY", name))
                if key.endswith("vbaproject.bin") or "/macros/" in key:
                    findings.append(_finding("MACRO_CONTENT", name))
                if "/embeddings/" in key or "oleobject" in key:
                    findings.append(_finding("OLE_CONTENT", name))
                if "/activex/" in key:
                    findings.append(_finding("ACTIVEX_CONTENT", name))
                if key == "[content_types].xml":
                    if info.file_size > MAX_RELATIONSHIP_XML_BYTES:
                        findings.append(_finding("CONTENT_TYPES_XML_SIZE_LIMIT", name))
                        continue
                    content_types = archive.read(info)
                    lowered_types = content_types.lower()
                    if b"<!doctype" in lowered_types or b"<!entity" in lowered_types:
                        findings.append(_finding("XML_DTD_CONTENT", name))
                        continue
                    if b"macroenabled" in lowered_types or b"vbaproject" in lowered_types:
                        findings.append(_finding("MACRO_CONTENT", name))
                    if b"oleobject" in lowered_types:
                        findings.append(_finding("OLE_CONTENT", name))
                    if b"activex" in lowered_types:
                        findings.append(_finding("ACTIVEX_CONTENT", name))
                if key.endswith(".rels"):
                    if info.file_size > MAX_RELATIONSHIP_XML_BYTES:
                        findings.append(_finding("RELATIONSHIP_XML_SIZE_LIMIT", name))
                        continue
                    relationship_xml = archive.read(info)
                    upper_xml = relationship_xml.upper()
                    if b"<!DOCTYPE" in upper_xml or b"<!ENTITY" in upper_xml:
                        findings.append(_finding("XML_DTD_CONTENT", name))
                        continue
                    try:
                        root = ElementTree.fromstring(relationship_xml)
                    except ElementTree.ParseError:
                        findings.append(_finding("MALFORMED_RELATIONSHIP_XML", name))
                    else:
                        for relationship in root:
                            if relationship.attrib.get("TargetMode", "").casefold() == "external":
                                findings.append(_finding("EXTERNAL_RELATIONSHIP", name))
                                break
            if uncompressed_total > MAX_UNCOMPRESSED_BYTES:
                findings.append(_finding("UNCOMPRESSED_SIZE_LIMIT"))
            ratio = uncompressed_total / max(compressed_total, 1)
            if ratio > MAX_COMPRESSION_RATIO:
                findings.append(_finding("COMPRESSION_RATIO_LIMIT"))
    except (zipfile.BadZipFile, OSError, RuntimeError):
        findings.append(_finding("MALFORMED_ARCHIVE"))

    codes = {item["code"] for item in findings}
    disposition = "REJECTED" if "MALFORMED_ARCHIVE" in codes else (
        "QUARANTINED" if findings else "ACCEPT"
    )
    return validate_quarantine_report({
        "schema_version": "1.0",
        "status": "PASS" if disposition == "ACCEPT" else "QUARANTINED",
        "disposition": disposition,
        "package_sha256": digest,
        "package_size_bytes": len(payload),
        "entry_count": entry_count,
        "compressed_bytes": compressed_total,
        "uncompressed_bytes": uncompressed_total,
        "findings": findings,
    })
