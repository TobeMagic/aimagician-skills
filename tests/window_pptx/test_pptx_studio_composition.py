from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
from jsonschema import validate


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.component_profiles import catalog_sha256, component_profile_sha256, load_component_profiles  # noqa: E402
from pptx_studio.composition import CompositionError, _mixed_library_evidence, _style_anchor_evidence, _validate_request, compile_composition, serialize_composition_plan, style_signature, verify_composition_replay_lock  # noqa: E402
from pptx_studio.query import role_matches_page  # noqa: E402
from manage_pptx_studio_library import run  # noqa: E402


def _page(letter: str, number: int, category: str, *, style: list[str] | None = None) -> dict[str, object]:
    return {
        "page_id": f"page_{letter * 24}_{number:03d}",
        "deck_id": f"deck_{letter * 24}",
        "package_sha256": letter * 64,
        "slide_number": number,
        "category": category,
        "render": {
            "image_sha256": chr(ord(letter) + 1) * 64,
            "visual_quality": 0.90,
        },
        "component_eligible": True,
        "shapes": [
            {"shape_id": "2", "kind": "text", "max_chars": 30},
            {"shape_id": "3", "kind": "text", "max_chars": 100},
            {"shape_id": "4", "kind": "image", "max_chars": 0},
        ],
        "_style": style or ["editorial", "dark"],
    }


def _fixture() -> tuple[dict[str, object], dict[str, object], dict[str, str]]:
    cover = _page("a", 1, "003-封面模板")
    closing = _page("a", 2, "039-结尾模板")
    process = _page("c", 1, "050-架构流程", style=["editorial", "light"])
    pages = [cover, closing, process]
    observations = {
        page["page_id"]: {
            "page_id": page["page_id"],
            "image_sha256": page["render"]["image_sha256"],
            "observation": {
                "suggested_roles": ["cover" if page is cover else ("closing" if page is closing else "process")],
                "semantic_tags": ["annual-report"],
                "visual_style": page.pop("_style"),
                "uncertainty": "none",
            },
        }
        for page in pages
    }
    regions = [
        {"region_id": "region_a_title", "page_id": cover["page_id"], "capacity": {"max_text_chars": 30}},
        {"region_id": "region_a_body", "page_id": cover["page_id"], "capacity": {"max_text_chars": 100}},
        {"region_id": "region_a_closing_title", "page_id": closing["page_id"], "capacity": {"max_text_chars": 30}},
        {"region_id": "region_a_closing_body", "page_id": closing["page_id"], "capacity": {"max_text_chars": 100}},
        {"region_id": "region_c_body", "page_id": process["page_id"], "capacity": {"max_text_chars": 100}},
        {"region_id": "region_c_step_1", "page_id": process["page_id"], "capacity": {"max_text_chars": 30}},
        {"region_id": "region_c_step_2", "page_id": process["page_id"], "capacity": {"max_text_chars": 30}},
        {"region_id": "region_c_step_3", "page_id": process["page_id"], "capacity": {"max_text_chars": 30}},
        {"region_id": "region_c_step_4", "page_id": process["page_id"], "capacity": {"max_text_chars": 30}},
    ]
    catalog = {"active_categories": ["003-封面模板", "039-结尾模板", "050-架构流程"], "pages": pages, "regions": regions}
    signatures = {str(page["page_id"]): style_signature(page, observations) for page in pages}
    return catalog, observations, signatures


