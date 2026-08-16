from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from manage_pptx_studio_library import run  # noqa: E402
from pptx_studio.style_planning import (  # noqa: E402
    StylePlanningError,
    _eligible_candidates,
    _eligible_for_cluster,
    _search_selection,
    plan_style_cluster,
)


_ROLES = [
    ("cover", "003-封面模板"), ("contents", "036-目录模板"), ("section-a", "037-章节模板"),
    ("current", "041-二段内容"), ("process", "050-架构流程"), ("summary", "046-多段内容"),
    ("section-b", "037-章节模板"), ("comparison", "042-三段内容"), ("roadmap", "049-时间轴图"),
    ("section-c", "037-章节模板"), ("team", "047-人物介绍"), ("quote", "053-金句模板"),
    ("partners", "054-合作伙伴"), ("closing", "039-结尾模板"),
]


def _fixture() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    active = sorted({category for _, category in _ROLES})
    pages: list[dict[str, object]] = []
    regions: list[dict[str, object]] = []
    observations: dict[str, object] = {}
    for index, (beat_id, category) in enumerate(_ROLES):
        page_id = f"page_{index:024x}_001"
        deck_id = f"deck_{index:024x}"
        image_sha = f"{index + 1:064x}"
        package = f"{index + 1:064x}"
        role = "section" if beat_id.startswith("section") else "multi-item" if beat_id == "summary" else beat_id
        pages.append({
            "page_id": page_id, "deck_id": deck_id, "category": category,
            "package_sha256": package, "slide_number": 1,
            "render": {"image_sha256": image_sha, "visual_quality": 0.91},
            "materialization": {"status": "eligible"},
            "shapes": [{"max_chars": 80}] * 8,
        })
        for slot in range(8):
            regions.append({
                "region_id": f"region_{index:020x}_{slot:03d}", "page_id": page_id,
                "capacity": {"max_text_chars": 80},
            })
        observations[page_id] = {
            "page_id": page_id, "image_sha256": image_sha,
            "observation": {
                "semantic_tags": ["annual-report", "finance"], "suggested_roles": [role],
                "visual_style": ["corporate", "blue", "balanced"], "uncertainty": "none",
            },
        }
    request = {
        "schema_version": "pptx-studio-style-cluster-request.v1", "suitability": "institutional-finance",
        "slides": [
            {"beat_id": beat_id, "role": "section" if beat_id.startswith("section") else "multi-item" if beat_id == "summary" else beat_id, "minimum_capacity": 20}
            for beat_id, _ in _ROLES
        ],
    }
    return {"active_categories": active, "pages": pages, "regions": regions}, observations, request


def test_style_planner_returns_one_exact_compiler_feasible_mixed_selection() -> None:
    catalog, observations, request = _fixture()

    first = plan_style_cluster(catalog, observations=observations, request=request)
    second = plan_style_cluster(catalog, observations=observations, request=request)

    assert first == second
    assert first["status"] == "PASS"
    assert first["evidence"] == {
        "source_package_count": 14, "source_category_count": 12,
        "maximum_pages_from_one_source": 1, "anchor_cluster_coverage": 1.0,
        "reused_page_instance_count": 0, "maximum_reuse_per_page": 4,
        "cross_package_quality_floor": 0.80,
        "estimated_dependency_bytes": 0,
        "maximum_estimated_dependency_bytes": 32 * 1024 * 1024,
    }
    assert len(first["recommended_slides"]) == 14
    assert all(item["candidate_ids"] == [item["selected_candidate_id"]] for item in first["recommended_slides"])
    assert all(item["page_visual_quality"] >= 0.80 for item in first["recommended_slides"][1:])


def test_style_planner_preserves_a_preflighted_locked_cover_anchor() -> None:
    catalog, observations, request = _fixture()
    locked_anchor_page_id = catalog["pages"][0]["page_id"]  # type: ignore[index]
    request["locked_anchor_page_id"] = locked_anchor_page_id

    result = plan_style_cluster(catalog, observations=observations, request=request)

    assert result["status"] == "PASS"
    assert result["art_direction"]["anchor_page_id"] == locked_anchor_page_id


