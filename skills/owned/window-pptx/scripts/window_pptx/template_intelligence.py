"""Certified template retrieval and bounded slide-blueprint planning."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .template_pack_v2 import TemplatePackV2, load_template_pack_v2


SKILL_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = SKILL_ROOT / "registries" / "template-intelligence-v3.json"
LAYOUTS_PATH = SKILL_ROOT / "registries" / "layouts.json"
FORBIDDEN_MODEL_FIELDS = frozenset({
    "x", "y", "width", "height", "coordinates", "shape_id", "shape_ids",
    "ooxml", "xml", "html", "code", "font", "font_face", "font_size",
    "color", "palette", "repair", "repair_instructions",
})


class TemplateIntelligenceError(ValueError):
    """A registry, selection, or blueprint violates the governed boundary."""


@dataclass(frozen=True)
class CandidateCapacity:
    max_items: int
    max_text_chars: int


@dataclass(frozen=True)
class PageCandidate:
    id: str
    family: str
    roles: tuple[str, ...]
    semantic_kinds: tuple[str, ...]
    required_assets: tuple[str, ...]
    capacity: CandidateCapacity
    source_mode: str
    materializer: str
    certification: str
    deck_family_ids: tuple[str, ...]
    style_cluster_ids: tuple[str, ...]
    physical_slide: int | None = None
    base_variant_id: str | None = None
    specialty: bool = False


@dataclass(frozen=True)
class VisualSpine:
    id: str
    source_mode: str
    deck_family_id: str
    style_cluster_id: str
    theme_id: str
    art_direction_id: str
    scenarios: tuple[str, ...]
    required_roles: tuple[str, ...]
    materializer: str
    pack: TemplatePackV2


@dataclass(frozen=True)
class RegistryV3:
    id: str
    candidates: Mapping[str, PageCandidate]
    spines: Mapping[str, VisualSpine]
    source_digests: Mapping[str, str]


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class SlideSelection:
    slide_id: str
    candidate_id: str
    fact_refs: tuple[str, ...]
    asset_refs: tuple[str, ...]
    importance: str
    confidence: float
    fallback_reason: str | None
    rationale_codes: tuple[str, ...]


@dataclass(frozen=True)
class TemplateSelectionPlan:
    schema_version: str
    brief_id: str
    spine_id: str
    selections: tuple[SlideSelection, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "brief_id": self.brief_id,
            "spine_id": self.spine_id,
            "selections": [
                {
                    "slide_id": item.slide_id,
                    "candidate_id": item.candidate_id,
                    "fact_refs": list(item.fact_refs),
                    "asset_refs": list(item.asset_refs),
                    "importance": item.importance,
                    "confidence": item.confidence,
                    "fallback_reason": item.fallback_reason,
                    "rationale_codes": list(item.rationale_codes),
                }
                for item in self.selections
            ],
        }


@dataclass(frozen=True)
class SlideBlueprint:
    schema_version: str
    slide_id: str
    spine_id: str
    candidate_id: str
    family: str
    materializer: str
    fact_refs: tuple[str, ...]
    asset_refs: tuple[str, ...]
    token_profile_id: str
    physical_slide: int | None
    base_variant_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "slide_id": self.slide_id,
            "spine_id": self.spine_id,
            "candidate_id": self.candidate_id,
            "family": self.family,
            "materializer": self.materializer,
            "fact_refs": list(self.fact_refs),
            "asset_refs": list(self.asset_refs),
            "token_profile_id": self.token_profile_id,
            "physical_slide": self.physical_slide,
            "base_variant_id": self.base_variant_id,
        }


_FAMILY_CAPACITY: dict[str, tuple[int, int]] = {
    "cover": (2, 120), "agenda": (6, 360), "section": (2, 160),
    "executive-summary": (6, 720), "focal-statement": (1, 220),
    "big-number": (5, 400), "text-media": (4, 620), "cards": (6, 720),
    "timeline": (6, 660), "process": (8, 720), "comparison": (6, 720),
    "matrix": (9, 780), "quadrant": (9, 680), "funnel": (7, 620),
    "roadmap": (7, 720), "data-chart": (10, 520), "table": (12, 920),
    "product-showcase": (4, 520), "case-study": (6, 720), "team": (6, 520),
    "risk-recommendation": (6, 760), "recommendation": (6, 720),
    "summary": (6, 680), "cta": (3, 220), "image-story": (4, 520),
}
_ROLE_FAMILIES = {
    "cover": ("cover",),
    "directory": ("agenda",),
    "agenda": ("agenda",),
    "section": ("section",),
    "chapter": ("section",),
    "decision": ("recommendation", "roadmap", "risk-recommendation", "summary"),
    "conclusion": ("summary", "focal-statement", "recommendation"),
    "closing": ("cta",),
    "appendix": ("table", "data-chart", "text-media"),
    "body": (),
}
_SEMANTIC_FAMILIES = {
    "map": ("text-media",), "regional-footprint": ("text-media",),
    "awards": ("case-study",), "honors": ("case-study",),
    "people-profile": ("team",), "team": ("team",),
    "partners": ("cards",), "logo-wall": ("cards",),
    "business-model": ("matrix",), "value-chain": ("matrix",),
    "architecture": ("process",), "system-flow": ("process",),
    "mockup": ("product-showcase",), "product-demo": ("product-showcase",),
    "quote": ("focal-statement",), "key-message": ("focal-statement",),
    "six-content": ("cards",), "multi-content": ("cards",),
    "timeline": ("timeline",), "process": ("process",),
    "comparison": ("comparison",), "matrix": ("matrix",),
    "quadrant": ("quadrant",), "funnel": ("funnel",),
    "roadmap": ("roadmap",), "chart": ("data-chart",),
    "trend": ("data-chart",), "composition": ("data-chart",),
    "table": ("table",), "case-study": ("case-study",),
    "risk": ("risk-recommendation",), "recommendation": ("recommendation",),
    "kpi": ("big-number",), "image-story": ("image-story",),
    "metrics": ("big-number",), "statement": ("focal-statement",),
    "bullets": ("cards",), "sequence": ("process",),
    "image": ("text-media", "image-story"), "generic": ("cards",),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TemplateIntelligenceError(f"{path} must be a non-empty string")
    return value.strip()


def _strings(value: Any, path: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TemplateIntelligenceError(f"{path} must be an array")
    result = tuple(_text(item, f"{path}[{index}]") for index, item in enumerate(value))
    if len(result) != len(set(result)):
        raise TemplateIntelligenceError(f"{path} contains duplicates")
    return result


def _load_raw(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplateIntelligenceError(f"cannot load {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise TemplateIntelligenceError(f"{path} root must be an object")
    return raw


def _roles_for_family(family: str) -> tuple[str, ...]:
    roles = [
        role for role, families in _ROLE_FAMILIES.items() if family in families
    ]
    if family not in {"cover", "agenda", "section", "cta"}:
        roles.append("body")
    return tuple(dict.fromkeys(roles)) or ("body",)


def _semantics_for_family(family: str) -> tuple[str, ...]:
    values = tuple(kind for kind, families in _SEMANTIC_FAMILIES.items() if family in families)
    return values or (family, "structured-content")


def _registered_candidate(
    candidate_id: str,
    family: str,
    variant_id: str,
    *,
    specialty: bool = False,
    semantic_kinds: Sequence[str] | None = None,
    required_assets: Sequence[str] = (),
    max_items: int | None = None,
) -> PageCandidate:
    capacity = _FAMILY_CAPACITY[family]
    return PageCandidate(
        id=candidate_id,
        family=family,
        roles=_roles_for_family(family),
        semantic_kinds=tuple(semantic_kinds or _semantics_for_family(family)),
        required_assets=tuple(required_assets),
        capacity=CandidateCapacity(max_items or capacity[0], capacity[1]),
        source_mode="registered_composition",
        materializer="registered_native_renderer",
        certification="certified",
        deck_family_ids=(
            "institutional-annual-editorial",
            "campus-innovation-pitch",
            "academic-defense-editorial",
        ),
        style_cluster_ids=(
            "ivory-green-gold-editorial",
            "optimistic-technical-stage",
            "research-editorial-evidence",
        ),
        base_variant_id=variant_id,
        specialty=specialty,
    )


def _derive_candidates(raw: Mapping[str, Any], spines: Mapping[str, VisualSpine]) -> dict[str, PageCandidate]:
    layouts = _load_raw(LAYOUTS_PATH)
    families = layouts.get("families")
    if not isinstance(families, list) or len(families) != 25:
        raise TemplateIntelligenceError("layout registry must expose the governed 25 families")
    candidates: list[PageCandidate] = []
    recipes = {
        recipe["id"]: recipe
        for recipe in layouts.get("recipes", [])
        if isinstance(recipe, dict) and isinstance(recipe.get("id"), str)
    }

    physical = spines["institutional-work-summary"].pack
    for page in physical.pages:
        capacity = _FAMILY_CAPACITY[page.family]
        candidates.append(PageCandidate(
            id=page.id,
            family=page.family,
            roles=(page.role,),
            semantic_kinds=_semantics_for_family(page.family),
            required_assets=(),
            capacity=CandidateCapacity(*capacity),
            source_mode="physical_ooxml",
            materializer="template_pack_v1_adapter",
            certification="certified",
            deck_family_ids=(physical.deck_family_id,),
            style_cluster_ids=(physical.style_cluster_id,),
            physical_slide=page.slide,
        ))

    ordered_families = sorted(families, key=lambda item: item["id"])
    supplement_remaining = raw["derivation"]["supplement_variants"]
    for family_entry in ordered_families:
        family = _text(family_entry.get("id"), "layouts.family.id")
        if family not in _FAMILY_CAPACITY:
            raise TemplateIntelligenceError(f"no certified capacity for family {family}")
        variants = family_entry.get("variants")
        if not isinstance(variants, list) or len(variants) < 2:
            raise TemplateIntelligenceError(f"family {family} needs at least two variants")
        chosen = list(variants[:2])
        if supplement_remaining and len(variants) >= 3:
            if family == "cover":
                assetless_cover = next(
                    (
                        variant
                        for variant in variants
                        if variant.get("id") == "cover.editorial"
                    ),
                    variants[2],
                )
                chosen.append(assetless_cover)
            else:
                chosen.append(variants[2])
            supplement_remaining -= 1
        for variant in chosen:
            variant_id = _text(variant.get("id"), f"{family}.variant.id")
            recipe = recipes.get(variant.get("recipe"))
            overrides = variant.get("components", {})
            required_assets: tuple[str, ...] = ()
            if isinstance(recipe, dict):
                effective_components = [
                    (
                        overrides.get(slot.get("id"), slot.get("component"))
                        if isinstance(overrides, dict)
                        else slot.get("component")
                    )
                    for slot in recipe.get("slots", [])
                    if isinstance(slot, dict)
                ]
                if "image-frame" in effective_components:
                    required_assets = ("image",)
            candidates.append(_registered_candidate(
                f"layout.{variant_id}",
                family,
                variant_id,
                required_assets=required_assets,
            ))
    if supplement_remaining:
        raise TemplateIntelligenceError("not enough third variants for supplements")

    aliases = raw.get("specialty_aliases")
    if not isinstance(aliases, list) or len(aliases) != 9:
        raise TemplateIntelligenceError("registry requires exactly nine specialty aliases")
    for index, alias in enumerate(aliases):
        if not isinstance(alias, dict) or set(alias) != {
            "id", "family", "semantic_kinds", "required_assets", "max_items"
        }:
            raise TemplateIntelligenceError(f"specialty_aliases[{index}] fields are invalid")
        family = _text(alias["family"], f"specialty_aliases[{index}].family")
        candidates.append(_registered_candidate(
            _text(alias["id"], f"specialty_aliases[{index}].id"),
            family,
            f"{family}.specialty",
            specialty=True,
            semantic_kinds=_strings(alias["semantic_kinds"], "semantic_kinds"),
            required_assets=_strings(alias["required_assets"], "required_assets"),
            max_items=alias["max_items"],
        ))

    by_id = {candidate.id: candidate for candidate in candidates}
    expected = raw.get("candidate_count")
    if len(candidates) != expected or len(by_id) != expected:
        raise TemplateIntelligenceError(
            f"candidate derivation expected {expected}, observed {len(candidates)}"
        )
    return by_id


def load_registry_v3(path: Path | str | None = None) -> RegistryV3:
    """Load the digest-bound 84-candidate certified pilot."""

    registry_path = Path(path) if path is not None else REGISTRY_PATH
    raw = _load_raw(registry_path)
    if set(raw) != {
        "schema_version", "registry_id", "candidate_count", "source_digests",
        "derivation", "specialty_aliases", "spines",
    } or raw["schema_version"] != "3.0":
        raise TemplateIntelligenceError("Registry v3 root contract is invalid")
    source_digests = raw["source_digests"]
    expected_names = {
        "layouts.json", "components.json", "themes.json",
        "design-packs.json", "art-directions.json",
    }
    if not isinstance(source_digests, dict) or set(source_digests) != expected_names:
        raise TemplateIntelligenceError("Registry v3 source digests are incomplete")
    for name, expected in source_digests.items():
        observed = f"sha256:{_sha256(SKILL_ROOT / 'registries' / name)}"
        if observed != expected:
            raise TemplateIntelligenceError(
                f"Registry v3 source drift for {name}: {observed}"
            )

    raw_spines = raw["spines"]
    if not isinstance(raw_spines, list) or len(raw_spines) != 3:
        raise TemplateIntelligenceError("Registry v3 requires exactly three spines")
    spines: dict[str, VisualSpine] = {}
    fields = {
        "id", "source_mode", "deck_family_id", "style_cluster_id", "theme_id",
        "art_direction_id", "manifest", "scenarios", "required_roles",
        "materializer",
    }
    for index, entry in enumerate(raw_spines):
        if not isinstance(entry, dict) or set(entry) != fields:
            raise TemplateIntelligenceError(f"spines[{index}] fields are invalid")
        pack = load_template_pack_v2(SKILL_ROOT / _text(entry["manifest"], "manifest"))
        spine_id = _text(entry["id"], "spine.id")
        if (
            pack.source_mode != entry["source_mode"]
            or pack.deck_family_id != entry["deck_family_id"]
            or pack.style_cluster_id != entry["style_cluster_id"]
            or pack.materializer != entry["materializer"]
        ):
            raise TemplateIntelligenceError(f"spine {spine_id} does not match its pack")
        if spine_id in spines:
            raise TemplateIntelligenceError(f"duplicate spine {spine_id}")
        spines[spine_id] = VisualSpine(
            id=spine_id,
            source_mode=pack.source_mode,
            deck_family_id=pack.deck_family_id,
            style_cluster_id=pack.style_cluster_id,
            theme_id=_text(entry["theme_id"], "spine.theme_id"),
            art_direction_id=_text(entry["art_direction_id"], "spine.art_direction_id"),
            scenarios=_strings(entry["scenarios"], "spine.scenarios"),
            required_roles=_strings(entry["required_roles"], "spine.required_roles"),
            materializer=pack.materializer,
            pack=pack,
        )
    candidates = _derive_candidates(raw, spines)
    return RegistryV3(
        id=_text(raw["registry_id"], "registry_id"),
        candidates=candidates,
        spines=spines,
        source_digests=dict(source_digests),
    )


def choose_spine(scenario: str, registry: RegistryV3 | None = None) -> VisualSpine:
    available = registry or load_registry_v3()
    normalized = _text(scenario, "scenario").casefold()
    matches = [
        spine for spine in available.spines.values()
        if normalized in {item.casefold() for item in spine.scenarios}
    ]
    if not matches:
        raise TemplateIntelligenceError(f"NO_FIT: no certified spine for {scenario}")
    return sorted(matches, key=lambda item: item.id)[0]


def retrieve_candidates(
    slide: Mapping[str, Any],
    spine: VisualSpine,
    registry: RegistryV3,
    *,
    limit: int = 6,
) -> tuple[CandidateScore, ...]:
    """Hard-filter, rank, and diversify candidates without freeform design."""

    role = _text(slide.get("role"), "slide.role")
    semantic = _text(slide.get("semantic_kind", "structured-content"), "semantic_kind")
    item_count = slide.get("item_count", 1)
    text_chars = slide.get("text_chars", 0)
    title_chars = slide.get("title_chars", 0)
    decision_three_ready = slide.get("decision_three_ready", False)
    if type(item_count) is not int or item_count < 0:
        raise TemplateIntelligenceError("slide.item_count must be a non-negative integer")
    if type(text_chars) is not int or text_chars < 0:
        raise TemplateIntelligenceError("slide.text_chars must be a non-negative integer")
    if type(title_chars) is not int or title_chars < 0:
        raise TemplateIntelligenceError("slide.title_chars must be a non-negative integer")
    if not isinstance(decision_three_ready, bool):
        raise TemplateIntelligenceError("slide.decision_three_ready must be boolean")
    asset_kinds = set(_strings(slide.get("asset_kinds", []), "slide.asset_kinds"))
    preferred = _ROLE_FAMILIES.get(role, ())
    semantic_families = _SEMANTIC_FAMILIES.get(semantic, ())
    ranked: list[tuple[float, str, CandidateScore, PageCandidate]] = []
    for candidate in registry.candidates.values():
        if candidate.certification != "certified":
            continue
        if (
            candidate.source_mode != spine.source_mode
            or candidate.materializer != spine.materializer
        ):
            continue
        if spine.deck_family_id not in candidate.deck_family_ids:
            continue
        if spine.style_cluster_id not in candidate.style_cluster_ids:
            continue
        if role == "body" and "body" not in candidate.roles:
            continue
        if role == "appendix" and not (
            "appendix" in candidate.roles or "body" in candidate.roles
        ):
            continue
        if role not in {"body", "appendix"} and role not in candidate.roles:
            continue
        if item_count > candidate.capacity.max_items or text_chars > candidate.capacity.max_text_chars:
            continue
        if set(candidate.required_assets) - asset_kinds:
            continue
        if (
            candidate.base_variant_id == "cta.centered"
            and title_chars > 8
        ):
            # The centered CTA has an intentionally compact eyebrow/title
            # lane. Route ordinary action titles to the top-band candidate
            # before materialization instead of allowing a render-time layout
            # substitution that would invalidate exact candidate evidence.
            continue
        if (
            candidate.base_variant_id == "cta.decision-three"
            and not decision_three_ready
        ):
            continue
        score = 0.25
        reasons = ["CERTIFIED", "CAPACITY_OK", "MATERIALIZER_OK", "FAMILY_OK"]
        if candidate.family in preferred:
            score += 0.30
            reasons.append("ROLE_FIT")
        elif preferred:
            continue
        if candidate.family in semantic_families or semantic in candidate.semantic_kinds:
            score += 0.30
            reasons.append("SEMANTIC_FIT")
        elif semantic_families:
            score += 0.04
        headroom = 1 - max(
            item_count / max(candidate.capacity.max_items, 1),
            text_chars / max(candidate.capacity.max_text_chars, 1),
        )
        score += max(0, headroom) * 0.10
        if candidate.specialty and semantic in candidate.semantic_kinds:
            score += 0.12
            reasons.append("SPECIALTY_FIT")
        ranked.append((
            -round(min(score, 1.0), 4),
            candidate.id,
            CandidateScore(candidate.id, round(min(score, 1.0), 4), tuple(reasons)),
            candidate,
        ))
    if not ranked:
        return ()
    ordered = sorted(ranked)
    return tuple(item[2] for item in ordered[:limit])


def _validate_brief(brief: Mapping[str, Any]) -> tuple[str, str, list[Mapping[str, Any]]]:
    if brief.get("status") != "Locked":
        raise TemplateIntelligenceError("formal selection requires status=Locked")
    if brief.get("discussion_status") not in {None, "complete", "Complete"}:
        raise TemplateIntelligenceError("formal selection requires complete discussion")
    brief_id = _text(brief.get("brief_id") or brief.get("id"), "brief_id")
    scenario = _text(brief.get("scenario"), "scenario")
    slides = brief.get("slides")
    if not isinstance(slides, list) or len(slides) < 6:
        raise TemplateIntelligenceError("locked brief requires at least six slides")
    ids = [_text(slide.get("slide_id"), "slide.slide_id") for slide in slides]
    if len(ids) != len(set(ids)):
        raise TemplateIntelligenceError("slide IDs must be unique")
    roles = [slide.get("role") for slide in slides]
    for required in ("cover", "agenda", "section", "closing"):
        aliases = {"agenda": {"agenda", "directory"}}.get(required, {required})
        if not any(role in aliases for role in roles):
            raise TemplateIntelligenceError(f"deck anatomy is missing {required}")
    return brief_id, scenario, slides


def validate_model_choices(
    choices: Sequence[Mapping[str, Any]],
    brief: Mapping[str, Any],
    spine: VisualSpine,
    registry: RegistryV3,
) -> tuple[SlideSelection, ...]:
    _, _, slides = _validate_brief(brief)
    if len(choices) != len(slides):
        raise TemplateIntelligenceError("model choices must contain one item per slide")
    allowed = {
        "slide_id", "candidate_id", "fact_refs", "asset_refs", "importance",
        "confidence", "fallback_reason", "rationale_codes",
    }
    slide_by_id = {slide["slide_id"]: slide for slide in slides}
    result: list[SlideSelection] = []
    for index, raw_choice in enumerate(choices):
        if not isinstance(raw_choice, Mapping):
            raise TemplateIntelligenceError(f"choices[{index}] must be an object")
        forbidden = sorted(set(raw_choice) & FORBIDDEN_MODEL_FIELDS)
        unknown = sorted(set(raw_choice) - allowed)
        missing = sorted(allowed - set(raw_choice))
        if forbidden or unknown or missing:
            raise TemplateIntelligenceError(
                f"choices[{index}] fields invalid; forbidden={forbidden}, "
                f"unknown={unknown}, missing={missing}"
            )
        slide_id = _text(raw_choice["slide_id"], "choice.slide_id")
        slide = slide_by_id.get(slide_id)
        if slide is None:
            raise TemplateIntelligenceError(f"unknown slide_id {slide_id}")
        candidate_id = _text(raw_choice["candidate_id"], "choice.candidate_id")
        candidate = registry.candidates.get(candidate_id)
        if candidate is None or candidate.certification != "certified":
            raise TemplateIntelligenceError(f"unknown or uncertified candidate {candidate_id}")
        eligible = {
            item.candidate_id
            for item in retrieve_candidates(slide, spine, registry, limit=84)
        }
        if candidate_id not in eligible:
            raise TemplateIntelligenceError(f"candidate {candidate_id} is not eligible")
        fact_refs = _strings(raw_choice["fact_refs"], "choice.fact_refs")
        asset_refs = _strings(raw_choice["asset_refs"], "choice.asset_refs")
        declared_facts = set(_strings(slide.get("fact_refs", []), "slide.fact_refs"))
        declared_assets = set(_strings(slide.get("asset_refs", []), "slide.asset_refs"))
        if not set(fact_refs) <= declared_facts:
            raise TemplateIntelligenceError("choice contains an unbound fact reference")
        if not set(asset_refs) <= declared_assets:
            raise TemplateIntelligenceError("choice contains an unbound asset reference")
        confidence = raw_choice["confidence"]
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            raise TemplateIntelligenceError("choice confidence must be 0..1")
        fallback = raw_choice["fallback_reason"]
        if fallback is not None and fallback not in {
            "LOW_CONFIDENCE_SAFE_DEFAULT", "SAME_FAMILY_CAPACITY_FALLBACK"
        }:
            raise TemplateIntelligenceError("choice fallback_reason is not governed")
        result.append(SlideSelection(
            slide_id=slide_id,
            candidate_id=candidate_id,
            fact_refs=fact_refs,
            asset_refs=asset_refs,
            importance=_text(raw_choice["importance"], "choice.importance"),
            confidence=float(confidence),
            fallback_reason=fallback,
            rationale_codes=_strings(raw_choice["rationale_codes"], "rationale_codes"),
        ))
    return tuple(result)


def build_selection_plan(
    brief: Mapping[str, Any],
    *,
    choices: Sequence[Mapping[str, Any]] | None = None,
    registry: RegistryV3 | None = None,
) -> TemplateSelectionPlan:
    """Create a deterministic plan or validate one bounded model decision."""

    available = registry or load_registry_v3()
    brief_id, scenario, slides = _validate_brief(brief)
    spine = choose_spine(scenario, available)
    if choices is None:
        generated: list[dict[str, Any]] = []
        candidate_run: list[str] = []
        for slide in slides:
            candidates = retrieve_candidates(slide, spine, available)
            if not candidates:
                raise TemplateIntelligenceError(
                    f"NO_FIT: no candidate for slide {slide['slide_id']}"
                )
            chosen = candidates[0]
            if len(candidate_run) >= 2:
                previous = candidate_run[-1]
                preferred_family = available.candidates[chosen.candidate_id].family
                alternate = next(
                    (
                        score for score in candidates
                        if score.candidate_id != previous
                        and available.candidates[score.candidate_id].family
                        == preferred_family
                    ),
                    None,
                )
                if alternate is not None:
                    chosen = alternate
            candidate_run = [*candidate_run[-1:], chosen.candidate_id]
            confidence = chosen.score
            fallback = None
            if confidence < 0.65:
                fallback = "LOW_CONFIDENCE_SAFE_DEFAULT"
            generated.append({
                "slide_id": slide["slide_id"],
                "candidate_id": chosen.candidate_id,
                "fact_refs": list(slide.get("fact_refs", [])),
                "asset_refs": list(slide.get("asset_refs", [])),
                "importance": slide.get("importance", "standard"),
                "confidence": confidence,
                "fallback_reason": fallback,
                "rationale_codes": list(chosen.reasons),
            })
        choices = generated
    selections = validate_model_choices(choices, brief, spine, available)
    _validate_rhythm(selections, slides, spine, available)
    return TemplateSelectionPlan("1.0", brief_id, spine.id, selections)


def _validate_rhythm(
    selections: Sequence[SlideSelection],
    slides: Sequence[Mapping[str, Any]],
    spine: VisualSpine,
    registry: RegistryV3,
) -> None:
    run_candidate: str | None = None
    run = 0
    for selection, slide in zip(selections, slides):
        role = slide["role"]
        if role in {"section", "chapter"}:
            run_candidate, run = None, 0
            continue
        if role not in {"body", "appendix"}:
            run_candidate, run = None, 0
            continue
        run = run + 1 if selection.candidate_id == run_candidate else 1
        run_candidate = selection.candidate_id
        if run > spine.pack.art_direction.max_same_family_run:
            raise TemplateIntelligenceError(
                f"rhythm violation: {selection.candidate_id} repeats "
                f"{run} ordinary pages"
            )


def compile_slide_blueprints(
    plan: TemplateSelectionPlan,
    registry: RegistryV3 | None = None,
) -> tuple[SlideBlueprint, ...]:
    available = registry or load_registry_v3()
    spine = available.spines.get(plan.spine_id)
    if spine is None:
        raise TemplateIntelligenceError(f"unknown spine {plan.spine_id}")
    result: list[SlideBlueprint] = []
    for selection in plan.selections:
        candidate = available.candidates.get(selection.candidate_id)
        if candidate is None or candidate.materializer not in {
            "template_pack_v1_adapter", "registered_native_renderer"
        }:
            raise TemplateIntelligenceError("blueprint candidate has no executable materializer")
        result.append(SlideBlueprint(
            "1.0",
            selection.slide_id,
            spine.id,
            candidate.id,
            candidate.family,
            candidate.materializer,
            selection.fact_refs,
            selection.asset_refs,
            spine.art_direction_id,
            candidate.physical_slide,
            candidate.base_variant_id,
        ))
    return tuple(result)


def validate_blueprint_payload(payload: Mapping[str, Any]) -> None:
    forbidden = sorted(set(payload) & FORBIDDEN_MODEL_FIELDS)
    allowed = {
        "schema_version", "slide_id", "spine_id", "candidate_id", "family",
        "materializer", "fact_refs", "asset_refs", "token_profile_id",
        "physical_slide", "base_variant_id",
    }
    unknown = sorted(set(payload) - allowed)
    if forbidden or unknown:
        raise TemplateIntelligenceError(
            f"blueprint fields invalid; forbidden={forbidden}, unknown={unknown}"
        )


def selection_plan_from_payload(payload: Mapping[str, Any]) -> TemplateSelectionPlan:
    """Load a serialized owned plan without reopening model design authority."""

    if set(payload) != {"schema_version", "brief_id", "spine_id", "selections"}:
        raise TemplateIntelligenceError("selection plan fields are invalid")
    if payload.get("schema_version") != "1.0":
        raise TemplateIntelligenceError("selection plan schema_version must be 1.0")
    raw_selections = payload.get("selections")
    if not isinstance(raw_selections, list) or not raw_selections:
        raise TemplateIntelligenceError("selection plan requires selections")
    selections: list[SlideSelection] = []
    required = {
        "slide_id", "candidate_id", "fact_refs", "asset_refs", "importance",
        "confidence", "fallback_reason", "rationale_codes",
    }
    for index, item in enumerate(raw_selections):
        if not isinstance(item, Mapping) or set(item) != required:
            raise TemplateIntelligenceError(
                f"selection plan selections[{index}] fields are invalid"
            )
        confidence = item["confidence"]
        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not 0 <= confidence <= 1
        ):
            raise TemplateIntelligenceError("selection confidence must be 0..1")
        fallback = item["fallback_reason"]
        if fallback not in {
            None,
            "LOW_CONFIDENCE_SAFE_DEFAULT",
            "SAME_FAMILY_CAPACITY_FALLBACK",
        }:
            raise TemplateIntelligenceError(
                "selection fallback_reason is not governed"
            )
        selections.append(
            SlideSelection(
                _text(item["slide_id"], "selection.slide_id"),
                _text(item["candidate_id"], "selection.candidate_id"),
                _strings(item["fact_refs"], "selection.fact_refs"),
                _strings(item["asset_refs"], "selection.asset_refs"),
                _text(item["importance"], "selection.importance"),
                float(confidence),
                fallback,
                _strings(item["rationale_codes"], "selection.rationale_codes"),
            )
        )
    return TemplateSelectionPlan(
        "1.0",
        _text(payload["brief_id"], "selection.brief_id"),
        _text(payload["spine_id"], "selection.spine_id"),
        tuple(selections),
    )


def slide_blueprints_from_payload(payload: Mapping[str, Any]) -> tuple[SlideBlueprint, ...]:
    """Load the versioned blueprint sidecar emitted by production."""

    if set(payload) != {"schema_version", "blueprints"}:
        raise TemplateIntelligenceError("blueprint sidecar fields are invalid")
    if payload.get("schema_version") != "1.0":
        raise TemplateIntelligenceError("blueprint sidecar schema_version must be 1.0")
    raw_blueprints = payload.get("blueprints")
    if not isinstance(raw_blueprints, list) or not raw_blueprints:
        raise TemplateIntelligenceError("blueprint sidecar requires blueprints")
    result: list[SlideBlueprint] = []
    for item in raw_blueprints:
        if not isinstance(item, Mapping):
            raise TemplateIntelligenceError("blueprint must be an object")
        validate_blueprint_payload(item)
        if item.get("schema_version") != "1.0":
            raise TemplateIntelligenceError(
                "blueprint schema_version must be 1.0"
            )
        physical_slide = item["physical_slide"]
        base_variant_id = item["base_variant_id"]
        if physical_slide is not None and (
            type(physical_slide) is not int or physical_slide < 1
        ):
            raise TemplateIntelligenceError("blueprint physical_slide is invalid")
        if base_variant_id is not None and (
            not isinstance(base_variant_id, str) or not base_variant_id.strip()
        ):
            raise TemplateIntelligenceError("blueprint base_variant_id is invalid")
        result.append(
            SlideBlueprint(
                _text(item["schema_version"], "blueprint.schema_version"),
                _text(item["slide_id"], "blueprint.slide_id"),
                _text(item["spine_id"], "blueprint.spine_id"),
                _text(item["candidate_id"], "blueprint.candidate_id"),
                _text(item["family"], "blueprint.family"),
                _text(item["materializer"], "blueprint.materializer"),
                _strings(item["fact_refs"], "blueprint.fact_refs"),
                _strings(item["asset_refs"], "blueprint.asset_refs"),
                _text(item["token_profile_id"], "blueprint.token_profile_id"),
                physical_slide,
                base_variant_id,
            )
        )
    return tuple(result)
