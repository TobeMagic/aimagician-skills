"""End-to-end governed preparation for the weak-model PPTX route.

This module is intentionally COM-free.  It turns immutable facts plus a small
model-authored BriefPlan into auditable narrative, direction, DeckPlan, and
RenderPlan artifacts.  The Windows facade performs the final transaction.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping

from .assets import (
    AssetIntent,
    choose_asset,
    read_raster_dimensions,
    read_svg_aspect_ratio,
)
from .brand import (
    BrandFinding,
    BrandSpec,
    assess_brand_assets,
    font_inventory_digest,
    validate_brand_spec,
)
from .deck_plan import compile_deck_plan
from .design_packs import DesignPack, select_design_pack
from .directions import (
    DirectionContext,
    DirectionDecision,
    load_art_directions,
    lock_art_direction,
    select_art_directions,
    select_proof_slide_ids,
)
from .layouts import SlideSize
from .render_plan import AssetBinding, RenderPlan, compile_render_plan
from .quality_v2 import (
    QualityFindingV2,
    StageRepairPass,
    build_quality_report_v2,
    execute_two_stage_repair,
)
from .themes import select_theme
from .weak_model import (
    BriefAttempt,
    BriefCompilation,
    FactStore,
    compile_brief_plan,
    compile_brief_with_retries,
)
from .visual_plan import (
    AssetPlan,
    VisualPlan,
    compile_visual_plan,
    governed_runtime_family,
)


class GenerationGateError(ValueError):
    """A governed pre-render gate failed before PowerPoint could be started."""


@dataclass(frozen=True)
class BriefGeneration:
    compilation: BriefCompilation
    design_pack: DesignPack
    visual_plan: VisualPlan
    asset_plan: AssetPlan
    effective_deck_plan: dict[str, Any]
    compiled_deck: dict[str, Any]
    render_plan: RenderPlan | None
    direction: DirectionDecision | None
    selected_theme_id: str | None
    proof_slide_ids: tuple[str, ...]
    brand_findings: tuple[BrandFinding, ...]
    asset_fallbacks: tuple[str, ...]
    asset_rejections: tuple[str, ...]
    pre_render_repair_passes: tuple[StageRepairPass, ...]
    brief_attempts: tuple[BriefAttempt, ...]
    brief_fallback_used: bool
    interaction_required: bool
    brand_spec_evidence: Mapping[str, Any] | None
    font_inventory_evidence: Mapping[str, Any]
    asset_manifest_evidence: Mapping[str, Any]

    def to_dict(self, *, include_render_plan: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": "1.0",
            "fact_store_digest": self.compilation.fact_store.digest,
            "normalization_trace": list(
                self.compilation.normalization_trace.changes
            ),
            "narrative_plan": self.compilation.narrative.to_dict(),
            "design_pack_id": self.design_pack.id,
            "visual_plan": self.visual_plan.to_dict(),
            "asset_plan": self.asset_plan.to_dict(),
            "deck_plan": copy.deepcopy(self.effective_deck_plan),
            "compiled_deck": copy.deepcopy(self.compiled_deck),
            "direction_decision": (
                self.direction.to_dict() if self.direction is not None else None
            ),
            "selected_theme_id": self.selected_theme_id,
            "proof_slide_ids": list(self.proof_slide_ids),
            "brand_findings": [
                {
                    "code": item.code,
                    "message": item.message,
                    "hard_gate": item.hard_gate,
                    "asset_kind": item.asset_kind,
                }
                for item in self.brand_findings
            ],
            "asset_fallbacks": list(self.asset_fallbacks),
            "asset_rejections": list(self.asset_rejections),
            "pre_render_repair_passes": [
                {
                    "stage": item.stage,
                    "before_vector": list(item.before_vector),
                    "after_vector": list(item.after_vector),
                    "accepted": item.accepted,
                    "rolled_back": item.rolled_back,
                    "failure_code": item.failure_code,
                }
                for item in self.pre_render_repair_passes
            ],
            "brief_attempts": [
                {
                    "index": item.index,
                    "accepted": item.accepted,
                    "error_code": item.error_code,
                    "error_message": item.error_message,
                }
                for item in self.brief_attempts
            ],
            "brief_fallback_used": self.brief_fallback_used,
            "interaction_required": self.interaction_required,
            "brand_spec_evidence": (
                copy.deepcopy(dict(self.brand_spec_evidence))
                if self.brand_spec_evidence is not None
                else None
            ),
            "font_inventory_evidence": copy.deepcopy(
                dict(self.font_inventory_evidence)
            ),
            "asset_manifest_evidence": copy.deepcopy(
                dict(self.asset_manifest_evidence)
            ),
        }
        if include_render_plan:
            payload["render_plan"] = (
                self.render_plan.to_dict() if self.render_plan is not None else None
            )
            payload["proof_render_plan"] = (
                {
                    "slide_ids": list(self.proof_slide_ids),
                    "slides": [
                        slide.to_dict()
                        for slide in self.render_plan.slides
                        if slide.source_id in self.proof_slide_ids
                    ],
                }
                if self.render_plan is not None
                else None
            )
        return payload


def available_asset_kinds(
    asset_bindings: Mapping[str, AssetBinding] | None,
) -> frozenset[str]:
    result: set[str] = set()
    for source_ref, binding in (asset_bindings or {}).items():
        result.add(binding.record.kind.casefold())
        searchable = " ".join(
            (
                source_ref,
                binding.record.id,
                binding.path.stem,
                binding.record.style or "",
            )
        ).casefold()
        if "product" in searchable:
            result.add("product")
        if any(token in searchable for token in ("screenshot", "screen", "ui")):
            result.add("ui")
    return frozenset(result)


def _canonical_sha256(value: Any) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _asset_manifest_content(
    asset_bindings: Mapping[str, AssetBinding] | None,
) -> dict[str, Any]:
    bindings: dict[str, Any] = {}
    for source_ref, binding in sorted((asset_bindings or {}).items()):
        record = binding.record
        bindings[source_ref] = {
            "path": str(binding.path.expanduser().resolve(strict=False)),
            "record": {
                "id": record.id,
                "kind": record.kind,
                "style": record.style,
                "aspect_ratio": record.aspect_ratio,
                "quality": record.quality,
                "source": record.source,
                "license": record.license,
                "retrieved_at": record.retrieved_at,
                "width_px": record.width_px,
                "height_px": record.height_px,
                "icon_family": record.icon_family,
            },
        }
    return {"schema_version": "1.0", "bindings": bindings}


def filter_usable_asset_bindings(
    asset_bindings: Mapping[str, AssetBinding] | None,
) -> tuple[dict[str, AssetBinding], tuple[str, ...]]:
    """Reject unusable governed image bindings before layout selection."""

    usable: dict[str, AssetBinding] = {}
    rejected: list[str] = []
    for source_ref, binding in (asset_bindings or {}).items():
        reason: str | None = None
        path = binding.path.expanduser().resolve(strict=False)
        suffix = path.suffix.casefold()
        if not path.is_file() or suffix not in {".png", ".jpg", ".jpeg", ".svg"}:
            reason = "MISSING_OR_UNSUPPORTED_FILE"
        else:
            try:
                if suffix == ".svg":
                    record_kind = (
                        binding.record.kind.strip().casefold()
                        if isinstance(binding.record.kind, str)
                        else ""
                    )
                    if record_kind not in {"icon", "vector", "logo"}:
                        reason = "SVG_KIND_NOT_ALLOWED"
                    elif binding.record.aspect_ratio is None:
                        reason = "ASPECT_EVIDENCE_MISSING"
                    elif not math.isclose(
                        binding.record.aspect_ratio,
                        read_svg_aspect_ratio(path),
                        rel_tol=0.01,
                    ):
                        reason = "ASPECT_EVIDENCE_MISMATCH"
                else:
                    width, height = read_raster_dimensions(path)
                    if (binding.record.width_px, binding.record.height_px) != (width, height):
                        reason = "DIMENSION_EVIDENCE_MISMATCH"
                    elif binding.record.aspect_ratio is None:
                        reason = "ASPECT_EVIDENCE_MISSING"
                if reason is None:
                    choice = choose_asset(
                        AssetIntent(
                            binding.record.kind,
                            binding.record.style,
                            binding.record.aspect_ratio,
                        ),
                        (binding.record,),
                    )
                    if choice.asset_id != binding.record.id:
                        reason = choice.reason or choice.rejected.get(
                            binding.record.id, "ASSET_POLICY_REJECTED"
                        )
            except ValueError as exc:
                reason = str(exc)
        if reason is None:
            usable[source_ref] = binding
        else:
            rejected.append(f"{source_ref}:{reason}")
    return usable, tuple(rejected)


def apply_asset_safe_fallback(
    deck_plan: Mapping[str, Any],
    asset_bindings: Mapping[str, AssetBinding] | None,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Downgrade unsupported image requests to native editable statements."""

    result = copy.deepcopy(dict(deck_plan))
    available = set((asset_bindings or {}).keys())
    fallbacks: list[str] = []
    for slide in result.get("slides", []):
        for block in slide.get("blocks", []):
            if block.get("kind") != "image":
                continue
            source_ref = block.get("source_ref")
            if source_ref in available:
                continue
            block["kind"] = "statement"
            fallbacks.append(
                f"{slide.get('id', '?')}.{block.get('id', '?')}:IMAGE_TO_NATIVE_STATEMENT"
            )
    return result, tuple(fallbacks)


