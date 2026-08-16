from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.component_profiles import (  # noqa: E402
    ComponentProfileError,
    catalog_sha256,
    component_profile_sha256,
    load_component_profiles,
    query_component_profiles,
)


def _catalog() -> dict[str, object]:
    return {
        "pages": [
            {
                "page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001",
                "package_sha256": "a" * 64,
                "slide_number": 1,
            },
            {
                "page_id": "page_bbbbbbbbbbbbbbbbbbbbbbbb_002",
                "package_sha256": "b" * 64,
                "slide_number": 2,
            },
        ],
    }


def _profile(catalog: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "pptx-studio-component-profile.v1",
        "status": "COMPLETE",
        "profile_id": "gaojie-component-core-v1",
        "profile_sha256": "",
        "catalog_sha256": catalog_sha256(catalog),
        "components": [
            {
                "component_id": "component_111111111111111111111111",
                "source": {
                    "page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001",
                    "package_sha256": "a" * 64,
                    "slide_number": 1,
                    "slide_sha256": "c" * 64,
                },
                "shape_ids": [2, 3],
                "component_sha256": "d" * 64,
                "relationship_ids": ["rId7"],
                "semantic_intent": "timeline-milestone",
                "allowed_roles": ["timeline"],
                "fields": [{"field_id": "date", "shape_id": 2, "semantic_role": "label", "max_chars": 12}],
                "allowed_host_anchor_ids": ["anchor_222222222222222222222222"],
            }
        ],
        "host_anchors": [
            {
                "host_anchor_id": "anchor_222222222222222222222222",
                "source": {
                    "page_id": "page_bbbbbbbbbbbbbbbbbbbbbbbb_002",
                    "package_sha256": "b" * 64,
                    "slide_number": 2,
                    "slide_sha256": "e" * 64,
                },
                "shape_ids": [4],
                "host_anchor_sha256": "f" * 64,
                "compatible_component_ids": ["component_111111111111111111111111"],
            }
        ],
    }
    payload["profile_sha256"] = component_profile_sha256(payload)
    return payload


