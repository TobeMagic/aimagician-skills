from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.template_intelligence import (  # noqa: E402
    FORBIDDEN_MODEL_FIELDS,
    RegistryV3,
    TemplateIntelligenceError,
    build_selection_plan,
    choose_spine,
    compile_slide_blueprints,
    load_registry_v3,
    retrieve_candidates,
    validate_blueprint_payload,
)
from window_pptx.template_pack import load_template_pack  # noqa: E402
from window_pptx.template_pack_v2 import (  # noqa: E402
    TemplatePackV2Error,
    adapt_template_pack_v1,
    load_template_pack_v2,
)


def _brief(scenario: str = "annual-work-report") -> dict:
    return {
        "brief_id": f"brief-{scenario}",
        "status": "Locked",
        "discussion_status": "complete",
        "scenario": scenario,
        "slides": [
            {"slide_id": "s01", "role": "cover", "semantic_kind": "key-message", "item_count": 1, "text_chars": 42, "fact_refs": ["f01"], "asset_refs": [], "asset_kinds": [], "importance": "hero"},
            {"slide_id": "s02", "role": "agenda", "semantic_kind": "structured-content", "item_count": 4, "text_chars": 120, "fact_refs": [], "asset_refs": [], "asset_kinds": []},
            {"slide_id": "s03", "role": "section", "semantic_kind": "key-message", "item_count": 1, "text_chars": 40, "fact_refs": [], "asset_refs": [], "asset_kinds": []},
            {"slide_id": "s04", "role": "body", "semantic_kind": "kpi", "item_count": 4, "text_chars": 260, "fact_refs": ["f02", "f03"], "asset_refs": [], "asset_kinds": [], "importance": "important"},
            {"slide_id": "s05", "role": "body", "semantic_kind": "trend", "item_count": 6, "text_chars": 240, "fact_refs": ["f04"], "asset_refs": [], "asset_kinds": []},
            {"slide_id": "s06", "role": "body", "semantic_kind": "process", "item_count": 5, "text_chars": 320, "fact_refs": ["f05"], "asset_refs": [], "asset_kinds": []},
            {"slide_id": "s07", "role": "decision", "semantic_kind": "roadmap", "item_count": 4, "text_chars": 280, "fact_refs": ["f06"], "asset_refs": [], "asset_kinds": [], "importance": "important"},
            {"slide_id": "s08", "role": "closing", "semantic_kind": "key-message", "item_count": 1, "text_chars": 40, "fact_refs": [], "asset_refs": [], "asset_kinds": [], "importance": "hero"},
        ],
    }


def test_v2_physical_pack_is_lossless_and_hash_bound() -> None:
    v1 = load_template_pack("institutional-work-summary-v1")
    v2 = load_template_pack_v2("institutional-work-summary-v2")

    assert v2.v1_pack == v1
    assert v2.source_sha256 == v1.template_sha256
    assert len(v2.pages) == v1.slide_count == 15
    assert adapt_template_pack_v1(v1) == v2
    assert set(v2.art_direction.forbidden) >= {
        "3d-chart", "mixed-icon-language", "tiny-label", "decorative-collision"
    }


@pytest.mark.parametrize(
    ("pack_id", "source_mode", "materializer"),
    [
        ("institutional-work-summary-v2", "physical_ooxml", "template_pack_v1_adapter"),
        ("campus-innovation-pitch-v2", "registered_composition", "registered_native_renderer"),
        ("academic-defense-editorial-v2", "registered_composition", "registered_native_renderer"),
    ],
)
def test_three_certified_spines_have_executable_design_systems(
    pack_id: str, source_mode: str, materializer: str
) -> None:
    pack = load_template_pack_v2(pack_id)

    assert pack.certification == "certified"
    assert pack.source_mode == source_mode
    assert pack.materializer == materializer
    assert len(pack.art_direction.palette) >= 4
    assert min(pack.art_direction.type_scale.values()) >= 11
    assert pack.art_direction.motifs
    assert pack.art_direction.forbidden


def test_registry_v3_has_exact_balanced_certified_pilot() -> None:
    registry = load_registry_v3()
    candidates = tuple(registry.candidates.values())

    assert len(candidates) == 84
    assert len([item for item in candidates if item.source_mode == "physical_ooxml"]) == 15
    assert len([item for item in candidates if item.specialty]) == 9
    assert len([item for item in candidates if item.id.startswith("layout.")]) == 60
    assert len({item.family for item in candidates}) == 25
    assert {item.certification for item in candidates} == {"certified"}
    assert {item.materializer for item in candidates} == {
        "template_pack_v1_adapter", "registered_native_renderer"
    }
    assert set(registry.spines) == {
        "institutional-work-summary",
        "campus-innovation-pitch",
        "academic-defense-editorial",
    }
    assert not any("legacy" in item.id for item in candidates)


@pytest.mark.parametrize(
    ("scenario", "spine_id"),
    [
        ("annual-work-report", "institutional-work-summary"),
        ("campus-competition", "campus-innovation-pitch"),
        ("academic-defense", "academic-defense-editorial"),
    ],
)
def test_locked_flagship_brief_produces_deterministic_plan_and_blueprints(
    scenario: str, spine_id: str
) -> None:
    registry = load_registry_v3()
    first = build_selection_plan(_brief(scenario), registry=registry)
    shuffled = dict(list(registry.candidates.items()))
    keys = list(shuffled)
    random.Random(7).shuffle(keys)
    reordered = RegistryV3(
        registry.id,
        {key: shuffled[key] for key in keys},
        registry.spines,
        registry.source_digests,
    )
    second = build_selection_plan(_brief(scenario), registry=reordered)

    assert first == second
    assert first.spine_id == spine_id
    blueprints = compile_slide_blueprints(first, registry)
    assert len(blueprints) == 8
    assert all(item.materializer for item in blueprints)
    assert all(item.token_profile_id.endswith("-v2") for item in blueprints)