def test_style_planner_keeps_a_certified_blue_skyline_quote_closing_in_a_cool_cluster() -> None:
    """A visually blue skyline closing cannot be rejected as a neutral outlier."""

    catalog, observations, request = _fixture()
    closing_page_id = catalog["pages"][-1]["page_id"]  # type: ignore[index]
    observations[closing_page_id]["observation"]["visual_style"] = [  # type: ignore[index]
        "corporate", "gradient", "inspirational", "minimalist", "modern", "skyline",
    ]

    result = plan_style_cluster(catalog, observations=observations, request=request)

    assert result["status"] == "PASS"
    closing = next(item for item in result["recommended_slides"] if item["beat_id"] == "closing")
    assert closing["selected_candidate_id"] == closing_page_id


def test_style_planner_accepts_a_locked_cover_when_fragment_regions_are_narrower_than_its_native_title_surface() -> None:
    """Do not reject a physically bindable cover solely due to letter regions."""

    catalog, observations, request = _fixture()
    page = catalog["pages"][0]  # type: ignore[index]
    page["shapes"] = [{  # type: ignore[index]
        "kind": "text", "text": "年度总结", "semantic_role": "title",
        "max_chars": 5, "bbox": {"x": 100, "y": 100, "w": 500, "h": 80},
    }]
    for region in catalog["regions"]:  # type: ignore[index]
        if region["page_id"] == page["page_id"]:
            region["region_kind"] = "title"
            region["capacity"] = {"max_text_chars": 1}
    request["slides"] = [{"beat_id": "cover", "role": "cover", "minimum_capacity": 5}]
    request["locked_anchor_page_id"] = page["page_id"]

    result = plan_style_cluster(catalog, observations=observations, request=request)

    assert result["status"] == "PASS"
    assert result["art_direction"]["anchor_page_id"] == page["page_id"]


def test_style_planner_fails_closed_when_the_locked_cover_is_not_a_safe_cover_candidate() -> None:
    catalog, observations, request = _fixture()
    request["locked_anchor_page_id"] = "page_" + "f" * 24 + "_001"

    result = plan_style_cluster(catalog, observations=observations, request=request)

    assert result == {
        "schema_version": "pptx-studio-style-cluster-plan.v1", "status": "NO_MATCH",
        "code": "STYLE_CLUSTER_LOCKED_ANCHOR_NO_MATCH", "missing_beat_ids": ["cover"],
    }


def test_style_planner_fails_closed_when_a_role_has_no_safe_page() -> None:
    catalog, observations, request = _fixture()
    request["slides"][4]["role"] = "map"  # type: ignore[index]

    result = plan_style_cluster(catalog, observations=observations, request=request)

    assert result == {
        "schema_version": "pptx-studio-style-cluster-plan.v1", "status": "NO_MATCH",
        "code": "STYLE_CLUSTER_ROLE_NO_MATCH", "missing_beat_ids": ["process"],
    }


def test_style_planner_reports_a_low_quality_role_as_a_named_library_gap() -> None:
    """Component fallback needs a named beat, not a generic solver failure."""

    catalog, observations, request = _fixture()
    request["slides"] = [request["slides"][0], request["slides"][-1]]  # type: ignore[index]
    for page in catalog["pages"][1:]:  # type: ignore[index]
        page["render"]["visual_quality"] = 0.79  # type: ignore[index]

    result = plan_style_cluster(catalog, observations=observations, request=request)

    assert result == {
        "schema_version": "pptx-studio-style-cluster-plan.v1", "status": "NO_MATCH",
        "code": "STYLE_CLUSTER_ROLE_NO_MATCH", "missing_beat_ids": ["closing"],
    }


