# Phase 32: CompositionPlan and Generated Reference Floor - Specification

**Created:** 2026-07-28
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Requirements:** 7

## Goal

Turn source-bound narrative intent into a reference-grade Chinese consulting
proposal whose real component compositions, visual anchors, assets, theme,
and repair decisions are owned by deterministic Skill contracts rather than
model-authored coordinates or generic layout seeds.

## Background

- R2 is a real editable 12-slide artifact and passes the portable engineering
  gates, but remains `PARTIAL_NOT_REFERENCE_GRADE`.
- `VisualSlide.variant`, `emphasis`, `density`, `components`, and `asset_refs`
  are not materialized in the renderer. Recipe IDs influence only a generic
  layout seed.
- Seven asset intents remain `planned`; large outline panels and `.art.*`
  decoration can raise object-count richness while carrying little semantic
  information.
- Quality v2 separates hard gates from findings but has no reference-grade
  visual score, art-review state, or composition-level repair loop.
- OpenCode Agnes does not prove direct-API image capability. Direct Agnes API
  has independently passed public-URL and Data-URI image probes in the current
  environment.

## Requirements

### P32-COMP-01 — CompositionPlan v1

- **Current:** The executable chain jumps from `VisualPlan` metadata to
  generic DeckPlan/RenderPlan layout resolution.
- **Target:** Add a validated, immutable `CompositionPlan` between
  `VisualPlan` and `RenderPlan`. Each composed slide contains source/fact
  trace, registered composition/variant/layout IDs, semantic slot bindings,
  background/density/emphasis, anchor/motif/annotation plans, materialized
  assets, repair alternatives, and a decision trace.
- **Acceptance:** A strict JSON schema and Python models reject missing
  required slots, unknown IDs, raw geometry/style/code fields, unbound
  required assets, and source/fact trace loss. The consulting fixture
  compiles through `VisualPlan -> CompositionPlan -> RenderPlan`, and every
  required slot maps to a real RenderObject.

Weak-model input cannot supply coordinates, fonts, colors, OOXML, HTML,
component implementation IDs, executable code, or arbitrary repair actions.

### P32-DESIGN-01 — Consulting editorial DesignPack

- **Current:** `consulting-executive` provides a shallow palette, page-family
  list, pacing, and asset priority but no executable motif, depth,
  choreography, or composition catalog.
- **Target:** Upgrade the pack to schema v2 and lock the first direction as
  `knowledge-wayfinding` with palette roles, portal/path/node motifs, four
  background modes, a governed grid/type/surface/depth system, composition
  variants, cadence, forbidden patterns, and quality profile.
- **Acceptance:** Pack validation proves the required tokens and composition
  coverage. The 14-page consulting choreography is deterministic for the
  same FactStore and frozen assets.

- palette roles: warm paper, navy ink, teal signal, warm-gold focus,
  supporting cool gray, and risk;
- portal/entry arc, route, signal node, and waypoint motif primitives;
- paper, tinted, deep-ink, and hero-image backgrounds;
- 12-column grid with 0.55in horizontal and 0.45in vertical text-safe
  margins; motif and media may bleed;
- explicit typography, surface, depth, asset-family, cadence, forbidden
  pattern, and quality-profile rules;
- at least two deterministic variants per required consulting composition,
  and at least three for cover, section, KPI/transformation, process, and
  timeline.

The authorized work-summary deck is a quality benchmark only. Literal
lighthouse reproduction, copied media, copied palette, rasterized full
slides, purple technology gradients, decorative empty frames, and card
monoculture are forbidden.

### P32-NARRATIVE-01 — Source-bound 14-page choreography

- **Current:** R2 is mostly one authored fact group per page with limited
  section rhythm and weak fact fusion.
- **Target:** Compile the consulting fixture into the source-bound 14-page
  sequence below.
- **Acceptance:** Exact fact IDs, source text, numbers, units, formulas, and
  FactStore digest survive compilation and both repair rounds.

1. editorial portal cover;
2. executive summary using the 10-day baseline, 5-day target, and six-month
   pilot;
3. section transition: why now;
4. current-state fragmentation map with the 10-day evidence anchor;
5. 10-to-5 transformation bridge with a traceable `-50%` derived fact;
6. section transition: what will be built;
7. four-step operating loop;
8. four-workstream compass around the common entry point;
9. section transition: how delivery works;
10. five-phase/six-month editable delivery rail;
11. four-role governance flow;
12. source-bound risk and mitigations;
13. three decision gates;
14. mirrored portal close and pilot CTA.

Facts may merge, reorder, and intentionally repeat, but every occurrence must
retain source/fact trace. No prose, value, formula, label, or evidence may be
invented.

### P32-ASSET-01 — Materialized asset pipeline

