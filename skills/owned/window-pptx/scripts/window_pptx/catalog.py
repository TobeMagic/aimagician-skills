"""Content-addressed Catalog v3 loader, compatibility adapter, and query API."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_CATALOG = Path(__file__).resolve().parents[2] / "registries" / "catalog-v3.json"
DEFAULT_LEGACY = (
    Path(__file__).resolve().parents[2] / "registries" / "legacy-templates.json"
)


class CatalogError(ValueError):
    """Catalog data is malformed, unsafe, or cannot close dependencies."""


def catalog_id(
    source_id: str,
    item_id: str,
    version_id: str,
    content_sha256: str,
) -> str:
    """Derive a stable ID without incorporating a local/private path."""

    normalized = "\n".join(
        part.strip().casefold()
        for part in (source_id, item_id, version_id, content_sha256)
    )
    return f"tplv3-{hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:24]}"


def _required_string(entry: dict[str, Any], key: str, prefix: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{prefix}.{key} must be a non-empty string")
    return value.strip()


def _string_list(entry: dict[str, Any], key: str, prefix: str) -> list[str]:
    value = entry[key]
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise CatalogError(f"{prefix}.{key} must be an array of strings")
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        raise CatalogError(f"{prefix}.{key} must not contain duplicates")
    return sorted(normalized)


def _validate_entry(entry: Any, index: int) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise CatalogError(f"entries[{index}] must be an object")
    prefix = f"entries[{index}]"
    required = {
        "catalog_item_id",
        "source_id",
        "item_id",
        "version_id",
        "content_sha256",
        "media_type",
        "geometry",
        "phash",
        "capacity",
        "scenarios",
        "style_tags",
        "rights_decision",
        "rights_record_digest",
        "quarantine_disposition",
        "quarantine_report_digest",
        "dependency_ids",
        "editability",
        "certification",
        "provenance",
    }
    unknown = sorted(set(entry) - required)
    if unknown:
        raise CatalogError(f"{prefix} has unknown fields: {', '.join(unknown)}")
    missing = sorted(required - set(entry))
    if missing:
        raise CatalogError(f"{prefix} is missing: {', '.join(missing)}")
    result = dict(entry)
    for key in (
        "catalog_item_id",
        "source_id",
        "item_id",
        "version_id",
        "content_sha256",
        "media_type",
        "rights_decision",
        "editability",
        "certification",
        "quarantine_disposition",
    ):
        result[key] = _required_string(result, key, prefix)
    if not result["content_sha256"].startswith("sha256:"):
        raise CatalogError(f"{prefix}.content_sha256 must use sha256:")
    for key in ("rights_record_digest", "quarantine_report_digest"):
        value = result[key]
        if value is not None and (
            not isinstance(value, str)
            or not value.startswith("sha256:")
            or len(value) != 71
            or any(character not in "0123456789abcdef" for character in value[7:])
        ):
            raise CatalogError(f"{prefix}.{key} must be null or sha256")
    if len(result["content_sha256"]) != 71 or any(
        character not in "0123456789abcdef"
        for character in result["content_sha256"][7:]
    ):
        raise CatalogError(f"{prefix}.content_sha256 must contain 64 lowercase hex")
    if result["rights_decision"] not in {"allowed", "restricted", "unknown"}:
        raise CatalogError(f"{prefix}.rights_decision is invalid")
    if result["editability"] not in {
        "native_editable",
        "partially_editable",
        "flattened",
        "unknown",
    }:
        raise CatalogError(f"{prefix}.editability is invalid")
    if result["certification"] not in {
        "certified",
        "quarantined",
        "unverified",
        "revoked",
    }:
        raise CatalogError(f"{prefix}.certification is invalid")
    if result["quarantine_disposition"] not in {
        "ACCEPT",
        "QUARANTINED",
        "REJECTED",
        "NOT_RUN",
    }:
        raise CatalogError(f"{prefix}.quarantine_disposition is invalid")
    expected_id = catalog_id(
        result["source_id"],
        result["item_id"],
        result["version_id"],
        result["content_sha256"],
    )
    if result["catalog_item_id"] != expected_id:
        raise CatalogError(f"{prefix}.catalog_item_id must equal {expected_id}")
    for key in ("scenarios", "style_tags", "dependency_ids", "provenance"):
        result[key] = _string_list(result, key, prefix)
    geometry = result["geometry"]
    if not isinstance(geometry, dict) or set(geometry) != {
        "width_in",
        "height_in",
        "slide_count",
    }:
        raise CatalogError(f"{prefix}.geometry must match the v3 contract")
    if any(
        not isinstance(geometry[key], (int, float))
        or isinstance(geometry[key], bool)
        or geometry[key] <= 0
        for key in ("width_in", "height_in")
    ) or (
        not isinstance(geometry["slide_count"], int)
        or isinstance(geometry["slide_count"], bool)
        or geometry["slide_count"] < 1
    ):
        raise CatalogError(f"{prefix}.geometry values are invalid")
    capacity = result["capacity"]
    if not isinstance(capacity, dict) or set(capacity) != {
        "min_slides",
        "max_slides",
        "max_text_chars",
    }:
        raise CatalogError(f"{prefix}.capacity must match the v3 contract")
    if any(
        not isinstance(capacity[key], int)
        or isinstance(capacity[key], bool)
        or capacity[key] < 1
        for key in capacity
    ) or capacity["min_slides"] > capacity["max_slides"]:
        raise CatalogError(f"{prefix}.capacity values are invalid")
    phash = result["phash"]
    if not isinstance(phash, dict) or phash.get("state") not in {
        "present",
        "not_applicable",
        "pending",
    }:
        raise CatalogError(f"{prefix}.phash state is invalid")
    if phash["state"] == "present":
        value = phash.get("value")
        if (
            set(phash) != {"state", "value"}
            or not isinstance(value, str)
            or not value
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise CatalogError(f"{prefix}.phash value is invalid")
    elif set(phash) != {"state"}:
        raise CatalogError(f"{prefix}.phash value is forbidden for this state")
    if result["certification"] == "certified":
        if result["rights_decision"] != "allowed":
            raise CatalogError(f"{prefix}: certified item requires allowed rights")
        if result["quarantine_disposition"] != "ACCEPT":
            raise CatalogError(f"{prefix}: certified item requires ACCEPT quarantine")
        if not result["rights_record_digest"] or not result["quarantine_report_digest"]:
            raise CatalogError(f"{prefix}: certified item requires evidence digests")
        if result["editability"] == "unknown":
            raise CatalogError(f"{prefix}: certified item requires known editability")
        if not result["style_tags"] or not result["provenance"]:
            raise CatalogError(f"{prefix}: certified metadata is incomplete")
    return result


def load_catalog(path: Path | str | None = None) -> dict[str, Any]:
    """Load, validate, and content-dedupe Catalog v3."""

    source = Path(path) if path is not None else DEFAULT_CATALOG
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot load catalog: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version",
        "catalog_id",
        "entries",
    }:
        raise CatalogError("catalog fields do not match v3")
    if raw.get("schema_version") != "3.0":
        raise CatalogError("catalog schema_version must be 3.0")
    if not isinstance(raw["catalog_id"], str) or not raw["catalog_id"].strip():
        raise CatalogError("catalog catalog_id must be a non-empty string")
    entries = raw.get("entries")
    if not isinstance(entries, list):
        raise CatalogError("catalog entries must be an array")
    validated = [_validate_entry(entry, index) for index, entry in enumerate(entries)]
    by_hash: dict[str, dict[str, Any]] = {}
    aliases: dict[str, list[str]] = {}
    rank = {"certified": 0, "unverified": 1, "quarantined": 2, "revoked": 3}
    for entry in validated:
        digest = entry["content_sha256"]
        current = by_hash.get(digest)
        entry_key = (rank[entry["certification"]], entry["catalog_item_id"])
        current_key = (
            rank[current["certification"]],
            current["catalog_item_id"],
        ) if current is not None else None
        if current is None or entry_key < current_key:
            if current is not None:
                replacement_aliases = aliases.pop(current["catalog_item_id"], [])
                aliases.setdefault(entry["catalog_item_id"], []).extend(
                    [current["catalog_item_id"], *replacement_aliases]
                )
            by_hash[digest] = entry
        else:
            aliases.setdefault(current["catalog_item_id"], []).append(
                entry["catalog_item_id"]
            )
    canonical = sorted(by_hash.values(), key=lambda item: item["catalog_item_id"])
    return {
        "schema_version": "3.0",
        "catalog_id": raw["catalog_id"].strip(),
        "entries": canonical,
        "aliases": {key: sorted(value) for key, value in sorted(aliases.items())},
    }


def load_legacy_catalog(path: Path | str | None = None) -> list[dict[str, Any]]:
    """Adapt the old registry without granting certification."""

    source = Path(path) if path is not None else DEFAULT_LEGACY
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot load legacy registry: {exc}") from exc
    templates = raw.get("templates") if isinstance(raw, dict) else None
    if not isinstance(templates, list):
        raise CatalogError("legacy registry templates must be an array")
    return [
        {
            "catalog_item_id": item["id"],
            "source_id": "legacy-registry",
            "item_id": item["id"],
            "version_id": "legacy",
            "content_sha256": f"unavailable:{item['id']}",
            "scenarios": [],
            "style_tags": [],
            "rights_decision": "unknown",
            "rights_record_digest": None,
            "quarantine_disposition": "NOT_RUN",
            "quarantine_report_digest": None,
            "dependency_ids": [],
            "editability": "unknown",
            "certification": "unverified",
            "auto_recommend": False,
            "legacy_path": item.get("path"),
        }
        for item in templates
    ]


def query_catalog(
    catalog: dict[str, Any],
    *,
    scenario: str | None = None,
    style_tags: Iterable[str] = (),
    minimum_slides: int | None = None,
    include_uncertified: bool = False,
) -> list[dict[str, Any]]:
    """Return deterministic, certified-only matches by default."""

    required_tags = set(style_tags)
    if minimum_slides is not None and (
        not isinstance(minimum_slides, int)
        or isinstance(minimum_slides, bool)
        or minimum_slides < 1
    ):
        raise CatalogError("minimum_slides must be a positive integer")
    results: list[dict[str, Any]] = []
    for index, entry in enumerate(catalog.get("entries", [])):
        if not include_uncertified and (
            entry.get("certification") != "certified"
            or entry.get("rights_decision") != "allowed"
        ):
            continue
        if not include_uncertified:
            entry = _validate_entry(entry, index)
        if not include_uncertified:
            try:
                dependency_closure(catalog, entry["catalog_item_id"])
            except CatalogError:
                continue
        if scenario and scenario not in entry.get("scenarios", []):
            continue
        if required_tags and not required_tags.issubset(set(entry.get("style_tags", []))):
            continue
        if minimum_slides is not None:
            capacity = entry.get("capacity", {})
            if capacity.get("max_slides", 0) < minimum_slides:
                continue
        results.append(entry)
    return sorted(
        results,
        key=lambda item: (
            -len(required_tags.intersection(item.get("style_tags", []))),
            item["catalog_item_id"],
        ),
    )


def dependency_closure(
    catalog: dict[str, Any],
    catalog_item_id: str,
) -> list[str]:
    """Return dependencies before the root and reject unsafe closure."""

    validated = [
        _validate_entry(item, index)
        for index, item in enumerate(catalog.get("entries", []))
    ]
    entries = {item["catalog_item_id"]: item for item in validated}
    aliases = {
        alias: canonical
        for canonical, values in catalog.get("aliases", {}).items()
        for alias in values
    }
    result: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> None:
        item_id = aliases.get(item_id, item_id)
        if item_id in visiting:
            raise CatalogError(f"dependency cycle at {item_id}")
        if item_id in visited:
            return
        entry = entries.get(item_id)
        if entry is None:
            raise CatalogError(f"missing dependency: {item_id}")
        if entry.get("certification") != "certified":
            raise CatalogError(f"uncertified dependency: {item_id}")
        visiting.add(item_id)
        for dependency_id in entry.get("dependency_ids", []):
            visit(dependency_id)
        visiting.remove(item_id)
        visited.add(item_id)
        result.append(item_id)

    visit(aliases.get(catalog_item_id, catalog_item_id))
    return result
