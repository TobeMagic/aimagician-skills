#!/usr/bin/env python3
"""Fail-closed validation for the Window-PPTX v6.1 clean-room run.

The validator is intentionally read-only.  ``pack`` proves that a client input
directory is a frozen, project-relative clean room.  ``run`` additionally
proves the exact Codex invocation, installed Skill bytes, input bundles, private
library resolution evidence, manifests, output PPTX, physical assembly report,
and successful process exit recorded by the external harness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from validate_window_pptx_v61_physical_report import validate_physical_report
from window_pptx.page_template_library import load_library_index
from window_pptx.v61_acceptance_settlement import (
    AcceptanceSettlementError,
    reject_symlink_components,
    validate_distinct_file_paths,
    validate_harness_topology,
    verify_settlement_evidence,
)
from window_pptx.v61_runtime_identity import (
    CONTROLLER_RELATIVE,
    RUNTIME_SCHEMA_NAME,
    RuntimeIdentityError,
    verify_runtime_identity_payload,
)


SCHEMA_VERSION = "1.0"
CONTRACT_ID = "pptx-studio-v61-clean-pack"
REQUIREMENT_SCHEMA = "annual-work-report-requirement-pack.v1.schema.json"
RUN_SCHEMA = "physical-assembly-run-fingerprint.v1.schema.json"
POST_RUN_SCHEMA = "physical-assembly-post-run-manifest.v1.schema.json"
SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schemas"

OUTPUT_PPTX_PATH = "output/hospital-finance-annual-2025.pptx"
EVIDENCE_OUTPUT_PATHS = (
    "evidence/direction-decision.v1.json",
    "evidence/narrative-plan.v1.json",
    "evidence/assembly-plan.v1.json",
    "evidence/template-query-results.v1.json",
    "evidence/physical-assembly-report.v1.json",
    "evidence/rule-qa.v1.json",
    "evidence/fingerprint-bundle.v1.json",
    "evidence/run-summary.md",
)
PHYSICAL_REPORT_PATH = "evidence/physical-assembly-report.v1.json"
RULE_QA_PATH = "evidence/rule-qa.v1.json"
QUERY_BUNDLE_PATH = "evidence/template-query-results.v1.json"
FINGERPRINT_BUNDLE_PATH = "evidence/fingerprint-bundle.v1.json"
PHASE49_LIBRARY_RELATIVE = "v61/reference-work-summary-library-v4.json"
REQUIRED_RULE_QA_RULES = {
    "output-identity",
    "zip-open",
    "slide-count",
    "placeholder-residue",
    "named-brand-residue",
    "source-template-residue",
    "text-bounds",
    "tiny-text",
    "style-lineage",
}

PRESENTATION_EXTENSIONS = {
    ".ppt",
    ".pptx",
    ".pptm",
    ".pot",
    ".potx",
    ".potm",
    ".pps",
    ".ppsx",
    ".ppsm",
}
GIT_MARKERS = {
    ".git",
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
}
PRIVATE_MARKERS = {
    ".private",
    "gaojie",
    "huashu-design",
    "private-library",
    "private-templates",
}
PREVIEW_MARKERS = {
    "preview",
    "previews",
    "template-preview",
    "template-previews",
    "contact-sheet",
    "contact-sheets",
    "thumbnail-sheet",
    "thumbnail-sheets",
}
HISTORY_MARKERS = {
    "history",
    "historical",
    "historical-output",
    "historical-outputs",
    "old-output",
    "old-outputs",
    "previous-output",
    "previous-outputs",
    "reference-output",
    "reference-outputs",
}
REFERENCE_MARKERS = {
    "reference",
    "references",
    "reference-deck",
    "reference-decks",
    "reference-pptx",
    "reference-pptxs",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_JSON_SCHEMAS = {
    "evidence/direction-decision.v1.json": "direction-decision.v1.schema.json",
    "evidence/narrative-plan.v1.json": "narrative-plan.v1.schema.json",
    "evidence/assembly-plan.v1.json": "assembly-plan.v1.schema.json",
    "evidence/template-query-results.v1.json": "page-template-query-bundle.v1.schema.json",
    "evidence/physical-assembly-report.v1.json": "physical-assembly-report.v1.schema.json",
    "evidence/fingerprint-bundle.v1.json": "fingerprint-bundle.v1.schema.json",
}


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalised_records(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    values = [
        {
            "path": str(record["path"]),
            "sha256": str(record["sha256"]),
            "size": int(record["size"]),
        }
        for record in records
    ]
    return sorted(values, key=lambda item: (item["path"].casefold(), item["path"]))


def bundle_fingerprint(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return the public canonical-file-records-sha256-v1 bundle."""

    normalised = _normalised_records(records)
    return {
        "digest_algorithm": "canonical-file-records-sha256-v1",
        "sha256": hashlib.sha256(_canonical_json(normalised)).hexdigest(),
        "file_count": len(normalised),
        "total_size": sum(int(item["size"]) for item in normalised),
        "files": normalised,
    }


def tree_fingerprint(root: Path | str) -> dict[str, Any]:
    """Hash every installed Skill file using tree-file-bytes-sha256-v1.

    The digest follows the existing Window-PPTX tree convention: sorted
    project-relative UTF-8 path, NUL, file bytes, NUL.  No file is silently
    excluded and symbolic links are rejected.
    """

    base = Path(root)
    if not base.is_absolute():
        raise ValueError("installed Skill path must be absolute")
    if base.is_symlink() or not base.is_dir():
        raise ValueError("installed Skill path must be a real directory")
    paths: list[Path] = []
    for directory, directory_names, file_names in os.walk(base, followlinks=False):
        directory_path = Path(directory)
        for name in tuple(directory_names):
            candidate = directory_path / name
            if candidate.is_symlink():
                raise ValueError(f"installed Skill contains a symlink: {candidate}")
        for name in file_names:
            candidate = directory_path / name
            mode = candidate.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"installed Skill contains a symlink: {candidate}")
            if not stat.S_ISREG(mode):
                raise ValueError(f"installed Skill contains a special file: {candidate}")
            relative_parts = {
                part.casefold().replace("_", "-")
                for part in candidate.relative_to(base).parts
            }
            if relative_parts & PRIVATE_MARKERS:
                raise ValueError("installed Skill contains private-library material")
            paths.append(candidate)
    if not paths:
        raise ValueError("installed Skill directory is empty")
    paths.sort(
        key=lambda path: (
            path.relative_to(base).as_posix().casefold(),
            path.relative_to(base).as_posix(),
        )
    )
    digest = hashlib.sha256()
    total_size = 0
    for path in paths:
        relative = path.relative_to(base).as_posix()
        payload = path.read_bytes()
        total_size += len(payload)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return {
        "digest_algorithm": "tree-file-bytes-sha256-v1",
        "sha256": digest.hexdigest(),
        "file_count": len(paths),
        "total_size": total_size,
    }


def _issue(issues: list[dict[str, str]], code: str, location: str, detail: str) -> None:
    issues.append({"code": code, "location": location, "detail": detail})


def _read_json(path: Path, issues: list[dict[str, str]], location: str) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _issue(issues, "JSON_READ_FAILED", location, str(exc))
        return None


def _validate_schema(
    payload: Any,
    schema_name: str,
    issues: list[dict[str, str]],
    location: str,
) -> bool:
    try:
        import jsonschema
    except ImportError:
        _issue(issues, "JSONSCHEMA_UNAVAILABLE", location, "jsonschema is required")
        return False
    schema_path = SCHEMA_ROOT / schema_name
    schema = _read_json(schema_path, issues, f"schema:{schema_name}")
    if schema is None:
        return False
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        _issue(issues, "SCHEMA_INVALID", f"schema:{schema_name}", exc.message)
        return False
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    for error in errors:
        suffix = ".".join(str(part) for part in error.absolute_path)
        error_location = f"{location}.{suffix}" if suffix else location
        _issue(issues, "SCHEMA_VALIDATION_FAILED", error_location, error.message)
    return not errors


