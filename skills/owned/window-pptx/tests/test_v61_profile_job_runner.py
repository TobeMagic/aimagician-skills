"""Focused tests for the bounded v6.1 profile job runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import run_window_pptx_v61_profile_job as runner  # noqa: E402
from window_pptx.assembly_autobinder import AutoBindingError  # noqa: E402
from window_pptx.weak_model import (  # noqa: E402
    Fact,
    FactSource,
    FactStore,
    TrustedProject,
)


SHA_VALUES = {
    "profile": "1" * 64,
    "library": "2" * 64,
    "query": "3" * 64,
    "plan": "4" * 64,
    "output": "5" * 64,
    "report": "6" * 64,
    "rule_qa": "7" * 64,
    "fact": "8" * 64,
    "asset": "9" * 64,
    "connective": "a" * 64,
}


def _profile_and_plan() -> tuple[dict[str, Any], dict[str, Any]]:
    page_one = f"{'b' * 64}:001"
    page_two = f"{'c' * 64}:002"
    profile = {
        "profile_id": "phase49-synthetic",
        "scenario_id": "synthetic-work-report",
        "acceptance_profile": "phase49-synthetic-acceptance",
        "dominant_style_cluster_id": "ivory-green-gold-editorial",
        "slides": [
            {
                "ordinal": 1,
                "page_id": page_one,
                "narrative_role": "cover",
                "fact_ids": ["fact-title"],
            },
            {
                "ordinal": 2,
                "page_id": page_two,
                "narrative_role": "body",
                "fact_ids": ["fact-body"],
            },
        ],
    }
    plan = {
        "schema_version": "1.0",
        "plan_id": "phase49-synthetic-compiled",
        "scenario_id": profile["scenario_id"],
        "dominant_style_cluster_id": profile["dominant_style_cluster_id"],
        "created_at": "2026-08-09T00:00:00Z",
        "target_slide_count": 2,
        "target_slides": [
            {
                "ordinal": 1,
                "narrative_role": "cover",
                "page_id": page_one,
                "package_sha256": "b" * 64,
                "slide_number": 1,
                "title": "年度工作总结",
                "headline": "",
                "bindings": {},
            },
            {
                "ordinal": 2,
                "narrative_role": "body",
                "page_id": page_two,
                "package_sha256": "c" * 64,
                "slide_number": 2,
                "title": "经营运行稳健",
                "headline": "",
                "bindings": {},
            },
        ],
        "library_index_sha256": SHA_VALUES["library"],
        "authority": {
            "fact_store": {"path": "fact-store.v1.json", "sha256": SHA_VALUES["fact"]},
            "asset_manifest": {
                "path": "asset-manifest.v1.json",
                "sha256": SHA_VALUES["asset"],
            },
            "connective_copy": {
                "path": "connective-copy.v1.json",
                "sha256": SHA_VALUES["connective"],
            },
        },
    }
    return profile, plan


def _fact_store() -> FactStore:
    return FactStore(
        schema_version="1.0",
        project=TrustedProject(
            title="Synthetic work report",
            objective="Exercise the bounded job runner",
            audience="Independent reviewers",
            language="zh-CN",
        ),
        sources=(
            FactSource(
                id="client-request",
                kind="request",
                locator="REQUEST.md",
                sha256="d" * 64,
            ),
        ),
        facts=(
            Fact(
                id="fact-title",
                kind="claim",
                text="年度工作总结",
                language="zh-CN",
                source_id="client-request",
                locator="REQUEST.md#title",
                required=False,
            ),
            Fact(
                id="fact-body",
                kind="claim",
                text="经营运行稳健",
                language="zh-CN",
                source_id="client-request",
                locator="REQUEST.md#body",
                required=False,
            ),
        ),
        digest="e" * 64,
    )


def _runner_args() -> argparse.Namespace:
    return argparse.Namespace(
        model_provider="openai",
        model="gpt-5.6-terra",
        reasoning_effort="medium",
    )


def _fingerprint(profile: dict[str, Any]) -> dict[str, Any]:
    return runner._fingerprint_bundle(
        args=_runner_args(),
        profile=profile,
        profile_sha256=SHA_VALUES["profile"],
        library_sha256=SHA_VALUES["library"],
        query_sha256=SHA_VALUES["query"],
        plan_sha256=SHA_VALUES["plan"],
        output_sha256=SHA_VALUES["output"],
        report_sha256=SHA_VALUES["report"],
        rule_qa_sha256=SHA_VALUES["rule_qa"],
        fact_sha256=SHA_VALUES["fact"],
        asset_sha256=SHA_VALUES["asset"],
        connective_sha256=SHA_VALUES["connective"],
        resolution_source="explicit-private-root",
    )


def test_profile_path_accepts_only_an_installed_registry_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_skill = tmp_path / "installed-skill"
    registry = fake_skill / "registries" / "v61-binding-profiles"
    registry.mkdir(parents=True)
    installed = registry / "approved.binding-profile.v1.json"
    installed.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(runner, "SKILL_ROOT", fake_skill)

    assert runner._profile_path("approved") == installed.resolve()

    outside = tmp_path / "outside.binding-profile.v1.json"
    outside.write_text("{}", encoding="utf-8")
    installed.unlink()
    installed.symlink_to(outside)
    with pytest.raises(AutoBindingError, match="PROFILE_NOT_FOUND: approved"):
        runner._profile_path("approved")


@pytest.mark.parametrize("profile_id", ["../escape", "a/b", "UPPER", "", "a.b"])
def test_profile_id_rejects_path_syntax(profile_id: str) -> None:
    with pytest.raises(AutoBindingError, match="PROFILE_ID_INVALID"):
        runner._profile_path(profile_id)


def test_private_library_path_must_be_relative_and_stay_beneath_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_root = tmp_path / "private"
    library = private_root / "v61" / "library-v4.json"
    library.parent.mkdir(parents=True)
    library.write_text("{}", encoding="utf-8")
    outside = tmp_path / "outside-library.json"
    outside.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        runner,
        "resolve_private_root",
        lambda *, explicit: private_root.resolve(),
    )

    args = argparse.Namespace(private_root=str(private_root), library="v61/library-v4.json")
    resolved, source, root = runner._library_path(args)
    assert resolved == library.resolve()
    assert source == "explicit-private-root"
    assert root == private_root.resolve()

    args.library = str(library.resolve())
    with pytest.raises(
        AutoBindingError,
        match="LIBRARY_MUST_BE_PRIVATE_ROOT_RELATIVE",
    ):
        runner._library_path(args)

    args.library = "../outside-library.json"
    with pytest.raises(AutoBindingError, match="LIBRARY_PATH_ESCAPE"):
        runner._library_path(args)


def test_direction_narrative_and_fingerprint_evidence_pass_schemas() -> None:
    profile, plan = _profile_and_plan()
    direction = runner._direction_evidence(profile)
    narrative = runner._narrative_evidence(profile, plan, _fact_store())
    fingerprint = _fingerprint(profile)

    runner._validate_schema(
        direction,
        "direction-decision.v1.schema.json",
        "DIRECTION_SCHEMA_INVALID",
    )
    runner._validate_schema(
        narrative,
        "narrative-plan.v1.schema.json",
        "NARRATIVE_SCHEMA_INVALID",
    )
    runner._validate_schema(
        fingerprint,
        "fingerprint-bundle.v1.schema.json",
        "FINGERPRINT_SCHEMA_INVALID",
    )
    assert direction["selected_slot"] == "editorial"
    assert direction["selected_profile_id"] == profile["profile_id"]
    assert narrative["coverage"] == {
        "active_fact_count": 2,
        "scoped_fact_count": 2,
        "unscoped_fact_ids": [],
    }


def test_fingerprint_binds_every_critical_sha_and_runtime_identity() -> None:
    profile, _ = _profile_and_plan()
    bundle = _fingerprint(profile)
    fingerprint = bundle["fingerprints"][0]

    assert fingerprint == {
        "profile_id": profile["profile_id"],
        "profile_sha256": SHA_VALUES["profile"],
        "library_index_sha256": SHA_VALUES["library"],
        "query_bundle_sha256": SHA_VALUES["query"],
        "assembly_plan_sha256": SHA_VALUES["plan"],
        "output_sha256": SHA_VALUES["output"],
        "physical_report_sha256": SHA_VALUES["report"],
        "rule_qa_sha256": SHA_VALUES["rule_qa"],
        "fact_store_sha256": SHA_VALUES["fact"],
        "asset_manifest_sha256": SHA_VALUES["asset"],
        "connective_copy_sha256": SHA_VALUES["connective"],
        "evidence_generation": "v61-physical-template-assembly",
    }
    assert bundle["components"] == {
        "model_provider": "openai",
        "model": "gpt-5.6-terra",
        "reasoning_effort": "medium",
        "acceptance_profile": profile["acceptance_profile"],
        "private_library_resolution_source": "explicit-private-root",
        "native_editable": True,
        "visual_fallback": False,
    }


def test_run_summary_is_candidate_terminal_state_without_visual_self_scoring() -> None:
    profile, plan = _profile_and_plan()
    summary = runner._run_summary(
        plan=plan,
        profile=profile,
        output_sha256=SHA_VALUES["output"],
        report={
            "status": "pass",
            "metrics": {"physical_reuse_coverage": 1.0},
            "editability": {"native_editable_coverage": 1.0},
        },
        rule_qa={"status": "pass"},
        auto_binding_report={"ordinary_slot_count": 12},
    )

    assert "Author state: `CANDIDATE_READY_FOR_BLIND_REVIEW`" in summary
    assert "visual release remains pending independent blind review" in summary
    assert "RELEASED" not in summary
    lowered = summary.casefold()
    for forbidden in (
        "visual score",
        "self-score",
        "self rating",
        "8/10",
        "9/10",
        "审美评分",
        "视觉评分",
    ):
        assert forbidden not in lowered


def test_parser_defaults_lock_the_acceptance_model_contract() -> None:
    args = runner._parser().parse_args(["--project-root", "/tmp/project"])

    assert args.model_provider == "openai"
    assert args.model == "gpt-5.6-terra"
    assert args.reasoning_effort == "medium"
    assert args.profile_id == "phase49-work-report-15"
    assert args.library == "v61/reference-work-summary-library-v4.json"


class _MachineResult:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.status = "pass"
        self._payload = payload

    def to_dict(self) -> dict[str, Any]:
        return dict(self._payload)


def _write_mock_report(payload: dict[str, Any], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def test_mocked_run_emits_exactly_eight_evidence_files_and_one_pptx(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "clean-project"
    project.mkdir()
    for name, payload in (
        ("fact-store.v1.json", {"schema_version": "1.0"}),
        ("asset-manifest.v1.json", {"schema_version": "1.0"}),
        (
            "connective-copy.v1.json",
            {"schema_version": "1.0", "entries": [{"id": "clear", "text": ""}]},
        ),
    ):
        (project / name).write_text(json.dumps(payload), encoding="utf-8")

    profile, plan_payload = _profile_and_plan()
    profile_path = tmp_path / "profile.json"
    profile_path.write_text("{}", encoding="utf-8")
    private_root = tmp_path / "private"
    private_root.mkdir()
    library_path = private_root / "library.json"
    library_path.write_text("synthetic-library", encoding="utf-8")
    library = SimpleNamespace(page_templates=())
    loaded_plan = SimpleNamespace(target_slide_count=2)
    physical_payload = {
        "status": "pass",
        "metrics": {"physical_reuse_coverage": 1.0},
        "editability": {"native_editable_coverage": 1.0},
    }
    qa_payload = {"status": "pass"}
    physical = _MachineResult(physical_payload)
    qa = _MachineResult(qa_payload)

    monkeypatch.setattr(
        runner,
        "validate_requirement_pack",
        lambda *_args, **_kwargs: {"status": "PASS", "issues": []},
    )
    monkeypatch.setattr(runner, "_profile_path", lambda _profile_id: profile_path)
    monkeypatch.setattr(
        runner,
        "load_binding_profile",
        lambda _path: (profile, SHA_VALUES["profile"]),
    )
    monkeypatch.setattr(
        runner,
        "_library_path",
        lambda _args: (library_path, "explicit-private-root", private_root),
    )
    monkeypatch.setattr(runner, "load_library_index", lambda _path: library)
    monkeypatch.setattr(runner, "load_fact_store", lambda _path: _fact_store())
    monkeypatch.setattr(
        runner,
        "build_profile_query_bundle",
        lambda *_args, **_kwargs: {
            "schema_version": "page-template-query-bundle.v1",
            "library_index_sha256": hashlib.sha256(
                library_path.read_bytes()
            ).hexdigest(),
            "query_count": 2,
            "queries": [],
        },
    )
    monkeypatch.setattr(
        runner,
        "compile_assembly_intent",
        lambda *_args, **_kwargs: (
            {
                **plan_payload,
                "library_index_sha256": hashlib.sha256(
                    library_path.read_bytes()
                ).hexdigest(),
            },
            {"ordinary_slot_count": 12},
        ),
    )
    monkeypatch.setattr(
        runner,
        "load_assembly_plan",
        lambda *_args, **_kwargs: loaded_plan,
    )

    def fake_assemble(_plan: Any, output_path: Path, **_kwargs: Any) -> _MachineResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"PK\x03\x04synthetic-pptx")
        return physical

    monkeypatch.setattr(runner, "assemble_physical_deck", fake_assemble)
    monkeypatch.setattr(
        runner,
        "write_assembly_report",
        lambda result, path: _write_mock_report(result.to_dict(), path),
    )
    monkeypatch.setattr(runner, "run_physical_rule_qa", lambda *_a, **_k: qa)
    monkeypatch.setattr(
        runner,
        "write_rule_qa_report",
        lambda result, path: _write_mock_report(result.to_dict(), path),
    )

    # The profile locks the private library bytes used by this synthetic run.
    profile["library_index_sha256"] = hashlib.sha256(library_path.read_bytes()).hexdigest()
    result = runner.run(["--project-root", str(project)])

    assert result["status"] == "CANDIDATE_READY_FOR_BLIND_REVIEW"
    assert result["output"] == runner.OUTPUT_RELATIVE
    evidence_files = sorted(
        path.relative_to(project).as_posix()
        for path in (project / "evidence").iterdir()
        if path.is_file()
    )
    assert evidence_files == sorted(
        [
            runner.DIRECTION_RELATIVE,
            runner.NARRATIVE_RELATIVE,
            runner.PLAN_RELATIVE,
            runner.QUERY_RELATIVE,
            runner.REPORT_RELATIVE,
            runner.RULE_QA_RELATIVE,
            runner.FINGERPRINT_RELATIVE,
            runner.SUMMARY_RELATIVE,
        ]
    )
    assert len(evidence_files) == 8
    output_files = [path for path in (project / "output").iterdir() if path.is_file()]
    assert [path.relative_to(project).as_posix() for path in output_files] == [
        runner.OUTPUT_RELATIVE
    ]
    summary = (project / runner.SUMMARY_RELATIVE).read_text(encoding="utf-8")
    assert "CANDIDATE_READY_FOR_BLIND_REVIEW" in summary
    fingerprint = json.loads(
        (project / runner.FINGERPRINT_RELATIVE).read_text(encoding="utf-8")
    )
    assert fingerprint["fingerprints"][0]["output_sha256"] == result["output_sha256"]
