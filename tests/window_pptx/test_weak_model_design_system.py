from __future__ import annotations

import copy
import json
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


from window_pptx.brand import (  # noqa: E402
    BrandSpecError,
    assess_brand_assets,
    font_inventory_digest,
    validate_brand_spec,
)
from window_pptx.directions import (  # noqa: E402
    ART_DIRECTION_IDS,
    DirectionContext,
    load_art_directions,
    select_art_directions,
    select_proof_slide_ids,
)
from window_pptx.fingerprints import (  # noqa: E402
    canonical_sha256,
    validate_fingerprint_bundle,
)
from window_pptx.layouts import (  # noqa: E402
    layout_geometry_signature,
    load_layout_registry,
)
from window_pptx.quality_v2 import (  # noqa: E402
    QualityFindingV2,
    build_quality_report_v2,
    defect_vector,
    execute_two_stage_repair,
)
from window_pptx.weak_model import (  # noqa: E402
    WeakModelValidationError,
    compile_brief_plan,
    normalize_brief_plan,
    validate_brief_plan,
    validate_fact_store,
)


def fact_store_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "project": {
            "title": "Northstar Q2 Review",
            "objective": "Select the two Q3 priorities.",
            "audience": "executive committee",
            "language": "en-US",
        },
        "sources": [
            {
                "id": "request",
                "kind": "request",
                "locator": "REQUEST.md",
                "sha256": "a" * 64,
            }
        ],
        "facts": [
            {
                "id": "revenue",
                "kind": "metric",
                "text": "Q2 revenue was 48.2 million dollars, 12 percent above Q1.",
                "language": "en-US",
                "source_id": "request",
                "locator": "line:1",
                "required": True,
                "value": 48.2,
                "unit": "million dollars",
                "claim_key": "revenue",
                "time_scope": "Q2",
            },
            {
                "id": "margin",
                "kind": "metric",
                "text": "Gross margin declined from 44 percent to 41 percent.",
                "language": "en-US",
                "source_id": "request",
                "locator": "line:2",
                "required": True,
                "value": 41,
                "unit": "percent",
                "claim_key": "gross-margin",
                "time_scope": "Q2",
            },
            {
                "id": "churn",
                "kind": "metric",
                "text": "Enterprise churn improved to 3.1 percent.",
                "language": "en-US",
                "source_id": "request",
                "locator": "line:3",
                "required": True,
                "value": 3.1,
                "unit": "percent",
                "claim_key": "enterprise-churn",
                "time_scope": "Q2",
            },
        ],
    }


def brief_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "scenario_id": "business-report",
        "groups": [
            {
                "id": "performance",
                "fact_refs": ["revenue", "margin"],
                "beat_hint": "performance",
                "semantic_hint": "comparison",
                "importance": "critical",
            },
            {
                "id": "insight",
                "fact_refs": ["churn"],
                "beat_hint": "insights",
                "semantic_hint": "metrics",
                "importance": "high",
            },
        ],
        "preferences": {
            "tone": "professional",
            "density": "balanced",
            "audience_mode": "executive",
            "motion": "off",
        },
    }


def test_fact_store_is_immutable_and_digest_is_stable() -> None:
    payload = fact_store_payload()
    store = validate_fact_store(payload)
    assert store.fact("revenue").text.startswith("Q2 revenue")
    assert store.digest == validate_fact_store(copy.deepcopy(payload)).digest
    with pytest.raises(FrozenInstanceError):
        store.facts[0].text = "changed"  # type: ignore[misc]


def test_fact_store_rejects_conflicting_active_claims() -> None:
    payload = fact_store_payload()
    conflicting = copy.deepcopy(payload["facts"][0])  # type: ignore[index]
    conflicting["id"] = "revenue-conflict"
    conflicting["value"] = 99
    payload["facts"].append(conflicting)  # type: ignore[union-attr]
    with pytest.raises(WeakModelValidationError, match="FACT_CONFLICT"):
        validate_fact_store(payload)


def test_brief_normalizer_repairs_only_harmless_shape_errors() -> None:
    raw = "```json\n" + json.dumps(
        {
            **brief_payload(),
            "schema_version": "v1",
            "scenario_id": "商业汇报",
            "groups": [
                {
                    "id": "Executive Performance",
                    "fact_refs": ["revenue", "margin", "churn"],
                    "beat_hint": "Executive Summary",
                    "semantic_hint": "METRICS",
                }
            ],
        }
    ) + "\n```"
    normalized, trace = normalize_brief_plan(raw)
    assert normalized["schema_version"] == "1.0"
    assert normalized["scenario_id"] == "business-report"
    assert normalized["groups"][0]["id"] == "executive-performance"
    assert normalized["groups"][0]["beat_hint"] == "executive-summary"
    assert normalized["groups"][0]["semantic_hint"] == "metrics"
    assert trace.changes


