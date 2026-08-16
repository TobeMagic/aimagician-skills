"""Safe, dry-run-first acquisition contracts for the private template library."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


COMMANDS = {"discover", "sync", "ingest", "certify", "query"}
STATUSES = {
    "PASS",
    "NEEDS_AUTH",
    "NEEDS_RIGHTS",
    "QUARANTINED",
    "PARTIAL",
    "FAIL",
}


class AcquisitionError(ValueError):
    """An acquisition request violates the private-library contract."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _resolved_below(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _validate_private_root(root: Path) -> None:
    if root.name != ".private" or root.is_symlink():
        raise AcquisitionError("private root must be a non-symlink named .private")


def _host(url: str, allow_insecure_http_hosts: Iterable[str] = ()) -> str:
    parsed = urlsplit(url)
    if not parsed.hostname:
        raise AcquisitionError("acquisition URLs must use https with a hostname")
    host = parsed.hostname.casefold().rstrip(".")
    insecure = {item.casefold().rstrip(".") for item in allow_insecure_http_hosts}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and host in insecure):
        raise AcquisitionError("acquisition URLs must use https unless the source host has an explicit HTTP exception")
    return host


def authorization_scope(
    origin_url: str,
    target_url: str,
    allowlisted_hosts: Iterable[str],
    allow_insecure_http_hosts: Iterable[str] = (),
) -> str:
    """Return attach, strip, or reject without reading any credential."""

    allowed = {item.casefold().rstrip(".") for item in allowlisted_hosts}
    origin = _host(origin_url, allow_insecure_http_hosts)
    target = _host(target_url, allow_insecure_http_hosts)
    if origin not in allowed:
        raise AcquisitionError("origin host is not allowlisted")
    if target not in allowed:
        return "reject"
    return "attach" if target == origin else "strip"


def validate_private_credential_file(
    credential_path: Path | str,
    private_root: Path | str,
) -> dict[str, str]:
    """Validate a private credential file and return only a one-way digest."""

    root = Path(private_root)
    path = Path(credential_path)
    _validate_private_root(root)
    if not _resolved_below(path, root):
        raise AcquisitionError("credential file must resolve below the private root")
    if not path.is_file():
        raise AcquisitionError("credential file is unavailable")
    try:
        secret = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise AcquisitionError("credential file cannot be read safely") from exc
    if not secret:
        raise AcquisitionError("credential file is empty")
    return {
        "status": "PASS",
        "credential_digest": _sha256_text(secret),
    }


def build_acquisition_manifest(
    *,
    command: str,
    source_id: str,
    origin: str,
    allowlisted_hosts: Iterable[str],
    requested_item_ids: Iterable[str] = (),
    completed_item_ids: Iterable[str] = (),
    unavailable_item_ids: Iterable[str] = (),
    status: str = "PASS",
    mode: str = "dry_run",
    state_path: str | None = None,
    resume_cursor: str | None = None,
    findings: Iterable[dict[str, Any]] = (),
    allow_insecure_http_hosts: Iterable[str] = (),
) -> dict[str, Any]:
    """Build a deterministic metadata-only acquisition manifest."""

    if command not in COMMANDS:
        raise AcquisitionError(f"unsupported acquisition command: {command}")
    if mode not in {"dry_run", "apply"}:
        raise AcquisitionError("mode must be dry_run or apply")
    if status not in STATUSES:
        raise AcquisitionError("unsupported acquisition status")
    if resume_cursor is not None and not isinstance(resume_cursor, str):
        raise AcquisitionError("resume_cursor must be a string or null")
    if mode == "apply":
        candidate = Path(state_path or "")
        if (
            not state_path
            or candidate.is_absolute()
            or any(part in {"", ".", ".."} for part in candidate.parts)
        ):
            raise AcquisitionError("apply mode requires a safe relative state_path")
    elif state_path is not None:
        raise AcquisitionError("dry_run mode cannot declare state_path")
    source = source_id.strip()
    if not source:
        raise AcquisitionError("source_id must be non-empty")
    hosts: list[str] = []
    for item in allowlisted_hosts:
        if (
            not isinstance(item, str)
            or not item
            or any(character in item for character in "/:@")
        ):
            raise AcquisitionError("allowlisted hosts must be bare hostnames")
        hosts.append(item.casefold().rstrip("."))
    hosts = sorted(set(hosts))
    if origin:
        origin_host = _host(origin, allow_insecure_http_hosts)
        if hosts and origin_host not in hosts:
            raise AcquisitionError("origin host is not allowlisted")
    normalized_findings: list[dict[str, str]] = []
    for finding in findings:
        if not isinstance(finding, dict) or not set(finding).issubset({"code", "path"}):
            raise AcquisitionError("findings may contain only code and path")
        code = finding.get("code")
        if not isinstance(code, str) or not code.strip():
            raise AcquisitionError("finding code must be a non-empty string")
        normalized = {"code": code.strip()}
        if "path" in finding:
            path = finding["path"]
            if not isinstance(path, str):
                raise AcquisitionError("finding path must be a string")
            normalized["path"] = path
        normalized_findings.append(normalized)
    item_sets: dict[str, list[str]] = {}
    for key, values in (
        ("requested_item_ids", requested_item_ids),
        ("completed_item_ids", completed_item_ids),
        ("unavailable_item_ids", unavailable_item_ids),
    ):
        normalized_values = list(values)
        if any(
            not isinstance(item, str) or not item.strip()
            for item in normalized_values
        ):
            raise AcquisitionError(f"{key} must contain non-empty strings")
        item_sets[key] = sorted({item.strip() for item in normalized_values})
    if set(item_sets["completed_item_ids"]).intersection(
        item_sets["unavailable_item_ids"]
    ):
        raise AcquisitionError("completed and unavailable items must be disjoint")
    normalized_findings.sort(key=lambda item: (item["code"], item.get("path", "")))
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "command": command,
        "mode": mode,
        "status": status,
        "source_id": source,
        "origin": origin,
        "allowlisted_hosts": hosts,
        **item_sets,
        "resume_cursor": resume_cursor,
        "state_path": state_path,
        "findings": normalized_findings,
    }
    body["state_digest"] = _sha256_text(_canonical_json(body))
    return body


def write_resume_state(
    private_root: Path | str,
    relative_path: Path | str,
    manifest: dict[str, Any],
) -> Path:
    """Atomically persist state below the private root."""

    root = Path(private_root)
    relative = Path(relative_path)
    _validate_private_root(root)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise AcquisitionError("resume state path must be a safe relative path")
    target = root / relative
    if not _resolved_below(target, root):
        raise AcquisitionError("resume state path escapes the private root")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = f"{json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2)}\n"
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, target)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
    return target
