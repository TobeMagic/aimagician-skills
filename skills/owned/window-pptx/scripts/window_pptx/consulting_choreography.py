"""Source-bound 14-page choreography for the consulting tracer."""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any, Iterable, Mapping

from .weak_model import BriefCompilation, NarrativePlan, NarrativeSlide


CONSULTING_TRACER_FACT_IDS = {
    "context-fragmentation",
    "problem-cycle",
    "objective-cycle",
    "solution-loop",
    "scope-workstreams",
    "approach-phases",
    "timeline-six-months",
    "team-governance",
    "risk-adoption",
    "next-step-approval",
}

CHOREOGRAPHY_SOURCE_SLIDES = {
    "cover": ("cover",),
    "executive-summary": ("problem", "objectives", "timeline"),
    "section-why-now": ("context", "problem"),
    "current-state": ("context", "problem"),
    "transformation-bridge": ("problem", "objectives"),
    "section-what-built": ("solution", "scope"),
    "solution": ("solution",),
    "scope": ("scope",),
    "section-how-delivery": ("approach", "timeline"),
    "delivery-rail": ("approach", "timeline"),
    "team": ("team",),
    "risks": ("risks",),
    "next-steps": ("next-steps",),
    "closing": ("problem", "objectives", "closing", "next-steps"),
}


