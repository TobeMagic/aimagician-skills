"""Authenticated, resumable Playwright acquisition for the private Gaojie catalog."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

from .acquisition import AcquisitionError, validate_private_credential_file


_CATEGORY_RE = re.compile(r"(?:^|[?&])category_id=(\d+)", re.I)
_DOWNLOAD_RE = re.compile(r"(download|down|下载|\.pptx?(?:$|[?#])|\.potx?(?:$|[?#])|\.zip(?:$|[?#]))", re.I)
_ALLOWED_SUFFIXES = {".pptx", ".ppt", ".potx", ".pot", ".zip"}


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


def parse_cookie_header(value: str) -> list[tuple[str, str]]:
    """Parse a Cookie header without returning attributes or logging values."""

    cookies: list[tuple[str, str]] = []
    for part in value.split(";"):
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
    port = parsed.port or (80 if parsed.scheme == "http" else 443)
    return parsed.scheme, parsed.hostname.casefold(), port


def _safe_name(value: str, fallback: str) -> str:
    value = unquote(value).strip().replace("\\", "_").replace("/", "_")
    value = re.sub(r"[\x00-\x1f<>:\"|?*]+", "_", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return (value[:120] or fallback)


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
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
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


def _free_gb(path: Path) -> float:
    path.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(path).free / (1024 ** 3)


def _links(page: Any) -> list[dict[str, str]]:
    return page.locator("a[href]").evaluate_all(
        """els => els.map(a => ({href: a.href, text: (a.innerText || a.title || '').trim()}))"""
    )


def _filename(headers: dict[str, str], url: str, digest: str) -> str:
    disposition = headers.get("content-disposition", "")
    match = re.search(r"filename\*?=(?:UTF-8''|[\"']?)([^\"';]+)", disposition, re.I)
    candidate = match.group(1) if match else Path(urlsplit(url).path).name
    name = _safe_name(candidate, f"{digest[:16]}.pptx")
    suffix = Path(name).suffix.casefold()
    if suffix not in _ALLOWED_SUFFIXES:
        name = f"{name}.pptx"
    return name


def _is_detail_link(url: str) -> bool:
    parsed = urlsplit(url)
    path = parsed.path.casefold()
    query = {key.casefold() for key in parse_qs(parsed.query)}
    return (
        any(token in path for token in ("detail", "view", "show", "product_"))
        or ("product" in path and bool(query.intersection({"id", "product_id", "productid"})))
    )


def _sync_gaojie_impl(config: GaojieConfig) -> dict[str, Any]:
    """Acquire entitled packages and persist a secret-free resumable state."""

    scheme, host, port = _validate_config(config)
    root = config.private_root
    state_path = root / "state" / "gaojie-sync.json"
    state: dict[str, Any] = {
        "schema_version": "gaojie-sync.v1",
        "status": "PARTIAL",
        "origin": config.origin.rstrip("/"),
        "categories": {},
        "visited_pages": [],
        "visited_details": [],
        "artifacts": [],
        "findings": [],
    }
    if state_path.is_file():
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8"))
            if previous.get("schema_version") == state["schema_version"] and previous.get("origin") == state["origin"]:
                state.update(previous)
        except (OSError, json.JSONDecodeError):
            state["findings"].append({"code": "RESUME_STATE_IGNORED"})

    secret = config.credential_file.read_text(encoding="utf-8").strip()
    cookie_pairs = parse_cookie_header(secret)
    valid_artifacts: list[dict[str, Any]] = []
    for item in state["artifacts"]:
        try:
            candidate = (root / item["path"]).resolve()
            candidate.relative_to(root.resolve())
            expected_hash = item["sha256"]
            expected_size = item["bytes"]
        except (KeyError, OSError, TypeError, ValueError):
            continue
        if not candidate.is_file() or candidate.stat().st_size != expected_size:
            continue
        actual_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual_hash == expected_hash:
            valid_artifacts.append(item)
    if len(valid_artifacts) != len(state["artifacts"]):
        state["findings"].append({"code": "RESUME_ARTIFACT_RECONCILED"})
        state["artifacts"] = valid_artifacts
        state["visited_details"] = []
    completed_hashes = {item["sha256"] for item in valid_artifacts}
    source_root = root / "sources" / "gaojie"
    if _free_gb(root) < config.minimum_free_gb:
        state["status"] = "FAIL"
        state["findings"].append({"code": "LOW_DISK_SPACE"})
        _atomic_json(state_path, state)
        return state

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
            [{"name": name, "value": value, "url": config.origin.rstrip("/")} for name, value in cookie_pairs]
        )
        page = context.new_page()
        entry = urljoin(f"{config.origin.rstrip('/')}/", "products.aspx?category_id=0")
        page.goto(entry, wait_until="domcontentloaded")
        if "login.aspx" in page.url.casefold() or page.locator("#txtUserName, #btnSubmit").count():
            state["status"] = "NEEDS_AUTH"
            state["findings"].append({"code": "AUTH_SESSION_REJECTED"})
            _atomic_json(state_path, state)
            return state

        category_links: dict[str, dict[str, str]] = {}
        for link in _links(page):
            match = _CATEGORY_RE.search(link["href"])
            if match and _same_origin(link["href"], scheme, host, port):
                query = parse_qs(urlsplit(link["href"]).query)
                candidate = {
                    "name": _safe_name(link["text"], f"category-{match.group(1)}"),
                    "url": link["href"],
                }
                if not any(key.casefold() in {"page", "p", "pageindex"} for key in query):
                    category_links[match.group(1)] = candidate
                else:
                    category_links.setdefault(match.group(1), candidate)
        if not category_links:
            state["status"] = "FAIL"
            state["findings"].append({"code": "CATEGORY_NAVIGATION_NOT_FOUND"})
            _atomic_json(state_path, state)
            return state
        if len(category_links) < config.minimum_categories:
            state["status"] = "FAIL"
            state["findings"].append({"code": "CATEGORY_TAXONOMY_INCOMPLETE"})
            state["category_count"] = len(category_links)
            _atomic_json(state_path, state)
            return state

        detail_urls: dict[str, dict[str, Any]] = {}
        for category_id, category in sorted(category_links.items(), key=lambda item: int(item[0])):
            state["categories"][category_id] = category["name"]
            pending = [category["url"]]
            seen: set[str] = set()
            while pending:
                category_url = pending.pop(0)
                if category_url in seen:
                    continue
                seen.add(category_url)
                page.goto(category_url, wait_until="domcontentloaded")
                if "login.aspx" in page.url.casefold():
                    state["status"] = "NEEDS_AUTH"
                    state["findings"].append({"code": "AUTH_SESSION_EXPIRED"})
                    _atomic_json(state_path, state)
                    return state
                state["visited_pages"] = sorted(set(state["visited_pages"]) | {category_url})
                for link in _links(page):
                    href = link["href"].split("#", 1)[0]
                    if not _same_origin(href, scheme, host, port) or "login.aspx" in href.casefold():
                        continue
                    query = parse_qs(urlsplit(href).query)
                    if _CATEGORY_RE.search(href) and any(key.casefold() in {"page", "p", "pageindex"} for key in query):
                        pending.append(href)
                    elif (
                        not _CATEGORY_RE.search(href)
                        and not _DOWNLOAD_RE.search(href)
                        and _is_detail_link(href)
                    ):
                        entry = detail_urls.setdefault(
                            href,
                            {"category_ids": [], "title": _safe_name(link["text"], "item")},
                        )
                        if category_id not in entry["category_ids"]:
                            entry["category_ids"].append(category_id)

        visited_details = set(state["visited_details"])
        for detail_url, detail in sorted(detail_urls.items()):
            category_ids = sorted(detail["category_ids"], key=int)
            category_id = category_ids[0]
            title = detail["title"]
            if len(category_ids) > 1:
                state["findings"].append({
                    "code": "MULTI_CATEGORY_PRODUCT",
                    "path": hashlib.sha256(detail_url.encode("utf-8")).hexdigest(),
                })
            if config.maximum_items is not None and len(state["artifacts"]) >= config.maximum_items:
                break
            if detail_url in visited_details:
                continue
            page.goto(detail_url, wait_until="domcontentloaded")
            if "login.aspx" in page.url.casefold():
                state["status"] = "NEEDS_AUTH"
                state["findings"].append({"code": "AUTH_SESSION_EXPIRED"})
                break
            downloads = [
                link["href"] for link in _links(page)
                if _same_origin(link["href"], scheme, host, port)
                and _DOWNLOAD_RE.search(f"{link['text']} {link['href']}")
            ]
            if not downloads:
                state["findings"].append({"code": "DOWNLOAD_LINK_NOT_FOUND", "path": detail_url})
            for download_url in sorted(set(downloads)):
                if _free_gb(root) < config.minimum_free_gb:
                    state["findings"].append({"code": "LOW_DISK_SPACE"})
                    state["status"] = "FAIL"
                    break
                response = context.request.get(download_url)
                if not response.ok:
                    state["findings"].append({"code": "DOWNLOAD_HTTP_ERROR", "path": detail_url})
                    continue
                if not _same_origin(response.url, scheme, host, port):
                    state["findings"].append({"code": "DOWNLOAD_REDIRECT_REJECTED", "path": detail_url})
                    continue
                content_type = response.headers.get("content-type", "").casefold()
                if "text/html" in content_type:
                    state["findings"].append({"code": "DOWNLOAD_RETURNED_HTML", "path": detail_url})
                    continue
                declared_size = response.headers.get("content-length")
                if declared_size and declared_size.isdigit() and int(declared_size) > config.maximum_file_bytes:
                    state["findings"].append({"code": "DOWNLOAD_TOO_LARGE", "path": detail_url})
                    continue
                payload = response.body()
                if len(payload) > config.maximum_file_bytes:
                    state["findings"].append({"code": "DOWNLOAD_TOO_LARGE", "path": detail_url})
                    continue
                required_free = config.minimum_free_gb + len(payload) / (1024 ** 3)
                if _free_gb(root) < required_free:
                    state["findings"].append({"code": "LOW_DISK_SPACE"})
                    state["status"] = "FAIL"
                    break
                digest = hashlib.sha256(payload).hexdigest()
                if digest in completed_hashes:
                    for artifact in state["artifacts"]:
                        if artifact["sha256"] == digest:
                            artifact["category_ids"] = sorted(
                                set(artifact.get("category_ids", [artifact["category_id"]]))
                                | set(category_ids),
                                key=int,
                            )
                    _atomic_json(state_path, state)
                    continue
                name = _filename({key.casefold(): value for key, value in response.headers.items()}, download_url, digest)
                target_dir = source_root / f"{int(category_id):02d}-{_safe_name(state['categories'][category_id], category_id)}" / _safe_name(title, digest[:12])
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / name
                if target.exists():
                    target = target.with_name(f"{target.stem}-{digest[:12]}{target.suffix}")
                fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".part", dir=target_dir)
                try:
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(payload)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, target)
                except Exception:
                    try:
                        os.unlink(temporary)
                    except OSError:
                        pass
                    raise
                relative = target.relative_to(root).as_posix()
                state["artifacts"].append({
                    "category_id": category_id,
                    "category_ids": category_ids,
                    "title": title,
                    "path": relative,
                    "sha256": digest,
                    "bytes": len(payload),
                    "source_url_sha256": hashlib.sha256(download_url.encode("utf-8")).hexdigest(),
                })
                completed_hashes.add(digest)
                _atomic_json(state_path, state)
            visited_details.add(detail_url)
            state["visited_details"] = sorted(visited_details)
            _atomic_json(state_path, state)
    if state["status"] not in {"FAIL", "NEEDS_AUTH"}:
        state["status"] = "PASS"
    state["artifact_count"] = len(state["artifacts"])
    state["category_count"] = len(state["categories"])
    _atomic_json(state_path, state)
    return state


def sync_gaojie(config: GaojieConfig) -> dict[str, Any]:
    """Run acquisition and convert unexpected runtime failures to redacted state."""

    try:
        return _sync_gaojie_impl(config)
    except AcquisitionError:
        raise
    except Exception:
        state_path = config.private_root / "state" / "gaojie-sync.json"
        state: dict[str, Any] = {
            "schema_version": "gaojie-sync.v1",
            "status": "FAIL",
            "origin": config.origin.rstrip("/"),
            "categories": {},
            "visited_pages": [],
            "visited_details": [],
            "artifacts": [],
            "findings": [{"code": "GAOJIE_SYNC_CRASHED"}],
            "artifact_count": 0,
            "category_count": 0,
        }
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8"))
            if previous.get("schema_version") == state["schema_version"]:
                state.update(previous)
                state["status"] = "FAIL"
                findings = list(state.get("findings", []))
                if {"code": "GAOJIE_SYNC_CRASHED"} not in findings:
                    findings.append({"code": "GAOJIE_SYNC_CRASHED"})
                state["findings"] = findings
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
        _atomic_json(state_path, state)
        return state