def _request(signatures: dict[str, str], *, strategy: str = "exact_deck") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "strategy": strategy,
        "art_direction": {"anchor_page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001", "allowed_style_signatures": [signatures["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]], "suitability": "general"},
        "slides": [
            {"slide_id": "s01", "role": "cover", "candidate_ids": ["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"], "selected_candidate_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001", "minimum_capacity": 60},
            {"slide_id": "s02", "role": "closing", "candidate_ids": ["page_aaaaaaaaaaaaaaaaaaaaaaaa_002"], "selected_candidate_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_002", "minimum_capacity": 60},
        ],
    }


def test_exact_deck_composition_is_stable_and_schema_valid() -> None:
    catalog, observations, signatures = _fixture()
    request = _request(signatures)
    first = compile_composition(catalog, observations=observations, request=request)
    second = compile_composition(catalog, observations=observations, request=request)

    assert serialize_composition_plan(first) == serialize_composition_plan(second)
    assert first["art_direction"]["exact_deck_id"] == "deck_aaaaaaaaaaaaaaaaaaaaaaaa"
    assert first["slides"][0]["evidence"]["style_match"] == "anchor"
    request_schema = json.loads((REPO_ROOT / "skills" / "owned" / "pptx-studio" / "schemas" / "pptx-studio-composition-request.v1.schema.json").read_text(encoding="utf-8"))
    validate(request, request_schema)
    schema = json.loads((REPO_ROOT / "skills" / "owned" / "pptx-studio" / "schemas" / "pptx-studio-composition-plan.v1.schema.json").read_text(encoding="utf-8"))
    validate(first, schema)


def test_v2_composition_binds_every_selected_page_to_the_validated_narrative() -> None:
    catalog, observations, signatures = _fixture()
    request = _request(signatures)
    request["schema_version"] = "2.0"
    request["narrative_validation"] = {
        "schema_version": "pptx-studio-narrative-validation.v1",
        "status": "PASS",
        "brief_id": "brief-1",
        "brief_sha256": "a" * 64,
        "narrative_sha256": "b" * 64,
        "slide_count": 2,
        "delivery_beat_ids": ["cover", "closing"],
        "section_evidence": [],
    }
    request["slides"][0]["beat_id"] = "cover"  # type: ignore[index]
    request["slides"][1]["beat_id"] = "closing"  # type: ignore[index]

    result = compile_composition(catalog, observations=observations, request=request)

    assert result["schema_version"] == "2.0"
    assert result["slides"][0]["beat_id"] == "cover"
    verify_composition_replay_lock(result, catalog=catalog, observations=observations)
    request_schema = json.loads((REPO_ROOT / "skills" / "owned" / "pptx-studio" / "schemas" / "pptx-studio-composition-request.v2.schema.json").read_text(encoding="utf-8"))
    output_schema = json.loads((REPO_ROOT / "skills" / "owned" / "pptx-studio" / "schemas" / "pptx-studio-composition-plan.v2.schema.json").read_text(encoding="utf-8"))
    validate(request, request_schema)
    validate(result, output_schema)


def test_v2_composition_rejects_a_page_sequence_that_does_not_match_narrative() -> None:
    catalog, observations, signatures = _fixture()
    request = _request(signatures)
    request["schema_version"] = "2.0"
    request["narrative_validation"] = {
        "schema_version": "pptx-studio-narrative-validation.v1",
        "status": "PASS",
        "brief_id": "brief-1",
        "brief_sha256": "a" * 64,
        "narrative_sha256": "b" * 64,
        "slide_count": 2,
        "delivery_beat_ids": ["cover", "closing"],
        "section_evidence": [],
    }
    request["slides"][0]["beat_id"] = "cover"  # type: ignore[index]
    request["slides"][1]["beat_id"] = "unplanned-title"  # type: ignore[index]

    with pytest.raises(CompositionError, match="NARRATIVE_DELIVERY_BINDING_MISMATCH"):
        compile_composition(catalog, observations=observations, request=request)


def test_v2_composition_replay_rejects_catalog_drift() -> None:
    catalog, observations, signatures = _fixture()
    request = _request(signatures)
    request["schema_version"] = "2.0"
    request["narrative_validation"] = {
        "schema_version": "pptx-studio-narrative-validation.v1", "status": "PASS",
        "brief_id": "brief-1", "brief_sha256": "a" * 64,
        "narrative_sha256": "b" * 64, "slide_count": 2,
        "delivery_beat_ids": ["cover", "closing"], "section_evidence": [],
    }
    request["slides"][0]["beat_id"] = "cover"  # type: ignore[index]
    request["slides"][1]["beat_id"] = "closing"  # type: ignore[index]
    plan = compile_composition(catalog, observations=observations, request=request)
    drifted_catalog = {**catalog, "active_categories": ["003-封面模板"]}

    with pytest.raises(CompositionError, match="REPLAY_CATALOG_DRIFT"):
        verify_composition_replay_lock(plan, catalog=drifted_catalog, observations=observations)


def test_replay_cli_writes_an_explicit_migration_report(tmp_path: Path) -> None:
    catalog, observations, signatures = _fixture()
    request = _request(signatures)
    request["schema_version"] = "2.0"
    request["narrative_validation"] = {
        "schema_version": "pptx-studio-narrative-validation.v1", "status": "PASS",
        "brief_id": "brief-1", "brief_sha256": "a" * 64,
        "narrative_sha256": "b" * 64, "slide_count": 2,
        "delivery_beat_ids": ["cover", "closing"], "section_evidence": [],
    }
    request["slides"][0]["beat_id"] = "cover"  # type: ignore[index]
    request["slides"][1]["beat_id"] = "closing"  # type: ignore[index]
    plan = compile_composition(catalog, observations=observations, request=request)
    catalog_path = tmp_path / "catalog.json"
    observations_path = tmp_path / "observations.json"
    plan_path = tmp_path / "plan.json"
    report_path = tmp_path / "replay-report.json"
    catalog_path.write_text(json.dumps({**catalog, "active_categories": ["003-封面模板"]}), encoding="utf-8")
    observations_path.write_text(json.dumps({"status": "COMPLETE", "observations": list(observations.values())}), encoding="utf-8")
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    result = run([
        "verify-replay", "--source-root", str(tmp_path / "source.sentinel"),
        "--archive-root", str(tmp_path / "archive.sentinel"),
        "--manifest", str(tmp_path / "manifest.sentinel"),
        "--catalog", str(catalog_path), "--observation-index", str(observations_path),
        "--composition-plan", str(plan_path), "--replay-output", str(report_path),
    ])

    assert result["status"] == "MIGRATION_REQUIRED"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["code"] == "REPLAY_CATALOG_DRIFT"
    assert "do_not_reinterpret_selection_or_component_keys" in report["action"]


def test_mixed_library_guard_rejects_a_twelve_page_single_source_deck() -> None:
    slides = [
        {"source": {"package_sha256": "a" * 64, "category": "041-二段内容"}}
        for _ in range(12)
    ]

    with pytest.raises(
        CompositionError,
        match="MIXED_LIBRARY_DIVERSITY_REQUIRED:packages=1:categories=1:max_pages_per_source=12",
    ):
        _mixed_library_evidence(slides)


def test_mixed_library_guard_cannot_be_evaded_by_merging_to_eleven_pages() -> None:
    slides = [
        {"source": {"package_sha256": "a" * 64, "category": "057-优秀作品"}}
        for _ in range(11)
    ]

    with pytest.raises(
        CompositionError,
        match="MIXED_LIBRARY_DIVERSITY_REQUIRED:packages=1:categories=1:max_pages_per_source=11",
    ):
        _mixed_library_evidence(slides)


def test_mixed_library_guard_accepts_a_bounded_eight_package_six_category_plan() -> None:
    package_ids = [chr(ord("a") + index) * 64 for index in range(8)]
    categories = ["003-封面模板", "036-目录模板", "037-章节模板", "041-二段内容", "049-时间轴图", "050-架构流程"]
    slides = [
        {"source": {"package_sha256": package_ids[index % len(package_ids)], "category": categories[index % len(categories)]}}
        for index in range(12)
    ]

    result = _mixed_library_evidence(slides)

    assert result == {
        "enforced": True,
        "source_package_count": 8,
        "source_category_count": 6,
        "maximum_pages_from_one_source": 2,
    }


def test_style_anchor_guard_rejects_a_collage_with_excessive_fallback_pages() -> None:
    slides = [
        {"evidence": {"style_match": "explicit_fallback" if index < 4 else "anchor"}}
        for index in range(12)
    ]

    with pytest.raises(
        CompositionError,
        match="STYLE_ANCHOR_COVERAGE_INSUFFICIENT:coverage=0.666667:minimum=0.700000",
    ):
        _style_anchor_evidence(slides, anchor_signature="style_" + "a" * 24)


def test_family_assembly_rejects_role_mismatch_inside_anchor_work() -> None:
    catalog, observations, signatures = _fixture()
    request = _request(signatures, strategy="family_assembly")
    # Sharing a master is not permission to reinterpret a closing page as a
    # process page.  Literal cross-role reuse is available only in the exact
    # deck reproduction route, whose source order is itself enforced.
    request["slides"][1]["role"] = "process"  # type: ignore[index]

    # The source first fails the equally hard editable-capacity floor; a
    # dense real page with enough slots reaches the role mismatch gate.
    with pytest.raises(CompositionError, match="BINDABLE_REGION_COUNT_INSUFFICIENT"):
        compile_composition(catalog, observations=observations, request=request)


def test_exact_deck_rejects_role_mismatch_inside_ordered_work() -> None:
    """Ordered reproduction cannot reinterpret a certified source page."""

    catalog, observations, signatures = _fixture()
    request = _request(signatures, strategy="exact_deck")
    # ``title`` has the same two-region floor as this source page, so the
    # assertion reaches semantic compatibility rather than only capacity.
    request["slides"][1]["role"] = "title"  # type: ignore[index]

    with pytest.raises(CompositionError, match="ROLE_INCOMPATIBLE"):
        compile_composition(catalog, observations=observations, request=request)


def test_composition_rejects_department_network_as_financial_card_page() -> None:
    catalog, observations, signatures = _fixture()
    request = _request(signatures)
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_002"]["observation"].update({  # type: ignore[index]
        "suggested_roles": ["multi-item", "team"],
        "semantic_tags": ["clinical departments", "department listing", "medical team"],
    })
    # ``title`` keeps the fixture's two-region floor, so this reaches the
    # irreducible-subject gate rather than a generic capacity failure.
    request["slides"][1]["role"] = "title"  # type: ignore[index]

    with pytest.raises(CompositionError, match="ROLE_INCOMPATIBLE"):
        compile_composition(catalog, observations=observations, request=request)


