from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"))

from pptx_studio.brief_binding import BriefBindingError, compile_outline_bindings  # noqa: E402


def _preflight() -> dict[str, object]:
    return {"status": "PASS", "slides": [{"slide_id": "s01", "regions": [
        {"region_id": "r-title", "native_capacity": 8, "shape_slots": [{"semantic_role": "title"}]},
        {"region_id": "r-body", "native_capacity": 24, "shape_slots": [{"semantic_role": "body"}]},
        {"region_id": "r-metric", "native_capacity": 5, "shape_slots": [{"semantic_role": "metric"}]},
    ]}]}


def test_outline_binding_uses_native_capacity_and_semantic_role() -> None:
    result = compile_outline_bindings({"schema_version": "1.0", "slides": [{"slide_id": "s01", "facts": [
        {"value": "年度报告", "semantic_role": "title"},
        {"value": "156", "semantic_role": "metric"},
        {"value": "预算执行总体平稳", "semantic_role": "body"},
    ]}]}, preflight=_preflight())
    assert [item["region_id"] for item in result["bindings"]] == ["r-title", "r-metric", "r-body"]
    assert [item["fact_id"] for item in result["facts"]] == ["s01-f01", "s01-f02", "s01-f03"]


def test_outline_binding_rejects_overflow_without_guessing() -> None:
    with pytest.raises(
        BriefBindingError,
        match=r"OUTLINE_FACT_NO_FITTING_SLOT:slide_id=s01:ordinal=1:requested_chars=[0-9]+:remaining_slots=body:24x1,metric:5x1,title:8x1",
    ):
        compile_outline_bindings({"schema_version": "1.0", "slides": [{"slide_id": "s01", "facts": [
            {"value": "这是一段明确超过所有认证槽位容量且不得截断的客户文字内容", "semantic_role": "body"},
        ]}]}, preflight=_preflight())


def test_outline_binding_never_uses_a_title_or_metric_surface_for_body_copy() -> None:
    preflight = {"status": "PASS", "slides": [{"slide_id": "s01", "regions": [
        {"region_id": "r-title", "native_capacity": 32, "shape_slots": [{"semantic_role": "title"}]},
        {"region_id": "r-metric", "native_capacity": 32, "shape_slots": [{"semantic_role": "metric"}]},
    ]}]}
    with pytest.raises(BriefBindingError, match=r"OUTLINE_FACT_NO_FITTING_SLOT:slide_id=s01:ordinal=1"):
        compile_outline_bindings({"schema_version": "1.0", "slides": [{"slide_id": "s01", "facts": [
            {"value": "这是一条不能冒充标题或指标的经营解释", "semantic_role": "body"},
        ]}]}, preflight=preflight)


def test_outline_binding_reserves_the_largest_slot_for_later_long_copy() -> None:
    preflight = {"status": "PASS", "slides": [{"slide_id": "s01", "regions": [
        {"region_id": "r-short", "native_capacity": 6, "shape_slots": [{"semantic_role": "label"}]},
        {"region_id": "r-long", "native_capacity": 24, "shape_slots": [{"semantic_role": "body"}]},
    ]}]}
    result = compile_outline_bindings({"schema_version": "1.0", "slides": [{"slide_id": "s01", "facts": [
        {"value": "治理基础", "semantic_role": "label"},
        {"value": "预算事前校验与月度偏差复盘闭环", "semantic_role": "body"},
    ]}]}, preflight=preflight)

    # Facts retain client narrative order, while the allocator has prevented
    # the short first label from consuming the only long-capacity surface.
    assert [item["fact_id"] for item in result["facts"]] == ["s01-f01", "s01-f02"]
    assert [item["region_id"] for item in result["bindings"]] == ["r-short", "r-long"]
