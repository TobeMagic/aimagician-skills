from __future__ import annotations

import sys
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.query import QueryError, _suitability_safe, inspect_certified_deck, query_catalog, serialize_query_result  # noqa: E402
from pptx_studio.composition import style_signature  # noqa: E402
from manage_pptx_studio_library import run  # noqa: E402


def _catalog() -> tuple[dict[str, object], dict[str, object]]:
    page = {
        "page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001",
        "deck_id": "deck_aaaaaaaaaaaaaaaaaaaaaaaa",
        "category": "003-封面模板",
        "render": {"image_sha256": "b" * 64},
        "component_eligible": True,
        "shapes": [{"max_chars": 90}],
    }
    catalog = {
        "active_categories": ["003-封面模板"],
        "decks": [{"deck_id": page["deck_id"], "category": page["category"]}],
        "pages": [page],
        "regions": [{
            "region_id": "region_aaaaaaaaaaaaaaaaaaaa",
            "page_id": page["page_id"],
            "region_kind": "title",
            "capacity": {"max_text_chars": 30},
        }, {
            "region_id": "region_bbbbbbbbbbbbbbbbbbbb",
            "page_id": page["page_id"],
            "region_kind": "content-item",
            "capacity": {"max_text_chars": 30},
        }],
    }
    observations = {
        page["page_id"]: {
            "page_id": page["page_id"],
            "image_sha256": "b" * 64,
            "observation": {
                "semantic_tags": ["annual-report", "finance"],
                "suggested_roles": ["cover"],
                "visual_style": ["dark", "editorial"],
                "uncertainty": "none",
            },
        }
    }
    return catalog, observations


def test_query_is_bounded_explainable_and_stable() -> None:
    catalog, observations = _catalog()
    request = {"mode": "region", "role": "cover", "tags": ["finance"], "style": "dark", "capacity": 20, "limit": 6}

    first = query_catalog(catalog, observations=observations, request=request)
    second = query_catalog(catalog, observations=observations, request=request)

    assert serialize_query_result(first) == serialize_query_result(second)
    assert first["status"] == "PASS"
    candidate = first["candidates"][0]
    assert candidate["candidate_id"] == "region_aaaaaaaaaaaaaaaaaaaa"
    assert candidate["deck_id"] == "deck_aaaaaaaaaaaaaaaaaaaaaaaa"
    assert candidate["theme_family_page_count"] == 1
    assert candidate["gates"] == ["active_source", "materialization", "observation_hash", "capacity"]
    assert candidate["scores"]["total"] == 1.0
    assert candidate["scores"]["canonical_role"] == 1.0
    assert "canonical_category_role" in candidate["reasons"]
    assert candidate["style_signature"] == style_signature(catalog["pages"][0], observations)  # type: ignore[index]
    assert candidate["bindable_region_count"] == 2
    assert candidate["governed_content_slot_count"] == 0
    assert candidate["requires_structured_data"] is False


def test_query_marks_native_chart_data_surface_without_exposing_source_content() -> None:
    catalog, observations = _catalog()
    catalog["pages"][0]["materialization"] = {  # type: ignore[index]
        "status": "eligible",
        "governed_content_slot_count": 12,
        "blocker_codes": [],
    }

    result = query_catalog(
        catalog, observations=observations, request={"mode": "page", "role": "cover"},
    )

    candidate = result["candidates"][0]
    assert candidate["governed_content_slot_count"] == 12
    assert candidate["requires_structured_data"] is True
    assert "chart" not in json.dumps(candidate, ensure_ascii=False).casefold()


def test_institutional_finance_subject_filter_does_not_reject_data_cards_as_cars() -> None:
    assert _suitability_safe(
        {"semantic_tags": ["financial report", "data card"], "visual_style": ["corporate"]},
        profile="institutional-finance",
    )
    assert not _suitability_safe(
        {"semantic_tags": ["automotive", "car"], "visual_style": ["corporate"]},
        profile="institutional-finance",
    )


