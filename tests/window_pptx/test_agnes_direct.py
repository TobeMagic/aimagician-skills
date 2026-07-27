from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.agnes_direct import (
    AGNES_IMAGE_ROUTE,
    AGNES_VISION_ROUTE,
    AgnesDirectClient,
    AgnesDirectError,
    ProviderRouteError,
    require_direct_route,
)


def _review_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "scope": "slide",
        "observations": [
            {
                "slide_id": "slide-01",
                "region": "upper-right",
                "evidence": "The title and portal motif are visibly separated.",
            }
        ],
        "findings": [],
        "scores": {
            "hierarchy_readability": 88,
            "composition_space": 86,
            "art_direction": 84,
            "business_evidence": 82,
            "deck_rhythm": 80,
            "asset_polish": 83,
        },
        "verdict": "PASS",
    }


def _chat_response(payload: dict[str, object]) -> bytes:
    return json.dumps(
        {"choices": [{"message": {"content": json.dumps(payload)}}]}
    ).encode()


def test_direct_route_identity_cannot_be_satisfied_by_opencode() -> None:
    assert AGNES_VISION_ROUTE.id == "agnes-direct/agnes-2.0-flash"
    assert AGNES_IMAGE_ROUTE.id == "agnes-direct/agnes-image-2.1-flash"
    with pytest.raises(ProviderRouteError, match="direct provider route"):
        require_direct_route("opencode/agnes-2.0-flash", capability="vision")
    with pytest.raises(ProviderRouteError, match="code-only"):
        require_direct_route(
            "opencode/deepseek-v4-flash-free", capability="vision"
        )


def test_public_url_review_is_schema_bound_and_cached(tmp_path: Path) -> None:
    requests: list[dict[str, object]] = []

    def transport(request):
        requests.append(request)
        return 200, {}, _chat_response(_review_payload())

    client = AgnesDirectClient(
        api_key="secret-token",
        base_url="https://provider.invalid/v1",
        transport=transport,
        cache_dir=tmp_path,
    )
    first = client.review(
        image_urls=("https://assets.invalid/slide-01.png",),
        prompt="Review visible hierarchy.",
        scope="slide",
    )
    second = client.review(
        image_urls=("https://assets.invalid/slide-01.png",),
        prompt="Review visible hierarchy.",
        scope="slide",
    )

    assert first.payload == second.payload
    assert first.request_sha256 == second.request_sha256
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert first.route_id == AGNES_VISION_ROUTE.id
    assert first.payload["verdict"] == "PASS"
    assert len(requests) == 1
    body = requests[0]["json"]
    assert body["model"] == "agnes-2.0-flash"
    image_parts = body["messages"][0]["content"][1:]
    assert image_parts[0]["image_url"]["url"].startswith("https://")
    cache_text = next(tmp_path.glob("*.json")).read_text(encoding="utf-8")
    assert "secret-token" not in cache_text


def test_data_uri_requires_session_challenge_probe() -> None:
    request_bodies: list[dict[str, object]] = []

    def transport(request):
        request_bodies.append(request["json"])
        payload = _review_payload()
        prompt = request["json"]["messages"][0]["content"][0]["text"]
        match = re.search(r"probe_token exactly as ([0-9a-f]{16})", prompt)
        if match is not None:
            payload["probe_token"] = match.group(1)
        return 200, {}, _chat_response(payload)

    challenge = "data:image/png;base64," + base64.b64encode(b"png").decode()
    client = AgnesDirectClient(
        api_key="token",
        base_url="https://provider.invalid/v1",
        transport=transport,
    )
    with pytest.raises(AgnesDirectError, match="challenge probe"):
        client.review(
            image_urls=(challenge,),
            prompt="Review.",
            scope="slide",
        )

    probe = client.probe_data_uri(challenge)
    assert probe.passed is True
    assert probe.session_id
    result = client.review(
        image_urls=(challenge,),
        prompt="Review.",
        scope="slide",
    )
    assert result.payload["verdict"] == "PASS"
    assert request_bodies[-1]["messages"][0]["content"][1]["image_url"][
        "url"
    ].startswith("data:image/png;base64,")