def test_style_planner_admits_only_an_opaque_certified_timeline_downshift() -> None:
    """A five-node source cannot impersonate four milestones without authority."""

    page_id = "page_" + "d" * 24 + "_001"
    shapes = [
        {"kind": "text", "text": "项目里程碑", "semantic_role": "title", "max_chars": 12,
         "bbox": {"x": 10, "y": 10, "w": 400, "h": 60}},
    ]
    for index in range(5):
        shapes.extend([
            {"kind": "text", "text": f"2026年{index + 1}月", "semantic_role": "title", "max_chars": 12,
             "bbox": {"x": 100 + index * 100, "y": 100, "w": 80, "h": 30}},
            {"kind": "text", "text": f"阶段{index + 1}行动", "semantic_role": "label", "max_chars": 24,
             "bbox": {"x": 100 + index * 100, "y": 150, "w": 80, "h": 50}},
        ])
    catalog = {
        "active_categories": ["049-时间轴图"],
        "pages": [{
            "page_id": page_id, "deck_id": "deck_" + "d" * 24,
            "category": "049-时间轴图", "package_sha256": "d" * 64,
            "slide_number": 1, "render": {"image_sha256": "e" * 64, "visual_quality": 0.91},
            "materialization": {"status": "eligible"}, "shapes": shapes,
        }],
        "regions": [{
            "region_id": f"region-{index}", "page_id": page_id,
            "capacity": {"max_text_chars": 24},
        } for index in range(10)],
    }
    observations = {page_id: {
        "page_id": page_id, "image_sha256": "e" * 64,
        "observation": {
            "semantic_tags": ["milestone"], "suggested_roles": ["timeline"],
            "visual_style": ["corporate", "blue", "balanced"], "uncertainty": "none",
        },
    }}
    slide = {
        "beat_id": "milestones", "role": "timeline", "minimum_capacity": 5,
        "content_requirements": {"title": 1, "label": 4, "body": 4},
        "minimum_role_capacities": {"title": 4, "label": 8, "body": 8},
    }

    assert _eligible_candidates(
        catalog, observations, slide=slide, suitability="institutional-finance",
    ) == []
    candidates = _eligible_candidates(
        catalog, observations, slide=slide, suitability="institutional-finance",
        sequence_cardinality_adaptation_keys={(page_id, "timeline", 5)},
    )
    assert [candidate["page_id"] for candidate in candidates] == [page_id]
    assert candidates[0]["certified_sequence_cardinality_adaptation"] is True


def test_style_planner_rejects_a_visually_valid_selection_that_exceeds_media_budget() -> None:
    """Do not wait for physical assembly to discover a 14-page media blow-up."""

    catalog, observations, request = _fixture()
    for page in catalog["pages"]:  # type: ignore[index]
        page["materialization"]["dependency_bytes"] = 3 * 1024 * 1024  # type: ignore[index]

    result = plan_style_cluster(catalog, observations=observations, request=request)

    assert result == {
        "schema_version": "pptx-studio-style-cluster-plan.v1", "status": "NO_MATCH",
        "code": "STYLE_CLUSTER_FEASIBILITY_NO_MATCH", "missing_beat_ids": [],
    }


def test_fragment_heavy_business_model_is_excluded_before_fact_binding() -> None:
    """Three one-character lockup fragments are not three client metrics."""

    catalog, observations, _request = _fixture()
    page = catalog["pages"][6]  # type: ignore[index]
    observations[page["page_id"]]["observation"]["suggested_roles"] = ["business-model"]  # type: ignore[index]
    page["materialization"]["fragment_slot_count"] = 3  # type: ignore[index]

    candidates = _eligible_candidates(
        catalog, observations,
        slide={"beat_id": "architecture", "role": "business-model", "minimum_capacity": 1},
        suitability="institutional-finance",
    )

    assert page["page_id"] not in {candidate["page_id"] for candidate in candidates}


