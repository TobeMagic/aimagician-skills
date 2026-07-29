# Phase 39: Work-Report Flagship Tracer - Specification

**Created:** 2026-07-30
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Depends on:** Phase 38
**Requirements:** 5

## Goal

Generate, render, and verify a complete 28-main plus 4-appendix annual work
report from a locked realistic brief. The output must preserve the accepted
reference's art-direction maturity while remaining native-editable and
portable without mandatory PowerPoint COM.

## Background

Phase 38 supplies certified complete-work spines and bounded template
selection. This phase proves that those contracts can produce a customer-grade
work report instead of a structurally valid but visually shallow slide deck.

## Requirements

### V6-DESIGN-01: Governed Art Direction

- **Source requests:** USR-V6-01, USR-V6-02, USR-V6-06
- **Current:** A structurally valid renderer can still depend on model taste.
- **Target:** Certified spines and registered native compositions own design.
- **Acceptance:** Unknown styles, raw geometry, and arbitrary code fail closed.

The renderer must use the certified institutional work-summary spine, locked
facts, stable page roles, and governed native compositions. Models may choose
registered IDs but may not emit coordinates, OOXML, HTML, or arbitrary style.

### V6-DECK-01: Complete Work-Report Anatomy

- **Source requests:** USR-V6-04, USR-V6-06, USR-V6-07
- **Current:** Generic generation can omit directory, sections, and cadence.
- **Target:** The complete 32-slide anatomy is explicit and enforced.
- **Acceptance:** Exact anatomy and page-role diversity tests pass.

The deck must contain cover, directory, four functional section dividers,
evidence pages, three distinct case-study treatments, organization and risk,
priorities, roadmap, decision ask, closing, and four appendices.

### V6-PORT-01: Native Portable PPTX

- **Source requests:** USR-V6-01, USR-V6-03, USR-V6-08
- **Current:** COM-dependent proof is unavailable and non-portable.
- **Target:** Native PPTX renders without mandatory COM.
- **Acceptance:** Isolated PDF/PNG proof and editability checks pass.

All slides must open and render through the portable LibreOffice/Poppler path.
Charts, tables, diagrams, and text remain native-editable; whole-slide
rasterization and external relationships are forbidden.

### V6-QA-01: Bounded Quality Closure

- **Source requests:** USR-V6-01, USR-V6-07, USR-V6-09
- **Current:** Broad repair can accumulate redundant component fixes.
- **Target:** Deterministic checks and bounded visual replanning own closure.
- **Acceptance:** Unresolved defects reject instead of looping indefinitely.

Generation uses deterministic checks and bounded visual replanning. Failed
rendering, lineage, anatomy, editability, or visual findings reject the
candidate instead of triggering open-ended component repair.

### V6-EVID-01: Reproducible Evidence

- **Source requests:** USR-V6-01, USR-V6-08, USR-V6-09
- **Current:** Automatic scores can hide visible failures.
- **Target:** Every candidate is hash-bound to complete visual evidence.
- **Acceptance:** PPTX/PDF/PNG/manifests/lineage reproduce exactly.

The accepted deck carries PPTX, manifest, PDF, physical-slide PNGs, contact
sheets, hashes, source-brief lineage, notes lineage, and anonymous visual
review evidence.

## Boundaries

### In Scope

- the 32-slide annual work-report generator and focused tests;
- locked fact bindings, native charts/tables/diagrams, notes, manifests, and
  isolated portable rendering;
- visual iteration required by the shared Phase 41 gate.

### Out Of Scope

- unsupported customer, financial, award, or market claims;
- private commercial bytes, mandatory COM, canonical HTML-to-PPTX, arbitrary
  cross-deck OOXML import, or whole-slide screenshots;
- campus and academic flagships, owned by Phase 40.

## Constraints

- Only the locked annual work-report ProjectBriefPack may supply claims.
- The flagship has exactly 32 slides: 28 main plus four appendix.
- The deck contains at least eight native charts and two native tables.
- The accepted reference guides hierarchy, motif, rhythm, and finish; it is
  not copied as unrelated content or organization identity.
- Portable output is canonical and PowerPoint COM is optional diagnostics.

## Acceptance Criteria

- [x] Exact slide count, full anatomy, case diversity, and fact-bound notes
      pass deterministic tests.
- [x] The PPTX opens in the isolated portable renderer with no missing page.
- [x] No slide picture, unsupported external relationship, or unsupported
      factual claim exists.
- [x] Native chart/table floors and editable object expectations pass.
- [x] Anonymous visual acceptance reaches the frozen Phase 41 thresholds with
      no consensus Blocker or Important finding.
- [x] Workflow, regression, private-asset, and diff gates pass.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.99
- **Boundary clarity:** 0.98
- **Constraint clarity:** 0.98
- **Acceptance clarity:** 0.98
- **Ambiguity:** 0.02

## Decision Log

| Round | Decision |
|---:|---|
| 1 | Use one complete 32-slide tracer, not isolated template screenshots |
| 2 | Preserve reference-level hierarchy and rhythm without copying its content |
| 3 | Keep native PPTX canonical; COM remains optional |
| 4 | Require visual acceptance in addition to engineering checks |
