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
    with pytest.raises(BriefBindingError, match="OUTLINE_FACT_NO_FITTING_SLOT"):
        compile_outline_bindings({"schema_version": "1.0", "slides": [{"slide_id": "s01", "facts": [
            {"value": "这是一段明确超过所有认证槽位容量且不得截断的客户文字内容", "semantic_role": "body"},
        ]}]}, preflight=_preflight())