def test_dense_visual_skeleton_is_excluded_from_low_cardinality_role() -> None:
    """Three facts cannot release a page with a dashboard-sized visible skeleton."""

    catalog, observations, _request = _fixture()
    page = catalog["pages"][6]  # type: ignore[index]
    observations[page["page_id"]]["observation"]["suggested_roles"] = ["three-item"]  # type: ignore[index]
    page["materialization"]["visual_text_unit_count"] = 29  # type: ignore[index]

    candidates = _eligible_candidates(
        catalog, observations,
        slide={"beat_id": "investment", "role": "three-item", "minimum_capacity": 3},
        suitability="institutional-finance",
    )

    assert candidates == []


def test_risk_role_requires_a_heading_and_one_body_per_risk_record() -> None:
    """A three-record risk register cannot land on an unfillable card shell."""

    catalog, observations, _request = _fixture()
    page = catalog["pages"][6]  # type: ignore[index]
    page["category"] = "057-优秀作品"
    catalog["active_categories"].append("057-优秀作品")  # type: ignore[index]
    observations[page["page_id"]]["observation"]["suggested_roles"] = ["case-study"]  # type: ignore[index]
    page["shapes"] = [  # type: ignore[index]
        {"kind": "text", "text": "风险责任", "semantic_role": "title", "bbox": {"y": 60}, "max_chars": 10},
        *[
            {"kind": "text", "text": f"风险说明{index}", "semantic_role": "body", "bbox": {"y": 240 + index * 160}, "max_chars": 80}
            for index in range(3)
        ],
    ]

    candidates = _eligible_candidates(
        catalog, observations,
        slide={"beat_id": "risk", "role": "risk", "minimum_capacity": 3},
        suitability="institutional-finance",
    )

    assert page["page_id"] in {candidate["page_id"] for candidate in candidates}


def test_content_surface_requirements_filter_a_page_before_binding() -> None:
    """A five-body investment ledger must not select a four-body layout."""

    catalog, observations, _request = _fixture()
    page = catalog["pages"][5]  # type: ignore[index]
    page["category"] = "057-优秀作品"
    catalog["active_categories"].append("057-优秀作品")  # type: ignore[index]
    observations[page["page_id"]]["observation"]["suggested_roles"] = ["multi-item"]  # type: ignore[index]
    page["shapes"] = [  # type: ignore[index]
        {"kind": "text", "text": "投资构成", "semantic_role": "title", "bbox": {"y": 50}, "max_chars": 12},
        *[
            {"kind": "text", "text": f"标签{index}", "semantic_role": "label", "bbox": {"y": 200 + index * 80}, "max_chars": 12}
            for index in range(4)
        ],
        *[
            {"kind": "text", "text": f"内容{index}", "semantic_role": "body", "bbox": {"y": 250 + index * 80}, "max_chars": 72}
            for index in range(4)
        ],
    ]

    candidates = _eligible_candidates(
        catalog, observations,
        slide={
            "beat_id": "investment", "role": "multi-item", "minimum_capacity": 4,
            "content_requirements": {"title": 1, "label": 4, "body": 5},
        },
        suitability="institutional-finance",
    )

    assert page["page_id"] not in {candidate["page_id"] for candidate in candidates}


@pytest.mark.parametrize(
    ("role", "minimum_capacity", "content_requirements", "code"),
    [
        (
            "timeline", 4,
            {"title": 1, "label": 4, "body": 4},
            "STYLE_CLUSTER_SEQUENCE_CAPACITY_INVALID:expected=5:actual=4",
        ),
        (
            "process", 3,
            {"title": 1, "label": 2, "body": 3},
            "STYLE_CLUSTER_SEQUENCE_PAIR_REQUIREMENTS_INVALID",
        ),
        (
            "roadmap", 5,
            {"label": 4, "body": 4},
            "STYLE_CLUSTER_SEQUENCE_TITLE_REQUIREMENT_INVALID",
        ),
    ],
)
def test_sequence_request_requires_title_and_complete_pairs_before_retrieval(
    role: str, minimum_capacity: int, content_requirements: dict[str, int], code: str,
) -> None:
    """Do not turn four dated milestones into a false three-step lookup."""

    catalog, observations, request = _fixture()
    request["slides"] = [
        {
            "beat_id": "cover",
            "role": "cover",
            "minimum_capacity": 1,
        },
        {
            "beat_id": "sequence",
            "role": role,
            "minimum_capacity": minimum_capacity,
            "content_requirements": content_requirements,
        },
    ]

    with pytest.raises(StylePlanningError, match=code):
        plan_style_cluster(catalog, observations=observations, request=request)


