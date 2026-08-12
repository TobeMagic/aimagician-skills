from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.observations import (  # noqa: E402
    ObservationError,
    build_vision_request,
    normalize_observation,
)


PAGE_ID = "page_aaaaaaaaaaaaaaaaaaaaaaaa_001"
IMAGE_SHA = "b" * 64


def _payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "page_id": PAGE_ID,
        "image_sha256": IMAGE_SHA,
        "observation": {
            "visual_style": ["editorial", "dark"],
            "composition": "title-over-evidence",
            "hierarchy": "title-first",
            "semantic_tags": ["annual-report", "kpi"],
            "suggested_roles": ["cover", "kpi"],
            "text_density": "balanced",
            "uncertainty": "none",
        },
    }


def test_request_and_normalization_are_hash_bound_and_sanitized() -> None:
    request = build_vision_request(PAGE_ID, IMAGE_SHA)
    assert request == {"schema_version": "1.0", "page_id": PAGE_ID, "image_sha256": IMAGE_SHA}

    normalized = normalize_observation(_payload(), page_id=PAGE_ID, image_sha256=IMAGE_SHA)
    assert normalized["observation"]["semantic_tags"] == ["annual-report", "kpi"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_path", "/private/secret.pptx"),
        ("package_name", "003-封面模板"),
        ("media_bytes", "UEsDBAoAAAA"),
        ("credential", "PHPSESSID=secret"),
        ("unknown_field", "value"),
    ],
)
def test_egress_validator_rejects_every_prohibited_data_class(field: str, value: str) -> None:
    payload = _payload()
    payload[field] = value

    with pytest.raises(ObservationError, match="EGRESS"):
        normalize_observation(payload, page_id=PAGE_ID, image_sha256=IMAGE_SHA)


def test_observation_rejects_hash_or_identity_mismatch() -> None:
    payload = _payload()
    payload["image_sha256"] = "c" * 64

    with pytest.raises(ObservationError, match="IMAGE_HASH_MISMATCH"):
        normalize_observation(payload, page_id=PAGE_ID, image_sha256=IMAGE_SHA)


def test_observation_canonicalizes_short_description_lists() -> None:
    payload = _payload()
    payload["observation"]["composition"] = ["left narrative", "right evidence"]  # type: ignore[index]
    payload["observation"]["hierarchy"] = ["title", "data"]  # type: ignore[index]

    normalized = normalize_observation(payload, page_id=PAGE_ID, image_sha256=IMAGE_SHA)

    assert normalized["observation"]["composition"] == "left narrative | right evidence"
    assert normalized["observation"]["hierarchy"] == "title | data"
