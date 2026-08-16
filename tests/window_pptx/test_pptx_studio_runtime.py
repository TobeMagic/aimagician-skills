from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"))

from pptx_studio.catalog import certification_evidence_sha256
from pptx_studio.runtime import RuntimeError, runtime_health, resolve_private_library_root


def _private_root(tmp_path):
    root = tmp_path / ".private"
    catalog = root / "intelligence/pptx-studio/catalogs/gaojie-active.v7.json"
    observations = root / "intelligence/pptx-studio/vision/gaojie-active-observations.v1.json"
    certification = root / "intelligence/gaojie/certified-core.json"
    source = root / "sources/gaojie/003-cover"
    catalog.parent.mkdir(parents=True)
    observations.parent.mkdir(parents=True)
    certification.parent.mkdir(parents=True)
    source.mkdir(parents=True)
    (source / "one.pptx").write_bytes(b"fixture")
    certification_payload = {
        "schema_version": "gaojie-certified-core.v2",
        "denied_page_count": 0,
        "denied_pages": [],
    }
    certification.write_text(json.dumps(certification_payload), encoding="utf-8")
    catalog.write_text(json.dumps({
        "pages": [{"page_id": "p1"}],
        "certification_overlay": {
            "schema_version": "pptx-studio-certification-overlay.v1",
            "status": "PASS",
            "source_schema_version": "gaojie-certified-core.v2",
            "source_sha256": certification_evidence_sha256(certification_payload),
            "source_entry_count": 0,
            "denied_page_count": 0,
            "applied_denied_page_count": 0,
            "out_of_scope_denied_page_count": 0,
        },
    }), encoding="utf-8")
    observations.write_text(json.dumps({"status": "COMPLETE", "observations": [{"page_id": "p1"}]}), encoding="utf-8")
    return root, catalog, observations


def test_runtime_health_uses_declared_root_and_redacts_locators(tmp_path, monkeypatch):
    root, catalog, observations = _private_root(tmp_path)
    monkeypatch.delenv("PPTX_STUDIO_PRIVATE_ROOT", raising=False)
    monkeypatch.delenv("PPTX_STUDIO_SKILL_ROOT", raising=False)

    assert resolve_private_library_root(explicit=root) == root.resolve()
    report = runtime_health(explicit=root)

    assert report == {
        "schema_version": "pptx-studio-runtime-health.v1",
        "status": "PASS",
        "catalog_sha256": hashlib.sha256(catalog.read_bytes()).hexdigest(),
        "observations_sha256": hashlib.sha256(observations.read_bytes()).hexdigest(),
        "certification_sha256": certification_evidence_sha256({
            "schema_version": "gaojie-certified-core.v2",
            "denied_page_count": 0,
            "denied_pages": [],
        }),
        "catalog_page_count": 1,
        "observation_count": 1,
        "catalog_denied_page_count": 0,
        "source_package_count": 1,
        "required_artifacts": {
            "catalog": True,
            "observations": True,
            "certification": True,
            "source_root": True,
        },
    }
    assert str(root) not in json.dumps(report)


def test_runtime_uses_declared_skill_root_before_coinstalled_tree(tmp_path, monkeypatch):
    root, _, _ = _private_root(tmp_path)
    skill_root = tmp_path / "skill-root"
    skill_root.mkdir()
    (skill_root / ".private").symlink_to(root, target_is_directory=True)
    monkeypatch.delenv("PPTX_STUDIO_PRIVATE_ROOT", raising=False)
    monkeypatch.setenv("PPTX_STUDIO_SKILL_ROOT", str(skill_root))

    assert resolve_private_library_root() == root.resolve()


def test_runtime_rejects_catalog_when_certification_ledger_drifted(tmp_path):
    root, _, _ = _private_root(tmp_path)
    certification = root / "intelligence/gaojie/certified-core.json"
    certification.write_text(json.dumps({
        "schema_version": "gaojie-certified-core.v2",
        "denied_page_count": 1,
        "denied_pages": [{"page_id": "changed"}],
    }), encoding="utf-8")

    import pytest

    with pytest.raises(RuntimeError, match="PPTX_STUDIO_PRIVATE_LIBRARY_INVALID"):
        runtime_health(explicit=root)
