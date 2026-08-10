"""Focused tests for deterministic AssemblyIntent auto-binding."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.assembly_autobinder import (  # noqa: E402
    AutoBindingError,
    _validate_capacity,
    build_default_intent,
    compile_assembly_intent,
)
from window_pptx.page_template_library import (  # noqa: E402
    DEFAULT_SCORING,
    LibraryIndex,
    PageTemplate,
)
from window_pptx.weak_model import (  # noqa: E402
    Fact,
    FactSource,
    FactStore,
    TrustedProject,
)


PACKAGE_SHA = "1" * 64
SOURCE_SLIDE_SHA = "2" * 64
LIBRARY_SHA = "3" * 64
PROFILE_SHA = "4" * 64
QUERY_SHA = "5" * 64
INTENT_SHA = "6" * 64
PAGE_ID = f"{PACKAGE_SHA}:001"
STYLE_ID = "synthetic-editorial"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slot(
    number: int,
    *,
    max_chars: int = 20,
    group_id: str | None = None,
    group_order: int | None = None,
) -> dict[str, Any]:
    return {
        "slot_id": f"shape_{number}",
        "shape_id": number,
        "kind": "text",
        "semantic_role": "title_fragment" if group_id else "body",
        "region": "middle-center",
        "reading_order": number,
        "bbox": {"x": 10, "y": number * 10, "w": 300, "h": 50},
        "max_chars": max_chars,
        "source_char_count": 1,
        "source_line_count": 1,
        "source_run_count": 1,
        "source_text_sha256": _sha(f"source-{number}"),
        "source_text": "",
        "group_id": group_id,
        "group_order": group_order,
        "font_size_pt": 20.0,
        "allowed_binding_modes": ["fact", "connective", "character", "clear"],
    }


def _empty_governed_inventory() -> dict[str, Any]:
    return {
        "schema_version": "governed-content-inventory.v1",
        "peer_mapping_method": "chart-formula-range-v1",
        "policy": "no-embedded-content",
        "complete": True,
        "content_slot_count": 0,
        "customer_data_slot_count": 0,
        "slots": [],
        "closure_metadata": {
            "table_count": 0,
            "chart_part_count": 0,
            "workbook_part_count": 0,
            "notes_part_count": 0,
            "comment_part_count": 0,
            "diagram_part_count": 0,
            "layout_master_field_count": 0,
            "layout_master_fields": [],
            "tag_part_count": 0,
            "tag_parts": [],
            "media_count": 0,
            "media_parts": [],
        },
        "scan_errors": [],
    }


def _template() -> PageTemplate:
    slots = tuple(
        _slot(
            number,
            group_id="fragment_01" if number in {3, 4} else None,
            group_order=number - 2 if number in {3, 4} else None,
        )
        for number in range(1, 7)
    )
    return PageTemplate(
        schema_version="1.0",
        page_id=PAGE_ID,
        package_sha256=PACKAGE_SHA,
        slide_number=1,
        source_path="private://synthetic/source.pptx",
        source_sha256=PACKAGE_SHA,
        source_slide_sha256=SOURCE_SLIDE_SHA,
        page_role="body",
        category_names=("synthetic",),
        style_cluster_id=STYLE_ID,
        deck_family_id="synthetic-deck",
        theme_palette=("#112233", "#DDBB77", "#F7F2E8"),
        capacity={"max_text_chars": 120, "max_text_runs": 6},
        editability="native_editable",
        certification="certified",
        visual_quality=0.95,
        structure={
            "slide_count": 1,
            "shape_count": 6,
            "layout_count": 1,
            "master_count": 1,
            "theme_count": 1,
            "media_count": 0,
            "page_shape_count": 6,
            "slide_relationship_count": 0,
            "linked_style_part_count": 0,
            "page_image_count": 0,
            "page_media_count": 0,
            "page_chart_count": 0,
            "page_table_count": 0,
            "page_native_object_count": 6,
        },
        slot_graph={
            "text_slot_ids": [f"shape_{number}" for number in range(1, 7)],
            "text_slot_count": 6,
            "reading_order": [f"shape_{number}" for number in range(1, 7)],
            "fragment_groups": [
                {"group_id": "fragment_01", "slot_ids": ["shape_3", "shape_4"]}
            ],
            "slots": list(slots),
        },
        requires_customer_asset=False,
        media_retention_policy="no-page-media",
        pool="certified-core",
        decision="direct-use",
        direct_use=True,
        eligibility_known=True,
        style_features={
            "tone": "light",
            "average_luminance": 210,
            "average_chroma": 30,
            "accent_family": "gold",
            "visual_mode": "editorial",
            "density": "balanced",
            "density_score": 45,
        },
        governed_content_inventory=_empty_governed_inventory(),
    )


def _library(template: PageTemplate) -> LibraryIndex:
    return LibraryIndex(
        schema_version="4.0",
        library_id="synthetic-library",
        compiled_at="1970-01-01T00:00:00Z",
        source_core_schema="gaojie-certified-core.v2",
        private_root_sha256="7" * 64,
        source_package_count=1,
        source_package_index={PACKAGE_SHA: {"slide_count": 1}},
        page_template_count=1,
        role_index={"body": 1},
        style_cluster_index={STYLE_ID: 1},
        deck_family_index={"synthetic-deck": 1},
        category_index={"synthetic": 1},
        scoring=dict(DEFAULT_SCORING),
        dominant_style_cluster_id=STYLE_ID,
        compatible_style_cluster_ids=(STYLE_ID,),
        page_templates=(template,),
    )


def _fact_store() -> FactStore:
    values = (
        ("fact-title", "年度总结"),
        ("fact-body", "经营稳健"),
        ("fact-fragment", "工作"),
        ("fact-glyph", "总"),
        ("fact-secret", "越权内容"),
    )
    return FactStore(
        schema_version="1.0",
        project=TrustedProject(
            title="Synthetic annual report",
            objective="Verify deterministic binding",
            audience="Review committee",
            language="zh-CN",
        ),
        sources=(
            FactSource(
                id="client-request",
                kind="request",
                locator="REQUEST.md",
                sha256="8" * 64,
            ),
        ),
        facts=tuple(
            Fact(
                id=fact_id,
                kind="claim",
                text=text,
                language="zh-CN",
                source_id="client-request",
                locator=f"REQUEST.md#{fact_id}",
                required=False,
                allowed_renderings=(text,),
            )
            for fact_id, text in values
        ),
        digest="9" * 64,
    )


def _fact_rule(fact_id: str, text: str) -> dict[str, Any]:
    return {
        "kind": "fact",
        "renderings": [
            {"fact_id": fact_id, "rendering_sha256": _sha(text)}
        ],
        "separator": "",
    }


def _profile() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "profile_id": "synthetic-profile",
        "scenario_id": "synthetic-work-report",
        "acceptance_profile": "synthetic-focused-test",
        "created_at": "2026-08-09T00:00:00Z",
        "library_id": "synthetic-library",
        "library_index_sha256": LIBRARY_SHA,
        "dominant_style_cluster_id": STYLE_ID,
        "default_unassigned_connective_id": "clear",
        "governed_policy": "deterministic-authorize-exact",
        "slides": [
            {
                "ordinal": 1,
                "page_id": PAGE_ID,
                "narrative_role": "body",
                "fact_ids": [
                    "fact-title",
                    "fact-body",
                    "fact-fragment",
                    "fact-glyph",
                ],
                "title_binding": _fact_rule("fact-title", "年度总结"),
                "query": {
                    "role": "body",
                    "capacity_budget": 40,
                    "semantic_categories": ["synthetic"],
                    "asset_requirements": [],
                    "customer_assets_available": False,
                    "style_cluster": STYLE_ID,
                    "limit": 3,
                    "allow_fallback": False,
                    "required_source_ordinal": 1,
                },
                "bindings": {
                    "shape_1": {
                        **_fact_rule("fact-body", "经营稳健"),
                        "fit_policy": "no-autofit",
                    },
                    "shape_2": {
                        "kind": "connective",
                        "connective_id": "bridge",
                    },
                },
                "fragment_bindings": [
                    {
                        "target_kind": "group",
                        "target_id": "fragment_01",
                        "fact_id": "fact-fragment",
                        "rendering_sha256": _sha("工作"),
                    },
                    {
                        "target_kind": "slot",
                        "target_id": "shape_5",
                        "fact_id": "fact-glyph",
                        "rendering_sha256": _sha("总"),
                    },
                ],
                "style_clones": [
                    {
                        "source_shape_id": 7,
                        "target_shape_id": 8,
                        "scope": "shape-fill",
                        "source_style_sha256": "1" * 64,
                        "target_guard_sha256": "2" * 64,
                    }
                ],
            }
        ],
    }


def _candidate(
    template: PageTemplate,
    *,
    page_id: str | None = None,
    score: float = 0.93,
) -> dict[str, Any]:
    page = template.to_dict()
    if page_id is not None:
        package_sha, slide = page_id.split(":")
        page.update(
            {
                "page_id": page_id,
                "package_sha256": package_sha,
                "source_sha256": package_sha,
                "source_slide_sha256": "a" * 64,
                "slide_number": int(slide),
            }
        )
    return {
        "schema_version": "1.0",
        "page_id": page["page_id"],
        "eligibility": True,
        "reasons": ["synthetic exact match"],
        "fallback_reason": None,
        "asset_fit": 1.0,
        "capacity_fit": True,
        "residue_risk": 0.0,
        "style_compatibility": "exact",
        "scores": {
            "role": 1.0,
            "capacity": 1.0,
            "semantic": 0.8,
            "style": 1.0,
            "editability": 1.0,
            "total": score,
        },
        "weights": dict(DEFAULT_SCORING),
        "page_template": page,
    }


def _query_bundle(template: PageTemplate) -> dict[str, Any]:
    candidate = _candidate(template)
    return {
        "schema_version": "page-template-query-bundle.v1",
        "request_sha256": "b" * 64,
        "library_index_sha256": LIBRARY_SHA,
        "library_resolution_source": "absolute-library",
        "query_count": 1,
        "queries": [
            {
                "target_ordinal": 1,
                "query_id": "slide-001-body",
                "result": {
                    "schema_version": "page-template-query-result.v1",
                    "library_index_sha256": LIBRARY_SHA,
                    "library_resolution_source": "absolute-library",
                    "required_source_ordinal": 1,
                    "role": "body",
                    "capacity_budget": 40,
                    "semantic_categories": ["synthetic"],
                    "style_cluster": STYLE_ID,
                    "asset_requirements": [],
                    "customer_assets_available": False,
                    "limit": 3,
                    "allow_fallback": False,
                    "direct_use_only": True,
                    "include_ineligible": False,
                    "weights": dict(DEFAULT_SCORING),
                    "count": 1,
                    "eligible_count": 1,
                    "candidates": [candidate],
                },
            }
        ],
    }


def _case() -> dict[str, Any]:
    template = _template()
    profile = _profile()
    return {
        "template": template,
        "library": _library(template),
        "profile": profile,
        "intent": build_default_intent(profile),
        "query": _query_bundle(template),
        "fact_store": _fact_store(),
        "connectives": {
            "schema_version": "1.0",
            "entries": [
                {"id": "clear", "text": ""},
                {"id": "bridge", "text": "·"},
            ],
        },
    }


def _compile(case: dict[str, Any], **overrides: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    arguments: dict[str, Any] = {
        "profile": case["profile"],
        "profile_sha256": PROFILE_SHA,
        "library_index": case["library"],
        "library_index_sha256": LIBRARY_SHA,
        "query_bundle": case["query"],
        "query_bundle_sha256": QUERY_SHA,
        "query_bundle_path": "evidence/template-query-results.v1.json",
        "fact_store": case["fact_store"],
        "connective_copy": case["connectives"],
        "authority_paths": {
            "fact_store": "facts/fact-store.json",
            "asset_manifest": "assets/asset-manifest.json",
            "connective_copy": "facts/connective-copy.json",
        },
        "authority_sha256": {
            "fact_store": "c" * 64,
            "asset_manifest": "d" * 64,
            "connective_copy": "e" * 64,
        },
        "intent_sha256": INTENT_SHA,
    }
    arguments.update(overrides)
    return compile_assembly_intent(case["intent"], **arguments)


def test_default_intent_is_minimal_ordered_and_schema_valid() -> None:
    case = _case()
    intent = case["intent"]

    assert intent == {
        "schema_version": "1.0",
        "profile_id": "synthetic-profile",
        "scenario_id": "synthetic-work-report",
        "slides": [
            {
                "ordinal": 1,
                "page_id": PAGE_ID,
                "narrative_role": "body",
                "fact_ids": [
                    "fact-title",
                    "fact-body",
                    "fact-fragment",
                    "fact-glyph",
                ],
            }
        ],
    }
    serialized = json.dumps(intent, ensure_ascii=False)
    assert "shape_" not in serialized
    assert "geometry" not in serialized


def test_compiler_expands_every_slot_with_fact_connective_and_fragments() -> None:
    plan, report = _compile(_case())
    slide = plan["target_slides"][0]

    assert slide["bindings"] == {
        "shape_3": {"text": "工", "fact_refs": ["fact-fragment"], "asset_refs": [], "fit_policy": "preserve"},
        "shape_4": {"text": "作", "fact_refs": ["fact-fragment"], "asset_refs": [], "fit_policy": "preserve"},
        "shape_5": {"text": "总", "fact_refs": ["fact-glyph"], "asset_refs": [], "fit_policy": "preserve"},
        "shape_1": {"text": "经营稳健", "fact_refs": ["fact-body"], "asset_refs": [], "fit_policy": "no-autofit"},
        "shape_2": {"text": "·", "fact_refs": [], "asset_refs": [], "fit_policy": "preserve"},
        "shape_6": {"text": "", "fact_refs": [], "asset_refs": [], "fit_policy": "preserve"},
    }
    assert slide["title"] == "年度总结"
    assert "style_clones" not in slide
    assert plan["binding_profile_authority"] == {
        "profile_id": "synthetic-profile",
        "profile_sha256": PROFILE_SHA,
    }
    assert report["ordinary_slot_count"] == 6
    assert report["fact_binding_count"] == 4
    assert report["connective_binding_count"] == 2
    assert report["fragment_slot_count"] == 3
    assert report["slides"] == [
        {
            "ordinal": 1,
            "page_id": PAGE_ID,
            "candidate_rank": 1,
            "ordinary_slot_count": 6,
            "fact_binding_count": 4,
            "connective_binding_count": 2,
            "fragment_slot_count": 3,
            "status": "pass",
        }
    ]


def test_candidate_rank_is_derived_from_query_order() -> None:
    case = _case()
    selected = case["query"]["queries"][0]["result"]["candidates"][0]
    decoy = _candidate(
        case["template"],
        page_id=f"{'f' * 64}:001",
        score=0.97,
    )
    case["query"]["queries"][0]["result"].update(
        {"count": 2, "eligible_count": 2, "candidates": [decoy, selected]}
    )

    plan, report = _compile(case)

    assert plan["target_slides"][0]["selection"]["candidate_rank"] == 2
    assert plan["target_slides"][0]["selection"]["score_total"] == 0.93
    assert report["slides"][0]["candidate_rank"] == 2


def test_output_is_deterministic_and_hash_bound() -> None:
    case = _case()

    first_plan, first_report = _compile(case)
    second_plan, second_report = _compile(copy.deepcopy(case))

    assert first_plan == second_plan
    assert first_report == second_report
    canonical = (
        json.dumps(
            first_plan,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    assert first_report["plan_sha256"] == hashlib.sha256(canonical).hexdigest()
    assert first_plan["query_bundle"]["sha256"] == QUERY_SHA
    assert first_report["profile_sha256"] == PROFILE_SHA
    assert first_report["query_bundle_sha256"] == QUERY_SHA
    assert first_report["intent_sha256"] == INTENT_SHA


def test_generated_contracts_and_synthetic_query_pass_schemas() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    case = _case()
    plan, report = _compile(case)
    schema_root = SKILL_ROOT / "schemas"

    for schema_name, payload in (
        ("assembly-intent.v1.schema.json", case["intent"]),
        ("binding-profile.v1.schema.json", case["profile"]),
        ("assembly-plan.v1.schema.json", plan),
        ("auto-binding-report.v1.schema.json", report),
    ):
        schema = json.loads((schema_root / schema_name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(payload)

    bundle_schema = json.loads(
        (schema_root / "page-template-query-bundle.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    query_schema = json.loads(
        (schema_root / "page-template-query-result.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    candidate_schema = json.loads(
        (schema_root / "page-template-candidate.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    page_schema = json.loads(
        (schema_root / "page-template.v1.schema.json").read_text(encoding="utf-8")
    )
    resolver = jsonschema.RefResolver(
        base_uri=schema_root.as_uri() + "/",
        referrer=bundle_schema,
        store={
            query_schema["$id"]: query_schema,
            candidate_schema["$id"]: candidate_schema,
            page_schema["$id"]: page_schema,
        },
    )
    jsonschema.Draft202012Validator(
        bundle_schema,
        resolver=resolver,
    ).validate(case["query"])


def test_assembly_plan_schema_rejects_agent_authored_style_operations() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    case = _case()
    plan, _ = _compile(case)
    plan["target_slides"][0]["style_clones"] = case["profile"]["slides"][0][
        "style_clones"
    ]
    schema = json.loads(
        (SKILL_ROOT / "schemas" / "assembly-plan.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )

    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(plan))

    assert errors
    assert any("style_clones" in error.message for error in errors)


def test_binding_profile_schema_rejects_unknown_fit_policy() -> None:
    case = _case()
    case["profile"]["slides"][0]["bindings"]["shape_1"]["fit_policy"] = "shrink"

    with pytest.raises(
        AutoBindingError,
        match="AUTO_BIND_PROFILE_SCHEMA_INVALID.*fit_policy",
    ):
        _compile(case)


def test_capacity_overflow_fails_closed() -> None:
    case = _case()
    slots = copy.deepcopy(case["template"].slot_graph)
    slots["slots"][0]["max_chars"] = 3
    limited = replace(case["template"], slot_graph=slots)
    case["library"] = replace(case["library"], page_templates=(limited,))

    with pytest.raises(
        AutoBindingError,
        match=r"AUTO_BIND_RENDERING_OVER_CAPACITY: 1:shape_1:4>3",
    ):
        _compile(case)


def test_capacity_uses_semantic_characters_for_template_layout_spacing() -> None:
    _validate_capacity(
        ordinal=12,
        slot_id="shape_75",
        slot={"max_chars": 15},
        text="深入" + (" " * 23) + "临床科室",
    )


def test_unknown_fact_fails_closed_before_binding() -> None:
    case = _case()
    case["profile"]["slides"][0]["fact_ids"].append("fact-missing")
    case["intent"] = build_default_intent(case["profile"])

    with pytest.raises(AutoBindingError, match="AUTO_BIND_FACT_UNKNOWN: fact-missing"):
        _compile(case)


def test_existing_but_unscoped_fact_is_rejected() -> None:
    case = _case()
    case["profile"]["slides"][0]["bindings"]["shape_1"] = _fact_rule(
        "fact-secret", "越权内容"
    )

    with pytest.raises(
        AutoBindingError,
        match="AUTO_BIND_FACT_SCOPE_VIOLATION: fact-secret",
    ):
        _compile(case)


def test_unregistered_fact_rendering_is_rejected() -> None:
    case = _case()
    case["profile"]["slides"][0]["bindings"]["shape_1"]["renderings"][0][
        "rendering_sha256"
    ] = _sha("未经登记的改写")

    with pytest.raises(
        AutoBindingError,
        match="AUTO_BIND_RENDERING_NOT_REGISTERED: fact-body",
    ):
        _compile(case)


def test_unknown_connective_is_rejected() -> None:
    case = _case()
    case["profile"]["slides"][0]["bindings"]["shape_2"][
        "connective_id"
    ] = "not-registered"

    with pytest.raises(
        AutoBindingError,
        match="AUTO_BIND_CONNECTIVE_UNKNOWN: not-registered",
    ):
        _compile(case)


def test_duplicate_physical_page_is_rejected_across_slides() -> None:
    case = _case()
    second = copy.deepcopy(case["profile"]["slides"][0])
    second["ordinal"] = 2
    case["profile"]["slides"].append(second)
    case["intent"] = build_default_intent(case["profile"])
    second_query = copy.deepcopy(case["query"]["queries"][0])
    second_query.update({"target_ordinal": 2, "query_id": "slide-002-body"})
    case["query"]["queries"].append(second_query)
    case["query"]["query_count"] = 2

    with pytest.raises(
        AutoBindingError,
        match=f"AUTO_BIND_DUPLICATE_PAGE_ID: {PAGE_ID}",
    ):
        _compile(case)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda case: case["profile"].update(
                {"library_index_sha256": "f" * 64}
            ),
            "AUTO_BIND_LIBRARY_FINGERPRINT_MISMATCH",
        ),
        (
            lambda case: case["query"].update(
                {"library_index_sha256": "f" * 64}
            ),
            "AUTO_BIND_LIBRARY_FINGERPRINT_MISMATCH",
        ),
        (
            lambda case: case["profile"].update({"library_id": "other-library"}),
            "AUTO_BIND_LIBRARY_ID_MISMATCH",
        ),
        (
            lambda case: case["intent"].update({"profile_id": "other-profile"}),
            "AUTO_BIND_PROFILE_APPLICABILITY_MISMATCH",
        ),
        (
            lambda case: case["intent"].update({"scenario_id": "other-scenario"}),
            "AUTO_BIND_PROFILE_APPLICABILITY_MISMATCH",
        ),
        (
            lambda case: case["query"]["queries"][0]["result"].update(
                {"required_source_ordinal": 2}
            ),
            "AUTO_BIND_REQUIRED_SOURCE_ORDINAL_MISMATCH: 1",
        ),
    ],
)
def test_profile_library_query_fingerprints_and_applicability_fail_closed(
    mutation: Any,
    expected: str,
) -> None:
    case = _case()
    mutation(case)

    with pytest.raises(AutoBindingError, match=expected):
        _compile(case)


@pytest.mark.parametrize(
    ("argument", "expected"),
    [
        ("profile_sha256", "AUTO_BIND_PLAN_SCHEMA_INVALID"),
        ("query_bundle_sha256", "AUTO_BIND_PLAN_SCHEMA_INVALID"),
    ],
)
def test_malformed_profile_and_query_hash_arguments_are_rejected(
    argument: str,
    expected: str,
) -> None:
    case = _case()

    with pytest.raises(AutoBindingError, match=expected):
        _compile(case, **{argument: "not-a-sha256"})