def _write(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "component-profile.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_profile_selection_is_opaque_and_catalog_bound(tmp_path: Path) -> None:
    catalog = _catalog()
    profile = load_component_profiles(_write(tmp_path, _profile(catalog)), catalog=catalog)

    anchor, components = profile.validate_selection(
        host_page_id="page_bbbbbbbbbbbbbbbbbbbbbbbb_002",
        host_anchor_id="anchor_222222222222222222222222",
        component_ids=("component_111111111111111111111111",),
    )

    assert anchor.host_anchor_id.startswith("anchor_")
    assert components[0].component_id.startswith("component_")
    assert components[0].semantic_intent == "timeline-milestone"


def test_profile_fails_closed_on_catalog_or_profile_drift(tmp_path: Path) -> None:
    catalog = _catalog()
    payload = _profile(catalog)
    path = _write(tmp_path, payload)

    drifted_catalog = _catalog()
    drifted_catalog["pages"][0]["slide_number"] = 3  # type: ignore[index]
    with pytest.raises(ComponentProfileError, match="COMPONENT_PROFILE_CATALOG_DRIFT"):
        load_component_profiles(path, catalog=drifted_catalog)

    payload["components"][0]["semantic_intent"] = "mutated"  # type: ignore[index]
    with pytest.raises(ComponentProfileError, match="COMPONENT_PROFILE_FINGERPRINT_INVALID"):
        load_component_profiles(_write(tmp_path, payload), catalog=catalog)


def test_profile_rejects_host_component_pair_not_explicitly_certified(tmp_path: Path) -> None:
    catalog = _catalog()
    payload = _profile(catalog)
    payload["host_anchors"][0]["compatible_component_ids"] = []  # type: ignore[index]
    payload["profile_sha256"] = component_profile_sha256(payload)
    profile = load_component_profiles(_write(tmp_path, payload), catalog=catalog)

    with pytest.raises(ComponentProfileError, match="COMPONENT_PROFILE_ANCHOR_INCOMPATIBLE"):
        profile.validate_selection(
            host_page_id="page_bbbbbbbbbbbbbbbbbbbbbbbb_002",
            host_anchor_id="anchor_222222222222222222222222",
            component_ids=("component_111111111111111111111111",),
        )


def test_profile_validates_v4_distinct_component_anchor_placements(tmp_path: Path) -> None:
    catalog = _catalog()
    payload = _profile(catalog)
    # The active private library has four-KPI and up-to-six-card families.
    # V4 must keep each native component tied to its own reservation rather
    # than silently treating a many-component list as one placement.
    for value, shape_id in ((3, 5), (4, 6), (5, 7)):
        component_id = f"component_{value:024x}"
        anchor_id = f"anchor_{value + 3:024x}"
        payload["components"].append({  # type: ignore[index]
            "component_id": component_id,
            "source": {
                "page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001",
                "package_sha256": "a" * 64,
                "slide_number": 1,
                "slide_sha256": "c" * 64,
            },
            "shape_ids": [shape_id], "component_sha256": f"{value:x}" * 64,
            "relationship_ids": [], "semantic_intent": "timeline-milestone",
            "allowed_roles": ["timeline"],
            "fields": [{"field_id": "action", "shape_id": shape_id, "semantic_role": "body", "max_chars": 20}],
            "allowed_host_anchor_ids": [anchor_id],
        })
        payload["host_anchors"].append({  # type: ignore[index]
            "host_anchor_id": anchor_id,
            "source": {
                "page_id": "page_bbbbbbbbbbbbbbbbbbbbbbbb_002",
                "package_sha256": "b" * 64,
                "slide_number": 2,
                "slide_sha256": "e" * 64,
            },
            "shape_ids": [shape_id + 3], "host_anchor_sha256": f"{value + 3:x}" * 64,
            "compatible_component_ids": [component_id],
        })
    payload["profile_sha256"] = component_profile_sha256(payload)
    profile = load_component_profiles(_write(tmp_path, payload), catalog=catalog)

    placements = profile.validate_placements(
        host_page_id="page_bbbbbbbbbbbbbbbbbbbbbbbb_002",
        placements=(
            ("anchor_222222222222222222222222", "component_111111111111111111111111"),
            ("anchor_000000000000000000000006", "component_000000000000000000000003"),
            ("anchor_000000000000000000000007", "component_000000000000000000000004"),
            ("anchor_000000000000000000000008", "component_000000000000000000000005"),
        ),
    )

    assert [anchor.host_anchor_id for anchor, _component in placements] == [
        "anchor_222222222222222222222222",
        "anchor_000000000000000000000006",
        "anchor_000000000000000000000007",
        "anchor_000000000000000000000008",
    ]
    with pytest.raises(ComponentProfileError, match="COMPONENT_PROFILE_PLACEMENTS_DUPLICATE"):
        profile.validate_placements(
            host_page_id="page_bbbbbbbbbbbbbbbbbbbbbbbb_002",
            placements=(
                ("anchor_222222222222222222222222", "component_111111111111111111111111"),
                ("anchor_222222222222222222222222", "component_000000000000000000000003"),
            ),
        )
    with pytest.raises(ComponentProfileError, match="COMPONENT_PROFILE_PLACEMENTS_INVALID"):
        profile.validate_placements(
            host_page_id="page_bbbbbbbbbbbbbbbbbbbbbbbb_002",
            placements=tuple(
                (f"anchor_{value:024x}", f"component_{value:024x}")
                for value in range(1, 8)
            ),
        )


def test_profile_v4_rejects_malformed_closure_visual_certification(tmp_path: Path) -> None:
    catalog = _catalog()
    payload = _profile(catalog)
    payload["schema_version"] = "pptx-studio-component-profile.v4"
    payload["components"][0]["visual_certification"] = {  # type: ignore[index]
        "review_id": "agnes.component.20260817",
        "review_sha256": "a" * 64,
        "style_profile": {"archetype": "corporate", "tone": "light", "color_family": "cool"},
        "suitability": ["institutional-finance"],
    }
    payload["host_anchors"][0]["removable_shape_ids"] = []  # type: ignore[index]
    payload["host_anchors"][0]["removable_shape_sha256"] = None  # type: ignore[index]
    payload["profile_sha256"] = component_profile_sha256(payload)
    assert load_component_profiles(_write(tmp_path, payload), catalog=catalog).components

    malformed = json.loads(json.dumps(payload))
    malformed["components"][0]["visual_certification"]["review_sha256"] = "not-a-sha"
    malformed["profile_sha256"] = component_profile_sha256(malformed)
    with pytest.raises(ComponentProfileError, match="COMPONENT_PROFILE_VISUAL_CERTIFICATION_INVALID"):
        load_component_profiles(_write(tmp_path, malformed), catalog=catalog)


def test_component_query_returns_only_opaque_selection_data(tmp_path: Path) -> None:
    catalog = _catalog()
    # Query eligibility uses the same catalog/visual authority as page
    # retrieval. These fields are deliberately sufficient but contain no
    # private path, source XML, geometry or shape identifier.
    catalog["pages"][0].update({  # type: ignore[index]
        "materialization": {"status": "eligible"},
    })
    catalog["pages"][1].update({  # type: ignore[index]
        "materialization": {"status": "eligible"},
    })
    profile = load_component_profiles(_write(tmp_path, _profile(catalog)), catalog=catalog)
    observations = {
        page["page_id"]: {"observation": {"semantic_tags": [], "visual_style": ["corporate", "blue"]}}
        for page in catalog["pages"]  # type: ignore[index]
    }

    result = query_component_profiles(
        profile, catalog=catalog, observations=observations,
        request={"role": "timeline", "style": None, "suitability": "general", "limit": 6},
    )

    assert result["status"] == "PASS"
    candidate = result["candidates"][0]
    assert candidate["component_id"].startswith("component_")
    assert candidate["hosts"][0]["host_anchor_id"].startswith("anchor_")
    assert set(candidate["fields"][0]) == {"field_id", "semantic_role", "max_chars"}
    assert "shape_id" not in json.dumps(result)
