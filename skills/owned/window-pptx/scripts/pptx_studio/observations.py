"""Sanitized, hash-bound visual-observation contracts for Agnes evidence."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


class ObservationError(ValueError):
    """Raised when a visual observation is ungrounded or leaks private data."""


_PAGE_ID = re.compile(r"^page_[0-9a-f]{24}_[0-9]{3}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_TOP_LEVEL = {"schema_version", "page_id", "image_sha256", "observation"}
_ALLOWED_OBSERVATION = {
    "visual_style", "composition", "hierarchy", "semantic_tags",
    "suggested_roles", "text_density", "uncertainty",
}
_FORBIDDEN_KEY = re.compile(r"(?:path|locator|package|category|media|byte|credential|cookie|token|password|secret|file)", re.I)
_FORBIDDEN_VALUE = re.compile(r"(?:^/|\\|\.pptx\b|php(?:sess)?id|cookie|token|password|base64|uesdb)", re.I)


def _validate_identity(page_id: str, image_sha256: str) -> None:
    if not _PAGE_ID.fullmatch(page_id):
        raise ObservationError("PAGE_ID_INVALID")
    if not _SHA256.fullmatch(image_sha256):
        raise ObservationError("IMAGE_HASH_INVALID")


def build_vision_request(page_id: str, image_sha256: str) -> dict[str, str]:
    """Return the only metadata allowed to leave the private uploader mapping."""

    _validate_identity(page_id, image_sha256)
    return {"schema_version": "1.0", "page_id": page_id, "image_sha256": image_sha256}


def _contains_forbidden(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_FORBIDDEN_KEY.search(str(key)) or _contains_forbidden(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden(item) for item in value)
    return isinstance(value, str) and bool(_FORBIDDEN_VALUE.search(value))


def _string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ObservationError(f"OBSERVATION_{field.upper()}_INVALID")
    return sorted(set(item.strip() for item in value), key=str.casefold)


def _description(value: Any, *, field: str) -> str:
    """Canonicalize a model's scalar or short-list prose without new facts."""

    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list) and value and all(isinstance(item, str) and item.strip() for item in value):
        return " | ".join(item.strip() for item in value)
    raise ObservationError(f"OBSERVATION_{field.upper()}_INVALID")


def normalize_observation(
    payload: Mapping[str, Any],
    *,
    page_id: str,
    image_sha256: str,
) -> dict[str, Any]:
    """Validate and canonically serialize a model observation without source egress."""

    _validate_identity(page_id, image_sha256)
    if set(payload) - _ALLOWED_TOP_LEVEL or _contains_forbidden(payload):
        raise ObservationError("EGRESS_FORBIDDEN")
    if payload.get("schema_version") != "1.0":
        raise ObservationError("SCHEMA_VERSION_INVALID")
    if payload.get("page_id") != page_id:
        raise ObservationError("PAGE_ID_MISMATCH")
    if payload.get("image_sha256") != image_sha256:
        raise ObservationError("IMAGE_HASH_MISMATCH")
    observation = payload.get("observation")
    if not isinstance(observation, Mapping) or set(observation) != _ALLOWED_OBSERVATION:
        raise ObservationError("OBSERVATION_SCHEMA_INVALID")
    composition = observation.get("composition")
    hierarchy = observation.get("hierarchy")
    density = observation.get("text_density")
    uncertainty = observation.get("uncertainty")
    composition = _description(composition, field="composition")
    hierarchy = _description(hierarchy, field="hierarchy")
    if not all(isinstance(item, str) and item.strip() for item in (density, uncertainty)):
        raise ObservationError("OBSERVATION_FIELD_INVALID")
    if uncertainty not in {"none", "low", "medium", "high"}:
        raise ObservationError("OBSERVATION_UNCERTAINTY_INVALID")
    result = {
        "schema_version": "1.0",
        "page_id": page_id,
        "image_sha256": image_sha256,
        "observation": {
            "visual_style": _string_list(observation.get("visual_style"), field="visual_style"),
            "composition": composition,
            "hierarchy": hierarchy,
            "semantic_tags": _string_list(observation.get("semantic_tags"), field="semantic_tags"),
            "suggested_roles": _string_list(observation.get("suggested_roles"), field="suggested_roles"),
            "text_density": density.strip(),
            "uncertainty": uncertainty,
        },
    }
    # The canonical JSON round trip makes non-JSON data impossible to retain.
    return json.loads(json.dumps(result, ensure_ascii=False, sort_keys=True))
