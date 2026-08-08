"""Constrained ordinary-model planning for the fifteen-scenario v6 suite."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from .registry import resolve_archetype
from .weak_model import (
    WeakModelValidationError,
    normalize_brief_plan,
    validate_brief_plan,
    validate_fact_store,
)


SEMANTIC_HINTS = (
    "metrics",
    "comparison",
    "sequence",
    "timeline",
    "process",
    "roadmap",
    "quadrant",
    "funnel",
    "trend",
    "composition",
    "matrix",
    "risk",
    "recommendation",
    "table",
    "statement",
)

SCENARIO_ARCHETYPE = {
    "annual-work-report": "annual-review",
    "campus-competition-defense": "project-proposal",
    "academic-thesis-defense": "research-report",
    "business-operations-review": "operations-review",
    "project-proposal": "project-proposal",
    "product-launch": "product-launch",
    "market-analysis": "market-analysis",
    "sales-proposal": "sales-proposal",
    "investor-pitch": "investor-pitch",
    "strategy-planning": "strategic-plan",
    "data-analysis-report": "data-analysis",
    "training-course": "training",
    "brand-company-introduction": "brand-introduction",
    "project-kickoff": "project-kickoff",
    "ecommerce-marketing-plan": "ecommerce-marketing",
}


@dataclass(frozen=True)
class OrdinaryPlanEvaluation:
    status: str
    normalized: dict[str, Any] | None
    fact_coverage: float
    group_count: int
    error: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "fact_coverage": self.fact_coverage,
            "group_count": self.group_count,
            "error": self.error,
        }


def build_ordinary_plan_prompt(pack: Mapping[str, Any]) -> str:
    """Build a closed-world prompt that exposes no geometry or style authority."""

    source_scenario = str(pack["scenario_id"])
    scenario = SCENARIO_ARCHETYPE[source_scenario]
    archetype = resolve_archetype(scenario)
    facts = pack["fact_store"]["facts"]
    fact_lines = [
        {
            "id": item["id"],
                "claim_key": item.get("claim_key", item["kind"]),
                "value": item.get("value", item["text"]),
            "unit": item.get("unit", ""),
            "time_scope": item.get("time_scope", ""),
        }
        for item in facts
    ]
    contract = {
        "schema_version": "1.0",
        "scenario_id": scenario,
        "groups": [
            {
                "id": "lowercase-hyphenated-id",
                "fact_refs": ["one-or-more-fact-ids"],
                "beat_hint": f"one of {list(archetype.sections)}",
                "semantic_hint": f"one of {list(SEMANTIC_HINTS)}",
                "importance": "low|normal|high|critical",
            }
        ],
        "preferences": {
            "tone": "professional",
            "density": "balanced",
            "audience_mode": "executive",
            "motion": "off",
        },
    }
    return (
        "你只负责把事实分组并排序，不负责写文案或设计页面。"
        "返回一个 JSON 对象，禁止 Markdown、解释、坐标、字体、颜色、模板 ID、"
        "HTML、代码或新事实。每个 fact id 必须且只能出现一次；组数 4–8。"
        f"\n语料场景：{source_scenario}\n注册场景：{scenario}"
        f"\n允许 beat_hint：{json.dumps(list(archetype.sections), ensure_ascii=False)}"
        f"\n允许 semantic_hint：{json.dumps(list(SEMANTIC_HINTS), ensure_ascii=False)}"
        f"\n事实：{json.dumps(fact_lines, ensure_ascii=False, separators=(',', ':'))}"
        f"\n严格结构示例：{json.dumps(contract, ensure_ascii=False, separators=(',', ':'))}"
    )


def evaluate_ordinary_plan(
    pack: Mapping[str, Any],
    response: str | Mapping[str, Any] | None,
) -> OrdinaryPlanEvaluation:
    """Validate syntax, closed-world fact coverage, and registered decisions."""

    facts = validate_fact_store(pack["fact_store"])
    expected = {item.id for item in facts.active_facts()}
    if response is None:
        return OrdinaryPlanEvaluation("UNAVAILABLE", None, 0.0, 0, "NO_RESPONSE")
    try:
        normalized, _trace = normalize_brief_plan(response)
        validated = validate_brief_plan(normalized, facts)
        observed = {
            fact_id for group in validated.groups for fact_id in group.fact_refs
        }
        coverage = len(observed & expected) / len(expected) if expected else 1.0
        if observed != expected:
            missing = sorted(expected - observed)
            extra = sorted(observed - expected)
            return OrdinaryPlanEvaluation(
                "FAIL",
                normalized,
                coverage,
                len(validated.groups),
                f"FACT_COVERAGE_MISMATCH missing={missing} extra={extra}",
            )
        if not 4 <= len(validated.groups) <= 8:
            return OrdinaryPlanEvaluation(
                "FAIL",
                normalized,
                coverage,
                len(validated.groups),
                "GROUP_COUNT_OUT_OF_RANGE",
            )
        return OrdinaryPlanEvaluation(
            "PASS", normalized, coverage, len(validated.groups), None
        )
    except (WeakModelValidationError, KeyError, TypeError, ValueError) as exc:
        return OrdinaryPlanEvaluation("FAIL", None, 0.0, 0, str(exc))


__all__ = [
    "OrdinaryPlanEvaluation",
    "build_ordinary_plan_prompt",
    "evaluate_ordinary_plan",
    "SCENARIO_ARCHETYPE",
]