def test_specialty_semantics_prefer_explicit_materializer_alias() -> None:
    registry = load_registry_v3()
    spine = choose_spine("campus-competition", registry)
    slide = {
        "slide_id": "map",
        "role": "body",
        "semantic_kind": "map",
        "item_count": 4,
        "text_chars": 200,
        "fact_refs": ["region-1"],
        "asset_refs": ["map-cn"],
        "asset_kinds": ["map"],
    }

    candidates = retrieve_candidates(slide, spine, registry)

    assert candidates[0].candidate_id == "specialty.map"
    assert "SPECIALTY_FIT" in candidates[0].reasons


def test_model_boundary_rejects_raw_design_fact_asset_and_capacity_escape() -> None:
    registry = load_registry_v3()
    brief = _brief()
    plan = build_selection_plan(brief, registry=registry)
    choices = plan.to_dict()["selections"]

    for forbidden in sorted(FORBIDDEN_MODEL_FIELDS):
        invalid = [dict(item) for item in choices]
        invalid[0][forbidden] = 1
        with pytest.raises(TemplateIntelligenceError, match="fields invalid"):
            build_selection_plan(brief, choices=invalid, registry=registry)

    invalid = [dict(item) for item in choices]
    invalid[3]["fact_refs"] = ["invented-fact"]
    with pytest.raises(TemplateIntelligenceError, match="unbound fact"):
        build_selection_plan(brief, choices=invalid, registry=registry)

    over_capacity = _brief()
    over_capacity["slides"][3]["item_count"] = 100
    with pytest.raises(TemplateIntelligenceError, match="NO_FIT"):
        build_selection_plan(over_capacity, registry=registry)


def test_selection_fails_closed_for_unlocked_incomplete_and_unknown_spine() -> None:
    unlocked = _brief()
    unlocked["status"] = "Draft"
    with pytest.raises(TemplateIntelligenceError, match="status=Locked"):
        build_selection_plan(unlocked)

    incomplete = _brief()
    incomplete["slides"] = [
        slide for slide in incomplete["slides"] if slide["role"] != "agenda"
    ]
    with pytest.raises(TemplateIntelligenceError, match="missing agenda"):
        build_selection_plan(incomplete)

    with pytest.raises(TemplateIntelligenceError, match="NO_FIT"):
        choose_spine("unknown-scenario", load_registry_v3())


def test_blueprint_contract_rejects_geometry_style_code_and_repair() -> None:
    plan = build_selection_plan(_brief())
    payload = compile_slide_blueprints(plan)[0].to_dict()
    validate_blueprint_payload(payload)
    for field in ("x", "shape_id", "ooxml", "html", "code", "font", "color", "repair"):
        with pytest.raises(TemplateIntelligenceError, match="forbidden"):
            validate_blueprint_payload({**payload, field: "unsafe"})


def test_registry_digest_drift_and_pack_unknown_fields_fail_closed(tmp_path: Path) -> None:
    registry_payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    registry_payload["source_digests"]["layouts.json"] = "sha256:" + "0" * 64
    bad_registry = tmp_path / "registry.json"
    bad_registry.write_text(json.dumps(registry_payload), encoding="utf-8")
    with pytest.raises(TemplateIntelligenceError, match="source drift"):
        load_registry_v3(bad_registry)

    pack_payload = json.loads(
        (SKILL_ROOT / "design-packs" / "product-launch-stage" / "template-pack-v2.json").read_text(encoding="utf-8")
    )
    pack_payload["raw_coordinates"] = [1, 2, 3, 4]
    bad_pack = tmp_path / "template-pack-v2.json"
    bad_pack.write_text(json.dumps(pack_payload), encoding="utf-8")
    with pytest.raises(TemplatePackV2Error, match="fields mismatch"):
        load_template_pack_v2(bad_pack)


def test_v2_and_selection_schemas_accept_owned_payloads() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    registry_schema = json.loads(
        (SKILL_ROOT / "schemas" / "registry.v3.schema.json").read_text()
    )
    pack_schema = json.loads(
        (SKILL_ROOT / "schemas" / "template-pack.v2.schema.json").read_text()
    )
    plan_schema = json.loads(
        (SKILL_ROOT / "schemas" / "template-selection-plan.v1.schema.json").read_text()
    )
    blueprint_schema = json.loads(
        (SKILL_ROOT / "schemas" / "slide-blueprint.v1.schema.json").read_text()
    )
    jsonschema.Draft202012Validator(registry_schema).validate(
        json.loads(REGISTRY.read_text())
    )
    for path in (SKILL_ROOT / "design-packs").glob("*/template-pack-v2.json"):
        jsonschema.Draft202012Validator(pack_schema).validate(json.loads(path.read_text()))
    plan = build_selection_plan(_brief())
    jsonschema.Draft202012Validator(plan_schema).validate(plan.to_dict())
    for blueprint in compile_slide_blueprints(plan):
        jsonschema.Draft202012Validator(blueprint_schema).validate(blueprint.to_dict())


REGISTRY = SKILL_ROOT / "registries" / "template-intelligence-v3.json"