def test_role_capacity_requirements_filter_short_native_labels() -> None:
    """A page with enough labels still fails when the longest label cannot fit."""

    catalog, observations, _request = _fixture()
    page = catalog["pages"][5]  # type: ignore[index]
    page["category"] = "057-优秀作品"
    catalog["active_categories"].append("057-优秀作品")  # type: ignore[index]
    observations[page["page_id"]]["observation"]["suggested_roles"] = ["multi-item"]  # type: ignore[index]
    page["shapes"] = [  # type: ignore[index]
        {"kind": "text", "text": "建设方案", "semantic_role": "title", "bbox": {"y": 50}, "max_chars": 12},
        *[
            {"kind": "text", "text": f"标签{index}", "semantic_role": "label", "bbox": {"y": 200 + index * 80}, "max_chars": 7}
            for index in range(3)
        ],
        *[
            {"kind": "text", "text": f"内容{index}", "semantic_role": "body", "bbox": {"y": 250 + index * 80}, "max_chars": 72}
            for index in range(3)
        ],
    ]

    candidates = _eligible_candidates(
        catalog, observations,
        slide={
            "beat_id": "solution", "role": "multi-item", "minimum_capacity": 3,
            "content_requirements": {"title": 1, "label": 3, "body": 3},
            "minimum_role_capacities": {"label": 8},
        },
        suitability="institutional-finance",
    )

    assert page["page_id"] not in {candidate["page_id"] for candidate in candidates}


def test_contents_page_requiring_more_facts_than_the_agenda_is_excluded() -> None:
    """Five agenda facts must not be stretched across eleven native surfaces."""

    catalog, observations, _request = _fixture()
    page = catalog["pages"][1]  # type: ignore[index]
    page["shapes"] = [  # type: ignore[index]
        {
            "kind": "text", "text": "目录", "semantic_role": "title",
            "bbox": {"y": 50}, "max_chars": 6,
        },
        *[
            {
                "kind": "text", "text": f"议题{index}", "semantic_role": "label",
                "bbox": {"y": 300 + index}, "max_chars": 12,
            }
            for index in range(10)
        ],
    ]
    page["materialization"]["visual_text_unit_count"] = 11  # type: ignore[index]

    candidates = _eligible_candidates(
        catalog, observations,
        slide={"beat_id": "agenda", "role": "contents", "minimum_capacity": 5},
        suitability="institutional-finance",
    )

    assert candidates == []


def test_section_page_without_a_real_title_surface_is_excluded() -> None:
    """A content composition is not a divider merely because vision called it one."""

    catalog, observations, _request = _fixture()
    page = catalog["pages"][2]  # type: ignore[index]
    page["shapes"] = [  # type: ignore[index]
        {
            "kind": "text", "text": "行业现状", "semantic_role": "label",
            "bbox": {"y": 300}, "max_chars": 8,
        },
        {
            "kind": "text", "text": "启发与感想", "semantic_role": "label",
            "bbox": {"y": 500}, "max_chars": 8,
        },
    ]

    candidates = _eligible_candidates(
        catalog, observations,
        slide={"beat_id": "current", "role": "section", "minimum_capacity": 2},
        suitability="institutional-finance",
    )

    assert page["page_id"] not in {candidate["page_id"] for candidate in candidates}


