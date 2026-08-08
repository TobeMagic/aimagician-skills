"""Deterministic semantic-intent to physical AssemblyPlan compiler.

The agent-facing input is intentionally small: one certified page ID,
narrative role, and fact-ID set per slide.  A Skill-owned binding profile then
expands that intent into complete ordinary-text bindings.  Geometry, literal
private source copy, OOXML locators, chart/workbook coordinates, and arbitrary
replacement prose are never accepted from the agent.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .page_template_library import (
    DEFAULT_SCORING,
    LibraryIndex,
    PageTemplate,
    query_page_template_candidates,
)
from .weak_model import Fact, FactStore


class AutoBindingError(ValueError):
    """A semantic intent cannot be proven against its locked profile."""


_SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"
_ALLOWED_SEPARATORS = {"", " ", "\n", " / ", " · ", "：", ": "}
_ALLOWED_FIT_POLICIES = {"preserve", "no-autofit", "shrink-to-fit"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _validate_schema(payload: Mapping[str, Any], schema_name: str, code: str) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - installation contract
        raise AutoBindingError(f"{code}: jsonschema is required") from exc
    schema = json.loads((_SCHEMA_ROOT / schema_name).read_text(encoding="utf-8"))
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(payload),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        path = ".".join(str(part) for part in errors[0].absolute_path) or "$"
        raise AutoBindingError(f"{code}: {path}: {errors[0].message}")


def load_binding_profile(path: str | os.PathLike[str]) -> tuple[dict[str, Any], str]:
    profile_path = Path(path).expanduser().resolve(strict=True)
    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AutoBindingError(f"AUTO_BIND_PROFILE_INVALID: {exc}") from exc
    if not isinstance(payload, dict):
        raise AutoBindingError("AUTO_BIND_PROFILE_INVALID: root must be an object")
    _validate_schema(
        payload,
        "binding-profile.v1.schema.json",
        "AUTO_BIND_PROFILE_SCHEMA_INVALID",
    )
    return payload, _sha256_bytes(profile_path.read_bytes())


def load_assembly_intent(path: str | os.PathLike[str]) -> tuple[dict[str, Any], str]:
    intent_path = Path(path).expanduser().resolve(strict=True)
    try:
        payload = json.loads(intent_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AutoBindingError(f"AUTO_BIND_INTENT_INVALID: {exc}") from exc
    if not isinstance(payload, dict):
        raise AutoBindingError("AUTO_BIND_INTENT_INVALID: root must be an object")
    _validate_schema(
        payload,
        "assembly-intent.v1.schema.json",
        "AUTO_BIND_INTENT_SCHEMA_INVALID",
    )
    return payload, _sha256_bytes(intent_path.read_bytes())


def build_default_intent(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Create the smallest schema-valid intent for a locked profile."""

    payload = {
        "schema_version": "1.0",
        "profile_id": profile["profile_id"],
        "scenario_id": profile["scenario_id"],
        "slides": [
            {
                "ordinal": slide["ordinal"],
                "page_id": slide["page_id"],
                "narrative_role": slide["narrative_role"],
                "fact_ids": list(slide["fact_ids"]),
            }
            for slide in sorted(profile["slides"], key=lambda item: item["ordinal"])
        ],
    }
    _validate_schema(
        payload,
        "assembly-intent.v1.schema.json",
        "AUTO_BIND_INTENT_SCHEMA_INVALID",
    )
    return payload


