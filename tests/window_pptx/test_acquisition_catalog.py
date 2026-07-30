from __future__ import annotations

import io
import json
import subprocess
import sys
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import parse_qs, urlsplit
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
CLI = SCRIPTS_ROOT / "manage_window_pptx_library.py"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))


from window_pptx.acquisition import (  # noqa: E402
    AcquisitionError,
    authorization_scope,
    build_acquisition_manifest,
    validate_private_credential_file,
    write_resume_state,
)
from window_pptx.catalog import (  # noqa: E402
    CatalogError,
    catalog_id,
    dependency_closure,
    load_catalog,
    load_legacy_catalog,
    query_catalog,
)
from window_pptx.quarantine import inspect_package_bytes  # noqa: E402
from window_pptx.rights import (  # noqa: E402
    RightsError,
    canonical_digest,
    certification_evidence,
    validate_rights_record,
)
from window_pptx.gaojie_playwright import (  # noqa: E402
    GaojieConfig,
    parse_cookie_header,
    sync_gaojie,
)
import window_pptx.gaojie_playwright as gaojie_module  # noqa: E402


def _zip(entries: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)
    return output.getvalue()


def _safe_pptx() -> bytes:
    return _zip(
        {
            "[Content_Types].xml": (
                b'<?xml version="1.0"?>'
                b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                b'<Default Extension="xml" ContentType="application/xml"/>'
                b"</Types>"
            ),
            "_rels/.rels": (
                b'<?xml version="1.0"?>'
                b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
            ),
            "ppt/presentation.xml": b"<presentation/>",
        }
    )


class _GaojieFixture(BaseHTTPRequestHandler):
    payload = _safe_pptx()
    mode = "normal"

    def log_message(self, *_args: object) -> None:
        return

    def _html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/login.aspx"):
            self._html('<input id="txtUserName"><button id="btnSubmit">login</button>')
            return
        if "session=fixture-ok" not in self.headers.get("Cookie", ""):
            self.send_response(302)
            self.send_header("Location", "/login.aspx")
            self.end_headers()
            return
        if self.path.startswith("/products.aspx"):
            page_two = "page=2" in self.path
            item = "2" if page_two else "1"
            pagination = "" if page_two else '<a href="/products.aspx?category_id=1&page=2">next</a>'
            self._html(
                '<a href="/products.aspx?category_id=1">封面模板</a>'
                '<a href="/products.aspx?category_id=2">目录模板</a>'
                f'<a href="/product-detail.aspx?id={item}">作品 {item}</a>{pagination}'
            )
            return
        if self.path.startswith("/product-detail.aspx"):
            item = parse_qs(urlsplit(self.path).query)["id"][0]
            if self.mode == "missing":
                self._html("<p>暂无下载</p>")
                return
            self._html(f'<a href="/download.ashx?id={item}">下载 PPTX</a>')
            return
        if self.path.startswith("/download.ashx"):
            if self.mode == "http-error":
                self._html("failed", 503)
                return
            if self.mode == "html":
                self._html("<p>session page</p>")
                return
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
            self.send_header("Content-Disposition", 'attachment; filename="fixture.pptx"')
            self.send_header("Content-Length", str(len(self.payload)))
            self.end_headers()
            self.wfile.write(self.payload)
            return
        self._html("not found", 404)


@pytest.fixture
def gaojie_fixture() -> str:
    _GaojieFixture.mode = "normal"
    server = ThreadingHTTPServer(("127.0.0.1", 0), _GaojieFixture)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        _GaojieFixture.mode = "normal"


def test_gaojie_cookie_parser_rejects_empty_or_attribute_only() -> None:
    assert parse_cookie_header("session=ok; Path=/") == [("session", "ok")]
    with pytest.raises(AcquisitionError):
        parse_cookie_header("Path=/; SameSite=Lax")


