"""Authenticated, resumable, diversity-first Gaojie template acquisition."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .acquisition import AcquisitionError, validate_private_credential_file
from .gaojie_diversity import (
    PreviewError,
    PreviewFingerprint,
    fingerprint_preview,
    median_nearest_neighbor,
    select_diverse,
)


_CATEGORY_RE = re.compile(r"(?:^|[?&])category_id=(\d+)", re.I)
_PRODUCT_DETAIL_PATH = "/products_show.aspx"
_TEMPLATE_CATEGORY_PATH = "/products.aspx"
_PAGE_KEYS = {"page", "p", "pageindex"}
_ALLOWED_SUFFIXES = {".pptx", ".ppt", ".potx", ".pot", ".zip"}
_OOXML_SUFFIXES = {".pptx", ".potx"}
_LEGACY_SUFFIXES = {".ppt", ".pot"}
_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
_OLE_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
_PREVIEW_RULE_VERSION = "gaojie-preview.v2"
_PREVIEW_RECOVERY_VERSION = "gaojie-preview-recovery.v1"
_PREVIEW_FETCH_ATTEMPTS = 3


@dataclass(frozen=True)
class GaojieConfig:
    origin: str
    private_root: Path
    credential_file: Path
    headless: bool = True
    maximum_items: int | None = None
    minimum_free_gb: float = 40.0
    allow_insecure_http: bool = False
    minimum_categories: int = 32
    maximum_file_bytes: int = 2 * 1024 * 1024 * 1024
    maximum_preview_bytes: int = 20 * 1024 * 1024
    items_per_category: int = 12
    minimum_diverse_items: int = 8
    near_duplicate_distance: float = 0.08
    preview_workers: int = 16
    asset_hosts: tuple[str, ...] = ("wstx.web.vleader.net.cn",)


def _extract_cookie_value(value: str) -> str:
    """Extract Cookie data from raw text or copied browser request headers."""

    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if not lines:
        raise AcquisitionError("credential file does not contain cookies")

    candidates: list[str] = []
    for index, line in enumerate(lines):
        header = re.fullmatch(r"cookie\s*:\s*(.+)", line, re.I)
        if header:
            candidates.append(header.group(1).strip())
        if line.casefold() == "cookie" and index + 1 < len(lines):
            candidates.append(lines[index + 1].strip())

    if candidates:
        unique = list(dict.fromkeys(candidates))
        if len(unique) != 1:
            raise AcquisitionError("credential file contains ambiguous Cookie headers")
        return unique[0]
    if len(lines) == 1:
        return lines[0]
    raise AcquisitionError("credential file does not contain a recognized Cookie header")


def parse_cookie_header(value: str) -> list[tuple[str, str]]:
    """Parse raw or copied request Cookie data without logging values."""

    cookies: list[tuple[str, str]] = []
    for part in _extract_cookie_value(value).split(";"):
        name, separator, cookie_value = part.strip().partition("=")
        if not separator or not name or any(ch in name for ch in "\r\n\t ,"):
            continue
        if name.casefold() in {"path", "domain", "expires", "max-age", "samesite"}:
            continue
        cookies.append((name, cookie_value))
    if not cookies:
        raise AcquisitionError("credential file does not contain cookies")
    return cookies


def _validate_config(config: GaojieConfig) -> tuple[str, str, int]:
    validate_private_credential_file(config.credential_file, config.private_root)
    parsed = urlsplit(config.origin)
    if not parsed.hostname or parsed.username or parsed.password:
        raise AcquisitionError("origin must be a credential-free absolute URL")
    if parsed.scheme == "http" and not config.allow_insecure_http:
        raise AcquisitionError("HTTP origin requires an explicit source exception")
    if parsed.scheme not in {"http", "https"}:
        raise AcquisitionError("origin scheme is unsupported")
    if config.maximum_items is not None and config.maximum_items < 1:
        raise AcquisitionError("maximum_items must be positive")
    if config.items_per_category < 1 or config.minimum_diverse_items < 1:
        raise AcquisitionError("diversity item limits must be positive")
    if config.minimum_diverse_items > config.items_per_category:
        raise AcquisitionError("minimum diverse items cannot exceed category target")
    if not 0 <= config.near_duplicate_distance <= 1:
        raise AcquisitionError("near duplicate distance must be between zero and one")
    if not 1 <= config.preview_workers <= 16:
        raise AcquisitionError("preview_workers must be between one and sixteen")
    port = parsed.port or (80 if parsed.scheme == "http" else 443)
    return parsed.scheme, parsed.hostname.casefold(), port


def _safe_name(value: str, fallback: str) -> str:
    value = unquote(value).strip().replace("\\", "_").replace("/", "_")
    value = re.sub(r"[\x00-\x1f<>:\"|?*]+", "_", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value[:120] or fallback


def _same_origin(url: str, scheme: str, host: str, port: int) -> bool:
    parsed = urlsplit(url)
    candidate_port = parsed.port or (80 if parsed.scheme == "http" else 443)
    return (
        parsed.scheme == scheme
        and parsed.hostname is not None
        and parsed.hostname.casefold() == host
        and candidate_port == port
    )


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".part", dir=path.parent
    )
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _free_gb(path: Path) -> float:
    path.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(path).free / (1024**3)


def _links(page: Any) -> list[dict[str, str]]:
    return page.locator("a[href]").evaluate_all(
        """els => els.map(a => ({
            href: a.href,
            text: (a.innerText || a.title || '').trim()
        }))"""
    )


class _HrefParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.hrefs: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.casefold() != "a":
            return
        values = {key.casefold(): value for key, value in attrs}
        href = values.get("href")
        if href:
            self.hrefs.append(urljoin(self.base_url, href))


def _html_hrefs(payload: str, base_url: str) -> list[str]:
    parser = _HrefParser(base_url)
    parser.feed(payload)
    parser.close()
    return parser.hrefs


def _product_cards(page: Any) -> list[dict[str, str]]:
    return page.locator("a[href]").evaluate_all(
        """els => els.map(a => {
            const img = a.querySelector('img');
            return {
                href: a.href,
                text: (a.innerText || a.title || '').trim(),
                preview: img
                    ? (img.getAttribute('data-src')
                        || img.getAttribute('data-original')
                        || img.currentSrc
                        || img.src
                        || '')
                    : ''
            };
        }).filter(x => x.preview)"""
    )


def _category_key(url: str) -> tuple[str, str] | None:
    parsed = urlsplit(url)
    if parsed.path.casefold() != _TEMPLATE_CATEGORY_PATH:
        return None
    query = parse_qs(parsed.query)
    values = query.get("category_id") or query.get("CATEGORY_ID")
    if not values or not values[0].isdigit() or int(values[0]) <= 0:
        return None
    return parsed.path.casefold(), values[0]


def _category_state_key(path: str, category_id: str) -> str:
    return f"{path.casefold()}:{int(category_id)}"


def _is_category_page_for(
    url: str,
    *,
    category_path: str,
    category_id: str,
) -> bool:
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    values = query.get("category_id") or query.get("CATEGORY_ID")
    return (
        parsed.path.casefold() == category_path.casefold()
        and bool(values)
        and values[0] == category_id
    )


def _is_product_detail(url: str) -> bool:
    parsed = urlsplit(url)
    query = {key.casefold() for key in parse_qs(parsed.query)}
    return (
        parsed.path.casefold() == _PRODUCT_DETAIL_PATH
        and bool(query.intersection({"id", "product_id", "productid"}))
    )


def _direct_file_suffix(url: str) -> str | None:
    suffix = Path(urlsplit(url).path).suffix.casefold()
    return suffix if suffix in _ALLOWED_SUFFIXES else None


def _url_digest(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _allowed_asset_url(
    url: str,
    *,
    scheme: str,
    host: str,
    port: int,
    asset_hosts: tuple[str, ...],
) -> bool:
    if _same_origin(url, scheme, host, port):
        return True
    parsed = urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname is not None
        and parsed.hostname.casefold()
        in {value.casefold() for value in asset_hosts}
        and (parsed.port or 443) == 443
        and not parsed.username
        and not parsed.password
    )


def _normalize_asset_url(url: str, asset_hosts: tuple[str, ...]) -> str:
    """Upgrade legacy HTTP links only on the exact pinned CDN allowlist."""

    parsed = urlsplit(url)
    allowed = {value.casefold() for value in asset_hosts}
    if (
        parsed.scheme == "http"
        and parsed.hostname is not None
        and parsed.hostname.casefold() in allowed
        and (parsed.port or 80) == 80
        and not parsed.username
        and not parsed.password
    ):
        return urlunsplit(
            (
                "https",
                parsed.hostname,
                parsed.path,
                parsed.query,
                "",
            )
        )
    return url


def _item_id(detail_url: str) -> str:
    return _url_digest(detail_url)[:24]


def _finding(code: str, url: str | None = None) -> dict[str, str]:
    result = {"code": code}
    if url:
        result["path"] = _url_digest(url)
    return result


def _filename(headers: dict[str, str], url: str, digest: str) -> str:
    disposition = headers.get("content-disposition", "")
    match = re.search(r"filename\*?=(?:UTF-8''|[\"']?)([^\"';]+)", disposition, re.I)
    candidate = match.group(1) if match else Path(urlsplit(url).path).name
    name = _safe_name(candidate, f"{digest[:16]}.pptx")
    suffix = Path(name).suffix.casefold()
    if suffix not in _ALLOWED_SUFFIXES:
        name = f"{name}.pptx"
    return name


def _preview_suffix(content_type: str) -> str:
    return {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(content_type.split(";", 1)[0].casefold(), ".img")


def _valid_powerpoint(payload: bytes, suffix: str) -> bool:
    if suffix in _LEGACY_SUFFIXES:
        return payload.startswith(_OLE_SIGNATURE)
    if suffix not in _OOXML_SUFFIXES and suffix != ".zip":
        return False
    if not payload.startswith(b"PK"):
        return False
    try:
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            names = set(archive.namelist())
    except (zipfile.BadZipFile, OSError):
        return False
    if suffix == ".zip":
        return bool(names)
    return "[Content_Types].xml" in names and "ppt/presentation.xml" in names


def _fingerprint_from_state(value: dict[str, Any]) -> PreviewFingerprint:
    return PreviewFingerprint(
        sha256=str(value["sha256"]),
        width=int(value["width"]),
        height=int(value["height"]),
        aspect_ratio=float(value["aspect_ratio"]),
        dhash=str(value["dhash"]),
        color_histogram=tuple(float(item) for item in value["color_histogram"]),
        entropy=float(value["entropy"]),
        edge_density=float(value["edge_density"]),
        quality=float(value["quality"]),
    )


def _fresh_state(origin: str) -> dict[str, Any]:
    return {
        "schema_version": "gaojie-sync.v2",
        "status": "PARTIAL",
        "origin": origin.rstrip("/"),
        "preview_rule_version": _PREVIEW_RULE_VERSION,
        "categories": {},
        "observed_routes": {},
        "visited_pages": [],
        "visited_details": [],
        "inventory": {},
        "selections": {},
        "artifacts": [],
        "findings": [],
    }


def _reconcile_artifacts(root: Path, state: dict[str, Any]) -> None:
    valid: list[dict[str, Any]] = []
    for item in state.get("artifacts", []):
        try:
            candidate = (root / item["path"]).resolve()
            candidate.relative_to(root.resolve())
            expected_hash = item["sha256"]
            expected_size = item["bytes"]
        except (KeyError, OSError, TypeError, ValueError):
            continue
        if not candidate.is_file():
            continue
        stat = candidate.stat()
        if stat.st_size != expected_size:
            continue
        if item.get("verified_mtime_ns") == stat.st_mtime_ns:
            valid.append(item)
            continue
        if hashlib.sha256(candidate.read_bytes()).hexdigest() == expected_hash:
            item["verified_mtime_ns"] = stat.st_mtime_ns
            valid.append(item)
    if len(valid) != len(state.get("artifacts", [])):
        state["findings"].append({"code": "RESUME_ARTIFACT_RECONCILED"})
        state["visited_details"] = []
    state["artifacts"] = valid
    completed_item_ids = {
        item_id
        for artifact in valid
        for item_id in artifact.get("item_ids", [])
    }
    for item_id in completed_item_ids:
        item = state.get("inventory", {}).get(item_id)
        if isinstance(item, dict):
            item["download_status"] = "PASS"
            item.pop("download_failure_count", None)
    state["artifact_count"] = len(valid)


def _load_state(root: Path, origin: str) -> tuple[Path, dict[str, Any]]:
    state_path = root / "state" / "gaojie-sync.json"
    state = _fresh_state(origin)
    if state_path.is_file():
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state["findings"].append({"code": "RESUME_STATE_IGNORED"})
        else:
            if (
                previous.get("schema_version") == state["schema_version"]
                and previous.get("origin") == state["origin"]
            ):
                previous_preview_rule = previous.get("preview_rule_version")
                state.update(previous)
                if previous_preview_rule != _PREVIEW_RULE_VERSION:
                    state["preview_rule_version"] = _PREVIEW_RULE_VERSION
                    state["visited_pages"] = []
                    state["inventory"] = {}
                    state["selections"] = {}
                    state["findings"].append({"code": "PREVIEW_RULE_REBUILT"})
            elif previous.get("schema_version") == "gaojie-sync.v1":
                state["findings"].append({"code": "RESUME_STATE_V1_REBUILT"})
            else:
                state["findings"].append({"code": "RESUME_STATE_IGNORED"})
    _reconcile_artifacts(root, state)
    return state_path, state


def _download_preview(
    context: Any,
    *,
    preview_url: str,
    root: Path,
    scheme: str,
    host: str,
    port: int,
    maximum_bytes: int,
    asset_hosts: tuple[str, ...],
    referer: str,
) -> tuple[str, PreviewFingerprint]:
    if not _allowed_asset_url(
        preview_url,
        scheme=scheme,
        host=host,
        port=port,
        asset_hosts=asset_hosts,
    ):
        raise PreviewError("preview origin is not allowed")
    if _same_origin(preview_url, scheme, host, port):
        response = context.request.get(preview_url, headers={"Referer": referer})
        if not response.ok:
            raise PreviewError("preview request failed")
        response_url = response.url
        headers = response.headers
        payload = response.body()
    else:
        request = Request(
            preview_url,
            headers={
                "Referer": referer,
                "User-Agent": "Mozilla/5.0 Window-PPTX/1.0",
            },
        )
        try:
            with urlopen(request, timeout=30) as remote:
                response_url = remote.geturl()
                headers = {key.casefold(): value for key, value in remote.headers.items()}
                declared = headers.get("content-length")
                if declared and declared.isdigit() and int(declared) > maximum_bytes:
                    raise PreviewError("preview exceeds byte limit")
                payload = remote.read(maximum_bytes + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise PreviewError("preview request failed") from exc
    if not _allowed_asset_url(
        response_url,
        scheme=scheme,
        host=host,
        port=port,
        asset_hosts=asset_hosts,
    ):
        raise PreviewError("preview request failed")
    content_type = headers.get("content-type", "").split(";", 1)[0].casefold()
    if content_type not in _IMAGE_CONTENT_TYPES:
        raise PreviewError("preview response is not an image")
    declared = headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > maximum_bytes:
        raise PreviewError("preview exceeds byte limit")
    if len(payload) > maximum_bytes:
        raise PreviewError("preview exceeds byte limit")
    fingerprint = fingerprint_preview(payload)
    relative = (
        Path("previews")
        / "gaojie"
        / fingerprint.sha256[:2]
        / f"{fingerprint.sha256}{_preview_suffix(content_type)}"
    )
    target = root / relative
    if not target.is_file():
        _atomic_bytes(target, payload)
    return relative.as_posix(), fingerprint


def _download_preview_with_retry(
    context: Any,
    **kwargs: Any,
) -> tuple[str, PreviewFingerprint]:
    """Retry transient CDN failures without weakening validation."""

    last_error: PreviewError | None = None
    for attempt in range(_PREVIEW_FETCH_ATTEMPTS):
        try:
            return _download_preview(context, **kwargs)
        except PreviewError as exc:
            last_error = exc
            if attempt + 1 < _PREVIEW_FETCH_ATTEMPTS:
                time.sleep(0.2 * (attempt + 1))
    assert last_error is not None
    raise last_error


def _inventory_category(
    page: Any,
    context: Any,
    *,
    category_key: str,
    category: dict[str, str],
    state: dict[str, Any],
    state_path: Path,
    root: Path,
    scheme: str,
    host: str,
    port: int,
    config: GaojieConfig,
    smoke_preview_target: int | None,
) -> None:
    pending = [category["url"]]
    seen = set(state.get("visited_pages", []))
    valid_preview_count = 0
    while pending:
        category_url = pending.pop(0)
        if category_url in seen:
            continue
        response = page.goto(category_url, wait_until="domcontentloaded")
        if "login.aspx" in page.url.casefold():
            raise AcquisitionError("authenticated session expired")
        if response is None:
            state["findings"].append(_finding("CATEGORY_HTTP_ERROR", category_url))
            continue

        for link in _links(page):
            href = link["href"].split("#", 1)[0]
            if not _same_origin(href, scheme, host, port):
                continue
            query = parse_qs(urlsplit(href).query)
            if (
                _is_category_page_for(
                    href,
                    category_path=category["route_path"],
                    category_id=category["category_id"],
                )
                and any(key.casefold() in _PAGE_KEYS for key in query)
                and href not in seen
            ):
                pending.append(href)

        page_complete = True
        preview_tasks: list[tuple[str, str]] = []
        for card in _product_cards(page):
            detail_url = card["href"].split("#", 1)[0]
            preview_url = _normalize_asset_url(
                urljoin(page.url, card["preview"]),
                config.asset_hosts,
            )
            if (
                not _same_origin(detail_url, scheme, host, port)
                or not _is_product_detail(detail_url)
            ):
                continue
            item_id = _item_id(detail_url)
            item = state["inventory"].setdefault(
                item_id,
                {
                    "item_id": item_id,
                    "title": _safe_name(card["text"], "template"),
                    "detail_url": detail_url,
                    "detail_url_sha256": _url_digest(detail_url),
                    "category_keys": [],
                    "preview_url_sha256": _url_digest(preview_url),
                },
            )
            if category_key not in item["category_keys"]:
                item["category_keys"].append(category_key)
                item["category_keys"].sort()
            existing_path = item.get("preview_path")
            existing_fingerprint = item.get("preview_fingerprint")
            if existing_path and existing_fingerprint:
                candidate = root / existing_path
                if candidate.is_file():
                    valid_preview_count += 1
                    continue
            preview_tasks.append((item_id, preview_url))
            if smoke_preview_target is not None:
                try:
                    relative, fingerprint = _download_preview_with_retry(
                        context,
                        preview_url=preview_url,
                        root=root,
                        scheme=scheme,
                        host=host,
                        port=port,
                        maximum_bytes=config.maximum_preview_bytes,
                        asset_hosts=config.asset_hosts,
                        referer=page.url,
                    )
                except PreviewError:
                    item["preview_status"] = "FAIL"
                    if sum(
                        finding.get("code") == "PREVIEW_INVALID"
                        for finding in state["findings"]
                    ) < 25:
                        state["findings"].append(
                            _finding("PREVIEW_INVALID", preview_url)
                        )
                else:
                    item["preview_status"] = "PASS"
                    item["preview_path"] = relative
                    item["preview_fingerprint"] = fingerprint.to_dict()
                    valid_preview_count += 1
                preview_tasks.pop()
                if valid_preview_count >= smoke_preview_target:
                    pending.clear()
                    page_complete = False
                    break

        if preview_tasks:
            referer = page.url

            def fetch(task: tuple[str, str]) -> tuple[
                str,
                str,
                tuple[str, PreviewFingerprint] | PreviewError,
            ]:
                item_id, preview_url = task
                try:
                    result: tuple[str, PreviewFingerprint] | PreviewError = (
                        _download_preview_with_retry(
                            context,
                            preview_url=preview_url,
                            root=root,
                            scheme=scheme,
                            host=host,
                            port=port,
                            maximum_bytes=config.maximum_preview_bytes,
                            asset_hosts=config.asset_hosts,
                            referer=referer,
                        )
                    )
                except PreviewError as exc:
                    result = exc
                return item_id, preview_url, result

            external_only = all(
                not _same_origin(preview_url, scheme, host, port)
                for _, preview_url in preview_tasks
            )
            if external_only and config.preview_workers > 1:
                with ThreadPoolExecutor(
                    max_workers=config.preview_workers,
                    thread_name_prefix="gaojie-preview",
                ) as executor:
                    results = list(executor.map(fetch, preview_tasks))
            else:
                results = [fetch(task) for task in preview_tasks]

            for item_id, preview_url, result in results:
                item = state["inventory"][item_id]
                if isinstance(result, PreviewError):
                    item["preview_status"] = "FAIL"
                    if sum(
                        finding.get("code") == "PREVIEW_INVALID"
                        for finding in state["findings"]
                    ) < 25:
                        state["findings"].append(
                            _finding("PREVIEW_INVALID", preview_url)
                        )
                    continue
                relative, fingerprint = result
                item["preview_status"] = "PASS"
                item["preview_path"] = relative
                item["preview_fingerprint"] = fingerprint.to_dict()
                valid_preview_count += 1

        if page_complete:
            seen.add(category_url)
        state["visited_pages"] = sorted(seen)
        _atomic_json(state_path, state)


def _retry_failed_previews(
    page: Any,
    context: Any,
    *,
    state: dict[str, Any],
    state_path: Path,
    root: Path,
    scheme: str,
    host: str,
    port: int,
    config: GaojieConfig,
) -> None:
    """Revisit completed catalog pages and recover transient preview failures."""

    failed = {
        item_id
        for item_id, item in state["inventory"].items()
        if item.get("preview_status") == "FAIL"
    }
    if state.get("preview_recovery_version") == _PREVIEW_RECOVERY_VERSION:
        return
    if not failed:
        state["preview_recovery_version"] = _PREVIEW_RECOVERY_VERSION
        _atomic_json(state_path, state)
        return

    for category_url in state.get("visited_pages", []):
        if not failed:
            break
        response = page.goto(category_url, wait_until="domcontentloaded")
        if "login.aspx" in page.url.casefold():
            raise AcquisitionError("authenticated session expired")
        if response is None:
            continue
        changed = False
        tasks: list[tuple[str, str]] = []
        referer = page.url
        for card in _product_cards(page):
            detail_url = card["href"].split("#", 1)[0]
            if (
                not _same_origin(detail_url, scheme, host, port)
                or not _is_product_detail(detail_url)
            ):
                continue
            item_id = _item_id(detail_url)
            if item_id not in failed:
                continue
            preview_url = _normalize_asset_url(
                urljoin(referer, card["preview"]),
                config.asset_hosts,
            )
            tasks.append((item_id, preview_url))

        def fetch(task: tuple[str, str]) -> tuple[
            str,
            tuple[str, PreviewFingerprint] | PreviewError,
        ]:
            item_id, preview_url = task
            try:
                result: tuple[str, PreviewFingerprint] | PreviewError = (
                    _download_preview_with_retry(
                        context,
                        preview_url=preview_url,
                        root=root,
                        scheme=scheme,
                        host=host,
                        port=port,
                        maximum_bytes=config.maximum_preview_bytes,
                        asset_hosts=config.asset_hosts,
                        referer=referer,
                    )
                )
            except PreviewError as exc:
                result = exc
            return item_id, result

        external_only = all(
            not _same_origin(preview_url, scheme, host, port)
            for _, preview_url in tasks
        )
        if tasks and external_only and config.preview_workers > 1:
            with ThreadPoolExecutor(
                max_workers=config.preview_workers,
                thread_name_prefix="gaojie-preview-retry",
            ) as executor:
                results = list(executor.map(fetch, tasks))
        else:
            results = [fetch(task) for task in tasks]

        for item_id, result in results:
            if isinstance(result, PreviewError):
                continue
            relative, fingerprint = result
            item = state["inventory"][item_id]
            item["preview_status"] = "PASS"
            item["preview_path"] = relative
            item["preview_fingerprint"] = fingerprint.to_dict()
            failed.remove(item_id)
            changed = True
        if changed:
            _atomic_json(state_path, state)
    state["preview_recovery_version"] = _PREVIEW_RECOVERY_VERSION
    _atomic_json(state_path, state)


def _build_selections(
    state: dict[str, Any],
    config: GaojieConfig,
) -> list[str]:
    selected_global: list[str] = []
    completed_item_ids = {
        item_id
        for artifact in state.get("artifacts", [])
        for item_id in artifact.get("item_ids", [])
    }
    for category_key in sorted(state["categories"]):
        candidates: dict[str, PreviewFingerprint] = {}
        for item_id, item in state["inventory"].items():
            if (
                category_key in item.get("category_keys", [])
                and item.get("preview_status") == "PASS"
                and item.get("download_status") not in {"NO_LINK", "UNAVAILABLE"}
            ):
                try:
                    candidates[item_id] = _fingerprint_from_state(
                        item["preview_fingerprint"]
                    )
                except (KeyError, TypeError, ValueError):
                    continue
        limit = config.items_per_category
        if config.maximum_items is not None:
            limit = max(config.maximum_items * 4, config.maximum_items)
        proposal = select_diverse(
            candidates,
            limit=min(max(limit * 4, limit), max(len(candidates), 1)),
            near_duplicate_distance=config.near_duplicate_distance,
        )
        completed = {
            item_id: fingerprint
            for item_id, fingerprint in candidates.items()
            if item_id in completed_item_ids
        }
        locked = select_diverse(
            completed,
            limit=limit,
            near_duplicate_distance=config.near_duplicate_distance,
        )["selected_item_ids"]
        selected_ids = list(locked)
        for item_id in proposal["selected_item_ids"]:
            if item_id not in selected_ids:
                selected_ids.append(item_id)
            if len(selected_ids) >= limit:
                break
        baseline_ids = sorted(candidates)[: min(limit, len(candidates))]
        baseline_metric = median_nearest_neighbor(
            candidates[item_id] for item_id in baseline_ids
        )
        selected_metric = median_nearest_neighbor(
            candidates[item_id] for item_id in selected_ids
        )
        selection = {
            **proposal,
            "selected_item_ids": selected_ids,
            "baseline_median_nearest_neighbor": baseline_metric,
            "selected_median_nearest_neighbor": selected_metric,
            "selection_gain": round(selected_metric - baseline_metric, 8),
            "locked_downloaded_count": len(locked),
            "rule_version": "gaojie-diversity-availability.v3",
        }
        state["selections"][category_key] = selection
        if (
            config.maximum_items is None
            and len(selection["selected_item_ids"]) < config.minimum_diverse_items
        ):
            state["findings"].append(
                {
                    "code": "DIVERSITY_SHORTFALL",
                    "path": hashlib.sha256(
                        category_key.encode("utf-8")
                    ).hexdigest(),
                }
            )
        for item_id in selection["selected_item_ids"]:
            if item_id not in selected_global:
                selected_global.append(item_id)
    return selected_global


def _download_selected(
    page: Any,
    context: Any,
    *,
    selected_item_ids: list[str],
    state: dict[str, Any],
    state_path: Path,
    root: Path,
    scheme: str,
    host: str,
    port: int,
    config: GaojieConfig,
) -> None:
    completed_hashes = {item["sha256"] for item in state["artifacts"]}
    completed_item_ids = {
        item_id
        for artifact in state["artifacts"]
        for item_id in artifact.get("item_ids", [])
    }
    visited = set(state.get("visited_details", []))
    source_root = root / "sources" / "gaojie"

    def record_transient_failure(item: dict[str, Any]) -> None:
        attempts = int(item.get("download_failure_count", 0)) + 1
        item["download_failure_count"] = attempts
        if attempts >= 3:
            item["download_status"] = "UNAVAILABLE"

    for item_id in selected_item_ids:
        if (
            config.maximum_items is not None
            and len(state["artifacts"]) >= config.maximum_items
        ):
            break
        if item_id in completed_item_ids:
            state["inventory"][item_id]["download_status"] = "PASS"
            state["inventory"][item_id].pop("download_failure_count", None)
            continue
        item = state["inventory"][item_id]
        detail_url = item["detail_url"]
        try:
            detail_response = context.request.get(
                detail_url,
                headers={"Referer": config.origin.rstrip("/") + "/"},
                timeout=30_000,
            )
        except Exception:
            record_transient_failure(item)
            state["findings"].append(_finding("DETAIL_HTTP_ERROR", detail_url))
            _atomic_json(state_path, state)
            continue
        if "login.aspx" in detail_response.url.casefold():
            state["status"] = "NEEDS_AUTH"
            state["findings"].append(_finding("AUTH_SESSION_EXPIRED", detail_url))
            return
        if not detail_response.ok or not _same_origin(
            detail_response.url,
            scheme,
            host,
            port,
        ):
            record_transient_failure(item)
            state["findings"].append(_finding("DETAIL_HTTP_ERROR", detail_url))
            _atomic_json(state_path, state)
            continue
        try:
            detail_hrefs = _html_hrefs(
                detail_response.text(),
                detail_response.url,
            )
        except Exception:
            record_transient_failure(item)
            state["findings"].append(_finding("DETAIL_HTML_INVALID", detail_url))
            _atomic_json(state_path, state)
            continue
        downloads = []
        for href in detail_hrefs:
            candidate = _normalize_asset_url(
                href,
                config.asset_hosts,
            )
            if (
                _allowed_asset_url(
                    candidate,
                    scheme=scheme,
                    host=host,
                    port=port,
                    asset_hosts=config.asset_hosts,
                )
                and _direct_file_suffix(candidate) is not None
            ):
                downloads.append(candidate)
        downloads = sorted(set(downloads))
        if not downloads:
            item["download_status"] = "NO_LINK"
            state["findings"].append(_finding("DOWNLOAD_LINK_NOT_FOUND", detail_url))
        for download_url in downloads:
            suffix = _direct_file_suffix(download_url)
            if suffix is None:
                continue
            if _free_gb(root) < config.minimum_free_gb:
                state["status"] = "FAIL"
                state["findings"].append({"code": "LOW_DISK_SPACE"})
                return
            if _same_origin(download_url, scheme, host, port):
                try:
                    response = context.request.get(
                        download_url,
                        headers={"Referer": detail_url},
                        timeout=60_000,
                    )
                except Exception:
                    record_transient_failure(item)
                    state["findings"].append(
                        _finding("DOWNLOAD_HTTP_ERROR", detail_url)
                    )
                    _atomic_json(state_path, state)
                    continue
                if not response.ok:
                    record_transient_failure(item)
                    state["findings"].append(
                        _finding("DOWNLOAD_HTTP_ERROR", detail_url)
                    )
                    _atomic_json(state_path, state)
                    continue
                response_url = response.url
                response_headers = {
                    key.casefold(): value
                    for key, value in response.headers.items()
                }
                declared = response_headers.get("content-length")
                if (
                    declared
                    and declared.isdigit()
                    and int(declared) > config.maximum_file_bytes
                ):
                    state["findings"].append(
                        _finding("DOWNLOAD_TOO_LARGE", detail_url)
                    )
                    continue
                try:
                    payload = response.body()
                except Exception:
                    record_transient_failure(item)
                    state["findings"].append(
                        _finding("DOWNLOAD_HTTP_ERROR", detail_url)
                    )
                    _atomic_json(state_path, state)
                    continue
            else:
                request = Request(
                    download_url,
                    headers={
                        "Referer": detail_url,
                        "User-Agent": "Mozilla/5.0 Window-PPTX/1.0",
                    },
                )
                try:
                    with urlopen(request, timeout=60) as remote:
                        response_url = remote.geturl()
                        response_headers = {
                            key.casefold(): value
                            for key, value in remote.headers.items()
                        }
                        declared = response_headers.get("content-length")
                        if (
                            declared
                            and declared.isdigit()
                            and int(declared) > config.maximum_file_bytes
                        ):
                            state["findings"].append(
                                _finding("DOWNLOAD_TOO_LARGE", detail_url)
                            )
                            continue
                        payload = remote.read(config.maximum_file_bytes + 1)
                except Exception:
                    record_transient_failure(item)
                    state["findings"].append(
                        _finding("DOWNLOAD_HTTP_ERROR", detail_url)
                    )
                    _atomic_json(state_path, state)
                    continue
            if not _allowed_asset_url(
                response_url,
                scheme=scheme,
                host=host,
                port=port,
                asset_hosts=config.asset_hosts,
            ):
                state["findings"].append(
                    _finding("DOWNLOAD_REDIRECT_REJECTED", detail_url)
                )
                continue
            content_type = response_headers.get("content-type", "").casefold()
            if "text/html" in content_type:
                state["findings"].append(
                    _finding("DOWNLOAD_RETURNED_HTML", detail_url)
                )
                continue
            declared = response_headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > config.maximum_file_bytes:
                state["findings"].append(_finding("DOWNLOAD_TOO_LARGE", detail_url))
                continue
            if len(payload) > config.maximum_file_bytes:
                state["findings"].append(_finding("DOWNLOAD_TOO_LARGE", detail_url))
                continue
            if not _valid_powerpoint(payload, suffix):
                state["findings"].append(
                    _finding("DOWNLOAD_PACKAGE_INVALID", detail_url)
                )
                continue
            if _free_gb(root) < config.minimum_free_gb + len(payload) / (1024**3):
                state["status"] = "FAIL"
                state["findings"].append({"code": "LOW_DISK_SPACE"})
                return
            digest = hashlib.sha256(payload).hexdigest()
            if digest in completed_hashes:
                for artifact in state["artifacts"]:
                    if artifact["sha256"] == digest:
                        artifact["category_keys"] = sorted(
                            set(artifact.get("category_keys", []))
                            | set(item["category_keys"])
                        )
                        artifact["item_ids"] = sorted(
                            set(artifact.get("item_ids", [])) | {item_id}
                        )
                completed_item_ids.add(item_id)
                item["download_status"] = "PASS"
                item.pop("download_failure_count", None)
                _atomic_json(state_path, state)
                continue
            primary_key = sorted(item["category_keys"])[0]
            category = state["categories"][primary_key]
            target_dir = (
                source_root
                / f"{int(category['category_id']):03d}-{_safe_name(category['name'], category['category_id'])}"
                / _safe_name(item["title"], item_id)
            )
            name = _filename(
                response_headers,
                download_url,
                digest,
            )
            target = target_dir / name
            if target.exists():
                target = target.with_name(
                    f"{target.stem}-{digest[:12]}{target.suffix}"
                )
            _atomic_bytes(target, payload)
            state["artifacts"].append(
                {
                    "item_ids": [item_id],
                    "category_keys": sorted(item["category_keys"]),
                    "title": item["title"],
                    "path": target.relative_to(root).as_posix(),
                    "sha256": digest,
                    "bytes": len(payload),
                    "source_url_sha256": _url_digest(download_url),
                    "verified_mtime_ns": target.stat().st_mtime_ns,
                }
            )
            item["download_status"] = "PASS"
            item.pop("download_failure_count", None)
            completed_hashes.add(digest)
            completed_item_ids.add(item_id)
            _atomic_json(state_path, state)
        visited.add(detail_url)
        state["visited_details"] = sorted(visited)
        _atomic_json(state_path, state)


def _sync_gaojie_impl(config: GaojieConfig) -> dict[str, Any]:
    """Inventory previews, select diverse candidates, and acquire packages."""

    scheme, host, port = _validate_config(config)
    root = config.private_root
    state_path, state = _load_state(root, config.origin)
    state["status"] = "PARTIAL"
    state["findings"] = [
        finding
        for finding in state.get("findings", [])
        if finding.get("code", "").startswith("RESUME_")
        or finding.get("code") == "PREVIEW_RULE_REBUILT"
    ]
    if _free_gb(root) < config.minimum_free_gb:
        state["status"] = "FAIL"
        state["findings"].append({"code": "LOW_DISK_SPACE"})
        _atomic_json(state_path, state)
        return state

    cookie_pairs = parse_cookie_header(
        config.credential_file.read_text(encoding="utf-8").strip()
    )
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise AcquisitionError("Playwright is not installed") from exc

    with (
        sync_playwright() as runtime,
        runtime.chromium.launch(headless=config.headless) as browser,
        browser.new_context(accept_downloads=True) as context,
    ):
        context.add_cookies(
            [
                {"name": name, "value": value, "url": config.origin.rstrip("/")}
                for name, value in cookie_pairs
            ]
        )
        page = context.new_page()
        entry = urljoin(
            f"{config.origin.rstrip('/')}/", "products.aspx?category_id=0"
        )
        page.goto(entry, wait_until="domcontentloaded")
        if "login.aspx" in page.url.casefold() or page.locator(
            "#txtUserName, #btnSubmit"
        ).count():
            state["status"] = "NEEDS_AUTH"
            state["findings"].append({"code": "AUTH_SESSION_REJECTED"})
            _atomic_json(state_path, state)
            return state

        categories: dict[str, dict[str, str]] = {}
        observed_routes: dict[str, set[str]] = {}
        for link in _links(page):
            parsed = urlsplit(link["href"])
            match = _CATEGORY_RE.search(link["href"])
            if match and _same_origin(link["href"], scheme, host, port):
                observed_routes.setdefault(parsed.path.casefold(), set()).add(
                    match.group(1)
                )
            category = _category_key(link["href"])
            if category is None:
                continue
            path, category_id = category
            key = _category_state_key(path, category_id)
            categories[key] = {
                "route_path": path,
                "category_id": category_id,
                "name": _safe_name(link["text"], f"category-{category_id}"),
                "url": link["href"],
            }
        state["observed_routes"] = {
            route: len(ids) for route, ids in sorted(observed_routes.items())
        }
        if not categories:
            state["status"] = "FAIL"
            state["findings"].append({"code": "CATEGORY_NAVIGATION_NOT_FOUND"})
            _atomic_json(state_path, state)
            return state
        if len(categories) < config.minimum_categories:
            state["status"] = "FAIL"
            state["findings"].append({"code": "CATEGORY_TAXONOMY_INCOMPLETE"})
            state["category_count"] = len(categories)
            _atomic_json(state_path, state)
            return state
        state["categories"] = categories

        smoke_target = None
        if config.maximum_items is not None:
            smoke_target = max(config.maximum_items * 4, config.maximum_items)
        for category_key in sorted(
            categories,
            key=lambda key: int(categories[key]["category_id"]),
        ):
            _inventory_category(
                page,
                context,
                category_key=category_key,
                category=categories[category_key],
                state=state,
                state_path=state_path,
                root=root,
                scheme=scheme,
                host=host,
                port=port,
                config=config,
                smoke_preview_target=smoke_target,
            )
            if config.maximum_items is not None:
                valid = sum(
                    item.get("preview_status") == "PASS"
                    for item in state["inventory"].values()
                )
                if valid >= smoke_target:
                    break

        _retry_failed_previews(
            page,
            context,
            state=state,
            state_path=state_path,
            root=root,
            scheme=scheme,
            host=host,
            port=port,
            config=config,
        )
        selected = _build_selections(state, config)
        state["download_pass_completed"] = False
        _atomic_json(state_path, state)
        _download_selected(
            page,
            context,
            selected_item_ids=selected,
            state=state,
            state_path=state_path,
            root=root,
            scheme=scheme,
            host=host,
            port=port,
            config=config,
        )
        state["download_pass_completed"] = True
        _atomic_json(state_path, state)

    if state["status"] not in {"FAIL", "NEEDS_AUTH"}:
        state["status"] = "PASS" if state["artifacts"] else "FAIL"
        if not state["artifacts"]:
            state["findings"].append({"code": "NO_VALID_ARTIFACTS"})
    state["artifact_count"] = len(state["artifacts"])
    state["category_count"] = len(state["categories"])
    state["inventory_count"] = len(state["inventory"])
    state["selected_count"] = len(
        {
            item_id
            for selection in state["selections"].values()
            for item_id in selection.get("selected_item_ids", [])
        }
    )
    _atomic_json(state_path, state)
    return state


def sync_gaojie(config: GaojieConfig) -> dict[str, Any]:
    """Run acquisition and convert unexpected runtime failures to redacted state."""

    try:
        return _sync_gaojie_impl(config)
    except AcquisitionError as exc:
        if "session expired" not in str(exc):
            raise
        state_path, state = _load_state(config.private_root, config.origin)
        state["status"] = "NEEDS_AUTH"
        state["findings"].append({"code": "AUTH_SESSION_EXPIRED"})
        _atomic_json(state_path, state)
        return state
    except Exception as exc:
        state_path, state = _load_state(config.private_root, config.origin)
        if (
            type(exc).__name__ == "TimeoutError"
            and state.get("download_pass_completed")
        ):
            state["status"] = "PARTIAL"
            state["findings"].append({"code": "BROWSER_CLEANUP_TIMEOUT"})
            state["artifact_count"] = len(state.get("artifacts", []))
            state["category_count"] = len(state.get("categories", {}))
            state["inventory_count"] = len(state.get("inventory", {}))
            _atomic_json(state_path, state)
            return state
        state["status"] = "FAIL"
        crash_code = "GAOJIE_SYNC_CRASHED"
        if {"code": crash_code} not in state["findings"]:
            state["findings"].append({"code": crash_code})
        state["artifact_count"] = len(state.get("artifacts", []))
        state["category_count"] = len(state.get("categories", {}))
        state["inventory_count"] = len(state.get("inventory", {}))
        _atomic_json(state_path, state)
        return state