def build_profile_query_bundle(
    profile: Mapping[str, Any],
    *,
    library_index: LibraryIndex,
    library_index_sha256: str,
    library_resolution_source: str,
) -> dict[str, Any]:
    """Build the full audit query bundle without an agent-authored request.

    The canonical request is embedded only through its digest.  Exact source
    ordinals are hard filters applied after the established global ranking and
    before the public limit, matching the production query CLI.
    """

    _validate_schema(
        profile,
        "binding-profile.v1.schema.json",
        "AUTO_BIND_PROFILE_SCHEMA_INVALID",
    )
    if profile["library_id"] != library_index.library_id:
        raise AutoBindingError("AUTO_BIND_LIBRARY_ID_MISMATCH")
    if profile["library_index_sha256"] != library_index_sha256:
        raise AutoBindingError("AUTO_BIND_LIBRARY_FINGERPRINT_MISMATCH")
    if library_resolution_source not in {
        "absolute-library",
        "explicit-private-root",
        "environment-private-root",
        "config-private-root",
    }:
        raise AutoBindingError("AUTO_BIND_LIBRARY_RESOLUTION_INVALID")

    request = {
        "schema_version": "page-template-query-request.v1",
        "slides": [
            {
                "target_ordinal": slide["ordinal"],
                "query_id": f"slide-{slide['ordinal']:02d}",
                **dict(slide["query"]),
            }
            for slide in sorted(profile["slides"], key=lambda item: item["ordinal"])
        ],
    }
    queries: list[dict[str, Any]] = []
    for slide in request["slides"]:
        required_source_ordinal = int(slide["required_source_ordinal"])
        limit = int(slide["limit"])
        ranked = query_page_template_candidates(
            library_index,
            role=str(slide["role"]),
            capacity_budget=int(slide["capacity_budget"]),
            semantic_categories=tuple(slide["semantic_categories"]),
            style_cluster=str(slide["style_cluster"]),
            asset_requirements=tuple(slide["asset_requirements"]),
            customer_assets_available=bool(slide["customer_assets_available"]),
            limit=max(limit, library_index.page_template_count),
            allow_fallback=bool(slide["allow_fallback"]),
            direct_use_only=True,
            include_ineligible=False,
        )
        candidates = tuple(
            candidate
            for candidate in ranked
            if candidate.page_template.slide_number == required_source_ordinal
        )[:limit]
        if not candidates:
            raise AutoBindingError(
                "AUTO_BIND_REQUIRED_SOURCE_NOT_FOUND: "
                f"{slide['target_ordinal']}:{required_source_ordinal}"
            )
        result = {
            "schema_version": "page-template-query-result.v1",
            "library_index_sha256": library_index_sha256,
            "required_source_ordinal": required_source_ordinal,
            "role": slide["role"],
            "capacity_budget": slide["capacity_budget"],
            "semantic_categories": list(slide["semantic_categories"]),
            "style_cluster": slide["style_cluster"],
            "asset_requirements": list(slide["asset_requirements"]),
            "customer_assets_available": slide["customer_assets_available"],
            "limit": limit,
            "allow_fallback": slide["allow_fallback"],
            "direct_use_only": True,
            "include_ineligible": False,
            "weights": dict(DEFAULT_SCORING),
            "count": len(candidates),
            "eligible_count": sum(candidate.eligibility for candidate in candidates),
            "candidates": [candidate.to_dict() for candidate in candidates],
        }
        queries.append(
            {
                "target_ordinal": slide["target_ordinal"],
                "query_id": slide["query_id"],
                "result": result,
            }
        )
    bundle = {
        "schema_version": "page-template-query-bundle.v1",
        "request_sha256": _sha256_bytes(_canonical_bytes(request)),
        "library_index_sha256": library_index_sha256,
        "library_resolution_source": library_resolution_source,
        "query_count": len(queries),
        "queries": queries,
    }
    return bundle


def _fact_renderings(fact: Fact) -> tuple[str, ...]:
    values: list[str] = [fact.text, *fact.allowed_renderings]
    if fact.value is not None:
        scalar = str(fact.value)
        values.extend((scalar, scalar + (fact.unit or "")))
    return tuple(dict.fromkeys(values))