def test_gaojie_playwright_sync_is_authenticated_resumable_and_deduplicated(
    tmp_path: Path, gaojie_fixture: str
) -> None:
    private_root = tmp_path / ".private"
    credential = private_root / "auth" / "gaojie.cookie"
    credential.parent.mkdir(parents=True)
    credential.write_text("session=fixture-ok", encoding="utf-8")
    config = GaojieConfig(
        origin=gaojie_fixture,
        private_root=private_root,
        credential_file=credential,
        minimum_free_gb=0,
        allow_insecure_http=True,
        minimum_categories=2,
    )

    first = sync_gaojie(config)
    second = sync_gaojie(config)

    assert first["status"] == "PASS"
    assert first["category_count"] == 2
    assert len(first["visited_pages"]) >= 3
    assert first["artifact_count"] == 1  # two entitled URLs contain identical bytes
    assert first["artifacts"][0]["category_ids"] == ["1", "2"]
    assert "MULTI_CATEGORY_PRODUCT" in {
        finding["code"] for finding in first["findings"]
    }
    assert second["artifact_count"] == 1
    artifact = private_root / first["artifacts"][0]["path"]
    assert artifact.read_bytes() == _GaojieFixture.payload
    artifact.unlink()
    repaired = sync_gaojie(config)
    assert repaired["artifact_count"] == 1
    assert (private_root / repaired["artifacts"][0]["path"]).is_file()
    assert {"code": "RESUME_ARTIFACT_RECONCILED"} in repaired["findings"]
    state_text = (private_root / "state" / "gaojie-sync.json").read_text(encoding="utf-8")
    assert "fixture-ok" not in state_text


def test_gaojie_playwright_sync_fails_closed_on_rejected_session(
    tmp_path: Path, gaojie_fixture: str
) -> None:
    private_root = tmp_path / ".private"
    credential = private_root / "auth" / "gaojie.cookie"
    credential.parent.mkdir(parents=True)
    credential.write_text("session=expired", encoding="utf-8")

    result = sync_gaojie(GaojieConfig(
        origin=gaojie_fixture,
        private_root=private_root,
        credential_file=credential,
        minimum_free_gb=0,
        allow_insecure_http=True,
        minimum_categories=2,
    ))

    assert result["status"] == "NEEDS_AUTH"
    assert result["artifacts"] == []
    assert "expired" not in json.dumps(result)


def test_gaojie_playwright_sync_rejects_incomplete_taxonomy(
    tmp_path: Path, gaojie_fixture: str
) -> None:
    private_root = tmp_path / ".private"
    credential = private_root / "auth" / "gaojie.cookie"
    credential.parent.mkdir(parents=True)
    credential.write_text("session=fixture-ok", encoding="utf-8")

    result = sync_gaojie(GaojieConfig(
        origin=gaojie_fixture,
        private_root=private_root,
        credential_file=credential,
        minimum_free_gb=0,
        allow_insecure_http=True,
        minimum_categories=3,
    ))

    assert result["status"] == "FAIL"
    assert {"code": "CATEGORY_TAXONOMY_INCOMPLETE"} in result["findings"]


