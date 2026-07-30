# Phase 45: Selection-to-Materialization Bridge - Research

**Created:** 2026-07-30
**Status:** Complete
**Requirement:** V6R-MAT-01

## Objective

Trace selection through real production execution and identify the smallest
truthful bridge.

## Local Evidence

- `template_intelligence.py` owns certified spines, deterministic candidate
  retrieval, `TemplateSelectionPlan`, and `SlideBlueprint`.
- The registered candidates carry `base_variant_id`, but the blueprint drops
  that field. Consequently a registered selection cannot identify the exact
  layout that must be rendered.
- `generation.prepare_brief_generation()` never imports or consumes template
  intelligence. Its visual, composition, deck, and render plans can therefore
  disagree with the selected candidate without detection.
- The production CLI exposes two disconnected routes: BriefPlan uses the native
  portable renderer, while `--render-template-pack` invokes the whole-deck
  TemplatePack adapter.
- The physical institutional spine is a hash-bound 15-slide OOXML pack with
  declared editable bindings. Campus and academic spines are registered native
  compositions.
- No safe arbitrary cross-package slide-graph cloner exists. Treating a private
  page ID as materialized metadata would be false evidence.

## Failed delegated discovery

The initial Agnes fallback repeatedly used an invalid file-read argument and
was stopped. None of its output is accepted as evidence. The findings above
come from direct repository inspection and will be challenged by a fresh,
self-contained OpenCode review after the design packet is frozen.

## Options

- Metadata-only evidence: rejected because it does not affect output.
- Dual registered-native/physical execution bridge: feasible now.
- Arbitrary multi-source OOXML merger: valuable but unsafe within this phase.

## Recommendation

Use a dual execution bridge:

1. Registered-native blueprints bind the exact `base_variant_id` into the
   compiler and renderer. Any fallback or observed-layout mismatch fails.
2. Physical blueprints are executable only through the whole-deck TemplatePack
   adapter. Evidence binds source digest, pack ID, physical slide, output slide,
   output digest, and adaptation report.
3. A materialization run may use one materializer only. Mixed physical/native,
   unknown, uncertified, reference-only, or unproven selections fail closed.

Full arbitrary private multi-source OOXML slide composition is deferred until a
safe relationship-graph merger is implemented; Phase 45 must not fabricate it.

## Assumptions To Confirm

None. Existing contracts and the user's continue-unless-blocked instruction
resolve the implementation choices.