def _resolve_rendering(
    selector: Mapping[str, Any],
    *,
    facts: Mapping[str, Fact],
    allowed_fact_ids: set[str],
) -> tuple[str, str]:
    fact_id = str(selector["fact_id"])
    if fact_id not in allowed_fact_ids:
        raise AutoBindingError(f"AUTO_BIND_FACT_SCOPE_VIOLATION: {fact_id}")
    fact = facts.get(fact_id)
    if fact is None:
        raise AutoBindingError(f"AUTO_BIND_FACT_UNKNOWN: {fact_id}")
    wanted = str(selector["rendering_sha256"])
    matches = [
        rendering
        for rendering in _fact_renderings(fact)
        if _sha256_bytes(rendering.encode("utf-8")) == wanted
    ]
    if len(matches) != 1:
        raise AutoBindingError(
            f"AUTO_BIND_RENDERING_NOT_REGISTERED: {fact_id}:{wanted}"
        )
    return fact_id, matches[0]


def _connective_index(payload: Mapping[str, Any]) -> dict[str, str]:
    if payload.get("schema_version") != "1.0" or not isinstance(
        payload.get("entries"), list
    ):
        raise AutoBindingError("AUTO_BIND_CONNECTIVE_AUTHORITY_INVALID")
    result: dict[str, str] = {}
    texts: set[str] = set()
    for raw in payload["entries"]:
        if not isinstance(raw, Mapping):
            raise AutoBindingError("AUTO_BIND_CONNECTIVE_AUTHORITY_INVALID")
        connective_id = raw.get("id")
        text = raw.get("text")
        if (
            not isinstance(connective_id, str)
            or not connective_id
            or not isinstance(text, str)
            or connective_id in result
            or text in texts
        ):
            raise AutoBindingError("AUTO_BIND_CONNECTIVE_AUTHORITY_INVALID")
        result[connective_id] = text
        texts.add(text)
    return result


def _resolve_rule(
    rule: Mapping[str, Any],
    *,
    facts: Mapping[str, Fact],
    allowed_fact_ids: set[str],
    connectives: Mapping[str, str],
) -> tuple[dict[str, Any], str]:
    kind = rule.get("kind")
    fit_policy = rule.get("fit_policy", "preserve")
    if fit_policy not in _ALLOWED_FIT_POLICIES:
        raise AutoBindingError(f"AUTO_BIND_FIT_POLICY_INVALID: {fit_policy}")
    if kind == "connective":
        connective_id = str(rule.get("connective_id", ""))
        if connective_id not in connectives:
            raise AutoBindingError(
                f"AUTO_BIND_CONNECTIVE_UNKNOWN: {connective_id}"
            )
        return {
            "text": connectives[connective_id],
            "fact_refs": [],
            "asset_refs": [],
            "fit_policy": fit_policy,
        }, "connective"
    if kind != "fact":
        raise AutoBindingError(f"AUTO_BIND_RULE_INVALID: {kind}")
    separator = rule.get("separator")
    if separator not in _ALLOWED_SEPARATORS:
        raise AutoBindingError(f"AUTO_BIND_SEPARATOR_INVALID: {separator!r}")
    resolved = [
        _resolve_rendering(
            selector,
            facts=facts,
            allowed_fact_ids=allowed_fact_ids,
        )
        for selector in rule.get("renderings", ())
    ]
    if not resolved:
        raise AutoBindingError("AUTO_BIND_RULE_INVALID: empty fact binding")
    return {
        "text": str(separator).join(rendering for _, rendering in resolved),
        "fact_refs": [fact_id for fact_id, _ in resolved],
        "asset_refs": [],
        "fit_policy": fit_policy,
    }, "fact"


def _slot_index(template: PageTemplate) -> dict[str, Mapping[str, Any]]:
    slots = template.slot_graph.get("slots", ())
    if not isinstance(slots, Sequence) or isinstance(slots, (str, bytes)):
        raise AutoBindingError(
            f"AUTO_BIND_SLOT_GRAPH_INVALID: {template.page_id}"
        )
    result: dict[str, Mapping[str, Any]] = {}
    for slot in slots:
        slot_id = slot.get("slot_id") if isinstance(slot, Mapping) else None
        if not isinstance(slot_id, str) or not slot_id or slot_id in result:
            raise AutoBindingError(
                f"AUTO_BIND_SLOT_GRAPH_INVALID: {template.page_id}"
            )
        result[slot_id] = slot
    expected = set(template.slot_graph.get("text_slot_ids", ()))
    if expected != set(result):
        raise AutoBindingError(
            f"AUTO_BIND_SLOT_GRAPH_INVALID: {template.page_id}"
        )
    return result


