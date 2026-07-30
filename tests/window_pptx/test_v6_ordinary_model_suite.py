from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from PIL import Image
from window_pptx.ordinary_model_suite import (
    SCENARIO_ARCHETYPE,
    build_ordinary_plan_prompt,
    evaluate_ordinary_plan,
)
from window_pptx.project_brief_corpus import load_project_brief_corpus
from window_pptx.registry import resolve_archetype


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"


def _valid_response(scenario: str) -> dict[str, object]:
    pack = load_project_brief_corpus()[scenario]
    facts = [item["id"] for item in pack["fact_store"]["facts"]]
    archetype_id = SCENARIO_ARCHETYPE[scenario]
    beats = resolve_archetype(archetype_id).sections
    groups = []
    for index in range(4):
        refs = facts[index::4]
        groups.append(
            {
                "id": f"group-{index + 1}",
                "fact_refs": refs,
                "beat_hint": beats[index % len(beats)],
                "semantic_hint": "metrics" if index == 0 else "process",
                "importance": "high" if index == 0 else "normal",
            }
        )
    return {
        "schema_version": "1.0",
        "scenario_id": archetype_id,
        "groups": groups,
        "preferences": {
            "tone": "professional",
            "density": "balanced",
            "audience_mode": "executive",
            "motion": "off",
        },
    }


def test_prompt_is_closed_world_and_excludes_geometry_authority() -> None:
    pack = load_project_brief_corpus()["project-proposal"]
    prompt = build_ordinary_plan_prompt(pack)

    assert "每个 fact id 必须且只能出现一次" in prompt
    assert all(item["id"] in prompt for item in pack["fact_store"]["facts"])
    assert "坐标" in prompt and "颜色" in prompt and "模板 ID" in prompt


def test_all_fifteen_scenarios_accept_complete_registered_grouping() -> None:
    for scenario, pack in load_project_brief_corpus().items():
        result = evaluate_ordinary_plan(pack, _valid_response(scenario))
        assert result.status == "PASS"
        assert result.fact_coverage == 1.0
        assert result.group_count == 4


def test_missing_fact_and_freeform_geometry_fail_closed() -> None:
    pack = load_project_brief_corpus()["market-analysis"]
    response = _valid_response("market-analysis")
    response["groups"][0]["fact_refs"].pop()  # type: ignore[index]
    result = evaluate_ordinary_plan(pack, response)
    assert result.status == "FAIL"
    assert "FACT_COVERAGE_MISMATCH" in str(result.error)

    poisoned = json.loads(json.dumps(_valid_response("market-analysis")))
    poisoned["groups"][0]["x"] = 1.2
    result = evaluate_ordinary_plan(pack, poisoned)
    assert result.status == "FAIL"


@pytest.fixture(scope="module")
def ordinary_suite_output(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("v6-ordinary-suite")
    briefs = root / "briefs"
    assets = root / "assets"
    plans = root / "plans"
    output = root / "output"
    assets.mkdir()
    plans.mkdir()
    for name, color in (
        ("work-hero.png", "#0A604D"),
        ("campus-hero.png", "#0A263D"),
        ("academic-hero.png", "#081B36"),
    ):
        Image.new("RGB", (1600, 900), color).save(assets / name)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SCRIPTS_ROOT)
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_ROOT / "export_window_pptx_brief_corpus.py"),
            "--output-dir",
            str(briefs),
        ],
        cwd=REPO_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    semantic_cycle = ("metrics", "comparison", "matrix", "process")
    for index, scenario in enumerate(load_project_brief_corpus()):
        plan = _valid_response(scenario)
        plan["groups"][0]["semantic_hint"] = semantic_cycle[index % 4]  # type: ignore[index]
        (plans / f"{scenario}.brief-plan.v1.json").write_text(
            json.dumps(plan, ensure_ascii=False),
            encoding="utf-8",
        )
    subprocess.run(
        [
            "node",
            str(SCRIPTS_ROOT / "build_window_pptx_v6_reference_anchors.mjs"),
            "--brief-dir",
            str(briefs),
            "--asset-dir",
            str(assets),
            "--output-dir",
            str(output),
            "--ordinary-plan-dir",
            str(plans),
            "--all-scenarios",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return output


def test_twelve_non_flagships_meet_budget_and_use_distinct_signatures(
    ordinary_suite_output: Path,
) -> None:
    corpus = load_project_brief_corpus()
    signatures = set()
    semantic_families = set()
    for scenario in sorted(set(corpus) - {
        "annual-work-report",
        "campus-competition-defense",
        "academic-thesis-defense",
    }):
        deck = ordinary_suite_output / f"{scenario}-reference-anchor.pptx"
        manifest = json.loads(
            Path(f"{deck}.manifest.json").read_text(encoding="utf-8")
        )
        assert 16 <= manifest["slide_count"] <= 20
        assert manifest["ordinary_model_plan"]["authority"] == (
            "semantic-fact-grouping-and-order-only"
        )
        roles = [slide["role"] for slide in manifest["slides"]]
        assert roles.count("section") == 4
        assert roles.count("appendix") == 3
        signature = next(
            slide["family"]
            for slide in manifest["slides"]
            if slide["role"] == "scenario-signature"
        )
        signatures.add(signature)
        semantic_families.add(
            next(
                slide["family"]
                for slide in manifest["slides"]
                if slide["role"] == "model-semantic"
            )
        )
        with zipfile.ZipFile(deck) as archive:
            slide_xml = [
                name for name in archive.namelist()
                if name.startswith("ppt/slides/slide")
                and name.endswith(".xml")
                and "/_rels/" not in name
            ]
            assert len(slide_xml) == manifest["slide_count"]
    assert len(signatures) == 12
    assert semantic_families >= {
        "semantic-metric-ledger",
        "semantic-comparison",
        "semantic-matrix",
        "semantic-process",
    }