def test_closing_page_requires_one_title_surface_that_fits_the_full_request() -> None:
    """An atomic closing request cannot be spread over template ornaments."""

    catalog, observations, _request = _fixture()
    page = catalog["pages"][-1]  # type: ignore[index]
    page["shapes"] = [  # type: ignore[index]
        {
            "kind": "text", "text": "感谢聆听", "semantic_role": "title",
            "bbox": {"y": 80}, "max_chars": 6,
        },
        {
            "kind": "text", "text": "副标题", "semantic_role": "label",
            "bbox": {"y": 620}, "max_chars": 4,
        },
    ]

    candidates = _eligible_candidates(
        catalog, observations,
        slide={"beat_id": "closing", "role": "closing", "minimum_capacity": 14},
        suitability="institutional-finance",
    )

    assert page["page_id"] not in {candidate["page_id"] for candidate in candidates}

    page["shapes"][0]["max_chars"] = 18  # type: ignore[index]
    candidates = _eligible_candidates(
        catalog, observations,
        slide={"beat_id": "closing", "role": "closing", "minimum_capacity": 14},
        suitability="institutional-finance",
    )

    assert page["page_id"] in {candidate["page_id"] for candidate in candidates}


def test_certified_quote_closing_fallback_accepts_one_long_statement_surface() -> None:
    catalog, observations, _request = _fixture()
    page = catalog["pages"][-1]  # type: ignore[index]
    page["category"] = "053-金句模板"
    catalog["active_categories"].append("053-金句模板")  # type: ignore[index]
    page["shapes"] = [  # type: ignore[index]
        {
            "kind": "text", "text": "审议通过", "semantic_role": "title",
            "bbox": {"y": 280}, "max_chars": 17,
        },
        {
            "kind": "text", "text": "说明", "semantic_role": "label",
            "bbox": {"y": 650}, "max_chars": 8,
        },
    ]
    observations[page["page_id"]]["observation"]["suggested_roles"] = ["quote"]  # type: ignore[index]

    candidates = _eligible_candidates(
        catalog, observations,
        slide={"beat_id": "closing", "role": "closing", "minimum_capacity": 14},
        suitability="institutional-finance",
    )

    assert page["page_id"] in {candidate["page_id"] for candidate in candidates}


def test_timeline_native_milestone_count_must_match_the_client_units() -> None:
    """Four client milestones cannot release a five-step native timeline."""

    catalog, observations, _request = _fixture()
    page = catalog["pages"][8]  # type: ignore[index]
    page["shapes"] = [  # type: ignore[index]
        {
            "kind": "text", "text": "实施里程碑", "semantic_role": "title",
            "bbox": {"y": 50}, "max_chars": 10,
        },
        *[
            item
            for index in range(5)
            for item in (
                {
                    "kind": "text", "text": f"20XX.0{index + 1}", "semantic_role": "title",
                    "bbox": {"y": 250, "x": index * 100}, "max_chars": 10,
                },
                {
                    "kind": "text", "text": f"阶段动作{index + 1}", "semantic_role": "label",
                    "bbox": {"y": 400, "x": index * 100}, "max_chars": 20,
                },
            )
        ],
    ]
    page["materialization"]["visual_text_unit_count"] = 11  # type: ignore[index]

    candidates = _eligible_candidates(
        catalog, observations,
        slide={"beat_id": "roadmap", "role": "timeline", "minimum_capacity": 5},
        suitability="institutional-finance",
    )

    assert candidates == []


def test_same_deck_page_does_not_bypass_the_visual_quality_floor() -> None:
    anchor = {
        "page_id": "anchor", "deck_id": "deck", "style_signature": "style",
        "style_profile": {"colour_family": "cool", "tone": "balanced", "professional": True},
        "page_visual_quality": 0.91,
    }
    weak_sibling = {
        **anchor, "page_id": "weak", "page_visual_quality": 0.67,
    }

    assert not _eligible_for_cluster(
        weak_sibling, anchor=anchor, companion_signatures=frozenset(),
    )