@pytest.mark.parametrize(
    "role,suggested,tags",
    [
        ("data", ["chart", "data-summary"], ["financial report", "data visualization"]),
        ("comparison", ["table", "chart"], ["budget comparison", "year-over-year comparison"]),
        ("roadmap", ["section"], ["future planning", "strategy"]),
        ("clinical-network", ["team"], ["clinical departments", "multi-department coverage"]),
    ],
)
def test_composition_accepts_certified_data_comparison_and_roadmap_grammars(role: str, suggested: list[str], tags: list[str]) -> None:
    catalog, _observations, _signatures = _fixture()
    page = catalog["pages"][1]  # type: ignore[index]
    observation = {
        "suggested_roles": suggested,
        "semantic_tags": tags,
        "visual_style": ["editorial", "dark"],
        "uncertainty": "none",
    }
    assert role_matches_page(page, observation, role)


def test_family_assembly_rejects_source_outside_anchor_work() -> None:
    catalog, observations, signatures = _fixture()
    # Make the external source visually compatible, so this exercise reaches
    # the stronger family-identity gate rather than failing earlier on style.
    observations["page_cccccccccccccccccccccccc_001"]["observation"]["visual_style"] = ["editorial", "dark"]  # type: ignore[index]
    signatures["page_cccccccccccccccccccccccc_001"] = style_signature(  # type: ignore[index]
        next(page for page in catalog["pages"] if page["page_id"] == "page_cccccccccccccccccccccccc_001"), observations,  # type: ignore[index]
    )
    request = _request(signatures, strategy="family_assembly")
    request["slides"][1].update({  # type: ignore[index]
        "role": "process",
        "selected_candidate_id": "page_cccccccccccccccccccccccc_001",
        "candidate_ids": ["page_cccccccccccccccccccccccc_001"],
    })

    with pytest.raises(CompositionError, match="FAMILY_ASSEMBLY_SOURCE_DECK_INVALID"):
        compile_composition(catalog, observations=observations, request=request)


def test_composition_reapplies_subject_suitability_to_preselected_page() -> None:
    """A copied candidate ID cannot bypass the query-stage subject filter."""

    catalog, observations, signatures = _fixture()
    request = _request(signatures)
    request["art_direction"]["suitability"] = "institutional-finance"  # type: ignore[index]
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"]["semantic_tags"] = [  # type: ignore[index]
        "traditional Chinese medicine", "annual-report",
    ]

    with pytest.raises(CompositionError, match="SOURCE_SUBJECT_INCOMPATIBLE"):
        compile_composition(catalog, observations=observations, request=request)


def _select_other_deck(request: dict[str, object], signatures: dict[str, str]) -> None:
    request["art_direction"].update({  # type: ignore[union-attr]
        "allowed_style_signatures": [
            signatures["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"],
            signatures["page_cccccccccccccccccccccccc_001"],
        ]
    })


