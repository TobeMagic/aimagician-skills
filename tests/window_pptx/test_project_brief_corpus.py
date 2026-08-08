from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx" / "scripts"
EXPORTER = SCRIPTS_ROOT / "export_window_pptx_brief_corpus.py"
SCHEMAS = REPO_ROOT / "skills" / "owned" / "window-pptx" / "schemas"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))


from window_pptx.project_brief import prepare_formal_brief  # noqa: E402
from window_pptx.project_brief_corpus import (  # noqa: E402
    FLAGSHIP_SCENARIO_IDS,
    REQUIRED_SCENARIO_IDS,
    load_project_brief_corpus,
)


def _facts_by_claim(pack: dict[str, object]) -> dict[tuple[str, str], object]:
    fact_store = pack["fact_store"]
    assert isinstance(fact_store, dict)
    facts = fact_store["facts"]
    assert isinstance(facts, list)
    result: dict[tuple[str, str], object] = {}
    for fact in facts:
        assert isinstance(fact, dict)
        key = (str(fact.get("claim_key", "")), str(fact.get("time_scope", "")))
        result[key] = fact.get("value")
    return result


def test_corpus_has_three_full_flagships_and_twelve_realistic_skeletons() -> None:
    corpus = load_project_brief_corpus()

    assert set(corpus) == REQUIRED_SCENARIO_IDS
    assert len(corpus) == 15
    assert len(FLAGSHIP_SCENARIO_IDS) == 3
    assert len(set(corpus) - FLAGSHIP_SCENARIO_IDS) == 12
    assert len({pack["lock_sha256"] for pack in corpus.values()}) == 15

    for scenario_id, pack in corpus.items():
        validated = prepare_formal_brief(pack)
        assert validated.formal_ready is True
        fact_store = pack["fact_store"]
        assert isinstance(fact_store, dict)
        facts = fact_store["facts"]
        assert isinstance(facts, list)
        assets = pack["assets"]
        assert isinstance(assets, list)
        assert len(facts) >= (16 if scenario_id in FLAGSHIP_SCENARIO_IDS else 8)
        assert len(assets) >= 3
        anatomy = pack["anatomy"]
        assert isinstance(anatomy, list)
        assert {item["role"] for item in anatomy if isinstance(item, dict)} >= {
            "cover",
            "directory",
            "section-divider",
            "closing",
            "appendix",
        }


def test_all_corpus_packs_conform_to_project_brief_json_schema() -> None:
    project_schema = json.loads(
        (SCHEMAS / "project-brief-pack.v1.schema.json").read_text(encoding="utf-8")
    )
    fact_schema = json.loads(
        (SCHEMAS / "fact-store.v1.schema.json").read_text(encoding="utf-8")
    )
    registry = Registry().with_resource(
        "fact-store.v1.schema.json",
        Resource.from_contents(fact_schema),
    )
    validator = Draft202012Validator(project_schema, registry=registry)

    for pack in load_project_brief_corpus().values():
        validator.validate(pack)


def test_work_report_preserves_every_locked_business_metric() -> None:
    work = load_project_brief_corpus()["annual-work-report"]
    claims = _facts_by_claim(work)

    assert [claims[("customer-count", f"2026-Q{quarter}")] for quarter in range(1, 5)] == [
        46,
        59,
        76,
        94,
    ]
    assert [claims[("monthly-active-users", f"2026-Q{quarter}")] for quarter in range(1, 5)] == [
        1840,
        2320,
        3080,
        4260,
    ]
    assert [claims[("self-service-rate", f"2026-Q{quarter}")] for quarter in range(1, 5)] == [
        38,
        46,
        57,
        68,
    ]
    assert claims[("annual-budget", "2026-actual")] == 11.6
    assert claims[("annual-budget", "2026-budget")] == 12
    assert claims[("duplicate-metrics", "before")] == 126
    assert claims[("duplicate-metrics", "after")] == 41
    assert claims[("annual-savings", "2026")] == 2.8
    slide_budget = work["slide_budget"]
    assert isinstance(slide_budget, dict)
    assert slide_budget == {
        "main": 28,
        "minimum": 26,
        "maximum": 30,
        "appendix": 4,
        "backup": 0,
    }


def test_campus_pack_preserves_pilot_scope_and_defense_constraints() -> None:
    campus = load_project_brief_corpus()["campus-competition-defense"]
    claims = _facts_by_claim(campus)

    assert claims[("sensor-nodes", "pilot")] == 18
    assert claims[("pilot-days", "pilot")] == 84
    assert claims[("valid-record-rate", "pilot")] == 98.6
    assert claims[("alert-precision", "pilot")] == 81.1
    assert claims[("alert-recall", "pilot")] == 90.9
    assert claims[("alert-f1", "pilot")] == 85.7
    assert claims[("lead-time", "pilot")] == 42
    assert claims[("inspection-hours", "before-pilot")] == 9.6
    assert claims[("inspection-hours", "pilot")] == 4.1
    assert "不得将试点结果外推为规模化商业效果" in campus["prohibitions"]
    timing = campus["timing"]
    assert isinstance(timing, dict)
    assert timing == {"presentation_minutes": 7, "qa_minutes": 5}


def test_academic_pack_separates_public_metadata_from_synthetic_results() -> None:
    academic = load_project_brief_corpus()["academic-thesis-defense"]
    fact_store = academic["fact_store"]
    assert isinstance(fact_store, dict)
    sources = fact_store["sources"]
    facts = fact_store["facts"]
    assert isinstance(sources, list)
    assert isinstance(facts, list)
    source_by_id = {
        source["id"]: source
        for source in sources
        if isinstance(source, dict)
    }
    assert source_by_id["dcrnn-paper"]["locator"] == "https://arxiv.org/abs/1707.01926"

    for fact in facts:
        assert isinstance(fact, dict)
        if fact.get("claim_key") in {
            "dataset-sensors",
            "dataset-observations",
            "sampling-interval",
            "data-split",
        }:
            assert fact["source_id"] == "dcrnn-paper"
        if str(fact.get("claim_key", "")).startswith(
            ("mae-", "ablation-", "missing-", "params-", "inference-")
        ):
            assert fact["source_id"] == "synthetic-experiment-log"

    claims = _facts_by_claim(academic)
    assert claims[("mae-mdgformer-metr-la", "60min")] == 3.31
    assert claims[("mae-mdgformer-pems-bay", "60min")] == 1.82
    assert claims[("ablation-static-graph", "metr-la-60min")] == 3.46
    assert claims[("missing-ours", "20pct")] == 3.91
    assert claims[("params-ours", "experiment")] == 3.18
    assert claims[("inference-ours", "experiment")] == 10.6
    assert "不得声称达到 SOTA" in academic["prohibitions"]


def test_exporter_materializes_fifteen_locked_reviewable_json_files(
    tmp_path: Path,
) -> None:
    output = tmp_path / "briefs"
    completed = subprocess.run(
        [
            sys.executable,
            str(EXPORTER),
            "--output-dir",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    report = json.loads(completed.stdout)
    assert report["status"] == "PASS"
    assert report["count"] == 15
    exported = sorted(output.glob("*.project-brief-pack.v1.json"))
    assert len(exported) == 15
    for path in exported:
        prepare_formal_brief(json.loads(path.read_text(encoding="utf-8")))

    refused = subprocess.run(
        [
            sys.executable,
            str(EXPORTER),
            "--output-dir",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert refused.returncode == 2
    assert json.loads(refused.stdout)["code"] == "OUTPUT_EXISTS"
