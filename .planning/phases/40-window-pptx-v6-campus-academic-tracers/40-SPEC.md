# Phase 40: Campus and Academic Flagship Tracers - Specification

**Created:** 2026-07-30
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Depends on:** Phase 39
**Requirements:** 4

## Goal

Generate and verify two complete 32-slide native-editable flagships: a campus
competition defense and an academic thesis defense. Each must have its own
scenario-specific visual grammar, evidence chain, and complete presentation
anatomy at the reference art-direction level.

## Background

A strong work-report style cannot be stretched across unrelated scenarios.
The user requires real campus competition and academic defense briefs with
detailed facts, data, limitations, appendices, and decision contracts. This
phase proves that certified first-party spines deliver that range.

## Requirements

### V6-PORT-01: Native Scenario Tracers

- **Source requests:** USR-V6-01, USR-V6-03, USR-V6-04
- **Current:** Scenario decks can collapse into generic templates.
- **Target:** Two scenario-specific native-editable 32-slide tracers.
- **Acceptance:** Exact anatomy, object, lineage, and claim guards pass.

Both flagships materialize as native PPTX with editable shapes, charts,
tables, maps, diagrams, and notes. Whole-slide rasterization and unsupported
external relationships fail closed.

### V6-PORT-02: Portable Reliability

- **Source requests:** USR-V6-01, USR-V6-03, USR-V6-08
- **Current:** Cross-engine completion evidence is incomplete.
- **Target:** Isolated repeated portable rendering covers every page.
- **Acceptance:** Both decks produce stable 32-page PDF/PNG proof.

Both outputs render all 32 pages through isolated LibreOffice and Poppler with
stable paths, fonts, aspect ratio, source protection, and repeated-run safety.

### V6-QA-01: Scenario-Specific Bounded Repair

- **Source requests:** USR-V6-01, USR-V6-07, USR-V6-09
- **Current:** Repeated generic cards and broad repair lower visual quality.
- **Target:** Semantic page types and bounded replanning replace generic fixes.
- **Acceptance:** Unresolved visual or factual defects reject the candidate.

The campus and academic spines use semantic page types and at most bounded
replanning. Generic repeated cards, unresolved overflow, unsupported facts,
or damaged native objects reject the candidate.

### V6-EVID-01: Complete Visual And Structural Evidence

- **Source requests:** USR-V6-01, USR-V6-08, USR-V6-09
- **Current:** Trial evidence is not sufficient for customer acceptance.
- **Target:** Every artifact is hash-bound to lineage and physical-page proof.
- **Acceptance:** Both evidence bundles reproduce and rehash successfully.

Each output retains PPTX, PDF, PNGs, contact sheets, manifests, hashes, locked
brief lineage, notes lineage, structural/editability proof, and anonymous
visual-review evidence.

## Boundaries

### In Scope

- campus: 22 main, four appendix, and six Q&A pages with map, product,
  prototype, pilot, business model, market boundary, risk, roadmap, and ask;
- academic: 26 main and six appendix pages with GAP/RQ mapping, dataset,
  method, experiments, ablation, robustness, efficiency, limits, and close;
- scenario-specific native compositions and focused regression tests.

### Out Of Scope

- invented campus coordinates, customers, patents, awards, orders, published
  SOTA status, causal certainty, or deployment evidence;
- screenshot mockups presented as real products;
- mandatory COM, canonical HTML conversion, and private unlicensed assets.

## Constraints

- Only locked ProjectBriefPack facts and declared public sources are allowed.
- Each deck contains exactly 32 slides.
- Campus Q&A pages must vary by question semantics while retaining one brand.
- Academic claims must distinguish synthetic evaluation logs from publication
  evidence and must keep limitations in the main deck.
- Native portable PPTX is canonical.

## Acceptance Criteria

- [ ] Both exact anatomy contracts and locked fact lineages pass.
- [ ] Scenario-specific maps, product visuals, experiment diagrams, charts,
      tables, appendices, and closes are present and editable.
- [ ] Isolated portable rendering produces 32 valid pages for each deck.
- [ ] No unsupported commercial, scientific, award, patent, or causal claim
      is present.
- [ ] Anonymous visual acceptance reaches all Phase 41 floors with no
      consensus Blocker or Important finding.
- [ ] Workflow, regression, private-asset, and diff gates pass.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.99
- **Boundary clarity:** 0.98
- **Constraint clarity:** 0.99
- **Acceptance clarity:** 0.98
- **Ambiguity:** 0.018

## Decision Log

| Round | Decision |
|---:|---|
| 1 | Use separate campus and academic art-direction spines |
| 2 | Keep realistic limitations and decision requests in the main decks |
| 3 | Use native editable visualizations rather than screenshot products |
| 4 | Accept only after shared blind visual review |
