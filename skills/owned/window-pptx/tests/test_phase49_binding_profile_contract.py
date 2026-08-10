from __future__ import annotations

import json
from pathlib import Path

import jsonschema


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = (
    SKILL_ROOT
    / "registries"
    / "v61-binding-profiles"
    / "phase49-work-report-15.binding-profile.v1.json"
)

NARRATIVE_ROLES = (
    "cover",
    "contents",
    "section-governance",
    "policy-evidence",
    "revenue-composition",
    "medical-revenue-comparison",
    "expenditure-table",
    "projects-debt",
    "kpi-dashboard",
    "section-innovation",
    "team",
    "efficiency-comparison",
    "section-roadmap",
    "roadmap",
    "closing",
)

TEMPLATE_ROLES = (
    "cover",
    "contents",
    "section",
    "section",
    "data",
    "data",
    "table",
    "case-study",
    "kpi",
    "section",
    "people",
    "content-blocks",
    "section",
    "process",
    "closing",
)


def _profile() -> dict[str, object]:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def test_phase49_binding_profile_is_schema_valid_and_registered() -> None:
    profile = _profile()
    schema = json.loads(
        (SKILL_ROOT / "schemas" / "binding-profile.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.Draft202012Validator(schema).validate(profile)
    assert profile["profile_id"] == "phase49-work-report-15"
    assert profile["acceptance_profile"] == "phase49-work-report-15"
    assert profile["library_index_sha256"] == (
        "ed4078111e8010d3b171e74463199a8720b7e0d5ca1814a72ff1616b285c42ab"
    )


def test_phase49_binding_profile_locks_exact_acceptance_sequences() -> None:
    slides = sorted(_profile()["slides"], key=lambda item: item["ordinal"])
    assert [slide["ordinal"] for slide in slides] == list(range(1, 16))
    assert [slide["narrative_role"] for slide in slides] == list(NARRATIVE_ROLES)
    assert [slide["query"]["role"] for slide in slides] == list(TEMPLATE_ROLES)
    assert [slide["query"]["required_source_ordinal"] for slide in slides] == list(
        range(1, 16)
    )
    assert [int(slide["page_id"].rsplit(":", 1)[1]) for slide in slides] == list(
        range(1, 16)
    )
    assert len({slide["page_id"] for slide in slides}) == 15


def test_phase49_binding_profile_contains_only_hash_rendering_selectors() -> None:
    profile = _profile()
    selectors: list[dict[str, object]] = []
    for slide in profile["slides"]:
        for key in ("title_binding", "headline_binding"):
            rule = slide.get(key)
            if isinstance(rule, dict) and rule.get("kind") == "fact":
                selectors.extend(rule["renderings"])
        for rule in slide.get("bindings", {}).values():
            if rule.get("kind") == "fact":
                selectors.extend(rule["renderings"])
        selectors.extend(slide.get("fragment_bindings", []))

    assert selectors
    for selector in selectors:
        assert set(selector) <= {
            "fact_id",
            "rendering_sha256",
            "target_kind",
            "target_id",
        }
        assert isinstance(selector["fact_id"], str) and selector["fact_id"]
        digest = selector["rendering_sha256"]
        assert isinstance(digest, str) and len(digest) == 64
        int(digest, 16)


def test_phase49_slide9_locks_no_autofit_for_compact_kpi_units() -> None:
    slide = next(item for item in _profile()["slides"] if item["ordinal"] == 9)

    assert {
        slot_id
        for slot_id, rule in slide["bindings"].items()
        if rule.get("fit_policy") == "no-autofit"
    } == {
        "shape_265",
        "shape_324",
        "shape_337",
        "shape_339",
        "shape_350",
        "shape_352",
        "shape_363",
        "shape_365",
        "shape_376",
        "shape_389",
    }


def test_phase49_slide8_places_the_total_unit_in_the_caption_not_over_the_art() -> None:
    slide = next(item for item in _profile()["slides"] if item["ordinal"] == 8)

    assert slide["bindings"]["shape_7"] == {
        "kind": "connective",
        "connective_id": "connective-clear",
    }
    assert slide["bindings"]["shape_78"] == {
        "kind": "connective",
        "connective_id": "connective-clear",
    }
    assert slide["bindings"]["shape_65"] == {
        "kind": "fact",
        "renderings": [
            {
                "fact_id": "projects-total",
                "rendering_sha256": "daabd20a5b699aed55f7e3b6fd0dd47f4e8d20073c4b8b18584bcfafbe60ca6e",
            },
        ],
        "separator": "",
    }


def test_phase49_slide9_locks_only_bounded_skill_owned_style_clones() -> None:
    slide = next(item for item in _profile()["slides"] if item["ordinal"] == 9)

    assert [
        (
            item["source_shape_id"],
            item["target_shape_id"],
            item["scope"],
        )
        for item in slide["style_clones"]
    ] == [
        (330, 343, "shape-fill"),
        (339, 352, "text-color"),
        (337, 350, "text-color"),
        (338, 351, "shape-fill"),
    ]
    for item in slide["style_clones"]:
        assert set(item) == {
            "source_shape_id",
            "target_shape_id",
            "scope",
            "source_style_sha256",
            "target_guard_sha256",
        }
        for key in ("source_style_sha256", "target_guard_sha256"):
            digest = item[key]
            assert isinstance(digest, str) and len(digest) == 64
            int(digest, 16)

    serialized = json.dumps(_profile(), ensure_ascii=False).lower()
    for forbidden in ("#008c72", "accent1", "accent2", "<a:", "ooxml"):
        assert forbidden not in serialized