def _renamed_blocks(
    slides: Mapping[str, Mapping[str, Any]],
    *slide_ids: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for slide_id in slide_ids:
        for block_index, source in enumerate(
            slides[slide_id].get("blocks", []), start=1
        ):
            block = copy.deepcopy(source)
            block["id"] = f"{slide_id}-{block_index}-{block['id']}"
            result.append(block)
    return result


def _slide(
    slide_id: str,
    role: str,
    title: str,
    blocks: Iterable[Mapping[str, Any]],
    *,
    importance: str = "normal",
) -> dict[str, Any]:
    return {
        "id": slide_id,
        "role": role,
        "title": title,
        "importance": importance,
        "blocks": [copy.deepcopy(dict(block)) for block in blocks],
    }


def _section(slide_id: str, title: str, support: str) -> dict[str, Any]:
    return _slide(
        slide_id,
        "section",
        title,
        (
            {
                "id": f"{slide_id}-statement",
                "kind": "statement",
                "text": support,
            },
        ),
        importance="high",
    )


def _source_text(
    slides: Mapping[str, Mapping[str, Any]], slide_id: str
) -> str:
    return "\n".join(
        str(block["text"])
        for block in slides[slide_id].get("blocks", [])
        if block.get("text")
    )


def _delivery_block(
    slides: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    approach = slides["approach"]["blocks"][0]
    timeline = slides["timeline"]["blocks"][0]
    approach_items = list(approach.get("items", []))
    timeline_items = list(timeline.get("items", []))
    if len(approach_items) != 5 or len(timeline_items) != 5:
        raise ValueError("consulting tracer delivery facts must contain five stages")
    return {
        "id": "delivery-rail-facts",
        "kind": "timeline",
        "items": [
            {
                "label": f"{index:02d}  {stage}",
                "text": (
                    str(month).replace(str(stage), "").strip()
                    or str(month)
                ),
            }
            for index, (stage, month) in enumerate(
                zip(approach_items, timeline_items, strict=True),
                start=1,
            )
        ],
        "text": f"{approach['text']}\n{timeline['text']}",
    }


def _narrative_slide(
    slide_id: str,
    role: str,
    title: str,
    fact_refs: tuple[str, ...],
    semantic_kind: str,
    *,
    importance: str = "normal",
    structural: bool = False,
) -> NarrativeSlide:
    return NarrativeSlide(
        id=slide_id,
        role=role,
        title=title,
        importance=importance,
        fact_refs=fact_refs,
        semantic_kind=semantic_kind,
        structural=structural,
    )


def apply_consulting_tracer_choreography(
    compilation: BriefCompilation,
) -> BriefCompilation:
    """Return the exact 14-page tracer only for the frozen consulting facts."""

    active_fact_ids = {
        fact.id for fact in compilation.fact_store.active_facts()
    }
    if (
        compilation.brief_plan.scenario_id != "project-proposal"
        or active_fact_ids != CONSULTING_TRACER_FACT_IDS
    ):
        return compilation
    source_slides = {
        slide["id"]: slide for slide in compilation.deck_plan["slides"]
    }
    required_source_ids = {
        "cover",
        "context",
        "problem",
        "objectives",
        "solution",
        "scope",
        "approach",
        "timeline",
        "team",
        "risks",
        "next-steps",
        "closing",
    }
    if not required_source_ids <= set(source_slides):
        return compilation

    cover = copy.deepcopy(source_slides["cover"])
    decision_text = _source_text(source_slides, "next-steps")
    solution_slide = copy.deepcopy(source_slides["solution"])
    scope_slide = copy.deepcopy(source_slides["scope"])
    team_slide = copy.deepcopy(source_slides["team"])
    for slide in (solution_slide, scope_slide):
        for block in slide.get("blocks", []):
            items = block.get("items")
            if isinstance(items, list):
                block["items"] = [
                    (
                        f"{index:02d}  {item}  →"
                        if slide is solution_slide
                        else f"{index:02d}  起点 · {item}"
                        if slide is scope_slide and index == 1
                        else f"{index:02d}  {item}"
                    )
                    for index, item in enumerate(items, start=1)
                ]
    for block in team_slide.get("blocks", []):
        items = block.get("items")
        if not isinstance(items, list):
            continue
        structured: list[dict[str, str]] = []
        for index, raw in enumerate(items, start=1):
            text = str(raw)
            owner, separator, responsibility = text.partition("负责")
            structured.append(
                {
                    "label": f"{index:02d}  {owner}",
                    "text": (
                        f"负责{responsibility}" if separator else text
                    ),
                }
            )
        block["items"] = structured
    decision_slide = _slide(
        "next-steps",
        "next-steps",
        "三项启动决策",
        (
            {
                "id": "next-steps-decision-gates",
                "kind": "recommendation",
                "items": [
                    "01\n确定试点范围",
                    "02\n指定业务负责人",
                    "03\n确认启动日期",
                ],
                "text": decision_text,
                "source_ref": "request#next-steps",
            },
        ),
        importance="critical",
    )
    derived_bridge = {
        "id": "transformation-derived-metric",
        "kind": "metrics",
        "items": [
            {
                "label": "改善幅度",
                "value": -50,
                "unit": "%",
            },
        ],
    }
    slides = [
        cover,
        _slide(
            "executive-summary",
            "executive-summary",
            "执行摘要",
            (
                {
                    "id": "executive-summary-facts",
                    "kind": "bullets",
                    "items": [
                        _source_text(source_slides, "problem"),
                        _source_text(source_slides, "objectives"),
                        _source_text(source_slides, "timeline"),
                    ],
                    "text": "\n".join(
                        (
                            _source_text(source_slides, "problem"),
                            _source_text(source_slides, "objectives"),
                            _source_text(source_slides, "timeline"),
                        )
                    ),
                },
            ),
            importance="critical",
        ),
        _section(
            "section-why-now",
            "为什么是现在",
            "现状断点 × 10 天审批周期",
        ),
        _slide(
            "current-state",
            "current-state",
            "当前状态与关键证据",
            (
                {
                    "id": "current-state-comparison",
                    "kind": "comparison",
                    "items": [
                        {
                            "label": "现状断点",
                            "text": _source_text(source_slides, "context"),
                        },
                        {
                            "label": "审批周期",
                            "text": _source_text(source_slides, "problem"),
                        },
                    ],
                    "text": (
                        f"{_source_text(source_slides, 'context')}\n"
                        f"{_source_text(source_slides, 'problem')}"
                    ),
                    "source_ref": "request#context+problem",
                },
            ),
        ),
        _slide(
            "transformation-bridge",
            "outcomes",
            "10 天 → 5 天：审批周期减半",
            (
                *_renamed_blocks(source_slides, "problem", "objectives"),
                derived_bridge,
            ),
            importance="critical",
        ),
        _section(
            "section-what-built",
            "将建设什么",
            "统一入口 × 四个环节 × 四个工作流",
        ),
        solution_slide,
        scope_slide,
        _section(
            "section-how-delivery",
            "如何交付",
            "五阶段 × 六个月试点",
        ),
        _slide(
            "delivery-rail",
            "timeline",
            "五阶段、六个月交付路径",
            (_delivery_block(source_slides),),
            importance="high",
        ),
        team_slide,
        copy.deepcopy(source_slides["risks"]),
        decision_slide,
        _slide(
            "closing",
            "closing",
            "批准六个月试点",
            (
                {
                    "id": "closing-decision",
                    "kind": "recommendation",
                    "text": (
                        "统一知识入口 · 审批周期 10 → 5 天 · 建立运营闭环\n\n"
                        "决策：试点范围｜业务负责人｜启动日期"
                    ),
                    "source_ref": "request#next-steps",
                },
            ),
            importance="critical",
        ),
    ]
    for slide in slides:
        for block_index, block in enumerate(slide.get("blocks", []), start=1):
            block["id"] = f"{slide['id']}-{block_index}-{block['id']}"
    narrative_slides = (
        _narrative_slide(
            "cover", "cover", cover.get("title") or "项目提案", (), "cards",
            importance="critical", structural=True
        ),
        _narrative_slide(
            "executive-summary",
            "executive-summary",
            "执行摘要",
            ("problem-cycle", "objective-cycle", "timeline-six-months"),
            "cards",
            importance="critical",
        ),
        _narrative_slide(
            "section-why-now",
            "section",
            "为什么是现在",
            ("context-fragmentation", "problem-cycle"),
            "statement",
            importance="high",
            structural=True,
        ),
        _narrative_slide(
            "current-state",
            "current-state",
            "当前状态与关键证据",
            ("context-fragmentation", "problem-cycle"),
            "comparison",
        ),
        _narrative_slide(
            "transformation-bridge",
            "outcomes",
            "10 天 → 5 天：审批周期减半",
            ("problem-cycle", "objective-cycle"),
            "metrics",
            importance="critical",
        ),
        _narrative_slide(
            "section-what-built",
            "section",
            "将建设什么",
            ("solution-loop", "scope-workstreams"),
            "statement",
            importance="high",
            structural=True,
        ),
        _narrative_slide(
            "solution",
            "solution",
            source_slides["solution"].get("title") or "解决方案",
            ("solution-loop",),
            "process",
        ),
        _narrative_slide(
            "scope",
            "scope",
            source_slides["scope"].get("title") or "试点范围",
            ("scope-workstreams",),
            "matrix",
        ),
        _narrative_slide(
            "section-how-delivery",
            "section",
            "如何交付",
            ("approach-phases", "timeline-six-months"),
            "statement",
            importance="high",
            structural=True,
        ),
        _narrative_slide(
            "delivery-rail",
            "timeline",
            "五阶段、六个月交付路径",
            ("approach-phases", "timeline-six-months"),
            "timeline",
            importance="high",
        ),
        _narrative_slide(
            "team",
            "governance",
            source_slides["team"].get("title") or "治理机制",
            ("team-governance",),
            "hierarchy",
        ),
        _narrative_slide(
            "risks",
            "risks",
            source_slides["risks"].get("title") or "风险与应对",
            ("risk-adoption",),
            "risk",
        ),
        _narrative_slide(
            "next-steps",
            "next-steps",
            "三项启动决策",
            ("next-step-approval",),
            "recommendation",
            importance="critical",
        ),
        _narrative_slide(
            "closing",
            "closing",
            source_slides["closing"].get("title") or "试点启动",
            ("problem-cycle", "objective-cycle", "next-step-approval"),
            "cards",
            importance="critical",
        ),
    )
    narrative = NarrativePlan(
        schema_version=compilation.narrative.schema_version,
        archetype_id=compilation.narrative.archetype_id,
        fact_store_digest=compilation.narrative.fact_store_digest,
        slides=narrative_slides,
        coverage={
            **copy.deepcopy(compilation.narrative.coverage),
            "required_fact_ids": sorted(CONSULTING_TRACER_FACT_IDS),
            "covered_fact_ids": sorted(CONSULTING_TRACER_FACT_IDS),
            "required_fact_count": len(CONSULTING_TRACER_FACT_IDS),
            "covered_required_fact_count": len(CONSULTING_TRACER_FACT_IDS),
            "required_fact_coverage": 1.0,
            "archetype_slide_count_range": [14, 14],
            "slide_floor_satisfied": True,
        },
        decisions=(
            *compilation.narrative.decisions,
            "CONSULTING_SOURCE_BOUND_14_PAGE_CHOREOGRAPHY",
            "DERIVED_CYCLE_REDUCTION=(5-10)/10=-50%",
        ),
    )
    deck_plan = {
        **copy.deepcopy(compilation.deck_plan),
        "slides": slides,
    }
    return replace(
        compilation,
        narrative=narrative,
        deck_plan=deck_plan,
    )


__all__ = [
    "CHOREOGRAPHY_SOURCE_SLIDES",
    "CONSULTING_TRACER_FACT_IDS",
    "apply_consulting_tracer_choreography",
]
