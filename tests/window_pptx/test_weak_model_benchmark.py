from __future__ import annotations

import json
import base64
import hashlib
import subprocess
import sys
import zipfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
BENCHMARK_ROOT = SKILL_ROOT / "benchmarks" / "v5"
BENCHMARK_RUNNER = SKILL_ROOT / "scripts" / "run_window_pptx_benchmark.py"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import run_window_pptx_benchmark as benchmark_runner  # noqa: E402

from window_pptx.benchmark import (  # noqa: E402
    _numeric_claims,
    aggregate_scorecards,
    build_benchmark_fact_store,
    build_blind_review_packet,
    build_trial_manifest,
    build_trial_prompt,
    canonical_sha256,
    digest_artifact,
    evaluate_trial_evidence,
    evaluate_trial_response,
    finalize_portable_trial_scorecard,
    load_benchmark_spec,
    load_blind_review_score_sheet,
    parse_opencode_events,
    run_opencode_response,
    verify_artifact_digest,
)
from window_pptx.deck_plan import CONTENT_KINDS  # noqa: E402
from window_pptx.fingerprints import validate_fingerprint_components  # noqa: E402
from window_pptx.registry import resolve_archetype  # noqa: E402
from window_pptx.weak_model import load_narrative_rules  # noqa: E402


EXPECTED_SCENARIOS = {
    "business-report",
    "project-proposal",
    "product-launch",
    "market-analysis",
    "sales-proposal",
    "investor-pitch",
    "annual-review",
    "strategic-plan",
    "data-analysis",
    "research-report",
    "training",
    "brand-introduction",
    "project-kickoff",
    "operations-review",
    "ecommerce-marketing",
}


def valid_response_for(scenario: object) -> str:
    facts = scenario.facts  # type: ignore[attr-defined]
    items = [fact.text for fact in facts]
    return json.dumps(
        {
            "schema_version": "1.0",
            "project": {
                "title": scenario.title,  # type: ignore[attr-defined]
                "scenario": scenario.id,  # type: ignore[attr-defined]
                "audience": scenario.audience,  # type: ignore[attr-defined]
                "objective": scenario.objective,  # type: ignore[attr-defined]
                "language": scenario.language,  # type: ignore[attr-defined]
            },
            "content": [
                {
                    "id": "evidence",
                    "kind": "bullets",
                    "title": "Evidence",
                    "items": items,
                },
                {
                    "id": "recommendation",
                    "kind": "recommendation",
                    "title": "Recommendation",
                    "items": list(scenario.required_beats),  # type: ignore[attr-defined]
                },
            ],
            "preferences": {
                "density": "balanced",
                "tone": "professional",
                "motion": "off",
            },
        },
        ensure_ascii=False,
    )


def valid_brief_response_for(scenario: object) -> str:
    critical_beat = load_narrative_rules()[scenario.id][0]  # type: ignore[attr-defined]
    archetype = resolve_archetype(scenario.id)  # type: ignore[attr-defined]
    required_beats = [
        str(beat).casefold().replace(" ", "-")
        for beat in scenario.required_beats  # type: ignore[attr-defined]
        if str(beat).casefold().replace(" ", "-") in archetype.sections
    ]
    beat_sequence = [
        critical_beat,
        *[
            beat
            for beat in (*required_beats, *archetype.sections)
            if beat not in {"cover", "agenda", "closing", critical_beat}
        ],
    ]
    beat_sequence = list(dict.fromkeys(beat_sequence))
    preferred_forms = [
        form
        for form in scenario.expected_forms  # type: ignore[attr-defined]
        if form in CONTENT_KINDS
    ]
    groups = []
    for index, fact in enumerate(scenario.facts):  # type: ignore[attr-defined]
        group = {
            "id": f"evidence-{index + 1}",
            "fact_refs": [fact.id],
            "beat_hint": beat_sequence[index % len(beat_sequence)],
            "semantic_hint": (
                preferred_forms[index % len(preferred_forms)]
                if preferred_forms
                else "statement"
            ),
            "importance": "critical" if index == 0 else "normal",
        }
        groups.append(group)
    return json.dumps(
        {
            "schema_version": "1.0",
            "scenario_id": scenario.id,  # type: ignore[attr-defined]
            "groups": groups,
            "preferences": {
                "density": "balanced",
                "tone": "professional",
                "motion": "off",
            },
        },
        ensure_ascii=False,
    )


def valid_fingerprint_for(spec: object, manifest: object) -> dict[str, object]:
    placeholder = canonical_sha256("benchmark-fixture")
    return {
        "git_commit": "0" * 40,
        "dirty_state": False,
        "engine_sha256": placeholder,
        "registry_bundle_sha256": placeholder,
        "schemas_sha256": placeholder,
        "skill_sha256": placeholder,
        "corpus_sha256": spec.corpus_sha256,  # type: ignore[attr-defined]
        "protocol_sha256": spec.protocol_sha256,  # type: ignore[attr-defined]
        "prompt_sha256": canonical_sha256(
            {
                trial.trial_id: trial.prompt_sha256
                for trial in manifest.trials  # type: ignore[attr-defined]
            }
        ),
        "thresholds_sha256": canonical_sha256(  # type: ignore[attr-defined]
            spec.protocol.thresholds
        ),
        "dependencies_sha256": placeholder,
        "model_provider_sha256": placeholder,
        "environment_sha256": placeholder,
        "font_inventory_sha256": placeholder,
        "powerpoint_build_sha256": placeholder,
        "asset_manifest_sha256": placeholder,
        "evidence_generation": "post-huashu",
    }


def fingerprint_components_for(spec: object) -> dict[str, object]:
    return {
        "dependencies": {"python": "3.12.0", "packages": {}},
        "model_provider": {
            "opencode_version": "1.0.0",
            "models": [model.id for model in spec.protocol.models],  # type: ignore[attr-defined]
        },
        "environment": {
            "system": "Windows",
            "release": "11",
            "locale": "en-US",
        },
        "font_inventory": {"fonts": ["Arial"]},
        "powerpoint_build": {"version": "16.0.18025.20160"},
        "asset_manifest": {"bindings": {}},
    }


