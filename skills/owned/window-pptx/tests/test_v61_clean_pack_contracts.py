from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = SKILL_ROOT / "schemas"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_window_pptx_v61_clean_pack import (  # noqa: E402
    bundle_fingerprint,
    main,
    tree_fingerprint,
    validate_requirement_pack,
    validate_run_fingerprint,
)


def _json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _record(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    return {
        "path": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": path.stat().st_size,
    }


def _write_pre_manifest(root: Path) -> Path:
    relative = "PRE-RUN-MANIFEST.json"
    entries: list[dict[str, object]] = []
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file() and not item.is_symlink()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        if path.relative_to(root).as_posix() == relative:
            continue
        entries.append(
            {
                **_record(root, path.relative_to(root).as_posix()),
                "type": "regular_file",
            }
        )
    manifest = {
        "schema_version": "1.0",
        "manifest_id": "fixture-pre-run",
        "generated_at": "2026-08-08T23:59:00+08:00",
        "root": ".",
        "recursive": True,
        "exclusion": {"path": relative, "reason": "self hash is external"},
        "constraints": {
            "pptx_count": 0,
            "template_preview_count": 0,
            "private_byte_count": 0,
            "history_output_count": 0,
            "repository_marker_count": 0,
            "symlink_count": 0,
        },
        "entry_count": len(entries),
        "total_size": sum(int(entry["size"]) for entry in entries),
        "entries": entries,
    }
    path = root / relative
    _json(path, manifest)
    return path


def _make_clean_pack(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "clean"
    root.mkdir()
    (root / "REQUEST.md").write_text("# 客户需求\n完整年度工作汇报。\n", encoding="utf-8")
    lock_sha = "a" * 64
    _json(root / "project-brief-pack.v1.json", {"schema_version": "1.0", "lock_sha256": lock_sha})
    _json(root / "fact-store.v1.json", {"schema_version": "1.0", "facts": [{"id": "fact-1"}]})
    _json(root / "connective-copy.v1.json", {"schema_version": "1.0", "entries": []})
    data_path = root / "data" / "revenue.csv"
    data_path.parent.mkdir()
    data_path.write_text("year,value\n2025,100\n", encoding="utf-8")
    _json(
        root / "data-manifest.v1.json",
        {
            "schema_version": "1.0",
            "files": [
                {
                    "id": "revenue",
                    **_record(root, "data/revenue.csv"),
                    "media_type": "text/csv",
                }
            ],
        },
    )
    asset_path = root / "assets" / "hospital-mark.png"
    asset_path.parent.mkdir()
    asset_path.write_bytes(b"client-owned-image-bytes")
    _json(
        root / "asset-manifest.v1.json",
        {
            "schema_version": "1.0",
            "bindings": {
                "hospital-mark": {
                    "path": "assets/hospital-mark.png",
                    "sha256": hashlib.sha256(asset_path.read_bytes()).hexdigest(),
                    "record": {
                        "id": "hospital-mark",
                        "kind": "logo",
                        "quality": 1.0,
                        "source": "client",
                        "license": "client-owned",
                        "retrieved_at": "2026-08-08",
                        "size": asset_path.stat().st_size,
                    },
                }
            },
        },
    )
    authorities = {
        "project_brief": {
            **_record(root, "project-brief-pack.v1.json"),
            "lock_sha256": lock_sha,
        },
        "request": _record(root, "REQUEST.md"),
        "fact_store": _record(root, "fact-store.v1.json"),
        "asset_manifest": _record(root, "asset-manifest.v1.json"),
        "connective_copy": _record(root, "connective-copy.v1.json"),
        "data_manifest": _record(root, "data-manifest.v1.json"),
    }
    requirement_name = "annual-work-report.requirement-pack.v1.json"
    _json(
        root / requirement_name,
        {
            "schema_version": "1.0",
            "pack_id": "annual-work-report-hospital-finance-2025-v61",
            "state": "Locked",
            "scenario": {
                "type": "annual-work-report",
                "language": "zh-CN",
                "slide_count": 15,
                "aspect_ratio": "16:9",
                "subject": "某市中心医院财务运营部",
                "data_classification": "synthetic-acceptance-data",
            },
            "authorities": authorities,
            "generation_contract": {
                "model": "gpt-5.6-terra",
                "reasoning_effort": "medium",
                "physical_template_lineage_required": 15,
                "distinct_page_ids_required": 15,
                "native_editable_required": True,
                "generated_visual_fallback_allowed": False,
                "author_terminal_state": "CANDIDATE_READY_FOR_BLIND_REVIEW",
            },
            "input_policy": {
                "reference_pptx_allowed": False,
                "template_preview_allowed": False,
                "private_template_bytes_allowed": False,
                "historical_output_allowed": False,
                "symlinks_allowed": False,
                "network_assets_allowed": False,
            },
        },
    )
    _write_pre_manifest(root)
    return root, requirement_name


def _build_run_fingerprint(
    tmp_path: Path,
    root: Path,
    requirement_name: str,
) -> tuple[Path, dict[str, object]]:
    pre_report = validate_requirement_pack(root, requirement_name)
    assert pre_report["status"] == "PASS", pre_report
    installed = (tmp_path / "installed-skill").resolve()
    installed.mkdir()
    (installed / "SKILL.md").write_text("# Installed fixture\n", encoding="utf-8")
    (installed / "scripts").mkdir()
    (installed / "scripts" / "entry.py").write_text("VALUE = 1\n", encoding="utf-8")
    installed_digest = tree_fingerprint(installed)
    output = root / "delivery" / "annual-report.pptx"
    output.parent.mkdir()
    output.write_bytes(b"PK\x03\x04physical-pptx-fixture")
    report = root / "evidence" / "physical-assembly-report.json"
    output_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    _json(report, {"schema_version": "1.0", "status": "pass", "output_sha256": output_sha})
    harness = tmp_path / "harness"
    harness.mkdir()
    post = harness / "post-run-manifest.v1.json"
    _json(post, {"schema_version": "1.0", "status": "captured"})
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "run_id": "hospital-finance-annual-2025-v61-run-1",
        "command": {
            "argv": [
                "codex",
                "exec",
                "--dangerously-bypass-approvals-and-sandbox",
                "--skip-git-repo-check",
                "-c",
                'model_provider="OpenAI"',
                "-c",
                'model_reasoning_effort="medium"',
                "--cd",
                str(root.resolve()),
                "-m",
                "gpt-5.6-terra",
                "--json",
                "-",
            ],
            "cwd": str(root.resolve()),
            "model_provider": "OpenAI",
            "model": "gpt-5.6-terra",
            "reasoning_effort": "medium",
        },
        "installed_skill": {"path": str(installed), **installed_digest},
        "requirements": pre_report["requirements"],
        "assets": pre_report["assets"],
        "private_library": {
            "resolution_source": "config-private-root",
            "private_root_sha256": "b" * 64,
            "library_index_sha256": "c" * 64,
        },
        "manifests": {
            "pre_run": _record(root, "PRE-RUN-MANIFEST.json"),
            "post_run": {
                "path": str(post.resolve()),
                "sha256": hashlib.sha256(post.read_bytes()).hexdigest(),
                "size": post.stat().st_size,
            },
        },
        "artifacts": {
            "output_pptx": _record(root, "delivery/annual-report.pptx"),
            "physical_assembly_report": _record(root, "evidence/physical-assembly-report.json"),
        },
        "exit": {"code": 0, "status": "success"},
    }
    fingerprint = harness / "physical-assembly-run-fingerprint.v1.json"
    _json(fingerprint, payload)
    return fingerprint, payload


def test_both_contract_schemas_are_valid_draft_2020_12() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    for name in (
        "annual-work-report-requirement-pack.v1.schema.json",
        "physical-assembly-run-fingerprint.v1.schema.json",
    ):
        schema = json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)