def test_malformed_json_retries_once_then_fails_closed() -> None:
    calls = 0

    def transport(_request):
        nonlocal calls
        calls += 1
        return 200, {}, b'{"choices":[{"message":{"content":"not-json"}}]}'

    client = AgnesDirectClient(
        api_key="token",
        base_url="https://provider.invalid/v1",
        transport=transport,
    )
    with pytest.raises(AgnesDirectError, match="strict JSON"):
        client.review(
            image_urls=("https://assets.invalid/slide.png",),
            prompt="Review.",
            scope="slide",
        )
    assert calls == 2


def test_review_normalizes_lossless_provider_shape_drift(tmp_path: Path) -> None:
    payload = _review_payload()
    payload["observations"] = [
        {
            "slide_id": 2,
            "region": None,
            "evidence": "The second slide visibly uses three cards.",
        }
    ]
    payload["findings"] = [
        {
            "code": "CARD_DENSITY",
            "severity": "medium",
            "slide_id": 2,
            "region": "",
            "evidence": "The third card contains substantially more copy.",
            "repair_code": None,
        }
    ]

    client = AgnesDirectClient(
        api_key="token",
        base_url="https://provider.invalid/v1",
        transport=lambda _request: (200, {}, _chat_response(payload)),
        cache_dir=tmp_path,
    )
    result = client.review(
        image_urls=("https://assets.invalid/slide.png",),
        prompt="Review.",
        scope="slide",
    )

    assert result.payload["observations"][0]["slide_id"] == "2"
    assert result.payload["observations"][0]["region"] == "whole-slide"
    assert result.payload["findings"][0]["severity"] == "important"
    assert result.payload["findings"][0]["repair_code"] == "MANUAL_ART_REVIEW"
    assert "OBSERVATION_SLIDE_ID_STRINGIFIED" in result.normalization_trace


def test_review_normalizes_common_finding_aliases(tmp_path: Path) -> None:
    payload = _review_payload()
    payload["findings"] = [
        {
            "code": "RHYTHM",
            "severity": "CRITICAL",
            "slide_id": None,
            "region": "whole-deck",
            "evidence": "Several pages repeat the same visual cadence.",
            "repair_code": ["VARY_LAYOUT", "ADD_PAUSE"],
            "suggestion": "Unsupported provider convenience field.",
        }
    ]
    client = AgnesDirectClient(
        api_key="token",
        base_url="https://provider.invalid/v1",
        transport=lambda _request: (200, {}, _chat_response(payload)),
        cache_dir=tmp_path,
    )

    result = client.review(
        image_urls=("https://assets.invalid/deck.png",),
        prompt="Review.",
        scope="slide",
    )

    finding = result.payload["findings"][0]
    assert finding["severity"] == "blocker"
    assert finding["slide_id"] == "deck"
    assert finding["repair_code"] == "VARY_LAYOUT + ADD_PAUSE"
    assert set(finding) == {
        "code",
        "severity",
        "slide_id",
        "region",
        "evidence",
        "repair_code",
    }


def test_rate_limit_error_redacts_key_and_authorization() -> None:
    def transport(_request):
        return (
            429,
            {"authorization": "Bearer secret-token"},
            b'{"error":"secret-token quota"}',
        )

    client = AgnesDirectClient(
        api_key="secret-token",
        base_url="https://provider.invalid/v1",
        transport=transport,
        max_retries=0,
    )
    with pytest.raises(AgnesDirectError) as captured:
        client.review(
            image_urls=("https://assets.invalid/slide.png",),
            prompt="Review.",
            scope="slide",
        )
    message = str(captured.value)
    assert "secret-token" not in message
    assert "authorization" not in message.casefold()
    assert "[REDACTED]" in message


def test_image_generation_returns_frozen_base64_manifest() -> None:
    image_bytes = b"\x89PNG\r\n\x1a\nfake"

    def transport(request):
        assert request["json"]["model"] == "agnes-image-2.1-flash"
        return (
            200,
            {},
            json.dumps(
                {"data": [{"b64_json": base64.b64encode(image_bytes).decode()}]}
            ).encode(),
        )

    client = AgnesDirectClient(
        api_key="token",
        base_url="https://provider.invalid/v1",
        transport=transport,
    )
    generated = client.generate_image(
        prompt=(
            "Abstract knowledge portal, no text, no logo, no watermark, "
            "warm ivory, navy, teal and gold."
        )
    )

    assert generated.route_id == AGNES_IMAGE_ROUTE.id
    assert generated.image_bytes == image_bytes
    assert generated.manifest["output_sha256"]
    assert generated.manifest["prompt_sha256"]
    assert "prompt" not in generated.manifest
