"""Rights-record validation and evidence-bound certification decisions."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .quarantine import validate_quarantine_report


class RightsError(ValueError):
    """A rights record is missing, malformed, or insufficient."""


def canonical_digest(value: Any) -> str:
    """Return a deterministic digest without exposing source evidence bytes."""

    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def validate_rights_record(value: Any) -> dict[str, Any]:
    """Validate the strict RightsRecord v1 runtime contract."""

    if not isinstance(value, dict):
        raise RightsError("rights record must be an object")
    required = {
        "schema_version",
        "status",
        "source_id",
        "item_id",
        "access_basis",
        "use_scope",
        "redistribution_state",
        "evidence_references",
        "reviewed_at",
        "decision",
    }
    unknown = sorted(set(value) - required)
    missing = sorted(required - set(value))
    if unknown:
        raise RightsError(f"rights record has unknown fields: {', '.join(unknown)}")
    if missing:
        raise RightsError(f"rights record is missing: {', '.join(missing)}")
    record = dict(value)
    if record["schema_version"] != "1.0":
        raise RightsError("rights record schema_version must be 1.0")
    for key in ("source_id", "item_id", "reviewed_at"):
        if not isinstance(record[key], str) or not record[key].strip():
            raise RightsError(f"rights record {key} must be a non-empty string")
        record[key] = record[key].strip()
    try:
        datetime.fromisoformat(record["reviewed_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise RightsError("rights record reviewed_at must be ISO-8601") from exc
    if record["access_basis"] not in {
        "public",
        "owned",
        "licensed",
        "client_authorized",
        "unknown",
    }:
        raise RightsError("rights record access_basis is invalid")
    if record["use_scope"] not in {
        "metadata_only",
        "local_adaptation",
        "client_delivery",
        "redistribution",
    }:
        raise RightsError("rights record use_scope is invalid")
    if record["redistribution_state"] not in {
        "allowed",
        "restricted",
        "prohibited",
        "unknown",
    }:
        raise RightsError("rights record redistribution_state is invalid")
    if record["decision"] not in {"allowed", "restricted", "unknown"}:
        raise RightsError("rights record decision is invalid")
    references = record["evidence_references"]
    if not isinstance(references, list) or any(
        not isinstance(item, str) or not item.strip() for item in references
    ):
        raise RightsError("rights record evidence_references must be strings")
    record["evidence_references"] = sorted(set(references))
    expected_status = "PASS" if record["decision"] == "allowed" else "NEEDS_RIGHTS"
    if record["status"] != expected_status:
        raise RightsError("rights record status contradicts decision")
    if record["decision"] == "allowed":
        if record["access_basis"] == "unknown" or not references:
            raise RightsError("allowed rights require known basis and evidence")
    return record


def load_rights_record(path: Path | str) -> dict[str, Any]:
    """Load a rights record from a private file without returning its path."""

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RightsError("rights record cannot be loaded") from exc
    return validate_rights_record(value)


def certification_evidence(
    *,
    source_id: str,
    item_id: str,
    quarantine_report: dict[str, Any],
    rights_record: dict[str, Any],
) -> dict[str, str]:
    """Return non-secret evidence digests only when certification may proceed."""

    rights = validate_rights_record(rights_record)
    if rights["source_id"] != source_id or rights["item_id"] != item_id:
        raise RightsError("rights record identity does not match certification target")
    if rights["decision"] != "allowed":
        raise RightsError("rights decision does not allow certification")
    if rights["use_scope"] == "metadata_only":
        raise RightsError("metadata-only rights do not allow package certification")
    try:
        quarantine = validate_quarantine_report(quarantine_report)
    except ValueError as exc:
        raise RightsError("quarantine report is invalid") from exc
    if (
        quarantine["status"] != "PASS"
        or quarantine["disposition"] != "ACCEPT"
        or quarantine["findings"] != []
    ):
        raise RightsError("certification requires an ACCEPT quarantine report")
    package_sha256 = quarantine["package_sha256"]
    if not isinstance(package_sha256, str) or not package_sha256.startswith("sha256:"):
        raise RightsError("quarantine report lacks a package SHA-256")
    return {
        "content_sha256": package_sha256,
        "quarantine_disposition": "ACCEPT",
        "quarantine_report_digest": canonical_digest(quarantine),
        "rights_record_digest": canonical_digest(rights),
        "rights_decision": "allowed",
    }
