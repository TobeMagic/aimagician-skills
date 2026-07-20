"""Versioned semantic DeckPlan validation and compilation."""

from __future__ import annotations

import copy
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .registry import Archetype, RegistryError, resolve_archetype


SCHEMA_VERSION = "1.0"
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")

FORBIDDEN_RAW_FIELDS = {
    "x",
    "y",
    "w",
    "h",
    "left",
    "top",
    "right",
    "bottom",
    "width",
    "height",
    "position",
    "coordinates",
    "bounds",
    "margin",
    "padding",
    "gap",
    "font",
    "fonts",
    "font_name",
    "font_size",
    "typeface",
    "color",
    "colors",
    "fill",
    "stroke",
    "shadow",
    "layout",
    "layout_id",
    "template_id",
    "theme_id",
    "com",
    "com_call",
    "vba",
    "macro",
    "script",
    "code",
    "python",
    "javascript",
}

CONTENT_KINDS = {
    "bullets",
    "metrics",
    "comparison",
    "sequence",
    "timeline",
    "trend",
    "composition",
    "matrix",
    "risk",
    "recommendation",
    "quote",
    "table",
    "image",
    "statement",
    "generic",
}
IMPORTANCE_LEVELS = {"low", "normal", "high", "critical"}
CHART_INTENTS = {"trend", "comparison", "composition", "distribution", "relationship"}
DATA_ITEM_FIELDS = {
    "id",
    "label",
    "title",
    "name",
    "value",
    "unit",
    "category",
    "series",
    "description",
    "text",
    "status",
    "date",
    "start",
    "end",
    "source",
    "group",
    "primary",
    "secondary",
    "before",
    "after",
    "target",
    "actual",
    "probability",
    "impact",
    "owner",
}
DATA_STRING_LIMITS = {
    "id": 160,
    "label": 160,
    "title": 160,
    "name": 160,
    "unit": 40,
    "category": 160,
    "series": 160,
    "description": 160,
    "text": 160,
    "status": 100,
    "date": 80,
    "source": 160,
    "group": 160,
    "owner": 160,
}
PREFERENCE_VALUES = {
    "tone": {"conservative", "professional", "bold", "editorial", "educational"},
    "density": {"sparse", "balanced", "dense"},
    "audience_mode": {"executive", "customer", "investor", "internal", "learner", "general"},
}


class DeckPlanValidationError(ValueError):
    """The model-supplied DeckPlan crossed a governed semantic boundary."""


@dataclass(frozen=True)
class ProjectIntent:
    title: str
    scenario: str
    audience: str | None = None
    objective: str | None = None
    language: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"title": self.title, "scenario": self.scenario}
        for key in ("audience", "objective", "language"):
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result


@dataclass(frozen=True)
class ContentBlock:
    id: str
    kind: str
    title: str | None = None
    text: str | None = None
    items: tuple[Any, ...] = ()
    role_hint: str | None = None
    chart_intent: str | None = None
    source_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"id": self.id, "kind": self.kind}
        for key in ("title", "text", "role_hint", "chart_intent", "source_ref"):
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        if self.items:
            result["items"] = copy.deepcopy(list(self.items))
        return result


@dataclass(frozen=True)
class SlideIntent:
    id: str
    role: str
    title: str | None
    importance: str
    blocks: tuple[ContentBlock, ...]
    continuation_of: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "role": self.role,
            "importance": self.importance,
            "blocks": [block.to_dict() for block in self.blocks],
        }
        if self.title is not None:
            result["title"] = self.title
        if self.continuation_of is not None:
            result["continuation_of"] = self.continuation_of
        return result


@dataclass(frozen=True)
class DeckPlan:
    schema_version: str
    project: ProjectIntent
    slides: tuple[SlideIntent, ...]
    preferences: tuple[tuple[str, str], ...] = ()

    def preferences_dict(self) -> dict[str, str]:
        return dict(self.preferences)