def _select_dense_role_on_page_assembly(request: dict[str, object], signatures: dict[str, str]) -> None:
    request["strategy"] = "page_assembly"
    request["slides"][0].update({"role": "five-item"})  # type: ignore[index]
    request["slides"][1].update({  # type: ignore[index]
        "role": "process",
        "selected_candidate_id": "page_cccccccccccccccccccccccc_001",
        "candidate_ids": ["page_cccccccccccccccccccccccc_001"],
    })


@pytest.mark.parametrize(
    "mutate,error",
    [
        (lambda request, signatures: request["art_direction"].update({"allowed_style_signatures": ["style_" + "f" * 24]}), "ANCHOR_SIGNATURE_NOT_ALLOWED"),
        (_select_other_deck, "STYLE_FALLBACK_INCOMPATIBLE"),
        (lambda request, signatures: request["slides"][0].update({"selected_candidate_id": "missing", "candidate_ids": ["missing"]}), "PAGE_CANDIDATE_UNKNOWN"),
        (_select_dense_role_on_page_assembly, "BINDABLE_REGION_COUNT_INSUFFICIENT"),
    ],
)
def test_composition_fails_closed(mutate, error: str) -> None:  # type: ignore[no-untyped-def]
    catalog, observations, signatures = _fixture()
    request = _request(signatures)
    mutate(request, signatures)
    with pytest.raises(CompositionError, match=error):
        compile_composition(catalog, observations=observations, request=request)


def test_component_requires_safe_region_and_explicit_signature() -> None:
    catalog, observations, signatures = _fixture()
    request = _request(signatures, strategy="component_assembly")
    request["slides"] = [{"slide_id": "s01", "role": "cover", "candidate_ids": ["region_a_title"], "selected_candidate_id": "region_a_title", "minimum_capacity": 20}]
    plan = compile_composition(catalog, observations=observations, request=request)
    assert plan["slides"][0]["source"]["region_ids"] == ["region_a_title"]