@pytest.mark.parametrize(
    "query_request,error",
    [
        ({"mode": "freeform", "role": "cover"}, "MODE_INVALID"),
        ({"mode": "page", "role": "cover", "client_root": "/client"}, "REQUEST_FIELD_INVALID"),
        ({"mode": "page", "role": "cover", "limit": 7}, "LIMIT_INVALID"),
    ],
)
def test_query_fails_closed_for_invalid_input(query_request: dict[str, object], error: str) -> None:
    catalog, observations = _catalog()
    with pytest.raises(QueryError, match=error):
        query_catalog(catalog, observations=observations, request=query_request)


def test_query_excludes_missing_or_mismatched_observation() -> None:
    catalog, observations = _catalog()
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["image_sha256"] = "c" * 64

    result = query_catalog(catalog, observations=observations, request={"mode": "page", "role": "cover"})

    assert result["status"] == "NO_MATCH"
    assert result["candidates"] == []


@pytest.mark.parametrize(
    ("semantic_tags", "visual_style"),
    [
        (["brand-characters", "company-history"], ["anime", "corporate-blue"]),
        (["landscape", "sailboat", "template"], ["nature-themed", "corporate"]),
        (["automotive", "annual-report"], ["corporate", "dark"]),
        (["traditional Chinese medicine", "pathology", "financial-report"], ["corporate", "green"]),
    ],
)
def test_institutional_finance_query_excludes_incompatible_visual_subjects(
    semantic_tags: list[str], visual_style: list[str],
) -> None:
    catalog, observations = _catalog()
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"].update({
        "semantic_tags": semantic_tags,
        "visual_style": visual_style,
    })
    result = query_catalog(
        catalog,
        observations=observations,
        request={"mode": "page", "role": "cover", "suitability": "institutional-finance"},
    )
    assert result["status"] == "NO_MATCH"


def test_general_query_keeps_subject_specific_pages_available() -> None:
    catalog, observations = _catalog()
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"].update({
        "semantic_tags": ["brand-characters"], "visual_style": ["anime"],
    })
    result = query_catalog(
        catalog, observations=observations,
        request={"mode": "page", "role": "cover", "suitability": "general"},
    )
    assert result["status"] == "PASS"


def test_query_recognizes_certified_chapter_tag_as_section_role() -> None:
    catalog, observations = _catalog()
    catalog["pages"][0]["category"] = "057-优秀作品"  # type: ignore[index]
    catalog["active_categories"] = ["057-优秀作品"]
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"].update({
        "semantic_tags": ["chapter_title", "annual-report"],
        "suggested_roles": ["title"],
    })
    result = query_catalog(
        catalog, observations=observations,
        request={"mode": "page", "role": "section"},
    )
    assert result["status"] == "PASS"


def test_query_can_revalidate_a_bounded_preselected_candidate() -> None:
    catalog, observations = _catalog()
    result = query_catalog(
        catalog, observations=observations,
        request={
            "mode": "page", "role": "cover", "candidate_ids": [
                "page_aaaaaaaaaaaaaaaaaaaaaaaa_001",
            ],
        },
    )
    assert result["status"] == "PASS"
    assert result["candidates"][0]["page_id"] == "page_aaaaaaaaaaaaaaaaaaaaaaaa_001"


def test_query_treats_returned_style_signature_as_an_exact_anchor_filter() -> None:
    catalog, observations = _catalog()
    signature = style_signature(catalog["pages"][0], observations)  # type: ignore[index]
    other = {
        "page_id": "page_cccccccccccccccccccccccc_001",
        "deck_id": "deck_cccccccccccccccccccccccc",
        "category": "003-封面模板",
        "render": {"image_sha256": "d" * 64},
        "component_eligible": True,
        "shapes": [{"max_chars": 90}],
    }
    catalog["pages"].append(other)  # type: ignore[union-attr]
    observations[other["page_id"]] = {
        "page_id": other["page_id"], "image_sha256": "d" * 64,
        "observation": {
            "semantic_tags": ["annual-report"],
            "suggested_roles": ["cover"],
            "visual_style": ["dark", "corporate"],
            "uncertainty": "none",
        },
    }

    result = query_catalog(
        catalog,
        observations=observations,
        request={"mode": "page", "role": "cover", "style": signature},
    )

    assert [item["page_id"] for item in result["candidates"]] == [
        "page_aaaaaaaaaaaaaaaaaaaaaaaa_001",
    ]