@pytest.mark.parametrize("field", ["title", "layout_id", "font", "color", "x"])
def test_brief_plan_rejects_free_text_and_raw_design(field: str) -> None:
    payload = brief_payload()
    payload["groups"][0][field] = "invented"  # type: ignore[index]
    with pytest.raises(WeakModelValidationError):
        validate_brief_plan(payload, validate_fact_store(fact_store_payload()))


def test_brief_plan_rejects_unknown_fact_reference() -> None:
    payload = brief_payload()
    payload["groups"][0]["fact_refs"] = ["unknown"]  # type: ignore[index]
    with pytest.raises(WeakModelValidationError, match="FACT_REF_UNKNOWN"):
        validate_brief_plan(payload, validate_fact_store(fact_store_payload()))


def test_narrative_compiler_preserves_facts_and_adds_structure() -> None:
    result = compile_brief_plan(fact_store_payload(), brief_payload())
    deck = result.deck_plan
    assert deck["schema_version"] == "1.0"
    assert deck["slides"][0]["role"] == "cover"
    assert deck["slides"][-1]["role"] == "closing"
    rendered_text = json.dumps(deck, ensure_ascii=False)
    for fact in fact_store_payload()["facts"]:  # type: ignore[index]
        assert fact["text"] in rendered_text
    assert result.narrative.coverage["required_fact_coverage"] == 1.0
    assert result.narrative.fact_store_digest
    assert all(len(slide.title) <= 60 for slide in result.narrative.slides)
    assert all(not slide.title.endswith("…") for slide in result.narrative.slides)


def test_omitted_required_fact_is_recovered_deterministically() -> None:
    brief = brief_payload()
    brief["groups"] = brief["groups"][:1]  # type: ignore[index]
    result = compile_brief_plan(fact_store_payload(), brief)
    assert "churn" in result.narrative.coverage["auto_assigned_fact_refs"]
    assert "Enterprise churn improved" in json.dumps(result.deck_plan)


def test_five_fact_deck_adds_agenda_and_assigns_distinct_unhinted_beats() -> None:
    facts = fact_store_payload()
    facts["facts"].extend(  # type: ignore[union-attr]
        [
            {
                "id": "backlog",
                "kind": "claim",
                "text": "Onboarding backlog increased during Q2.",
                "language": "en-US",
                "source_id": "request",
                "locator": "line:4",
                "required": True,
            },
            {
                "id": "priority",
                "kind": "instruction",
                "text": "Prioritize onboarding capacity in Q3.",
                "language": "en-US",
                "source_id": "request",
                "locator": "line:5",
                "required": True,
            },
        ]
    )
    plan = {
        "schema_version": "1.0",
        "scenario_id": "business-report",
        "groups": [
            {
                "id": f"group-{index + 1}",
                "fact_refs": [fact["id"]],
                **({"beat_hint": "performance"} if index == 0 else {}),
            }
            for index, fact in enumerate(facts["facts"])  # type: ignore[index]
        ],
    }

    result = compile_brief_plan(facts, plan)
    roles = [slide.role for slide in result.narrative.slides]

    assert len(result.deck_plan["slides"]) == 8
    assert "agenda" in roles
    assert len(set(roles[2:-1])) == 5
    assert result.narrative.coverage["auto_assigned_beat_groups"] == [
        "group-2",
        "group-3",
        "group-4",
        "group-5",
    ]


def test_incompatible_model_semantic_is_downgraded_by_fact_rules() -> None:
    payload = fact_store_payload()
    payload["facts"][0]["kind"] = "claim"  # type: ignore[index]
    payload["facts"][0].pop("value")  # type: ignore[index]
    payload["facts"][0].pop("unit")  # type: ignore[index]
    plan = {
        "schema_version": "1.0",
        "scenario_id": "business-report",
        "groups": [
            {
                "id": "unsafe-trend",
                "fact_refs": ["revenue"],
                "beat_hint": "performance",
                "semantic_hint": "trend",
            },
            {
                "id": "remaining",
                "fact_refs": ["margin", "churn"],
                "beat_hint": "insights",
                "semantic_hint": "comparison",
            },
        ],
    }

    result = compile_brief_plan(payload, plan)
    unsafe = next(
        slide for slide in result.deck_plan["slides"] if slide["id"] == "unsafe-trend"
    )

    assert unsafe["blocks"][0]["kind"] == "statement"
    assert result.narrative.coverage["semantic_adjustments"] == [
        "unsafe-trend:INCOMPATIBLE_SEMANTIC_DOWNGRADED:trend->statement",
        "remaining-detail-2:INCOMPATIBLE_SEMANTIC_DOWNGRADED:comparison->metrics",
    ]


