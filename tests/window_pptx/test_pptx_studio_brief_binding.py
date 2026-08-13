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


def test_outline_binding_rejects_sparse_rich_text_only_template() -> None:
    preflight = {"status": "PASS", "slides": [{
        "slide_id": "s01",
        "content_contract": {"title": 1, "label": 12, "metric": 2, "body": 0},
        "governed_content_contract": {"requires_structured_data": False},
        "regions": [
            *[
                {"region_id": f"r-label-{index}", "native_capacity": 12,
                 "shape_slots": [{"semantic_role": "label"}]}
                for index in range(12)
            ],
            {"region_id": "r-title", "native_capacity": 12,
             "shape_slots": [{"semantic_role": "title"}]},
        ],
    }]}
    with pytest.raises(
        BriefBindingError,
        match=r"OUTLINE_STRUCTURAL_COVERAGE_INSUFFICIENT:slide_id=s01:role=label:provided=2:required=8",
    ):
        compile_outline_bindings({"schema_version": "1.0", "slides": [{
            "slide_id": "s01", "facts": [
                {"value": "标题", "semantic_role": "title"},
                {"value": "标签一", "semantic_role": "label"},
                {"value": "标签二", "semantic_role": "label"},
            ],
        }]}, preflight=preflight)


def test_outline_binding_defers_rich_governed_page_to_data_contract() -> None:
    preflight = {"status": "PASS", "slides": [{
        "slide_id": "s01",
        "content_contract": {"title": 1, "label": 12, "metric": 10, "body": 0},
        "governed_content_contract": {"requires_structured_data": True},
        "regions": [
            {"region_id": "r-title", "native_capacity": 12,
             "shape_slots": [{"semantic_role": "title"}]},
        ],
    }]}
    result = compile_outline_bindings({"schema_version": "1.0", "slides": [{
        "slide_id": "s01", "facts": [
            {"value": "收入构成", "semantic_role": "title"},
        ],
    }]}, preflight=preflight)
    assert result["facts"] == [{"fact_id": "s01-f01", "value": "收入构成"}]


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


def test_outline_binding_places_a_long_summary_label_in_body_only_as_last_resort() -> None:
    preflight = {"status": "PASS", "slides": [{"slide_id": "s01", "regions": [
        {"region_id": "r-label", "native_capacity": 6, "shape_slots": [{"semantic_role": "label"}]},
        {"region_id": "r-body", "native_capacity": 36, "shape_slots": [{"semantic_role": "body"}]},
    ]}]}
    result = compile_outline_bindings({"schema_version": "1.0", "slides": [{"slide_id": "s01", "facts": [
        {"value": "总支出92846.30万元，全年预算总体平稳", "semantic_role": "label"},
    ]}]}, preflight=preflight)

    assert result["bindings"][0]["region_id"] == "r-body"


def _fact_store() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "facts": [
            {"id": "report-title", "text": "年度财务运营报告", "status": "active"},
            {"id": "budget-rate", "text": "96.9%", "status": "active"},
        ],
    }


def test_locked_fact_outline_resolves_only_ledger_values() -> None:
    result = compile_outline_bindings({"schema_version": "1.0", "slides": [{"slide_id": "s01", "facts": [
        {"fact_id": "report-title", "semantic_role": "title"},
        {"fact_id": "budget-rate", "semantic_role": "metric"},
    ]}]}, preflight=_preflight(), fact_store=_fact_store())

    assert result["facts"] == [
        {"fact_id": "report-title", "value": "年度财务运营报告"},
        {"fact_id": "budget-rate", "value": "96.9%"},
    ]


@pytest.mark.parametrize(
    "outline,error",
    [
        ({"schema_version": "1.0", "slides": [{"slide_id": "s01", "facts": [{"value": "自行新增", "semantic_role": "title"}]}]}, "LOCKED_FACT_REFERENCE_REQUIRED"),
        ({"schema_version": "1.0", "slides": [{"slide_id": "s01", "facts": [{"fact_id": "unknown", "semantic_role": "title"}]}]}, "LOCKED_FACT_UNKNOWN"),
    ],
)
def test_locked_fact_outline_rejects_free_or_unknown_values(outline: dict[str, object], error: str) -> None:
    with pytest.raises(BriefBindingError, match=error):
        compile_outline_bindings(outline, preflight=_preflight(), fact_store=_fact_store())


def test_locked_fact_outline_enforces_client_approved_slide_beat() -> None:
    fact_store = _fact_store()
    fact_store["facts"][0]["recommended_beat"] = "s02"  # type: ignore[index]
    outline = {"schema_version": "1.0", "slides": [{"slide_id": "s01", "facts": [
        {"fact_id": "report-title", "semantic_role": "title"},
    ]}]}

    with pytest.raises(BriefBindingError, match="LOCKED_FACT_BEAT_MISMATCH"):
        compile_outline_bindings(outline, preflight=_preflight(), fact_store=fact_store)
