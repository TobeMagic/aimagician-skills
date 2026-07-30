# Phase 46: Three Reference-Grade Anchors - Specification

**Created:** 2026-07-30
**Status:** Complete
**Risk:** high
**User-facing:** yes
**Requirements:** 1
**Original requests:** USR-V6-06, USR-V6-11

## Goal

Regenerate work-report, campus-competition, and academic-defense anchors from actual certified candidates at the reference art-direction level.

## Background

The former three flagships are editable and portable but visually rejected.
They use metadata-only spine labels and a repeated rounded-card grammar. Phase
45 now guarantees candidate-to-output truth; Phase 46 must convert that
foundation into actual reference-grade complete works.

## Requirements

### V6R-ANCHOR-01: Three reference-grade editable anchors

- **Source requests:** USR-V6-06, USR-V6-11
- **Current:** Three 32-slide engineering artifacts are visually generic and
  do not show the supplied reference or excellent-work influence.
- **Target:** Three complete editable decks use certified candidates and
  authorized assets, preserve materialization truth, and pass independent
  reference-grade pixel review.
- **Acceptance:** GOAL-46-01 through GOAL-46-04 pass.

## Boundaries

### In Scope

- New anchor art-direction blueprints and composition engine.
- Bounded certified private media/motif reuse with digest provenance.
- Work-summary, campus-competition, and academic-defense artifacts.
- Portable rendering, editability/OOXML checks, contact sheets, and repeated
  independent AI visual review.

### Out Of Scope

- Fifteen-scenario ordinary-model expansion (Phase 47).
- Redistribution of private source packages or extracted media.
- Claiming reference-only pages were materialized.
- Whole-slide raster output or mandatory PowerPoint COM.

## Constraints

- Every anchor has cover, directory, section pages, body, conclusion/decision,
  and closing.
- Every selected candidate or reused media asset has provenance and SHA-256.
- Reference-only pages can influence art direction but never direct output.
- No more than two consecutive pages use the same composition family.
- Each deck includes native editable text, shapes, chart, table or diagram.
- Any fresh visual Blocker or Important rejects the candidate.

## Acceptance Criteria

- [x] **GOAL-46-01:** Each anchor has a real locked brief, complete commercial
  anatomy, and an explicit page-by-page art-direction blueprint.
- [x] **GOAL-46-02:** Every anchor consumes certified physical/native
  candidates with exact materialization evidence and uses the private
  reference-only pool only as non-materialized art-direction guidance.
- [x] **GOAL-46-03:** The three PPTX files remain editable, open and render
  portably, and pass structural, geometry, typography, asset, and artifact
  gates.
- [x] **GOAL-46-04:** Three fresh independent visual-capable AI contexts find
  no unresolved Blocker or Important and judge the anchors at reference-grade
  art-direction quality.

## Engineering Contract

An `AnchorDeckBlueprint` records scenario, slide order, narrative role,
composition family, density, focal hierarchy, candidate ID, materializer or
influence-only policy, authorized media references, motif, typography mode,
chart/diagram intent, and fact references. Models choose semantic content only;
coordinates, type scale, palette, crop, and composition are governed.

The engine emits the blueprint, candidate/asset provenance, native-editability
inspection, portable render report, per-page PNGs, contact sheet, artifact
manifest, and visual review packet. A reference-only influence record is never
eligible for materialization PASS.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.97
- **Boundary clarity:** 0.95
- **Constraint clarity:** 0.96
- **Acceptance clarity:** 0.95
- **Ambiguity:** 0.04

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | Visual | Repair old flagships or rebuild grammar? | Build a new anchor-specific engine. |
| 2 | Assets | May private media be used? | Yes, locally, with digest provenance and no redistribution. |
| 3 | Editability | May pages be flattened? | No; photos may be images, but text/charts/diagrams remain native. |
| 4 | Sequence | Build all three immediately? | Prove the work-summary slice first, then expand without lowering the gate. |