def _fragment_groups(template: PageTemplate) -> dict[str, tuple[str, ...]]:
    slots = _slot_index(template)
    groups = template.slot_graph.get("fragment_groups", ())
    if not isinstance(groups, Sequence) or isinstance(groups, (str, bytes)):
        raise AutoBindingError(
            f"AUTO_BIND_FRAGMENT_GROUPS_INVALID: {template.page_id}"
        )
    result: dict[str, tuple[str, ...]] = {}
    for raw in groups:
        group_id = raw.get("group_id") if isinstance(raw, Mapping) else None
        slot_ids = raw.get("slot_ids") if isinstance(raw, Mapping) else None
        if (
            not isinstance(group_id, str)
            or not group_id
            or group_id in result
            or not isinstance(slot_ids, list)
            or len(slot_ids) < 2
        ):
            raise AutoBindingError(
                f"AUTO_BIND_FRAGMENT_GROUPS_INVALID: {template.page_id}"
            )
        ordered: list[tuple[int, str]] = []
        for slot_id in slot_ids:
            slot = slots.get(slot_id)
            order = slot.get("group_order") if slot is not None else None
            if type(order) is not int or order < 1:
                raise AutoBindingError(
                    f"AUTO_BIND_FRAGMENT_ORDER_MISMATCH: {group_id}"
                )
            ordered.append((order, slot_id))
        if sorted(order for order, _ in ordered) != list(
            range(1, len(ordered) + 1)
        ):
            raise AutoBindingError(
                f"AUTO_BIND_FRAGMENT_ORDER_MISMATCH: {group_id}"
            )
        result[group_id] = tuple(slot_id for _, slot_id in sorted(ordered))
    return result


def _validate_capacity(
    *,
    ordinal: int,
    slot_id: str,
    slot: Mapping[str, Any],
    text: str,
) -> None:
    limit = slot.get("max_chars")
    # Certified slot capacities use semantic characters: extraction records
    # `source_char_count` after removing layout whitespace.  Applying the same
    # rule here preserves intentional spacing from the source template (for
    # example labels placed on both sides of a hero number) without treating
    # those positioning spaces as additional copy.
    semantic_char_count = len("".join(text.split()))
    if (
        type(limit) is not int
        or limit < 0
        or semantic_char_count > limit
    ):
        raise AutoBindingError(
            f"AUTO_BIND_RENDERING_OVER_CAPACITY: {ordinal}:{slot_id}:"
            f"{semantic_char_count}>{limit}"
        )
    item_limit = slot.get("max_items")
    if type(item_limit) is int and item_limit > 0:
        item_count = sum(1 for item in text.splitlines() if item.strip()) if text else 0
        if item_count > item_limit:
            raise AutoBindingError(
                f"AUTO_BIND_RENDERING_OVER_CAPACITY: {ordinal}:{slot_id}:"
                f"items={item_count}>{item_limit}"
            )


