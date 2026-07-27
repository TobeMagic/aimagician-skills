"""Strict weak-model intake and deterministic narrative planning.

The model never owns facts or raw design.  It may only group immutable fact
identifiers and choose registered semantic hints.  This module compiles that
small contract into the existing canonical DeckPlan v1 boundary.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .deck_plan import (
    CONTENT_KINDS,
    FORBIDDEN_RAW_FIELDS,
    IMPORTANCE_LEVELS,
    PREFERENCE_VALUES,
    validate_deck_plan,
)
from .registry import Archetype, resolve_archetype


SCHEMA_VERSION = "1.0"
SKILL_ROOT = Path(__file__).resolve().parents[2]
NARRATIVE_RULES_PATH = SKILL_ROOT / "registries" / "narrative-rules.json"
FACT_KINDS = {"claim", "metric", "quote", "date", "instruction", "label"}
SOURCE_KINDS = {"request", "document", "data", "manual"}
FACT_STATUSES = {"active", "superseded", "disputed"}
WEAK_IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMANTIC_HINT_ALIASES = {
    "scope": "bullets",
    "objectives": "bullets",
    "team": "bullets",
    "roles": "bullets",
    "performance": "metrics",
    "key-metrics": "metrics",
    "market-size": "metrics",
    "traction": "metrics",
    "financials": "metrics",
    "competition": "comparison",
    "differentiation": "comparison",
    "milestones": "timeline",
    "calendar": "timeline",
    "implementation": "process",
    "go-to-market": "process",
    "workstreams": "process",
    "risks": "risk",
    "limitations": "risk",
    "recommendations": "recommendation",
    "next-steps": "recommendation",
    "call-to-action": "recommendation",
    "funding-ask": "recommendation",
    "case-study": "quote",
}


class WeakModelValidationError(ValueError):
    """Weak-model input crossed a fact, schema, or design boundary."""


@dataclass(frozen=True)
class FactSource:
    id: str
    kind: str
    locator: str
    sha256: str | None = None


@dataclass(frozen=True)
class Fact:
    id: str
    kind: str
    text: str
    language: str
    source_id: str
    locator: str
    required: bool
    value: str | int | float | bool | None = None
    unit: str | None = None
    claim_key: str | None = None
    time_scope: str | None = None
    status: str = "active"
    recommended_beat: str | None = None
    recommended_semantic: str | None = None


@dataclass(frozen=True)
class TrustedProject:
    title: str
    objective: str | None
    audience: str | None
    language: str


@dataclass(frozen=True)
class FactStore:
    schema_version: str
    project: TrustedProject
    sources: tuple[FactSource, ...]
    facts: tuple[Fact, ...]
    digest: str

    def fact(self, fact_id: str) -> Fact:
        for fact in self.facts:
            if fact.id == fact_id:
                return fact
        raise WeakModelValidationError(f"FACT_REF_UNKNOWN: {fact_id}")

    def active_facts(self) -> tuple[Fact, ...]:
        return tuple(item for item in self.facts if item.status == "active")


@dataclass(frozen=True)
class BriefGroup:
    id: str
    fact_refs: tuple[str, ...]
    beat_hint: str | None
    semantic_hint: str | None
    importance: str
    auto_assigned: bool = False


@dataclass(frozen=True)
class BriefPlan:
    schema_version: str
    scenario_id: str
    groups: tuple[BriefGroup, ...]
    preferences: tuple[tuple[str, str], ...]

    def preferences_dict(self) -> dict[str, str]:
        return dict(self.preferences)


@dataclass(frozen=True)
class NormalizationTrace:
    changes: tuple[str, ...]


@dataclass(frozen=True)
class NarrativeSlide:
    id: str
    role: str
    title: str
    importance: str
    fact_refs: tuple[str, ...]
    semantic_kind: str
    structural: bool = False


@dataclass(frozen=True)
class NarrativePlan:
    schema_version: str
    archetype_id: str
    fact_store_digest: str
    slides: tuple[NarrativeSlide, ...]
    coverage: dict[str, Any]
    decisions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "archetype_id": self.archetype_id,
            "fact_store_digest": self.fact_store_digest,
            "slides": [
                {
                    "id": item.id,
                    "role": item.role,
                    "title": item.title,
                    "importance": item.importance,
                    "fact_refs": list(item.fact_refs),
                    "semantic_kind": item.semantic_kind,
                    "structural": item.structural,
                }
                for item in self.slides
            ],
            "coverage": copy.deepcopy(self.coverage),
            "decisions": list(self.decisions),
        }


@dataclass(frozen=True)
class BriefCompilation:
    fact_store: FactStore
    brief_plan: BriefPlan
    narrative: NarrativePlan
    deck_plan: dict[str, Any]
    normalization_trace: NormalizationTrace


@dataclass(frozen=True)
class BriefAttempt:
    index: int
    accepted: bool
    error_code: str | None
    error_message: str | None


@dataclass(frozen=True)
class BriefRetryResult:
    compilation: BriefCompilation
    attempts: tuple[BriefAttempt, ...]
    fallback_used: bool


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _strict_object(value: Any, path: str, allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WeakModelValidationError(f"{path} must be an object")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise WeakModelValidationError(
            f"{path} has unknown fields: {', '.join(unknown)}"
        )
    return value


def _strict_string(value: Any, path: str, maximum: int = 4000) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise WeakModelValidationError(f"{path} must be a trimmed non-empty string")
    if len(value) > maximum:
        raise WeakModelValidationError(f"{path} exceeds {maximum} characters")
    return value


def _identifier(value: Any, path: str) -> str:
    result = _strict_string(value, path, 80)
    if not WEAK_IDENTIFIER.fullmatch(result):
        raise WeakModelValidationError(f"{path} must be a lowercase semantic id")
    return result


def _scan_model_boundary(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise WeakModelValidationError(f"{path} has a non-string key")
            normalized = key.casefold().replace("-", "_").strip()
            if normalized in FORBIDDEN_RAW_FIELDS:
                raise WeakModelValidationError(
                    f"{path}.{key} is forbidden; BriefPlan accepts semantic references only"
                )
            _scan_model_boundary(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_model_boundary(item, f"{path}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise WeakModelValidationError(f"{path} contains a non-finite number")
    elif value is None or isinstance(value, (str, int, float, bool)):
        return
    else:
        raise WeakModelValidationError(f"{path} is not JSON-compatible")


def validate_fact_store(payload: Any) -> FactStore:
    """Validate trusted factual input and freeze it behind a canonical digest."""

    raw = _strict_object(
        payload, "$", {"schema_version", "project", "sources", "facts"}
    )
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise WeakModelValidationError("$.schema_version must equal 1.0")
    project_raw = _strict_object(
        raw.get("project"),
        "$.project",
        {"title", "objective", "audience", "language"},
    )
    project = TrustedProject(
        title=_strict_string(project_raw.get("title"), "$.project.title", 200),
        objective=(
            _strict_string(project_raw["objective"], "$.project.objective", 500)
            if "objective" in project_raw
            else None
        ),
        audience=(
            _strict_string(project_raw["audience"], "$.project.audience", 160)
            if "audience" in project_raw
            else None
        ),
        language=_strict_string(project_raw.get("language"), "$.project.language", 20),
    )
    source_items = raw.get("sources")
    if not isinstance(source_items, list) or not source_items:
        raise WeakModelValidationError("$.sources must be a non-empty array")
    sources: list[FactSource] = []
    for index, value in enumerate(source_items):
        path = f"$.sources[{index}]"
        item = _strict_object(value, path, {"id", "kind", "locator", "sha256"})
        kind = _strict_string(item.get("kind"), f"{path}.kind", 30)
        if kind not in SOURCE_KINDS:
            raise WeakModelValidationError(f"{path}.kind is not registered: {kind}")
        digest = item.get("sha256")
        if digest is not None and (
            not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise WeakModelValidationError(f"{path}.sha256 must be lowercase SHA-256")
        sources.append(
            FactSource(
                id=_identifier(item.get("id"), f"{path}.id"),
                kind=kind,
                locator=_strict_string(item.get("locator"), f"{path}.locator", 500),
                sha256=digest,
            )
        )
    source_ids = [item.id for item in sources]
    if len(source_ids) != len(set(source_ids)):
        raise WeakModelValidationError("$.sources contains duplicate ids")

    fact_items = raw.get("facts")
    if not isinstance(fact_items, list) or not fact_items:
        raise WeakModelValidationError("$.facts must be a non-empty array")
    facts: list[Fact] = []
    fact_allowed = {
        "id",
        "kind",
        "text",
        "language",
        "source_id",
        "locator",
        "required",
        "value",
        "unit",
        "claim_key",
        "time_scope",
        "status",
        "recommended_beat",
        "recommended_semantic",
    }
    for index, value in enumerate(fact_items):
        path = f"$.facts[{index}]"
        item = _strict_object(value, path, fact_allowed)
        kind = _strict_string(item.get("kind"), f"{path}.kind", 30)
        if kind not in FACT_KINDS:
            raise WeakModelValidationError(f"{path}.kind is not registered: {kind}")
        source_id = _identifier(item.get("source_id"), f"{path}.source_id")
        if source_id not in source_ids:
            raise WeakModelValidationError(f"{path}.source_id is unknown: {source_id}")
        required = item.get("required")
        if not isinstance(required, bool):
            raise WeakModelValidationError(f"{path}.required must be boolean")
        scalar = item.get("value")
        if scalar is not None and not isinstance(scalar, (str, int, float, bool)):
            raise WeakModelValidationError(f"{path}.value must be scalar")
        if isinstance(scalar, float) and not math.isfinite(scalar):
            raise WeakModelValidationError(f"{path}.value must be finite")
        status = item.get("status", "active")
        if status not in FACT_STATUSES:
            raise WeakModelValidationError(f"{path}.status is not registered: {status}")
        facts.append(
            Fact(
                id=_identifier(item.get("id"), f"{path}.id"),
                kind=kind,
                text=_strict_string(item.get("text"), f"{path}.text"),
                language=_strict_string(item.get("language"), f"{path}.language", 20),
                source_id=source_id,
                locator=_strict_string(item.get("locator"), f"{path}.locator", 500),
                required=required,
                value=scalar,
                unit=(
                    _strict_string(item["unit"], f"{path}.unit", 80)
                    if "unit" in item
                    else None
                ),
                claim_key=(
                    _identifier(item["claim_key"], f"{path}.claim_key")
                    if "claim_key" in item
                    else None
                ),
                time_scope=(
                    _strict_string(item["time_scope"], f"{path}.time_scope", 120)
                    if "time_scope" in item
                    else None
                ),
                status=status,
                recommended_beat=(
                    _identifier(item["recommended_beat"], f"{path}.recommended_beat")
                    if "recommended_beat" in item
                    else None
                ),
                recommended_semantic=(
                    _strict_string(
                        item["recommended_semantic"],
                        f"{path}.recommended_semantic",
                        40,
                    )
                    if "recommended_semantic" in item
                    else None
                ),
            )
        )
        if (
            facts[-1].recommended_semantic is not None
            and facts[-1].recommended_semantic not in CONTENT_KINDS
        ):
            raise WeakModelValidationError(
                f"{path}.recommended_semantic is not registered"
            )
    fact_ids = [item.id for item in facts]
    if len(fact_ids) != len(set(fact_ids)):
        raise WeakModelValidationError("$.facts contains duplicate ids")
    active_claims: dict[tuple[str, str, str], Fact] = {}
    for fact in facts:
        if fact.status != "active" or fact.claim_key is None:
            continue
        key = (fact.claim_key, fact.time_scope or "", fact.unit or "")
        previous = active_claims.get(key)
        if previous is not None and previous.value != fact.value:
            raise WeakModelValidationError(
                f"FACT_CONFLICT: {previous.id} and {fact.id} have different active values"
            )
        active_claims[key] = fact
    digest = hashlib.sha256(_canonical_json(raw).encode("utf-8")).hexdigest()
    return FactStore(SCHEMA_VERSION, project, tuple(sources), tuple(facts), digest)


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return normalized[:80]


def normalize_brief_plan(payload: str | Mapping[str, Any]) -> tuple[dict[str, Any], NormalizationTrace]:
    """Repair harmless serialization/alias errors without changing semantics."""

    changes: list[str] = []
    if isinstance(payload, str):
        text = payload.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.I | re.S)
        if fenced:
            text = fenced.group(1)
            changes.append("STRIPPED_JSON_FENCE")
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise WeakModelValidationError(f"BRIEF_JSON_INVALID: {exc}") from exc
    elif isinstance(payload, Mapping):
        value = copy.deepcopy(dict(payload))
    else:
        raise WeakModelValidationError("BriefPlan must be an object or JSON string")
    _scan_model_boundary(value)
    if value.get("schema_version") in {1, "v1", "V1"}:
        value["schema_version"] = SCHEMA_VERSION
        changes.append("NORMALIZED_SCHEMA_VERSION")
    scenario = value.get("scenario_id")
    if isinstance(scenario, str):
        try:
            canonical = resolve_archetype(scenario).id
        except Exception:
            canonical = scenario
        if canonical != scenario:
            value["scenario_id"] = canonical
            changes.append("NORMALIZED_SCENARIO_ALIAS")
    groups = value.get("groups")
    if isinstance(groups, list):
        for group in groups:
            if not isinstance(group, dict):
                continue
            group_id = group.get("id")
            if isinstance(group_id, str) and not WEAK_IDENTIFIER.fullmatch(group_id):
                normalized_id = _slug(group_id)
                if normalized_id:
                    group["id"] = normalized_id
                    changes.append("NORMALIZED_GROUP_ID")
            for field in ("beat_hint", "semantic_hint"):
                item = group.get(field)
                if isinstance(item, str):
                    normalized_item = _slug(item)
                    if normalized_item != item:
                        group[field] = normalized_item
                        changes.append(f"NORMALIZED_{field.upper()}")
                    if field == "semantic_hint":
                        aliased = SEMANTIC_HINT_ALIASES.get(normalized_item)
                        if aliased is not None:
                            group[field] = aliased
                            changes.append("NORMALIZED_SEMANTIC_ALIAS")
    return value, NormalizationTrace(tuple(changes))


def validate_brief_plan(payload: Any, fact_store: FactStore) -> BriefPlan:
    _scan_model_boundary(payload)
    raw = _strict_object(
        payload, "$", {"schema_version", "scenario_id", "groups", "preferences"}
    )
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise WeakModelValidationError("$.schema_version must equal 1.0")
    scenario = _strict_string(raw.get("scenario_id"), "$.scenario_id", 100)
    try:
        archetype = resolve_archetype(scenario)
    except Exception as exc:
        raise WeakModelValidationError(f"SCENARIO_UNKNOWN: {scenario}") from exc
    group_items = raw.get("groups")
    if not isinstance(group_items, list) or not group_items:
        raise WeakModelValidationError("$.groups must be a non-empty array")
    active = {item.id: item for item in fact_store.active_facts()}
    groups: list[BriefGroup] = []
    used_refs: set[str] = set()
    for index, value in enumerate(group_items):
        path = f"$.groups[{index}]"
        item = _strict_object(
            value,
            path,
            {"id", "fact_refs", "beat_hint", "semantic_hint", "importance"},
        )
        refs = item.get("fact_refs")
        if not isinstance(refs, list) or not refs:
            raise WeakModelValidationError(f"{path}.fact_refs must be non-empty")
        normalized_refs: list[str] = []
        for ref_index, ref in enumerate(refs):
            fact_id = _identifier(ref, f"{path}.fact_refs[{ref_index}]")
            if fact_id not in active:
                raise WeakModelValidationError(f"FACT_REF_UNKNOWN: {fact_id}")
            if fact_id in used_refs:
                raise WeakModelValidationError(f"FACT_REF_DUPLICATED: {fact_id}")
            used_refs.add(fact_id)
            normalized_refs.append(fact_id)
        beat = item.get("beat_hint")
        if beat is not None:
            beat = _identifier(beat, f"{path}.beat_hint")
            if beat not in archetype.sections:
                raise WeakModelValidationError(
                    f"BEAT_UNKNOWN: {beat} is not registered for {archetype.id}"
                )
        semantic = item.get("semantic_hint")
        if semantic is not None:
            semantic = _strict_string(semantic, f"{path}.semantic_hint", 40)
            if semantic not in CONTENT_KINDS:
                raise WeakModelValidationError(f"SEMANTIC_UNKNOWN: {semantic}")
        importance = item.get("importance", "normal")
        if importance not in IMPORTANCE_LEVELS:
            raise WeakModelValidationError(f"{path}.importance is not registered")
        groups.append(
            BriefGroup(
                id=_identifier(item.get("id"), f"{path}.id"),
                fact_refs=tuple(normalized_refs),
                beat_hint=beat,
                semantic_hint=semantic,
                importance=importance,
            )
        )
    if len({item.id for item in groups}) != len(groups):
        raise WeakModelValidationError("$.groups contains duplicate ids")
    preferences_raw = raw.get("preferences", {})
    preferences_obj = _strict_object(
        preferences_raw, "$.preferences", set(PREFERENCE_VALUES)
    )
    preferences: list[tuple[str, str]] = []
    for key in sorted(preferences_obj):
        value = preferences_obj[key]
        if value not in PREFERENCE_VALUES[key]:
            raise WeakModelValidationError(f"$.preferences.{key} is not registered")
        preferences.append((key, value))
    return BriefPlan(
        SCHEMA_VERSION, archetype.id, tuple(groups), tuple(preferences)
    )


def load_narrative_rules(path: Path | str | None = None) -> dict[str, tuple[str, ...]]:
    source = Path(path) if path is not None else NARRATIVE_RULES_PATH
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WeakModelValidationError(f"cannot load narrative rules: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "archetypes"}:
        raise WeakModelValidationError("narrative rules have an invalid root")
    if raw["schema_version"] != SCHEMA_VERSION or not isinstance(raw["archetypes"], list):
        raise WeakModelValidationError("narrative rules schema_version must equal 1.0")
    result: dict[str, tuple[str, ...]] = {}
    for index, item in enumerate(raw["archetypes"]):
        if not isinstance(item, dict) or set(item) != {"id", "critical_beats"}:
            raise WeakModelValidationError(f"narrative rules entry {index} is invalid")
        archetype = resolve_archetype(item["id"])
        beats = item["critical_beats"]
        if not isinstance(beats, list) or not beats:
            raise WeakModelValidationError(f"{archetype.id} critical_beats is empty")
        beat_tuple = tuple(_identifier(value, f"{archetype.id}.critical_beats") for value in beats)
        if not set(beat_tuple) <= set(archetype.sections):
            raise WeakModelValidationError(f"{archetype.id} has unknown critical beats")
        result[archetype.id] = beat_tuple
    expected = set(resolve_archetype(item).id for item in (
        "business-report", "project-proposal", "product-launch", "market-analysis",
        "sales-proposal", "investor-pitch", "annual-review", "strategic-plan",
        "data-analysis", "research-report", "training", "brand-introduction",
        "project-kickoff", "operations-review", "ecommerce-marketing",
    ))
    if set(result) != expected:
        raise WeakModelValidationError("narrative rules must cover all 15 archetypes")
    return result


def _semantic_from_fact_kind(fact: Fact) -> str:
    """Return the strongest semantic form supported by the fact payload itself."""

    if fact.kind == "metric":
        return "metrics"
    if fact.kind == "quote":
        return "quote"
    if fact.kind == "instruction":
        return "recommendation"
    if fact.kind == "date":
        return "timeline"
    return "statement"


def _semantic_for_fact(fact: Fact) -> str:
    if fact.recommended_semantic is not None:
        return fact.recommended_semantic
    return _semantic_from_fact_kind(fact)


def _role_for_fact(fact: Fact, archetype: Archetype) -> str:
    if fact.recommended_beat is not None:
        if fact.recommended_beat not in archetype.sections:
            raise WeakModelValidationError(
                f"TRUSTED_BEAT_UNKNOWN: {fact.id} -> {fact.recommended_beat}"
            )
        return fact.recommended_beat
    candidates = {
        "metric": ("performance", "key-metrics", "traction", "market-size", "findings"),
        "instruction": ("recommendations", "next-steps", "call-to-action", "immediate-actions"),
        "date": ("timeline", "roadmap", "calendar", "milestones"),
        "quote": ("executive-summary", "abstract", "brand-story", "takeaways"),
        "claim": ("insights", "findings", "value-proposition", "executive-summary"),
        "label": ("context", "background", "agenda"),
    }.get(fact.kind, ("insights", "findings"))
    return next((item for item in candidates if item in archetype.sections), archetype.sections[1])


def _action_title(
    fact: Fact,
    *,
    role: str | None = None,
    prefer_role: bool = False,
) -> str:
    """Keep a complete evidence-backed thought, never an ellipsized fragment."""

    text = re.sub(r"\s+", " ", fact.text).strip()
    title_budget = 30 if re.search(r"[\u3400-\u9fff]", text) else 60
    if (
        prefer_role
        and role
        and not fact.language.casefold().startswith(("zh", "ja", "ko"))
    ):
        return role.replace("-", " ").title()
    if len(text) <= title_budget:
        return text
    # A decimal point is data, not a safe clause boundary.  Match terminal
    # punctuation only when the period is not followed by another digit so
    # values such as 8.6 or 3.8% can never become misleading titles like
    # ``The target is 8.``.
    for match in re.finditer(
        r"(?:\.(?!\d)|[!?。！？;；])(?=\s|$)", text
    ):
        if match.end() > title_budget:
            break
        candidate = text[: match.end()].strip()
        if len(candidate) >= (10 if title_budget == 30 else 18):
            return candidate
    # When the full evidence belongs in the body/KPI slot, use the governed
    # narrative beat as the concise page label.  This is deterministic and
    # contextual (Performance, Traction, Measurement...) without attempting
    # an abstractive rewrite of the evidence.  CJK decks keep the localized
    # fact-kind labels below until localized archetype labels are registered.
    if role and not fact.language.casefold().startswith(("zh", "ja", "ko")):
        return role.replace("-", " ").title()
    labels = {
        "claim": "Key takeaway",
        "metric": "Key metric",
        "quote": "Stakeholder voice",
        "date": "Milestone",
        "instruction": "Recommended action",
        "label": "Context",
    }
    if fact.language.casefold().startswith("zh"):
        labels = {
            "claim": "核心结论",
            "metric": "核心指标",
            "quote": "关键声音",
            "date": "关键里程碑",
            "instruction": "建议行动",
            "label": "背景信息",
        }
    return labels[fact.kind]


def _closing_title(objective: str, language: str) -> str:
    """Use a structural close label without paraphrasing the trusted action."""

    if language.casefold().startswith("zh"):
        return (
            "决策事项"
            if re.match(r"^\s*(?:决定|批准|选择|确认|优先)", objective)
            else "下一步行动"
        )
    return (
        "Decision required"
        if re.match(
            r"^\s*(?:decide|approve|select|choose|confirm|commit|prioritize)\b",
            objective,
            flags=re.IGNORECASE,
        )
        else "Next action"
    )


_EXACT_MEASURE_PATTERN = re.compile(
    r"(?P<value>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s+"
    r"(?P<unit>percent|percentage points?|million dollars?|billion dollars?|"
    r"thousand dollars?|accounts?|customer teams?|customers?|records?|retailers?|warehouses?|"
    r"offices?|brands?|regions?|subscriptions?|releases?|hours?|minutes?|"
    r"days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
_EXACT_CHANGE_PATTERN = re.compile(
    r"\bfrom\s+(?P<before>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?:\s+(?P<before_unit>[A-Za-z ]+?))?\s+to\s+"
    r"(?P<after>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s+"
    r"(?P<after_unit>percent|percentage points?|million dollars?|"
    r"billion dollars?|thousand dollars?|accounts?|customer teams?|customers?|records?|"
    r"retailers?|warehouses?|offices?|brands?|regions?|subscriptions?|"
    r"releases?|hours?|minutes?|days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
_EXACT_PRIORITY_PAIR_PATTERN = re.compile(
    r"\b(?:identified|selected|named)\s+"
    r"(?P<first>[A-Za-z][A-Za-z0-9 /&-]{1,60}?)\s+and\s+"
    r"(?P<second>[A-Za-z][A-Za-z0-9 /&-]{1,60}?)\s+"
    r"as\s+the\s+two\b",
    re.IGNORECASE,
)
_EXACT_PARALLEL_LIST_PATTERN = re.compile(
    r"\b(?:supports|includes|offers|integrates with)\s+"
    r"(?P<items>[A-Za-z0-9][A-Za-z0-9, /&+.-]{1,140}?)\.\s*$",
    re.IGNORECASE,
)


def _exact_number(value: str) -> int | float:
    normalized = value.replace(",", "")
    return float(normalized) if "." in normalized else int(normalized)


def _exact_measure_label(
    fact: Fact,
    match: re.Match[str],
    *,
    fallback: str,
) -> str:
    """Use a source-present comparison label, otherwise a neutral fallback."""

    suffix = fact.text[match.end() :]
    prefix = fact.text[: match.start()]
    if re.search(r"\bonboarding\s+within\s*$", prefix, re.IGNORECASE):
        return "Onboarding Window"
    if re.search(r"\bretain\s*$", prefix, re.IGNORECASE) and re.match(
        r"\s+better\b", suffix, re.IGNORECASE
    ):
        return "Retention Lift"
    qualified = re.match(
        r"\s+for\s+(?P<label>[A-Za-z][A-Za-z0-9 /&-]{1,40}?)"
        r"(?=(?:\s+(?:and|versus|vs\.?)\s+\d)|[.,;]|$)",
        suffix,
        re.IGNORECASE,
    )
    if qualified is not None:
        return re.sub(r"\s+", " ", qualified.group("label")).strip().title()
    relative = re.match(
        r"\s+(?P<label>(?:above|below|over|under)\s+"
        r"[A-Za-z0-9][A-Za-z0-9 /&-]{0,40}?)(?=[.,;]|$)",
        suffix,
        re.IGNORECASE,
    )
    if relative is not None:
        return re.sub(r"\s+", " ", relative.group("label")).strip().title()

    subject = re.search(
        r"(?:^|[.;]|\band\b)\s*"
        r"(?P<label>[A-Za-z][A-Za-z0-9 /&-]{0,40}?)\s+"
        r"(?:is|was|were|reached|equals?|total(?:ed|s)?)\s*$",
        prefix,
        re.IGNORECASE,
    )
    if subject is not None:
        return re.sub(r"\s+", " ", subject.group("label")).strip().title()
    return fallback


def _trusted_categorical_comparison(fact: Fact) -> bool:
    """Recognize two or more same-unit measures with explicit source labels."""

    if fact.kind != "metric":
        return False
    measures = tuple(_EXACT_MEASURE_PATTERN.finditer(fact.text))
    if len(measures) < 2:
        return False
    units = {match.group("unit").strip().casefold() for match in measures}
    if len(units) != 1:
        return False
    labels = tuple(
        _exact_measure_label(fact, match, fallback="") for match in measures
    )
    return all(labels) and len({label.casefold() for label in labels}) == len(labels)


def _unseriesed_trend_claim(fact: Fact) -> bool:
    """Identify an exact trend statement that has no chartable time series."""

    if fact.kind != "metric" or isinstance(fact.value, (int, float)):
        return False
    lowered = fact.text.casefold()
    return bool(
        re.search(r"\b(?:declined|increased|grew|fell|rose|improved)\b", lowered)
        and re.search(r"\bfrom\s+[^.]{1,50}\s+to\s+[^.]{1,50}", lowered)
    )


def _trusted_metric_change(
    fact: Fact,
) -> tuple[int | float, str, int | float, str] | None:
    """Return an explicit from/to pair only for an already trusted scalar fact."""

    if fact.kind != "metric" or fact.value is None or fact.unit is None:
        return None
    match = _EXACT_CHANGE_PATTERN.search(fact.text)
    if match is None:
        return None
    before = _exact_number(match.group("before"))
    after = _exact_number(match.group("after"))
    after_unit = match.group("after_unit").strip()
    # English often elides the first unit ("from 44 to 41 percent").  When
    # it is written explicitly, however, it is factual content and must stay
    # attached to the first value.  In particular, converting
    # "3 hours to 35 minutes" into "3 minutes to 35 minutes" reverses the
    # visual meaning even though both numeric tokens remain source-present.
    before_unit = (match.group("before_unit") or after_unit).strip()
    if (
        isinstance(fact.value, bool)
        or not isinstance(fact.value, (int, float))
        or float(after) != float(fact.value)
        or after_unit.casefold() != fact.unit.strip().casefold()
    ):
        return None
    return before, before_unit, after, after_unit


def _structured_metric_items(
    fact: Fact,
    *,
    include_description: bool,
) -> list[dict[str, Any]]:
    label = (
        fact.claim_key.replace("-", " ").title()
        if fact.claim_key is not None
        else _action_title(fact)
    )
    change = _trusted_metric_change(fact)
    if change is not None:
        before, before_unit, after, after_unit = change
        items: list[dict[str, Any]] = [
            {"label": "Before", "value": before, "unit": before_unit},
            {"label": "After", "value": after, "unit": after_unit},
        ]
        if include_description and len(fact.text) <= 160:
            items[-1]["description"] = fact.text
        return items

    measures = tuple(_EXACT_MEASURE_PATTERN.finditer(fact.text))
    trusted_measure_present = any(
        float(_exact_number(match.group("value"))) == float(fact.value)
        and match.group("unit").strip().casefold() == fact.unit.strip().casefold()
        for match in measures
        if isinstance(fact.value, (int, float)) and not isinstance(fact.value, bool)
    )
    if trusted_measure_present:
        items = []
        for index, match in enumerate(measures):
            item: dict[str, Any] = {
                "label": _exact_measure_label(
                    fact,
                    match,
                    fallback=label if index == 0 else f"Measure {index + 1}",
                ),
                "value": _exact_number(match.group("value")),
                "unit": match.group("unit").strip(),
            }
            if index == 0 and fact.time_scope is not None:
                item["category"] = fact.time_scope
            items.append(item)
        if include_description and len(fact.text) <= 160:
            items[-1]["description"] = fact.text
        return items

    item = {"label": label, "value": fact.value}
    if fact.time_scope is not None:
        item["category"] = fact.time_scope
    if fact.unit is not None:
        item["unit"] = fact.unit
    if include_description and len(fact.text) <= 160:
        item["description"] = fact.text
    return [item]


def _structured_instruction_items(fact: Fact) -> list[dict[str, Any]] | None:
    """Extract exactly two source-present priorities without paraphrasing."""

    if fact.kind != "instruction":
        return None
    match = _EXACT_PRIORITY_PAIR_PATTERN.search(fact.text)
    if match is None:
        return None
    first = re.sub(r"\s+", " ", match.group("first")).strip()
    second = re.sub(r"\s+", " ", match.group("second")).strip()
    if (
        not first
        or not second
        or first.casefold() == second.casefold()
        or len(first.split()) > 8
        or len(second.split()) > 8
    ):
        return None
    return [
        {"label": "Priority 1", "text": first},
        {"label": "Priority 2", "text": second},
    ]


def _structured_parallel_items(fact: Fact) -> list[str] | None:
    """Extract a short, explicit source list without paraphrasing its items."""

    match = _EXACT_PARALLEL_LIST_PATTERN.search(fact.text)
    if match is None:
        return None
    raw = match.group("items")
    if not re.search(r"\band\b", raw, re.IGNORECASE) or re.search(
        r"\d,\d{3}\b", raw
    ):
        return None
    parts = []
    for item in re.split(r"\s*,\s*|\s+and\s+", raw, flags=re.IGNORECASE):
        normalized = re.sub(r"\s+", " ", item).strip(" ,")
        normalized = re.sub(r"^and\s+", "", normalized, flags=re.IGNORECASE)
        parts.append(normalized)
    if (
        not 2 <= len(parts) <= 5
        or any(not item or len(item) > 48 for item in parts)
        or len({item.casefold() for item in parts}) != len(parts)
    ):
        return None
    return parts


def _semantic_hint_compatible(kind: str, facts: tuple[Fact, ...]) -> bool:
    numeric = tuple(
        fact
        for fact in facts
        if isinstance(fact.value, (int, float)) and not isinstance(fact.value, bool)
    )
    if kind in {"statement", "generic"}:
        return True
    if kind == "bullets":
        return len(facts) >= 2
    if kind == "metrics":
        # A trusted metric may carry its exact customer-visible value inside
        # the evidence sentence even when upstream data was not normalized
        # into ``value``.  Preserve metric emphasis without parsing, rounding,
        # or inventing a number; chart semantics still require structured data.
        return bool(numeric) or any(
            fact.kind == "metric"
            and (fact.value is not None or re.search(r"\d", fact.text))
            for fact in facts
        )
    if kind == "trend":
        return len(numeric) >= 2 and all(fact.time_scope for fact in numeric)
    if kind in {"comparison", "table", "matrix", "quadrant"}:
        return len(facts) >= 2 or (
            kind == "comparison"
            and len(facts) == 1
            and (
                _trusted_metric_change(facts[0]) is not None
                or _trusted_categorical_comparison(facts[0])
            )
        )
    if kind == "composition":
        return len(numeric) >= 2
    if kind == "funnel":
        return len(numeric) >= 3
    if kind == "timeline":
        return any(fact.kind == "date" or fact.time_scope for fact in facts)
    if kind in {"sequence", "process", "roadmap"}:
        return len(facts) >= 2 or any(
            fact.kind in {"instruction", "date"} for fact in facts
        )
    if kind == "risk":
        return any(fact.kind in {"claim", "instruction"} for fact in facts)
    if kind == "recommendation":
        return any(fact.kind == "instruction" for fact in facts)
    if kind == "quote":
        return len(facts) == 1 and facts[0].kind == "quote"
    if kind == "image":
        return False
    return False


def _effective_semantic(
    facts: tuple[Fact, ...], requested: str | None
) -> tuple[str, str | None]:
    trusted = {
        fact.recommended_semantic
        for fact in facts
        if fact.recommended_semantic is not None
    }
    if len(trusted) == 1:
        selected = next(iter(trusted))
        # Trusted image intent delegates its final compatibility decision to the
        # governed asset preflight, which can inspect the source-locator binding.
        if selected == "image" or _semantic_hint_compatible(selected, facts):
            return selected, (
                None
                if requested in {None, selected}
                else f"TRUSTED_SEMANTIC_OVERRIDES_MODEL:{requested}->{selected}"
            )
        fallback = _semantic_from_fact_kind(facts[0])
        if not _semantic_hint_compatible(fallback, facts):
            fallback = "statement"
        return fallback, (
            f"INCOMPATIBLE_TRUSTED_SEMANTIC_DOWNGRADED:{selected}->{fallback}"
        )
    if not trusted and len(facts) == 1:
        if _unseriesed_trend_claim(facts[0]):
            return "statement", (
                "UNSTRUCTURED_TREND_USES_STATEMENT"
                if requested is None
                else f"UNSTRUCTURED_TREND_OVERRIDES_MODEL:{requested}->statement"
            )
        if (
            _trusted_categorical_comparison(facts[0])
            and requested in {None, "generic", "statement", "metrics", "comparison"}
        ):
            return "comparison", (
                None
                if requested == "comparison"
                else "CATEGORICAL_COMPARISON_SELECTED"
                if requested is None
                else f"CATEGORICAL_COMPARISON_OVERRIDES_MODEL:{requested}->comparison"
            )
        parallel_items = _structured_parallel_items(facts[0])
        if parallel_items is not None and requested in {
            None,
            "generic",
            "statement",
            "table",
        }:
            return "bullets", (
                "EXACT_PARALLEL_LIST_SELECTED"
                if requested is None
                else f"EXACT_PARALLEL_LIST_OVERRIDES_MODEL:{requested}->bullets"
            )
        if (
            facts[0].kind == "metric"
            and facts[0].value is not None
            and requested in {None, "generic", "statement"}
        ):
            return "metrics", (
                "STRUCTURED_METRIC_SELECTED"
                if requested is None
                else f"STRUCTURED_METRIC_OVERRIDES_MODEL:{requested}->metrics"
            )
    if (
        not trusted
        and len(facts) == 1
        and requested in {"metrics", "risk", "comparison"}
        and _trusted_metric_change(facts[0]) is not None
    ):
        return "comparison", (
            None
            if requested == "comparison"
            else f"EXPLICIT_NUMERIC_CHANGE_OVERRIDES_MODEL:{requested}->comparison"
        )
    if requested is not None and _semantic_hint_compatible(requested, facts):
        return requested, None
    fallback = _semantic_for_fact(facts[0])
    if not _semantic_hint_compatible(fallback, facts):
        fallback = "statement"
    return fallback, (
        None
        if requested is None
        else f"INCOMPATIBLE_SEMANTIC_DOWNGRADED:{requested}->{fallback}"
    )


def _fact_block(
    fact: Fact,
    group: BriefGroup,
    index: int,
    *,
    semantic_kind: str,
    include_description: bool = False,
) -> dict[str, Any]:
    kind = semantic_kind
    block: dict[str, Any] = {
        "id": f"{group.id}.fact-{index + 1}",
        "kind": kind,
        "source_ref": f"{fact.source_id}#{fact.locator}",
    }
    if kind == "comparison" and _trusted_categorical_comparison(fact):
        block["chart_intent"] = "comparison"
    instruction_items = (
        _structured_instruction_items(fact) if kind == "recommendation" else None
    )
    parallel_items = _structured_parallel_items(fact) if kind == "bullets" else None
    if instruction_items is not None:
        block["items"] = instruction_items
        block["text"] = fact.text
    elif parallel_items is not None:
        block["items"] = parallel_items
        block["text"] = fact.text
    elif fact.value is not None and kind in {
        "metrics", "trend", "comparison", "composition", "table"
    }:
        block["items"] = _structured_metric_items(
            fact,
            include_description=include_description,
        )
        block["text"] = fact.text
    else:
        block["text"] = fact.text
    return block


def _split_groups_for_slide_floor(
    groups: list[BriefGroup],
    *,
    target_content_slides: int,
) -> tuple[list[BriefGroup], int]:
    """Split only existing multi-fact groups to approach an archetype floor.

    This never invents a page or repeats a fact.  It is the deterministic
    weak-model fallback for a valid but over-compressed BriefPlan: distinct
    facts become continuation pages until the governed content-page floor is
    reached or no evidence-safe split remains.
    """

    result = list(groups)
    splits = 0
    while len(result) < target_content_slides:
        candidates = [
            (-(len(group.fact_refs)), index, group)
            for index, group in enumerate(result)
            if len(group.fact_refs) > 1
        ]
        if not candidates:
            break
        _negative_size, index, group = min(candidates)
        first_ref, remaining_refs = group.fact_refs[0], group.fact_refs[1:]
        part_one = BriefGroup(
            id=_slug(f"{group.id}-detail-1"),
            fact_refs=(first_ref,),
            beat_hint=group.beat_hint,
            semantic_hint=group.semantic_hint,
            importance=group.importance,
            auto_assigned=group.auto_assigned,
        )
        part_two = BriefGroup(
            id=_slug(f"{group.id}-detail-2"),
            fact_refs=remaining_refs,
            beat_hint=group.beat_hint,
            semantic_hint=group.semantic_hint,
            importance=group.importance,
            auto_assigned=group.auto_assigned,
        )
        result[index : index + 1] = [part_one, part_two]
        splits += 1
    return result, splits


def _compile_narrative(fact_store: FactStore, brief: BriefPlan) -> tuple[NarrativePlan, dict[str, Any]]:
    archetype = resolve_archetype(brief.scenario_id)
    groups = list(brief.groups)
    used = {ref for group in groups for ref in group.fact_refs}
    auto_assigned: list[str] = []
    for fact in fact_store.active_facts():
        if fact.required and fact.id not in used:
            role = _role_for_fact(fact, archetype)
            group_id = f"auto-{fact.id}"
            groups.append(
                BriefGroup(
                    id=group_id,
                    fact_refs=(fact.id,),
                    beat_hint=role,
                    semantic_hint=_semantic_for_fact(fact),
                    importance="high",
                    auto_assigned=True,
                )
            )
            used.add(fact.id)
            auto_assigned.append(fact.id)

    authority_adjustments: list[str] = []
    authority_groups: list[BriefGroup] = []
    for group in groups:
        partitions: dict[str | None, list[str]] = {}
        for fact_id in group.fact_refs:
            fact = fact_store.fact(fact_id)
            trusted_role = fact.recommended_beat
            if trusted_role is not None and trusted_role not in archetype.sections:
                raise WeakModelValidationError(
                    f"TRUSTED_BEAT_UNKNOWN: {fact.id} -> {trusted_role}"
                )
            role = trusted_role or group.beat_hint
            partitions.setdefault(role, []).append(fact_id)
        if len(partitions) == 1:
            role, refs = next(iter(partitions.items()))
            if role != group.beat_hint and group.beat_hint is not None:
                authority_adjustments.append(
                    f"{group.id}:TRUSTED_BEAT_OVERRIDES_MODEL:{group.beat_hint}->{role}"
                )
            authority_groups.append(
                BriefGroup(
                    id=group.id,
                    fact_refs=tuple(refs),
                    beat_hint=role,
                    semantic_hint=group.semantic_hint,
                    importance=group.importance,
                    auto_assigned=group.auto_assigned,
                )
            )
            continue
        authority_adjustments.append(
            f"{group.id}:MIXED_TRUSTED_BEATS_SPLIT:{len(partitions)}"
        )
        for part_index, (role, refs) in enumerate(partitions.items(), start=1):
            authority_groups.append(
                BriefGroup(
                    id=_slug(f"{group.id}-part-{part_index}"),
                    fact_refs=tuple(refs),
                    beat_hint=role,
                    semantic_hint=group.semantic_hint,
                    importance=group.importance,
                    auto_assigned=group.auto_assigned,
                )
            )
    groups = authority_groups
    critical = load_narrative_rules()[archetype.id]
    assigned_roles = {group.beat_hint for group in groups if group.beat_hint}
    missing_critical = [beat for beat in critical if beat not in assigned_roles]
    if missing_critical:
        raise WeakModelValidationError(
            "NARRATIVE_REQUIRED_EVIDENCE_MISSING: " + ", ".join(missing_critical)
        )

    content_roles = tuple(
        role
        for role in archetype.sections
        if role not in {"cover", "agenda", "closing"}
    )
    used_roles = set(assigned_roles)
    auto_assigned_beat_groups: list[str] = []
    assigned_groups: list[BriefGroup] = []
    for group in groups:
        if group.beat_hint is not None:
            assigned_groups.append(group)
            continue
        fact = fact_store.fact(group.fact_refs[0])
        suggested = _role_for_fact(fact, archetype)
        role = next(
            (
                candidate
                for candidate in (suggested, *content_roles)
                if candidate not in used_roles
            ),
            suggested,
        )
        used_roles.add(role)
        auto_assigned_beat_groups.append(group.id)
        assigned_groups.append(
            BriefGroup(
                id=group.id,
                fact_refs=group.fact_refs,
                beat_hint=role,
                semantic_hint=group.semantic_hint,
                importance=group.importance,
                auto_assigned=group.auto_assigned,
            )
        )
    groups = assigned_groups
    assigned_roles = {group.beat_hint for group in groups if group.beat_hint}
    order = {role: index for index, role in enumerate(archetype.sections)}
    groups.sort(key=lambda item: (order.get(item.beat_hint or "", 10_000), item.id))
    include_agenda = "agenda" in archetype.sections and len(groups) >= 3
    structural_slide_count = 3 if include_agenda else 2
    groups, slide_floor_splits = _split_groups_for_slide_floor(
        groups,
        target_content_slides=max(
            1,
            archetype.slide_count_min - structural_slide_count,
        ),
    )

    narrative_slides: list[NarrativeSlide] = [
        NarrativeSlide(
            id="cover",
            role="cover",
            title=fact_store.project.title,
            importance="high",
            fact_refs=(),
            semantic_kind="statement",
            structural=True,
        )
    ]
    deck_slides: list[dict[str, Any]] = [
        {
            "id": "cover",
            "role": "cover",
            "title": fact_store.project.title,
            "importance": "high",
            "blocks": [
                {
                    "id": "cover.objective",
                    "kind": "statement",
                    "text": fact_store.project.objective or fact_store.project.title,
                }
            ],
        }
    ]
    if include_agenda:
        agenda_items = list(dict.fromkeys(
            (group.beat_hint or _role_for_fact(fact_store.fact(group.fact_refs[0]), archetype)).replace("-", " ").title()
            for group in groups
        ))
        narrative_slides.append(
            NarrativeSlide("agenda", "agenda", "Agenda", "normal", (), "bullets", True)
        )
        deck_slides.append(
            {
                "id": "agenda",
                "role": "agenda",
                "title": "Agenda",
                "importance": "normal",
                "blocks": [{"id": "agenda.items", "kind": "bullets", "items": agenda_items}],
            }
        )
    semantic_adjustments: list[str] = []
    for group in groups:
        facts = tuple(fact_store.fact(ref) for ref in group.fact_refs)
        role = group.beat_hint or _role_for_fact(facts[0], archetype)
        kind, semantic_adjustment = _effective_semantic(facts, group.semantic_hint)
        if semantic_adjustment is not None:
            semantic_adjustments.append(f"{group.id}:{semantic_adjustment}")
        explicit_change = (
            len(facts) == 1 and _trusted_metric_change(facts[0]) is not None
        )
        explicit_metric_title = (
            len(facts) == 1
            and (
                kind == "metrics"
                or (kind == "comparison" and _trusted_categorical_comparison(facts[0]))
            )
            and len(re.sub(r"\s+", " ", facts[0].text).strip())
            <= (
                30
                if re.search(r"[\u3400-\u9fff]", facts[0].text)
                else 100
            )
        )
        # A source-present from/to sentence is already an evidence-backed
        # action title.  Preserve it verbatim (within a conservative bound)
        # so the comparison panels can stay compact instead of repeating the
        # same sentence inside one card.  No paraphrase or derived delta is
        # introduced here.
        title = (
            re.sub(r"\s+", " ", facts[0].text).strip()
            if (explicit_change or explicit_metric_title)
            and len(facts[0].text) <= 100
            else _action_title(
                facts[0],
                role=role,
                prefer_role=(
                    kind == "timeline"
                    or (
                        kind == "metrics"
                        and all(fact.value is None for fact in facts)
                    )
                ),
            )
        )
        narrative_slides.append(
            NarrativeSlide(group.id, role, title, group.importance, group.fact_refs, kind)
        )
        deck_slides.append(
            {
                "id": group.id,
                "role": role,
                "title": title,
                "importance": group.importance,
                "blocks": [
                    _fact_block(
                        fact,
                        group,
                        index,
                        semantic_kind=kind,
                        include_description=(
                            re.sub(r"\s+", " ", fact.text).strip().casefold()
                            not in re.sub(r"\s+", " ", title).strip().casefold()
                        ),
                    )
                    for index, fact in enumerate(facts)
                ],
            }
        )
    closing_text = fact_store.project.objective or fact_store.project.title
    closing_title = _closing_title(closing_text, fact_store.project.language)
    narrative_slides.append(
        NarrativeSlide(
            "closing",
            "closing",
            closing_title,
            "high",
            (),
            "recommendation",
            True,
        )
    )
    deck_slides.append(
        {
            "id": "closing",
            "role": "closing",
            "title": closing_title,
            "importance": "high",
            "blocks": [{"id": "closing.action", "kind": "recommendation", "text": closing_text}],
        }
    )
    required = [fact.id for fact in fact_store.active_facts() if fact.required]
    covered = sorted(set(required) & used)
    coverage = {
        "required_fact_count": len(required),
        "covered_required_fact_count": len(covered),
        "required_fact_coverage": 1.0 if not required else len(covered) / len(required),
        "auto_assigned_fact_refs": auto_assigned,
        "auto_assigned_beat_groups": auto_assigned_beat_groups,
        "authority_adjustments": authority_adjustments,
        "semantic_adjustments": semantic_adjustments,
        "critical_beats": list(critical),
        "covered_critical_beats": sorted(set(critical) & assigned_roles),
        "archetype_slide_count_range": [
            archetype.slide_count_min,
            archetype.slide_count_max,
        ],
        "slide_floor_splits": slide_floor_splits,
        "slide_floor_satisfied": (
            len(groups) + structural_slide_count >= archetype.slide_count_min
        ),
    }
    narrative = NarrativePlan(
        SCHEMA_VERSION,
        archetype.id,
        fact_store.digest,
        tuple(narrative_slides),
        coverage,
        (
            "FACTSTORE_IMMUTABLE",
            "REQUIRED_FACTS_AUTO_ASSIGNED",
            "ACTION_TITLES_EVIDENCE_BOUNDED",
            "ARCHETYPE_ORDER_STABLE",
            "UNHINTED_BEATS_ASSIGNED_WITHOUT_REPETITION",
            "ARCHETYPE_SLIDE_RANGE_GOVERNED",
            *(
                ("EVIDENCE_SAFE_SLIDE_FLOOR_SPLIT",)
                if slide_floor_splits
                else ()
            ),
            *(
                ("ARCHETYPE_SLIDE_FLOOR_UNMET_WITHOUT_INVENTION",)
                if len(groups) + structural_slide_count < archetype.slide_count_min
                else ()
            ),
        ),
    )
    deck_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "project": {
            "title": fact_store.project.title,
            "scenario": archetype.id,
            "language": fact_store.project.language,
        },
        "slides": deck_slides,
    }
    if fact_store.project.audience is not None:
        deck_payload["project"]["audience"] = fact_store.project.audience
    if fact_store.project.objective is not None:
        deck_payload["project"]["objective"] = fact_store.project.objective
    if brief.preferences:
        deck_payload["preferences"] = brief.preferences_dict()
    validate_deck_plan(deck_payload)
    return narrative, deck_payload


def compile_brief_plan(fact_payload: Any, brief_payload: Any) -> BriefCompilation:
    """Compile trusted facts plus model references into canonical DeckPlan v1."""

    facts = fact_payload if isinstance(fact_payload, FactStore) else validate_fact_store(fact_payload)
    normalized, trace = normalize_brief_plan(brief_payload)
    brief = validate_brief_plan(normalized, facts)
    narrative, deck = _compile_narrative(facts, brief)
    return BriefCompilation(facts, brief, narrative, deck, trace)


def safe_default_brief_plan(
    fact_payload: FactStore | Any,
    scenario_id: str,
) -> dict[str, Any]:
    """Build the deterministic non-creative fallback after model retries fail."""

    facts = (
        fact_payload
        if isinstance(fact_payload, FactStore)
        else validate_fact_store(fact_payload)
    )
    archetype = resolve_archetype(scenario_id)
    critical = load_narrative_rules()[archetype.id][0]
    groups: list[dict[str, Any]] = []
    required_facts = tuple(fact for fact in facts.active_facts() if fact.required)
    for index, fact in enumerate(required_facts):
        group = {
            "id": f"safe-{fact.id}",
            "fact_refs": [fact.id],
            "semantic_hint": _semantic_for_fact(fact),
            "importance": "high" if fact.required else "normal",
        }
        if index == 0:
            group["beat_hint"] = critical
        groups.append(group)
    if not groups:
        raise WeakModelValidationError("SAFE_DEFAULT_HAS_NO_REQUIRED_FACTS")
    return {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": archetype.id,
        "groups": groups,
        "preferences": {
            "tone": "professional",
            "density": "balanced",
            "audience_mode": "general",
            "motion": "off",
        },
    }


def compile_brief_with_retries(
    fact_payload: FactStore | Any,
    candidate_payloads: list[Any] | tuple[Any, ...],
    *,
    scenario_id: str,
    max_retries: int = 2,
) -> BriefRetryResult:
    """Try at most one initial model response plus two retries, then fall back."""

    if isinstance(max_retries, bool) or not isinstance(max_retries, int) or not 0 <= max_retries <= 2:
        raise ValueError("max_retries must be an integer from 0 to 2")
    facts = (
        fact_payload
        if isinstance(fact_payload, FactStore)
        else validate_fact_store(fact_payload)
    )
    attempts: list[BriefAttempt] = []
    for index, payload in enumerate(tuple(candidate_payloads)[: max_retries + 1], start=1):
        try:
            compilation = compile_brief_plan(facts, payload)
            attempts.append(BriefAttempt(index, True, None, None))
            return BriefRetryResult(compilation, tuple(attempts), False)
        except WeakModelValidationError as exc:
            message = str(exc)
            code = message.split(":", 1)[0].split(" ", 1)[0]
            attempts.append(BriefAttempt(index, False, code, message))
    fallback = safe_default_brief_plan(facts, scenario_id)
    compilation = compile_brief_plan(facts, fallback)
    return BriefRetryResult(compilation, tuple(attempts), True)


def load_fact_store(path: Path | str) -> FactStore:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WeakModelValidationError(f"cannot load FactStore: {exc}") from exc
    return validate_fact_store(value)


def load_brief_plan(path: Path | str, fact_store: FactStore) -> BriefPlan:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise WeakModelValidationError(f"cannot load BriefPlan: {exc}") from exc
    normalized, _ = normalize_brief_plan(text)
    return validate_brief_plan(normalized, fact_store)


__all__ = [
    "BriefCompilation",
    "BriefAttempt",
    "BriefGroup",
    "BriefPlan",
    "BriefRetryResult",
    "Fact",
    "FactSource",
    "FactStore",
    "NarrativePlan",
    "NarrativeSlide",
    "NormalizationTrace",
    "TrustedProject",
    "WeakModelValidationError",
    "compile_brief_plan",
    "compile_brief_with_retries",
    "load_brief_plan",
    "load_fact_store",
    "load_narrative_rules",
    "normalize_brief_plan",
    "safe_default_brief_plan",
    "validate_brief_plan",
    "validate_fact_store",
]