def test_style_planner_uses_two_certified_cool_professional_companions_when_required() -> None:
    """A third compatible signature is a bounded cadence tool, not a collage."""

    catalog, observations, request = _fixture()
    styles = [
        ["corporate", "blue", "balanced"],
        ["minimal", "blue", "balanced"],
        ["minimal", "light", "cyan"],
    ]
    for index, page in enumerate(catalog["pages"]):  # type: ignore[index]
        observations[page["page_id"]]["observation"]["visual_style"] = styles[index % len(styles)]  # type: ignore[index]

    plan = plan_style_cluster(catalog, observations=observations, request=request)

    assert plan["status"] == "PASS"
    assert len(plan["art_direction"]["allowed_style_signatures"]) == 3  # type: ignore[index]
    assert all(
        observation["observation"]["visual_style"] != ["festive", "red", "balanced"]
        for observation in observations.values()
    )


def test_style_planner_never_uses_a_warm_companion_for_a_cool_anchor() -> None:
    catalog, observations, request = _fixture()
    for index, page in enumerate(catalog["pages"]):  # type: ignore[index]
        observations[page["page_id"]]["observation"]["visual_style"] = (  # type: ignore[index]
            ["corporate", "blue", "balanced"] if index == 0
            else ["corporate", "red", "balanced"]
        )

    plan = plan_style_cluster(catalog, observations=observations, request=request)

    assert plan == {
        "schema_version": "pptx-studio-style-cluster-plan.v1", "status": "NO_MATCH",
        "code": "STYLE_CLUSTER_FEASIBILITY_NO_MATCH", "missing_beat_ids": [],
    }


def test_style_planner_uses_one_nonadjacent_repeat_only_when_unique_supply_is_short() -> None:
    catalog, observations, request = _fixture()
    repeated_indices = (3, 7, 11)
    candidate_indices = repeated_indices[:2]
    for index in repeated_indices:
        request["slides"][index]["role"] = "three-item"  # type: ignore[index]
    for index in candidate_indices:
        page = catalog["pages"][index]  # type: ignore[index]
        observations[page["page_id"]]["observation"]["suggested_roles"] = ["three-item"]  # type: ignore[index]

    plan = plan_style_cluster(catalog, observations=observations, request=request)

    assert plan["status"] == "PASS"
    selected = [item["selected_candidate_id"] for item in plan["recommended_slides"]]
    assert len(selected) - len(set(selected)) == 1
    assert plan["evidence"]["reused_page_instance_count"] == 1
    duplicate = next(page_id for page_id in selected if selected.count(page_id) == 2)
    positions = [index for index, page_id in enumerate(selected) if page_id == duplicate]
    assert positions[1] - positions[0] > 1


def test_style_search_prunes_adjacent_repeat_before_beam_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    """An illegal high-score state must not evict the legal nonadjacent repeat."""

    import pptx_studio.style_planning as style_planning

    monkeypatch.setattr(style_planning, "_BEAM_WIDTH", 1)
    monkeypatch.setattr(style_planning, "_max_reused_page_instances", lambda _count: 1)
    slides = [
        {"beat_id": "cover", "role": "cover", "minimum_capacity": 1},
        {"beat_id": "first", "role": "three-item", "minimum_capacity": 3},
        {"beat_id": "second", "role": "three-item", "minimum_capacity": 3},
        {"beat_id": "divider", "role": "section", "minimum_capacity": 1},
        {"beat_id": "third", "role": "three-item", "minimum_capacity": 3},
    ]

    def candidate(page: str, role: str, quality: float) -> dict[str, object]:
        return {
            "page_id": page, "deck_id": "deck_anchor", "package_sha256": page,
            "category": role, "style_signature": "style_anchor",
            "style_profile": {"colour_family": "cool", "tone": "balanced", "professional": True},
            "page_visual_quality": quality, "capacity": 20, "dependency_bytes": 0,
            "fragment_slot_count": 0, "visual_text_unit_count": 1,
        }

    anchor = candidate("cover", "cover", 0.95)
    shared = candidate("shared", "three-item", 0.99)
    alternate = candidate("alternate", "three-item", 0.80)
    selected = _search_selection(
        slides,
        [[anchor], [shared], [shared, alternate], [candidate("section", "section", 0.90)], [shared]],
        anchor=anchor,
        companion_signatures=frozenset(),
    )

    assert selected is not None
    page_ids = [item["page_id"] for item in selected]
    assert page_ids == ["cover", "shared", "alternate", "section", "shared"]