def _ensure_fact_safety(fact_store: FactStore, deck_plan: Mapping[str, Any]) -> None:
    serialized = json.dumps(deck_plan, ensure_ascii=False, sort_keys=True)
    missing = [
        fact.id
        for fact in fact_store.active_facts()
        if fact.required and fact.text not in serialized
    ]
    if missing:
        raise GenerationGateError(
            "FACT_COVERAGE_FAILED: " + ", ".join(sorted(missing))
        )


def prepare_brief_generation(
    fact_payload: Any,
    brief_payload: Any,
    *,
    slide_size: SlideSize | None = None,
    installed_fonts: set[str] | None = None,
    theme_id: str | None = None,
    brand_spec: BrandSpec | Mapping[str, Any] | None = None,
    brand_spec_source: str | None = None,
    asset_bindings: Mapping[str, AssetBinding] | None = None,
    asset_manifest_source: str | None = None,
    direction_mode: str = "auto",
    direction_id: str | None = None,
    design_system_version: str = "art-direction-v1",
    build_render: bool = False,
    brief_retry_payloads: tuple[Any, ...] = (),
    use_safe_default: bool = False,
    fallback_scenario_id: str | None = None,
) -> BriefGeneration:
    """Prepare a deterministic weak-model generation and optionally RenderPlan."""

    if direction_mode not in {"auto", "interactive", "locked"}:
        raise GenerationGateError(f"unknown direction mode: {direction_mode}")
    if design_system_version not in {"legacy-v5", "art-direction-v1"}:
        raise GenerationGateError(
            f"unknown design system version: {design_system_version}"
        )
    if len(brief_retry_payloads) > 2:
        raise GenerationGateError("at most two BriefPlan retries are allowed")
    if use_safe_default:
        scenario_id = fallback_scenario_id
        if scenario_id is None and isinstance(brief_payload, Mapping):
            candidate = brief_payload.get("scenario_id")
            scenario_id = candidate if isinstance(candidate, str) else None
        if scenario_id is None:
            raise GenerationGateError(
                "fallback_scenario_id is required when safe-default retry mode is enabled"
            )
        retry_result = compile_brief_with_retries(
            fact_payload,
            (brief_payload, *brief_retry_payloads),
            scenario_id=scenario_id,
            max_retries=2,
        )
        compilation = retry_result.compilation
        brief_attempts = retry_result.attempts
        brief_fallback_used = retry_result.fallback_used
    else:
        compilation = compile_brief_plan(fact_payload, brief_payload)
        brief_attempts = (BriefAttempt(1, True, None, None),)
        brief_fallback_used = False
    design_pack = select_design_pack(compilation.brief_plan.scenario_id)
    visual_plan, asset_plan = compile_visual_plan(
        compilation.narrative,
        design_pack=design_pack,
    )
    visual_family_by_slide = {
        slide.slide_id: governed_runtime_family(slide.family)
        for slide in visual_plan.slides
    }
    bindings, asset_rejections = filter_usable_asset_bindings(asset_bindings)
    asset_kinds = available_asset_kinds(bindings)
    font_inventory = set(installed_fonts or {"Arial"})
    resolved_brand = (
        brand_spec
        if isinstance(brand_spec, BrandSpec)
        else validate_brand_spec(brand_spec)
        if brand_spec is not None
        else None
    )
    brand_spec_evidence: dict[str, Any] | None = None
    if resolved_brand is not None:
        brand_content = resolved_brand.to_dict()
        brand_spec_evidence = {
            "source": "file" if brand_spec_source else "inline",
            "path": brand_spec_source,
            "sha256": _canonical_sha256(brand_content),
            "content": brand_content,
        }
    font_names = sorted(font_inventory, key=str.casefold)
    font_inventory_evidence = {
        "source": "installed-font-inventory",
        "sha256": font_inventory_digest(font_names),
        "fonts": font_names,
    }
    asset_content = _asset_manifest_content(asset_bindings)
    asset_manifest_evidence = {
        "source": "file" if asset_manifest_source else (
            "inline" if asset_bindings else "none"
        ),
        "path": asset_manifest_source,
        "sha256": _canonical_sha256(asset_content),
        "content": asset_content,
    }
    brand_findings = list(
        assess_brand_assets(
            resolved_brand,
            asset_kinds,
            installed_fonts=font_inventory,
        )
        if resolved_brand is not None
        else ()
    )
    hard_brand = [item for item in brand_findings if item.hard_gate]
    if hard_brand:
        if all(item.code == "REQUIRED_BRAND_ASSET_MISSING" for item in hard_brand):
            raise GenerationGateError(
                "BRAND_ASSET_GATE_FAILED: "
                + ", ".join(item.asset_kind or "unknown" for item in hard_brand)
            )
        raise GenerationGateError(
            "BRAND_FIDELITY_GATE_FAILED: "
            + ", ".join(item.code for item in hard_brand)
        )

    direction: DirectionDecision | None = None
    preferred_families: tuple[str, ...] = ()
    selected_theme = theme_id
    selected_profile_id: str | None = None
    if design_system_version == "art-direction-v1":
        preferences = compilation.brief_plan.preferences_dict()
        context = DirectionContext(
            scenario=compilation.brief_plan.scenario_id,
            audience=(
                compilation.fact_store.project.audience
                or preferences.get("audience_mode")
            ),
            density=preferences.get("density", "balanced"),
            tone=preferences.get("tone", "professional"),
            locale=compilation.fact_store.project.language,
            available_asset_kinds=asset_kinds,
            has_brand=(
                resolved_brand is not None
                and bool(
                    resolved_brand.palette
                    or resolved_brand.fonts
                    or resolved_brand.required_assets
                )
            ),
        )
        direction = (
            lock_art_direction(context, direction_id)
            if direction_mode == "locked" and direction_id is not None
            else select_art_directions(context)
        )
        profiles = load_art_directions()
        profile = profiles[direction.selected_profile_id]
        selected_profile_id = profile.id
        preferred_families = profile.preferred_families
        if selected_theme is None:
            selected_theme = (
                select_theme(
                    compilation.brief_plan.scenario_id,
                    audience=compilation.fact_store.project.audience,
                )
                if direction.fallback_reason == "LOW_CONFIDENCE_SAFE_DEFAULT"
                else profile.theme_candidates[0]
            )

    initial_asset_findings: list[QualityFindingV2] = []
    available_sources = set(bindings)
    for slide in compilation.deck_plan.get("slides", []):
        for block in slide.get("blocks", []):
            if (
                block.get("kind") == "image"
                and block.get("source_ref") not in available_sources
            ):
                initial_asset_findings.append(
                    QualityFindingV2(
                        "compile",
                        "IMAGE_ASSET_UNAVAILABLE",
                        "important",
                        str(slide.get("id", "")) or None,
                        str(block.get("id", "")) or None,
                        "image semantic has no governed asset and requires native fallback",
                        repairable=True,
                        source_stage="pre-render",
                    )
                )
    initial_pre_report = build_quality_report_v2(
        initial_asset_findings, transaction_status="pre-render"
    )

    def repair_assets(state: dict[str, Any]) -> tuple[Mapping[str, Any], Any]:
        fixed, fallbacks = apply_asset_safe_fallback(state["deck_plan"], bindings)
        proposed = dict(state)
        proposed["deck_plan"] = fixed
        proposed["asset_fallbacks"] = fallbacks
        return proposed, build_quality_report_v2(
            (), transaction_status="pre-render-repaired"
        )

    pre_result = execute_two_stage_repair(
        state={
            "deck_plan": compilation.deck_plan,
            "fact_digest": compilation.fact_store.digest,
            "asset_fallbacks": (),
        },
        initial_report=initial_pre_report,
        pre_render=repair_assets if initial_asset_findings else None,
    )
    safe_deck = copy.deepcopy(pre_result.state["deck_plan"])
    asset_fallbacks = tuple(pre_result.state.get("asset_fallbacks", ()))
    _ensure_fact_safety(compilation.fact_store, safe_deck)
    interaction_required = direction_mode == "interactive"
    should_build = build_render
    if should_build:
        if slide_size is None:
            raise GenerationGateError("slide_size is required to build a RenderPlan")
        compiled_deck, render_plan = compile_render_plan(
            safe_deck,
            slide_size=slide_size,
            installed_fonts=font_inventory,
            theme_id=selected_theme,
            brand=resolved_brand.to_overrides() if resolved_brand else None,
            asset_bindings=bindings,
            preferred_families=preferred_families,
            visual_family_by_slide=visual_family_by_slide,
            art_direction_id=selected_profile_id,
        )
    else:
        compiled_deck = compile_deck_plan(
            safe_deck,
            preferred_families=preferred_families,
            visual_family_by_slide=visual_family_by_slide,
        )
        render_plan = None
    if resolved_brand is not None and render_plan is not None:
        for event in render_plan.theme_events:
            if event.code not in {
                "BRAND_COLOR_CONTRAST_FALLBACK",
                "FONT_FALLBACK",
                "FONT_SAFE_DEFAULT_UNVERIFIED",
            }:
                continue
            code = (
                "BRAND_COLOR_FALLBACK"
                if event.code == "BRAND_COLOR_CONTRAST_FALLBACK"
                else "BRAND_FONT_FALLBACK"
            )
            finding = BrandFinding(
                code,
                (
                    f"brand {event.field} requested {event.requested!r} "
                    f"but resolved to {event.resolved!r}"
                ),
                resolved_brand.require_brand_fidelity,
                event.field,
            )
            if finding not in brand_findings:
                brand_findings.append(finding)
    if resolved_brand is not None and resolved_brand.prohibited_patterns:
        design_surface = json.dumps(
            {
                "direction": selected_profile_id,
                "theme": selected_theme,
                "slides": [
                    {
                        "page_family": slide.get("page_family"),
                        "layout_variant": slide.get("layout_variant"),
                    }
                    for slide in compiled_deck.get("slides", [])
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        ).casefold()
        for pattern in resolved_brand.prohibited_patterns:
            normalized = pattern.casefold().replace("_", "-").replace(" ", "-")
            if normalized not in design_surface.replace("_", "-").replace(" ", "-"):
                continue
            brand_findings.append(
                BrandFinding(
                    "BRAND_PROHIBITED_PATTERN_DETECTED",
                    f"brand-prohibited design pattern is present: {pattern}",
                    resolved_brand.require_brand_fidelity,
                    pattern,
                )
            )
    late_hard_brand = [item for item in brand_findings if item.hard_gate]
    if late_hard_brand:
        raise GenerationGateError(
            "BRAND_FIDELITY_GATE_FAILED: "
            + ", ".join(item.code for item in late_hard_brand)
        )
    return BriefGeneration(
        compilation=compilation,
        design_pack=design_pack,
        visual_plan=visual_plan,
        asset_plan=asset_plan,
        effective_deck_plan=safe_deck,
        compiled_deck=compiled_deck,
        render_plan=render_plan,
        direction=direction,
        selected_theme_id=selected_theme,
        proof_slide_ids=select_proof_slide_ids(compiled_deck),
        brand_findings=tuple(brand_findings),
        asset_fallbacks=asset_fallbacks,
        asset_rejections=asset_rejections,
        pre_render_repair_passes=pre_result.passes,
        brief_attempts=brief_attempts,
        brief_fallback_used=brief_fallback_used,
        interaction_required=interaction_required,
        brand_spec_evidence=brand_spec_evidence,
        font_inventory_evidence=font_inventory_evidence,
        asset_manifest_evidence=asset_manifest_evidence,
    )


__all__ = [
    "BriefGeneration",
    "GenerationGateError",
    "apply_asset_safe_fallback",
    "available_asset_kinds",
    "filter_usable_asset_bindings",
    "prepare_brief_generation",
]