def _query_selection(
    query_bundle: Mapping[str, Any],
    *,
    ordinal: int,
    page_id: str,
    source_ordinal: int,
) -> tuple[int, float, str, str | None]:
    queries = query_bundle.get("queries")
    if not isinstance(queries, list):
        raise AutoBindingError("AUTO_BIND_QUERY_INVALID")
    matches = [
        item
        for item in queries
        if isinstance(item, Mapping) and item.get("target_ordinal") == ordinal
    ]
    if len(matches) != 1:
        raise AutoBindingError(f"AUTO_BIND_QUERY_ORDINAL_INVALID: {ordinal}")
    query = matches[0]
    result = query.get("result")
    if not isinstance(result, Mapping):
        raise AutoBindingError(f"AUTO_BIND_QUERY_INVALID: {ordinal}")
    required_source = result.get("required_source_ordinal")
    if required_source is not None and required_source != source_ordinal:
        raise AutoBindingError(
            f"AUTO_BIND_REQUIRED_SOURCE_ORDINAL_MISMATCH: {ordinal}"
        )
    candidates = result.get("candidates")
    if not isinstance(candidates, list):
        raise AutoBindingError(f"AUTO_BIND_QUERY_INVALID: {ordinal}")
    selected = [
        (rank, item)
        for rank, item in enumerate(candidates, start=1)
        if isinstance(item, Mapping) and item.get("page_id") == page_id
    ]
    if len(selected) != 1:
        raise AutoBindingError(
            f"AUTO_BIND_PAGE_NOT_CANDIDATE: {ordinal}:{page_id}"
        )
    rank, candidate = selected[0]
    if candidate.get("eligibility") is not True:
        raise AutoBindingError(
            f"AUTO_BIND_PAGE_INELIGIBLE: {ordinal}:{page_id}"
        )
    page = candidate.get("page_template")
    scores = candidate.get("scores")
    if (
        not isinstance(page, Mapping)
        or page.get("slide_number") != source_ordinal
        or not isinstance(scores, Mapping)
        or not isinstance(scores.get("total"), (int, float))
    ):
        raise AutoBindingError(f"AUTO_BIND_QUERY_INVALID: {ordinal}")
    query_id = query.get("query_id")
    if not isinstance(query_id, str) or not query_id:
        raise AutoBindingError(f"AUTO_BIND_QUERY_INVALID: {ordinal}")
    fallback = candidate.get("fallback_reason")
    if fallback is not None and not isinstance(fallback, str):
        raise AutoBindingError(f"AUTO_BIND_QUERY_INVALID: {ordinal}")
    return rank, float(scores["total"]), query_id, fallback