def test_style_search_uses_preserved_narrative_indices_across_component_gaps() -> None:
    """A component-filled beat must prevent a false adjacent section repeat."""

    slides = [
        {"beat_id": "cover", "role": "cover", "minimum_capacity": 1, "sequence_index": 0},
        {"beat_id": "section-a", "role": "section", "minimum_capacity": 1, "sequence_index": 1},
        # The omitted component beat occupies narrative index 2.
        {"beat_id": "section-b", "role": "section", "minimum_capacity": 1, "sequence_index": 3},
        {"beat_id": "closing", "role": "closing", "minimum_capacity": 1, "sequence_index": 4},
    ]

    def candidate(page: str, role: str) -> dict[str, object]:
        return {
            "page_id": page, "deck_id": "deck_anchor", "package_sha256": page,
            "category": role, "style_signature": "style_anchor",
            "style_profile": {"color_family": "cool", "tone": "balanced", "archetype": "corporate"},
            "page_visual_quality": 0.90, "capacity": 20, "dependency_bytes": 0,
            "fragment_slot_count": 0, "visual_text_unit_count": 1,
        }

    anchor = candidate("cover", "cover")
    section = candidate("section", "section")
    selection = _search_selection(
        slides, [[anchor], [section], [section], [candidate("closing", "closing")]],
        anchor=anchor, companion_signatures=frozenset(),
    )

    assert selection is not None
    assert [item["page_id"] for item in selection] == ["cover", "section", "section", "closing"]


def test_style_planner_rejects_structured_data_roles_without_a_declared_complete_data_contract() -> None:
    catalog, observations, request = _fixture()
    # The only data-role candidate is a chart/table surface. It must not be
    # selected from a text/fact-only narrative request merely because it has a
    # high visual-quality score.
    data_page = catalog["pages"][5]  # type: ignore[index]
    observations[data_page["page_id"]]["observation"]["suggested_roles"] = ["data"]  # type: ignore[index]
    data_page["materialization"] = {"status": "eligible", "governed_content_slot_count": 3}
    request["slides"][5]["role"] = "data"  # type: ignore[index]

    with pytest.raises(StylePlanningError, match="STYLE_CLUSTER_STRUCTURED_DATA_ROLE_REQUIRES_CONTRACT"):
        plan_style_cluster(catalog, observations=observations, request=request)


def test_style_planner_requires_cover_as_the_first_narrative_beat() -> None:
    catalog, observations, request = _fixture()
    request["slides"][0]["role"] = "contents"  # type: ignore[index]

    with pytest.raises(StylePlanningError, match="STYLE_CLUSTER_COVER_FIRST_REQUIRED"):
        plan_style_cluster(catalog, observations=observations, request=request)


def test_style_planner_cli_writes_safe_plan(tmp_path: Path) -> None:
    catalog, observations, request = _fixture()
    catalog_path = tmp_path / "catalog.json"
    observations_path = tmp_path / "observations.json"
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    observations_path.write_text(json.dumps({"status": "COMPLETE", "observations": list(observations.values())}), encoding="utf-8")
    input_path.write_text(json.dumps(request), encoding="utf-8")

    result = run([
        "plan-style-cluster", "--source-root", str(tmp_path / "source.sentinel"),
        "--archive-root", str(tmp_path / "archive.sentinel"), "--manifest", str(tmp_path / "manifest.sentinel"),
        "--catalog", str(catalog_path), "--observation-index", str(observations_path),
        "--style-cluster-input", str(input_path), "--style-cluster-output", str(output_path),
    ])

    assert result["status"] == "PASS"
    plan = json.loads(output_path.read_text(encoding="utf-8"))
    assert plan["status"] == "PASS"
    assert "private" not in json.dumps(plan).casefold()