def test_clean_requirement_pack_passes_and_binds_requirement_and_asset_bytes(tmp_path: Path) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    report = validate_requirement_pack(root, requirement_name)
    assert report["status"] == "PASS", report
    assert report["requirements"]["file_count"] == 7
    assert report["assets"]["file_count"] == 2
    assert report["requirements"] == bundle_fingerprint(report["requirements"]["files"])
    assert report["assets"] == bundle_fingerprint(report["assets"]["files"])


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("sha", "BOUND_SHA256_MISMATCH"),
        ("size", "BOUND_SIZE_MISMATCH"),
        ("escape", "SCHEMA_VALIDATION_FAILED"),
    ],
)
def test_requirement_authority_drift_and_escape_fail_closed(
    tmp_path: Path,
    mutation: str,
    expected_code: str,
) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    requirement_path = root / requirement_name
    payload = json.loads(requirement_path.read_text(encoding="utf-8"))
    if mutation == "sha":
        payload["authorities"]["request"]["sha256"] = "f" * 64
    elif mutation == "size":
        payload["authorities"]["request"]["size"] += 1
    else:
        payload["authorities"]["request"]["path"] = "../outside.md"
    _json(requirement_path, payload)
    report = validate_requirement_pack(root, requirement_name)
    assert report["status"] == "FAIL"
    assert expected_code in {issue["code"] for issue in report["issues"]}


