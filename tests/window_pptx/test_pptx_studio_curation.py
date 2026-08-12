from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.curation import (  # noqa: E402
    ACTIVE_GAOJIE_CATEGORIES,
    CurationError,
    INACTIVE_GAOJIE_CATEGORIES,
    apply_curation,
    plan_curation,
    recover_curation,
    verify_curation,
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sources(tmp_path: Path) -> tuple[Path, Path]:
    sources = tmp_path / "private" / "sources" / "gaojie"
    archive = tmp_path / "private" / "archive" / "pptx-studio" / "v7"
    active = ACTIVE_GAOJIE_CATEGORIES[0]
    inactive = "055-图文排版"
    for category in ACTIVE_GAOJIE_CATEGORIES:
        (sources / category).mkdir(parents=True, exist_ok=True)
    for category in INACTIVE_GAOJIE_CATEGORIES:
        (sources / category).mkdir(parents=True, exist_ok=True)
    (sources / active / "nested").mkdir(parents=True)
    (sources / active / "nested" / "active.pptx").write_bytes(b"active")
    (sources / inactive / "nested").mkdir(parents=True)
    (sources / inactive / "nested" / "inactive.pptx").write_bytes(b"inactive")
    return sources, archive


def test_plan_is_closed_partition_and_has_recovery_per_package(tmp_path: Path) -> None:
    sources, archive = _sources(tmp_path)

    plan = plan_curation(sources, archive_root=archive)

    assert plan["status"] == "PLANNED"
    assert plan["active_categories"] == list(ACTIVE_GAOJIE_CATEGORIES)
    assert plan["inactive_categories"] == list(INACTIVE_GAOJIE_CATEGORIES)
    assert plan["inactive_packages"] == [
        {
            "archive_locator": "055-图文排版/nested/inactive.pptx",
            "opaque_id": "pkg_" + _sha(b"inactive")[:24],
            "original_locator": "055-图文排版/nested/inactive.pptx",
            "post_move_sha256": None,
            "recovery": {
                "from_archive_locator": "055-图文排版/nested/inactive.pptx",
                "operation": "restore_package_tree",
                "to_source_locator": "055-图文排版/nested/inactive.pptx",
            },
            "source_sha256": _sha(b"inactive"),
        }
    ]
    assert plan["source_tree_sha256"]
    assert plan["active_tree_sha256"]
    assert plan["inactive_tree_sha256"]


def test_plan_rejects_unknown_or_missing_active_categories(tmp_path: Path) -> None:
    sources, archive = _sources(tmp_path)
    (sources / "unknown").mkdir()

    with pytest.raises(CurationError, match="UNKNOWN_CATEGORY"):
        plan_curation(sources, archive_root=archive)

    (sources / "unknown").rmdir()
    with pytest.raises(CurationError, match="ACTIVE_CATEGORY_MISSING"):
        plan_curation(
            sources,
            archive_root=archive,
            active_categories=(ACTIVE_GAOJIE_CATEGORIES[0], "missing"),
        )


def test_apply_verify_and_recover_are_hash_guarded(tmp_path: Path) -> None:
    sources, archive = _sources(tmp_path)
    plan = plan_curation(
        sources,
        archive_root=archive,
    )

    applied = apply_curation(plan, sources, archive_root=archive)
    assert applied["status"] == "APPLIED"
    assert (archive / "055-图文排版" / "nested" / "inactive.pptx").is_file()
    assert not (sources / "055-图文排版").exists()
    assert verify_curation(applied, sources, archive_root=archive)["status"] == "PASS"

    dry_run = recover_curation(applied, sources, archive_root=archive)
    assert dry_run["status"] == "RECOVERY_PLANNED"
    recovered = recover_curation(applied, sources, archive_root=archive, apply=True)
    assert recovered["status"] == "RECOVERED"
    assert (sources / "055-图文排版" / "nested" / "inactive.pptx").read_bytes() == b"inactive"
    assert not (archive / "055-图文排版").exists()


def test_apply_fails_closed_when_source_hash_changes_after_plan(tmp_path: Path) -> None:
    sources, archive = _sources(tmp_path)
    plan = plan_curation(
        sources,
        archive_root=archive,
    )
    target = sources / "055-图文排版" / "nested" / "inactive.pptx"
    target.write_bytes(b"changed")

    with pytest.raises(CurationError, match="SOURCE_HASH_MISMATCH"):
        apply_curation(plan, sources, archive_root=archive)
    assert target.is_file()
    assert not archive.exists()