def _validate_evidence_schema(
    payload: Any,
    schema_name: str,
    issues: list[dict[str, str]],
    location: str,
) -> bool:
    """Validate one evidence document with local-only cross-schema refs."""

    try:
        import jsonschema
        from referencing import Registry, Resource
    except ImportError:
        _issue(issues, "JSONSCHEMA_UNAVAILABLE", location, "jsonschema is required")
        return False
    schema_path = SCHEMA_ROOT / schema_name
    schema = _read_json(schema_path, issues, f"schema:{schema_name}")
    if not isinstance(schema, Mapping):
        return False
    resources: list[tuple[str, Any]] = []
    for candidate in SCHEMA_ROOT.glob("*.schema.json"):
        try:
            candidate_schema = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(candidate_schema, Mapping):
            continue
        resource = Resource.from_contents(candidate_schema)
        schema_id = candidate_schema.get("$id")
        if isinstance(schema_id, str) and schema_id.startswith(("http://", "https://")):
            resources.append((schema_id, resource))
        resources.append(
            (f"https://pptx-studio.local/schemas/{candidate.name}", resource)
        )
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        registry = Registry().with_resources(resources)
        validator = jsonschema.Draft202012Validator(schema, registry=registry)
        errors = sorted(
            validator.iter_errors(payload),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
    except Exception as exc:
        _issue(issues, "EVIDENCE_SCHEMA_INVALID", f"schema:{schema_name}", str(exc))
        return False
    for error in errors:
        suffix = ".".join(str(part) for part in error.absolute_path)
        error_location = f"{location}.{suffix}" if suffix else location
        _issue(
            issues,
            "EVIDENCE_SCHEMA_VALIDATION_FAILED",
            error_location,
            error.message,
        )
    return not errors


def _validate_run_summary(
    path: Path,
    *,
    output_path: Path | None,
    report_payload: Any,
    issues: list[dict[str, str]],
) -> None:
    """Validate the minimum human-readable Phase 49 run-summary contract."""

    location = "run_fingerprint.artifacts.evidence_outputs.run_summary"
    try:
        payload = path.read_bytes()
        text = payload.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        _issue(issues, "RUN_SUMMARY_UNREADABLE", location, str(exc))
        return
    if not payload or len(payload) > 1_000_000 or "\0" in text:
        _issue(
            issues,
            "RUN_SUMMARY_INVALID",
            location,
            "summary must be non-empty UTF-8 text no larger than 1 MiB",
        )
        return
    lines = text.splitlines()
    required_exact = {
        "# Phase 49 candidate run",
        "Author state: `CANDIDATE_READY_FOR_BLIND_REVIEW`",
        "## Machine-gate result",
        "- Physical assembly: pass",
        "- Rule QA: pass",
        "- Unresolved warnings: none from blocking machine gates; visual release remains pending independent blind review.",
    }
    for required in sorted(required_exact):
        if lines.count(required) != 1:
            _issue(
                issues,
                "RUN_SUMMARY_REQUIRED_LINE_INVALID",
                location,
                required,
            )
    table_header = (
        "| Page | Narrative role | Title | Page ID | Package SHA-256 | "
        "Style cluster | Fact IDs | Rule QA |"
    )
    if lines.count(table_header) != 1:
        _issue(issues, "RUN_SUMMARY_TABLE_HEADER_INVALID", location, table_header)
    row_ordinals: list[int] = []
    for line in lines:
        match = re.match(r"^\|\s*(\d+)\s*\|", line)
        if match:
            row_ordinals.append(int(match.group(1)))
    expected_slide_count = (
        report_payload.get("target_slide_count")
        if isinstance(report_payload, Mapping)
        else None
    )
    if type(expected_slide_count) is not int or expected_slide_count < 1:
        expected_slide_count = 15
    if row_ordinals != list(range(1, expected_slide_count + 1)):
        _issue(
            issues,
            "RUN_SUMMARY_PAGE_ROWS_INVALID",
            location,
            f"expected 1..{expected_slide_count}, got {row_ordinals}",
        )

    fields: dict[str, list[str]] = {}
    for line in lines:
        match = re.match(r"^- ([^:]+):\s*(.*)$", line)
        if match:
            fields.setdefault(match.group(1), []).append(match.group(2))
    required_fields = {
        "Final PPTX SHA-256",
        "Slide count",
        "Distinct page IDs",
        "Physical lineage coverage",
        "Native editable coverage",
        "Ordinary bindings expanded by Skill",
    }
    for field in sorted(required_fields):
        if len(fields.get(field, [])) != 1:
            _issue(
                issues,
                "RUN_SUMMARY_MACHINE_FIELD_INVALID",
                location,
                field,
            )
    if output_path is not None and len(fields.get("Final PPTX SHA-256", [])) == 1:
        summary_sha = fields["Final PPTX SHA-256"][0].strip("`")
        if not SHA256_RE.fullmatch(summary_sha) or summary_sha != _sha256_file(output_path):
            _issue(
                issues,
                "RUN_SUMMARY_OUTPUT_SHA256_MISMATCH",
                location,
                summary_sha,
            )
    for field, expected in (
        ("Slide count", expected_slide_count),
        ("Distinct page IDs", expected_slide_count),
    ):
        values = fields.get(field, [])
        if len(values) == 1:
            try:
                observed = int(values[0])
            except ValueError:
                observed = -1
            if observed != expected:
                _issue(
                    issues,
                    "RUN_SUMMARY_MACHINE_VALUE_MISMATCH",
                    location,
                    f"{field}: expected {expected}, got {values[0]}",
                )
    for field in ("Physical lineage coverage", "Native editable coverage"):
        values = fields.get(field, [])
        if len(values) == 1:
            try:
                observed = float(values[0])
            except ValueError:
                observed = -1.0
            if not math.isfinite(observed) or not math.isclose(observed, 1.0):
                _issue(
                    issues,
                    "RUN_SUMMARY_COVERAGE_INCOMPLETE",
                    location,
                    f"{field}: {values[0]}",
                )
    ordinary = fields.get("Ordinary bindings expanded by Skill", [])
    if len(ordinary) == 1:
        try:
            ordinary_count = int(ordinary[0])
        except ValueError:
            ordinary_count = 0
        if ordinary_count < 1:
            _issue(
                issues,
                "RUN_SUMMARY_BINDING_COUNT_INVALID",
                location,
                ordinary[0],
            )


def _project_path_parts(raw: Any) -> tuple[str, ...] | None:
    if not isinstance(raw, str) or not raw or "\0" in raw or "\\" in raw:
        return None
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        return None
    raw_parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        return None
    pure = PurePosixPath(raw)
    if pure.is_absolute() or pure.as_posix() != raw:
        return None
    return pure.parts


def _resolve_project_file(
    root: Path,
    raw: Any,
    issues: list[dict[str, str]],
    location: str,
) -> Path | None:
    parts = _project_path_parts(raw)
    if parts is None:
        _issue(
            issues,
            "PROJECT_PATH_INVALID",
            location,
            "path must be a normalized project-relative POSIX path",
        )
        return None
    cursor = root
    for part in parts:
        cursor = cursor / part
        try:
            if cursor.is_symlink():
                _issue(issues, "SYMLINK_FORBIDDEN", location, f"symlink component: {raw}")
                return None
        except OSError as exc:
            _issue(issues, "PATH_INSPECTION_FAILED", location, str(exc))
            return None
    try:
        resolved = cursor.resolve(strict=False)
    except OSError as exc:
        _issue(issues, "PATH_RESOLUTION_FAILED", location, str(exc))
        return None
    if not resolved.is_relative_to(root):
        _issue(issues, "PROJECT_PATH_ESCAPE", location, str(raw))
        return None
    try:
        mode = cursor.lstat().st_mode
    except OSError as exc:
        _issue(issues, "BOUND_FILE_MISSING", location, str(exc))
        return None
    if not stat.S_ISREG(mode):
        _issue(issues, "BOUND_FILE_NOT_REGULAR", location, str(raw))
        return None
    return cursor


def _verify_project_record(
    root: Path,
    record: Any,
    issues: list[dict[str, str]],
    location: str,
) -> dict[str, Any] | None:
    if not isinstance(record, Mapping):
        _issue(issues, "BOUND_RECORD_INVALID", location, "record must be an object")
        return None
    raw_path = record.get("path")
    path = _resolve_project_file(root, raw_path, issues, f"{location}.path")
    if path is None:
        return None
    expected_sha = record.get("sha256")
    expected_size = record.get("size")
    if not isinstance(expected_sha, str) or not SHA256_RE.fullmatch(expected_sha):
        _issue(issues, "BOUND_SHA256_INVALID", f"{location}.sha256", str(expected_sha))
        return None
    if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
        _issue(issues, "BOUND_SIZE_INVALID", f"{location}.size", str(expected_size))
        return None
    actual_size = path.stat().st_size
    actual_sha = _sha256_file(path)
    if actual_size != expected_size:
        _issue(
            issues,
            "BOUND_SIZE_MISMATCH",
            location,
            f"expected {expected_size}, got {actual_size}",
        )
    if actual_sha != expected_sha:
        _issue(
            issues,
            "BOUND_SHA256_MISMATCH",
            location,
            f"expected {expected_sha}, got {actual_sha}",
        )
    return {"path": str(raw_path), "sha256": actual_sha, "size": actual_size}


def _contamination_scan(root: Path, issues: list[dict[str, str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        for name in tuple(directory_names):
            path = directory_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                _issue(issues, "SYMLINK_FORBIDDEN", relative, "directory symlink")
                directory_names.remove(name)
                continue
            _check_forbidden_path(relative, True, issues)
        for name in file_names:
            path = directory_path / name
            relative = path.relative_to(root).as_posix()
            try:
                mode = path.lstat().st_mode
            except OSError as exc:
                _issue(issues, "PATH_INSPECTION_FAILED", relative, str(exc))
                continue
            if stat.S_ISLNK(mode):
                _issue(issues, "SYMLINK_FORBIDDEN", relative, "file symlink")
                continue
            if not stat.S_ISREG(mode):
                _issue(issues, "SPECIAL_FILE_FORBIDDEN", relative, "not a regular file")
                continue
            _check_forbidden_path(relative, False, issues)
            records.append(
                {"path": relative, "sha256": _sha256_file(path), "size": path.stat().st_size}
            )
    return _normalised_records(records)


def _post_run_inventory(
    root: Path,
    issues: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Return the exact post-run tree while applying output-safe hygiene rules."""

    records: list[dict[str, Any]] = []
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        for name in tuple(directory_names):
            path = directory_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                _issue(issues, "SYMLINK_FORBIDDEN", relative, "directory symlink")
                directory_names.remove(name)
                continue
            _check_post_run_forbidden_path(relative, issues)
        for name in file_names:
            path = directory_path / name
            relative = path.relative_to(root).as_posix()
            try:
                mode = path.lstat().st_mode
            except OSError as exc:
                _issue(issues, "PATH_INSPECTION_FAILED", relative, str(exc))
                continue
            if stat.S_ISLNK(mode):
                _issue(issues, "SYMLINK_FORBIDDEN", relative, "file symlink")
                continue
            if not stat.S_ISREG(mode):
                _issue(issues, "SPECIAL_FILE_FORBIDDEN", relative, "not a regular file")
                continue
            _check_post_run_forbidden_path(relative, issues)
            records.append(
                {
                    "path": relative,
                    "sha256": _sha256_file(path),
                    "size": path.stat().st_size,
                }
            )
    return _normalised_records(records)


def _check_post_run_forbidden_path(
    relative: str,
    issues: list[dict[str, str]],
) -> None:
    path = PurePosixPath(relative)
    folded = [part.casefold().replace("_", "-") for part in path.parts]
    folded_set = set(folded)
    if folded_set & GIT_MARKERS or any(part.startswith(".git") for part in folded):
        _issue(issues, "GIT_MARKER_FORBIDDEN", relative, "Git metadata is not a clean output")
    if folded_set & PRIVATE_MARKERS:
        _issue(issues, "PRIVATE_MARKER_FORBIDDEN", relative, "private-library marker")
    if folded_set & PREVIEW_MARKERS:
        _issue(issues, "TEMPLATE_PREVIEW_FORBIDDEN", relative, "template preview marker")
    if folded_set & REFERENCE_MARKERS:
        _issue(issues, "REFERENCE_MATERIAL_FORBIDDEN", relative, "reference material marker")
    if folded_set & HISTORY_MARKERS:
        _issue(issues, "HISTORICAL_OUTPUT_FORBIDDEN", relative, "historical output marker")


def _check_forbidden_path(
    relative: str,
    is_directory: bool,
    issues: list[dict[str, str]],
) -> None:
    path = PurePosixPath(relative)
    folded = [part.casefold().replace("_", "-") for part in path.parts]
    folded_set = set(folded)
    if folded_set & GIT_MARKERS or any(part.startswith(".git") for part in folded):
        _issue(issues, "GIT_MARKER_FORBIDDEN", relative, "Git metadata is not a clean input")
    if folded_set & PRIVATE_MARKERS:
        _issue(issues, "PRIVATE_MARKER_FORBIDDEN", relative, "private-library marker")
    if folded_set & PREVIEW_MARKERS:
        _issue(issues, "TEMPLATE_PREVIEW_FORBIDDEN", relative, "template preview marker")
    if folded_set & HISTORY_MARKERS:
        _issue(issues, "HISTORICAL_OUTPUT_FORBIDDEN", relative, "historical output marker")
    if not is_directory and path.suffix.casefold() in PRESENTATION_EXTENSIONS:
        _issue(issues, "PRESENTATION_INPUT_FORBIDDEN", relative, path.suffix.casefold())


def _unique_records(
    records: list[dict[str, Any]],
    issues: list[dict[str, str]],
    location: str,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for record in _normalised_records(records):
        folded = record["path"].casefold()
        if folded in seen:
            _issue(issues, "BOUND_PATH_DUPLICATE", location, record["path"])
            continue
        seen.add(folded)
        result.append(record)
    return result


def _nested_data_records(
    root: Path,
    manifest_path: Path,
    issues: list[dict[str, str]],
) -> list[dict[str, Any]]:
    payload = _read_json(manifest_path, issues, "authorities.data_manifest")
    if not isinstance(payload, Mapping) or not isinstance(payload.get("files"), list):
        _issue(
            issues,
            "DATA_MANIFEST_INVALID",
            "authorities.data_manifest",
            "root must contain a files array",
        )
        return []
    records: list[dict[str, Any]] = []
    for index, raw in enumerate(payload["files"]):
        location = f"authorities.data_manifest.files[{index}]"
        if not isinstance(raw, Mapping):
            _issue(issues, "BOUND_RECORD_INVALID", location, "entry must be an object")
            continue
        if "size" not in raw:
            _issue(issues, "BOUND_SIZE_MISSING", f"{location}.size", "size is required")
            continue
        record = _verify_project_record(root, raw, issues, location)
        if record is not None:
            records.append(record)
    return records


def _nested_asset_records(
    root: Path,
    manifest_path: Path,
    issues: list[dict[str, str]],
) -> list[dict[str, Any]]:
    payload = _read_json(manifest_path, issues, "authorities.asset_manifest")
    if not isinstance(payload, Mapping) or not isinstance(payload.get("bindings"), Mapping):
        _issue(
            issues,
            "ASSET_MANIFEST_INVALID",
            "authorities.asset_manifest",
            "root must contain a bindings object",
        )
        return []
    records: list[dict[str, Any]] = []
    for asset_id, raw in sorted(payload["bindings"].items(), key=lambda item: str(item[0])):
        location = f"authorities.asset_manifest.bindings.{asset_id}"
        if not isinstance(raw, Mapping):
            _issue(issues, "BOUND_RECORD_INVALID", location, "binding must be an object")
            continue
        size = raw.get("size")
        if size is None and isinstance(raw.get("record"), Mapping):
            size = raw["record"].get("size")
        if size is None:
            _issue(issues, "BOUND_SIZE_MISSING", f"{location}.size", "size is required")
            continue
        record = _verify_project_record(
            root,
            {"path": raw.get("path"), "sha256": raw.get("sha256"), "size": size},
            issues,
            location,
        )
        if record is not None:
            records.append(record)
    return records


def _validate_pre_manifest(
    root: Path,
    raw_path: str,
    issues: list[dict[str, str]],
    *,
    enforce_snapshot: bool,
) -> dict[str, Any] | None:
    path = _resolve_project_file(root, raw_path, issues, "pre_run_manifest.path")
    if path is None:
        return None
    payload = _read_json(path, issues, "pre_run_manifest")
    if not isinstance(payload, Mapping):
        _issue(issues, "PRE_MANIFEST_INVALID", "pre_run_manifest", "root must be an object")
        return None
    if payload.get("schema_version") != SCHEMA_VERSION:
        _issue(issues, "PRE_MANIFEST_INVALID", "pre_run_manifest.schema_version", "must be 1.0")
    if payload.get("root") != "." or payload.get("recursive") is not True:
        _issue(issues, "PRE_MANIFEST_INVALID", "pre_run_manifest", "root/recursive drift")
    exclusion = payload.get("exclusion")
    if not isinstance(exclusion, Mapping) or exclusion.get("path") != raw_path:
        _issue(issues, "PRE_MANIFEST_INVALID", "pre_run_manifest.exclusion", "self-exclusion drift")
    constraints = payload.get("constraints")
    required_zeroes = {
        "pptx_count",
        "template_preview_count",
        "private_byte_count",
        "history_output_count",
        "repository_marker_count",
        "symlink_count",
    }
    if not isinstance(constraints, Mapping) or any(constraints.get(key) != 0 for key in required_zeroes):
        _issue(issues, "PRE_MANIFEST_INVALID", "pre_run_manifest.constraints", "all clean-room counts must be zero")
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        _issue(issues, "PRE_MANIFEST_INVALID", "pre_run_manifest.entries", "must be an array")
        return {"path": raw_path, "sha256": _sha256_file(path), "size": path.stat().st_size}
    manifest_records: list[dict[str, Any]] = []
    for index, entry in enumerate(raw_entries):
        location = f"pre_run_manifest.entries[{index}]"
        if not isinstance(entry, Mapping) or entry.get("type") != "regular_file":
            _issue(issues, "PRE_MANIFEST_ENTRY_INVALID", location, "regular_file entry required")
            continue
        record = _verify_project_record(root, entry, issues, location)
        if record is not None:
            manifest_records.append(record)
    manifest_records = _unique_records(manifest_records, issues, "pre_run_manifest.entries")
    if payload.get("entry_count") != len(manifest_records):
        _issue(issues, "PRE_MANIFEST_COUNT_MISMATCH", "pre_run_manifest.entry_count", str(len(manifest_records)))
    total_size = sum(record["size"] for record in manifest_records)
    if payload.get("total_size") != total_size:
        _issue(issues, "PRE_MANIFEST_SIZE_MISMATCH", "pre_run_manifest.total_size", str(total_size))
    if enforce_snapshot:
        actual = [
            record
            for record in _contamination_scan(root, issues)
            if record["path"] != raw_path
        ]
        if manifest_records != actual:
            _issue(
                issues,
                "PRE_MANIFEST_SNAPSHOT_MISMATCH",
                "pre_run_manifest.entries",
                "manifest does not exactly cover the current clean-room files",
            )
    return {"path": raw_path, "sha256": _sha256_file(path), "size": path.stat().st_size}


def validate_requirement_pack(
    root: Path | str,
    requirement_pack: str,
    *,
    pre_manifest: str | None = "PRE-RUN-MANIFEST.json",
    enforce_snapshot: bool = True,
    scan_contamination: bool = True,
) -> dict[str, Any]:
    """Validate a locked clean-room requirement pack without writing files."""

    issues: list[dict[str, str]] = []
    requested_root = Path(root)
    if requested_root.is_symlink() or not requested_root.is_dir():
        _issue(issues, "ROOT_INVALID", "root", "root must be a real directory")
        canonical_root = requested_root.resolve(strict=False)
    else:
        canonical_root = requested_root.resolve()
    if scan_contamination and canonical_root.is_dir():
        _contamination_scan(canonical_root, issues)
    pack_path = _resolve_project_file(
        canonical_root,
        requirement_pack,
        issues,
        "requirement_pack.path",
    )
    payload = _read_json(pack_path, issues, "requirement_pack") if pack_path else None
    schema_valid = payload is not None and _validate_schema(
        payload, REQUIREMENT_SCHEMA, issues, "requirement_pack"
    )
    requirement_records: list[dict[str, Any]] = []
    asset_records: list[dict[str, Any]] = []
    pack_record: dict[str, Any] | None = None
    if pack_path is not None:
        pack_record = {
            "path": requirement_pack,
            "sha256": _sha256_file(pack_path),
            "size": pack_path.stat().st_size,
        }
        requirement_records.append(pack_record)
    if schema_valid and isinstance(payload, Mapping):
        authorities = payload["authorities"]
        authority_paths: dict[str, Path] = {}
        for name in (
            "project_brief",
            "request",
            "fact_store",
            "asset_manifest",
            "connective_copy",
            "data_manifest",
        ):
            record = _verify_project_record(
                canonical_root,
                authorities[name],
                issues,
                f"requirement_pack.authorities.{name}",
            )
            if record is None:
                continue
            authority_paths[name] = canonical_root / record["path"]
            if name == "asset_manifest":
                asset_records.append(record)
            else:
                requirement_records.append(record)
        project_brief_path = authority_paths.get("project_brief")
        if project_brief_path is not None:
            brief = _read_json(project_brief_path, issues, "authorities.project_brief")
            expected_lock = authorities["project_brief"].get("lock_sha256")
            if not isinstance(brief, Mapping) or brief.get("lock_sha256") != expected_lock:
                _issue(
                    issues,
                    "PROJECT_BRIEF_LOCK_MISMATCH",
                    "requirement_pack.authorities.project_brief.lock_sha256",
                    "brief lock does not match the top-level authority lock",
                )
        data_manifest_path = authority_paths.get("data_manifest")
        if data_manifest_path is not None:
            requirement_records.extend(
                _nested_data_records(canonical_root, data_manifest_path, issues)
            )
        asset_manifest_path = authority_paths.get("asset_manifest")
        if asset_manifest_path is not None:
            asset_records.extend(
                _nested_asset_records(canonical_root, asset_manifest_path, issues)
            )
    requirement_records = _unique_records(requirement_records, issues, "requirements")
    asset_records = _unique_records(asset_records, issues, "assets")
    pre_record = None
    if pre_manifest is not None and canonical_root.is_dir():
        pre_record = _validate_pre_manifest(
            canonical_root,
            pre_manifest,
            issues,
            enforce_snapshot=enforce_snapshot,
        )
    issues.sort(key=lambda item: (item["location"], item["code"], item["detail"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "mode": "pack",
        "status": "PASS" if not issues else "FAIL",
        "root": str(canonical_root),
        "requirement_pack": pack_record,
        "pre_run_manifest": pre_record,
        "requirements": bundle_fingerprint(requirement_records),
        "assets": bundle_fingerprint(asset_records),
        "issues": issues,
    }


def _verify_external_artifact(
    raw: Any,
    base: Path,
    issues: list[dict[str, str]],
    location: str,
) -> Path | None:
    if not isinstance(raw, Mapping):
        _issue(issues, "ARTIFACT_RECORD_INVALID", location, "record must be an object")
        return None
    raw_path = raw.get("path")
    if not isinstance(raw_path, str) or not raw_path or "\0" in raw_path:
        _issue(issues, "ARTIFACT_PATH_INVALID", f"{location}.path", str(raw_path))
        return None
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        candidate = reject_symlink_components(candidate)
    except AcceptanceSettlementError as exc:
        _issue(issues, exc.code, f"{location}.path", exc.detail or raw_path)
        return None
    try:
        mode = candidate.lstat().st_mode
    except OSError as exc:
        _issue(issues, "ARTIFACT_MISSING", location, str(exc))
        return None
    if not stat.S_ISREG(mode):
        _issue(issues, "ARTIFACT_NOT_REGULAR", location, raw_path)
        return None
    expected_sha = raw.get("sha256")
    expected_size = raw.get("size")
    if _sha256_file(candidate) != expected_sha:
        _issue(issues, "ARTIFACT_SHA256_MISMATCH", location, raw_path)
    if candidate.stat().st_size != expected_size:
        _issue(issues, "ARTIFACT_SIZE_MISMATCH", location, raw_path)
    return candidate


def _validate_codex_events_jsonl(
    path: Path,
    issues: list[dict[str, str]],
) -> None:
    location = "run_fingerprint.process_evidence.events_jsonl"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        _issue(issues, "CODEX_EVENTS_UNREADABLE", location, str(exc))
        return
    count = 0
    for ordinal, line in enumerate(lines, 1):
        if not line.strip():
            continue
        count += 1
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            _issue(
                issues,
                "CODEX_EVENT_JSON_INVALID",
                f"{location}[{ordinal}]",
                exc.msg,
            )
            continue
        if not isinstance(payload, Mapping):
            _issue(
                issues,
                "CODEX_EVENT_NOT_OBJECT",
                f"{location}[{ordinal}]",
                type(payload).__name__,
            )
    if count == 0:
        _issue(issues, "CODEX_EVENTS_EMPTY", location, "at least one event is required")


def _verify_file_bundle(
    raw: Any,
    expected: Mapping[str, Any],
    issues: list[dict[str, str]],
    location: str,
) -> None:
    if not isinstance(raw, Mapping):
        _issue(issues, "FILE_BUNDLE_INVALID", location, "bundle must be an object")
        return
    try:
        calculated = bundle_fingerprint(raw.get("files", []))
    except (KeyError, TypeError, ValueError) as exc:
        _issue(issues, "FILE_BUNDLE_INVALID", location, str(exc))
        return
    for key in ("digest_algorithm", "sha256", "file_count", "total_size"):
        if raw.get(key) != calculated[key]:
            _issue(issues, "FILE_BUNDLE_SELF_MISMATCH", f"{location}.{key}", str(raw.get(key)))
    if calculated != expected:
        _issue(
            issues,
            "FILE_BUNDLE_AUTHORITY_MISMATCH",
            location,
            "fingerprint files do not exactly match the validated requirement pack",
        )


def _validate_post_run_manifest(
    root: Path,
    path: Path,
    issues: list[dict[str, str]],
) -> list[dict[str, Any]]:
    payload = _read_json(path, issues, "run_fingerprint.manifests.post_run")
    if payload is None or not _validate_schema(
        payload,
        POST_RUN_SCHEMA,
        issues,
        "run_fingerprint.manifests.post_run",
    ):
        return []
    if not isinstance(payload, Mapping):
        return []
    if payload.get("project_root") != str(root):
        _issue(
            issues,
            "POST_MANIFEST_ROOT_MISMATCH",
            "run_fingerprint.manifests.post_run.project_root",
            str(payload.get("project_root")),
        )
    declared: list[dict[str, Any]] = []
    for index, raw in enumerate(payload.get("entries", [])):
        record = _verify_project_record(
            root,
            raw,
            issues,
            f"run_fingerprint.manifests.post_run.entries[{index}]",
        )
        if record is not None:
            declared.append(record)
    declared = _unique_records(
        declared,
        issues,
        "run_fingerprint.manifests.post_run.entries",
    )
    calculated = bundle_fingerprint(declared)
    expected_fields = {
        "digest_algorithm": calculated["digest_algorithm"],
        "inventory_sha256": calculated["sha256"],
        "entry_count": calculated["file_count"],
        "total_size": calculated["total_size"],
    }
    for field, expected in expected_fields.items():
        if payload.get(field) != expected:
            _issue(
                issues,
                "POST_MANIFEST_FINGERPRINT_MISMATCH",
                f"run_fingerprint.manifests.post_run.{field}",
                f"expected {expected}, got {payload.get(field)}",
            )
    actual = _post_run_inventory(root, issues)
    if declared != actual:
        _issue(
            issues,
            "POST_MANIFEST_SNAPSHOT_MISMATCH",
            "run_fingerprint.manifests.post_run.entries",
            "manifest does not exactly cover the current post-run project tree",
        )
    return actual


def _pre_run_declared_paths(
    root: Path,
    raw_path: str,
    issues: list[dict[str, str]],
) -> set[str]:
    path = _resolve_project_file(root, raw_path, issues, "pre_run_manifest.path")
    if path is None:
        return set()
    payload = _read_json(path, issues, "pre_run_manifest")
    if not isinstance(payload, Mapping) or not isinstance(payload.get("entries"), list):
        return set()
    result = {raw_path}
    for index, raw in enumerate(payload["entries"]):
        candidate = raw.get("path") if isinstance(raw, Mapping) else None
        if _project_path_parts(candidate) is None:
            _issue(
                issues,
                "PRE_MANIFEST_ENTRY_INVALID",
                f"pre_run_manifest.entries[{index}].path",
                str(candidate),
            )
            continue
        result.add(str(candidate))
    return result


def _validate_rule_qa_report(
    path: Path,
    output_path: Path,
    physical_observed: Mapping[str, Any],
    issues: list[dict[str, str]],
) -> None:
    location = "run_fingerprint.artifacts.rule_qa_report"
    payload = _read_json(path, issues, location)
    if not isinstance(payload, Mapping):
        _issue(issues, "RULE_QA_REPORT_INVALID", location, "root must be an object")
        return
    required_fields = {
        "schema_version",
        "status",
        "output_path",
        "output_sha256",
        "output_size_bytes",
        "output_identity_status",
        "path_policy",
        "slide_count",
        "checked_rules",
        "blocking_findings",
        "warnings",
    }
    missing = sorted(required_fields - set(payload))
    if missing:
        _issue(issues, "RULE_QA_REPORT_INVALID", location, f"missing fields: {missing}")
    if payload.get("schema_version") != "1.1":
        _issue(issues, "RULE_QA_REPORT_INVALID", f"{location}.schema_version", "1.1 required")
    if payload.get("status") != "pass":
        _issue(issues, "RULE_QA_REPORT_NOT_PASS", f"{location}.status", "pass required")
    if payload.get("output_identity_status") != "verified-stable":
        _issue(
            issues,
            "RULE_QA_OUTPUT_IDENTITY_INVALID",
            f"{location}.output_identity_status",
            "verified-stable required",
        )
    reported_output = payload.get("output_path")
    try:
        reported_path = Path(reported_output).expanduser().resolve(strict=False)
    except (TypeError, OSError):
        reported_path = None
    if reported_path != output_path:
        _issue(
            issues,
            "RULE_QA_OUTPUT_PATH_MISMATCH",
            f"{location}.output_path",
            str(reported_output),
        )
    actual_sha = _sha256_file(output_path)
    actual_size = output_path.stat().st_size
    if payload.get("output_sha256") != actual_sha:
        _issue(
            issues,
            "RULE_QA_OUTPUT_SHA256_MISMATCH",
            f"{location}.output_sha256",
            f"expected {actual_sha}",
        )
    if payload.get("output_size_bytes") != actual_size:
        _issue(
            issues,
            "RULE_QA_OUTPUT_SIZE_MISMATCH",
            f"{location}.output_size_bytes",
            f"expected {actual_size}",
        )
    checked = payload.get("checked_rules")
    if not isinstance(checked, list) or not REQUIRED_RULE_QA_RULES.issubset(
        {item for item in checked if isinstance(item, str)}
    ):
        _issue(
            issues,
            "RULE_QA_RULE_COVERAGE_INCOMPLETE",
            f"{location}.checked_rules",
            "all deterministic Phase 49 rules are required",
        )
    blockers = payload.get("blocking_findings")
    if blockers != []:
        _issue(
            issues,
            "RULE_QA_BLOCKERS_PRESENT",
            f"{location}.blocking_findings",
            "must be an empty array",
        )
    if not isinstance(payload.get("warnings"), list):
        _issue(issues, "RULE_QA_REPORT_INVALID", f"{location}.warnings", "array required")
    slide_count = payload.get("slide_count")
    observed_slide_count = physical_observed.get("pptx_slide_count")
    if (
        type(slide_count) is not int
        or slide_count < 1
        or (type(observed_slide_count) is int and slide_count != observed_slide_count)
    ):
        _issue(
            issues,
            "RULE_QA_SLIDE_COUNT_MISMATCH",
            f"{location}.slide_count",
            f"physical validator observed {observed_slide_count}",
        )
    policy = payload.get("path_policy")
    if not isinstance(policy, Mapping) or any(
        policy.get(key) != value
        for key, value in {
            "stored_path_format": "canonical-absolute",
            "canonicalization": "expanduser+resolve(strict=false)",
            "relative_input_resolution": "invocation-working-directory",
        }.items()
    ):
        _issue(
            issues,
            "RULE_QA_PATH_POLICY_INVALID",
            f"{location}.path_policy",
            "canonical path policy required",
        )


def _validate_private_library_cross_bind(
    root: Path,
    raw: Any,
    report_payload: Any,
    issues: list[dict[str, str]],
    *,
    private_root: Path | str | None,
    installed_skill_root: Path | str | None = None,
) -> None:
    location = "run_fingerprint.private_library"
    if not isinstance(raw, Mapping):
        _issue(issues, "PRIVATE_LIBRARY_RECORD_INVALID", location, "object required")
        return
    expected_sha = raw.get("library_index_sha256")
    expected_root_sha = raw.get("private_root_sha256")
    expected_source = raw.get("resolution_source")

    query_path = _resolve_project_file(
        root,
        QUERY_BUNDLE_PATH,
        issues,
        f"{location}.query_bundle",
    )
    query = (
        _read_json(query_path, issues, f"{location}.query_bundle")
        if query_path is not None
        else None
    )
    fingerprint_path = _resolve_project_file(
        root,
        FINGERPRINT_BUNDLE_PATH,
        issues,
        f"{location}.fingerprint_bundle",
    )
    fingerprint = (
        _read_json(fingerprint_path, issues, f"{location}.fingerprint_bundle")
        if fingerprint_path is not None
        else None
    )
    observed: list[tuple[str, Any, Any]] = []
    if isinstance(query, Mapping):
        observed.extend(
            (
                (
                    f"{location}.query_bundle.library_index_sha256",
                    query.get("library_index_sha256"),
                    expected_sha,
                ),
                (
                    f"{location}.query_bundle.library_resolution_source",
                    query.get("library_resolution_source"),
                    expected_source,
                ),
            )
        )
    if isinstance(report_payload, Mapping):
        selection = report_payload.get("selection_authority")
        if isinstance(selection, Mapping):
            observed.append(
                (
                    f"{location}.physical_report.library_index_sha256",
                    selection.get("library_index_sha256"),
                    expected_sha,
                )
            )
        else:
            _issue(
                issues,
                "PRIVATE_LIBRARY_CROSS_BIND_MISSING",
                f"{location}.physical_report.selection_authority",
                "selection authority is required",
            )
    if isinstance(fingerprint, Mapping):
        records = fingerprint.get("fingerprints")
        components = fingerprint.get("components")
        if isinstance(records, list) and len(records) == 1 and isinstance(records[0], Mapping):
            observed.append(
                (
                    f"{location}.fingerprint_bundle.library_index_sha256",
                    records[0].get("library_index_sha256"),
                    expected_sha,
                )
            )
        else:
            _issue(
                issues,
                "PRIVATE_LIBRARY_CROSS_BIND_MISSING",
                f"{location}.fingerprint_bundle.fingerprints",
                "one physical fingerprint is required",
            )
        if isinstance(components, Mapping):
            observed.append(
                (
                    f"{location}.fingerprint_bundle.private_library_resolution_source",
                    components.get("private_library_resolution_source"),
                    expected_source,
                )
            )
        else:
            _issue(
                issues,
                "PRIVATE_LIBRARY_CROSS_BIND_MISSING",
                f"{location}.fingerprint_bundle.components",
                "components object is required",
            )
    for field_location, actual, expected in observed:
        if actual != expected:
            _issue(
                issues,
                "PRIVATE_LIBRARY_CROSS_BIND_MISMATCH",
                field_location,
                f"expected {expected}, got {actual}",
            )

    if private_root is None:
        return
    requested = Path(private_root).expanduser()
    if requested.is_symlink() or not requested.is_dir():
        _issue(
            issues,
            "PRIVATE_LIBRARY_ROOT_INVALID",
            f"{location}.private_root",
            str(requested),
        )
        return
    resolved_root = requested.resolve()
    library_path = resolved_root / PHASE49_LIBRARY_RELATIVE
    if library_path.is_symlink() or not library_path.is_file():
        _issue(
            issues,
            "PRIVATE_LIBRARY_INDEX_MISSING",
            f"{location}.library_index",
            str(library_path),
        )
        return
    if not library_path.resolve().is_relative_to(resolved_root):
        _issue(
            issues,
            "PRIVATE_LIBRARY_INDEX_ESCAPE",
            f"{location}.library_index",
            str(library_path),
        )
        return
    actual_sha = _sha256_file(library_path)
    if actual_sha != expected_sha:
        _issue(
            issues,
            "PRIVATE_LIBRARY_INDEX_SHA256_MISMATCH",
            f"{location}.library_index_sha256",
            f"expected {expected_sha}, got {actual_sha}",
        )
    allowed_source_roots = [resolved_root]
    if installed_skill_root is not None:
        installed_requested = Path(installed_skill_root).expanduser()
        if installed_requested.is_symlink() or not installed_requested.is_dir():
            _issue(
                issues,
                "INSTALLED_SKILL_ROOT_INVALID",
                f"{location}.installed_skill_root",
                str(installed_requested),
            )
        else:
            allowed_source_roots.append(installed_requested.resolve())
    try:
        identity = _phase49_private_library_identity(
            library_path,
            allowed_source_roots=allowed_source_roots,
        )
    except (OSError, ValueError) as exc:
        _issue(
            issues,
            "PRIVATE_LIBRARY_SOURCE_IDENTITY_INVALID",
            f"{location}.library_index",
            str(exc),
        )
        actual_root_sha = None
    else:
        actual_root_sha = identity["private_root_sha256"]
    if actual_root_sha != expected_root_sha:
        _issue(
            issues,
            "PRIVATE_LIBRARY_ROOT_SHA256_MISMATCH",
            f"{location}.private_root_sha256",
            f"expected {expected_root_sha}, got {actual_root_sha}",
        )


def _phase49_private_library_identity(
    library_path: Path,
    *,
    allowed_source_roots: Sequence[Path] | None = None,
) -> dict[str, Any]:
    """Recompute the locked reference library and backing package identity."""

    index = load_library_index(library_path)
    if index.source_core_schema != "user-certified-reference-deck.v1":
        raise ValueError("PHASE49_PRIVATE_LIBRARY_SOURCE_SCHEMA_MISMATCH")
    package_ids = set(index.source_package_index)
    if len(package_ids) != 1:
        raise ValueError("PHASE49_PRIVATE_LIBRARY_PACKAGE_COUNT_MISMATCH")
    package_sha = next(iter(package_ids))
    if index.private_root_sha256 != package_sha:
        raise ValueError("PHASE49_PRIVATE_ROOT_PACKAGE_SHA256_MISMATCH")
    # Synthetic schema fixtures may intentionally contain no pages.  Real
    # Phase 49 indexes contain fifteen pages; whenever page records exist,
    # every referenced source package is independently re-hashed here.
    if allowed_source_roots is None:
        allowed_source_roots = (library_path.resolve().parent.parent,)
    canonical_allowed_roots: tuple[Path, ...] = tuple(
        root.expanduser().resolve(strict=True) for root in allowed_source_roots
    )
    observed_packages: set[str] = set()
    observed_paths: set[Path] = set()
    for template in index.page_templates:
        source = Path(template.source_path).expanduser()
        try:
            reject_symlink_components(source)
        except AcceptanceSettlementError as exc:
            raise ValueError(f"PHASE49_SOURCE_PACKAGE_PATH_INVALID: {exc}") from exc
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"PHASE49_SOURCE_PACKAGE_MISSING: {source}")
        source = source.resolve()
        if not any(source.is_relative_to(root) for root in canonical_allowed_roots):
            raise ValueError(
                f"PHASE49_SOURCE_PACKAGE_AUTHORITY_ESCAPE: {source}"
            )
        if _sha256_file(source) != template.package_sha256:
            raise ValueError(f"PHASE49_SOURCE_PACKAGE_SHA256_MISMATCH: {source}")
        if template.source_sha256 != template.package_sha256:
            raise ValueError(f"PHASE49_SOURCE_IDENTITY_MISMATCH: {source}")
        observed_packages.add(template.package_sha256)
        observed_paths.add(source)
    if index.page_templates and observed_packages != package_ids:
        raise ValueError("PHASE49_SOURCE_PACKAGE_COVERAGE_MISMATCH")
    return {
        "private_root_sha256": index.private_root_sha256,
        "library_index_sha256": _sha256_file(library_path),
        "source_package_sha256": package_sha,
        "source_package_count": len(observed_packages),
        "source_path_count": len(observed_paths),
    }


def validate_run_fingerprint(
    root: Path | str,
    requirement_pack: str,
    fingerprint_path: Path | str,
    *,
    private_root: Path | str,
) -> dict[str, Any]:
    """Validate the external physical-assembly run fingerprint."""

    pack_report = validate_requirement_pack(
        root,
        requirement_pack,
        pre_manifest=None,
        enforce_snapshot=False,
        scan_contamination=False,
    )
    issues = list(pack_report["issues"])
    canonical_root = Path(pack_report["root"])
    fingerprint_requested = Path(fingerprint_path).expanduser()
    fingerprint = fingerprint_requested
    try:
        fingerprint_lexical = reject_symlink_components(fingerprint_requested)
    except AcceptanceSettlementError as exc:
        _issue(issues, exc.code, "run_fingerprint.path", exc.detail)
        fingerprint_lexical = fingerprint_requested
    if fingerprint.is_symlink() or not fingerprint.is_file():
        _issue(issues, "RUN_FINGERPRINT_MISSING", "run_fingerprint", str(fingerprint))
        payload = None
    else:
        fingerprint = fingerprint_lexical.resolve()
        payload = _read_json(fingerprint, issues, "run_fingerprint")
    schema_valid = payload is not None and _validate_schema(
        payload, RUN_SCHEMA, issues, "run_fingerprint"
    )
    verified_artifacts: dict[str, dict[str, Any] | None] = {
        "pre_run_manifest": None,
        "post_run_manifest": None,
        "output_pptx": None,
        "physical_assembly_report": None,
        "rule_qa_report": None,
        "codex_events_jsonl": None,
        "codex_stderr": None,
        "runtime_identity_manifest": None,
    }
    if schema_valid and isinstance(payload, Mapping):
        expected_argv = [
            "codex",
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "--skip-git-repo-check",
            "-c",
            'model_provider="openai"',
            "-c",
            'model_reasoning_effort="medium"',
            "--cd",
            str(canonical_root),
            "-m",
            "gpt-5.6-terra",
            "--json",
            "-",
        ]
        command = payload["command"]
        if command["cwd"] != str(canonical_root):
            _issue(issues, "CODEX_CWD_MISMATCH", "run_fingerprint.command.cwd", command["cwd"])
        if command["argv"] != expected_argv:
            _issue(
                issues,
                "CODEX_ARGV_MISMATCH",
                "run_fingerprint.command.argv",
                "argv must exactly match the locked Phase 49 command",
            )
        stdin_record = _verify_project_record(
            canonical_root,
            command["stdin"],
            issues,
            "run_fingerprint.command.stdin",
        )
        executable = command["executable"]
        executable_path = _verify_external_artifact(
            {
                "path": executable["resolved_path"],
                "sha256": executable["sha256"],
                "size": executable["size"],
            },
            fingerprint.parent,
            issues,
            "run_fingerprint.command.executable",
        )
        if executable_path is not None:
            try:
                requested_resolved = Path(executable["requested_path"]).resolve(
                    strict=True
                )
            except OSError as exc:
                _issue(
                    issues,
                    "CODEX_REQUESTED_PATH_INVALID",
                    "run_fingerprint.command.executable.requested_path",
                    str(exc),
                )
            else:
                if requested_resolved != executable_path.resolve():
                    _issue(
                        issues,
                        "CODEX_EXECUTABLE_RESOLUTION_MISMATCH",
                        "run_fingerprint.command.executable.requested_path",
                        str(requested_resolved),
                    )
            try:
                version_probe = subprocess.run(
                    [str(executable_path), "--version"],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=15,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                _issue(
                    issues,
                    "CODEX_VERSION_PROBE_FAILED",
                    "run_fingerprint.command.executable.version",
                    str(exc),
                )
            else:
                actual_version = version_probe.stdout.decode(
                    "utf-8", errors="replace"
                ).strip()
                if (
                    version_probe.returncode != 0
                    or actual_version != executable["version"]
                ):
                    _issue(
                        issues,
                        "CODEX_VERSION_MISMATCH",
                        "run_fingerprint.command.executable.version",
                        actual_version,
                    )
        installed = payload["installed_skill"]
        try:
            actual_tree = tree_fingerprint(Path(installed["path"]))
        except (OSError, ValueError) as exc:
            _issue(issues, "INSTALLED_SKILL_INVALID", "run_fingerprint.installed_skill", str(exc))
        else:
            for key, actual in actual_tree.items():
                if installed.get(key) != actual:
                    _issue(
                        issues,
                        "INSTALLED_SKILL_DIGEST_MISMATCH",
                        f"run_fingerprint.installed_skill.{key}",
                        f"expected actual value {actual}",
                    )
            if installed.get("expected_sha256") != actual_tree.get("sha256"):
                _issue(
                    issues,
                    "INSTALLED_SKILL_EXPECTED_DIGEST_MISMATCH",
                    "run_fingerprint.installed_skill.expected_sha256",
                    "externally frozen digest must equal the installed tree digest",
                )
        runtime_identity = payload["runtime_identity"]
        runtime_record = runtime_identity["manifest"]
        runtime_path = _verify_external_artifact(
            runtime_record,
            fingerprint.parent,
            issues,
            "run_fingerprint.runtime_identity.manifest",
        )
        if runtime_record.get("sha256") != runtime_identity.get("expected_sha256"):
            _issue(
                issues,
                "RUNTIME_IDENTITY_EXPECTED_SHA256_MISMATCH",
                "run_fingerprint.runtime_identity.expected_sha256",
                "expected SHA must equal the externally frozen manifest bytes",
            )
        if runtime_path is not None:
            runtime_payload = _read_json(
                runtime_path,
                issues,
                "run_fingerprint.runtime_identity.manifest",
            )
            runtime_schema_valid = runtime_payload is not None and _validate_schema(
                runtime_payload,
                RUNTIME_SCHEMA_NAME,
                issues,
                "run_fingerprint.runtime_identity.manifest",
            )
            if runtime_schema_valid and isinstance(runtime_payload, Mapping):
                try:
                    expected_controller = (
                        Path(installed["path"]) / CONTROLLER_RELATIVE
                    ).resolve(strict=True)
                    runtime_components = verify_runtime_identity_payload(
                        runtime_payload,
                        installed_skill_root=Path(installed["path"]),
                        expected_installed_skill_sha256=installed["expected_sha256"],
                        actual_controller_entry=expected_controller,
                        production=True,
                        enforce_current_process=False,
                    )
                except (OSError, RuntimeIdentityError, ValueError) as exc:
                    _issue(
                        issues,
                        "RUNTIME_IDENTITY_COMPONENT_MISMATCH",
                        "run_fingerprint.runtime_identity.manifest",
                        str(exc),
                    )
                else:
                    native = runtime_payload["codex"]["native_executable"]
                    executable = command["executable"]
                    expected_executable = {
                        "requested_path": native["path"],
                        "resolved_path": native["path"],
                        "sha256": native["sha256"],
                        "size": native["size"],
                        "version": native["version"],
                    }
                    if executable != expected_executable:
                        _issue(
                            issues,
                            "CODEX_RUNTIME_IDENTITY_CROSS_BIND_MISMATCH",
                            "run_fingerprint.command.executable",
                            "command executable must equal the frozen native Codex record",
                        )
                    if runtime_components["codex_native_executable"] != Path(
                        native["path"]
                    ):
                        _issue(
                            issues,
                            "CODEX_RUNTIME_IDENTITY_PATH_MISMATCH",
                            "run_fingerprint.runtime_identity.manifest",
                            str(native["path"]),
                        )
            verified_artifacts["runtime_identity_manifest"] = {
                "path": str(runtime_path),
                "sha256": _sha256_file(runtime_path),
                "size": runtime_path.stat().st_size,
            }
        _verify_file_bundle(payload["requirements"], pack_report["requirements"], issues, "run_fingerprint.requirements")
        _verify_file_bundle(payload["assets"], pack_report["assets"], issues, "run_fingerprint.assets")
        process_evidence = payload["process_evidence"]
        events_path = _verify_external_artifact(
            process_evidence["events_jsonl"],
            fingerprint.parent,
            issues,
            "run_fingerprint.process_evidence.events_jsonl",
        )
        if events_path is not None:
            _validate_codex_events_jsonl(events_path, issues)
            verified_artifacts["codex_events_jsonl"] = {
                "path": str(events_path),
                "sha256": _sha256_file(events_path),
                "size": events_path.stat().st_size,
            }
        stderr_path = _verify_external_artifact(
            process_evidence["stderr"],
            fingerprint.parent,
            issues,
            "run_fingerprint.process_evidence.stderr",
        )
        if stderr_path is not None:
            verified_artifacts["codex_stderr"] = {
                "path": str(stderr_path),
                "sha256": _sha256_file(stderr_path),
                "size": stderr_path.stat().st_size,
            }
        pre_raw = payload["manifests"]["pre_run"]
        pre_path_value = pre_raw.get("path") if isinstance(pre_raw, Mapping) else None
        pre_path = None
        pre_declared_paths: set[str] = set()
        if _project_path_parts(pre_path_value) is None:
            _issue(
                issues,
                "PRE_MANIFEST_PATH_INVALID",
                "run_fingerprint.manifests.pre_run.path",
                "pre-run manifest must be project-relative",
            )
        else:
            pre_path = _verify_project_record(
                canonical_root,
                pre_raw,
                issues,
                "run_fingerprint.manifests.pre_run",
            )
            if pre_path is not None:
                verified_artifacts["pre_run_manifest"] = pre_path
                _validate_pre_manifest(
                    canonical_root,
                    str(pre_path_value),
                    issues,
                    enforce_snapshot=False,
                )
                pre_declared_paths = _pre_run_declared_paths(
                    canonical_root,
                    str(pre_path_value),
                    issues,
                )
        if stdin_record is not None and stdin_record["path"] not in pre_declared_paths:
            _issue(
                issues,
                "CODEX_STDIN_NOT_PREDECLARED",
                "run_fingerprint.command.stdin",
                stdin_record["path"],
            )
        post_path = _verify_external_artifact(
            payload["manifests"]["post_run"],
            fingerprint.parent,
            issues,
            "run_fingerprint.manifests.post_run",
        )
        if post_path is not None:
            verified_artifacts["post_run_manifest"] = {
                "path": str(post_path),
                "sha256": _sha256_file(post_path),
                "size": post_path.stat().st_size,
            }
        post_inventory: list[dict[str, Any]] = []
        output_raw = payload["artifacts"]["output_pptx"]
        report_raw = payload["artifacts"]["physical_assembly_report"]
        qa_raw = payload["artifacts"]["rule_qa_report"]
        output_path = _resolve_project_file(
            canonical_root,
            output_raw["path"],
            issues,
            "run_fingerprint.artifacts.output_pptx.path",
        )
        report_path = _resolve_project_file(
            canonical_root,
            report_raw["path"],
            issues,
            "run_fingerprint.artifacts.physical_assembly_report.path",
        )
        qa_path = _resolve_project_file(
            canonical_root,
            qa_raw["path"],
            issues,
            "run_fingerprint.artifacts.rule_qa_report.path",
        )
        if output_path is not None:
            _verify_project_record(canonical_root, output_raw, issues, "run_fingerprint.artifacts.output_pptx")
            if output_path.suffix.casefold() != ".pptx" or output_path.stat().st_size == 0:
                _issue(issues, "OUTPUT_PPTX_INVALID", "run_fingerprint.artifacts.output_pptx", output_raw["path"])
            verified_artifacts["output_pptx"] = {
                "path": output_raw["path"],
                "sha256": _sha256_file(output_path),
                "size": output_path.stat().st_size,
            }
        report_payload: Any = None
        if report_path is not None:
            _verify_project_record(
                canonical_root,
                report_raw,
                issues,
                "run_fingerprint.artifacts.physical_assembly_report",
            )
            report_payload = _read_json(
                report_path,
                issues,
                "run_fingerprint.artifacts.physical_assembly_report",
            )
            if report_path.suffix.casefold() != ".json" or report_path.stat().st_size == 0:
                _issue(issues, "ASSEMBLY_REPORT_INVALID", "run_fingerprint.artifacts.physical_assembly_report", report_raw["path"])
            if not isinstance(report_payload, Mapping) or report_payload.get("status") != "pass":
                _issue(issues, "ASSEMBLY_REPORT_NOT_PASS", "run_fingerprint.artifacts.physical_assembly_report.status", "pass required")
            elif output_path is not None and report_payload.get("output_sha256") != _sha256_file(output_path):
                _issue(issues, "ASSEMBLY_REPORT_OUTPUT_MISMATCH", "run_fingerprint.artifacts.physical_assembly_report.output_sha256", "output digest drift")
            try:
                physical_validation = validate_physical_report(
                    report_path,
                    canonical_root,
                )
            except Exception as exc:
                physical_validation = {
                    "status": "fail",
                    "issues": [
                        {
                            "code": "VALIDATOR_EXCEPTION",
                            "location": "validator",
                            "detail": f"{exc.__class__.__name__}: {exc}",
                        }
                    ],
                    "observed": {},
                }
            if physical_validation.get("status") != "pass":
                _issue(
                    issues,
                    "PHYSICAL_REPORT_INDEPENDENT_VALIDATION_FAILED",
                    "run_fingerprint.artifacts.physical_assembly_report",
                    f"{len(physical_validation.get('issues', []))} independent issue(s)",
                )
                for finding in physical_validation.get("issues", []):
                    if not isinstance(finding, Mapping):
                        continue
                    _issue(
                        issues,
                        f"PHYSICAL_REPORT_{finding.get('code', 'INVALID')}",
                        f"physical_report.{finding.get('location', 'unknown')}",
                        str(finding.get("detail", "")),
                    )
            verified_artifacts["physical_assembly_report"] = {
                "path": report_raw["path"],
                "sha256": _sha256_file(report_path),
                "size": report_path.stat().st_size,
            }
        else:
            physical_validation = {"status": "fail", "issues": [], "observed": {}}
        _validate_private_library_cross_bind(
            canonical_root,
            payload["private_library"],
            report_payload,
            issues,
            private_root=private_root,
            installed_skill_root=installed["path"],
        )
        if qa_path is not None:
            _verify_project_record(
                canonical_root,
                qa_raw,
                issues,
                "run_fingerprint.artifacts.rule_qa_report",
            )
            if output_path is not None:
                _validate_rule_qa_report(
                    qa_path,
                    output_path,
                    physical_validation.get("observed", {}),
                    issues,
                )
            verified_artifacts["rule_qa_report"] = {
                "path": qa_raw["path"],
                "sha256": _sha256_file(qa_path),
                "size": qa_path.stat().st_size,
            }

        evidence_records: list[dict[str, Any]] = []
        for index, raw in enumerate(payload["artifacts"]["evidence_outputs"]):
            record = _verify_project_record(
                canonical_root,
                raw,
                issues,
                f"run_fingerprint.artifacts.evidence_outputs[{index}]",
            )
            if record is not None:
                evidence_records.append(record)
        evidence_records = _unique_records(
            evidence_records,
            issues,
            "run_fingerprint.artifacts.evidence_outputs",
        )
        evidence_paths = {record["path"] for record in evidence_records}
        if evidence_paths != set(EVIDENCE_OUTPUT_PATHS):
            _issue(
                issues,
                "EVIDENCE_OUTPUT_SET_MISMATCH",
                "run_fingerprint.artifacts.evidence_outputs",
                "the exact eight Phase 49 evidence outputs are required",
            )
        if evidence_paths == set(EVIDENCE_OUTPUT_PATHS):
            try:
                validate_distinct_file_paths(
                    root=canonical_root,
                    relative_paths=[record["path"] for record in evidence_records],
                )
            except (AcceptanceSettlementError, OSError) as exc:
                code = (
                    exc.code
                    if isinstance(exc, AcceptanceSettlementError)
                    else "EVIDENCE_PATH_INSPECTION_FAILED"
                )
                detail = (
                    exc.detail
                    if isinstance(exc, AcceptanceSettlementError)
                    else str(exc)
                )
                _issue(
                    issues,
                    code,
                    "run_fingerprint.artifacts.evidence_outputs",
                    detail,
                )
            for relative, schema_name in EVIDENCE_JSON_SCHEMAS.items():
                evidence_path = canonical_root / relative
                evidence_payload = _read_json(
                    evidence_path,
                    issues,
                    f"run_fingerprint.artifacts.evidence_outputs.{relative}",
                )
                if evidence_payload is not None:
                    _validate_evidence_schema(
                        evidence_payload,
                        schema_name,
                        issues,
                        f"run_fingerprint.artifacts.evidence_outputs.{relative}",
                    )
            _validate_run_summary(
                canonical_root / "evidence/run-summary.md",
                output_path=output_path,
                report_payload=report_payload,
                issues=issues,
            )
        evidence_by_path = {record["path"]: record for record in evidence_records}
        for role_path, role_raw, role_name in (
            (PHYSICAL_REPORT_PATH, report_raw, "physical_assembly_report"),
            (RULE_QA_PATH, qa_raw, "rule_qa_report"),
        ):
            if evidence_by_path.get(role_path) != {
                "path": role_raw.get("path"),
                "sha256": role_raw.get("sha256"),
                "size": role_raw.get("size"),
            }:
                _issue(
                    issues,
                    "EVIDENCE_ROLE_RECORD_MISMATCH",
                    f"run_fingerprint.artifacts.{role_name}",
                    "role record must exactly equal its evidence_outputs record",
                )

        if post_path is not None:
            post_inventory = _validate_post_run_manifest(
                canonical_root,
                post_path,
                issues,
            )
        actual_paths = {record["path"] for record in post_inventory}
        pptx_paths = {
            record["path"]
            for record in post_inventory
            if PurePosixPath(record["path"]).suffix.casefold() == ".pptx"
        }
        if pptx_paths != {OUTPUT_PPTX_PATH}:
            _issue(
                issues,
                "POST_RUN_PPTX_SET_MISMATCH",
                "run_fingerprint.manifests.post_run.entries",
                f"expected only {OUTPUT_PPTX_PATH}, got {sorted(pptx_paths)}",
            )
        actual_evidence_paths = {
            record["path"]
            for record in post_inventory
            if PurePosixPath(record["path"]).parts[:1] == ("evidence",)
        }
        if actual_evidence_paths != set(EVIDENCE_OUTPUT_PATHS):
            _issue(
                issues,
                "POST_RUN_EVIDENCE_SET_MISMATCH",
                "run_fingerprint.manifests.post_run.entries",
                "project evidence directory must contain exactly the eight declared outputs",
            )
        expected_paths = pre_declared_paths | {OUTPUT_PPTX_PATH} | set(EVIDENCE_OUTPUT_PATHS)
        if actual_paths != expected_paths:
            undeclared = sorted(actual_paths - expected_paths)
            missing = sorted(expected_paths - actual_paths)
            _issue(
                issues,
                "POST_RUN_OUTPUT_SET_MISMATCH",
                "run_fingerprint.manifests.post_run.entries",
                f"undeclared={undeclared}; missing={missing}",
            )
        if (
            events_path is not None
            and stderr_path is not None
            and post_path is not None
        ):
            authority_paths: dict[str, Path | str] = {
                "project": Path(root),
                "installed_skill": installed["path"],
                "private_root": private_root,
                "codex_runtime": executable["resolved_path"],
            }
            runtime_identity = payload.get("runtime_identity")
            if isinstance(runtime_identity, Mapping):
                manifest_record = runtime_identity.get("manifest")
                if isinstance(manifest_record, Mapping):
                    value = manifest_record.get("path")
                    if isinstance(value, str) and value:
                        authority_paths["runtime_identity.manifest"] = value
            try:
                validate_harness_topology(
                    artifact_paths={
                        "events_jsonl": process_evidence["events_jsonl"]["path"],
                        "stderr": process_evidence["stderr"]["path"],
                        "post_run_manifest": payload["manifests"]["post_run"]["path"],
                        "run_fingerprint": fingerprint_requested,
                    },
                    authority_paths=authority_paths,
                )
            except (AcceptanceSettlementError, OSError) as exc:
                code = (
                    exc.code
                    if isinstance(exc, AcceptanceSettlementError)
                    else "HARNESS_TOPOLOGY_INSPECTION_FAILED"
                )
                detail = (
                    exc.detail
                    if isinstance(exc, AcceptanceSettlementError)
                    else str(exc)
                )
                _issue(issues, code, "run_fingerprint.external_harness", detail)
            try:
                verify_settlement_evidence(
                    process_evidence.get("settlement"),
                    post_inventory=post_inventory,
                )
            except AcceptanceSettlementError as exc:
                _issue(
                    issues,
                    exc.code,
                    "run_fingerprint.process_evidence.settlement",
                    exc.detail,
                )
        exit_record = payload["exit"]
        if exit_record["status"] != "success" or exit_record["code"] != 0:
            _issue(issues, "CODEX_RUN_NOT_SUCCESSFUL", "run_fingerprint.exit", json.dumps(exit_record, sort_keys=True))
    issues.sort(key=lambda item: (item["location"], item["code"], item["detail"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "mode": "run",
        "status": "PASS" if not issues else "FAIL",
        "root": str(canonical_root),
        "run_fingerprint": (
            {
                "path": str(fingerprint),
                "sha256": _sha256_file(fingerprint),
                "size": fingerprint.stat().st_size,
            }
            if fingerprint.is_file()
            else None
        ),
        "requirements": pack_report["requirements"],
        "assets": pack_report["assets"],
        "verified_artifacts": verified_artifacts,
        "issues": issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Window-PPTX v6.1 clean-room inputs or a completed run."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    pack = subparsers.add_parser("pack", help="validate the frozen pre-run clean pack")
    pack.add_argument("--root", type=Path, required=True)
    pack.add_argument("--requirement-pack", default="annual-work-report.requirement-pack.v1.json")
    pack.add_argument("--pre-manifest", default="PRE-RUN-MANIFEST.json")
    run = subparsers.add_parser("run", help="validate a completed external run fingerprint")
    run.add_argument("--root", type=Path, required=True)
    run.add_argument("--requirement-pack", default="annual-work-report.requirement-pack.v1.json")
    run.add_argument("--fingerprint", type=Path, required=True)
    run.add_argument("--private-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "pack":
            report = validate_requirement_pack(
                args.root,
                args.requirement_pack,
                pre_manifest=args.pre_manifest,
            )
        else:
            report = validate_run_fingerprint(
                args.root,
                args.requirement_pack,
                args.fingerprint,
                private_root=args.private_root,
            )
    except Exception as exc:  # pragma: no cover - last-resort machine-readable gate
        report = {
            "schema_version": SCHEMA_VERSION,
            "contract_id": CONTRACT_ID,
            "mode": getattr(args, "command", "unknown"),
            "status": "NOT_RUN",
            "issues": [
                {
                    "code": "VALIDATOR_INTERNAL_ERROR",
                    "location": "validator",
                    "detail": f"{exc.__class__.__name__}: {exc}",
                }
            ],
        }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if report["status"] == "PASS":
        return 0
    return 2 if report["status"] == "NOT_RUN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
