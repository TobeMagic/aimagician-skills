"""Deterministic anti-slop and art-direction drift checks."""

from __future__ import annotations

import re
from typing import Any

from .directions import load_art_directions
from .quality_v2 import QualityFindingV2


def _governed_family(selector: str) -> str:
    return {
        "line-chart": "data-chart",
        "area-chart": "data-chart",
        "bar-chart": "data-chart",
        "composition-chart": "data-chart",
        "stacked-bar": "data-chart",
        "distribution-chart": "data-chart",
        "dot-plot": "data-chart",
        "scatter-plot": "data-chart",
        "bubble-chart": "data-chart",
        "before-after": "comparison",
        "recommendation": "risk-recommendation",
        "modular-grid": "cards",
    }.get(selector, selector)


def inspect_design_quality(generation: Any) -> tuple[QualityFindingV2, ...]:
    findings: list[QualityFindingV2] = []
    slides = generation.compiled_deck.get("slides", [])
    content_slides = [
        slide for slide in slides if slide.get("role") not in {"cover", "closing", "cta"}
    ]
    families = [_governed_family(str(slide.get("page_family", ""))) for slide in content_slides]
    for slide in content_slides:
        for block in slide.get("blocks", []):
            if (
                block.get("kind") in {"metrics", "trend", "comparison", "composition"}
                and re.search(r"\d", str(block.get("text") or ""))
                and not block.get("items")
            ):
                findings.append(
                    QualityFindingV2(
                        "compile",
                        "UNSTRUCTURED_METRIC_PRESENTATION",
                        "important",
                        str(slide.get("id") or "") or None,
                        str(block.get("id") or "") or None,
                        (
                            "numeric evidence is editable text but lacks a trusted "
                            "value/unit structure for governed KPI or chart treatment"
                        ),
                        repairable=True,
                        source_stage="design-quality",
                    )
                )
    if len(families) >= 3 and families.count("cards") / len(families) >= 0.6:
        findings.append(
            QualityFindingV2(
                "compile",
                "CARD_MONOCULTURE",
                "important",
                None,
                None,
                "cards occupy at least 60 percent of content pages",
                metric=round(families.count("cards") / len(families), 3),
                threshold=0.6,
                repairable=True,
                source_stage="design-quality",
            )
        )
    direction = generation.direction
    if direction is not None:
        profile = load_art_directions()[direction.selected_profile_id]
        preferred = set(profile.preferred_families)
        matched = sum(family in preferred for family in families)
        if families and matched == 0:
            findings.append(
                QualityFindingV2(
                    "compile",
                    "DIRECTION_PROFILE_DRIFT",
                    "warning",
                    None,
                    direction.selected_profile_id,
                    "no content page uses a preferred family from the selected direction",
                    metric=0,
                    threshold=1,
                    repairable=True,
                    source_stage="design-quality",
                )
            )
        scenario = generation.compilation.brief_plan.scenario_id
        locked_unsuitable = (
            direction.fallback_reason in {None, "LOCKED_WITH_ASSET_GAPS"}
            and scenario not in profile.scenario_fit
        )
        if locked_unsuitable:
            findings.append(
                QualityFindingV2(
                    "compile",
                    "CONCEPT_CONTENT_FIT_LOW",
                    "important",
                    None,
                    direction.selected_profile_id,
                    "selected direction does not register the current scenario as a fit",
                    repairable=True,
                    source_stage="design-quality",
                )
            )
    render_plan = generation.render_plan
    if render_plan is not None:
        content_render_slides = [
            slide
            for slide in render_plan.slides
            if slide.role not in {"cover", "agenda", "closing", "cta", "section"}
        ]
        substantive = sum(
            any(
                item.advanced is not None
                or item.source_path is not None
                or item.component
                in {
                    "kpi",
                    "quote",
                    "risk-panel",
                    "recommendation-panel",
                    "comparison-panel",
                    "timeline-node",
                    "process-step",
                }
                for item in slide.objects
            )
            for slide in content_render_slides
        )
        if len(content_render_slides) >= 4 and substantive == 0:
            findings.append(
                QualityFindingV2(
                    "render",
                    "TEXT_ONLY_DECK_MONOCULTURE",
                    "important",
                    None,
                    None,
                    "all content pages use plain text without a governed visual form",
                    metric=0,
                    threshold=1,
                    repairable=True,
                    source_stage="design-quality",
                )
            )
        for slide in render_plan.slides:
            decorations = sum(
                item.component in {"decoration", "accent"}
                for item in slide.objects
            )
            if decorations > 3:
                findings.append(
                    QualityFindingV2(
                        "render",
                        "DECORATION_OVERUSE",
                        "important",
                        slide.source_id,
                        None,
                        "decorative object count exceeds the governed maximum",
                        metric=decorations,
                        threshold=3,
                        repairable=True,
                        source_stage="design-quality",
                    )
                )
            if slide.role not in {"cover", "agenda", "closing", "cta", "section"}:
                semantic_objects = [
                    item
                    for item in slide.objects
                    if item.component not in {"footer", "decoration", "accent"}
                ]
                occupied = sum(item.width * item.height for item in semantic_objects)
                slide_area = render_plan.slide_size.width * render_plan.slide_size.height
                occupied_ratio = occupied / slide_area if slide_area else 0.0
                if occupied_ratio < 0.12:
                    findings.append(
                        QualityFindingV2(
                            "render",
                            "LOW_INFORMATION_AREA",
                            "warning",
                            slide.source_id,
                            None,
                            "semantic objects occupy less than 12 percent of the page",
                            metric=round(occupied_ratio, 3),
                            threshold=0.12,
                            repairable=True,
                            source_stage="design-quality",
                        )
                    )
    return tuple(findings)


__all__ = ["inspect_design_quality"]
