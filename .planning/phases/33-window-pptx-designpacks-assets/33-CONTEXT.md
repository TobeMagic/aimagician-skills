# Phase 33 Context

## Decision

Phase 33 closes the gap between a structurally valid generated deck and an
authored, customer-deliverable deck. The four DesignPack directories already
exist, but only `consulting-executive` implements the v2 art-direction
contract. Phase 33 upgrades the remaining three packs and makes AssetPlan
produce governed bytes or explicit native fallbacks that RenderPlan actually
consumes.

## Visual baseline

- Authorized reference: `.planning/references/pptx/工作总结.pptx`.
- Portable reference proof:
  `.planning/evidence/v5.1-reference-grade-work-summary-r10/contact-sheet.png`.
- Generated failing baseline:
  `.planning/evidence/phase32-consulting-tracer-r6/contact-sheet.png`.
- R6 engineering is accepted, but its visual release remains `NO_GO`.
- Direct Agnes comparison request:
  `e9cde2359a41b47adf170633536467c04cd8cf6286b39664bf714c5f32c4df1d`.
- Direct Agnes comparison response:
  `c6d4816ff38249c1dae0736076b0ae4373371cd4987ec1e80e67833eb8de8841`.
- Comparison verdict: `FAIL`; R6 scores `62/58/55/70/50/48`.

The reference is a method baseline, not a skin to copy. The reusable method is:
one memorable visual anchor, strong display typography, authored section
peaks, layered surfaces, evidence-rich charts and tables, controlled density,
and a motif that changes form while remaining recognizable.

## Provider boundary

- Direct Agnes is the preferred pixel-level visual reviewer after the
  session-bound Data URI probe.
- OpenCode Agnes currently rejects image attachments and is used only for
  code, contract, planning, and evidence audits.
- DeepSeek V4 Flash Free is the ordinary-model planning and code-audit lane.
- Provider names never imply capability; every visual route needs a fresh
  image-input probe.

## Accepted implementation direction

1. Add an `AssetMaterialization` seam between AssetPlan and renderer bindings.
2. Freeze generated or selected bytes, dimensions, crop intent, provenance,
   hashes, provider route, and safe fallback.
3. Keep facts, labels, charts, tables, and processes native and editable.
4. Give cover, section, case, product, and selected evidence pages a real
   image-led composition; do not rasterize complete slides.
5. Upgrade the three v1 DesignPacks to v2 with distinct art-direction systems.
6. Keep TemplatePack and generated DesignPack paths separate but governed by
   the same quality and evidence vocabulary.

## Anti-copy boundary

The system may generalize hierarchy, anchor scale, visual cadence, cropping,
layering, motif continuity, and evidence density. It must not copy the
reference's lighthouse, hand photograph, exact typography arrangement,
illustrations, decorative geometry, or page-by-page composition.
