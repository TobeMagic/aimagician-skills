"""Narrative-first contracts for governed PPTX Studio assembly.

The authoring model decides *why* a page exists and which supplied facts it
owns.  It does not decide geometry or implementation.  This module derives
the delivery count from retained beats and rejects the common replay failure of
section/title pages that are never followed by evidence.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


class NarrativeError(ValueError):
    """Raised when a brief or narrative exceeds the governed planning contract."""


_BRIEF_FIELDS = frozenset({
    "schema_version", "brief_id", "audience", "purpose", "delivery_context",
    "facts", "assets", "constraints", "assumptions",
})
_FACT_FIELDS = frozenset({"fact_id", "value"})
_ASSET_FIELDS = frozenset({"asset_id", "sha256"})
_PLAN_FIELDS = frozenset({
    "schema_version", "brief_id", "style_intent", "beats", "fact_coverage",
})
_STYLE_FIELDS = frozenset({"industry", "audience_tone", "visual_tone", "brand_constraints"})
_BEAT_FIELDS = frozenset({
    "beat_id", "kind", "section_id", "page_intent", "key_message", "fact_ids",
    "grammar", "density", "estimated_units", "capacity_units", "disposition",
})
_COVERAGE_FIELDS = frozenset({"fact_id", "disposition", "reason"})
_BEAT_KINDS = frozenset({"cover", "contents", "section", "body", "closing"})
_GRAMMARS = frozenset({
    "cover", "agenda", "section", "statement", "kpi", "comparison", "trend",
    "composition", "table", "timeline", "process", "matrix", "roadmap",
    "business_model", "product", "team", "risk", "quote", "closing",
})
_DENSITIES = frozenset({"low", "balanced", "high"})
_DISPOSITIONS = frozenset({"keep", "split", "merge", "delete"})
_COVERAGE_DISPOSITIONS = frozenset({"used", "deferred", "rejected"})
_STRUCTURAL_KINDS = frozenset({"cover", "contents", "section", "closing"})


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def narrative_digest(value: Mapping[str, Any]) -> str:
    """Return a stable digest for a validated brief or narrative plan."""

    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_exact_fields(value: Any, fields: frozenset[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise NarrativeError(code)
    return value


def validate_normalized_brief(brief: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a client-only brief without interpreting visual design details."""

    payload = _require_exact_fields(brief, _BRIEF_FIELDS, "BRIEF_SCHEMA_INVALID")
    if payload.get("schema_version") != "pptx-studio-brief-normalized.v1":
        raise NarrativeError("BRIEF_SCHEMA_INVALID")
    for field in ("brief_id", "audience", "purpose", "delivery_context"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise NarrativeError(f"BRIEF_{field.upper()}_INVALID")
    facts = payload.get("facts")
    assets = payload.get("assets")
    constraints = payload.get("constraints")
    assumptions = payload.get("assumptions")
    if not isinstance(facts, list) or not facts:
        raise NarrativeError("BRIEF_FACTS_INVALID")
    if not isinstance(assets, list) or not isinstance(constraints, list) or not isinstance(assumptions, list):
        raise NarrativeError("BRIEF_LIST_INVALID")
    fact_ids: set[str] = set()
    for item in facts:
        fact = _require_exact_fields(item, _FACT_FIELDS, "BRIEF_FACT_INVALID")
        fact_id, value = fact.get("fact_id"), fact.get("value")
        if not isinstance(fact_id, str) or not fact_id or fact_id in fact_ids or not isinstance(value, str) or not value.strip():
            raise NarrativeError("BRIEF_FACT_INVALID")
        fact_ids.add(fact_id)
    asset_ids: set[str] = set()
    for item in assets:
        asset = _require_exact_fields(item, _ASSET_FIELDS, "BRIEF_ASSET_INVALID")
        asset_id, digest = asset.get("asset_id"), asset.get("sha256")
        if (
            not isinstance(asset_id, str) or not asset_id or asset_id in asset_ids
            or not isinstance(digest, str) or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise NarrativeError("BRIEF_ASSET_INVALID")
        asset_ids.add(asset_id)
    if any(not isinstance(item, str) or not item.strip() for item in constraints + assumptions):
        raise NarrativeError("BRIEF_LIST_ENTRY_INVALID")
    return {
        "brief_id": payload["brief_id"],
        "fact_ids": frozenset(fact_ids),
        "asset_ids": frozenset(asset_ids),
        "digest": narrative_digest(payload),
    }


def validate_narrative_plan(
    brief: Mapping[str, Any], plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate beats, derive delivery count, and return an evidence report.

    A `merge` or `delete` beat documents planning work but is deliberately not
    emitted.  `keep` and `split` are delivery beats.  No plan field specifies
    a final number of slides: the returned count is calculated from the valid
    delivery beat sequence.
    """

    validated_brief = validate_normalized_brief(brief)
    payload = _require_exact_fields(plan, _PLAN_FIELDS, "NARRATIVE_SCHEMA_INVALID")
    if payload.get("schema_version") != "pptx-studio-narrative-plan.v1":
        raise NarrativeError("NARRATIVE_SCHEMA_INVALID")
    if payload.get("brief_id") != validated_brief["brief_id"]:
        raise NarrativeError("NARRATIVE_BRIEF_MISMATCH")
    style = _require_exact_fields(payload.get("style_intent"), _STYLE_FIELDS, "STYLE_INTENT_INVALID")
    if any(not isinstance(style.get(field), str) or not style[field].strip() for field in _STYLE_FIELDS):
        raise NarrativeError("STYLE_INTENT_INVALID")
    beats = payload.get("beats")
    coverage = payload.get("fact_coverage")
    if not isinstance(beats, list) or len(beats) < 2 or not isinstance(coverage, list):
        raise NarrativeError("NARRATIVE_LIST_INVALID")

    beat_ids: set[str] = set()
    delivery_beats: list[Mapping[str, Any]] = []
    all_referenced_facts: set[str] = set()
    for raw in beats:
        beat = _require_exact_fields(raw, _BEAT_FIELDS, "BEAT_SCHEMA_INVALID")
        beat_id, kind = beat.get("beat_id"), beat.get("kind")
        if not isinstance(beat_id, str) or not beat_id or beat_id in beat_ids:
            raise NarrativeError("BEAT_ID_INVALID")
        beat_ids.add(beat_id)
        if kind not in _BEAT_KINDS:
            raise NarrativeError("BEAT_KIND_INVALID")
        section_id = beat.get("section_id")
        if section_id is not None and (not isinstance(section_id, str) or not section_id):
            raise NarrativeError("BEAT_SECTION_INVALID")
        for field in ("page_intent", "key_message"):
            if not isinstance(beat.get(field), str) or not beat[field].strip():
                raise NarrativeError(f"BEAT_{field.upper()}_INVALID")
        if beat.get("grammar") not in _GRAMMARS or beat.get("density") not in _DENSITIES:
            raise NarrativeError("BEAT_GRAMMAR_OR_DENSITY_INVALID")
        disposition = beat.get("disposition")
        if disposition not in _DISPOSITIONS:
            raise NarrativeError("BEAT_DISPOSITION_INVALID")
        estimated, capacity = beat.get("estimated_units"), beat.get("capacity_units")
        if type(estimated) is not int or type(capacity) is not int or estimated < 0 or capacity < 1:
            raise NarrativeError("BEAT_CAPACITY_INVALID")
        if estimated > capacity and disposition != "split":
            raise NarrativeError(f"BEAT_CAPACITY_SPLIT_REQUIRED:{beat_id}")
        fact_ids = beat.get("fact_ids")
        if not isinstance(fact_ids, list) or any(not isinstance(item, str) or not item for item in fact_ids):
            raise NarrativeError("BEAT_FACT_IDS_INVALID")
        if len(set(fact_ids)) != len(fact_ids) or any(item not in validated_brief["fact_ids"] for item in fact_ids):
            raise NarrativeError("BEAT_FACT_UNKNOWN")
        if kind == "section" and (not isinstance(section_id, str) or not section_id):
            raise NarrativeError("SECTION_ID_REQUIRED")
        if kind == "body" and not fact_ids:
            raise NarrativeError(f"BODY_FACT_REQUIRED:{beat_id}")
        if kind not in _STRUCTURAL_KINDS and estimated == 0:
            raise NarrativeError(f"BEAT_UNDERFILLED:{beat_id}")
        if disposition in {"keep", "split"}:
            delivery_beats.append(beat)
            all_referenced_facts.update(fact_ids)
    if len(delivery_beats) < 2:
        raise NarrativeError("DELIVERY_BEAT_COUNT_INVALID")
    if delivery_beats[0]["kind"] != "cover" or delivery_beats[-1]["kind"] != "closing":
        raise NarrativeError("DELIVERY_ANATOMY_INVALID")

    for index, beat in enumerate(delivery_beats):
        if beat["kind"] != "section":
            continue
        section_id = beat["section_id"]
        evidence_window = delivery_beats[index + 1:index + 3]
        if not any(
            candidate["kind"] == "body"
            and candidate.get("section_id") == section_id
            and candidate.get("fact_ids")
            for candidate in evidence_window
        ):
            raise NarrativeError(f"SECTION_EVIDENCE_REQUIRED:{beat['beat_id']}")

    coverage_by_fact: dict[str, Mapping[str, Any]] = {}
    for raw in coverage:
        entry = _require_exact_fields(raw, _COVERAGE_FIELDS, "FACT_COVERAGE_SCHEMA_INVALID")
        fact_id, disposition, reason = entry.get("fact_id"), entry.get("disposition"), entry.get("reason")
        if (
            not isinstance(fact_id, str) or fact_id not in validated_brief["fact_ids"]
            or fact_id in coverage_by_fact or disposition not in _COVERAGE_DISPOSITIONS
            or not isinstance(reason, str) or not reason.strip()
        ):
            raise NarrativeError("FACT_COVERAGE_INVALID")
        coverage_by_fact[fact_id] = entry
    if set(coverage_by_fact) != set(validated_brief["fact_ids"]):
        raise NarrativeError("FACT_COVERAGE_INCOMPLETE")
    for fact_id in all_referenced_facts:
        if coverage_by_fact[fact_id]["disposition"] != "used":
            raise NarrativeError(f"FACT_COVERAGE_CONTRADICTION:{fact_id}")

    return {
        "schema_version": "pptx-studio-narrative-validation.v1",
        "status": "PASS",
        "brief_id": validated_brief["brief_id"],
        "brief_sha256": validated_brief["digest"],
        "narrative_sha256": narrative_digest(payload),
        "slide_count": len(delivery_beats),
        "delivery_beat_ids": [str(beat["beat_id"]) for beat in delivery_beats],
        "section_evidence": [
            {
                "section_beat_id": str(beat["beat_id"]),
                "section_id": str(beat["section_id"]),
            }
            for beat in delivery_beats if beat["kind"] == "section"
        ],
    }