- **Current:** Asset priority exists but required intents can remain
  `planned`.
- **Target:** Resolve assets in this order:
  `user -> Iconify/Pixabay -> Agnes Image 2.1/ModelScope -> native editable`.
  Generated images are limited to non-text hero/background/illustration/
  texture roles and selected bytes are frozen with provenance and hashes.
- **Acceptance:** Every required intent ends in `resolved` or
  `native-materialized`. Missing providers degrade to a complete native
  composition rather than an empty panel.

Generated images are limited to hero, background, illustration, and texture
roles. They must not contain facts, text, numbers, charts, logos, or
watermarks. Selected bytes are frozen with provider/model/prompt/input/output
hashes and crop metadata; replay never silently regenerates.

### P32-AGNES-01 — Direct Agnes providers

- **Current:** Reviewer routing is model-name based and conflates OpenCode
  and direct-provider capabilities.
- **Target:** Add provider-neutral direct Agnes routes, a session-bound
  challenge probe, strict JSON review, per-slide/deck passes, deterministic
  cache/replay, redacted errors, and explicit OpenCode/DeepSeek separation.
- **Acceptance:** Mock and opt-in live tests cover public URL/Data URI,
  malformed output, timeout, retry, auth/rate-limit redaction, cache replay,
  asset Base64 validation, and route separation. DeepSeek can never become a
  pixel-review fallback.

- `agnes-direct/agnes-2.0-flash`: visual observation and review;
- `agnes-direct/agnes-image-2.1-flash`: text-to-image and image-to-image;
- `opencode/deepseek-v4-flash-free`: code/contract audit only.

The direct route performs a session-bound challenge-image probe. Data URI is
enabled only after a successful probe; otherwise a configured controlled
public URL transport is required. Customer images are never uploaded to an
anonymous host. Reviews use a deck contact sheet plus high-resolution pages
in batches of at most four and return strict schema-bound JSON with
region-specific visible evidence and registered finding/repair codes.

### P32-QA-01 — QualityReport v3

- **Current:** Quality v2 can pass an engineering-safe artifact containing
  important visual findings.
- **Target:** Add engineering/visual/art/release pass states, six scored
  visual axes, role/theme profiles, a total threshold of `84`, per-axis
  threshold of `75`, and the required visual hard-gate codes.
- **Acceptance:** The frozen R2 artifact fails v3 for the expected reasons;
  the reference baseline avoids false edge/decoration failures; R3/R4 expose
  all four pass states and the score trace.

- `engineering_passed`;
- `visual_passed`;
- `art_review_passed`;
- `release_passed`, true only when all three are true;
- six scored axes: hierarchy/readability, composition/space, art direction,
  business evidence, deck rhythm, and asset/polish.

The reference-grade automatic threshold is total score `>=84`, every axis
`>=75`, and no visual hard gate. Required hard-gate codes include:

- `SEMANTIC_COMPONENT_UNMATERIALIZED`;
- `ASSET_INTENT_UNMATERIALIZED`;
- `EMPTY_PANEL_SHELL`;
- `DECK_CONTENT_INK_FLOOR`;
- `ART_DIRECTION_NOT_MATERIALIZED`;
- `DECORATION_DOMINATES_CONTENT`;
- `EVIDENCE_ANNOTATION_COVERAGE_LOW`;
- `DECK_CHOREOGRAPHY_FLAT`.

Role- and theme-specific profiles prevent legitimate full-bleed, monochrome,
section, and motif pages from being rejected by universal raw counts.

### P32-REPAIR-01 — Composition recompilation

- **Current:** Existing repair changes candidate geometry/fonts or performs
  pre-render asset fallback; it cannot redesign a weak composition.
- **Target:** Run an initial candidate plus at most two CompositionPlan
  recompilations using registered actions. Accept only lexicographically
  improving defect vectors with an unchanged protected FactStore digest.
- **Acceptance:** Non-monotonic, repeated-fingerprint, unregistered, or
  fact-changing repairs roll back and stop.

## AI and evaluation contract

- Agnes observes pixels and ranks candidates; it does not own facts,
  implementation code, geometry, or release truth.
- Contact-sheet-only review is insufficient. Every reviewed slide must have
  a high-resolution image and region-specific visible evidence.
- Invalid JSON receives one schema-repair attempt; a second failure is
  `NOT_RUN`.
- `agnes-2.0-flash` is the initial direct-review candidate. Any replacement
  model must first pass the frozen calibration: reference accepted, R2
  rejected, and page evidence complete.
- Agnes automatic scores support iteration. Final reference-grade acceptance
  still requires anonymous human review averaging at least `4.2/5` with no
  dimension below `4`; absent human evidence remains `NOT_RUN`, not PASS.

