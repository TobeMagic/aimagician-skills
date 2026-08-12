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