def test_trusted_fact_beat_and_semantic_override_model_hints() -> None:
    payload = fact_store_payload()
    payload["facts"][0]["recommended_beat"] = "performance"  # type: ignore[index]
    payload["facts"][0]["recommended_semantic"] = "metrics"  # type: ignore[index]
    plan = brief_payload()
    plan["groups"][0]["fact_refs"] = ["revenue"]  # type: ignore[index]
    plan["groups"][0]["beat_hint"] = "risks"  # type: ignore[index]
    plan["groups"][0]["semantic_hint"] = "image"  # type: ignore[index]
    plan["groups"][1]["fact_refs"] = ["margin", "churn"]  # type: ignore[index]

    result = compile_brief_plan(payload, plan)
    slide = next(
        item for item in result.narrative.slides if item.id == "performance"
    )

    assert slide.role == "performance"
    assert slide.semantic_kind == "metrics"
    assert any(
        "TRUSTED_BEAT_OVERRIDES_MODEL" in item
        for item in result.narrative.coverage["authority_adjustments"]
    )
    assert any(
        "TRUSTED_SEMANTIC_OVERRIDES_MODEL" in item
        for item in result.narrative.coverage["semantic_adjustments"]
    )


def test_trusted_metric_sentence_extracts_only_source_present_values() -> None:
    payload = fact_store_payload()
    payload["facts"][0].pop("value")  # type: ignore[index]
    payload["facts"][0].pop("unit")  # type: ignore[index]
    payload["facts"][0]["recommended_semantic"] = "metrics"  # type: ignore[index]
    plan = brief_payload()
    plan["groups"][0]["fact_refs"] = ["revenue"]  # type: ignore[index]
    plan["groups"][0]["semantic_hint"] = "metrics"  # type: ignore[index]
    plan["groups"][1]["fact_refs"] = ["margin", "churn"]  # type: ignore[index]

    result = compile_brief_plan(payload, plan)
    slide = next(
        item for item in result.deck_plan["slides"] if item["id"] == "performance"
    )

    assert slide["blocks"][0]["kind"] == "metrics"
    assert slide["blocks"][0]["text"] == (
        "Q2 revenue was 48.2 million dollars, 12 percent above Q1."
    )
    assert slide["blocks"][0]["items"] == [
        {
            "label": "Q2 Revenue",
            "value": 48.2,
            "unit": "million dollars",
            "category": "Q2",
        },
        {
            "label": "Above Q1",
            "value": 12,
            "unit": "percent",
        },
    ]
    assert result.narrative.coverage["semantic_adjustments"] == [
        "insight-detail-1:EXPLICIT_NUMERIC_CHANGE_OVERRIDES_MODEL:metrics->comparison"
    ]


@pytest.mark.parametrize(
    ("language", "text", "maximum"),
    [
        (
            "en-US",
            "Revenue momentum remains strong across every enterprise segment "
            "without a short complete clause for the slide heading",
            60,
        ),
        (
            "zh-CN",
            "本季度企业客户收入保持强劲增长同时续费质量与销售效率均持续改善但该句没有可安全截取的短句边界",
            30,
        ),
    ],
)
def test_long_fact_uses_layout_safe_title_without_losing_body_evidence(
    language: str, text: str, maximum: int
) -> None:
    payload = fact_store_payload()
    payload["facts"][0]["text"] = text  # type: ignore[index]
    payload["facts"][0]["language"] = language  # type: ignore[index]
    plan = brief_payload()

    result = compile_brief_plan(payload, plan)
    slide = next(
        item
        for item in result.deck_plan["slides"]
        if text in json.dumps(item, ensure_ascii=False)
    )

    assert len(slide["title"]) <= maximum
    assert not slide["title"].endswith(("…", "..."))
    assert text in json.dumps(slide, ensure_ascii=False)


def test_decimal_value_is_never_mistaken_for_a_title_sentence_boundary() -> None:
    payload = fact_store_payload()
    text = (
        "The revenue target is 8.6 million dollars, compared with "
        "5.9 million dollars last year."
    )
    payload["facts"][0]["text"] = text  # type: ignore[index]

    result = compile_brief_plan(payload, brief_payload())
    slide = next(
        item
        for item in result.deck_plan["slides"]
        if text in json.dumps(item, ensure_ascii=False)
    )

    assert slide["title"] != "The revenue target is 8."
    assert text in json.dumps(slide, ensure_ascii=False)