def test_gaojie_cli_adapter_wiring_is_secret_free(
    tmp_path: Path, gaojie_fixture: str
) -> None:
    private_root = tmp_path / ".private"
    credential = private_root / "auth" / "gaojie.cookie"
    credential.parent.mkdir(parents=True)
    secret = "session=fixture-ok"
    credential.write_text(secret, encoding="utf-8")

    process = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "sync",
            "--private-root",
            str(private_root),
            "--source-id",
            "gaojie-fixture",
            "--source-adapter",
            "gaojie",
            "--origin",
            gaojie_fixture,
            "--allow-host",
            "127.0.0.1",
            "--allow-insecure-http",
            "--credential-file",
            str(credential),
            "--minimum-categories",
            "2",
            "--minimum-free-gb",
            "0",
            "--apply",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(process.stdout)

    assert result["status"] == "PASS"
    assert len(result["completed_item_ids"]) == 1
    assert secret not in process.stdout
    assert secret not in process.stderr


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("missing", "DOWNLOAD_LINK_NOT_FOUND"),
        ("http-error", "DOWNLOAD_HTTP_ERROR"),
        ("html", "DOWNLOAD_RETURNED_HTML"),
    ],
)
def test_gaojie_download_failures_are_explicit(
    tmp_path: Path, gaojie_fixture: str, mode: str, expected: str
) -> None:
    _GaojieFixture.mode = mode
    private_root = tmp_path / ".private"
    credential = private_root / "auth" / "gaojie.cookie"
    credential.parent.mkdir(parents=True)
    credential.write_text("session=fixture-ok", encoding="utf-8")

    result = sync_gaojie(GaojieConfig(
        origin=gaojie_fixture,
        private_root=private_root,
        credential_file=credential,
        minimum_free_gb=0,
        allow_insecure_http=True,
        minimum_categories=2,
    ))

    assert expected in {finding["code"] for finding in result["findings"]}


def test_gaojie_download_and_disk_limits_fail_closed(
    tmp_path: Path, gaojie_fixture: str
) -> None:
    private_root = tmp_path / ".private"
    credential = private_root / "auth" / "gaojie.cookie"
    credential.parent.mkdir(parents=True)
    credential.write_text("session=fixture-ok", encoding="utf-8")
    base = dict(
        origin=gaojie_fixture,
        private_root=private_root,
        credential_file=credential,
        allow_insecure_http=True,
        minimum_categories=2,
    )

    oversized = sync_gaojie(GaojieConfig(
        **base,
        minimum_free_gb=0,
        maximum_file_bytes=1,
    ))
    low_disk = sync_gaojie(GaojieConfig(
        **base,
        minimum_free_gb=10**9,
    ))

    assert "DOWNLOAD_TOO_LARGE" in {finding["code"] for finding in oversized["findings"]}
    assert low_disk["status"] == "FAIL"
    assert "LOW_DISK_SPACE" in {finding["code"] for finding in low_disk["findings"]}


