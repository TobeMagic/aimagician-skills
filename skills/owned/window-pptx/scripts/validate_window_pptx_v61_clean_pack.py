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
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "1.0"
CONTRACT_ID = "window-pptx-v61-clean-pack"
REQUIREMENT_SCHEMA = "annual-work-report-requirement-pack.v1.schema.json"
RUN_SCHEMA = "physical-assembly-run-fingerprint.v1.schema.json"
SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schemas"

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
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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
    if candidate.is_symlink():
        _issue(issues, "SYMLINK_FORBIDDEN", f"{location}.path", raw_path)
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


def validate_run_fingerprint(
    root: Path | str,
    requirement_pack: str,
    fingerprint_path: Path | str,
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
    fingerprint = Path(fingerprint_path)
    if fingerprint.is_symlink() or not fingerprint.is_file():
        _issue(issues, "RUN_FINGERPRINT_MISSING", "run_fingerprint", str(fingerprint))
        payload = None
    else:
        fingerprint = fingerprint.resolve()
        payload = _read_json(fingerprint, issues, "run_fingerprint")
    schema_valid = payload is not None and _validate_schema(
        payload, RUN_SCHEMA, issues, "run_fingerprint"
    )
    verified_artifacts: dict[str, dict[str, Any] | None] = {
        "pre_run_manifest": None,
        "post_run_manifest": None,
        "output_pptx": None,
        "physical_assembly_report": None,
    }
    if schema_valid and isinstance(payload, Mapping):
        expected_argv = [
            "codex",
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "--skip-git-repo-check",
            "-c",
            'model_provider="OpenAI"',
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
        _verify_file_bundle(payload["requirements"], pack_report["requirements"], issues, "run_fingerprint.requirements")
        _verify_file_bundle(payload["assets"], pack_report["assets"], issues, "run_fingerprint.assets")
        pre_raw = payload["manifests"]["pre_run"]
        pre_path_value = pre_raw.get("path") if isinstance(pre_raw, Mapping) else None
        pre_path = None
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
            _read_json(post_path, issues, "run_fingerprint.manifests.post_run")
        output_raw = payload["artifacts"]["output_pptx"]
        report_raw = payload["artifacts"]["physical_assembly_report"]
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
        if output_path is not None:
            _verify_project_record(canonical_root, output_raw, issues, "run_fingerprint.artifacts.output_pptx")
            if output_path.suffix.casefold() != ".pptx" or output_path.stat().st_size == 0:
                _issue(issues, "OUTPUT_PPTX_INVALID", "run_fingerprint.artifacts.output_pptx", output_raw["path"])
            verified_artifacts["output_pptx"] = {
                "path": output_raw["path"],
                "sha256": _sha256_file(output_path),
                "size": output_path.stat().st_size,
            }
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
            verified_artifacts["physical_assembly_report"] = {
                "path": report_raw["path"],
                "sha256": _sha256_file(report_path),
                "size": report_path.stat().st_size,
            }
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
