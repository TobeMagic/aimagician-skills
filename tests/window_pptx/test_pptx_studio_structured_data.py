from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.structured_data import (  # noqa: E402
    StructuredDataError,
    contract_for_source,
    expand_contract_values,
    expand_contract_text_values,
)


def _contract():
    contract = contract_for_source(
        "59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839",
        5,
    )
    assert contract is not None
    return contract


def test_revenue_contract_publishes_only_customer_schema_and_expands_privately() -> None:
    contract = _contract()
    assert contract.public_dict() == {
        "contract_id": "hospital-finance-revenue-composition-v1",
        "fields": [
            {"name": "series_label", "kind": "text", "count": 1, "max_chars": [8]},
            {"name": "categories", "kind": "text", "count": 5, "max_chars": [5, 6, 5, 5, 5]},
            {"name": "ratios", "kind": "percentage", "count": 5, "max_chars": [5, 5, 4, 4, 4]},
            {"name": "amounts", "kind": "number", "count": 5, "max_chars": [10, 8, 10, 10, 8]},
        ],
    }
    values = {
        "series_label": "收入占比",
        "categories": ["医疗收入", "政府债收入", "财政收入", "其他收入", "科教收入"],
        "ratios": ["57.5%", "27.1%", "4.9%", "1.4%", "0.1%"],
        "amounts": ["63,621", "30,000", "5,450", "1,533", "109.74"],
    }
    expanded = expand_contract_values(contract, values)
    assert len(expanded) == 11
    assert set(expanded.values()) == {"收入占比", "医疗收入", "政府债收入", "财政收入", "其他收入", "科教收入", "57.5%", "27.1%", "4.9%", "1.4%", "0.1%"}
    visible = expand_contract_text_values(contract, values)
    assert len(visible) == 15
    assert visible["shape_43"] == "医疗收入"
    assert visible["shape_45"] == "63,621"


@pytest.mark.parametrize(
    ("slide_number", "contract_id", "expected_governed_count", "expected_visible_count", "values"),
    [
        (
            6,
            "hospital-finance-medical-revenue-trend-v1",
            27,
            9,
            {
                "trend_series_label": "医疗收入",
                "trend_periods": ["预算", "本年", "上年"],
                "trend_amounts": ["46,000", "45,063", "41,600"],
                "prior_share_series_label": "收入占比",
                "prior_share_categories": ["检查检验", "药品", "卫材", "医疗服务"],
                "prior_share_ratios": ["30.1%", "24.3%", "5.8%", "39.8%"],
                "current_share_series_label": "收入占比",
                "current_share_categories": ["检查检验", "药品", "卫材", "医疗服务"],
                "current_share_ratios": ["28.1%", "26.8%", "5.4%", "39.7%"],
                "comparison_labels": ["前年收入占比", "去年收入占比"],
                "headline_amounts": ["46,000", "41,600", "45,063"],
                "headline_metric_labels": ["完成年初预算", "同比增长"],
                "headline_metrics": ["98.3%", "11.9%"],
            },
        ),
        (
            7,
            "hospital-finance-expenditure-table-v1",
            27,
            10,
            {
                "table_business_header": "业务支出",
                "table_time_header": "时间",
                "table_change_header": "增减",
                "current_year_label": "2025年",
                "previous_year_label": "去年",
                "delta_amount_label": "增减额",
                "delta_rate_label": "增减率",
                "current_values": ["24,267.26", "5,174.52", "19,969.60", "3,173.94", "1,657.09"],
                "previous_values": ["22,026.94", "6,862.09", "18,058.74", "2,497.98", "1,562.99"],
                "delta_values": ["2,240.33", "-1,687.57", "1,910.86", "675.96", "94.10"],
                "delta_rates": ["9.3%", "-19.0%", "9.5%", "15.0%", "6.0%"],
                "summary_labels": ["业务支出", "财政基本支出"],
                "summary_amounts": ["52,242.43", "49,991.23", "2,251.20"],
                "expense_labels": ["工资薪酬", "资产购置", "药品材料", "运行费用", "个人补助"],
            },
        ),
    ],
)
def test_reference_governed_contracts_are_complete_and_do_not_expose_targets(
    slide_number: int,
    contract_id: str,
    expected_governed_count: int,
    expected_visible_count: int,
    values: dict[str, object],
) -> None:
    contract = contract_for_source(
        "59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839",
        slide_number,
    )
    assert contract is not None
    assert contract.public_dict()["contract_id"] == contract_id
    serialized = str(contract.public_dict())
    assert "peer_" not in serialized
    assert "shape_" not in serialized
    assert "table_cell_" not in serialized
    assert len(expand_contract_values(contract, values)) == expected_governed_count
    assert len(expand_contract_text_values(contract, values)) == expected_visible_count