def test_query_can_constrain_role_retrieval_to_returned_complete_theme_family() -> None:
    catalog, observations = _catalog()
    sibling = {
        "page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_002",
        "deck_id": "deck_aaaaaaaaaaaaaaaaaaaaaaaa",
        "category": "039-结尾模板",
        "render": {"image_sha256": "c" * 64},
        "component_eligible": True,
        "shapes": [{"max_chars": 90}],
    }
    catalog["active_categories"].append("039-结尾模板")  # type: ignore[union-attr]
    catalog["pages"].append(sibling)  # type: ignore[union-attr]
    catalog["regions"].extend([  # type: ignore[union-attr]
        {"region_id": "region_sibling_1", "page_id": sibling["page_id"], "region_kind": "title", "capacity": {"max_text_chars": 30}},
    ])
    observations[sibling["page_id"]] = {
        "page_id": sibling["page_id"], "image_sha256": "c" * 64,
        "observation": {"semantic_tags": ["annual-report"], "suggested_roles": ["closing"], "visual_style": ["dark", "editorial"], "uncertainty": "none"},
    }

    result = query_catalog(
        catalog,
        observations=observations,
        request={"mode": "page", "role": "closing", "deck_id": "deck_aaaaaaaaaaaaaaaaaaaaaaaa"},
    )

    assert [item["page_id"] for item in result["candidates"]] == [sibling["page_id"]]


def test_inspect_certified_deck_exposes_only_hash_bound_value_free_page_inventory() -> None:
    catalog, observations = _catalog()
    sibling = {
        "page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_002",
        "deck_id": "deck_aaaaaaaaaaaaaaaaaaaaaaaa",
        "category": "003-封面模板",
        "render": {"image_sha256": "c" * 64},
        "component_eligible": True,
        "shapes": [{"max_chars": 30}],
        "slide_number": 2,
    }
    catalog["pages"][0]["slide_number"] = 1  # type: ignore[index]
    catalog["pages"].append(sibling)  # type: ignore[union-attr]
    catalog["regions"].append({  # type: ignore[union-attr]
        "region_id": "region_sibling_1", "page_id": sibling["page_id"],
        "region_kind": "title", "editable_shape_ids": ["2"],
        "capacity": {"max_text_chars": 30},
    })
    observations[sibling["page_id"]] = {
        "page_id": sibling["page_id"], "image_sha256": "c" * 64,
        "observation": {
            "semantic_tags": ["annual-report"], "suggested_roles": ["chart"],
            "visual_style": ["dark", "editorial"], "composition": "chart left",
            "hierarchy": "title then chart", "text_density": "low", "uncertainty": "none",
        },
    }

    result = inspect_certified_deck(
        catalog, observations=observations, deck_id="deck_aaaaaaaaaaaaaaaaaaaaaaaa",
    )

    assert result["status"] == "PASS"
    assert [item["page_id"] for item in result["pages"]] == [
        "page_aaaaaaaaaaaaaaaaaaaaaaaa_001", sibling["page_id"],
    ]
    assert result["pages"][1]["content_grammar"] == {"title": 1, "content": 0}
    assert "package_sha256" not in result["pages"][1]


def test_inspect_certified_deck_fails_closed_for_unknown_or_hash_drifted_family() -> None:
    catalog, observations = _catalog()
    assert inspect_certified_deck(catalog, observations=observations, deck_id="deck_" + "c" * 24)["status"] == "NO_MATCH"
    observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["image_sha256"] = "c" * 64
    assert inspect_certified_deck(catalog, observations=observations, deck_id="deck_" + "a" * 24)["status"] == "NO_MATCH"