## Boundaries

### In Scope

- CompositionPlan v1 and its rendering seam.
- Consulting `knowledge-wayfinding` DesignPack and 14-page tracer.
- Direct Agnes Vision/Image adapters and deterministic replay.
- QualityReport v3 and composition-level repair.
- R3/R4 real PPTX, PNG, manifests, before/after evidence, Skill workflow, and
  Phase 32 records.

### Out Of Scope

- Multi-scenario DesignPacks and full 15-scenario rollout (Phase 33).
- Four-scenario UAT and formal weak-model benchmark (Phases 34–35).
- COM registry repair or making COM a daily dependency.
- HTML-to-PPTX, full-slide screenshot delivery, SmartArt, and arbitrary
  model-authored rendering.

## Constraints

- Preserve existing public VisualPlan, DeckPlan, RenderPlan, Quality v2, and
  reviewer-routing consumers through additive schema/API versioning.
- Keep native-editable facts, text, numbers, charts, diagrams, tables, and
  core shapes; only non-text decorative media may be raster.
- Never record or log `AGNES_API_KEY`, authorization headers, or raw cached
  Data URIs.
- Do not require PowerPoint COM for portable generation or verification.
- Provider/network failure is fail-closed for art review and deterministic
  native fallback for optional generated assets.
- Repair is capped at two recompilations and cannot alter protected content.

## Engineering Contract

- **Domain terms and owners:** VisualPlan owns visual intent; CompositionPlan
  owns registered executable composition choices; Asset Resolution owns
  materialized bytes/native fallback; RenderPlan owns geometry; Quality v3
  owns reference-grade automatic verdicts; Agnes owns observations only.
- **Invariants:** FactStore digest, facts, numbers, units, formulas, citations,
  and native editability remain unchanged through composition and repair.
- **Interfaces and compatibility:** New v1/v3 contracts are additive. Existing
  v2 reports and seed-only callers continue to parse and receive deterministic
  compatibility output until migrated.
- **Failure semantics:** Unknown registry IDs, unmaterialized required slots,
  invalid provider output, missing evidence, and non-monotonic repair fail
  closed with registered error/finding codes.
- **Migration and rollback:** VisualPlan-to-CompositionPlan is introduced
  expand-contract. The old seed path remains a compatibility fallback only
  for non-reference profiles; a rejected repair preserves the prior candidate.

## Test Seams And Critical Cases

| Behavior | Observable Seam | Failing Case | Evidence |
|---|---|---|---|
| P32-COMP-01 | VisualPlan-to-CompositionPlan public compiler | unknown IDs/raw geometry | focused model/schema tests |
| P32-DESIGN-01 | DesignPack loader and coverage validator | missing motif/token/variant | pack contract tests |
| P32-NARRATIVE-01 | consulting fixture compilation | lost/duplicated fact trace | 14-page choreography tests |
| P32-ASSET-01 | AssetPlan resolution | required intent remains planned | asset manifest tests |
| P32-AGNES-01 | direct provider adapter | unprobed image/malformed JSON | mock and opt-in live tests |
| P32-QA-01 | Quality v3 report | frozen R2 incorrectly passes | R2/reference regression |
| P32-REPAIR-01 | composition repair coordinator | fact change/non-improvement | rollback/fingerprint tests |

## Acceptance Criteria

- [ ] P32-COMP-01 has concrete passing evidence.
- [ ] P32-DESIGN-01 has concrete passing evidence.
- [ ] P32-NARRATIVE-01 has concrete passing evidence.
- [ ] P32-ASSET-01 has concrete passing evidence.
- [ ] P32-AGNES-01 has concrete passing evidence.
- [ ] P32-QA-01 has concrete passing evidence.
- [ ] P32-REPAIR-01 has concrete passing evidence.
- [ ] The R3/R4 deliverables retain native editability and exact fact trace.
- [ ] Final blind human review is recorded as PASS or explicitly `NOT_RUN`;
  it is never inferred from Agnes.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.96
- **Boundary clarity:** 0.93
- **Constraint clarity:** 0.92
- **Acceptance clarity:** 0.94
- **Ambiguity:** 0.06

## Decision Log

- 2026-07-27: Reference is a quality benchmark, not a literal skin.
- 2026-07-27: First direction is `knowledge-wayfinding`.
- 2026-07-27: Fact merge/reorder/reuse is allowed only with exact trace.
- 2026-07-27: Assets are automatic and quality-first; generated output is
  frozen locally.
- 2026-07-27: Direct Agnes and OpenCode routes are separate capabilities.
- 2026-07-27: COM remains optional sampled certification.
- 2026-07-28: Plan review blockers resolved by this locked schema, DesignPack,
  Quality v3, and evaluation contract.