def test_reference_data_contracts_preserve_chart_and_table_semantic_order() -> None:
    trend = contract_for_source(
        "59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839", 6,
    )
    assert trend is not None
    trend_values = {
        "trend_series_label": "SERIES",
        "trend_periods": ["P1", "P2", "P3"],
        "trend_amounts": ["101", "202", "303"],
        "prior_share_series_label": "PRIOR",
        "prior_share_categories": ["P-A", "P-B", "P-C", "P-D"],
        "prior_share_ratios": ["1%", "2%", "3%", "4%"],
        "current_share_series_label": "CURRENT",
        "current_share_categories": ["C-A", "C-B", "C-C", "C-D"],
        "current_share_ratios": ["5%", "6%", "7%", "8%"],
        "comparison_labels": ["LEFT", "RIGHT"],
        "headline_amounts": ["401", "402", "403"],
        "headline_metric_labels": ["RATE", "YOY"],
        "headline_metrics": ["9%", "10%"],
    }
    trend_expanded = expand_contract_values(trend, trend_values)
    assert trend_expanded["peer_76e448f4f21f6c3ac7ed6468"] == "SERIES"
    assert trend_expanded["peer_a277fe88de4355a941e5a019"] == "P1"
    assert trend_expanded["peer_e16ee229e78521a459b0204e"] == "PRIOR"
    assert trend_expanded["peer_65a5336f48dc84182cfc731f"] == "P-A"
    assert trend_expanded["peer_eed7194fc9c5a929ad5d56a7"] == "CURRENT"
    assert trend_expanded["peer_b11ced8b3ac599a47cf6ba0d"] == "C-A"

    table = contract_for_source(
        "59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839", 7,
    )
    assert table is not None
    table_values = {
        "table_business_header": "业务支出", "table_time_header": "时间", "table_change_header": "增减",
        "current_year_label": "2025", "previous_year_label": "2024", "delta_amount_label": "差额", "delta_rate_label": "比率",
        "current_values": ["C1", "C2", "C3", "C4", "C5"],
        "previous_values": ["P1", "P2", "P3", "P4", "P5"],
        "delta_values": ["D1", "D2", "D3", "D4", "D5"],
        "delta_rates": ["R1", "R2", "R3", "R4", "R5"],
        "summary_labels": ["总支出", "财政基本"], "summary_amounts": ["S1", "S2", "S3"],
        "expense_labels": ["项目1", "项目2", "项目3", "项目4", "项目5"],
    }
    table_expanded = expand_contract_values(table, table_values)
    # The physical table is row-major; every semantic field must remain
    # column-major across all five rows rather than following raw XML order.
    assert table_expanded["table_cell_32430ca774fb0d9b2aa158fb"] == "C1"
    assert table_expanded["table_cell_63c9e1fa3e7512f3f0608018"] == "C2"
    assert table_expanded["table_cell_9beffd1036f8f272192aaecb"] == "P1"
    assert table_expanded["table_cell_c1b29a30a6dbf4a1d389b236"] == "P2"
    assert table_expanded["table_cell_41d3df671f23b38d6ec6293a"] == "D1"
    assert table_expanded["table_cell_b8fa8dcc9328eb358d51693c"] == "D2"
    assert table_expanded["table_cell_b1eb7848d629c452e33a90a5"] == "R1"
    assert table_expanded["table_cell_9552567c84b7b3bdd4c97040"] == "R2"


@pytest.mark.parametrize(
    "values,error",
    [
        ({"series_label": "收入", "categories": ["A"] * 5}, "STRUCTURED_DATA_FIELDS_INVALID"),
        ({"series_label": "收入", "categories": ["A"] * 4, "ratios": ["1%"] * 5, "amounts": ["1"] * 5}, "STRUCTURED_DATA_CARDINALITY_INVALID:categories"),
        ({"series_label": "收入", "categories": ["A"] * 5, "ratios": ["1%"] * 4 + [""], "amounts": ["1"] * 5}, "STRUCTURED_DATA_VALUE_INVALID:ratios"),
        ({"series_label": "收入", "categories": ["A"] * 5, "ratios": ["1%"] * 5, "amounts": ["123456789"] * 5}, "STRUCTURED_DATA_VALUE_CAPACITY_EXCEEDED:amounts"),
    ],
)
def test_revenue_contract_fails_closed_on_incomplete_dataset(values, error) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(StructuredDataError, match=error):
        expand_contract_values(_contract(), values)
