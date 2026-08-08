# Phase 46 Research

**Status:** Complete
**Date:** 2026-07-30

## Objective

Determine the smallest safe architecture that can produce a visible
reference-grade step-change while preserving editable PPTX and materialization
truth.

## Local Evidence

- The 15-slide user reference contact sheet and individual rendered pages.
- The rejected 32-slide work-report, campus, and academic contact sheets.
- All seven final 129-page direct-use contact sheets.
- The private certified-core v2 role/pool inventory.
- The Phase 45 selection/materialization bridge.
- The existing monolithic flagship PptxGenJS generator and locked briefs.

Two attempted OpenCode research runs were excluded: the first used invalid
Read arguments; the second violated its evidence-only protocol by calling
WebFetch. Neither result influenced this decision.

## Finding

The visual gap is architectural, not a repair-list problem.

The old generator's dominant grammar is a header plus repeated rounded cards.
It is consistent and editable, but its cover, chapters, metrics, cases,
diagrams, tables, and appendices share too much geometry. It cannot reach the
reference by adjusting colors, shadows, or repair thresholds.

The accepted reference instead uses:

- oversized expressive Chinese display typography;
- photo-led cover and closing;
- a distinctive recurring diagonal/radial motif;
- chapter pages that reset scale and density;
- native charts embedded into composed editorial scenes;
- illustration, iconography, and contextual photography;
- deliberate alternation among sparse, medium, and dense pages;
- strong page-specific compositions inside one coherent design language.

The direct-use private pool supplies useful art-direction and editable asset
sources, but many entries are isolated one-slide packs and share a blue
corporate style. Blindly importing them would make the three anchors look
unrelated and would not reproduce the reference's complete-work coherence.

## Architecture decision

Choose route D:

1. Build a new anchor-specific art-direction blueprint and composition engine.
2. Reuse certified private source media and design primitives in bounded,
   provenance-recorded ways.
3. Keep exact candidate materialization evidence distinct from art-direction
   influence evidence.
4. Defer arbitrary multi-source OOXML relationship merging unless the new
   engine cannot meet the visual gate without it.

Do not extend the old monolithic flagship generator as the primary route.
Retain it as the rejected baseline and regression fixture.

## Options

- A: extend the old monolithic flagship generator — rejected because its
  repeated-card grammar is the principal visual defect.
- B: build a new anchor blueprint/composition engine — selected as the core.
- C: implement arbitrary multi-source OOXML slide import first — deferred
  because relationship cloning adds high risk before proving the visual
  grammar.
- D: combine B with bounded certified media/motif reuse and add controlled
  import later only if required — selected overall.

## Recommendation

Implement D. Prove it on the 15-slide work-summary, then scale the accepted
grammar into distinct campus and academic directions.

## Assumptions To Confirm

- Local private asset use remains authorized and non-redistributable.
- Portable rendering remains the canonical acceptance route.
- The visual gate, not preservation of the old 32-slide count, determines the
  first anchor's page count.

## First execution slice

Regenerate the 15-slide annual work-summary first because it has an exact
15-slide reference:

- cover;
- directory;
- four section dividers;
- financial overview;
- variance/trend;
- expense table;
- capital-project scene;
- KPI dashboard;
- organization/innovation illustration;
- clinical coverage/data map;
- forward plan;
- closing.

The slice must visibly demonstrate hero imagery, oversized Chinese type,
gold/green motif continuity, native charts/tables, mixed density, and exact
asset/candidate provenance before campus and academic expansion.

## Test and evidence strategy

- blueprint schema and deterministic compilation tests;
- private source digest and candidate policy tests;
- no whole-slide rasterization;
- editable native text/shape/chart/table inspection;
- portable LibreOffice/Poppler rendering;
- exact slide count, required anatomy, and output hash manifest;
- contact sheets and page-level PNGs;
- candidate influence/materialization report;
- three fresh independent visual-capable AI reviews, with any Blocker or
  Important blocking completion.