def test_art_direction_registry_has_exact_neutral_profiles() -> None:
    registry = load_art_directions()
    assert set(registry) == ART_DIRECTION_IDS
    assert len(registry) == 12
    assert {profile.temperature for profile in registry.values()} == {
        "quiet",
        "neutral",
        "bold",
    }


def test_three_direction_candidates_are_deterministic_and_distinct() -> None:
    context = DirectionContext(
        scenario="business-report",
        audience="executive committee",
        density="balanced",
        tone="professional",
        locale="en-US",
        available_asset_kinds=frozenset(),
        has_brand=False,
    )
    first = select_art_directions(context)
    second = select_art_directions(context)
    assert first == second
    assert [item.slot for item in first.candidates] == [
        "safe",
        "editorial",
        "expressive",
    ]
    assert len({item.profile_id for item in first.candidates}) == 3
    assert first.selected_slot == "safe"


def test_proof_selector_uses_cover_and_densest_key_page() -> None:
    compiled = {
        "slides": [
            {"id": "cover", "role": "cover", "importance": "normal", "blocks": [{"items": []}]},
            {"id": "light", "role": "context", "importance": "normal", "blocks": [{"items": [1]}]},
            {"id": "key", "role": "performance", "importance": "critical", "blocks": [{"items": [1, 2, 3]}]},
            {"id": "closing", "role": "closing", "importance": "normal", "blocks": [{"items": []}]},
            {"id": "extra", "role": "insights", "importance": "high", "blocks": [{"items": [1, 2]}]},
        ]
    }
    assert select_proof_slide_ids(compiled) == ("cover", "key")


def test_brand_spec_requires_governed_assets_only_when_locked() -> None:
    spec = validate_brand_spec(
        {
            "schema_version": "1.0",
            "name": "Northstar",
            "require_brand_fidelity": True,
            "palette": [{"role": "primary", "value": "#0B3A67", "source": "brand-guide"}],
            "fonts": [],
            "required_assets": [{"kind": "logo", "mandatory": True}],
            "prohibited_patterns": ["generic-purple-gradient"],
        }
    )
    findings = assess_brand_assets(spec, frozenset())
    assert findings[0].code == "REQUIRED_BRAND_ASSET_MISSING"
    assert findings[0].hard_gate is True
    assert font_inventory_digest({"Arial", "Aptos"}) == font_inventory_digest({"Aptos", "Arial"})
    with pytest.raises(BrandSpecError):
        validate_brand_spec({"schema_version": "1.0", "name": "X", "surprise": 1})
    with pytest.raises(BrandSpecError, match="source"):
        validate_brand_spec(
            {
                "schema_version": "1.0",
                "name": "X",
                "fonts": [{"role": "heading", "family": "Brand Sans"}],
            }
        )
    with pytest.raises(BrandSpecError, match="mandatory"):
        validate_brand_spec(
            {
                "schema_version": "1.0",
                "name": "X",
                "required_assets": [{"kind": "logo"}],
            }
        )


def test_brand_spec_consumes_every_registered_semantic_color() -> None:
    values = {
        "primary": "#0B3A67",
        "accent": "#A64600",
        "positive": "#137333",
        "warning": "#8A4B08",
        "negative": "#B3261E",
        "background": "#F7F8FA",
    }
    spec = validate_brand_spec(
        {
            "schema_version": "1.0",
            "name": "Northstar",
            "palette": [
                {"role": role, "value": value, "source": "brand-guide"}
                for role, value in values.items()
            ],
        }
    )

    overrides = spec.to_overrides()

    assert {role: getattr(overrides, role) for role in values} == values


def test_each_layout_family_has_three_distinct_geometry_signatures() -> None:
    registry = load_layout_registry()
    for family in registry.families.values():
        signatures = {
            layout_geometry_signature(registry, registry.variants[variant_id])
            for variant_id in family.variant_ids
        }
        assert len(signatures) >= 3, family.id


def test_quality_v2_dedupes_and_orders_cross_stage_findings() -> None:
    findings = [
        QualityFindingV2("render", "TEXT_OVERFLOW", "hard-gate", "s1", "o1", "overflow"),
        QualityFindingV2("narrative", "FACT_MISSING", "critical", "s1", None, "missing"),
        QualityFindingV2("render", "TEXT_OVERFLOW", "hard-gate", "s1", "o1", "duplicate"),
    ]
    report = build_quality_report_v2(findings, transaction_status="candidate")
    assert [item.code for item in report.findings] == ["TEXT_OVERFLOW", "FACT_MISSING"]
    assert report.hard_gate_failures == ("TEXT_OVERFLOW",)
    assert defect_vector(report)[:2] == (1, 1)