def _scan_forbidden(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise DeckPlanValidationError(f"{path} contains a non-string JSON key")
            normalized = key.casefold().replace("-", "_").strip()
            if normalized in FORBIDDEN_RAW_FIELDS:
                raise DeckPlanValidationError(
                    f"{path}.{key} is forbidden; DeckPlan accepts semantic intent only"
                )
            _scan_forbidden(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_forbidden(item, f"{path}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise DeckPlanValidationError(f"{path} must contain a finite JSON number")
    elif value is None or isinstance(value, (str, int, float, bool)):
        return
    else:
        raise DeckPlanValidationError(f"{path} is not JSON-compatible")


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DeckPlanValidationError(f"{path} must be an object")
    return value


def _array(value: Any, path: str, *, non_empty: bool = True) -> list[Any]:
    if not isinstance(value, list) or (non_empty and not value):
        qualifier = "a non-empty" if non_empty else "an"
        raise DeckPlanValidationError(f"{path} must be {qualifier} array")
    return value


def _reject_unknown(value: Mapping[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise DeckPlanValidationError(
            f"{path} has unknown fields: {', '.join(unknown)}"
        )


def _string(
    value: Any,
    path: str,
    *,
    required: bool = True,
    minimum: int = 1,
    maximum: int = 4000,
) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise DeckPlanValidationError(f"{path} must be a non-empty string")
    if value != value.strip():
        raise DeckPlanValidationError(
            f"{path} must not contain leading or trailing whitespace"
        )
    result = value
    if len(result) < minimum:
        raise DeckPlanValidationError(f"{path} must contain at least {minimum} characters")
    if len(result) > maximum:
        raise DeckPlanValidationError(f"{path} exceeds {maximum} characters")
    return result


def _identifier(value: Any, path: str) -> str:
    result = _string(value, path, maximum=80)
    assert result is not None
    if not IDENTIFIER.fullmatch(result):
        raise DeckPlanValidationError(
            f"{path} must match lowercase semantic identifier syntax"
        )
    return result


def _parse_project(value: Any) -> tuple[ProjectIntent, Archetype]:
    raw = _object(value, "$.project")
    _reject_unknown(raw, {"title", "scenario", "audience", "objective", "language"}, "$.project")
    title = _string(raw.get("title"), "$.project.title", maximum=200)
    scenario = _string(raw.get("scenario"), "$.project.scenario", maximum=100)
    assert title is not None and scenario is not None
    try:
        archetype = resolve_archetype(scenario)
    except RegistryError as exc:
        raise DeckPlanValidationError(f"$.project.scenario: {exc}") from exc
    return (
        ProjectIntent(
            title=title,
            scenario=archetype.id,
            audience=_string(
                raw.get("audience"),
                "$.project.audience",
                required=False,
                maximum=120,
            ),
            objective=_string(
                raw.get("objective"),
                "$.project.objective",
                required=False,
                maximum=300,
            ),
            language=_string(
                raw.get("language"),
                "$.project.language",
                required=False,
                minimum=2,
                maximum=20,
            ),
        ),
        archetype,
    )


def _parse_block(value: Any, path: str) -> ContentBlock:
    raw = _object(value, path)
    allowed = {
        "id",
        "kind",
        "title",
        "text",
        "items",
        "role_hint",
        "chart_intent",
        "source_ref",
    }
    _reject_unknown(raw, allowed, path)
    block_id = _identifier(raw.get("id"), f"{path}.id")
    kind = _string(raw.get("kind"), f"{path}.kind", maximum=40)
    assert kind is not None
    if kind not in CONTENT_KINDS:
        raise DeckPlanValidationError(f"{path}.kind is not registered: {kind}")
    items = (
        _array(raw["items"], f"{path}.items") if "items" in raw else []
    )
    normalized_items: list[Any] = []
    for index, item in enumerate(items):
        item_path = f"{path}.items[{index}]"
        if isinstance(item, dict):
            if not item:
                raise DeckPlanValidationError(
                    f"{item_path} must contain at least one semantic field"
                )
            if len(item) > 5:
                raise DeckPlanValidationError(
                    f"{item_path} must contain at most 5 semantic fields"
                )
            _reject_unknown(item, DATA_ITEM_FIELDS, item_path)
            normalized_item: dict[str, Any] = {}
            for field, field_value in item.items():
                field_path = f"{item_path}.{field}"
                if field in DATA_STRING_LIMITS:
                    normalized_item[field] = _string(
                        field_value,
                        field_path,
                        maximum=DATA_STRING_LIMITS[field],
                    )
                elif isinstance(field_value, str):
                    normalized_item[field] = _string(
                        field_value,
                        field_path,
                        maximum=160,
                    )
                elif field_value is None or isinstance(
                    field_value, (int, float, bool)
                ):
                    normalized_item[field] = field_value
                else:
                    raise DeckPlanValidationError(
                        f"{field_path} must be a scalar semantic value"
                    )
            normalized_items.append(normalized_item)
        elif isinstance(item, str):
            normalized_items.append(_string(item, item_path, maximum=600))
        elif item is None or isinstance(item, (int, float, bool)):
            normalized_items.append(item)
        else:
            raise DeckPlanValidationError(
                f"{item_path} must be a scalar or controlled data item"
            )
    chart_intent = _string(
        raw.get("chart_intent"), f"{path}.chart_intent", required=False, maximum=40
    )
    if chart_intent is not None and chart_intent not in CHART_INTENTS:
        raise DeckPlanValidationError(
            f"{path}.chart_intent is not registered: {chart_intent}"
        )
    role_hint_raw = raw.get("role_hint")
    role_hint = (
        _identifier(role_hint_raw, f"{path}.role_hint")
        if role_hint_raw is not None
        else None
    )
    title = _string(raw.get("title"), f"{path}.title", required=False, maximum=200)
    text = _string(raw.get("text"), f"{path}.text", required=False)
    source_ref = _string(
        raw.get("source_ref"), f"{path}.source_ref", required=False, maximum=500
    )
    if not normalized_items and title is None and text is None and source_ref is None:
        raise DeckPlanValidationError(
            f"{path} must contain semantic content in title, text, items, or source_ref"
        )
    return ContentBlock(
        id=block_id,
        kind=kind,
        title=title,
        text=text,
        items=tuple(copy.deepcopy(normalized_items)),
        role_hint=role_hint,
        chart_intent=chart_intent,
        source_ref=source_ref,
    )


def _parse_slide(value: Any, path: str) -> SlideIntent:
    raw = _object(value, path)
    _reject_unknown(raw, {"id", "role", "title", "importance", "blocks"}, path)
    blocks = tuple(
        _parse_block(block, f"{path}.blocks[{index}]")
        for index, block in enumerate(_array(raw.get("blocks"), f"{path}.blocks"))
    )
    block_ids = [block.id for block in blocks]
    if len(block_ids) != len(set(block_ids)):
        raise DeckPlanValidationError(f"{path}.blocks contains duplicate block ids")
    importance = raw.get("importance", "normal")
    if not isinstance(importance, str) or importance not in IMPORTANCE_LEVELS:
        raise DeckPlanValidationError(f"{path}.importance is not registered: {importance}")
    return SlideIntent(
        id=_identifier(raw.get("id"), f"{path}.id"),
        role=_identifier(raw.get("role"), f"{path}.role"),
        title=_string(raw.get("title"), f"{path}.title", required=False, maximum=200),
        importance=importance,
        blocks=blocks,
    )


_ROLE_CANDIDATES: dict[str, tuple[str, ...]] = {
    "metrics": ("performance", "traction", "key-metrics", "financials", "executive-summary"),
    "trend": ("trends", "market-trends", "performance", "insights", "findings"),
    "composition": ("segments", "channels", "funnel", "insights", "findings"),
    "comparison": ("competition", "options", "positioning", "current-state", "insights"),
    "sequence": ("process", "approach", "workstreams", "implementation", "next-steps"),
    "timeline": ("timeline", "roadmap", "calendar", "milestones", "next-steps"),
    "matrix": ("choices", "competition", "risks", "insights"),
    "risk": ("risks", "issues", "limitations", "challenges"),
    "recommendation": ("recommendations", "action-plan", "next-steps", "immediate-actions"),
    "quote": ("executive-summary", "vision", "brand-story", "takeaways"),
    "table": ("data-scope", "commercials", "performance", "findings"),
    "image": ("product-showcase", "brand-story", "evidence", "case-study"),
    "statement": ("executive-summary", "value-proposition", "vision", "takeaways"),
    "bullets": ("insights", "findings", "strategic-pillars", "takeaways"),
    "generic": ("insights", "findings", "executive-summary"),
}


def _role_for_block(block: ContentBlock, archetype: Archetype) -> str:
    if block.role_hint is not None:
        if block.role_hint not in archetype.sections:
            raise DeckPlanValidationError(
                f"content block {block.id} role_hint {block.role_hint!r} is not in "
                f"archetype {archetype.id}"
            )
        return block.role_hint
    for candidate in _ROLE_CANDIDATES.get(block.kind, _ROLE_CANDIDATES["generic"]):
        if candidate in archetype.sections:
            return candidate
    return archetype.sections[1]


def _derive_slides(
    content: list[Any], project: ProjectIntent, archetype: Archetype
) -> tuple[SlideIntent, ...]:
    blocks = tuple(
        _parse_block(item, f"$.content[{index}]") for index, item in enumerate(content)
    )
    ids = [block.id for block in blocks]
    if len(ids) != len(set(ids)):
        raise DeckPlanValidationError("$.content contains duplicate block ids")
    section_order = {section: index for index, section in enumerate(archetype.sections)}
    derived: list[tuple[int, int, SlideIntent]] = []
    for index, block in enumerate(blocks):
        role = _role_for_block(block, archetype)
        derived.append(
            (
                section_order[role],
                index,
                SlideIntent(
                    id=block.id,
                    role=role,
                    title=block.title or role.replace("-", " ").title(),
                    importance="normal",
                    blocks=(block,),
                ),
            )
        )
    return tuple(item[2] for item in sorted(derived, key=lambda item: (item[0], item[1])))


def _parse_preferences(value: Any) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    raw = _object(value, "$.preferences")
    _reject_unknown(raw, set(PREFERENCE_VALUES), "$.preferences")
    result: list[tuple[str, str]] = []
    for key in sorted(raw):
        item = raw[key]
        if not isinstance(item, str) or item not in PREFERENCE_VALUES[key]:
            raise DeckPlanValidationError(f"$.preferences.{key} is not registered: {item}")
        result.append((key, item))
    return tuple(result)


def validate_deck_plan(payload: Any) -> DeckPlan:
    """Validate JSON-compatible semantic input without accepting design instructions."""

    _scan_forbidden(payload)
    raw = _object(payload, "$")
    _reject_unknown(raw, {"schema_version", "project", "slides", "content", "preferences"}, "$")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise DeckPlanValidationError("$.schema_version must equal 1.0")
    has_slides = "slides" in raw
    has_content = "content" in raw
    if has_slides == has_content:
        raise DeckPlanValidationError("DeckPlan requires exactly one of slides or content")
    project, archetype = _parse_project(raw.get("project"))
    if has_slides:
        slides = tuple(
            _parse_slide(item, f"$.slides[{index}]")
            for index, item in enumerate(_array(raw["slides"], "$.slides"))
        )
    else:
        slides = _derive_slides(_array(raw["content"], "$.content"), project, archetype)
    slide_ids = [slide.id for slide in slides]
    if len(slide_ids) != len(set(slide_ids)):
        raise DeckPlanValidationError("DeckPlan contains duplicate slide ids")
    block_ids = [block.id for slide in slides for block in slide.blocks]
    if len(block_ids) != len(set(block_ids)):
        raise DeckPlanValidationError("DeckPlan contains duplicate block ids")
    return DeckPlan(
        schema_version=SCHEMA_VERSION,
        project=project,
        slides=slides,
        preferences=_parse_preferences(raw.get("preferences")),
    )


def load_deck_plan(path: Path | str) -> DeckPlan:
    """Read one UTF-8 DeckPlan JSON document and apply semantic validation."""

    deck_path = Path(path)
    try:
        payload = json.loads(deck_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeckPlanValidationError(f"cannot load DeckPlan {deck_path}: {exc}") from exc
    return validate_deck_plan(payload)


def _deck_plan_payload(plan: DeckPlan) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": plan.schema_version,
        "project": plan.project.to_dict(),
        "slides": [slide.to_dict() for slide in plan.slides],
    }
    if plan.preferences:
        payload["preferences"] = plan.preferences_dict()
    return payload


_SEMANTIC_PRIORITY = {
    "metrics": 100,
    "trend": 98,
    "composition": 96,
    "comparison": 94,
    "timeline": 92,
    "sequence": 90,
    "matrix": 88,
    "risk": 86,
    "recommendation": 84,
    "table": 82,
    "image": 80,
    "bullets": 70,
    "quote": 62,
    "statement": 60,
    "generic": 10,
}


def _dominant_semantic_block(
    slide: SlideIntent,
) -> tuple[ContentBlock, str, int]:
    ranked: list[tuple[int, int, int, ContentBlock, str]] = []
    for index, block in enumerate(slide.blocks):
        semantic_type = block.chart_intent or block.kind
        priority = (
            200
            if block.chart_intent is not None
            else _SEMANTIC_PRIORITY.get(block.kind, 0)
        )
        richness = len(block.items) or (1 if block.text or block.title else 0)
        ranked.append((priority, richness, -index, block, semantic_type))
    _, _, negative_index, block, semantic_type = max(
        ranked, key=lambda item: item[:3]
    )
    return block, semantic_type, -negative_index


def compile_deck_plan(payload: Any) -> dict[str, Any]:
    """Compile validated semantic intent into deterministic, design-neutral slides."""

    from .capacity import split_slide
    from .rules import rank_page_families

    plan = validate_deck_plan(
        _deck_plan_payload(payload) if isinstance(payload, DeckPlan) else payload
    )
    archetype = resolve_archetype(plan.project.scenario)
    compiled_slides: list[dict[str, Any]] = []
    previous_families: list[str] = []
    density = plan.preferences_dict().get("density", "balanced")
    for source_slide in plan.slides:
        for slide in split_slide(source_slide, density=density):
            primary, semantic_type, block_index = _dominant_semantic_block(slide)
            item_count = len(primary.items) or (1 if primary.text or primary.title else 0)
            decision = rank_page_families(
                semantic_type,
                item_count=item_count,
                previous_families=previous_families,
            )
            compiled = slide.to_dict()
            compiled["page_family"] = decision.selected
            compiled["semantic_basis"] = {
                "block_id": primary.id,
                "block_index": block_index,
                "semantic_type": semantic_type,
                "rule_id": "DOMINANT_SEMANTIC_BLOCK",
            }
            compiled["decision_trace"] = decision.to_dict()
            compiled_slides.append(compiled)
            previous_families.append(decision.selected)
    return {
        "schema_version": SCHEMA_VERSION,
        "compiler_version": "window-pptx-semantic-1.0",
        "project": plan.project.to_dict(),
        "preferences": plan.preferences_dict(),
        "archetype_id": archetype.id,
        "archetype_outline": list(archetype.sections),
        "slides": compiled_slides,
    }