def test_gaojie_unexpected_runtime_failure_is_redacted_and_persisted(
    tmp_path: Path, gaojie_fixture: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    private_root = tmp_path / ".private"
    credential = private_root / "auth" / "gaojie.cookie"
    credential.parent.mkdir(parents=True)
    credential.write_text("session=fixture-ok", encoding="utf-8")

    def crash(_page: object) -> list[dict[str, str]]:
        raise RuntimeError("sensitive runtime detail")

    monkeypatch.setattr(gaojie_module, "_links", crash)
    result = sync_gaojie(GaojieConfig(
        origin=gaojie_fixture,
        private_root=private_root,
        credential_file=credential,
        minimum_free_gb=0,
        allow_insecure_http=True,
        minimum_categories=2,
    ))

    assert result["status"] == "FAIL"
    assert {"code": "GAOJIE_SYNC_CRASHED"} in result["findings"]
    rendered = json.dumps(result)
    assert "sensitive runtime detail" not in rendered
    assert "fixture-ok" not in rendered


def _allowed_rights(source_id: str = "public-seed", item_id: str = "item") -> dict:
    return {
        "schema_version": "1.0",
        "status": "PASS",
        "source_id": source_id,
        "item_id": item_id,
        "access_basis": "public",
        "use_scope": "local_adaptation",
        "redistribution_state": "restricted",
        "evidence_references": ["synthetic-test-evidence"],
        "reviewed_at": "2026-07-29T00:00:00Z",
        "decision": "allowed",
    }


def _certification_fields() -> dict[str, str]:
    report = inspect_package_bytes(_safe_pptx())
    return {
        "rights_record_digest": canonical_digest(_allowed_rights()),
        "quarantine_disposition": "ACCEPT",
        "quarantine_report_digest": canonical_digest(report),
    }


def test_redirect_policy_is_host_scoped_and_strips_cross_host_auth() -> None:
    allowed = {"templates.example.com", "cdn.example.com"}
    assert (
        authorization_scope(
            "https://templates.example.com/list",
            "https://templates.example.com/page/2",
            allowed,
        )
        == "attach"
    )
    assert (
        authorization_scope(
            "https://templates.example.com/list",
            "https://cdn.example.com/file.pptx",
            allowed,
        )
        == "strip"
    )
    assert (
        authorization_scope(
            "https://templates.example.com/list",
            "https://evil.example.net/file.pptx",
            allowed,
        )
        == "reject"
    )
    with pytest.raises(AcquisitionError):
        authorization_scope(
            "http://templates.example.com/list",
            "http://templates.example.com/page/2",
            allowed,
        )
    assert authorization_scope(
        "http://templates.example.com/list",
        "http://templates.example.com/page/2",
        allowed,
        allow_insecure_http_hosts={"templates.example.com"},
    ) == "attach"


def test_private_credential_path_is_required_and_secret_is_never_returned(
    tmp_path: Path,
) -> None:
    private_root = tmp_path / ".private"
    private_root.mkdir()
    secret = "opaque-fixture-" + "redaction-sentinel"
    credential = private_root / "session.txt"
    credential.write_text(secret, encoding="utf-8")

    result = validate_private_credential_file(credential, private_root)

    rendered = json.dumps(result, ensure_ascii=False)
    assert result["status"] == "PASS"
    assert result["credential_digest"].startswith("sha256:")
    assert secret not in rendered
    with pytest.raises(AcquisitionError):
        validate_private_credential_file(tmp_path / "outside.txt", private_root)
    with pytest.raises(AcquisitionError):
        validate_private_credential_file(credential, tmp_path / "private")
    outside_root = tmp_path / "outside-private"
    outside_root.mkdir()
    symlink_root = tmp_path / "links" / ".private"
    symlink_root.parent.mkdir()
    symlink_root.symlink_to(outside_root, target_is_directory=True)
    with pytest.raises(AcquisitionError, match="non-symlink"):
        validate_private_credential_file(outside_root / "missing", symlink_root)


@pytest.mark.parametrize(
    ("entries", "expected_code"),
    [
        ({"../escape.xml": b"x"}, "TRAVERSAL_PATH"),
        ({"ppt/vbaProject.bin": b"x"}, "MACRO_CONTENT"),
        ({"ppt/embeddings/oleObject1.bin": b"x"}, "OLE_CONTENT"),
        ({"ppt/activeX/activeX1.xml": b"x"}, "ACTIVEX_CONTENT"),
        (
            {
                "[Content_Types].xml": (
                    b'<Types><Override PartName="/ppt/hidden.bin" '
                    b'ContentType="application/vnd.ms-powerpoint.presentation.macroEnabled.main+xml"/>'
                    b"</Types>"
                )
            },
            "MACRO_CONTENT",
        ),
        (
            {
                "ppt/slides/_rels/slide1.xml.rels": (
                    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    b'<Relationship Id="rId1" TargetMode="External" Target="https://example.com"/>'
                    b"</Relationships>"
                )
            },
            "EXTERNAL_RELATIONSHIP",
        ),
        (
            {
                "ppt/slides/_rels/slide1.xml.rels": (
                    b'<!DOCTYPE x [<!ENTITY y "z">]>'
                    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
                )
            },
            "XML_DTD_CONTENT",
        ),
    ],
)
def test_quarantine_rejects_active_or_escaping_packages(
    entries: dict[str, bytes], expected_code: str
) -> None:
    report = inspect_package_bytes(_zip(entries))
    assert report["disposition"] == "QUARANTINED"
    assert expected_code in {item["code"] for item in report["findings"]}


def test_passive_safe_package_is_accepted_and_hash_bound() -> None:
    report = inspect_package_bytes(_safe_pptx())
    assert report["disposition"] == "ACCEPT"
    assert report["package_sha256"].startswith("sha256:")
    assert report["entry_count"] == 3
    assert report["findings"] == []


def test_quarantine_rejects_symlink_entries() -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        entry = zipfile.ZipInfo("ppt/media/link")
        entry.create_system = 3
        entry.external_attr = 0o120777 << 16
        archive.writestr(entry, "../outside")
    report = inspect_package_bytes(output.getvalue())
    assert report["disposition"] == "QUARANTINED"
    assert "SYMLINK_ENTRY" in {item["code"] for item in report["findings"]}


def test_certification_requires_matching_allowed_rights_and_accept_report() -> None:
    rights = _allowed_rights()
    report = inspect_package_bytes(_safe_pptx())
    evidence = certification_evidence(
        source_id="public-seed",
        item_id="item",
        quarantine_report=report,
        rights_record=rights,
    )
    assert evidence["content_sha256"] == report["package_sha256"]
    assert evidence["quarantine_disposition"] == "ACCEPT"
    with pytest.raises(RightsError):
        certification_evidence(
            source_id="public-seed",
            item_id="different",
            quarantine_report=report,
            rights_record=rights,
        )
    restricted = {**rights, "status": "NEEDS_RIGHTS", "decision": "restricted"}
    with pytest.raises(RightsError):
        certification_evidence(
            source_id="public-seed",
            item_id="item",
            quarantine_report=report,
            rights_record=restricted,
        )
    with pytest.raises(RightsError, match="metadata-only"):
        certification_evidence(
            source_id="public-seed",
            item_id="item",
            quarantine_report=report,
            rights_record={**rights, "use_scope": "metadata_only"},
        )


def test_rights_record_fails_closed_on_missing_evidence() -> None:
    with pytest.raises(RightsError):
        validate_rights_record(
            {**_allowed_rights(), "evidence_references": []}
        )


def test_acquisition_manifest_is_dry_run_by_default_and_resume_is_atomic(
    tmp_path: Path,
) -> None:
    manifest = build_acquisition_manifest(
        command="discover",
        source_id="public-seed",
        origin="https://templates.example.com",
        allowlisted_hosts=["templates.example.com"],
        requested_item_ids=["item-b", "item-a"],
    )
    assert manifest["mode"] == "dry_run"
    assert manifest["status"] == "PASS"
    assert manifest["requested_item_ids"] == ["item-a", "item-b"]
    assert list(tmp_path.iterdir()) == []

    private_root = tmp_path / ".private"
    state_path = write_resume_state(
        private_root,
        "state/acquisition.json",
        {**manifest, "completed_item_ids": ["item-a"]},
    )
    assert state_path == private_root / "state" / "acquisition.json"
    assert json.loads(state_path.read_text(encoding="utf-8"))[
        "completed_item_ids"
    ] == ["item-a"]
    with pytest.raises(AcquisitionError):
        write_resume_state(private_root, "../escape.json", manifest)
    with pytest.raises(AcquisitionError):
        write_resume_state(tmp_path / "state", "resume.json", manifest)
    with pytest.raises(AcquisitionError):
        build_acquisition_manifest(
            command="discover",
            source_id="public-seed",
            origin="https://templates.example.com",
            allowlisted_hosts=["templates.example.com"],
            mode="apply",
        )


def test_catalog_ids_dedupe_query_and_dependency_closure(tmp_path: Path) -> None:
    content_hash = "sha256:" + "a" * 64
    canonical_id = catalog_id("public-seed", "work-report-spine", "1", content_hash)
    raw = {
        "schema_version": "3.0",
        "catalog_id": "window-pptx-public-seed",
        "entries": [
            {
                "catalog_item_id": canonical_id,
                "source_id": "public-seed",
                "item_id": "work-report-spine",
                "version_id": "1",
                "content_sha256": content_hash,
                "media_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "geometry": {"width_in": 13.333, "height_in": 7.5, "slide_count": 28},
                "phash": {"state": "not_applicable"},
                "capacity": {"min_slides": 24, "max_slides": 32, "max_text_chars": 7200},
                "scenarios": ["annual-work-report"],
                "style_tags": ["editorial", "executive"],
                "rights_decision": "allowed",
                **_certification_fields(),
                "dependency_ids": [],
                "editability": "native_editable",
                "certification": "certified",
                "provenance": ["public-metadata-seed"],
            },
            {
                "catalog_item_id": catalog_id("mirror", "same-bytes", "1", content_hash),
                "source_id": "mirror",
                "item_id": "same-bytes",
                "version_id": "1",
                "content_sha256": content_hash,
                "media_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "geometry": {"width_in": 13.333, "height_in": 7.5, "slide_count": 28},
                "phash": {"state": "not_applicable"},
                "capacity": {"min_slides": 24, "max_slides": 32, "max_text_chars": 7200},
                "scenarios": ["annual-work-report"],
                "style_tags": ["editorial"],
                "rights_decision": "allowed",
                **_certification_fields(),
                "dependency_ids": [],
                "editability": "native_editable",
                "certification": "certified",
                "provenance": ["mirror"],
            },
        ],
    }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    catalog = load_catalog(path)

    assert len(catalog["entries"]) == 1
    results = query_catalog(catalog, scenario="annual-work-report")
    mirror_id = catalog_id("mirror", "same-bytes", "1", content_hash)
    expected_id = min(canonical_id, mirror_id)
    assert [entry["catalog_item_id"] for entry in results] == [expected_id]
    assert dependency_closure(catalog, expected_id) == [expected_id]


def test_dependency_closure_fails_on_missing_and_cycles(tmp_path: Path) -> None:
    base = {
        "source_id": "seed",
        "version_id": "1",
        "content_sha256": "sha256:" + "b" * 64,
        "media_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "geometry": {"width_in": 13.333, "height_in": 7.5, "slide_count": 1},
        "phash": {"state": "not_applicable"},
        "capacity": {"min_slides": 1, "max_slides": 1, "max_text_chars": 100},
        "scenarios": ["annual-work-report"],
        "style_tags": ["editorial"],
        "rights_decision": "allowed",
        **_certification_fields(),
        "editability": "native_editable",
        "certification": "certified",
        "provenance": ["seed"],
    }
    a_id = catalog_id("seed", "a", "1", "sha256:" + "b" * 64)
    b_id = catalog_id("seed", "b", "1", "sha256:" + "c" * 64)
    raw = {
        "schema_version": "3.0",
        "catalog_id": "cycle",
        "entries": [
            {
                **base,
                "catalog_item_id": a_id,
                "item_id": "a",
                "dependency_ids": [b_id],
            },
            {
                **base,
                "catalog_item_id": b_id,
                "item_id": "b",
                "content_sha256": "sha256:" + "c" * 64,
                "dependency_ids": [a_id],
            },
        ],
    }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    catalog = load_catalog(path)
    assert query_catalog(catalog) == []
    with pytest.raises(CatalogError, match="cycle"):
        dependency_closure(catalog, a_id)
    raw["entries"][1]["dependency_ids"] = ["missing"]
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(CatalogError, match="missing"):
        dependency_closure(load_catalog(path), a_id)


def test_catalog_runtime_rejects_schema_shape_drift(tmp_path: Path) -> None:
    content_hash = "sha256:" + "d" * 64
    entry = {
        "catalog_item_id": catalog_id("seed", "bad", "1", content_hash),
        "source_id": "seed",
        "item_id": "bad",
        "version_id": "1",
        "content_sha256": content_hash,
        "media_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "geometry": {"width_in": 13.333, "height_in": 7.5, "slide_count": 1},
        "phash": {"state": "not_applicable"},
        "capacity": {"min_slides": 2, "max_slides": 1, "max_text_chars": 100},
        "scenarios": ["annual-work-report"],
        "style_tags": ["editorial"],
        "rights_decision": "allowed",
        **_certification_fields(),
        "dependency_ids": [],
        "editability": "native_editable",
        "certification": "certified",
        "provenance": ["seed"],
    }
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "3.0",
                "catalog_id": "invalid",
                "entries": [entry],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogError, match="capacity"):
        load_catalog(path)
    with pytest.raises(CatalogError, match="capacity"):
        query_catalog({"entries": [entry]})


