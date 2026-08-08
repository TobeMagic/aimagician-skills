"""Focused regression tests for final v6.1 harness hardening."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_window_pptx_v61_clean_pack as validator  # noqa: E402
from window_pptx.v61_acceptance_settlement import (  # noqa: E402
    AcceptanceSettlementError,
    HARNESS_FILE_NAMES,
    capture_settled_inventory,
    run_in_isolated_process_group,
    validate_distinct_file_paths,
    validate_harness_topology,
    verify_settlement_evidence,
)


def _write_harness(root: Path) -> dict[str, Path]:
    root.mkdir()
    paths: dict[str, Path] = {}
    for role, name in HARNESS_FILE_NAMES.items():
        path = root / name
        path.write_text(f"{role}\n", encoding="utf-8")
        paths[role] = path
    return paths


def _records(root: Path) -> list[dict[str, object]]:
    records = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        payload = path.read_bytes()
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
            }
        )
    return records


def test_harness_topology_requires_one_exact_real_isolated_directory(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    installed = tmp_path / "installed"
    private = tmp_path / "private"
    runtime = tmp_path / "runtime.json"
    for directory in (project, installed, private):
        directory.mkdir()
    runtime.write_text("{}\n", encoding="utf-8")
    paths = _write_harness(tmp_path / "harness")
    assert validate_harness_topology(
        artifact_paths=paths,
        authority_paths={
            "project": project,
            "installed": installed,
            "private": private,
            "runtime": runtime,
        },
    ) == (tmp_path / "harness").resolve()

    (tmp_path / "harness" / "undeclared.log").write_text("no\n", encoding="utf-8")
    with pytest.raises(
        AcceptanceSettlementError, match="HARNESS_DIRECTORY_CONTENT_MISMATCH"
    ):
        validate_harness_topology(
            artifact_paths=paths,
            authority_paths={"project": project},
        )


def test_harness_topology_rejects_parent_symlink_and_authority_overlap(
    tmp_path: Path,
) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    paths = _write_harness(real_parent / "harness")
    alias = tmp_path / "alias"
    alias.symlink_to(real_parent, target_is_directory=True)
    aliased_paths = {
        role: alias / "harness" / path.name for role, path in paths.items()
    }
    with pytest.raises(AcceptanceSettlementError, match="PARENT_SYMLINK_FORBIDDEN"):
        validate_harness_topology(
            artifact_paths=aliased_paths,
            authority_paths={"project": tmp_path / "unrelated"},
        )

    with pytest.raises(AcceptanceSettlementError, match="HARNESS_AUTHORITY_OVERLAP"):
        validate_harness_topology(
            artifact_paths=paths,
            authority_paths={"project": real_parent},
        )

    traversal_paths = dict(paths)
    traversal_paths["events_jsonl"] = (
        real_parent / "harness" / "nested" / ".." / HARNESS_FILE_NAMES["events_jsonl"]
    )
    with pytest.raises(AcceptanceSettlementError, match="PATH_TRAVERSAL_FORBIDDEN"):
        validate_harness_topology(
            artifact_paths=traversal_paths,
            authority_paths={"project": tmp_path / "unrelated"},
        )


def test_evidence_paths_must_not_alias_by_case_or_hardlink(tmp_path: Path) -> None:
    root = tmp_path / "project"
    evidence = root / "evidence"
    evidence.mkdir(parents=True)
    first = evidence / "one.json"
    second = evidence / "two.json"
    first.write_text("{}\n", encoding="utf-8")
    os.link(first, second)
    with pytest.raises(
        AcceptanceSettlementError, match="EVIDENCE_FILE_IDENTITY_DUPLICATE"
    ):
        validate_distinct_file_paths(
            root=root,
            relative_paths=["evidence/one.json", "evidence/two.json"],
        )
    with pytest.raises(AcceptanceSettlementError, match="EVIDENCE_PATH_CASE_COLLISION"):
        validate_distinct_file_paths(
            root=root,
            relative_paths=["evidence/one.json", "EVIDENCE/ONE.JSON"],
        )


def test_private_library_source_must_stay_in_private_or_installed_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private = tmp_path / "private"
    installed = tmp_path / "installed"
    outside = tmp_path / "outside"
    for directory in (private / "v61", installed, outside):
        directory.mkdir(parents=True)
    library = private / "v61" / "library.json"
    library.write_text("{}\n", encoding="utf-8")
    source = outside / "template.pptx"
    source.write_bytes(b"private-template")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    fake_index = SimpleNamespace(
        source_core_schema="user-certified-reference-deck.v1",
        source_package_index={source_sha: {}},
        private_root_sha256=source_sha,
        page_templates=[
            SimpleNamespace(
                source_path=str(source),
                package_sha256=source_sha,
                source_sha256=source_sha,
            )
        ],
    )
    monkeypatch.setattr(validator, "load_library_index", lambda _path: fake_index)
    with pytest.raises(ValueError, match="PHASE49_SOURCE_PACKAGE_AUTHORITY_ESCAPE"):
        validator._phase49_private_library_identity(
            library,
            allowed_source_roots=(private, installed),
        )
    accepted = validator._phase49_private_library_identity(
        library,
        allowed_source_roots=(private, installed, outside),
    )
    assert accepted["source_package_count"] == 1


def test_settlement_requires_three_separated_identical_inventories(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "input.txt").write_text("stable\n", encoding="utf-8")
    entries, evidence = capture_settled_inventory(
        lambda: _records(project),
        minimum_window_ms=20,
        sample_interval_seconds=0.01,
    )
    assert evidence["sample_count"] >= 3
    assert evidence["window_ms"] >= 20
    settlement = {
        "process_group": {
            "isolation": "new-posix-session",
            "leader_pid": 2_000_000_000,
            "process_group_id": 2_000_000_000,
            "cleanup_attempted": False,
            "signals_sent": [],
            "absence_probe_count": 1,
            "residue_status": "absent",
        },
        "inventory": evidence,
    }
    # Unit tests use a shorter window; production validation is intentionally
    # stricter and therefore rejects this weakened fixture.
    with pytest.raises(
        AcceptanceSettlementError, match="SETTLEMENT_WINDOW_POLICY_TOO_WEAK"
    ):
        verify_settlement_evidence(
            settlement,
            post_inventory=entries,
            probe_process_group=False,
        )

    entries, evidence = capture_settled_inventory(lambda: _records(project))
    settlement["inventory"] = evidence
    verify_settlement_evidence(
        settlement,
        post_inventory=entries,
        probe_process_group=False,
    )
    tampered = json.loads(json.dumps(settlement))
    tampered["inventory"]["samples"][-1]["inventory_sha256"] = "0" * 64
    with pytest.raises(AcceptanceSettlementError, match="SETTLEMENT_INVENTORY_MISMATCH"):
        verify_settlement_evidence(
            tampered,
            post_inventory=entries,
            probe_process_group=False,
        )


def test_settlement_discards_unstable_prefix_and_renumbers_stable_samples() -> None:
    calls = 0

    def inventory() -> list[dict[str, object]]:
        nonlocal calls
        calls += 1
        payload = b"first" if calls == 1 else b"settled"
        return [
            {
                "path": "result.bin",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
            }
        ]

    entries, evidence = capture_settled_inventory(
        inventory,
        minimum_window_ms=20,
        sample_interval_seconds=0.01,
    )
    assert [sample["ordinal"] for sample in evidence["samples"]] == list(
        range(1, evidence["sample_count"] + 1)
    )
    assert evidence["samples"][0]["inventory_sha256"] == hashlib.sha256(
        json.dumps(
            entries,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups required")
def test_isolated_author_process_cleans_background_group_residue(
    tmp_path: Path,
) -> None:
    stdout = tmp_path / "events.jsonl"
    stderr = tmp_path / "stderr.log"
    code = (
        "import json,subprocess; "
        "subprocess.Popen(['sleep','30']); "
        "print(json.dumps({'type':'result','status':'completed'}))"
    )
    with stdout.open("wb") as stdout_stream, stderr.open("wb") as stderr_stream:
        result = run_in_isolated_process_group(
            [sys.executable, "-c", code],
            cwd=tmp_path,
            environment=os.environ,
            stdin_payload=b"",
            stdout_stream=stdout_stream,
            stderr_stream=stderr_stream,
        )
    assert result.returncode == 0
    assert result.process_group_evidence["cleanup_attempted"] is True
    assert result.process_group_evidence["signals_sent"]
    assert result.process_group_evidence["residue_status"] == "absent"


def test_validator_applies_existing_json_schema_and_summary_contract(
    tmp_path: Path,
) -> None:
    issues: list[dict[str, str]] = []
    assert not validator._validate_evidence_schema(
        {"schema_version": "1.0"},
        "direction-decision.v1.schema.json",
        issues,
        "evidence.direction",
    )
    assert "EVIDENCE_SCHEMA_VALIDATION_FAILED" in {
        issue["code"] for issue in issues
    }

    output = tmp_path / "candidate.pptx"
    output.write_bytes(b"candidate")
    output_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    rows = [
        f"| {ordinal} | role-{ordinal} | Title {ordinal} | `page-{ordinal}` | "
        f"`{'a' * 64}` | `cluster` | fact-{ordinal} | pass |"
        for ordinal in range(1, 16)
    ]
    summary = tmp_path / "run-summary.md"
    summary.write_text(
        "\n".join(
            [
                "# Phase 49 candidate run",
                "",
                "Author state: `CANDIDATE_READY_FOR_BLIND_REVIEW`",
                "",
                "| Page | Narrative role | Title | Page ID | Package SHA-256 | Style cluster | Fact IDs | Rule QA |",
                "|---:|---|---|---|---|---|---|---|",
                *rows,
                "",
                "## Machine-gate result",
                "",
                f"- Final PPTX SHA-256: `{output_sha}`",
                "- Slide count: 15",
                "- Distinct page IDs: 15",
                "- Physical lineage coverage: 1.0",
                "- Native editable coverage: 1.0",
                "- Physical assembly: pass",
                "- Rule QA: pass",
                "- Ordinary bindings expanded by Skill: 257",
                "- Unresolved warnings: none from blocking machine gates; visual release remains pending independent blind review.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    summary_issues: list[dict[str, str]] = []
    validator._validate_run_summary(
        summary,
        output_path=output,
        report_payload={"target_slide_count": 15},
        issues=summary_issues,
    )
    assert summary_issues == []

    summary.write_text(summary.read_text(encoding="utf-8").replace("257", "0"), encoding="utf-8")
    validator._validate_run_summary(
        summary,
        output_path=output,
        report_payload={"target_slide_count": 15},
        issues=summary_issues,
    )
    assert "RUN_SUMMARY_BINDING_COUNT_INVALID" in {
        issue["code"] for issue in summary_issues
    }