def component_bound_fingerprint_for(
    spec: object,
    manifest: object,
) -> tuple[dict[str, object], dict[str, object]]:
    components = fingerprint_components_for(spec)
    fingerprint = valid_fingerprint_for(spec, manifest)
    for component, field in {
        "dependencies": "dependencies_sha256",
        "model_provider": "model_provider_sha256",
        "environment": "environment_sha256",
        "font_inventory": "font_inventory_sha256",
        "powerpoint_build": "powerpoint_build_sha256",
        "asset_manifest": "asset_manifest_sha256",
    }.items():
        fingerprint[field] = canonical_sha256(components[component])
    return fingerprint, components


def review_ready_score(score: object, artifact_root: Path) -> object:
    trial_dir = artifact_root / "trials" / score.trial_id  # type: ignore[attr-defined]
    trial_dir.mkdir(parents=True, exist_ok=True)
    deck_path = trial_dir / "delivery.pptx"
    with zipfile.ZipFile(deck_path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("_rels/.rels", "<Relationships/>")
        archive.writestr("ppt/presentation.xml", "<p:presentation/>")
    preview_path = trial_dir / "portable-proof" / "slide-001.png"
    preview_path.parent.mkdir()
    preview_path.write_bytes(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
    )
    contact_sheet = trial_dir / "contact-sheet.png"
    contact_sheet.write_bytes(preview_path.read_bytes())
    asset_png = trial_dir / "asset.png"
    asset_png.write_bytes(preview_path.read_bytes())
    return replace(
        score,
        artifact_digests=(
            *score.artifact_digests,  # type: ignore[attr-defined]
            digest_artifact(deck_path, root=artifact_root),
            digest_artifact(preview_path, root=artifact_root),
            digest_artifact(contact_sheet, root=artifact_root),
            digest_artifact(asset_png, root=artifact_root),
        ),
    )


def write_trial_inventory(trial_dir: Path, score: object) -> None:
    score_path = trial_dir / "scorecard.json"
    score_path.write_text(
        json.dumps(score.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",  # type: ignore[attr-defined]
        encoding="utf-8",
    )
    rows = []
    for path in sorted(
        (item for item in trial_dir.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(trial_dir).as_posix(),
    ):
        if path.name == "sha256-inventory.json":
            continue
        payload = path.read_bytes()
        rows.append(
            {
                "relative_path": path.relative_to(trial_dir).as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
            }
        )
    (trial_dir / "sha256-inventory.json").write_text(
        json.dumps(
            {"schema_version": "1.0", "files": rows},
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_resumable_trial(
    output_dir: Path,
    spec: object,
    manifest: object,
    trial: object,
    response: str,
) -> object:
    output_dir.mkdir(parents=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(
            manifest.to_dict(),  # type: ignore[attr-defined]
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    evaluation = evaluate_trial_evidence(  # type: ignore[arg-type]
        spec,
        trial,
        response,
        installed_fonts={"Arial"},
    )
    trial_dir = output_dir / "trials" / trial.trial_id  # type: ignore[attr-defined]
    trial_dir.mkdir(parents=True)
    (trial_dir / "prompt.txt").write_text(
        build_trial_prompt(spec, trial),  # type: ignore[arg-type]
        encoding="utf-8",
    )
    (trial_dir / "provider-events.jsonl").write_text("", encoding="utf-8")
    (trial_dir / "provider-stderr.txt").write_text("", encoding="utf-8")
    (trial_dir / "provider-metadata.json").write_text(
        json.dumps(
            {
                "trial_identity": {
                    "trial_id": trial.trial_id,  # type: ignore[attr-defined]
                    "scenario_id": trial.scenario_id,  # type: ignore[attr-defined]
                    "arm_id": trial.arm_id,  # type: ignore[attr-defined]
                    "model_id": trial.model_id,  # type: ignore[attr-defined]
                    "repeat_index": trial.repeat_index,  # type: ignore[attr-defined]
                },
                "provider": {"status": "received"},
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (trial_dir / "response.txt").write_text(response, encoding="utf-8")
    for name, document in evaluation.documents:
        (trial_dir / name).write_text(
            json.dumps(document, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    artifact_digests = tuple(
        digest_artifact(path, root=output_dir)
        for path in sorted(
            (item for item in trial_dir.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(trial_dir).as_posix(),
        )
    )
    score = replace(evaluation.scorecard, artifact_digests=artifact_digests)
    write_trial_inventory(trial_dir, score)
    return score


def stub_benchmark_runner_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = {
        "node": {"executable": "node"},
        "libreoffice": {"executable": "soffice"},
        "poppler": {
            "pdfinfo_executable": "pdfinfo",
            "pdftoppm_executable": "pdftoppm",
        },
    }
    monkeypatch.setattr(
        benchmark_runner,
        "collect_portable_runtime_manifest",
        lambda **_kwargs: runtime,
    )
    monkeypatch.setattr(
        benchmark_runner,
        "discover_installed_fonts",
        lambda: {"Arial"},
    )
    monkeypatch.setattr(
        benchmark_runner,
        "collect_font_inventory_manifest",
        lambda fonts: {"fonts": sorted(fonts)},
    )
    monkeypatch.setattr(
        benchmark_runner,
        "PptxGenJSRenderer",
        lambda **_kwargs: object(),
    )
    monkeypatch.setattr(
        benchmark_runner,
        "LibreOfficeVerifier",
        lambda **_kwargs: object(),
    )

    def provider_must_not_run(**_kwargs: object) -> object:
        raise AssertionError("resume invoked the provider")

    monkeypatch.setattr(
        benchmark_runner,
        "run_opencode_response",
        provider_must_not_run,
    )


def test_frozen_corpus_covers_exactly_fifteen_required_business_scenarios() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)

    assert spec.schema_version == "1.0"
    assert {scenario.id for scenario in spec.scenarios} == EXPECTED_SCENARIOS
    assert len(spec.scenarios) == 15
    assert all(scenario.expected_archetype == scenario.id for scenario in spec.scenarios)
    assert all(len(scenario.facts) >= 3 for scenario in spec.scenarios)
    assert all(scenario.required_beats for scenario in spec.scenarios)
    assert all(scenario.expected_forms for scenario in spec.scenarios)
    assert all(scenario.slide_count_min >= 5 for scenario in spec.scenarios)


def test_protocol_freezes_three_arms_two_ordinary_models_two_repeats() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)

    assert tuple(arm.id for arm in spec.protocol.arms) == (
        "unassisted-json",
        "governed-plan",
        "full-v5",
    )
    assert len(spec.protocol.models) == 2
    assert all(model.ordinary is True for model in spec.protocol.models)
    assert spec.protocol.repeats == 2
    assert spec.protocol.seed == 20260720
    assert spec.protocol.thresholds["full_v5_plan_validity"] == 0.95


def test_trial_manifest_is_canonical_deterministic_and_complete() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)

    first = build_trial_manifest(spec)
    second = build_trial_manifest(spec)

    assert first == second
    assert len(first.trials) == 180
    assert len({trial.trial_id for trial in first.trials}) == 180
    assert all(trial.status == "planned" for trial in first.trials)
    assert all(len(trial.input_sha256) == 64 for trial in first.trials)
    assert canonical_sha256(first.to_dict()) == canonical_sha256(second.to_dict())
    counts = {
        arm_id: sum(trial.arm_id == arm_id for trial in first.trials)
        for arm_id in ("unassisted-json", "governed-plan", "full-v5")
    }
    assert counts == {
        "unassisted-json": 60,
        "governed-plan": 60,
        "full-v5": 60,
    }


def test_canonical_hash_ignores_object_key_order_but_not_value_changes() -> None:
    assert canonical_sha256({"b": 2, "a": 1}) == canonical_sha256(
        {"a": 1, "b": 2}
    )
    assert canonical_sha256({"a": 1}) != canonical_sha256({"a": 2})


def test_real_response_evaluation_preserves_raw_hash_without_fake_delivery_credit() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    scenario = spec.scenarios[0]
    trial = next(
        item
        for item in manifest.trials
        if item.scenario_id == scenario.id and item.arm_id == "full-v5"
    )
    raw_response = valid_brief_response_for(scenario)

    score = evaluate_trial_response(spec, trial, raw_response)

    assert score.status == "evaluated"
    assert score.raw_response_sha256 == canonical_sha256(raw_response)
    assert score.metrics["response_json_valid"] == 1.0
    assert score.metrics["deck_plan_valid"] == 1.0
    assert score.metrics["fact_retention"] == 1.0
    assert score.metrics["prohibited_claim_safety"] == 1.0
    assert score.metrics["compile_success"] == 1.0
    assert score.metrics["hard_gate_pass"] == 0.0
    assert score.metrics["native_editable_coverage"] == 0.0
    assert score.quality_report_sha256 is None
    assert score.composite is not None


def test_benchmark_fact_store_adds_exact_structure_without_design_overrides() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenario_by_id("business-report")

    fact_store = build_benchmark_fact_store(scenario)
    facts_by_id = {item["id"]: item for item in fact_store["facts"]}

    assert all("recommended_beat" not in item for item in fact_store["facts"])
    assert all("recommended_semantic" not in item for item in fact_store["facts"])
    assert facts_by_id["br-revenue"]["value"] == 48.2
    assert facts_by_id["br-revenue"]["unit"] == "million dollars"
    assert facts_by_id["br-margin"]["value"] == 41
    assert facts_by_id["br-margin"]["unit"] == "percent"
    assert facts_by_id["br-priorities"]["kind"] == "instruction"
    assert "value" not in facts_by_id["br-priorities"]

    data_facts = {
        item["id"]: item
        for item in build_benchmark_fact_store(
            spec.scenario_by_id("data-analysis")
        )["facts"]
    }
    assert data_facts["da-sample"]["value"] == 42180
    assert data_facts["da-sample"]["unit"] == "subscriptions"

    product_facts = {
        item["id"]: item
        for item in build_benchmark_fact_store(
            spec.scenario_by_id("product-launch")
        )["facts"]
    }
    assert product_facts["pl-fragmentation"]["kind"] == "metric"
    assert product_facts["pl-fragmentation"]["value"] == "Sixty-four"
    assert product_facts["pl-fragmentation"]["unit"] == "percent"
    assert product_facts["pl-cohort"]["value"] == 40
    assert product_facts["pl-cohort"]["unit"] == "customer teams"


def test_full_v5_preserves_valid_model_grouping_when_facts_have_no_design_override() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenario_by_id("business-report")
    trial = next(
        item
        for item in build_trial_manifest(spec).trials
        if item.scenario_id == scenario.id and item.arm_id == "full-v5"
    )
    response = json.dumps(
        {
            "schema_version": "1.0",
            "scenario_id": "business-report",
            "groups": [
                {
                    "id": "summary",
                    "fact_refs": ["br-revenue"],
                    "beat_hint": "executive-summary",
                    "semantic_hint": "metrics",
                    "importance": "high",
                },
                {
                    "id": "performance",
                    "fact_refs": ["br-margin", "br-churn"],
                    "beat_hint": "performance",
                    "semantic_hint": "metrics",
                    "importance": "high",
                },
                {
                    "id": "risk",
                    "fact_refs": ["br-backlog"],
                    "beat_hint": "risks",
                    "semantic_hint": "risk",
                    "importance": "high",
                },
                {
                    "id": "action",
                    "fact_refs": ["br-priorities"],
                    "beat_hint": "recommendations",
                    "semantic_hint": "recommendation",
                    "importance": "critical",
                },
            ],
            "preferences": {
                "density": "balanced",
                "tone": "professional",
                "motion": "off",
            },
        }
    )

    evaluation = evaluate_trial_evidence(
        spec,
        trial,
        response,
        installed_fonts={"Arial"},
    )
    narrative = dict(evaluation.documents)["narrative-plan.json"]
    deck_plan = dict(evaluation.documents)["deck-plan.json"]
    content = [slide for slide in narrative["slides"] if not slide["structural"]]

    assert [(slide["id"], slide["role"], slide["fact_refs"]) for slide in content] == [
        ("summary", "executive-summary", ["br-revenue"]),
        ("performance-detail-1", "performance", ["br-margin"]),
        ("performance-detail-2", "performance", ["br-churn"]),
        ("risk", "risks", ["br-backlog"]),
        ("action", "recommendations", ["br-priorities"]),
    ]
    assert narrative["coverage"]["slide_floor_splits"] == 1
    assert narrative["coverage"]["slide_floor_satisfied"] is True
    deck_by_id = {slide["id"]: slide for slide in deck_plan["slides"]}
    assert len(deck_by_id["summary"]["blocks"][0]["items"]) == 2
    assert deck_by_id["performance-detail-1"]["blocks"][0]["kind"] == "comparison"
    assert deck_by_id["performance-detail-1"]["blocks"][0]["items"][:2] == [
        {"label": "Before", "value": 44, "unit": "percent"},
        {"label": "After", "value": 41, "unit": "percent"},
    ]
    assert deck_by_id["risk"]["blocks"][0]["kind"] == "comparison"
    assert deck_by_id["action"]["blocks"][0]["items"] == [
        {"label": "Priority 1", "text": "onboarding capacity"},
        {"label": "Priority 2", "text": "gross margin recovery"},
    ]


def test_portable_finalization_uses_real_backend_and_quality_metrics() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenarios[0]
    trial = next(
        item
        for item in build_trial_manifest(spec).trials
        if item.scenario_id == scenario.id and item.arm_id == "full-v5"
    )
    evaluation = evaluate_trial_evidence(
        spec,
        trial,
        valid_brief_response_for(scenario),
        installed_fonts={"Arial"},
    )
    quality_document = {
        "schema_version": "2.0",
        "findings": [],
        "hard_gate_failures": [],
        "weighted_defect_score": 0,
        "passed": True,
        "transaction_status": "transaction-promoted",
    }
    quality = SimpleNamespace(
        passed=True,
        hard_gate_failures=(),
        to_dict=lambda: quality_document,
    )
    result = SimpleNamespace(
        render_report=SimpleNamespace(
            planned_object_count=20,
            native_editable_count=18,
            diagram_child_count=0,
        ),
        verification=SimpleNamespace(quality=quality),
        candidate_result=SimpleNamespace(promoted=True),
    )

    finalized = finalize_portable_trial_scorecard(spec, evaluation, result)

    assert finalized.status == "evaluated"
    assert finalized.metrics["native_editable_coverage"] == pytest.approx(0.9)
    assert finalized.metrics["hard_gate_pass"] == 1.0
    assert finalized.quality_report_sha256 == canonical_sha256(quality_document)
    assert finalized.composite is not None


def test_portable_finalization_counts_editable_diagram_children_in_denominator() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenarios[0]
    trial = next(
        item
        for item in build_trial_manifest(spec).trials
        if item.scenario_id == scenario.id and item.arm_id == "full-v5"
    )
    evaluation = evaluate_trial_evidence(
        spec,
        trial,
        valid_brief_response_for(scenario),
        installed_fonts={"Arial"},
    )
    quality_document = {
        "schema_version": "2.0",
        "findings": [],
        "hard_gate_failures": [],
        "weighted_defect_score": 0,
        "passed": True,
        "transaction_status": "transaction-promoted",
    }
    quality = SimpleNamespace(
        passed=True,
        hard_gate_failures=(),
        to_dict=lambda: quality_document,
    )
    result = SimpleNamespace(
        render_report=SimpleNamespace(
            planned_object_count=26,
            native_editable_count=27,
            diagram_child_count=1,
        ),
        verification=SimpleNamespace(quality=quality),
        candidate_result=SimpleNamespace(promoted=True),
    )

    finalized = finalize_portable_trial_scorecard(spec, evaluation, result)

    assert finalized.metrics["native_editable_coverage"] == 1.0


def test_invalid_and_unavailable_outputs_are_distinct_and_never_imputed() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    trial = build_trial_manifest(spec).trials[0]

    invalid = evaluate_trial_response(spec, trial, "not json")
    unavailable = evaluate_trial_response(spec, trial, None)

    assert invalid.status == "invalid"
    assert invalid.failure_code == "RESPONSE_JSON_INVALID"
    assert invalid.metrics["response_json_valid"] == 0.0
    assert invalid.composite == 0.0
    assert unavailable.status == "unavailable"
    assert unavailable.failure_code == "PROVIDER_UNAVAILABLE"
    assert unavailable.metrics == {}
    assert unavailable.composite is None
    assert unavailable.raw_response_sha256 is None


def test_prohibited_claims_reduce_safety_without_post_editing_response() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenarios[0]
    trial = next(
        item
        for item in build_trial_manifest(spec).trials
        if item.scenario_id == scenario.id and item.arm_id == "governed-plan"
    )
    payload = json.loads(valid_response_for(scenario))
    payload["content"][0]["items"].append(scenario.prohibited_claims[0])
    raw = json.dumps(payload, ensure_ascii=False)

    score = evaluate_trial_response(spec, trial, raw)

    assert score.raw_response_sha256 == canonical_sha256(raw)
    assert score.metrics["prohibited_claim_safety"] == 0.0
    assert score.violations == (scenario.prohibited_claims[0],)


def test_unsourced_numeric_claim_is_detected_even_when_not_on_prohibited_list() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenarios[0]
    trial = next(
        item
        for item in build_trial_manifest(spec).trials
        if item.scenario_id == scenario.id and item.arm_id == "governed-plan"
    )
    payload = json.loads(valid_response_for(scenario))
    payload["content"][0]["items"].append(
        "Revenue will reach 60 million dollars next quarter."
    )

    score = evaluate_trial_response(
        spec, trial, json.dumps(payload, ensure_ascii=False)
    )

    assert score.metrics["numeric_claim_safety"] == 0.0
    assert "UNSUPPORTED_NUMERIC:60 million" in score.violations


def test_numeric_claim_parser_preserves_decimal_after_json_escaped_newline() -> None:
    claims = _numeric_claims('"Exclusions\\n6.4 percent of records"')

    assert claims == {"6.4 percent"}


def test_prohibited_numeric_claim_is_never_whitelisted_as_scenario_input() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenarios[0]
    trial = next(
        item
        for item in build_trial_manifest(spec).trials
        if item.scenario_id == scenario.id and item.arm_id == "governed-plan"
    )
    payload = json.loads(valid_response_for(scenario))
    prohibited = scenario.prohibited_claims[1]
    payload["content"][0]["items"].append(prohibited)

    score = evaluate_trial_response(
        spec, trial, json.dumps(payload, ensure_ascii=False)
    )

    assert score.metrics["prohibited_claim_safety"] == 0.0
    assert score.metrics["numeric_claim_safety"] == 0.0
    assert prohibited in score.violations
    assert "UNSUPPORTED_NUMERIC:50 percent" in score.violations


def test_fact_retention_normalizes_percent_currency_and_million_abbreviations() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenarios[0]
    trial = next(
        item
        for item in build_trial_manifest(spec).trials
        if item.scenario_id == scenario.id and item.arm_id == "governed-plan"
    )
    raw = valid_response_for(scenario).replace(
        "48.2 million dollars, 12 percent", "$48.2M, 12%"
    ).replace("44 percent", "44%").replace("41 percent", "41%").replace(
        "3.1 percent", "3.1%"
    )

    score = evaluate_trial_response(spec, trial, raw)

    assert score.metrics["fact_retention"] == 1.0


def test_artifact_digest_detects_tampering(tmp_path: Path) -> None:
    artifact = tmp_path / "report.json"
    artifact.write_text('{"passed": true}\n', encoding="utf-8")
    digest = digest_artifact(artifact, root=tmp_path)

    assert verify_artifact_digest(digest, root=tmp_path) is True
    artifact.write_text('{"passed": false}\n', encoding="utf-8")
    assert verify_artifact_digest(digest, root=tmp_path) is False


def test_aggregate_verifies_trial_identity_documents_and_artifact_hashes(
    tmp_path: Path,
) -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    trial = manifest.trials[0]
    scenario = spec.scenario_by_id(trial.scenario_id)
    response = valid_response_for(scenario)
    evaluation = evaluate_trial_evidence(spec, trial, response)
    trial_dir = tmp_path / "trials" / trial.trial_id
    trial_dir.mkdir(parents=True)
    (trial_dir / "prompt.txt").write_text(
        build_trial_prompt(spec, trial), encoding="utf-8"
    )
    (trial_dir / "provider-events.jsonl").write_text("", encoding="utf-8")
    (trial_dir / "provider-stderr.txt").write_text("", encoding="utf-8")
    (trial_dir / "provider-metadata.json").write_text(
        json.dumps(
            {
                "trial_identity": {
                    "trial_id": trial.trial_id,
                    "scenario_id": trial.scenario_id,
                    "arm_id": trial.arm_id,
                    "model_id": trial.model_id,
                    "repeat_index": trial.repeat_index,
                },
                "provider": {"status": "received"},
            }
        ),
        encoding="utf-8",
    )
    (trial_dir / "response.txt").write_text(response, encoding="utf-8")
    for name, document in evaluation.documents:
        (trial_dir / name).write_text(json.dumps(document), encoding="utf-8")
    artifacts = tuple(
        digest_artifact(path, root=tmp_path)
        for path in sorted(trial_dir.iterdir())
    )
    score = replace(evaluation.scorecard, artifact_digests=artifacts)
    write_trial_inventory(trial_dir, score)

    aggregate = aggregate_scorecards(
        spec, manifest, (score,), artifact_root=tmp_path
    )

    assert aggregate.release_status == "incomplete"
    assert aggregate.artifact_hash_coverage == pytest.approx(1 / 180)
    (trial_dir / "render-plan.json").write_text("{}", encoding="utf-8")
    tampered = aggregate_scorecards(
        spec, manifest, (score,), artifact_root=tmp_path
    )
    assert tampered.artifact_hash_coverage == 0.0


def test_blind_review_packet_is_deterministic_and_hides_arm_model_trial_ids() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    scorecards = tuple(
        evaluate_trial_response(
            spec,
            trial,
            valid_response_for(spec.scenario_by_id(trial.scenario_id)),
        )
        for trial in manifest.trials[:6]
    )

    first_packet, first_map = build_blind_review_packet(spec, scorecards)
    second_packet, second_map = build_blind_review_packet(spec, scorecards)

    assert first_packet == second_packet
    assert first_map == second_map
    assert len(first_packet.entries) == 6
    assert first_packet.delivery_evidence_ready is False
    serialized = json.dumps(first_packet.to_dict(), ensure_ascii=False)
    assert "model_id" not in serialized
    assert "arm_id" not in serialized
    assert "trial_id" not in serialized
    assert all(entry.blind_id.startswith("B-") for entry in first_packet.entries)
    assert set(first_map) == {entry.blind_id for entry in first_packet.entries}


def test_aggregate_keeps_missing_trials_in_completeness_and_locks_thresholds() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    scenario = spec.scenarios[0]
    evaluated_trial = next(
        trial
        for trial in manifest.trials
        if trial.scenario_id == scenario.id and trial.arm_id == "full-v5"
    )
    scores = (
        evaluate_trial_response(
            spec, evaluated_trial, valid_brief_response_for(scenario)
        ),
        evaluate_trial_response(spec, manifest.trials[1], None),
    )

    aggregate = aggregate_scorecards(spec, manifest, scores)

    assert aggregate.planned_trials == 180
    assert aggregate.recorded_trials == 2
    assert aggregate.available_trials == 1
    assert aggregate.completeness == pytest.approx(1 / 180)
    assert aggregate.release_status == "incomplete"
    assert aggregate.artifact_hash_coverage == 0.0
    assert aggregate.thresholds_sha256 == canonical_sha256(
        spec.protocol.thresholds
    )


def test_complete_invalid_run_fails_thresholds_and_rejects_placeholder_fingerprints() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    complete = tuple(
        evaluate_trial_response(spec, trial, "not json")
        for trial in manifest.trials
    )

    missing = aggregate_scorecards(spec, manifest, complete)
    valid = valid_fingerprint_for(spec, manifest)
    dirty = {**valid, "dirty_state": True}
    mismatched = {**valid, "protocol_sha256": canonical_sha256("wrong")}

    assert missing.release_status == "threshold-rejected"
    assert missing.fingerprint_status == "missing"
    gates = dict(missing.automatic_gates)
    assert gates["full_v5_plan_validity"] is False
    assert gates["delta_vs_unassisted_points"] is False
    assert gates["delta_vs_governed_plan_points"] is False
    assert gates["artifact_hash_coverage"] is False
    dirty_result = aggregate_scorecards(
        spec, manifest, complete, fingerprints=(dirty,)
    )
    mismatched_result = aggregate_scorecards(
        spec, manifest, complete, fingerprints=(mismatched,)
    )
    placeholder_result = aggregate_scorecards(
        spec, manifest, complete, fingerprints=(valid,)
    )
    assert dirty_result.fingerprint_status == "rejected"
    assert mismatched_result.fingerprint_status == "rejected"
    assert placeholder_result.fingerprint_status == "rejected"
    assert placeholder_result.release_status != "pending-human-review"


def test_aggregate_rejects_scorecard_identity_drift() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    trial = manifest.trials[0]
    score = evaluate_trial_response(spec, trial, "not json")

    with pytest.raises(ValueError, match="identity mismatch"):
        aggregate_scorecards(
            spec,
            manifest,
            (replace(score, model_id="different-provider/model"),),
        )


def test_benchmark_schemas_are_strict_and_accept_manifest_score_and_review() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    scenario = spec.scenarios[0]
    score = evaluate_trial_response(
        spec,
        next(trial for trial in manifest.trials if trial.arm_id == "full-v5"),
        valid_brief_response_for(scenario),
    )
    packet, _mapping = build_blind_review_packet(spec, (score,))
    fingerprint, components = component_bound_fingerprint_for(spec, manifest)
    fingerprint_bundle = {
        "schema_version": "1.0",
        "fingerprints": [fingerprint],
        "components": components,
    }
    run_contract = benchmark_runner._build_formal_run_contract(
        spec,
        manifest,
        fingerprint_bundle,
        benchmark_root=BENCHMARK_ROOT,
        timeout_seconds=benchmark_runner.FORMAL_TIMEOUT_SECONDS,
    )
    documents = (
        (
            "benchmark-corpus.v1.schema.json",
            json.loads((BENCHMARK_ROOT / "scenarios.json").read_text(encoding="utf-8")),
        ),
        (
            "benchmark-protocol.v1.schema.json",
            json.loads((BENCHMARK_ROOT / "protocol.json").read_text(encoding="utf-8")),
        ),
        ("benchmark-manifest.v1.schema.json", manifest.to_dict()),
        ("benchmark-scorecard.v1.schema.json", score.to_dict()),
        ("blind-review.v1.schema.json", packet.to_dict()),
        ("fingerprint-bundle.v1.schema.json", fingerprint_bundle),
        ("benchmark-run-contract.v1.schema.json", run_contract),
    )

    for schema_name, payload in documents:
        schema = json.loads(
            (SKILL_ROOT / "schemas" / schema_name).read_text(encoding="utf-8")
        )
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(payload))
        assert not errors, [error.message for error in errors]

    contract_schema = json.loads(
        (SKILL_ROOT / "schemas" / "benchmark-run-contract.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    diagnostic_contract = {**run_contract, "run_kind": "diagnostic"}
    assert list(
        jsonschema.Draft202012Validator(contract_schema).iter_errors(
            diagnostic_contract
        )
    )


def test_formal_benchmark_freezes_critical_cli_parameters(tmp_path: Path) -> None:
    output_dir = tmp_path / "formal"
    fingerprint_path = tmp_path / "fingerprint.json"
    base = [
        "--output-dir",
        str(output_dir),
        "--run-kind",
        "formal",
        "--fingerprint-json",
        str(fingerprint_path),
    ]
    cases = (
        (
            ["--benchmark-root", str(tmp_path / "other-benchmark")],
            "default --benchmark-root",
        ),
        (["--timeout-seconds", "91"], "--timeout-seconds=90"),
        (["--manifest-only"], "forbids --manifest-only"),
        (
            ["--response-file", str(tmp_path / "response.json")],
            "forbids --response-file",
        ),
    )

    for extra, message in cases:
        with pytest.raises(ValueError, match=message):
            benchmark_runner.main([*base, *extra])


def test_formal_run_contract_resume_requires_the_exact_document(
    tmp_path: Path,
) -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    fingerprint, components = component_bound_fingerprint_for(spec, manifest)
    bundle = {
        "schema_version": "1.0",
        "fingerprints": [fingerprint],
        "components": components,
    }
    contract = benchmark_runner._build_formal_run_contract(
        spec,
        manifest,
        bundle,
        benchmark_root=BENCHMARK_ROOT,
        timeout_seconds=benchmark_runner.FORMAL_TIMEOUT_SECONDS,
    )
    contract_path = tmp_path / benchmark_runner.FORMAL_RUN_CONTRACT_FILENAME
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    benchmark_runner._require_exact_json(
        contract_path,
        contract,
        label="formal run contract",
    )
    changed = {
        **contract,
        "fingerprint_bundle_sha256": canonical_sha256("changed-fingerprint"),
    }
    with pytest.raises(ValueError, match="exact formal run contract"):
        benchmark_runner._require_exact_json(
            contract_path,
            changed,
            label="formal run contract",
        )
    assert json.loads(contract_path.read_text(encoding="utf-8")) == contract

    contract_path.unlink()
    with pytest.raises(ValueError, match="formal run contract is missing"):
        benchmark_runner._require_exact_json(
            contract_path,
            contract,
            label="formal run contract",
        )


def test_diagnostic_resume_cannot_mutate_a_formal_run(tmp_path: Path) -> None:
    output_dir = tmp_path / "formal-run"
    output_dir.mkdir()
    (output_dir / benchmark_runner.FORMAL_RUN_CONTRACT_FILENAME).write_text(
        "{}", encoding="utf-8"
    )

    with pytest.raises(
        ValueError,
        match="diagnostic resume cannot target a formal benchmark run",
    ):
        benchmark_runner.main(
            [
                "--output-dir",
                str(output_dir),
                "--resume",
                "--manifest-only",
            ]
        )


def test_benchmark_runner_requires_and_preserves_the_strict_fingerprint_bundle(
    tmp_path: Path,
) -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    fingerprint, components = component_bound_fingerprint_for(spec, manifest)
    bundle = {
        "schema_version": "1.0",
        "fingerprints": [fingerprint],
        "components": components,
    }
    bundle_path = tmp_path / "input-bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    output_dir = tmp_path / "run"

    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK_RUNNER),
            "--output-dir",
            str(output_dir),
            "--fingerprint-json",
            str(bundle_path),
            "--manifest-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(
        (output_dir / "fingerprint-bundle.json").read_text(encoding="utf-8")
    ) == bundle
    raw_path = tmp_path / "raw-fingerprint.json"
    raw_path.write_text(json.dumps(fingerprint), encoding="utf-8")
    rejected = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK_RUNNER),
            "--output-dir",
            str(tmp_path / "rejected"),
            "--fingerprint-json",
            str(raw_path),
            "--manifest-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode != 0
    assert "fingerprint-bundle.v1" in rejected.stderr


def test_benchmark_runner_resumes_verified_trial_without_provider_invocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    trial = next(
        item
        for item in manifest.trials
        if item.scenario_id == "business-report"
        and item.arm_id == "governed-plan"
        and item.repeat_index == 1
    )
    output_dir = tmp_path / "resume-valid"
    write_resumable_trial(
        output_dir,
        spec,
        manifest,
        trial,
        valid_response_for(spec.scenario_by_id(trial.scenario_id)),
    )
    stub_benchmark_runner_runtime(monkeypatch)

    result = benchmark_runner.main(
        [
            "--output-dir",
            str(output_dir),
            "--scenario",
            trial.scenario_id,
            "--arm",
            trial.arm_id,
            "--model",
            trial.model_id,
            "--repeat",
            str(trial.repeat_index),
            "--resume",
        ]
    )

    assert result == 0
    summary = json.loads(
        (output_dir / "run-summary.json").read_text(encoding="utf-8")
    )
    assert summary["selected_trials"] == 1
    assert summary["evaluated_trials"] == 1
    assert summary["aggregate"]["recorded_trials"] == 1


def test_formal_resume_rejects_diagnostic_trial_import_even_with_matching_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    trial = manifest.trials[0]
    output_dir = tmp_path / "diagnostic-import"
    write_resumable_trial(
        output_dir,
        spec,
        manifest,
        trial,
        valid_response_for(spec.scenario_by_id(trial.scenario_id)),
    )
    runtime = {
        "node": {"executable": "node"},
        "libreoffice": {"executable": "soffice"},
        "poppler": {
            "pdfinfo_executable": "pdfinfo",
            "pdftoppm_executable": "pdftoppm",
        },
    }
    bundle = {
        "schema_version": "1.0",
        "fingerprints": [{"fixture": "formal"}],
        "components": {
            "portable_runtime": runtime,
            "font_inventory": {"fonts": ["Arial"]},
        },
    }
    bundle_path = tmp_path / "formal-fingerprint.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    contract = benchmark_runner._build_formal_run_contract(
        spec,
        manifest,
        bundle,
        benchmark_root=BENCHMARK_ROOT,
        timeout_seconds=benchmark_runner.FORMAL_TIMEOUT_SECONDS,
    )
    (output_dir / "fingerprint-bundle.json").write_text(
        json.dumps(bundle), encoding="utf-8"
    )
    (output_dir / benchmark_runner.FORMAL_RUN_CONTRACT_FILENAME).write_text(
        json.dumps(contract), encoding="utf-8"
    )
    monkeypatch.setattr(
        benchmark_runner,
        "validate_fingerprint_bundle",
        lambda values: dict(tuple(values)[0]),
    )
    monkeypatch.setattr(
        benchmark_runner,
        "validate_fingerprint_components",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        benchmark_runner,
        "validate_benchmark_fingerprint_source",
        lambda *_args, **_kwargs: None,
    )
    stub_benchmark_runner_runtime(monkeypatch)

    with pytest.raises(ValueError, match="not bound to the formal run contract"):
        benchmark_runner.main(
            [
                "--output-dir",
                str(output_dir),
                "--run-kind",
                "formal",
                "--fingerprint-json",
                str(bundle_path),
                "--resume",
            ]
        )


def test_benchmark_runner_resume_rejects_mismatched_scorecard_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    trial = next(
        item
        for item in manifest.trials
        if item.scenario_id == "business-report"
        and item.arm_id == "governed-plan"
        and item.repeat_index == 1
    )
    output_dir = tmp_path / "resume-mismatch"
    score = write_resumable_trial(
        output_dir,
        spec,
        manifest,
        trial,
        valid_response_for(spec.scenario_by_id(trial.scenario_id)),
    )
    trial_dir = output_dir / "trials" / trial.trial_id
    mismatched = replace(score, model_id="opencode/different-model")
    write_trial_inventory(trial_dir, mismatched)
    stub_benchmark_runner_runtime(monkeypatch)

    with pytest.raises(ValueError, match="identity mismatch"):
        benchmark_runner.main(
            [
                "--output-dir",
                str(output_dir),
                "--scenario",
                trial.scenario_id,
                "--arm",
                trial.arm_id,
                "--model",
                trial.model_id,
                "--repeat",
                str(trial.repeat_index),
                "--resume",
            ]
        )


def test_fingerprint_component_manifests_are_typed_and_hash_bound() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    fingerprint, components = component_bound_fingerprint_for(spec, manifest)

    assert validate_fingerprint_components(fingerprint, components) == components

    tampered = {
        **components,
        "environment": {**components["environment"], "release": "12"},
    }
    with pytest.raises(ValueError, match="hash mismatch: environment"):
        validate_fingerprint_components(fingerprint, tampered)

    arbitrary_hash = {**fingerprint, "dependencies_sha256": "a" * 64}
    with pytest.raises(ValueError, match="hash mismatch: dependencies"):
        validate_fingerprint_components(arbitrary_hash, components)

    unavailable = {
        **components,
        "powerpoint_build": {"version": "NOT_RUN"},
    }
    unavailable_fingerprint = {
        **fingerprint,
        "powerpoint_build_sha256": canonical_sha256(
            unavailable["powerpoint_build"]
        ),
    }
    with pytest.raises(ValueError, match="placeholder evidence"):
        validate_fingerprint_components(unavailable_fingerprint, unavailable)


def test_evaluated_full_v5_trial_exposes_hash_matched_audit_documents() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenarios[0]
    trial = next(
        item
        for item in build_trial_manifest(spec).trials
        if item.scenario_id == scenario.id and item.arm_id == "full-v5"
    )

    evaluation = evaluate_trial_evidence(
        spec, trial, valid_brief_response_for(scenario)
    )
    documents = dict(evaluation.documents)

    assert evaluation.scorecard.status == "evaluated"
    assert set(documents) == {
        "fact-store.json",
        "brief-plan.json",
        "narrative-plan.json",
        "direction-decision.json",
        "generation-manifest.json",
        "repair-log.v2.json",
        "deck-plan.json",
        "compiled-plan.json",
        "render-plan.json",
    }
    assert canonical_sha256(documents["deck-plan.json"]) == evaluation.scorecard.deck_plan_sha256
    assert canonical_sha256(documents["compiled-plan.json"]) == evaluation.scorecard.compiled_sha256
    assert canonical_sha256(documents["render-plan.json"]) == evaluation.scorecard.render_plan_sha256
    assert evaluation.scorecard.quality_report_sha256 is None


def test_completed_blind_review_sheet_requires_every_exact_rubric_score(
    tmp_path: Path,
) -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenarios[0]
    trial = next(
        item
        for item in build_trial_manifest(spec).trials
        if item.scenario_id == scenario.id and item.arm_id == "full-v5"
    )
    score = review_ready_score(evaluate_trial_response(
        spec, trial, valid_brief_response_for(scenario)
    ), tmp_path)
    packet, _mapping = build_blind_review_packet(
        spec,
        (score,),
        artifact_root=tmp_path,
        review_root=tmp_path / "blind-review",
    )
    assert packet.delivery_evidence_ready is True
    assert {item.kind for item in packet.entries[0].artifacts} == {
        "editable-pptx",
        "slide-preview",
    }
    assert all(
        (tmp_path / "blind-review" / item.review_path).is_file()
        for item in packet.entries[0].artifacts
    )
    entry = packet.entries[0]
    payload = {
        "schema_version": "1.0",
        "benchmark_id": packet.benchmark_id,
        "packet_sha256": packet.packet_sha256,
        "reviewer_id": "R-001",
        "reviews": [
            {
                "blind_id": entry.blind_id,
                "evidence_sha256": entry.evidence_sha256,
                "scores": {rubric: 4 for rubric in entry.rubric},
                "notes": None,
            }
        ],
    }

    sheet = load_blind_review_score_sheet(packet, payload)

    assert sheet.reviewer_id == "R-001"
    assert sheet.reviews[0].mean_score == 4.0
    schema = json.loads(
        (SKILL_ROOT / "schemas" / "blind-review-score.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema = pytest.importorskip("jsonschema")
    assert not list(jsonschema.Draft202012Validator(schema).iter_errors(sheet.to_dict()))


def test_blind_review_sheet_rejects_missing_entries_and_extra_rubrics(
    tmp_path: Path,
) -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    manifest = build_trial_manifest(spec)
    scorecards = tuple(
        evaluate_trial_response(
            spec,
            trial,
            valid_response_for(spec.scenario_by_id(trial.scenario_id)),
        )
        for trial in manifest.trials[:2]
    )
    scorecards = tuple(review_ready_score(score, tmp_path) for score in scorecards)
    packet, _mapping = build_blind_review_packet(
        spec,
        scorecards,
        artifact_root=tmp_path,
        review_root=tmp_path / "blind-review",
    )
    entry = packet.entries[0]
    payload = {
        "schema_version": "1.0",
        "benchmark_id": packet.benchmark_id,
        "packet_sha256": packet.packet_sha256,
        "reviewer_id": "R-002",
        "reviews": [
            {
                "blind_id": entry.blind_id,
                "evidence_sha256": entry.evidence_sha256,
                "scores": {**{rubric: 4 for rubric in entry.rubric}, "overall": 5},
                "notes": "complete only after viewing rendered evidence",
            }
        ],
    }

    with pytest.raises(ValueError, match="blind review entries mismatch"):
        load_blind_review_score_sheet(packet, payload)


def test_blind_review_scoring_is_blocked_without_verified_delivery_files() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenarios[0]
    trial = build_trial_manifest(spec).trials[0]
    score = evaluate_trial_response(spec, trial, valid_response_for(scenario))
    packet, _mapping = build_blind_review_packet(spec, (score,))

    assert packet.delivery_evidence_ready is False
    with pytest.raises(ValueError, match="editable PPTX and PNG evidence"):
        load_blind_review_score_sheet(packet, {})


def test_opencode_event_parser_extracts_only_assistant_text() -> None:
    stdout = "\n".join(
        [
            json.dumps({"type": "step_start"}),
            json.dumps(
                {
                    "type": "text",
                    "part": {"type": "text", "text": '{"schema_version":"1.0"}'},
                }
            ),
            json.dumps({"type": "step_finish"}),
        ]
    )

    assert parse_opencode_events(stdout) == '{"schema_version":"1.0"}'


def test_full_v5_response_parser_accepts_only_exact_json_or_a_whole_json_fence() -> None:
    spec = load_benchmark_spec(BENCHMARK_ROOT)
    scenario = spec.scenarios[0]
    trial = next(
        item
        for item in build_trial_manifest(spec).trials
        if item.scenario_id == scenario.id and item.arm_id == "full-v5"
    )
    fenced = f"```json\n{valid_brief_response_for(scenario)}\n```"
    trailing = fenced + "\nVerification summary"

    accepted = evaluate_trial_response(spec, trial, fenced)
    rejected = evaluate_trial_response(spec, trial, trailing)
    wrong_root = evaluate_trial_response(spec, trial, "[]")

    assert accepted.status == "evaluated"
    assert accepted.metrics["response_json_valid"] == 1.0
    assert rejected.status == "invalid"
    assert rejected.failure_code == "RESPONSE_JSON_INVALID"
    assert rejected.metrics["response_json_valid"] == 0.0
    assert wrong_root.status == "invalid"
    assert wrong_root.failure_code == "RESPONSE_JSON_INVALID"


def test_opencode_runner_records_provider_failure_without_inventing_output() -> None:
    calls: list[list[str]] = []

    def fake_runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="provider down")

    result = run_opencode_response(
        model_id="opencode/model-free",
        prompt="Return JSON",
        directory=REPO_ROOT,
        timeout_seconds=30,
        runner=fake_runner,
    )

    assert calls and calls[0][0] == "opencode" and "run" in calls[0]
    assert "--pure" in calls[0]
    assert result.status == "unavailable"
    assert result.response is None
    assert result.exit_code == 1
    assert result.stdout_sha256 == canonical_sha256("")
    assert result.stderr_sha256 == canonical_sha256("provider down")


def test_opencode_runner_returns_exact_text_event_response() -> None:
    response = '{"schema_version":"1.0"}'
    stdout = json.dumps(
        {"type": "text", "part": {"type": "text", "text": response}}
    )

    def fake_runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    result = run_opencode_response(
        model_id="opencode/model-free",
        prompt="Return JSON",
        directory=REPO_ROOT,
        timeout_seconds=30,
        runner=fake_runner,
    )

    assert result.status == "received"
    assert result.response == response
    assert result.response_sha256 == canonical_sha256(response)
