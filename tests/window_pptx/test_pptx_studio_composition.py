from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import validate


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.composition import CompositionError, compile_composition, serialize_composition_plan, style_signature  # noqa: E402
from manage_pptx_studio_library import run  # noqa: E402


def _page(letter: str, number: int, category: str, *, style: list[str] | None = None) -> dict[str, object]:
    return {
        "page_id": f"page_{letter * 24}_{number:03d}",
        "deck_id": f"deck_{letter * 24}",
        "package_sha256": letter * 64,
        "slide_number": number,
        "category": category,
        "render": {"image_sha256": chr(ord(letter) + 1) * 64},
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
        {"region_id": "region_c_body", "page_id": process["page_id"], "capacity": {"max_text_chars": 100}},
    ]
    catalog = {"active_categories": ["003-封面模板", "039-结尾模板", "050-架构流程"], "pages": pages, "regions": regions}
    signatures = {str(page["page_id"]): style_signature(page, observations) for page in pages}
    return catalog, observations, signatures


def _request(signatures: dict[str, str], *, strategy: str = "exact_deck") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "strategy": strategy,
        "art_direction": {"anchor_page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001", "allowed_style_signatures": [signatures["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"]]},
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


def _select_other_deck(request: dict[str, object], signatures: dict[str, str]) -> None:
    request["art_direction"].update({  # type: ignore[union-attr]
        "allowed_style_signatures": [
            signatures["page_aaaaaaaaaaaaaaaaaaaaaaaa_001"],
            signatures["page_cccccccccccccccccccccccc_001"],
        ]
    })
    request["slides"][1].update({  # type: ignore[index]
        "role": "process",
        "selected_candidate_id": "page_cccccccccccccccccccccccc_001",
        "candidate_ids": ["page_cccccccccccccccccccccccc_001"],
    })


@pytest.mark.parametrize(
    "mutate,error",
    [
        (lambda request, signatures: request["art_direction"].update({"allowed_style_signatures": ["style_" + "f" * 24]}), "ANCHOR_SIGNATURE_NOT_ALLOWED"),
        (_select_other_deck, "EXACT_DECK_SEQUENCE_INVALID"),
        (lambda request, signatures: request["slides"][0].update({"selected_candidate_id": "missing", "candidate_ids": ["missing"]}), "PAGE_CANDIDATE_UNKNOWN"),
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
