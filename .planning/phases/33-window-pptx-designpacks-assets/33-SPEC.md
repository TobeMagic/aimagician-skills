# Phase 33 Specification: Multi-Scenario DesignPacks and Asset Materialization

**Status:** Locked for implementation
**Date:** 2026-07-28
**Depends on:** Phase 32
**Milestone requirements:** V51-DESIGN-01, V51-DESIGN-03, V51-DESIGN-04

## Goal

Produce four executable DesignPack v2 systems and a deterministic,
provenance-safe asset materialization pipeline. The first vertical tracer is a
consulting proposal that must move from R6 visual `NO_GO` to a direct Agnes
`PASS` before the other three packs are accepted.

## Requirements

### P33-ASSET-01 — Materialization contract

The Skill shall compile every PlannedAsset into one of:

- `resolved`: user, template, or licensed bytes selected by policy;
- `generated`: frozen provider bytes with prompt/input/output hashes;
- `native-materialized`: editable chart, table, diagram, icon, or geometry;
- `fallback`: explicit safe native replacement with a reason;
- `rejected`: unusable evidence that cannot enter RenderPlan.

No required asset may remain `planned` in a release candidate.

### P33-ASSET-02 — Provenance and safety

Every raster or vector binding shall record source, license or user
authorization, retrieval date, dimensions, aspect ratio, byte SHA-256, crop
mode, focal-safe zone, provider route when generated, and replaceability.
Generated prompts shall prohibit text, logos, watermarks, and factual data.

### P33-ASSET-03 — Renderer integration

Materialized visual assets shall become governed AssetBindings and be consumed
by registered `image-frame` slots. Missing or rejected assets shall select a
registered native fallback before layout resolution. Full-slide screenshots
and image-only slides are forbidden.

### P33-COMP-01 — Image-led authored compositions

The consulting tracer shall implement registered variants for:

- image-led editorial cover;
- high-energy section divider;
- asymmetric executive summary;
- evidence/data story with one dominant claim;
- connected process and timeline;
- risk/decision split;
- closing action stage.

At least 35% of non-structural slides shall carry a dominant visual anchor
occupying 25–60% of usable page area. At least 40% shall use asymmetric
composition. No more than two consecutive slides may share the same layout
signature.

These are executable post-CompositionPlan/RenderPlan checks, not prose-only
guidance. The report shall expose the numerator, denominator, offending slide
IDs, and registered repair code for each failed threshold.

Evidence text is never truncated to satisfy a title slot. For non-CJK metric
evidence longer than 72 normalized characters, the compiler may use the
registered narrative role as the concise title only when the complete source
fact remains in the governed body/KPI/annotation content. This decision must
emit `LONG_EVIDENCE_TITLE_ROLE_FALLBACK` in the normalization evidence.

### P33-DESIGN-01 — Four DesignPack v2 contracts

`consulting-executive`, `product-launch-stage`,
`data-research-editorial`, and `institutional-annual-editorial` shall all use
schema 2.0 with distinct:

- palette roles and light/dark behavior;
- typography scale;
- grid, margin, and spacing system;
- motif family and variants;
- image crop and icon language;
- surface rules;
- energy pattern;
- quality thresholds;
- scenario coverage and safe fallback.

Together they shall cover all fifteen v5.1 scenarios.

### P33-DESIGN-02 — Art-direction floor

The first consulting tracer must satisfy all of:

- Quality v3 total score at least 84;
- every Quality v3 axis at least 75;
- direct Agnes verdict `PASS`;
- no Blocker or Important direct Agnes finding;
- no empty shell, placeholder, filler label, typo, or meaningless decoration;
- at least six layout signatures and three energy levels;
- editable fact coverage 1.0;
- all required asset intents materialized;
- PowerPoint package, LibreOffice render, PDF, and PNG proof succeed.

The threshold is necessary but not sufficient: visual comparison must also
show an authored anchor, hierarchy, and cadence comparable to the reference
method.

R6's frozen root-cause classes are: missing dominant anchors, flat section
rhythm, repetitive card shells, weak display hierarchy, disconnected process
geometry, under-authored evidence/data pages, and low asset polish. Red tests
shall prove that the new profile identifies these classes. Two bounded repair
passes apply to one candidate; they do not limit the number of separately
versioned design candidates that may be generated and reviewed.

### P33-WEAK-01 — Weak-model bounded choice

Ordinary models may choose scenario, semantic intent, fact references, and
one of at most three registered composition candidates. They may not emit raw
coordinates, colors, fonts, OOXML, executable code, or arbitrary layout IDs.
Low-confidence decisions use the DesignPack safe default and record why.

## Invariants

- Facts and derived facts retain their immutable digests.
- Text, data, charts, tables, and core diagrams remain native and editable.
- Generated imagery contains no business facts.
- The original reference and all prior R2–R6 evidence remain immutable.
- COM is optional certification only and is not a Phase 33 gate.
- HTML-to-PPT may be used for proof or ideation, not as the native editable
  delivery path.

## Verification

Focused tests must cover state transitions, provenance validation, invalid
bytes, dimension mismatch, provider failure, deterministic fallback, renderer
binding, pack v2 validation, composition diversity, protected facts, and
Quality v3 hard gates. The phase also requires a real PPTX evidence bundle,
per-slide PNGs, contact sheet, asset manifest, generation manifest, Quality v3
report, direct Agnes review, and exact hashes.