def test_legacy_registry_remains_queryable_but_never_auto_selects() -> None:
    entries = load_legacy_catalog(SKILL_ROOT / "registries" / "legacy-templates.json")
    assert len(entries) == 4
    assert all(entry["certification"] == "unverified" for entry in entries)
    assert all(entry["auto_recommend"] is False for entry in entries)
    assert query_catalog({"entries": entries}, scenario=None) == []


@pytest.mark.parametrize("command", ["discover", "sync", "ingest", "certify", "query"])
def test_library_cli_has_machine_readable_dry_run_routes(
    command: str, tmp_path: Path
) -> None:
    args = [
        sys.executable,
        str(CLI),
        command,
        "--private-root",
        str(tmp_path / ".private"),
    ]
    if command == "query":
        args.extend(["--catalog", str(SKILL_ROOT / "registries" / "catalog-v3.json")])
    result = subprocess.run(args, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["command"] == command
    assert payload["mode"] == "dry_run"
    assert not (tmp_path / ".private").exists()


def test_sync_without_private_credential_is_needs_auth(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "sync",
            "--private-root",
            str(tmp_path / ".private"),
            "--source-id",
            "commercial-source",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "NEEDS_AUTH"


def test_public_metadata_sync_does_not_require_auth(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "sync",
            "--private-root",
            str(tmp_path / ".private"),
            "--source-id",
            "public-metadata-seed",
            "--public-metadata-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASS"
    assert payload["findings"] == [{"code": "PUBLIC_METADATA_SYNC_PLANNED"}]
    assert not (tmp_path / ".private").exists()


def test_public_metadata_flag_cannot_bypass_authenticated_source(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "sync",
            "--private-root",
            str(tmp_path / ".private"),
            "--source-id",
            "commercial-source",
            "--public-metadata-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "FAIL"


def test_invalid_credential_still_emits_redacted_machine_json(
    tmp_path: Path,
) -> None:
    private_root = tmp_path / ".private"
    private_root.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "sync",
            "--private-root",
            str(private_root),
            "--credential-file",
            str(private_root / "missing.txt"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "NEEDS_AUTH"
    assert payload["findings"] == [{"code": "PRIVATE_CREDENTIAL_INVALID"}]


def test_cli_apply_is_private_only_and_output_never_contains_secret(
    tmp_path: Path,
) -> None:
    private_root = tmp_path / ".private"
    private_root.mkdir()
    secret = "opaque-cli-" + "redaction-sentinel"
    credential = private_root / "session.txt"
    credential.write_text(secret, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "sync",
            "--private-root",
            str(private_root),
            "--source-id",
            "commercial-source",
            "--credential-file",
            str(credential),
            "--apply",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert secret not in result.stdout
    assert secret not in result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "apply"
    assert payload["state_path"] == "state/commercial-source-sync.json"
    assert payload["status"] == "PARTIAL"
    assert (private_root / "state" / "commercial-source-sync.json").is_file()

    outside_package = tmp_path / "outside.pptx"
    outside_package.write_bytes(_safe_pptx())
    rejected = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "ingest",
            "--private-root",
            str(private_root),
            "--package",
            str(outside_package),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode == 0
    assert json.loads(rejected.stdout)["status"] == "FAIL"


def test_cli_certify_closes_public_metadata_evidence_without_auth(
    tmp_path: Path,
) -> None:
    private_root = tmp_path / ".private"
    private_root.mkdir()
    report = inspect_package_bytes(_safe_pptx())
    rights = _allowed_rights("public-seed", "item")
    report_path = private_root / "quarantine.json"
    rights_path = private_root / "rights.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    rights_path.write_text(json.dumps(rights), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "certify",
            "--private-root",
            str(private_root),
            "--source-id",
            "public-seed",
            "--item-id",
            "item",
            "--quarantine-report",
            str(report_path),
            "--rights-record",
            str(rights_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASS"
    assert payload["completed_item_ids"] == ["item"]


def test_cli_certify_preserves_quarantine_failure_semantics(
    tmp_path: Path,
) -> None:
    private_root = tmp_path / ".private"
    private_root.mkdir()
    report = inspect_package_bytes(_zip({"ppt/vbaProject.bin": b"x"}))
    report_path = private_root / "quarantine.json"
    rights_path = private_root / "rights.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    rights_path.write_text(
        json.dumps(_allowed_rights("public-seed", "item")), encoding="utf-8"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "certify",
            "--private-root",
            str(private_root),
            "--source-id",
            "public-seed",
            "--item-id",
            "item",
            "--quarantine-report",
            str(report_path),
            "--rights-record",
            str(rights_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "QUARANTINED"


def test_public_metadata_seed_traces_all_five_commands_without_auth(
    tmp_path: Path,
) -> None:
    private_root = tmp_path / ".private"
    private_root.mkdir()
    package_path = private_root / "seed.pptx"
    package_path.write_bytes(_safe_pptx())
    report = inspect_package_bytes(package_path.read_bytes())
    report_path = private_root / "quarantine.json"
    rights_path = private_root / "rights.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    rights_path.write_text(
        json.dumps(_allowed_rights("public-metadata-seed", "item")), encoding="utf-8"
    )
    commands = [
        ["discover", "--item-id", "item"],
        ["sync", "--item-id", "item", "--public-metadata-only"],
        ["ingest", "--package", str(package_path)],
        [
            "certify",
            "--item-id",
            "item",
            "--quarantine-report",
            str(report_path),
            "--rights-record",
            str(rights_path),
        ],
        [
            "query",
            "--catalog",
            str(SKILL_ROOT / "registries" / "catalog-v3.json"),
            "--include-uncertified",
        ],
    ]
    payloads = []
    for command in commands:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                *command,
                "--private-root",
                str(private_root),
                "--source-id",
                "public-metadata-seed",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        payloads.append(json.loads(result.stdout))
    assert [payload["command"] for payload in payloads] == [
        "discover",
        "sync",
        "ingest",
        "certify",
        "query",
    ]
    assert all(payload["status"] == "PASS" for payload in payloads)
    assert all(payload["mode"] == "dry_run" for payload in payloads)


def test_phase37_contracts_and_public_seed_validate() -> None:
    schema_root = SKILL_ROOT / "schemas"
    acquisition = build_acquisition_manifest(
        command="discover",
        source_id="public-seed",
        origin="https://templates.example.com",
        allowlisted_hosts=["templates.example.com"],
    )
    quarantine = inspect_package_bytes(_safe_pptx())
    rights = _allowed_rights(
        "public-seed", "annual-work-report-editorial-spine"
    )
    catalog = json.loads(
        (SKILL_ROOT / "registries" / "catalog-v3.json").read_text(encoding="utf-8")
    )
    fixtures = {
        "acquisition-manifest.v1.schema.json": acquisition,
        "quarantine-report.v1.schema.json": quarantine,
        "rights-record.v1.schema.json": rights,
        "catalog.v3.schema.json": catalog,
    }
    for schema_name, instance in fixtures.items():
        schema = json.loads((schema_root / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(instance)

    entry = catalog["entries"][0]
    assert entry["catalog_item_id"] == catalog_id(
        entry["source_id"],
        entry["item_id"],
        entry["version_id"],
        entry["content_sha256"],
    )
    assert query_catalog(catalog) == []
    assert len(query_catalog(catalog, include_uncertified=True)) == 1