def test_query_excludes_catalog_page_blocked_by_physical_materialization() -> None:
    catalog, observations = _catalog()
    catalog["pages"][0]["materialization"] = {  # type: ignore[index]
        "status": "blocked",
        "governed_content_slot_count": 4,
        "blocker_codes": ["chart-reference-cache-unmapped"],
    }

    result = query_catalog(
        catalog,
        observations=observations,
        request={"mode": "page", "role": "cover"},
    )

    assert result["status"] == "NO_MATCH"


def test_cover_query_rejects_weak_complete_theme_family() -> None:
    catalog, observations = _catalog()
    catalog["pages"][0]["render"]["visual_quality"] = 0.91  # type: ignore[index]
    weak_deck = "deck_cccccccccccccccccccccccc"
    for ordinal in range(1, 9):
        page_id = f"page_cccccccccccccccccccccccc_{ordinal:03d}"
        image_sha = f"{ordinal:064x}"
        page = {
            "page_id": page_id,
            "deck_id": weak_deck,
            "category": "003-封面模板",
            "render": {"image_sha256": image_sha, "visual_quality": 0.70},
            "component_eligible": True,
            "shapes": [{"max_chars": 90}],
        }
        catalog["pages"].append(page)  # type: ignore[union-attr]
        catalog["regions"].extend([  # type: ignore[union-attr]
            {"region_id": f"region_d{ordinal}a", "page_id": page_id, "region_kind": "title", "capacity": {"max_text_chars": 30}},
            {"region_id": f"region_d{ordinal}b", "page_id": page_id, "region_kind": "content-item", "capacity": {"max_text_chars": 30}},
        ])
        observations[page_id] = {
            "page_id": page_id,
            "image_sha256": image_sha,
            "observation": observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"],
        }
    catalog["decks"].append({"deck_id": weak_deck, "category": "003-封面模板"})  # type: ignore[union-attr]

    result = query_catalog(catalog, observations=observations, request={"mode": "page", "role": "cover"})

    assert result["status"] == "PASS"
    assert all(item["deck_id"] != weak_deck for item in result["candidates"])
    assert result["candidates"][0]["theme_family_visual_quality"]["mean"] == 0.91


