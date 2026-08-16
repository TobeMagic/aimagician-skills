from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.agnes_direct import (
    AGNES_IMAGE_ROUTE,
    AGNES_VISION_ROUTE,
    AgnesDirectClient,
    AgnesDirectError,
    AgnesReviewResult,
    GeneratedAsset,
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


def test_blind_review_is_uncached_session_bound_and_schema_strict() -> None:
    request_bodies: list[dict[str, object]] = []
    blind_payload = {
        "schema_version": "1.0",
        "reviewer_id": "R-AI-ART-DIRECTOR",
        "blind_id": "B-001-12345678",
        "scores": {
            "narrative_clarity": 4,
            "content_accuracy": 4,
            "visual_hierarchy": 5,
            "layout_fitness_variety": 4,
            "readability": 4,
            "chart_diagram_appropriateness": 4,
            "brand_consistency": 5,
            "editability": 4,
            "customer_delivery_readiness": 4,
        },
        "findings": [],
        "notes": "Visible presentation quality is customer-ready.",
        "verdict": "PASS",
    }

    def transport(request):
        request_bodies.append(request["json"])
        if "Capability challenge" in request["json"]["messages"][0]["content"][0][
            "text"
        ]:
            payload = _review_payload()
            match = re.search(
                r"probe_token exactly as ([0-9a-f]{16})",
                request["json"]["messages"][0]["content"][0]["text"],
            )
            assert match is not None
            payload["probe_token"] = match.group(1)
            return 200, {}, _chat_response(payload)
        return 200, {}, _chat_response(blind_payload)

    image = "data:image/png;base64," + base64.b64encode(b"png").decode()
    client = AgnesDirectClient(
        api_key="token",
        base_url="https://provider.invalid/v1",
        transport=transport,
    )
    probe = client.probe_data_uri(image)
    result = client.blind_review(
        image_urls=(image, image),
        prompt="Review the anonymous deck.",
        reviewer_id="R-AI-ART-DIRECTOR",
        blind_id="B-001-12345678",
    )

    assert result.session_id == probe.session_id
    assert result.payload == blind_payload
    assert result.request_sha256
    assert result.response_sha256
    assert len(request_bodies) == 2


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
        assert "response_format" not in request["json"]
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


def test_image_generation_freezes_authorized_provider_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image_bytes = b"\x89PNG\r\n\x1a\nfrozen"

    client = AgnesDirectClient(
        api_key="token",
        base_url="https://provider.invalid/v1",
        transport=lambda _request: (
            200,
            {},
            json.dumps(
                {
                    "data": [
                        {
                            "b64_json": None,
                            "url": (
                                "https://platform-outputs.agnes-ai.space/"
                                "images/t2i/example.png"
                            ),
                        }
                    ]
                }
            ).encode(),
        ),
    )
    monkeypatch.setattr(
        client,
        "_download_generated_image",
        lambda url: (
            image_bytes
            if url.startswith("https://platform-outputs.agnes-ai.space/")
            else b""
        ),
    )

    generated = client.generate_image(
        prompt="Abstract field, no text, no logo, no watermark."
    )

    assert generated.image_bytes == image_bytes
    assert generated.manifest["output_sha256"]


def test_clean_image_retries_and_freezes_visual_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AgnesDirectClient(
        api_key="token",
        base_url="https://provider.invalid/v1",
        transport=lambda _request: (500, {}, b""),
    )
    generated_prompts: list[str] = []
    review_prompts: list[str] = []

    def fake_generate_image(**kwargs):
        generated_prompts.append(kwargs["prompt"])
        payload = f"image-{len(generated_prompts)}".encode()
        return GeneratedAsset(
            route_id=AGNES_IMAGE_ROUTE.id,
            model=AGNES_IMAGE_ROUTE.model,
            image_bytes=payload,
            manifest={"output_sha256": "f" * 64},
        )

    verdicts = iter(("FAIL", "PASS"))

    def fake_review(**kwargs):
        review_prompts.append(kwargs["prompt"])
        verdict = next(verdicts)
        payload = _review_payload()
        payload["verdict"] = verdict
        if verdict == "FAIL":
            payload["findings"] = [
                {
                    "code": "PSEUDO_TEXT",
                    "severity": "blocker",
                    "slide_id": "asset",
                    "region": "center",
                    "evidence": "Visible pseudo-lettering.",
                    "repair_code": "REGENERATE_WITHOUT_TEXT",
                }
            ]
        return AgnesReviewResult(
            route_id=AGNES_VISION_ROUTE.id,
            model=AGNES_VISION_ROUTE.model,
            request_sha256="a" * 64,
            response_sha256=("b" if verdict == "FAIL" else "c") * 64,
            cache_hit=False,
            payload=payload,
        )

    monkeypatch.setattr(client, "generate_image", fake_generate_image)
    monkeypatch.setattr(client, "probe_data_uri", lambda _value: None)
    monkeypatch.setattr(client, "review", fake_review)

    generated = client.generate_clean_image(
        prompt="Editorial visual, no text, no logo, no watermark."
    )

    validation = generated.manifest["visual_validation"]
    assert generated.image_bytes == b"image-2"
    assert validation["verdict"] == "PASS"
    assert validation["attempt"] == 2
    assert validation["prior_failures"][0]["status"] == "rejected"
    assert "Retry instruction" in generated_prompts[1]
    assert "ORIGINAL VISUAL BRIEF" in review_prompts[0]
    assert "explicit inclusion and exclusion" in review_prompts[0]


def test_clean_image_exercises_generate_probe_and_review_transport() -> None:
    image_bytes = b"\x89PNG\r\n\x1a\nclean"
    request_urls: list[str] = []

    def transport(request):
        request_urls.append(request["url"])
        if request["url"].endswith("/images/generations"):
            return (
                200,
                {},
                json.dumps(
                    {
                        "data": [
                            {
                                "b64_json": base64.b64encode(
                                    image_bytes
                                ).decode()
                            }
                        ]
                    }
                ).encode(),
            )

        payload = _review_payload()
        prompt = request["json"]["messages"][0]["content"][0]["text"]
        match = re.search(r"probe_token exactly as ([0-9a-f]{16})", prompt)
        if match is not None:
            payload["probe_token"] = match.group(1)
        return 200, {}, _chat_response(payload)

    client = AgnesDirectClient(
        api_key="token",
        base_url="https://provider.invalid/v1",
        transport=transport,
    )

    generated = client.generate_clean_image(
        prompt=(
            "Editorial visual with layered paper geometry, "
            "no text, no logo, no watermark."
        ),
        max_attempts=1,
    )

    assert generated.image_bytes == image_bytes
    assert request_urls == [
        "https://provider.invalid/v1/images/generations",
        "https://provider.invalid/v1/chat/completions",
        "https://provider.invalid/v1/chat/completions",
    ]
    validation = generated.manifest["visual_validation"]
    assert validation["verdict"] == "PASS"
    assert validation["attempt"] == 1
    assert validation["route_id"] == AGNES_VISION_ROUTE.id
    assert validation["request_sha256"]
    assert validation["response_sha256"]


def test_clean_image_fails_closed_after_visual_rejections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AgnesDirectClient(
        api_key="token",
        base_url="https://provider.invalid/v1",
        transport=lambda _request: (500, {}, b""),
    )
    generated = GeneratedAsset(
        route_id=AGNES_IMAGE_ROUTE.id,
        model=AGNES_IMAGE_ROUTE.model,
        image_bytes=b"image",
        manifest={"output_sha256": "f" * 64},
    )
    payload = _review_payload()
    payload["verdict"] = "FAIL"
    review = AgnesReviewResult(
        route_id=AGNES_VISION_ROUTE.id,
        model=AGNES_VISION_ROUTE.model,
        request_sha256="a" * 64,
        response_sha256="b" * 64,
        cache_hit=False,
        payload=payload,
    )
    monkeypatch.setattr(client, "generate_image", lambda **_kwargs: generated)
    monkeypatch.setattr(client, "probe_data_uri", lambda _value: None)
    monkeypatch.setattr(client, "review", lambda **_kwargs: review)

    with pytest.raises(AgnesDirectError, match="failed semantic/no-text"):
        client.generate_clean_image(
            prompt="Editorial visual, no text, no logo, no watermark.",
            max_attempts=2,
        )


def test_blind_review_normalizes_verdict_to_frozen_score_rule() -> None:
    from window_pptx.agnes_direct import _strict_blind_review_payload

    payload = {
        "schema_version": "1.0",
        "reviewer_id": "R-AI-ART-DIRECTOR",
        "blind_id": "B-001-12345678",
        "scores": {
            "narrative_clarity": 4,
            "content_accuracy": 4,
            "visual_hierarchy": 4,
            "layout_fitness_variety": 4,
            "readability": 4,
            "chart_diagram_appropriateness": 4,
            "brand_consistency": 4,
            "editability": 4,
            "customer_delivery_readiness": 4,
        },
        "findings": [],
        "notes": "Scores are internally consistent.",
        "verdict": "PASS",
    }

    normalized = _strict_blind_review_payload(
        payload,
        reviewer_id="R-AI-ART-DIRECTOR",
        blind_id="B-001-12345678",
    )

    assert normalized["verdict"] == "FAIL"