def test_two_stage_repair_is_bounded_monotonic_and_fact_safe() -> None:
    initial = build_quality_report_v2(
        [QualityFindingV2("narrative", "DIRECTION_PROFILE_DRIFT", "important", "s1", None, "drift")],
        transaction_status="planned",
    )
    result = execute_two_stage_repair(
        state={"fact_digest": "immutable", "layout": "a", "x": 0},
        initial_report=initial,
        pre_render=lambda state: (
            {**state, "layout": "b"},
            build_quality_report_v2(
                [QualityFindingV2("render", "COM_GEOMETRY_DRIFT", "warning", "s1", "o1", "drift")],
                transaction_status="planned",
            ),
        ),
        post_render=lambda state: ({**state, "x": 1}, build_quality_report_v2([], transaction_status="candidate")),
    )
    assert len(result.passes) == 2
    assert result.state["fact_digest"] == "immutable"
    assert all(item.accepted for item in result.passes)


def test_two_stage_repair_rolls_back_regression() -> None:
    initial = build_quality_report_v2([], transaction_status="planned")
    result = execute_two_stage_repair(
        state={"fact_digest": "same", "layout": "a"},
        initial_report=initial,
        pre_render=lambda state: (
            {**state, "fact_digest": "changed"},
            build_quality_report_v2(
                [QualityFindingV2("narrative", "FACT_MUTATED", "hard-gate", None, None, "bad")],
                transaction_status="planned",
            ),
        ),
    )
    assert result.state["fact_digest"] == "same"
    assert result.passes[0].rolled_back is True


@pytest.mark.parametrize(
    ("field", "mutated"),
    [
        ("text", "Invented revenue claim"),
        ("value", 999),
        ("source", "untrusted-source"),
    ],
)
def test_two_stage_repair_recomputes_protected_content_digest(
    field: str,
    mutated: object,
) -> None:
    initial = build_quality_report_v2(
        [
            QualityFindingV2(
                "render",
                "GEOMETRY_DRIFT",
                "warning",
                "s1",
                "o1",
                "repairable drift",
            )
        ],
        transaction_status="candidate",
    )
    state = {
        "fact_digest": "stale-but-unchanged",
        "layout": "a",
        "facts": [
            {
                "text": "Revenue reached 100 million",
                "value": 100,
                "source": "audited-ledger",
            }
        ],
    }

    def mutate(proposed: dict[str, object]) -> tuple[dict[str, object], object]:
        proposed["layout"] = "b"
        proposed["facts"][0][field] = mutated  # type: ignore[index]
        return proposed, build_quality_report_v2([], transaction_status="candidate")

    result = execute_two_stage_repair(
        state=state,
        initial_report=initial,
        pre_render=mutate,  # type: ignore[arg-type]
    )

    assert result.state == state
    assert result.passes[0].accepted is False
    assert result.passes[0].rolled_back is True
    assert result.passes[0].failure_code == "PROTECTED_CONTENT_MUTATED"


def test_fingerprint_bundle_is_canonical_and_rejects_mixed_or_dirty() -> None:
    assert canonical_sha256({"b": 1, "a": 2}) == canonical_sha256({"a": 2, "b": 1})
    base = {
        "git_commit": "f" * 40,
        "dirty_state": False,
        "engine_sha256": "a" * 64,
        "registry_bundle_sha256": "b" * 64,
        "schemas_sha256": "c" * 64,
        "skill_sha256": "d" * 64,
        "corpus_sha256": "e" * 64,
        "protocol_sha256": "1" * 64,
        "prompt_sha256": "2" * 64,
        "thresholds_sha256": "3" * 64,
        "dependencies_sha256": "4" * 64,
        "model_provider_sha256": "5" * 64,
        "environment_sha256": "6" * 64,
        "font_inventory_sha256": "7" * 64,
        "powerpoint_build_sha256": "8" * 64,
        "asset_manifest_sha256": "9" * 64,
        "evidence_generation": "post-huashu",
    }
    assert validate_fingerprint_bundle([base, copy.deepcopy(base)]) == base
    dirty = {**base, "dirty_state": True}
    with pytest.raises(ValueError, match="dirty"):
        validate_fingerprint_bundle([dirty])
    mixed = {**base, "engine_sha256": "0" * 64}
    with pytest.raises(ValueError, match="mixed"):
        validate_fingerprint_bundle([base, mixed])
