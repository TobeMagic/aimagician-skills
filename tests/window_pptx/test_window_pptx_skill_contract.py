from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio"


def test_v6_skill_defaults_to_locked_quality_first_authoring() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "ProjectBriefPack (Draft -> NeedsDiscussion -> Locked)" in skill
    assert "## v6.0 Quality-First Authoring Contract" in skill
    assert "Codex GPT-5.5 medium" in skill
    assert "## Realistic Brief Corpus" in skill
    assert "## Private Template-Library Boundary" in skill
    assert "three-context AI-only blind reference review" in skill
    assert "no two-reviewer fallback or human override" in skill
    assert "Governed BriefPlan Mode (Default" not in skill
    assert "independent-human" not in skill
    assert "human blind review" not in skill.casefold()
    assert "python -m window_pptx.cli --doctor" not in skill
    assert "scripts/node/window_pptx_worker.mjs --doctor" in skill


def test_v6_skill_links_executable_contract_files() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    linked = (
        "references/quality-first-v6-workflow.md",
        "scripts/manage_window_pptx_project_brief.py",
        "scripts/export_window_pptx_brief_corpus.py",
        "scripts/check_window_pptx_private_assets.py",
        "scripts/manage_window_pptx_library.py",
        "schemas/project-brief-pack.v1.schema.json",
        "schemas/acquisition-manifest.v1.schema.json",
        "schemas/quarantine-report.v1.schema.json",
        "schemas/rights-record.v1.schema.json",
        "schemas/catalog.v3.schema.json",
        "registries/catalog-v3.json",
    )

    for relative in linked:
        assert relative in skill
        assert (SKILL_ROOT / relative).is_file()


def test_v6_behavior_eval_cases_cover_new_failure_boundaries() -> None:
    payload = json.loads(
        (SKILL_ROOT / "assets" / "calibration" / "scenarios.json").read_text(encoding="utf-8")
    )
    scenarios = {item["id"]: item for item in payload["scenarios"]}

    assert {
        "quality-first-new-business-deck",
        "unresolved-real-client-brief",
        "private-commercial-template-cookie",
        "v6-blind-review-unavailable",
        "weak-model-distillation-request",
        "private-library-dry-run-query",
    } <= set(scenarios)
    assert "no PPTX" in scenarios["unresolved-real-client-brief"]["expected"]
    assert "GO from two reviewers" in scenarios["v6-blind-review-unavailable"][
        "forbidden"
    ]
    assert "cookie in command argument" in scenarios[
        "private-commercial-template-cookie"
    ]["forbidden"]
    assert "cookie in argv" in scenarios["private-library-dry-run-query"]["forbidden"]