def compile_assembly_intent(
    intent: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    profile_sha256: str,
    library_index: LibraryIndex,
    library_index_sha256: str,
    query_bundle: Mapping[str, Any],
    query_bundle_sha256: str,
    query_bundle_path: str,
    fact_store: FactStore,
    connective_copy: Mapping[str, Any],
    authority_paths: Mapping[str, str],
    authority_sha256: Mapping[str, str],
    intent_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compile a bounded intent into a complete AssemblyPlan and audit report."""

    _validate_schema(
        intent,
        "assembly-intent.v1.schema.json",
        "AUTO_BIND_INTENT_SCHEMA_INVALID",
    )
    _validate_schema(
        profile,
        "binding-profile.v1.schema.json",
        "AUTO_BIND_PROFILE_SCHEMA_INVALID",
    )
    if profile["profile_id"] != intent["profile_id"]:
        raise AutoBindingError("AUTO_BIND_PROFILE_APPLICABILITY_MISMATCH")
    if profile["scenario_id"] != intent["scenario_id"]:
        raise AutoBindingError("AUTO_BIND_PROFILE_APPLICABILITY_MISMATCH")
    if profile["library_id"] != library_index.library_id:
        raise AutoBindingError("AUTO_BIND_LIBRARY_ID_MISMATCH")
    if (
        profile["library_index_sha256"] != library_index_sha256
        or query_bundle.get("library_index_sha256") != library_index_sha256
    ):
        raise AutoBindingError("AUTO_BIND_LIBRARY_FINGERPRINT_MISMATCH")
    if query_bundle.get("schema_version") != "page-template-query-bundle.v1":
        raise AutoBindingError("AUTO_BIND_QUERY_INVALID")
    if query_bundle.get("query_count") != len(query_bundle.get("queries", ())):
        raise AutoBindingError("AUTO_BIND_QUERY_INVALID")

    facts = {fact.id: fact for fact in fact_store.active_facts()}
    connectives = _connective_index(connective_copy)
    clear_id = str(profile["default_unassigned_connective_id"])
    if connectives.get(clear_id) != "":
        raise AutoBindingError(f"AUTO_BIND_CLEAR_CONNECTIVE_INVALID: {clear_id}")
    templates = {item.page_id: item for item in library_index.page_templates}
    profile_slides = {
        int(item["ordinal"]): item for item in profile["slides"]
    }
    intent_slides = {int(item["ordinal"]): item for item in intent["slides"]}
    if (
        len(profile_slides) != len(profile["slides"])
        or len(intent_slides) != len(intent["slides"])
        or set(profile_slides) != set(intent_slides)
    ):
        raise AutoBindingError("AUTO_BIND_ORDINAL_SET_MISMATCH")

    selected_page_ids: set[str] = set()
    target_slides: list[dict[str, Any]] = []
    slide_reports: list[dict[str, Any]] = []
    used_fact_ids: set[str] = set()
    total_fact_bindings = 0
    total_connective_bindings = 0
    total_fragment_slots = 0

    for ordinal in sorted(profile_slides):
        profile_slide = profile_slides[ordinal]
        intent_slide = intent_slides[ordinal]
        if (
            intent_slide["page_id"] != profile_slide["page_id"]
            or intent_slide["narrative_role"] != profile_slide["narrative_role"]
            or set(intent_slide["fact_ids"]) != set(profile_slide["fact_ids"])
        ):
            raise AutoBindingError(
                f"AUTO_BIND_PROFILE_APPLICABILITY_MISMATCH: {ordinal}"
            )
        page_id = str(intent_slide["page_id"])
        if page_id in selected_page_ids:
            raise AutoBindingError(f"AUTO_BIND_DUPLICATE_PAGE_ID: {page_id}")
        selected_page_ids.add(page_id)
        template = templates.get(page_id)
        if template is None:
            raise AutoBindingError(f"AUTO_BIND_PAGE_UNKNOWN: {page_id}")
        query_spec = profile_slide["query"]
        if (
            template.page_role != query_spec["role"]
            or template.slide_number != query_spec["required_source_ordinal"]
        ):
            raise AutoBindingError(f"AUTO_BIND_ROLE_MISMATCH: {ordinal}")
        rank, score_total, query_id, fallback_reason = _query_selection(
            query_bundle,
            ordinal=ordinal,
            page_id=page_id,
            source_ordinal=int(query_spec["required_source_ordinal"]),
        )

        allowed_fact_ids = set(intent_slide["fact_ids"])
        unknown = sorted(allowed_fact_ids - set(facts))
        if unknown:
            raise AutoBindingError(
                "AUTO_BIND_FACT_UNKNOWN: " + ",".join(unknown)
            )
        slots = _slot_index(template)
        groups = _fragment_groups(template)
        bindings: dict[str, dict[str, Any]] = {}
        fact_binding_count = 0
        connective_binding_count = 0
        fragment_slot_ids: set[str] = set()

        for fragment in profile_slide["fragment_bindings"]:
            fact_id, rendering = _resolve_rendering(
                fragment,
                facts=facts,
                allowed_fact_ids=allowed_fact_ids,
            )
            target_kind = fragment["target_kind"]
            target_id = fragment["target_id"]
            if target_kind == "group":
                ordered = groups.get(target_id)
                if ordered is None:
                    raise AutoBindingError(
                        f"AUTO_BIND_FRAGMENT_GROUP_UNKNOWN: {ordinal}:{target_id}"
                    )
                if len(rendering) > len(ordered):
                    raise AutoBindingError(
                        f"AUTO_BIND_FRAGMENT_RENDERING_TOO_LONG: {ordinal}:{target_id}"
                    )
                for index, slot_id in enumerate(ordered):
                    if slot_id in bindings:
                        raise AutoBindingError(
                            f"AUTO_BIND_FRAGMENT_SLOT_DUPLICATE: {ordinal}:{slot_id}"
                        )
                    if index < len(rendering):
                        bindings[slot_id] = {
                            "text": rendering[index],
                            "fact_refs": [fact_id],
                            "asset_refs": [],
                            "fit_policy": "preserve",
                        }
                        fact_binding_count += 1
                        used_fact_ids.add(fact_id)
                    else:
                        bindings[slot_id] = {
                            "text": connectives[clear_id],
                            "fact_refs": [],
                            "asset_refs": [],
                            "fit_policy": "preserve",
                        }
                        connective_binding_count += 1
                    fragment_slot_ids.add(slot_id)
            else:
                slot_id = target_id
                if slot_id not in slots or len(rendering) != 1 or slot_id in bindings:
                    raise AutoBindingError(
                        f"AUTO_BIND_FRAGMENT_STANDALONE_INVALID: {ordinal}:{slot_id}"
                    )
                bindings[slot_id] = {
                    "text": rendering,
                    "fact_refs": [fact_id],
                    "asset_refs": [],
                    "fit_policy": "preserve",
                }
                fact_binding_count += 1
                used_fact_ids.add(fact_id)
                fragment_slot_ids.add(slot_id)

        for slot_id, rule in profile_slide["bindings"].items():
            if slot_id not in slots:
                raise AutoBindingError(
                    f"AUTO_BIND_SLOT_UNKNOWN: {ordinal}:{slot_id}"
                )
            if slot_id in bindings:
                raise AutoBindingError(
                    f"AUTO_BIND_SLOT_DUPLICATE: {ordinal}:{slot_id}"
                )
            binding, binding_kind = _resolve_rule(
                rule,
                facts=facts,
                allowed_fact_ids=allowed_fact_ids,
                connectives=connectives,
            )
            bindings[slot_id] = binding
            if binding_kind == "fact":
                fact_binding_count += 1
                used_fact_ids.update(binding["fact_refs"])
            else:
                connective_binding_count += 1

        for slot_id in sorted(slots, key=lambda value: int(value.split("_", 1)[1])):
            if slot_id not in bindings:
                bindings[slot_id] = {
                    "text": connectives[clear_id],
                    "fact_refs": [],
                    "asset_refs": [],
                    "fit_policy": "preserve",
                }
                connective_binding_count += 1
            _validate_capacity(
                ordinal=ordinal,
                slot_id=slot_id,
                slot=slots[slot_id],
                text=str(bindings[slot_id]["text"]),
            )

        title_binding, _ = _resolve_rule(
            profile_slide["title_binding"],
            facts=facts,
            allowed_fact_ids=allowed_fact_ids,
            connectives=connectives,
        )
        used_fact_ids.update(title_binding["fact_refs"])
        headline = ""
        if "headline_binding" in profile_slide:
            headline_binding, _ = _resolve_rule(
                profile_slide["headline_binding"],
                facts=facts,
                allowed_fact_ids=allowed_fact_ids,
                connectives=connectives,
            )
            headline = str(headline_binding["text"])
            used_fact_ids.update(headline_binding["fact_refs"])

        target_slides.append(
            {
                "ordinal": ordinal,
                "narrative_role": profile_slide["narrative_role"],
                "page_id": page_id,
                "package_sha256": template.package_sha256,
                "slide_number": template.slide_number,
                "title": str(title_binding["text"]),
                "headline": headline,
                "bindings": bindings,
                "selection": {
                    "query_id": query_id,
                    "candidate_rank": rank,
                    "score_total": score_total,
                    "selection_reason": (
                        "Hash-locked profile selected the exact certified "
                        "source ordinal after deterministic hard filtering."
                    ),
                    "fallback_reason": fallback_reason,
                },
            }
        )
        slide_reports.append(
            {
                "ordinal": ordinal,
                "page_id": page_id,
                "candidate_rank": rank,
                "ordinary_slot_count": len(bindings),
                "fact_binding_count": fact_binding_count,
                "connective_binding_count": connective_binding_count,
                "fragment_slot_count": len(fragment_slot_ids),
                "status": "pass",
            }
        )
        total_fact_bindings += fact_binding_count
        total_connective_bindings += connective_binding_count
        total_fragment_slots += len(fragment_slot_ids)

    required_fact_ids = {fact.id for fact in facts.values() if fact.required}
    unscoped_required = sorted(required_fact_ids - {
        fact_id
        for slide in intent["slides"]
        for fact_id in slide["fact_ids"]
    })
    if unscoped_required:
        raise AutoBindingError(
            "AUTO_BIND_REQUIRED_FACT_UNSCOPED: " + ",".join(unscoped_required)
        )
    # Governed chart/table/workbook facts are intentionally authorized later
    # by the assembler.  They must be in an intent scope, but need not appear
    # in an ordinary text binding here.

    expected_authorities = {"fact_store", "asset_manifest", "connective_copy"}
    if set(authority_paths) != expected_authorities or set(authority_sha256) != expected_authorities:
        raise AutoBindingError("AUTO_BIND_AUTHORITY_INVALID")
    for key in expected_authorities:
        if (
            not isinstance(authority_paths[key], str)
            or not authority_paths[key]
            or not isinstance(authority_sha256[key], str)
            or len(authority_sha256[key]) != 64
        ):
            raise AutoBindingError(f"AUTO_BIND_AUTHORITY_INVALID: {key}")

    plan = {
        "schema_version": "1.0",
        "plan_id": f"{profile['profile_id']}-compiled",
        "scenario_id": profile["scenario_id"],
        "dominant_style_cluster_id": profile["dominant_style_cluster_id"],
        "created_at": profile["created_at"],
        "target_slide_count": len(target_slides),
        "target_slides": target_slides,
        "library_index_sha256": library_index_sha256,
        "query_bundle": {
            "path": query_bundle_path,
            "sha256": query_bundle_sha256,
        },
        "authority": {
            key: {"path": authority_paths[key], "sha256": authority_sha256[key]}
            for key in ("fact_store", "asset_manifest", "connective_copy")
        },
    }
    _validate_schema(
        plan,
        "assembly-plan.v1.schema.json",
        "AUTO_BIND_PLAN_SCHEMA_INVALID",
    )
    plan_bytes = _canonical_bytes(plan)
    resolved_intent_sha = intent_sha256 or _sha256_bytes(_canonical_bytes(intent))
    report = {
        "schema_version": "1.0",
        "status": "pass",
        "profile_id": profile["profile_id"],
        "profile_sha256": profile_sha256,
        "library_index_sha256": library_index_sha256,
        "query_bundle_sha256": query_bundle_sha256,
        "intent_sha256": resolved_intent_sha,
        "slide_count": len(target_slides),
        "ordinary_slot_count": sum(item["ordinary_slot_count"] for item in slide_reports),
        "fact_binding_count": total_fact_bindings,
        "connective_binding_count": total_connective_bindings,
        "fragment_slot_count": total_fragment_slots,
        "governed_policy": profile["governed_policy"],
        "plan_sha256": _sha256_bytes(plan_bytes),
        "slides": slide_reports,
    }
    _validate_schema(
        report,
        "auto-binding-report.v1.schema.json",
        "AUTO_BIND_REPORT_SCHEMA_INVALID",
    )
    return plan, report


def atomic_write_json(path: str | os.PathLike[str], payload: Mapping[str, Any]) -> str:
    """Write canonical JSON atomically and return its SHA-256."""

    output = Path(path).expanduser().resolve(strict=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = _canonical_bytes(payload)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return _sha256_bytes(data)


__all__ = [
    "AutoBindingError",
    "atomic_write_json",
    "build_default_intent",
    "build_profile_query_bundle",
    "compile_assembly_intent",
    "load_assembly_intent",
    "load_binding_profile",
]
