"""Direct Agnes provider adapters with explicit capability boundaries.

The adapter intentionally does not reuse OpenCode model identities.  It
supports strict visual-review JSON, a session-bound Data-URI probe, redacted
HTTP failures, deterministic cache replay, and frozen image generation.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


class AgnesDirectError(RuntimeError):
    """A direct Agnes request failed without exposing credentials."""


class ProviderRouteError(ValueError):
    """A caller attempted to substitute a route with different authority."""


@dataclass(frozen=True)
class ProviderRoute:
    id: str
    provider: str
    model: str
    capability: str
    transport: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "provider": self.provider,
            "model": self.model,
            "capability": self.capability,
            "transport": self.transport,
        }


@dataclass(frozen=True)
class CapabilityProbe:
    route_id: str
    session_id: str
    transport: str
    passed: bool
    response_sha256: str


@dataclass(frozen=True)
class AgnesReviewResult:
    route_id: str
    model: str
    request_sha256: str
    response_sha256: str
    cache_hit: bool
    payload: Mapping[str, Any]
    normalization_trace: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "route_id": self.route_id,
            "model": self.model,
            "request_sha256": self.request_sha256,
            "response_sha256": self.response_sha256,
            "cache_hit": self.cache_hit,
            "payload": dict(self.payload),
            "normalization_trace": list(self.normalization_trace),
        }


@dataclass(frozen=True)
class AgnesBlindReviewResult:
    route_id: str
    model: str
    session_id: str
    request_sha256: str
    response_sha256: str
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "route_id": self.route_id,
            "model": self.model,
            "session_id": self.session_id,
            "request_sha256": self.request_sha256,
            "response_sha256": self.response_sha256,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class GeneratedAsset:
    route_id: str
    model: str
    image_bytes: bytes
    manifest: Mapping[str, Any]

    def to_dict(self, *, include_bytes: bool = False) -> dict[str, Any]:
        result = {
            "schema_version": "1.0",
            "route_id": self.route_id,
            "model": self.model,
            **dict(self.manifest),
        }
        if include_bytes:
            result["b64_json"] = base64.b64encode(self.image_bytes).decode("ascii")
        return result


AGNES_VISION_ROUTE = ProviderRoute(
    id="agnes-direct/agnes-2.0-flash",
    provider="agnes-direct",
    model="agnes-2.0-flash",
    capability="vision",
    transport="https-json",
)
AGNES_IMAGE_ROUTE = ProviderRoute(
    id="agnes-direct/agnes-image-2.1-flash",
    provider="agnes-direct",
    model="agnes-image-2.1-flash",
    capability="image-generation",
    transport="https-json",
)
DEESEEK_CODE_ROUTE = ProviderRoute(
    id="opencode/deepseek-v4-flash-free",
    provider="opencode",
    model="deepseek-v4-flash-free",
    capability="code-only",
    transport="opencode-session",
)

_DIRECT_ROUTES = {
    AGNES_VISION_ROUTE.id: AGNES_VISION_ROUTE,
    AGNES_IMAGE_ROUTE.id: AGNES_IMAGE_ROUTE,
}
_SCORE_AXES = {
    "hierarchy_readability",
    "composition_space",
    "art_direction",
    "business_evidence",
    "deck_rhythm",
    "asset_polish",
}
_BLIND_SCORE_AXES = {
    "narrative_clarity",
    "content_accuracy",
    "visual_hierarchy",
    "layout_fitness_variety",
    "readability",
    "chart_diagram_appropriateness",
    "brand_consistency",
    "editability",
    "customer_delivery_readiness",
}
_DATA_URI = re.compile(
    r"^data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=]+)$"
)
Transport = Callable[[dict[str, Any]], tuple[int, Mapping[str, str], bytes]]
_GENERATED_IMAGE_HOSTS = {"platform-outputs.agnes-ai.space"}
_MAX_GENERATED_IMAGE_BYTES = 24 * 1024 * 1024


def require_direct_route(route_id: str, *, capability: str) -> ProviderRoute:
    if route_id == DEESEEK_CODE_ROUTE.id:
        raise ProviderRouteError(
            f"{route_id} is code-only and cannot satisfy {capability}"
        )
    try:
        route = _DIRECT_ROUTES[route_id]
    except KeyError as exc:
        raise ProviderRouteError(
            f"{route_id} is not an authorized direct provider route"
        ) from exc
    if route.capability != capability:
        raise ProviderRouteError(
            f"{route_id} provides {route.capability}, not {capability}"
        )
    return route


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validated_data_uri(value: str) -> bytes:
    match = _DATA_URI.fullmatch(value)
    if match is None:
        raise AgnesDirectError("image Data URI is invalid or unsupported")
    try:
        decoded = base64.b64decode(match.group(2), validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise AgnesDirectError("image Data URI Base64 is invalid") from exc
    if not decoded:
        raise AgnesDirectError("image Data URI cannot be empty")
    return decoded


def _strict_review_payload(
    value: Any, *, scope: str
) -> tuple[dict[str, Any], tuple[str, ...]]:
    if not isinstance(value, dict):
        raise AgnesDirectError("Agnes review did not return strict JSON")
    required = {
        "schema_version",
        "scope",
        "observations",
        "findings",
        "scores",
        "verdict",
    }
    if set(value) - required - {"probe_token"} or required - set(value):
        raise AgnesDirectError("Agnes review did not return strict JSON")
    normalized = dict(value)
    trace: list[str] = []
    if normalized["schema_version"] != "1.0":
        raise AgnesDirectError("Agnes review did not return strict JSON")
    if normalized["scope"] != scope:
        raw_scope = str(normalized["scope"]).casefold()
        if scope not in raw_scope:
            raise AgnesDirectError("Agnes review did not return strict JSON")
        normalized["scope"] = scope
        trace.append(f"SCOPE_ALIAS_NORMALIZED:{value['scope']}->{scope}")
    if normalized["verdict"] not in {"PASS", "FAIL"}:
        raise AgnesDirectError("Agnes review did not return strict JSON")
    observations = normalized["observations"]
    findings = normalized["findings"]
    scores = normalized["scores"]
    if not isinstance(observations, list) or not observations:
        raise AgnesDirectError("Agnes review did not return strict JSON")
    normalized_observations: list[dict[str, str]] = []
    for item in observations:
        if isinstance(item, dict) and set(item) == {
            "slide_id",
            "region",
            "evidence",
        }:
            slide_id = item.get("slide_id")
            region = item.get("region")
            if isinstance(slide_id, (int, float)) and not isinstance(
                slide_id, bool
            ):
                item = {**item, "slide_id": str(slide_id)}
                trace.append("OBSERVATION_SLIDE_ID_STRINGIFIED")
            if region is None or (
                isinstance(region, str) and not region.strip()
            ):
                item = {**item, "region": "whole-slide"}
                trace.append("OBSERVATION_REGION_DEFAULTED")
        if (
            not isinstance(item, dict)
            or set(item) != {"slide_id", "region", "evidence"}
            or not all(
                isinstance(item[field], str) and item[field].strip()
                for field in ("slide_id", "region", "evidence")
            )
        ):
            raise AgnesDirectError("Agnes review did not return strict JSON")
        normalized_observations.append(item)
    normalized["observations"] = normalized_observations
    if not isinstance(findings, list):
        raise AgnesDirectError("Agnes review did not return strict JSON")
    severity_aliases = {
        "high": "blocker",
        "critical": "blocker",
        "medium": "important",
        "major": "important",
        "moderate": "important",
        "low": "minor",
        "warning": "minor",
    }
    finding_fields = {
        "code",
        "severity",
        "slide_id",
        "region",
        "evidence",
        "repair_code",
    }
    normalized_findings: list[dict[str, Any]] = []
    for item in findings:
        if isinstance(item, dict):
            if finding_fields < set(item):
                item = {field: item.get(field) for field in finding_fields}
                trace.append("FINDING_EXTRA_FIELDS_DROPPED")
            slide_id = item.get("slide_id")
            region = item.get("region")
            repair_code = item.get("repair_code")
            if isinstance(slide_id, (int, float)) and not isinstance(
                slide_id, bool
            ):
                item = {**item, "slide_id": str(slide_id)}
                trace.append("FINDING_SLIDE_ID_STRINGIFIED")
            elif slide_id is None or (
                isinstance(slide_id, str) and not slide_id.strip()
            ):
                item = {**item, "slide_id": "deck"}
                trace.append("FINDING_SLIDE_ID_DEFAULTED")
            if region is None or (
                isinstance(region, str) and not region.strip()
            ):
                item = {**item, "region": "whole-slide"}
                trace.append("FINDING_REGION_DEFAULTED")
            if repair_code is None or (
                isinstance(repair_code, str) and not repair_code.strip()
            ):
                item = {**item, "repair_code": "MANUAL_ART_REVIEW"}
                trace.append("FINDING_REPAIR_CODE_DEFAULTED")
            elif isinstance(repair_code, list) and all(
                isinstance(value, str) and value.strip()
                for value in repair_code
            ):
                item = {**item, "repair_code": " + ".join(repair_code)}
                trace.append("FINDING_REPAIR_CODE_JOINED")
            severity = item.get("severity")
            if isinstance(severity, str):
                lowered = severity.casefold()
                normalized_severity = severity_aliases.get(lowered, lowered)
                if normalized_severity != severity:
                    item = {**item, "severity": normalized_severity}
                    trace.append("SEVERITY_ALIAS_NORMALIZED")
        if (
            not isinstance(item, dict)
            or set(item)
            != {"code", "severity", "slide_id", "region", "evidence", "repair_code"}
            or item["severity"] not in {"minor", "important", "blocker"}
            or not all(
                isinstance(item[field], str) and item[field].strip()
                for field in (
                    "code",
                    "slide_id",
                    "region",
                    "evidence",
                    "repair_code",
                )
            )
        ):
            raise AgnesDirectError("Agnes review did not return strict JSON")
        normalized_findings.append(item)
    normalized["findings"] = normalized_findings
    if not isinstance(scores, dict) or set(scores) != _SCORE_AXES:
        raise AgnesDirectError("Agnes review did not return strict JSON")
    if any(
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not 0 <= score <= 100
        for score in scores.values()
    ):
        raise AgnesDirectError("Agnes review did not return strict JSON")
    if scores and max(scores.values()) <= 10:
        normalized["scores"] = {
            key: score * 10 for key, score in scores.items()
        }
        scores = normalized["scores"]
        trace.append("SCORE_SCALE_NORMALIZED:0-10->0-100")
    if "probe_token" in normalized and (
        not isinstance(normalized["probe_token"], str)
        or not normalized["probe_token"]
    ):
        raise AgnesDirectError("Agnes review did not return strict JSON")
    return normalized, tuple(trace)


def _strict_blind_review_payload(
    value: Any,
    *,
    reviewer_id: str,
    blind_id: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "reviewer_id",
        "blind_id",
        "scores",
        "findings",
        "notes",
        "verdict",
    }:
        raise AgnesDirectError("Agnes blind review did not return strict JSON")
    if (
        value["schema_version"] != "1.0"
        or value["reviewer_id"] != reviewer_id
        or value["blind_id"] != blind_id
        or value["verdict"] not in {"PASS", "FAIL"}
        or not isinstance(value["notes"], str)
        or not value["notes"].strip()
    ):
        raise AgnesDirectError("Agnes blind review did not return strict JSON")
    scores = value["scores"]
    if (
        not isinstance(scores, dict)
        or set(scores) != _BLIND_SCORE_AXES
        or any(
            isinstance(score, bool)
            or not isinstance(score, int)
            or not 1 <= score <= 5
            for score in scores.values()
        )
    ):
        raise AgnesDirectError("Agnes blind review did not return strict JSON")
    findings = value["findings"]
    if not isinstance(findings, list):
        raise AgnesDirectError("Agnes blind review did not return strict JSON")
    for finding in findings:
        if (
            not isinstance(finding, dict)
            or set(finding) != {"severity", "dimension", "evidence"}
            or finding["severity"] not in {"blocker", "important", "nitpick"}
            or finding["dimension"] not in _BLIND_SCORE_AXES
            or not isinstance(finding["evidence"], str)
            or not finding["evidence"].strip()
        ):
            raise AgnesDirectError("Agnes blind review did not return strict JSON")
    normalized = dict(value)
    expected_verdict = (
        "PASS"
        if sum(scores.values()) / len(scores) >= 4.2
        and min(scores.values()) >= 4
        else "FAIL"
    )
    normalized["verdict"] = expected_verdict
    return normalized


class AgnesDirectClient:
    """Small dependency-free direct client with injectable HTTP transport."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://apihub.agnes-ai.com/v1",
        transport: Transport | None = None,
        cache_dir: Path | str | None = None,
        timeout_seconds: float = 45.0,
        max_retries: int = 2,
    ) -> None:
        if not isinstance(api_key, str) or not api_key.strip():
            raise AgnesDirectError("AGNES_API_KEY is required")
        if not isinstance(base_url, str) or not base_url.startswith("https://"):
            raise AgnesDirectError("Agnes base URL must use HTTPS")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or timeout_seconds <= 0
        ):
            raise AgnesDirectError("Agnes timeout must be positive")
        if type(max_retries) is not int or not 0 <= max_retries <= 4:
            raise AgnesDirectError("Agnes max_retries must be 0..4")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._transport = transport or self._urllib_transport
        self._cache_dir = Path(cache_dir).resolve() if cache_dir else None
        self._timeout_seconds = float(timeout_seconds)
        self._max_retries = max_retries
        self._session_id = secrets.token_hex(12)
        self._data_uri_enabled = False

    def _urllib_transport(
        self, request: dict[str, Any]
    ) -> tuple[int, Mapping[str, str], bytes]:
        raw = _canonical_bytes(request["json"])
        http_request = urllib.request.Request(
            request["url"],
            data=raw,
            headers=request["headers"],
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                http_request, timeout=request["timeout"]
            ) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AgnesDirectError("Agnes request timed out or was unreachable") from exc

    def _redacted(self, value: object) -> str:
        text = str(value).replace(self._api_key, "[REDACTED]")
        text = re.sub(
            r"(?i)authorization\s*[:=]\s*[^\s,;}]+(?:\s+[^\s,;}]+)?",
            "[REDACTED]",
            text,
        )
        return text[:500]

    def _post_json(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        request = {
            "url": f"{self._base_url}/{path.lstrip('/')}",
            "headers": {
                "content-type": "application/json",
                "accept": "application/json",
                "authorization": f"Bearer {self._api_key}",
                "x-pptx-studio-session": self._session_id,
            },
            "json": dict(payload),
            "timeout": self._timeout_seconds,
        }
        status = 0
        body = b""
        for attempt in range(self._max_retries + 1):
            status, _headers, body = self._transport(request)
            if 200 <= status < 300:
                break
            if status not in {408, 425, 429, 500, 502, 503, 504}:
                break
            if attempt == self._max_retries:
                break
        if not 200 <= status < 300:
            detail = self._redacted(body.decode("utf-8", errors="replace"))
            raise AgnesDirectError(
                f"Agnes HTTP {status}: [REDACTED] {detail}"
            )
        try:
            value = json.loads(body)
        except json.JSONDecodeError as exc:
            raise AgnesDirectError("Agnes HTTP response was not JSON") from exc
        if not isinstance(value, dict):
            raise AgnesDirectError("Agnes HTTP response was not an object")
        return value

    def _cache_path(self, request_sha256: str) -> Path | None:
        if self._cache_dir is None:
            return None
        return self._cache_dir / f"{request_sha256}.json"

    def _load_review_cache(
        self, request_sha256: str
    ) -> AgnesReviewResult | None:
        path = self._cache_path(request_sha256)
        if path is None or not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            payload, trace = _strict_review_payload(
                raw["payload"], scope=raw["payload"]["scope"]
            )
            if raw["route_id"] != AGNES_VISION_ROUTE.id:
                return None
            return AgnesReviewResult(
                route_id=raw["route_id"],
                model=raw["model"],
                request_sha256=request_sha256,
                response_sha256=raw["response_sha256"],
                cache_hit=True,
                payload=payload,
                normalization_trace=tuple(
                    raw.get("normalization_trace", trace)
                ),
            )
        except (OSError, KeyError, TypeError, json.JSONDecodeError, AgnesDirectError):
            return None

    def _store_review_cache(self, result: AgnesReviewResult) -> None:
        path = self._cache_path(result.request_sha256)
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = result.to_dict()
        payload["cache_hit"] = False
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)

    def _review_request(
        self,
        *,
        image_urls: tuple[str, ...],
        prompt: str,
        scope: str,
        probe_token: str | None = None,
    ) -> AgnesReviewResult:
        if scope not in {"slide", "deck"}:
            raise AgnesDirectError("Agnes review scope must be slide or deck")
        if not 1 <= len(image_urls) <= 4:
            raise AgnesDirectError("Agnes review requires one to four images")
        if not isinstance(prompt, str) or not prompt.strip():
            raise AgnesDirectError("Agnes review prompt cannot be empty")
        for image_url in image_urls:
            if image_url.startswith("data:"):
                _validated_data_uri(image_url)
                if not self._data_uri_enabled and probe_token is None:
                    raise AgnesDirectError(
                        "Data URI requires a successful session challenge probe"
                    )
            elif not image_url.startswith("https://"):
                raise AgnesDirectError(
                    "Agnes review images require HTTPS or probed Data URI"
                )
        schema_instruction = (
            "Return only strict JSON with schema_version=1.0, scope, non-empty "
            f"scope exactly {scope}, observations[{{slide_id,region,evidence}}], "
            "findings[{code,severity,"
            "slide_id,region,evidence,repair_code}], scores for "
            "hierarchy_readability, composition_space, art_direction, "
            "business_evidence, deck_rhythm, asset_polish, each scored 0..100, "
            "and verdict PASS/FAIL."
        )
        if probe_token is not None:
            schema_instruction += (
                f" Also return probe_token exactly as {probe_token}."
            )
        content: list[dict[str, Any]] = [
            {"type": "text", "text": f"{prompt}\n\n{schema_instruction}"}
        ]
        content.extend(
            {"type": "image_url", "image_url": {"url": image_url}}
            for image_url in image_urls
        )
        request_payload = {
            "model": AGNES_VISION_ROUTE.model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        request_sha256 = _sha256(_canonical_bytes(request_payload))
        if probe_token is None:
            cached = self._load_review_cache(request_sha256)
            if cached is not None:
                return cached

        last_error: AgnesDirectError | None = None
        for repair_attempt in range(2):
            payload = dict(request_payload)
            if repair_attempt:
                payload["messages"] = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    content[0]["text"]
                                    + "\nYour prior response was invalid. Repair "
                                    "the JSON schema only; do not add prose."
                                ),
                            },
                            *content[1:],
                        ],
                    }
                ]
            response = self._post_json("chat/completions", payload)
            try:
                raw_content = response["choices"][0]["message"]["content"]
                decoded = json.loads(raw_content)
                strict, normalization_trace = _strict_review_payload(
                    decoded, scope=scope
                )
            except (
                KeyError,
                IndexError,
                TypeError,
                json.JSONDecodeError,
                AgnesDirectError,
            ) as exc:
                last_error = AgnesDirectError(
                    "Agnes review did not return strict JSON"
                )
                last_error.__cause__ = exc
                continue
            if probe_token is not None and strict.get("probe_token") != probe_token:
                last_error = AgnesDirectError(
                    "Agnes challenge probe token was not returned"
                )
                continue
            response_sha256 = _sha256(_canonical_bytes(strict))
            result = AgnesReviewResult(
                route_id=AGNES_VISION_ROUTE.id,
                model=AGNES_VISION_ROUTE.model,
                request_sha256=request_sha256,
                response_sha256=response_sha256,
                cache_hit=False,
                payload=strict,
                normalization_trace=normalization_trace,
            )
            if probe_token is None:
                self._store_review_cache(result)
            return result
        raise last_error or AgnesDirectError(
            "Agnes review did not return strict JSON"
        )

    def probe_data_uri(self, challenge_data_uri: str) -> CapabilityProbe:
        _validated_data_uri(challenge_data_uri)
        probe_token = _sha256(
            f"{self._session_id}|{challenge_data_uri}".encode("utf-8")
        )[:16]
        result = self._review_request(
            image_urls=(challenge_data_uri,),
            prompt=(
                "Capability challenge: inspect the attached image and return "
                "region-specific visible evidence."
            ),
            scope="slide",
            probe_token=probe_token,
        )
        self._data_uri_enabled = True
        return CapabilityProbe(
            route_id=AGNES_VISION_ROUTE.id,
            session_id=self._session_id,
            transport="data-uri",
            passed=True,
            response_sha256=result.response_sha256,
        )

    def review(
        self,
        *,
        image_urls: tuple[str, ...],
        prompt: str,
        scope: str,
    ) -> AgnesReviewResult:
        return self._review_request(
            image_urls=image_urls,
            prompt=prompt,
            scope=scope,
        )

    def blind_review(
        self,
        *,
        image_urls: tuple[str, ...],
        prompt: str,
        reviewer_id: str,
        blind_id: str,
    ) -> AgnesBlindReviewResult:
        """Run one uncached, session-bound independent blind scoring request."""

        if not 2 <= len(image_urls) <= 4:
            raise AgnesDirectError(
                "Agnes blind review requires two to four images"
            )
        if not isinstance(prompt, str) or not prompt.strip():
            raise AgnesDirectError("Agnes blind review prompt cannot be empty")
        if not isinstance(reviewer_id, str) or not reviewer_id.strip():
            raise AgnesDirectError("Agnes blind reviewer_id cannot be empty")
        if not isinstance(blind_id, str) or not blind_id.strip():
            raise AgnesDirectError("Agnes blind_id cannot be empty")
        for image_url in image_urls:
            if image_url.startswith("data:"):
                _validated_data_uri(image_url)
                if not self._data_uri_enabled:
                    raise AgnesDirectError(
                        "Data URI requires a successful session challenge probe"
                    )
            elif not image_url.startswith("https://"):
                raise AgnesDirectError(
                    "Agnes blind review images require HTTPS or probed Data URI"
                )
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    f"{prompt}\n\nReturn only strict JSON. Exact root keys: "
                    "schema_version, reviewer_id, blind_id, scores, findings, "
                    "notes, verdict. scores must contain exactly "
                    f"{', '.join(sorted(_BLIND_SCORE_AXES))}, each integer 1..5. "
                    "findings items contain exactly severity, dimension, evidence."
                ),
            }
        ]
        content.extend(
            {"type": "image_url", "image_url": {"url": image_url}}
            for image_url in image_urls
        )
        request_payload = {
            "model": AGNES_VISION_ROUTE.model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        request_sha256 = _sha256(_canonical_bytes(request_payload))
        last_error: AgnesDirectError | None = None
        for attempt in range(2):
            payload = request_payload
            if attempt:
                payload = {
                    **request_payload,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        content[0]["text"]
                                        + "\nYour prior response was invalid. "
                                        "Repair the JSON schema only; add no prose."
                                    ),
                                },
                                *content[1:],
                            ],
                        }
                    ],
                }
            response = self._post_json("chat/completions", payload)
            try:
                raw_content = response["choices"][0]["message"]["content"]
                decoded = json.loads(raw_content)
                strict = _strict_blind_review_payload(
                    decoded,
                    reviewer_id=reviewer_id,
                    blind_id=blind_id,
                )
            except (
                KeyError,
                IndexError,
                TypeError,
                json.JSONDecodeError,
                AgnesDirectError,
            ) as exc:
                last_error = AgnesDirectError(
                    "Agnes blind review did not return strict JSON"
                )
                last_error.__cause__ = exc
                continue
            return AgnesBlindReviewResult(
                route_id=AGNES_VISION_ROUTE.id,
                model=AGNES_VISION_ROUTE.model,
                session_id=self._session_id,
                request_sha256=request_sha256,
                response_sha256=_sha256(_canonical_bytes(strict)),
                payload=strict,
            )
        raise last_error or AgnesDirectError(
            "Agnes blind review did not return strict JSON"
        )

    def generate_image(
        self,
        *,
        prompt: str,
        reference_data_uri: str | None = None,
        size: str = "1536x1024",
    ) -> GeneratedAsset:
        if not isinstance(prompt, str) or not prompt.strip():
            raise AgnesDirectError("Agnes image prompt cannot be empty")
        normalized = prompt.casefold()
        required_guardrails = ("no text", "no logo", "no watermark")
        if any(item not in normalized for item in required_guardrails):
            raise AgnesDirectError(
                "generated visual prompts must prohibit text, logos, and watermarks"
            )
        payload: dict[str, Any] = {
            "model": AGNES_IMAGE_ROUTE.model,
            "prompt": prompt,
            "size": size,
        }
        input_hashes: list[str] = []
        if reference_data_uri is not None:
            reference_bytes = _validated_data_uri(reference_data_uri)
            payload["image"] = reference_data_uri
            input_hashes.append(_sha256(reference_bytes))
        response = self._post_json("images/generations", payload)
        try:
            item = response["data"][0]
            encoded = item.get("b64_json")
            image_url = item.get("url")
            if isinstance(encoded, str) and encoded:
                image_bytes = base64.b64decode(encoded, validate=True)
            elif isinstance(image_url, str) and image_url:
                image_bytes = self._download_generated_image(image_url)
            else:
                raise TypeError
        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            base64.binascii.Error,
        ) as exc:
            raise AgnesDirectError(
                "Agnes image response did not contain valid Base64"
            ) from exc
        if not image_bytes:
            raise AgnesDirectError("Agnes image response was empty")
        return GeneratedAsset(
            route_id=AGNES_IMAGE_ROUTE.id,
            model=AGNES_IMAGE_ROUTE.model,
            image_bytes=image_bytes,
            manifest={
                "prompt_sha256": _sha256(prompt.encode("utf-8")),
                "input_sha256": input_hashes,
                "output_sha256": _sha256(image_bytes),
                "size": size,
                "content_policy": {
                    "facts": "forbidden",
                    "text": "forbidden",
                    "logos": "forbidden",
                    "watermarks": "forbidden",
                },
            },
        )

    def generate_clean_image(
        self,
        *,
        prompt: str,
        reference_data_uri: str | None = None,
        size: str = "1536x1024",
        max_attempts: int = 3,
    ) -> GeneratedAsset:
        """Generate a raster and fail closed unless Agnes sees a faithful asset.

        Prompt guardrails are necessary but insufficient: image models can
        still synthesize pseudo-lettering or ignore subject exclusions.  This
        method freezes a direct vision review into the provider manifest and
        retries with a stricter instruction before the asset can enter a
        presentation.
        """

        if type(max_attempts) is not int or not 1 <= max_attempts <= 3:
            raise AgnesDirectError("clean image max_attempts must be 1..3")
        failures: list[dict[str, Any]] = []
        for attempt in range(1, max_attempts + 1):
            attempt_prompt = prompt
            if attempt > 1:
                attempt_prompt += (
                    " Retry instruction: remove every visible letter, number, "
                    "word-like glyph, signature, label, brand mark, interface "
                    "caption, and watermark. Obey every subject inclusion and "
                    "exclusion in the original brief literally. Use only "
                    "non-text visual elements permitted by that brief."
                )
            generated = self.generate_image(
                prompt=attempt_prompt,
                reference_data_uri=reference_data_uri,
                size=size,
            )
            data_uri = (
                "data:image/png;base64,"
                + base64.b64encode(generated.image_bytes).decode("ascii")
            )
            if not self._data_uri_enabled:
                self.probe_data_uri(data_uri)
            try:
                review = self.review(
                    image_urls=(data_uri,),
                    scope="slide",
                    prompt=(
                        "This is a generated presentation background asset. "
                        "Inspect the pixels against the complete original visual "
                        "brief below. Verdict PASS is allowed only when (1) there "
                        "are zero visible letters, words, numbers, word-like "
                        "pseudo-glyphs, logos, signatures, UI labels, or "
                        "watermarks anywhere, and (2) the depicted subject obeys "
                        "every explicit inclusion and exclusion in the brief. "
                        "Any forbidden object, off-brief subject, or ambiguous "
                        "glyph-like mark requires FAIL. Do not judge whether later "
                        "editable PowerPoint text would be attractive.\n\n"
                        f"ORIGINAL VISUAL BRIEF:\n{prompt}"
                    ),
                )
            except AgnesDirectError as exc:
                failures.append(
                    {
                        "attempt": attempt,
                        "status": "review-error",
                        "error": type(exc).__name__,
                    }
                )
                continue
            verdict = review.payload["verdict"]
            if verdict == "PASS":
                return GeneratedAsset(
                    route_id=generated.route_id,
                    model=generated.model,
                    image_bytes=generated.image_bytes,
                    manifest={
                        **dict(generated.manifest),
                        "visual_validation": {
                            "route_id": review.route_id,
                            "model": review.model,
                            "request_sha256": review.request_sha256,
                            "response_sha256": review.response_sha256,
                            "verdict": verdict,
                            "criteria": (
                                "semantic-brief-fidelity-and-no-visible-"
                                "text-logo-watermark"
                            ),
                            "attempt": attempt,
                            "prior_failures": failures,
                            "review_payload": dict(review.payload),
                        },
                    },
                )
            failures.append(
                {
                    "attempt": attempt,
                    "status": "rejected",
                    "response_sha256": review.response_sha256,
                    "findings": list(review.payload["findings"]),
                }
            )
        raise AgnesDirectError(
            "generated image failed semantic/no-text visual validation"
        )

    def _download_generated_image(self, image_url: str) -> bytes:
        parsed = urllib.parse.urlparse(image_url)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in _GENERATED_IMAGE_HOSTS
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise AgnesDirectError(
                "Agnes generated-image URL is not on an authorized HTTPS host"
            )
        request = urllib.request.Request(
            image_url,
            headers={"accept": "image/png,image/jpeg"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self._timeout_seconds
            ) as response:
                final = urllib.parse.urlparse(response.geturl())
                if (
                    final.scheme != "https"
                    or final.hostname not in _GENERATED_IMAGE_HOSTS
                ):
                    raise AgnesDirectError(
                        "Agnes generated-image redirect left the authorized host"
                    )
                payload = response.read(_MAX_GENERATED_IMAGE_BYTES + 1)
        except AgnesDirectError:
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise AgnesDirectError(
                "Agnes generated image could not be downloaded"
            ) from exc
        if not payload or len(payload) > _MAX_GENERATED_IMAGE_BYTES:
            raise AgnesDirectError(
                "Agnes generated image is empty or exceeds the size limit"
            )
        if not (
            payload.startswith(b"\x89PNG\r\n\x1a\n")
            or payload.startswith(b"\xff\xd8")
        ):
            raise AgnesDirectError(
                "Agnes generated image is not a supported PNG or JPEG"
            )
        return payload


__all__ = [
    "AGNES_IMAGE_ROUTE",
    "AGNES_VISION_ROUTE",
    "DEESEEK_CODE_ROUTE",
    "AgnesDirectClient",
    "AgnesDirectError",
    "AgnesBlindReviewResult",
    "AgnesReviewResult",
    "CapabilityProbe",
    "GeneratedAsset",
    "ProviderRoute",
    "ProviderRouteError",
    "require_direct_route",
]
