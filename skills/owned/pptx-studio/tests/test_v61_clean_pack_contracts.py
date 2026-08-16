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

import validate_window_pptx_v61_clean_pack as clean_validator  # noqa: E402
import run_window_pptx_v61_codex_acceptance as acceptance_controller  # noqa: E402

from validate_window_pptx_v61_clean_pack import (  # noqa: E402
    bundle_fingerprint,
    main,
    tree_fingerprint,
    validate_requirement_pack,
    validate_run_fingerprint,
)
from window_pptx.v61_runtime_identity import (  # noqa: E402
    build_runtime_identity_payload,
    write_runtime_identity_manifest,
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


EVIDENCE_OUTPUTS = (
    "evidence/direction-decision.v1.json",
    "evidence/narrative-plan.v1.json",
    "evidence/assembly-plan.v1.json",
    "evidence/template-query-results.v1.json",
    "evidence/physical-assembly-report.v1.json",
    "evidence/rule-qa.v1.json",
    "evidence/fingerprint-bundle.v1.json",
    "evidence/run-summary.md",
)


def _write_post_manifest(root: Path, path: Path) -> None:
    entries = [
        _record(root, item.relative_to(root).as_posix())
        for item in sorted(
            (candidate for candidate in root.rglob("*") if candidate.is_file()),
            key=lambda candidate: candidate.relative_to(root).as_posix(),
        )
    ]
    fingerprint = bundle_fingerprint(entries)
    _json(
        path,
        {
            "schema_version": "1.0",
            "manifest_id": "fixture-post-run",
            "project_root": str(root.resolve()),
            "recursive": True,
            "digest_algorithm": fingerprint["digest_algorithm"],
            "inventory_sha256": fingerprint["sha256"],
            "entry_count": fingerprint["file_count"],
            "total_size": fingerprint["total_size"],
            "entries": entries,
        },
    )


def _make_clean_pack(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "clean"
    root.mkdir()
    (root / "REQUEST.md").write_text("# 客户需求\n完整年度工作汇报。\n", encoding="utf-8")
    (root / "PRODUCTION_PROMPT.md").write_text(
        "Use the installed Window-PPTX Skill and run the locked profile job.\n",
        encoding="utf-8",
    )
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
    private_root = tmp_path / "private-library"
    private_root.mkdir()
    _, library_sha = _minimal_private_index(private_root)
    installed = (tmp_path / "installed-skill").resolve()
    installed.mkdir()
    (installed / "SKILL.md").write_text("# Installed fixture\n", encoding="utf-8")
    (installed / "scripts").mkdir()
    (installed / "scripts" / "run_window_pptx_v61_codex_acceptance.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )
    installed_digest = tree_fingerprint(installed)
    codex_executable = Path(sys.executable).resolve()
    runtime_payload = build_runtime_identity_payload(
        installed_skill_root=installed,
        expected_installed_skill_sha256=str(installed_digest["sha256"]),
        controller_interpreter=Path(sys.executable).resolve(),
        codex_native_executable=codex_executable,
    )
    runtime_path = tmp_path / "runtime-identity.v1.json"
    runtime_record = write_runtime_identity_manifest(runtime_path, runtime_payload)
    native_record = runtime_payload["codex"]["native_executable"]
    codex_record = {
        "requested_path": str(codex_executable.resolve()),
        "resolved_path": str(codex_executable.resolve()),
        "sha256": native_record["sha256"],
        "size": native_record["size"],
        "version": native_record["version"],
    }
    output = root / "output" / "hospital-finance-annual-2025.pptx"
    output.parent.mkdir()
    output.write_bytes(b"PK\x03\x04physical-pptx-fixture")
    for relative in EVIDENCE_OUTPUTS:
        candidate = root / relative
        candidate.parent.mkdir(parents=True, exist_ok=True)
        if candidate.suffix == ".md":
            candidate.write_text("# Candidate run\n", encoding="utf-8")
        else:
            _json(candidate, {"schema_version": "1.0"})
    report = root / "evidence" / "physical-assembly-report.v1.json"
    output_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    _json(
        report,
        {
            "schema_version": "1.0",
            "status": "pass",
            "output_sha256": output_sha,
            "selection_authority": {
                "library_index_sha256": library_sha,
            },
        },
    )
    _json(
        root / "evidence" / "template-query-results.v1.json",
        {
            "schema_version": "page-template-query-bundle.v1",
            "library_index_sha256": library_sha,
            "library_resolution_source": "config-private-root",
        },
    )
    _json(
        root / "evidence" / "fingerprint-bundle.v1.json",
        {
            "schema_version": "1.0",
            "fingerprints": [{"library_index_sha256": library_sha}],
            "components": {
                "private_library_resolution_source": "config-private-root",
            },
        },
    )
    rule_qa = root / "evidence" / "rule-qa.v1.json"
    _json(
        rule_qa,
        {
            "schema_version": "1.1",
            "status": "pass",
            "output_path": str(output.resolve()),
            "output_sha256": output_sha,
            "output_size_bytes": output.stat().st_size,
            "output_identity_status": "verified-stable",
            "path_policy": {
                "input_path_kind": "absolute",
                "relative_input_base": None,
                "stored_path_format": "canonical-absolute",
                "canonicalization": "expanduser+resolve(strict=false)",
                "relative_input_resolution": "invocation-working-directory",
            },
            "slide_count": 1,
            "checked_rules": [
                "output-identity",
                "zip-open",
                "slide-count",
                "placeholder-residue",
                "named-brand-residue",
                "source-template-residue",
                "text-bounds",
                "tiny-text",
                "style-lineage",
            ],
            "blocking_findings": [],
            "warnings": [],
        },
    )
    harness = tmp_path / "harness"
    harness.mkdir()
    events = harness / "codex-events.jsonl"
    events.write_text('{"type":"result","status":"completed"}\n', encoding="utf-8")
    stderr = harness / "codex-stderr.log"
    stderr.write_bytes(b"")
    post = harness / "post-run-manifest.v1.json"
    _write_post_manifest(root, post)
    post_payload = json.loads(post.read_text(encoding="utf-8"))
    settlement_samples = [
        {
            "ordinal": ordinal,
            "offset_ms": (ordinal - 1) * 100,
            "digest_algorithm": post_payload["digest_algorithm"],
            "inventory_sha256": post_payload["inventory_sha256"],
            "entry_count": post_payload["entry_count"],
            "total_size": post_payload["total_size"],
        }
        for ordinal in range(1, 4)
    ]
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
                'model_provider="openai"',
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
            "stdin": _record(root, "PRODUCTION_PROMPT.md"),
            "executable": codex_record,
            "model_provider": "openai",
            "model": "gpt-5.6-terra",
            "reasoning_effort": "medium",
        },
        "installed_skill": {
            "path": str(installed),
            "expected_sha256": installed_digest["sha256"],
            **installed_digest,
        },
        "runtime_identity": {
            "manifest": runtime_record,
            "expected_sha256": runtime_record["sha256"],
            "launch_mode": "native-codex-direct",
        },
        "requirements": pre_report["requirements"],
        "assets": pre_report["assets"],
        "private_library": {
            "resolution_source": "config-private-root",
            "private_root_sha256": "d" * 64,
            "library_index_sha256": library_sha,
        },
        "process_evidence": {
            "events_jsonl": {
                "path": str(events.resolve()),
                "sha256": hashlib.sha256(events.read_bytes()).hexdigest(),
                "size": events.stat().st_size,
            },
            "stderr": {
                "path": str(stderr.resolve()),
                "sha256": hashlib.sha256(stderr.read_bytes()).hexdigest(),
                "size": stderr.stat().st_size,
            },
            "settlement": {
                "process_group": {
                    "isolation": "new-posix-session",
                    "leader_pid": 2_000_000_000,
                    "process_group_id": 2_000_000_000,
                    "cleanup_attempted": False,
                    "signals_sent": [],
                    "absence_probe_count": 1,
                    "residue_status": "absent",
                },
                "inventory": {
                    "policy": "separated-stable-inventory-v1",
                    "stable": True,
                    "minimum_sample_count": 3,
                    "minimum_window_ms": 200,
                    "sample_interval_ms": 100,
                    "sample_count": 3,
                    "window_ms": 200,
                    "samples": settlement_samples,
                },
            },
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
            "output_pptx": _record(root, "output/hospital-finance-annual-2025.pptx"),
            "physical_assembly_report": _record(root, "evidence/physical-assembly-report.v1.json"),
            "rule_qa_report": _record(root, "evidence/rule-qa.v1.json"),
            "evidence_outputs": [_record(root, relative) for relative in EVIDENCE_OUTPUTS],
        },
        "exit": {"code": 0, "status": "success"},
    }
    fingerprint = harness / "physical-assembly-run-fingerprint.v1.json"
    _json(fingerprint, payload)
    return fingerprint, payload


def test_clean_room_contract_schemas_are_valid_draft_2020_12() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    for name in (
        "annual-work-report-requirement-pack.v1.schema.json",
        "physical-assembly-run-fingerprint.v1.schema.json",
        "physical-assembly-post-run-manifest.v1.schema.json",
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


def test_exact_successful_run_fingerprint_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, _ = _build_run_fingerprint(tmp_path, root, requirement_name)
    output = root / "output" / "hospital-finance-annual-2025.pptx"
    monkeypatch.setattr(
        clean_validator,
        "validate_physical_report",
        lambda _report, _root: {
            "status": "pass",
            "issue_count": 0,
            "issues": [],
            "observed": {
                "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "output_size_bytes": output.stat().st_size,
                "pptx_slide_count": 1,
            },
        },
    )
    monkeypatch.setattr(
        clean_validator,
        "_validate_evidence_schema",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        clean_validator,
        "_validate_run_summary",
        lambda *_args, **_kwargs: None,
    )
    report = validate_run_fingerprint(
        root, requirement_name, fingerprint, private_root=tmp_path / "private-library"
    )
    assert report["status"] == "PASS", report
    assert report["verified_artifacts"]["output_pptx"]["sha256"]
    assert report["verified_artifacts"]["physical_assembly_report"]["sha256"]
    assert report["verified_artifacts"]["rule_qa_report"]["sha256"]


def test_fake_pptx_and_minimal_physical_report_fail_strong_validation(
    tmp_path: Path,
) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, _ = _build_run_fingerprint(tmp_path, root, requirement_name)
    report = validate_run_fingerprint(
        root, requirement_name, fingerprint, private_root=tmp_path / "private-library"
    )
    assert report["status"] == "FAIL"
    assert "PHYSICAL_REPORT_INDEPENDENT_VALIDATION_FAILED" in {
        issue["code"] for issue in report["issues"]
    }


def test_empty_post_run_manifest_fails(tmp_path: Path) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, payload = _build_run_fingerprint(tmp_path, root, requirement_name)
    post = Path(payload["manifests"]["post_run"]["path"])
    _json(
        post,
        {
            "schema_version": "1.0",
            "manifest_id": "fixture-post-run",
            "project_root": str(root.resolve()),
            "recursive": True,
            "digest_algorithm": "canonical-file-records-sha256-v1",
            "inventory_sha256": hashlib.sha256(b"[]").hexdigest(),
            "entry_count": 0,
            "total_size": 0,
            "entries": [],
        },
    )
    payload["manifests"]["post_run"] = {
        "path": str(post.resolve()),
        "sha256": hashlib.sha256(post.read_bytes()).hexdigest(),
        "size": post.stat().st_size,
    }
    _json(fingerprint, payload)
    report = validate_run_fingerprint(
        root, requirement_name, fingerprint, private_root=tmp_path / "private-library"
    )
    assert report["status"] == "FAIL"
    assert {
        "SCHEMA_VALIDATION_FAILED",
        "POST_MANIFEST_SNAPSHOT_MISMATCH",
    } & {issue["code"] for issue in report["issues"]}


def test_extra_pptx_is_rejected_even_when_not_declared(tmp_path: Path) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, _ = _build_run_fingerprint(tmp_path, root, requirement_name)
    (root / "output" / "extra.pptx").write_bytes(b"extra")
    report = validate_run_fingerprint(
        root, requirement_name, fingerprint, private_root=tmp_path / "private-library"
    )
    assert report["status"] == "FAIL"
    assert "POST_RUN_PPTX_SET_MISMATCH" in {
        issue["code"] for issue in report["issues"]
    }


def test_missing_rule_qa_report_fails(tmp_path: Path) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, _ = _build_run_fingerprint(tmp_path, root, requirement_name)
    (root / "evidence" / "rule-qa.v1.json").unlink()
    report = validate_run_fingerprint(
        root, requirement_name, fingerprint, private_root=tmp_path / "private-library"
    )
    assert report["status"] == "FAIL"
    assert {
        "BOUND_FILE_MISSING",
        "POST_MANIFEST_SNAPSHOT_MISMATCH",
    } & {issue["code"] for issue in report["issues"]}


def test_run_fingerprint_binds_exact_prompt_bytes(tmp_path: Path) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, payload = _build_run_fingerprint(tmp_path, root, requirement_name)
    payload["command"]["stdin"]["sha256"] = "f" * 64
    _json(fingerprint, payload)
    report = validate_run_fingerprint(
        root, requirement_name, fingerprint, private_root=tmp_path / "private-library"
    )
    assert report["status"] == "FAIL"
    assert "BOUND_SHA256_MISMATCH" in {issue["code"] for issue in report["issues"]}


def test_private_library_is_cross_bound_to_project_evidence(tmp_path: Path) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, payload = _build_run_fingerprint(tmp_path, root, requirement_name)
    payload["private_library"]["library_index_sha256"] = "d" * 64
    _json(fingerprint, payload)
    report = validate_run_fingerprint(
        root, requirement_name, fingerprint, private_root=tmp_path / "private-library"
    )
    assert report["status"] == "FAIL"
    assert "PRIVATE_LIBRARY_CROSS_BIND_MISMATCH" in {
        issue["code"] for issue in report["issues"]
    }


@pytest.mark.parametrize(
    ("relative", "expected_code"),
    [
        ("undeclared.txt", "POST_RUN_OUTPUT_SET_MISMATCH"),
        (".private/secret.bin", "PRIVATE_MARKER_FORBIDDEN"),
        ("template-previews/page.png", "TEMPLATE_PREVIEW_FORBIDDEN"),
        ("references/source.png", "REFERENCE_MATERIAL_FORBIDDEN"),
        ("historical-output/old.json", "HISTORICAL_OUTPUT_FORBIDDEN"),
    ],
)
def test_post_run_rejects_undeclared_and_forbidden_material(
    tmp_path: Path,
    relative: str,
    expected_code: str,
) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, _ = _build_run_fingerprint(tmp_path, root, requirement_name)
    candidate = root / relative
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_bytes(b"forbidden")
    report = validate_run_fingerprint(
        root, requirement_name, fingerprint, private_root=tmp_path / "private-library"
    )
    assert report["status"] == "FAIL"
    assert expected_code in {issue["code"] for issue in report["issues"]}


def test_post_run_rejects_symlink(tmp_path: Path) -> None:
    root, requirement_name = _make_clean_pack(tmp_path)
    fingerprint, _ = _build_run_fingerprint(tmp_path, root, requirement_name)
    (root / "linked-output").symlink_to(root / "REQUEST.md")
    report = validate_run_fingerprint(
        root, requirement_name, fingerprint, private_root=tmp_path / "private-library"
    )
    assert report["status"] == "FAIL"
    assert "SYMLINK_FORBIDDEN" in {issue["code"] for issue in report["issues"]}


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
    report = validate_run_fingerprint(
        root, requirement_name, fingerprint, private_root=tmp_path / "private-library"
    )
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


def _minimal_private_index(private_root: Path) -> tuple[Path, str]:
    library = private_root / "v61" / "reference-work-summary-library-v4.json"
    package_sha = "d" * 64
    _json(
        library,
        {
            "schema_version": "4.0",
            "library_id": "fixture-reference-work-summary",
            "compiled_at": "2026-08-08T00:00:00Z",
            "source_core_schema": "user-certified-reference-deck.v1",
            "private_root_sha256": package_sha,
            "source_package_count": 1,
            "source_package_index": {
                package_sha: {
                    "page_count": 1,
                    "source_sha256": package_sha,
                    "source_size_bytes": 1,
                }
            },
            "page_template_count": 0,
            "role_index": {},
            "style_cluster_index": {},
            "deck_family_index": {},
            "category_index": {},
            "page_templates": [],
            "scoring": {
                "role": 0.3,
                "capacity": 0.25,
                "semantic": 0.2,
                "style": 0.15,
                "editability": 0.1,
            },
            "dominant_style_cluster_id": "reference-work-summary",
            "compatible_style_cluster_ids": ["reference-work-summary"],
        },
    )
    return library, hashlib.sha256(library.read_bytes()).hexdigest()


def _installed_skill(tmp_path: Path, library_sha: str) -> Path:
    installed = tmp_path / "codex-home" / "skills" / "pptx-studio"
    installed.mkdir(parents=True)
    (installed / "SKILL.md").write_text("# Installed fixture\n", encoding="utf-8")
    controller = installed / "scripts" / "run_window_pptx_v61_codex_acceptance.py"
    controller.parent.mkdir(parents=True)
    controller.write_text("VALUE = 1\n", encoding="utf-8")
    _json(
        installed
        / "registries"
        / "v61-binding-profiles"
        / "phase49-work-report-15.binding-profile.v1.json",
        {
            "schema_version": "1.0",
            "profile_id": "phase49-work-report-15",
            "library_index_sha256": library_sha,
        },
    )
    return installed


def _fake_codex(tmp_path: Path) -> tuple[Path, Path]:
    executable = tmp_path / "fake-codex"
    capture = tmp_path / "fake-codex-capture.json"
    executable.write_text(
        """#!/usr/bin/env python3
import hashlib
import json
import os
import pathlib
import sys

args = sys.argv[1:]
if args == ['--version']:
    print('codex-cli test-double-1.0')
    raise SystemExit(0)
project = pathlib.Path(args[args.index('--cd') + 1])
prompt = sys.stdin.read()
capture = pathlib.Path(os.environ['FAKE_CODEX_CAPTURE'])
capture.write_text(json.dumps({'args': args, 'cwd': os.getcwd(), 'prompt': prompt, 'codex_home': os.environ.get('CODEX_HOME')}), encoding='utf-8')
returncode = int(os.environ.get('FAKE_CODEX_EXIT', '0'))
if returncode:
    print(json.dumps({'type': 'failed', 'code': returncode}))
    raise SystemExit(returncode)
outputs = [
    'output/hospital-finance-annual-2025.pptx',
    'evidence/direction-decision.v1.json',
    'evidence/narrative-plan.v1.json',
    'evidence/assembly-plan.v1.json',
    'evidence/template-query-results.v1.json',
    'evidence/physical-assembly-report.v1.json',
    'evidence/rule-qa.v1.json',
    'evidence/fingerprint-bundle.v1.json',
    'evidence/run-summary.md',
]
for relative in outputs:
    path = project / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == '.pptx':
        path.write_bytes(b'PK\\x03\\x04fixture')
    elif path.suffix == '.md':
        path.write_text('# Candidate\\n', encoding='utf-8')
    else:
        path.write_text(json.dumps({'schema_version': '1.0'}), encoding='utf-8')
output = project / 'output/hospital-finance-annual-2025.pptx'
output_sha = hashlib.sha256(output.read_bytes()).hexdigest()
library = pathlib.Path(os.environ['WINDOW_PPTX_PRIVATE_ROOT']) / 'v61/reference-work-summary-library-v4.json'
library_sha = hashlib.sha256(library.read_bytes()).hexdigest()
(project / 'evidence/template-query-results.v1.json').write_text(json.dumps({
    'schema_version': 'page-template-query-bundle.v1',
    'library_index_sha256': library_sha,
    'library_resolution_source': 'environment-private-root',
}), encoding='utf-8')
(project / 'evidence/physical-assembly-report.v1.json').write_text(json.dumps({
    'schema_version': '1.0',
    'status': 'pass',
    'output_sha256': output_sha,
    'selection_authority': {'library_index_sha256': library_sha},
}), encoding='utf-8')
(project / 'evidence/fingerprint-bundle.v1.json').write_text(json.dumps({
    'schema_version': '1.0',
    'fingerprints': [{'library_index_sha256': library_sha}],
    'components': {'private_library_resolution_source': 'environment-private-root'},
}), encoding='utf-8')
(project / 'evidence/rule-qa.v1.json').write_text(json.dumps({
    'schema_version': '1.1',
    'status': 'pass',
    'output_path': str(output.resolve()),
    'output_sha256': output_sha,
    'output_size_bytes': output.stat().st_size,
    'output_identity_status': 'verified-stable',
    'path_policy': {
        'input_path_kind': 'absolute',
        'relative_input_base': None,
        'stored_path_format': 'canonical-absolute',
        'canonicalization': 'expanduser+resolve(strict=false)',
        'relative_input_resolution': 'invocation-working-directory',
    },
    'slide_count': 1,
    'checked_rules': [
        'output-identity', 'zip-open', 'slide-count', 'placeholder-residue',
        'named-brand-residue', 'source-template-residue', 'text-bounds',
        'tiny-text', 'style-lineage',
    ],
    'blocking_findings': [],
    'warnings': [],
}), encoding='utf-8')
mutate = os.environ.get('FAKE_MUTATE_SKILL')
if mutate:
    pathlib.Path(mutate).write_text('# Mutated during run\\n', encoding='utf-8')
if os.environ.get('FAKE_MUTATE_PROMPT'):
    (project / 'PRODUCTION_PROMPT.md').write_text('mutated by child\\n', encoding='utf-8')
    (project / 'PRE-RUN-MANIFEST.json').write_text(json.dumps({'schema_version': '1.0', 'entries': []}), encoding='utf-8')
print(json.dumps({'type': 'result', 'status': 'completed'}))
""",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable, capture


def _controller_fixture(tmp_path: Path) -> tuple[Path, str, Path, Path, Path, Path]:
    root, requirement_name = _make_clean_pack(tmp_path)
    private_root = tmp_path / "private-library"
    private_root.mkdir()
    _, library_sha = _minimal_private_index(private_root)
    installed = _installed_skill(tmp_path, library_sha)
    fake_codex, capture = _fake_codex(tmp_path)
    harness = tmp_path / "external-harness"
    return root, requirement_name, private_root, installed, fake_codex, capture


def _mock_pass_validation(*_args: object, **_kwargs: object) -> dict[str, object]:
    return {"status": "PASS", "issues": []}


def test_acceptance_controller_happy_path_binds_command_prompt_and_external_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, requirement_name, private_root, installed, fake_codex, capture = (
        _controller_fixture(tmp_path)
    )
    harness = tmp_path / "external-harness"
    monkeypatch.setenv("FAKE_CODEX_CAPTURE", str(capture))
    output = root / "output" / "hospital-finance-annual-2025.pptx"
    monkeypatch.setattr(
        clean_validator,
        "validate_physical_report",
        lambda _report, _root: {
            "status": "pass",
            "issue_count": 0,
            "issues": [],
            "observed": {
                "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "output_size_bytes": output.stat().st_size,
                "pptx_slide_count": 1,
            },
        },
    )
    monkeypatch.setattr(
        acceptance_controller,
        "validate_run_fingerprint",
        _mock_pass_validation,
    )
    result = acceptance_controller.run_acceptance(
        project_root=root,
        installed_skill_root=installed,
        private_root=private_root,
        harness_dir=harness,
        requirement_pack=requirement_name,
        codex_bin=str(fake_codex),
        allow_test_codex=True,
    )
    assert result["status"] == "PASS", result
    observed = json.loads(capture.read_text(encoding="utf-8"))
    assert observed["cwd"] == str(root.resolve())
    assert observed["codex_home"] == str((installed.parent.parent).resolve())
    assert observed["prompt"] == (root / "PRODUCTION_PROMPT.md").read_text(encoding="utf-8")
    assert 'model_provider="openai"' in observed["args"]
    fingerprint = json.loads(
        (harness / "physical-assembly-run-fingerprint.v1.json").read_text(encoding="utf-8")
    )
    assert fingerprint["command"]["stdin"] == _record(root, "PRODUCTION_PROMPT.md")
    assert fingerprint["command"]["stdin"]["sha256"] == hashlib.sha256(
        observed["prompt"].encode("utf-8")
    ).hexdigest()
    assert fingerprint["command"]["stdin"]["size"] == len(
        observed["prompt"].encode("utf-8")
    )
    assert fingerprint["command"]["executable"]["resolved_path"] == str(
        fake_codex.resolve()
    )
    assert fingerprint["command"]["executable"]["version"] == (
        "codex-cli test-double-1.0"
    )
    assert fingerprint["installed_skill"]["expected_sha256"] == (
        fingerprint["installed_skill"]["sha256"]
    )
    assert fingerprint["exit"] == {"code": 0, "status": "success"}
    assert (harness / "post-run-manifest.v1.json").is_file()
    assert not (root / "post-run-manifest.v1.json").exists()


def test_acceptance_controller_rejects_unfrozen_installed_skill_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, requirement_name, private_root, installed, fake_codex, capture = (
        _controller_fixture(tmp_path)
    )
    monkeypatch.setenv("FAKE_CODEX_CAPTURE", str(capture))

    with pytest.raises(
        acceptance_controller.AcceptanceControllerError,
        match="INSTALLED_SKILL_EXPECTED_DIGEST_MISMATCH",
    ):
        acceptance_controller.run_acceptance(
            project_root=root,
            installed_skill_root=installed,
            private_root=private_root,
            harness_dir=tmp_path / "external-harness",
            requirement_pack=requirement_name,
            expected_installed_skill_sha256="0" * 64,
            codex_bin=str(fake_codex),
            allow_test_codex=True,
        )
    assert not capture.exists()


def test_acceptance_controller_preflight_prompt_drift_never_spawns_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, requirement_name, private_root, installed, fake_codex, capture = (
        _controller_fixture(tmp_path)
    )
    (root / "PRODUCTION_PROMPT.md").write_text("drift\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CODEX_CAPTURE", str(capture))
    with pytest.raises(acceptance_controller.AcceptanceControllerError, match="PREFLIGHT"):
        acceptance_controller.run_acceptance(
            project_root=root,
            installed_skill_root=installed,
            private_root=private_root,
            harness_dir=tmp_path / "external-harness",
            requirement_pack=requirement_name,
            codex_bin=str(fake_codex),
            allow_test_codex=True,
        )
    assert not capture.exists()


def test_acceptance_controller_rejects_consistent_prompt_and_manifest_swap_after_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, requirement_name, private_root, installed, fake_codex, capture = (
        _controller_fixture(tmp_path)
    )
    original_validate = acceptance_controller.validate_requirement_pack

    def validate_then_swap(*args: object, **kwargs: object) -> dict[str, object]:
        report = original_validate(*args, **kwargs)
        (root / "PRODUCTION_PROMPT.md").write_text(
            "replacement prompt after preflight\n",
            encoding="utf-8",
        )
        _write_pre_manifest(root)
        return report

    monkeypatch.setenv("FAKE_CODEX_CAPTURE", str(capture))
    monkeypatch.setattr(
        acceptance_controller,
        "validate_requirement_pack",
        validate_then_swap,
    )
    with pytest.raises(
        acceptance_controller.AcceptanceControllerError,
        match="PRE_RUN_MANIFEST_CHANGED_AFTER_PREFLIGHT",
    ):
        acceptance_controller.run_acceptance(
            project_root=root,
            installed_skill_root=installed,
            private_root=private_root,
            harness_dir=tmp_path / "external-harness",
            requirement_pack=requirement_name,
            codex_bin=str(fake_codex),
            allow_test_codex=True,
        )
    assert not capture.exists()


def test_acceptance_controller_child_nonzero_preserves_external_failure_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, requirement_name, private_root, installed, fake_codex, capture = (
        _controller_fixture(tmp_path)
    )
    harness = tmp_path / "external-harness"
    monkeypatch.setenv("FAKE_CODEX_CAPTURE", str(capture))
    monkeypatch.setenv("FAKE_CODEX_EXIT", "7")
    monkeypatch.setattr(
        acceptance_controller,
        "validate_run_fingerprint",
        _mock_pass_validation,
    )
    result = acceptance_controller.run_acceptance(
        project_root=root,
        installed_skill_root=installed,
        private_root=private_root,
        harness_dir=harness,
        requirement_pack=requirement_name,
        codex_bin=str(fake_codex),
        allow_test_codex=True,
    )
    assert result["status"] == "FAIL"
    assert result["child_exit"] == {"code": 7, "status": "failed"}
    assert (harness / "post-run-manifest.v1.json").is_file()
    assert (harness / "physical-assembly-run-fingerprint.v1.json").is_file()


def test_acceptance_controller_rejects_private_library_profile_mismatch_before_spawn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, requirement_name, private_root, installed, fake_codex, capture = (
        _controller_fixture(tmp_path)
    )
    library = private_root / "v61" / "reference-work-summary-library-v4.json"
    payload = json.loads(library.read_text(encoding="utf-8"))
    payload["library_id"] = "drifted-library"
    _json(library, payload)
    monkeypatch.setenv("FAKE_CODEX_CAPTURE", str(capture))
    with pytest.raises(
        acceptance_controller.AcceptanceControllerError,
        match="PRIVATE_LIBRARY_PROFILE_SHA256_MISMATCH",
    ):
        acceptance_controller.run_acceptance(
            project_root=root,
            installed_skill_root=installed,
            private_root=private_root,
            harness_dir=tmp_path / "external-harness",
            requirement_pack=requirement_name,
            codex_bin=str(fake_codex),
            allow_test_codex=True,
        )
    assert not capture.exists()


def test_acceptance_controller_detects_installed_skill_drift_during_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, requirement_name, private_root, installed, fake_codex, capture = (
        _controller_fixture(tmp_path)
    )
    monkeypatch.setenv("FAKE_CODEX_CAPTURE", str(capture))
    monkeypatch.setenv("FAKE_MUTATE_SKILL", str(installed / "SKILL.md"))
    monkeypatch.setattr(
        acceptance_controller,
        "validate_run_fingerprint",
        _mock_pass_validation,
    )
    result = acceptance_controller.run_acceptance(
        project_root=root,
        installed_skill_root=installed,
        private_root=private_root,
        harness_dir=tmp_path / "external-harness",
        requirement_pack=requirement_name,
        codex_bin=str(fake_codex),
        allow_test_codex=True,
    )
    assert result["status"] == "FAIL"
    assert "INSTALLED_SKILL_CHANGED_DURING_RUN" in result["controller_issues"]


def test_acceptance_controller_keeps_pre_execution_prompt_and_manifest_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, requirement_name, private_root, installed, fake_codex, capture = (
        _controller_fixture(tmp_path)
    )
    original_prompt = _record(root, "PRODUCTION_PROMPT.md")
    original_manifest = _record(root, "PRE-RUN-MANIFEST.json")
    harness = tmp_path / "external-harness"
    monkeypatch.setenv("FAKE_CODEX_CAPTURE", str(capture))
    monkeypatch.setenv("FAKE_MUTATE_PROMPT", "1")
    monkeypatch.setattr(
        acceptance_controller,
        "validate_run_fingerprint",
        _mock_pass_validation,
    )
    result = acceptance_controller.run_acceptance(
        project_root=root,
        installed_skill_root=installed,
        private_root=private_root,
        harness_dir=harness,
        requirement_pack=requirement_name,
        codex_bin=str(fake_codex),
        allow_test_codex=True,
    )
    fingerprint = json.loads(
        (harness / "physical-assembly-run-fingerprint.v1.json").read_text(encoding="utf-8")
    )
    observed = json.loads(capture.read_text(encoding="utf-8"))
    assert result["status"] == "FAIL"
    assert fingerprint["command"]["stdin"] == original_prompt
    assert fingerprint["command"]["stdin"]["sha256"] == hashlib.sha256(
        observed["prompt"].encode("utf-8")
    ).hexdigest()
    assert fingerprint["manifests"]["pre_run"] == original_manifest
    assert "PROMPT_CHANGED_DURING_RUN" in result["controller_issues"]
    assert "PRE_RUN_MANIFEST_CHANGED_DURING_RUN" in result["controller_issues"]


@pytest.mark.parametrize(
    "mode",
    ["inside-project", "inside-installed-skill", "inside-private-root", "nonempty"],
)
def test_acceptance_controller_rejects_unsafe_harness_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    root, requirement_name, private_root, installed, fake_codex, capture = (
        _controller_fixture(tmp_path)
    )
    if mode == "inside-project":
        harness = root / "harness"
    elif mode == "inside-installed-skill":
        harness = installed / "harness"
    elif mode == "inside-private-root":
        harness = private_root / "harness"
    else:
        harness = tmp_path / "external-harness"
        harness.mkdir()
        (harness / "old.txt").write_text("old\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CODEX_CAPTURE", str(capture))
    with pytest.raises(acceptance_controller.AcceptanceControllerError):
        acceptance_controller.run_acceptance(
            project_root=root,
            installed_skill_root=installed,
            private_root=private_root,
            harness_dir=harness,
            requirement_pack=requirement_name,
            codex_bin=str(fake_codex),
            allow_test_codex=True,
        )
    assert not capture.exists()
    if mode != "nonempty":
        assert not harness.exists()