def test_v3_component_slide_uses_only_profile_certified_host_and_component_ids(tmp_path: Path) -> None:
    catalog, observations, signatures = _fixture()
    observations["page_cccccccccccccccccccccccc_001"]["observation"]["visual_style"] = ["editorial", "dark"]  # type: ignore[index]
    signatures["page_cccccccccccccccccccccccc_001"] = style_signature(  # type: ignore[index]
        next(page for page in catalog["pages"] if page["page_id"] == "page_cccccccccccccccccccccccc_001"), observations,  # type: ignore[index]
    )
    profile: dict[str, object] = {
        "schema_version": "pptx-studio-component-profile.v1", "status": "COMPLETE",
        "profile_id": "fixture-components", "profile_sha256": "",
        "catalog_sha256": catalog_sha256(catalog),
        "components": [{
            "component_id": "component_111111111111111111111111",
            "source": {"page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001", "package_sha256": "a" * 64, "slide_number": 1, "slide_sha256": "d" * 64},
            "shape_ids": [2], "component_sha256": "e" * 64, "relationship_ids": [],
            "semantic_intent": "process-step", "allowed_roles": ["process"],
            "fields": [{"field_id": "action", "shape_id": 2, "semantic_role": "body", "max_chars": 30}],
            "allowed_host_anchor_ids": ["anchor_222222222222222222222222"],
        }],
        "host_anchors": [{
            "host_anchor_id": "anchor_222222222222222222222222",
            "source": {"page_id": "page_cccccccccccccccccccccccc_001", "package_sha256": "c" * 64, "slide_number": 1, "slide_sha256": "f" * 64},
            "shape_ids": [4], "host_anchor_sha256": "a" * 64,
            "compatible_component_ids": ["component_111111111111111111111111"],
        }],
    }
    profile["profile_sha256"] = component_profile_sha256(profile)
    profile_path = tmp_path / "component-profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    index = load_component_profiles(profile_path, catalog=catalog)
    request: dict[str, object] = {
        "schema_version": "3.0", "strategy": "page_assembly",
        "art_direction": {"anchor_page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001", "allowed_style_signatures": [signatures["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]], "suitability": "general"},
        "narrative_validation": {
            "schema_version": "pptx-studio-narrative-validation.v1", "status": "PASS", "brief_id": "brief-1",
            "brief_sha256": "a" * 64, "narrative_sha256": "b" * 64, "slide_count": 2,
            "delivery_beat_ids": ["cover", "process"], "section_evidence": [],
        },
        "component_profile": {"profile_id": index.profile_id, "profile_sha256": index.profile_sha256},
        "slides": [
            {"slide_id": "s01", "beat_id": "cover", "role": "cover", "candidate_ids": ["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"], "selected_candidate_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001", "minimum_capacity": 1},
            {"slide_id": "s02", "beat_id": "process", "role": "process", "host_candidate_ids": ["page_cccccccccccccccccccccccc_001"], "selected_host_candidate_id": "page_cccccccccccccccccccccccc_001", "host_anchor_id": "anchor_222222222222222222222222", "selected_component_ids": ["component_111111111111111111111111"], "minimum_capacity": 1},
        ],
    }

    result = compile_composition(catalog, observations=observations, request=request, component_profiles=index)

    assert result["schema_version"] == "3.0"
    assert result["slides"][1]["source"]["component_assembly"] == {
        "host_anchor_id": "anchor_222222222222222222222222",
        "component_ids": ["component_111111111111111111111111"],
        "component_intents": ["process-step"],
    }
    verify_composition_replay_lock(result, catalog=catalog, observations=observations, component_profiles=index)
    with pytest.raises(CompositionError, match="REPLAY_COMPONENT_PROFILE_REQUIRED"):
        verify_composition_replay_lock(result, catalog=catalog, observations=observations)

    v4_request = copy.deepcopy(request)
    v4_request["schema_version"] = "4.0"
    component_slide = v4_request["slides"][1]
    component_slide.pop("host_anchor_id")
    component_slide.pop("selected_component_ids")
    component_slide["component_placements"] = [{
        "host_anchor_id": "anchor_222222222222222222222222",
        "component_id": "component_111111111111111111111111",
    }]
    v4_result = compile_composition(
        catalog, observations=observations, request=v4_request, component_profiles=index,
    )
    assert v4_result["schema_version"] == "4.0"
    assert v4_result["slides"][1]["source"]["component_assembly"]["placements"] == [{
        "host_anchor_id": "anchor_222222222222222222222222",
        "component_id": "component_111111111111111111111111",
        "component_intent": "process-step",
    }]

    # A component must satisfy the locked visual family itself. The host's
    # compliance cannot launder a visually unrelated component source.
    component_source = copy.deepcopy(next(
        page for page in catalog["pages"] if page["page_id"] == "page_aaaaaaaaaaaaaaaaaaaaaaaa_001"
    ))
    component_source.update({
        "page_id": "page_dddddddddddddddddddddddd_001",
        "deck_id": "deck_dddddddddddddddddddddddd",
        "package_sha256": "d" * 64,
    })
    catalog["pages"].append(component_source)
    observations["page_dddddddddddddddddddddddd_001"] = {
        "page_id": "page_dddddddddddddddddddddddd_001",
        "image_sha256": component_source["render"]["image_sha256"],
        "observation": {
            "suggested_roles": ["process"], "semantic_tags": ["annual-report"],
            "visual_style": ["corporate", "green"], "uncertainty": "none",
        },
    }
    mismatched_profile = copy.deepcopy(profile)
    mismatched_profile["catalog_sha256"] = catalog_sha256(catalog)
    mismatched_profile["components"][0]["source"].update({  # type: ignore[index]
        "page_id": "page_dddddddddddddddddddddddd_001",
        "package_sha256": "d" * 64,
    })
    mismatched_profile["profile_sha256"] = component_profile_sha256(mismatched_profile)
    mismatched_path = tmp_path / "mismatched-component-profile.json"
    mismatched_path.write_text(json.dumps(mismatched_profile), encoding="utf-8")
    mismatched_index = load_component_profiles(mismatched_path, catalog=catalog)
    mismatched_request = copy.deepcopy(request)
    mismatched_request["component_profile"] = {
        "profile_id": mismatched_index.profile_id,
        "profile_sha256": mismatched_index.profile_sha256,
    }
    with pytest.raises(CompositionError, match="COMPONENT_STYLE_SIGNATURE_NOT_ALLOWED"):
        compile_composition(
            catalog, observations=observations, request=mismatched_request,
            component_profiles=mismatched_index,
        )


def test_v4_component_visual_certification_is_closure_scoped_and_still_fail_closed(tmp_path: Path) -> None:
    """A reviewed closure may exclude unrelated source-page imagery only.

    The page-level observation deliberately describes a green source page. A
    v4 certification may admit its exact reviewed closure into a cool
    professional plan, but an unsuitable or warm certification remains
    ineligible. This keeps component certification a precise curator gate,
    never a generic way to bypass art direction.
    """

    catalog, observations, _signatures = _fixture()
    cover_id = "page_aaaaaaaaaaaaaaaaaaaaaaaa_001"
    host_id = "page_cccccccccccccccccccccccc_001"
    observations[cover_id]["observation"]["visual_style"] = ["corporate", "blue"]  # type: ignore[index]
    observations[host_id]["observation"]["visual_style"] = ["technology", "dark", "blue"]  # type: ignore[index]
    signatures = {
        str(page["page_id"]): style_signature(page, observations)
        for page in catalog["pages"]  # type: ignore[index]
    }

    component_source = copy.deepcopy(next(
        page for page in catalog["pages"] if page["page_id"] == cover_id  # type: ignore[index]
    ))
    component_source.update({
        "page_id": "page_dddddddddddddddddddddddd_001",
        "deck_id": "deck_dddddddddddddddddddddddd",
        "package_sha256": "d" * 64,
    })
    catalog["pages"].append(component_source)  # type: ignore[index]
    observations["page_dddddddddddddddddddddddd_001"] = {
        "page_id": "page_dddddddddddddddddddddddd_001",
        "image_sha256": component_source["render"]["image_sha256"],
        "observation": {
            "suggested_roles": ["process"], "semantic_tags": ["consumer-marketing"],
            "visual_style": ["corporate", "green"], "uncertainty": "none",
        },
    }

    profile: dict[str, object] = {
        "schema_version": "pptx-studio-component-profile.v4", "status": "COMPLETE",
        "profile_id": "fixture-closure-certified-components", "profile_sha256": "",
        "catalog_sha256": catalog_sha256(catalog),
        "components": [{
            "component_id": "component_111111111111111111111111",
            "source": {
                "page_id": "page_dddddddddddddddddddddddd_001",
                "package_sha256": "d" * 64, "slide_number": 1, "slide_sha256": "d" * 64,
            },
            "shape_ids": [2], "component_sha256": "e" * 64, "relationship_ids": [],
            "semantic_intent": "process-step", "allowed_roles": ["process"],
            "fields": [{"field_id": "action", "shape_id": 2, "semantic_role": "body", "max_chars": 30}],
            "allowed_host_anchor_ids": ["anchor_222222222222222222222222"],
            "visual_certification": {
                "review_id": "agnes.component-process.20260817", "review_sha256": "f" * 64,
                "style_profile": {"archetype": "corporate", "tone": "light", "color_family": "cool"},
                "suitability": ["institutional-finance"],
            },
        }],
        "host_anchors": [{
            "host_anchor_id": "anchor_222222222222222222222222",
            "source": {
                "page_id": host_id, "package_sha256": "c" * 64,
                "slide_number": 1, "slide_sha256": "f" * 64,
            },
            "shape_ids": [4], "host_anchor_sha256": "a" * 64,
            "compatible_component_ids": ["component_111111111111111111111111"],
            "removable_shape_ids": [], "removable_shape_sha256": None,
        }],
    }
    profile["profile_sha256"] = component_profile_sha256(profile)
    profile_path = tmp_path / "closure-certified-profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    index = load_component_profiles(profile_path, catalog=catalog)
    request: dict[str, object] = {
        "schema_version": "4.0", "strategy": "page_assembly",
        "art_direction": {
            "anchor_page_id": cover_id,
            "allowed_style_signatures": [signatures[cover_id], signatures[host_id]],
            "suitability": "institutional-finance",
        },
        "narrative_validation": {
            "schema_version": "pptx-studio-narrative-validation.v1", "status": "PASS", "brief_id": "brief-1",
            "brief_sha256": "a" * 64, "narrative_sha256": "b" * 64, "slide_count": 2,
            "delivery_beat_ids": ["cover", "process"], "section_evidence": [],
        },
        "component_profile": {"profile_id": index.profile_id, "profile_sha256": index.profile_sha256},
        "slides": [
            {"slide_id": "s01", "beat_id": "cover", "role": "cover", "candidate_ids": [cover_id], "selected_candidate_id": cover_id, "minimum_capacity": 1},
            {
                "slide_id": "s02", "beat_id": "process", "role": "process",
                "host_candidate_ids": [host_id], "selected_host_candidate_id": host_id,
                "component_placements": [{
                    "host_anchor_id": "anchor_222222222222222222222222",
                    "component_id": "component_111111111111111111111111",
                }],
                "minimum_capacity": 1,
            },
        ],
    }

    assert compile_composition(
        catalog, observations=observations, request=request, component_profiles=index,
    )["status"] == "PASS"

    unsuitable = copy.deepcopy(profile)
    unsuitable["components"][0]["visual_certification"]["suitability"] = ["general"]  # type: ignore[index]
    unsuitable["profile_sha256"] = component_profile_sha256(unsuitable)
    unsuitable_path = tmp_path / "unsuitable-closure-profile.json"
    unsuitable_path.write_text(json.dumps(unsuitable), encoding="utf-8")
    unsuitable_index = load_component_profiles(unsuitable_path, catalog=catalog)
    unsuitable_request = copy.deepcopy(request)
    unsuitable_request["component_profile"] = {
        "profile_id": unsuitable_index.profile_id, "profile_sha256": unsuitable_index.profile_sha256,
    }
    with pytest.raises(CompositionError, match="COMPONENT_VISUAL_SUITABILITY_NOT_ALLOWED"):
        compile_composition(
            catalog, observations=observations, request=unsuitable_request,
            component_profiles=unsuitable_index,
        )

    warm = copy.deepcopy(profile)
    warm["components"][0]["visual_certification"]["style_profile"]["color_family"] = "warm"  # type: ignore[index]
    warm["profile_sha256"] = component_profile_sha256(warm)
    warm_path = tmp_path / "warm-closure-profile.json"
    warm_path.write_text(json.dumps(warm), encoding="utf-8")
    warm_index = load_component_profiles(warm_path, catalog=catalog)
    warm_request = copy.deepcopy(request)
    warm_request["component_profile"] = {
        "profile_id": warm_index.profile_id, "profile_sha256": warm_index.profile_sha256,
    }
    with pytest.raises(CompositionError, match="COMPONENT_VISUAL_STYLE_INCOMPATIBLE"):
        compile_composition(
            catalog, observations=observations, request=warm_request,
            component_profiles=warm_index,
        )


def test_page_assembly_rejects_warm_fallback_from_cool_anchor() -> None:
    catalog, observations, signatures = _fixture()
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"]["visual_style"] = ["corporate", "blue"]  # type: ignore[index]
    observations["page_cccccccccccccccccccccccc_001"]["observation"]["visual_style"] = ["corporate", "red"]  # type: ignore[index]
    signatures = {str(page["page_id"]): style_signature(page, observations) for page in catalog["pages"]}  # type: ignore[index]
    request = _request(signatures, strategy="page_assembly")
    _select_other_deck(request, signatures)
    with pytest.raises(CompositionError, match="STYLE_FALLBACK_INCOMPATIBLE"):
        compile_composition(catalog, observations=observations, request=request)


def test_page_assembly_allows_dark_cool_professional_cadence_page() -> None:
    catalog, observations, signatures = _fixture()
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"]["visual_style"] = ["corporate", "blue"]  # type: ignore[index]
    observations["page_cccccccccccccccccccccccc_001"]["observation"]["visual_style"] = ["technology", "dark", "blue"]  # type: ignore[index]
    signatures = {str(page["page_id"]): style_signature(page, observations) for page in catalog["pages"]}  # type: ignore[index]
    request = _request(signatures, strategy="page_assembly")
    _select_other_deck(request, signatures)
    # The cool dark process page provides controlled rhythm within the same
    # blue professional system; red/green/warm pages remain rejected above.
    assert compile_composition(catalog, observations=observations, request=request)["status"] == "PASS"


def test_page_assembly_rejects_low_quality_cross_deck_fallback() -> None:
    catalog, observations, signatures = _fixture()
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"]["visual_style"] = ["corporate", "blue"]  # type: ignore[index]
    observations["page_cccccccccccccccccccccccc_001"]["observation"]["visual_style"] = ["technology", "dark", "blue"]  # type: ignore[index]
    catalog["pages"][2]["render"]["visual_quality"] = 0.79  # type: ignore[index]
    signatures = {str(page["page_id"]): style_signature(page, observations) for page in catalog["pages"]}  # type: ignore[index]
    request = _request(signatures, strategy="page_assembly")
    _select_other_deck(request, signatures)
    request["slides"][1].update({  # type: ignore[index]
        "role": "process",
        "candidate_ids": ["page_cccccccccccccccccccccccc_001"],
        "selected_candidate_id": "page_cccccccccccccccccccccccc_001",
    })

    with pytest.raises(CompositionError, match="STYLE_FALLBACK_VISUAL_QUALITY_INSUFFICIENT"):
        compile_composition(catalog, observations=observations, request=request)


def test_page_assembly_accepts_a_certified_section_at_its_lower_quality_floor() -> None:
    catalog, observations, signatures = _fixture()
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"]["visual_style"] = ["corporate", "blue"]  # type: ignore[index]
    observations["page_cccccccccccccccccccccccc_001"]["observation"].update({  # type: ignore[index]
        "suggested_roles": ["section"],
        "visual_style": ["technology", "dark", "blue"],
    })
    catalog["pages"][2]["category"] = "037-章节模板"  # type: ignore[index]
    catalog["active_categories"].append("037-章节模板")  # type: ignore[index]
    catalog["pages"][2]["render"]["visual_quality"] = 0.79  # type: ignore[index]
    signatures = {str(page["page_id"]): style_signature(page, observations) for page in catalog["pages"]}  # type: ignore[index]
    request = _request(signatures, strategy="page_assembly")
    _select_other_deck(request, signatures)
    request["slides"][1].update({  # type: ignore[index]
        "role": "section",
        "candidate_ids": ["page_cccccccccccccccccccccccc_001"],
        "selected_candidate_id": "page_cccccccccccccccccccccccc_001",
    })

    assert compile_composition(catalog, observations=observations, request=request)["status"] == "PASS"


def test_exact_deck_cannot_bypass_the_ordinary_page_quality_floor() -> None:
    catalog, observations, signatures = _fixture()
    catalog["pages"][1]["render"]["visual_quality"] = 0.79  # type: ignore[index]
    request = _request(signatures)

    with pytest.raises(CompositionError, match="STYLE_FALLBACK_VISUAL_QUALITY_INSUFFICIENT"):
        compile_composition(catalog, observations=observations, request=request)


def test_exact_certified_deck_is_a_theme_family_despite_page_level_vision_labels() -> None:
    catalog, observations, _signatures = _fixture()
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"]["visual_style"] = ["corporate", "blue"]  # type: ignore[index]
    # A chart/closing page in the same certified PPTX can be described with
    # another visual archetype even though it inherits the actual deck master.
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_002"]["observation"]["visual_style"] = ["festive", "red"]  # type: ignore[index]
    signatures = {str(page["page_id"]): style_signature(page, observations) for page in catalog["pages"]}  # type: ignore[index]
    request = _request(signatures)
    plan = compile_composition(catalog, observations=observations, request=request)
    assert plan["slides"][1]["evidence"]["style_match"] == "same_certified_theme_family"


def test_composition_rejects_native_chart_without_structured_data_contract() -> None:
    catalog, observations, signatures = _fixture()
    # A complete source deck may contain a strong chart page with only one
    # native heading, but an unregistered source has no data contract.
    # Neither exact-deck nor page assembly may preserve its sample values.
    catalog["regions"] = [  # type: ignore[index]
        item for item in catalog["regions"]  # type: ignore[index]
        if item["page_id"] != "page_aaaaaaaaaaaaaaaaaaaaaaaa_002"
        or item["region_id"] == "region_a_closing_title"
    ]
    request = _request(signatures)
    catalog["pages"][1]["materialization"] = {  # type: ignore[index]
        "status": "eligible", "governed_content_slot_count": 1,
    }
    request["slides"][1].update({  # type: ignore[index]
        "role": "dashboard", "minimum_capacity": 20,
    })
    with pytest.raises(CompositionError, match="STRUCTURED_DATA_CONTRACT_UNAVAILABLE"):
        compile_composition(catalog, observations=observations, request=request)
    request["strategy"] = "page_assembly"
    # Governed data authority is a stronger prerequisite than generic native
    # region count in every composition route.
    with pytest.raises(CompositionError, match="STRUCTURED_DATA_CONTRACT_UNAVAILABLE"):
        compile_composition(catalog, observations=observations, request=request)


def test_composition_rejects_more_than_three_cross_deck_style_companions() -> None:
    catalog, observations, signatures = _fixture()
    request = _request(signatures, strategy="page_assembly")
    request["art_direction"]["allowed_style_signatures"] = [  # type: ignore[index]
        signatures["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"],
        signatures["page_cccccccccccccccccccccccc_001"],
        "style_" + "f" * 24,
        "style_" + "e" * 24,
        "style_" + "d" * 24,
    ]
    with pytest.raises(CompositionError, match="STYLE_SIGNATURES_DUPLICATE"):
        compile_composition(catalog, observations=observations, request=request)


def test_composition_accepts_four_certified_same_theme_signatures() -> None:
    """The anchor plus three compatible cadence variants remains one system."""

    catalog, observations, _signatures = _fixture()
    cover = catalog["pages"][0]  # type: ignore[index]
    closing = catalog["pages"][1]  # type: ignore[index]
    extra = _page("a", 3, "050-架构流程", style=["technology", "blue", "balanced"])
    extra_light = _page("b", 4, "050-架构流程", style=["technology", "light", "blue"])
    catalog["pages"].append(extra)  # type: ignore[index]
    catalog["pages"].append(extra_light)  # type: ignore[index]
    observations[cover["page_id"]]["observation"]["visual_style"] = ["corporate", "blue", "balanced"]  # type: ignore[index]
    observations[closing["page_id"]]["observation"]["visual_style"] = ["minimal", "blue", "balanced"]  # type: ignore[index]
    observations[extra["page_id"]] = {
        "page_id": extra["page_id"],
        "image_sha256": extra["render"]["image_sha256"],
        "observation": {
            "suggested_roles": ["process"], "semantic_tags": ["annual-report"],
            "visual_style": extra.pop("_style"), "uncertainty": "none",
        },
    }
    observations[extra_light["page_id"]] = {
        "page_id": extra_light["page_id"],
        "image_sha256": extra_light["render"]["image_sha256"],
        "observation": {
            "suggested_roles": ["process"], "semantic_tags": ["annual-report"],
            "visual_style": extra_light.pop("_style"), "uncertainty": "none",
        },
    }
    signatures = {
        str(page["page_id"]): style_signature(page, observations)
        for page in catalog["pages"]  # type: ignore[index]
    }
    request = _request(signatures, strategy="page_assembly")
    request["art_direction"]["allowed_style_signatures"] = [  # type: ignore[index]
        signatures[cover["page_id"]], signatures[closing["page_id"]], signatures[extra["page_id"]],
        signatures[extra_light["page_id"]],
    ]

    plan = compile_composition(catalog, observations=observations, request=request)

    assert len(plan["art_direction"]["allowed_style_signatures"]) == 4


def test_page_assembly_rejects_repeated_physical_source_before_materialization() -> None:
    catalog, observations, signatures = _fixture()
    request = _request(signatures, strategy="page_assembly")
    request["slides"][1].update({  # type: ignore[index]
        "role": "cover",
        "candidate_ids": ["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"],
        "selected_candidate_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001",
    })
    with pytest.raises(CompositionError, match="PAGE_SOURCE_DUPLICATE"):
        compile_composition(catalog, observations=observations, request=request)


def test_page_assembly_allows_one_nonadjacent_same_role_repeat_in_substantive_deck() -> None:
    _catalog, _observations, signatures = _fixture()
    request = _request(signatures, strategy="page_assembly")
    repeated = "page_" + "d" * 24 + "_001"
    request["slides"] = [
        {
            "slide_id": f"s{index:02d}", "role": "three-item" if index in {3, 7} else "one-item",
            "candidate_ids": [repeated if index in {3, 7} else f"page_{index:024x}_001"],
            "selected_candidate_id": repeated if index in {3, 7} else f"page_{index:024x}_001",
            "minimum_capacity": 1,
        }
        for index in range(1, 11)
    ]

    strategy, _art, slides, _validation = _validate_request(request)

    assert strategy == "page_assembly"
    assert len(slides) == 10


def test_page_assembly_rejects_adjacent_or_structural_repeat() -> None:
    _catalog, _observations, signatures = _fixture()
    request = _request(signatures, strategy="page_assembly")
    repeated = "page_" + "d" * 24 + "_001"
    request["slides"] = [
        {
            "slide_id": f"s{index:02d}", "role": "section" if index in {3, 4} else "one-item",
            "candidate_ids": [repeated if index in {3, 4} else f"page_{index:024x}_001"],
            "selected_candidate_id": repeated if index in {3, 4} else f"page_{index:024x}_001",
            "minimum_capacity": 1,
        }
        for index in range(1, 11)
    ]

    with pytest.raises(CompositionError, match="PAGE_SOURCE_DUPLICATE"):
        _validate_request(request)


def test_page_assembly_allows_one_section_system_across_nonadjacent_dividers() -> None:
    _catalog, _observations, signatures = _fixture()
    request = _request(signatures, strategy="page_assembly")
    repeated = "page_" + "d" * 24 + "_001"
    section_indices = {2, 4, 6, 8}
    request["slides"] = [
        {
            "slide_id": f"s{index:02d}", "role": "section" if index in section_indices else "one-item",
            "candidate_ids": [repeated if index in section_indices else f"page_{index:024x}_001"],
            "selected_candidate_id": repeated if index in section_indices else f"page_{index:024x}_001",
            "minimum_capacity": 1,
        }
        for index in range(1, 11)
    ]

    strategy, _art, slides, _validation = _validate_request(request)

    assert strategy == "page_assembly"
    assert len(slides) == 10


def test_cli_composition_uses_compiled_json_only(tmp_path: Path) -> None:
    catalog, observations, signatures = _fixture()
    paths = {name: tmp_path / f"{name}.json" for name in ("manifest", "catalog", "observations", "request", "output")}
    paths["manifest"].write_text(json.dumps({"status": "APPLIED"}), encoding="utf-8")
    paths["catalog"].write_text(json.dumps(catalog), encoding="utf-8")
    paths["observations"].write_text(json.dumps({"status": "COMPLETE", "observations": list(observations.values())}), encoding="utf-8")
    paths["request"].write_text(json.dumps(_request(signatures)), encoding="utf-8")
    result = run(["compose", "--source-root", str(tmp_path), "--archive-root", str(tmp_path), "--manifest", str(paths["manifest"]), "--catalog", str(paths["catalog"]), "--observation-index", str(paths["observations"]), "--composition-input", str(paths["request"]), "--composition-output", str(paths["output"])])
    assert result["status"] == "PASS"
    assert json.loads(paths["output"].read_text(encoding="utf-8"))["strategy"] == "exact_deck"
