# Phase 45: Selection-to-Materialization Bridge - Specification

**Created:** 2026-07-30
**Status:** Locked
**Risk:** high
**User-facing:** no
**Requirements:** 1
**Original requests:** USR-V6-11

## Goal

Make production generation consume TemplateSelectionPlan and SlideBlueprint and prove the selected physical/native candidates were actually materialized.

## Background

Template intelligence currently selects candidates in tests only. Production
can render a different native layout or adapt a physical pack without any
selection lineage.

## Requirements

### V6R-MAT-01: Exact selected-candidate materialization

- **Source requests:** USR-V6-11
- **Current:** Selection and execution are disconnected.
- **Target:** Every selected candidate drives its declared engine and produces
  exact evidence.
- **Acceptance:** GOAL-45-01 through GOAL-45-04 pass.

## Boundaries

### In Scope

Registered-native exact layout binding, physical whole-pack adaptation,
evidence, production artifact emission, and fail-closed tests.

### Out Of Scope

- Arbitrary multi-source OOXML slide relationship merging.
- Auto-materializing Phase 44 reference-only pages.
- Claiming the whole private 288-page core is already connected to production.

## Constraints

- One materializer per run.
- PASS requires observed output, not planning metadata.
- No native fallback after an exact selection.
- Every selection has exactly one evidence item.

## Acceptance Criteria

- [ ] V6R-MAT-01 has passing evidence for GOAL-45-01 through GOAL-45-04.

- **GOAL-45-01:** Brief generation builds and serializes a deterministic
  selection plan and complete blueprints for supported certified spines.
- **GOAL-45-02:** Registered-native selections force the exact registered
  variant; missing variants, fallback, or observed mismatch fail closed.
- **GOAL-45-03:** Physical selections execute only through the hash-bound
  TemplatePack adapter and emit per-slide source/output evidence.
- **GOAL-45-04:** Unknown, uncertified, unmaterialized, reference-only, mixed
  materializer, drift, and incomplete evidence paths fail; focused and
  regression tests plus fresh independent completion audit pass.

## Engineering Contract

Each evidence item contains slide ID, candidate ID, spine ID, source mode,
materializer, expected variant or physical slide, observed output slide/layout,
source digest, output digest when available, and status. Overall PASS requires
one PASS item per selection with no fallback.

Production writes versioned `template-selection-plan.json`,
`slide-blueprints.json`, and `candidate-materialization-report.json` beside the
existing generation audit artifacts. Their schemas are `1.0`; the generation
manifest embeds the same canonical payloads so a missing sidecar is detectable.

Registered validation resolves `base_variant_id` against the governed layout
registry before compilation (`MATERIALIZER_VARIANT_UNKNOWN`), rejects a
non-native blueprint on the native route (`MATERIALIZER_KIND_MISMATCH`), and
compares every observed `RenderSlide.layout_id` after compilation
(`MATERIALIZER_VARIANT_MISMATCH`). There is no fallback after exact binding.

Physical validation requires one spine and one materializer
(`MATERIALIZER_MIXED_PLAN`), a known physical slide for every selection
(`MATERIALIZER_PHYSICAL_SLIDE_UNKNOWN`), stable source digest
(`MATERIALIZER_SOURCE_DRIFT`), successful atomic adaptation
(`MATERIALIZER_ADAPTATION_FAILED`), and one output/evidence item per selection
(`MATERIALIZER_EVIDENCE_INCOMPLETE`). More than one physical spine is rejected;
the current registry exposes one.

Auto mode preserves compatibility for scenarios without a certified spine by
emitting no selection. Once a spine or explicit choice is present, all
materialization rules are mandatory.

The single consistency checkpoint is report construction after the declared
engine finishes: evidence IDs and cardinality must exactly equal selection
IDs; expected candidate fields must equal observed engine output; source and
output evidence must be stable. Only that checkpoint can change `planned` to
`pass`.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.96
- **Boundary clarity:** 0.95
- **Constraint clarity:** 0.96
- **Acceptance clarity:** 0.95
- **Ambiguity:** 0.04

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | Evidence | Is a candidate ID proof? | No; observed output is required. |
| 2 | Native | May exact selection fall back? | No; fail closed. |
| 3 | Physical | May physical/native mix? | No; current engines cannot prove it. |
| 4 | Compatibility | What happens without a certified spine? | Auto mode skips; explicit selection stays strict. |
