from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import validate


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.adaptation import AdaptationError, compile_adaptation  # noqa: E402
from pptx_studio.composition import compile_composition, style_signature  # noqa: E402
from manage_pptx_studio_library import run  # noqa: E402


def _inputs() -> tuple[dict[str, object], dict[str, object]]:
    page = {"page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001", "deck_id": "deck_aaaaaaaaaaaaaaaaaaaaaaaa", "package_sha256": "a" * 64, "slide_number": 1, "category": "003-封面模板", "render": {"image_sha256": "b" * 64}, "component_eligible": True, "shapes": [{"shape_id": "2", "kind": "text", "max_chars": 30}, {"shape_id": "3", "kind": "image", "max_chars": 0}]}
    catalog = {"active_categories": ["003-封面模板"], "pages": [page], "regions": [{"region_id": "region_a_title", "page_id": page["page_id"], "capacity": {"max_text_chars": 30}}, {"region_id": "region_a_subtitle", "page_id": page["page_id"], "capacity": {"max_text_chars": 30}}]}
    observations = {page["page_id"]: {"page_id": page["page_id"], "image_sha256": "b" * 64, "observation": {"suggested_roles": ["cover"], "semantic_tags": ["annual-report"], "visual_style": ["editorial"], "uncertainty": "none"}}}
    signature = style_signature(page, observations)
    plan = compile_composition(catalog, observations=observations, request={"schema_version": "1.0", "strategy": "page_assembly", "art_direction": {"anchor_page_id": page["page_id"], "allowed_style_signatures": [signature], "suitability": "general"}, "slides": [{"slide_id": "s01", "role": "cover", "candidate_ids": [page["page_id"]], "selected_candidate_id": page["page_id"], "minimum_capacity": 20}]})
    return catalog, plan


def _request() -> dict[str, object]:
    return {"schema_version": "1.0", "facts": [{"fact_id": "fact_title", "value": "2025 年度工作汇报"}], "assets": [{"asset_id": "asset_cover", "sha256": "c" * 64}], "bindings": [{"slide_id": "s01", "operation": "replace_text", "region_id": "region_a_title", "shape_id": None, "fact_id": "fact_title", "asset_id": None}, {"slide_id": "s01", "operation": "replace_asset", "region_id": None, "shape_id": "3", "fact_id": None, "asset_id": "asset_cover"}], "structured_data": []}


def _preflight(capacity: int = 30) -> dict[str, object]:
    return {"status": "PASS", "slides": [{"slide_id": "s01", "regions": [
        {"region_id": "region_a_title", "native_capacity": capacity},
        {"region_id": "region_a_subtitle", "native_capacity": capacity},
    ]}]}


def test_adaptation_contains_only_bound_references() -> None:
    catalog, plan = _inputs()
    request = _request()
    result = compile_adaptation(plan, catalog=catalog, request=request)
    assert result["status"] == "PASS"
    assert "2025 年度工作汇报" not in json.dumps(result, ensure_ascii=False)
    assert result["operations"][0]["fact_id"] == "fact_title"
    request_schema = json.loads((REPO_ROOT / "skills" / "owned" / "pptx-studio" / "schemas" / "pptx-studio-adaptation-request.v1.schema.json").read_text(encoding="utf-8"))
    validate(request, request_schema)
    schema = json.loads((REPO_ROOT / "skills" / "owned" / "pptx-studio" / "schemas" / "pptx-studio-adaptation-plan.v1.schema.json").read_text(encoding="utf-8"))
    validate(result, schema)


def test_adaptation_rejects_source_drift() -> None:
    catalog, plan = _inputs()
    catalog["pages"][0]["package_sha256"] = "d" * 64  # type: ignore[index]
    with pytest.raises(AdaptationError, match="SOURCE_DRIFT"):
        compile_adaptation(plan, catalog=catalog, request=_request())


def test_cli_adaptation_uses_only_catalog_and_plan_json(tmp_path: Path) -> None:
    catalog, plan = _inputs()
    paths = {name: tmp_path / f"{name}.json" for name in ("manifest", "catalog", "plan", "request", "preflight", "output")}
    paths["manifest"].write_text(json.dumps({"status": "APPLIED"}), encoding="utf-8")
    paths["catalog"].write_text(json.dumps(catalog), encoding="utf-8")
    paths["plan"].write_text(json.dumps(plan), encoding="utf-8")
    paths["request"].write_text(json.dumps(_request()), encoding="utf-8")
    paths["preflight"].write_text(json.dumps(_preflight()), encoding="utf-8")
    result = run(["adapt", "--source-root", str(tmp_path), "--archive-root", str(tmp_path), "--manifest", str(paths["manifest"]), "--catalog", str(paths["catalog"]), "--composition-plan", str(paths["plan"]), "--preflight-output", str(paths["preflight"]), "--adaptation-input", str(paths["request"]), "--adaptation-output", str(paths["output"])])
    assert result["status"] == "PASS"
    assert len(json.loads(paths["output"].read_text(encoding="utf-8"))["operations"]) == 2


@pytest.mark.parametrize(
    "mutate,error",
    [
        (lambda request: request["bindings"][0].update({"text": "freeform"}), "BINDING_SCHEMA_INVALID"),
        (lambda request: request["bindings"][0].update({"fact_id": "missing"}), "TEXT_BINDING_INVALID"),
        (lambda request: request["facts"][0].update({"value": "x" * 31}), "TEXT_CAPACITY_EXCEEDED"),
        (lambda request: request["bindings"].append(dict(request["bindings"][0])), "BINDING_TARGET_DUPLICATE"),
    ],
)
def test_adaptation_fails_closed(mutate, error: str) -> None:  # type: ignore[no-untyped-def]
    catalog, plan = _inputs()
    request = _request()
    mutate(request)
    with pytest.raises(AdaptationError, match=error):
        compile_adaptation(plan, catalog=catalog, request=request)


def test_adaptation_uses_physical_preflight_capacity_over_catalog_hint() -> None:
    catalog, plan = _inputs()
    catalog["regions"][0]["capacity"]["max_text_chars"] = 4  # type: ignore[index]

    result = compile_adaptation(plan, catalog=catalog, request=_request(), preflight=_preflight(30))

    assert result["operations"][0]["capacity"] == 30