def test_cover_query_prefers_certified_complete_family_over_orphan() -> None:
    catalog, observations = _catalog()
    catalog["pages"][0]["render"]["visual_quality"] = 0.98  # type: ignore[index]
    full_deck = "deck_dddddddddddddddddddddddd"
    for ordinal in range(1, 9):
        page_id = f"page_dddddddddddddddddddddddd_{ordinal:03d}"
        image_sha = f"{ordinal + 10:064x}"
        page = {
            "page_id": page_id,
            "deck_id": full_deck,
            "category": "003-封面模板",
            "render": {"image_sha256": image_sha, "visual_quality": 0.85},
            "component_eligible": True,
            "shapes": [{"max_chars": 90}],
        }
        catalog["pages"].append(page)  # type: ignore[union-attr]
        catalog["regions"].extend([  # type: ignore[union-attr]
            {"region_id": f"region_full_{ordinal}a", "page_id": page_id, "region_kind": "title", "capacity": {"max_text_chars": 30}},
            {"region_id": f"region_full_{ordinal}b", "page_id": page_id, "region_kind": "content-item", "capacity": {"max_text_chars": 30}},
        ])
        observations[page_id] = {
            "page_id": page_id,
            "image_sha256": image_sha,
            "observation": observations["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]["observation"],
        }
    catalog["decks"].append({"deck_id": full_deck, "category": "003-封面模板"})  # type: ignore[union-attr]

    result = query_catalog(catalog, observations=observations, request={"mode": "page", "role": "cover"})

    assert result["candidates"][0]["deck_id"] == full_deck


def test_query_rejects_candidate_filter_for_region_mode() -> None:
    catalog, observations = _catalog()
    with pytest.raises(QueryError, match="CANDIDATE_IDS_MODE_INVALID"):
        query_catalog(
            catalog, observations=observations,
            request={"mode": "region", "role": "cover", "candidate_ids": ["region_aaaaaaaaaaaaaaaaaaaa"]},
        )


def test_canonical_category_role_outranks_incorrect_visual_role() -> None:
    catalog, observations = _catalog()
    other = {
        "page_id": "page_cccccccccccccccccccccccc_001",
        "deck_id": "deck_cccccccccccccccccccccccc",
        "category": "038-标题模板",
        "render": {"image_sha256": "d" * 64},
        "component_eligible": True,
        "shapes": [{"max_chars": 90}],
    }
    catalog["active_categories"].append("038-标题模板")  # type: ignore[union-attr]
    catalog["pages"].append(other)  # type: ignore[union-attr]
    observations[other["page_id"]] = {
        "page_id": other["page_id"], "image_sha256": "d" * 64,
        "observation": {"semantic_tags": ["finance"], "suggested_roles": ["cover"], "visual_style": ["dark"], "uncertainty": "none"},
    }

    result = query_catalog(catalog, observations=observations, request={"mode": "page", "role": "cover"})

    assert result["candidates"][0]["page_id"] == "page_aaaaaaaaaaaaaaaaaaaaaaaa_001"


def test_cli_query_uses_catalog_and_complete_observations_only(tmp_path: Path) -> None:
    catalog, observations = _catalog()
    manifest = tmp_path / "manifest.json"
    source, archive = tmp_path / "source", tmp_path / "archive"
    source.mkdir()
    archive.mkdir()
    catalog_path, observations_path, request_path, output_path = (tmp_path / name for name in ("catalog.json", "observations.json", "request.json", "result.json"))
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    observations_path.write_text(json.dumps({"status": "COMPLETE", "observations": list(observations.values())}), encoding="utf-8")
    request_path.write_text(json.dumps({"mode": "page", "role": "cover"}), encoding="utf-8")

    result = run(["query", "--source-root", str(source), "--archive-root", str(archive), "--manifest", str(manifest), "--catalog", str(catalog_path), "--observation-index", str(observations_path), "--query-input", str(request_path), "--query-output", str(output_path)])

    assert result["status"] == "PASS"
    candidate = json.loads(output_path.read_text(encoding="utf-8"))["candidates"][0]
    assert candidate["page_id"] == "page_aaaaaaaaaaaaaaaaaaaaaaaa_001"
    assert candidate["style_signature"].startswith("style_")
    assert not manifest.exists(), "query must accept the documented client-local manifest sentinel"


def test_cli_query_batch_keeps_requests_separate_and_accepts_manifest_sentinel(tmp_path: Path) -> None:
    catalog, observations = _catalog()
    source, archive = tmp_path / "source", tmp_path / "archive"
    source.mkdir()
    archive.mkdir()
    catalog_path, observations_path, request_path, output_path = (tmp_path / name for name in ("catalog.json", "observations.json", "batch.json", "result.json"))
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    observations_path.write_text(json.dumps({"status": "COMPLETE", "observations": list(observations.values())}), encoding="utf-8")
    request_path.write_text(json.dumps({"queries": [
        {"request_id": "cover", "request": {"mode": "page", "role": "cover", "tags": [], "style": None, "capacity": 0, "limit": 2, "suitability": "general"}},
        {"request_id": "contents", "request": {"mode": "page", "role": "contents", "tags": [], "style": None, "capacity": 0, "limit": 2, "suitability": "general"}},
    ]}), encoding="utf-8")

    result = run(["query-batch", "--source-root", str(source), "--archive-root", str(archive), "--manifest", str(tmp_path / "missing-sentinel.json"), "--catalog", str(catalog_path), "--observation-index", str(observations_path), "--query-input", str(request_path), "--query-output", str(output_path)])

    assert result["status"] == "NO_MATCH"
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert [item["request_id"] for item in payload["results"]] == ["cover", "contents"]
    assert payload["results"][0]["result"]["status"] == "PASS"
    assert payload["results"][1]["result"]["status"] == "NO_MATCH"