@pytest.mark.parametrize(
    ("relative", "expected_code"),
    [
        ("reference.pptx", "PRESENTATION_INPUT_FORBIDDEN"),
        ("template-previews/page-1.png", "TEMPLATE_PREVIEW_FORBIDDEN"),
        ("historical-output/old.pdf", "HISTORICAL_OUTPUT_FORBIDDEN"),
        (".git/config", "GIT_MARKER_FORBIDDEN"),
        (".private/library.json", "PRIVATE_MARKER_FORBIDDEN"),
    ],
)
def test_clean_room_rejects_presentation_preview_history_git_and_private_markers(
    tmp_path: Path,
    relative: str,
    expected_code: str,
) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"contamination")
    report = validate_requirement_pack(root, requirement_name)
    assert report["status"] == "FAIL"
    assert expected_code in {issue["code"] for issue in report["issues"]}


def test_clean_room_rejects_symlinks(tmp_path: Path) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    target = root / "REQUEST.md"
    (root / "linked-request.md").symlink_to(target)
    report = validate_requirement_pack(root, requirement_name)
    assert report["status"] == "FAIL"
    assert "SYMLINK_FORBIDDEN" in {issue["code"] for issue in report["issues"]}


def test_pre_run_manifest_must_exactly_cover_clean_room(tmp_path: Path) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    (root / "unlisted.txt").write_text("late input\n", encoding="utf-8")
    report = validate_requirement_pack(root, requirement_name)
    assert report["status"] == "FAIL"
    assert "PRE_MANIFEST_SNAPSHOT_MISMATCH" in {
        issue["code"] for issue in report["issues"]
    }


def test_exact_successful_run_fingerprint_passes(tmp_path: Path) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, _ = _build_run_fingerprint(tmp_path, root, requirement_name)
    report = validate_run_fingerprint(root, requirement_name, fingerprint)
    assert report["status"] == "PASS", report
    assert report["verified_artifacts"]["output_pptx"]["sha256"]
    assert report["verified_artifacts"]["physical_assembly_report"]["sha256"]


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("argv", "SCHEMA_VALIDATION_FAILED"),
        ("skill", "INSTALLED_SKILL_DIGEST_MISMATCH"),
        ("requirements", "FILE_BUNDLE_SELF_MISMATCH"),
        ("output", "ARTIFACT_SHA256_MISMATCH"),
        ("exit", "CODEX_RUN_NOT_SUCCESSFUL"),
    ],
)
def test_run_fingerprint_drift_is_non_pass(
    tmp_path: Path,
    mutation: str,
    expected_code: str,
) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, original = _build_run_fingerprint(tmp_path, root, requirement_name)
    payload = copy.deepcopy(original)
    if mutation == "argv":
        payload["command"]["argv"][11] = "another-model"
    elif mutation == "skill":
        payload["installed_skill"]["sha256"] = "d" * 64
    elif mutation == "requirements":
        payload["requirements"]["sha256"] = "e" * 64
    elif mutation == "output":
        payload["artifacts"]["output_pptx"]["sha256"] = "f" * 64
    else:
        payload["exit"] = {"code": 1, "status": "failed"}
    _json(fingerprint, payload)
    report = validate_run_fingerprint(root, requirement_name, fingerprint)
    assert report["status"] == "FAIL"
    codes = {issue["code"] for issue in report["issues"]}
    assert expected_code in codes or (
        mutation == "output" and "BOUND_SHA256_MISMATCH" in codes
    )


def test_cli_prints_one_machine_readable_json_document_and_nonzero_on_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    assert main(["pack", "--root", str(root), "--requirement-pack", requirement_name]) == 0
    stdout = capsys.readouterr().out
    assert json.loads(stdout)["status"] == "PASS"
    (root / "bad.pptx").write_bytes(b"bad")
    assert main(["pack", "--root", str(root), "--requirement-pack", requirement_name]) == 1
    stdout = capsys.readouterr().out
    assert json.loads(stdout)["status"] == "FAIL"
