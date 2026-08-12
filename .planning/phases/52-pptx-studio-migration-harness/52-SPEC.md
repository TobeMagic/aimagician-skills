# Phase 52: PPTX Studio Migration and Agent Workflow — Specification

**Created:** 2026-08-12
**Milestone:** v7 PPTX Studio Curated Composition
**Roadmap phase:** 52
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Requirements:** 3
**Requirement IDs:** V7-SKILL-01, V7-QA-01, V7-MIGRATE-01

## Goal

Ship the concise `pptx-studio` owned Skill and harness: requirement

## Background

Phase 50 supplies curated pages/regions and Phase 51 supplies locked,
value-safe selection/adaptation plans. Existing v6.1 cross-package OPC
assembly is proven for a fixed profile but it consumes a different page-library
contract. The public `window-pptx` skill remains large and historical, so it
cannot be renamed/deleted until a new source/install behavior is exercised.

## Requirements

### V7-SKILL-01: Concise governed agent workflow

- **Source requests:** USR-V7-01
- **Current:** agent instructions mix historic routes and do not expose the
  Phase 50/51 selection-to-plan capability as the default workflow.
- **Target:** `pptx-studio` documents a strict client discussion/brief lock,
  art direction, bounded query, composition, adaptation, assembly, QA/repair
  and release path with safe defaults for a mid/high-tier model.
- **Acceptance:** a trigger/eval routes presentation production to the new
  concise workflow; it asks questions for incomplete briefs and never exposes
  raw geometry/code/release authority.

### V7-QA-01: Evidence-bound assembly quality and repair

- **Source requests:** USR-V7-01
- **Current:** v6.1 physical QA exists but is not attached to Phase 51 plan
  lineage and does not return a bounded repair decision.
- **Target:** one harness validates source lineage, editability, package open,
  bounds, overflow/clipping, overlap, typography, image deformation, page
  density/repetition and style coherence; it applies only declared safe repairs
  or stops with an actionable failure.
- **Acceptance:** deliberate fixtures for each blocking class fail or repair
  within policy and preserve plan/output lineage.

### V7-MIGRATE-01: Flag-day public identity migration

- **Source requests:** USR-V7-01
- **Current:** source/install identity remains `window-pptx`.
- **Target:** after source and installed `pptx-studio` workflow tests pass,
  rename the owned Skill and configuration/install ownership; delete the old
  production tree with no compatibility shim.
- **Acceptance:** no tracked `window-pptx` production entry point remains,
  source/install digest parity passes, and private roots remain ignored.

## Boundaries

### In Scope

- Adapter from validated Phase 51 plans to the existing portable physical OPC
  assembler; source-hash/slide/slot mapping is local and deterministic.
- Plan-aware QA/repair harness and concise source Skill, then install parity.
- Flag-day source-tree migration only after all preceding checks pass.

### Out Of Scope

- Final 15-slide clean-room work-report acceptance and three fresh visual
  reviews (Phase 53); commercial/private asset publication; COM dependence.

## Constraints

- Physical reuse remains editable and portable; COM may certify but never
  blocks delivery.
- Model output is IDs/facts/assets only; all slot and geometry resolution is
  compiler-owned.
- Migration is last and atomic: no `window-pptx` compatibility shell.

## Engineering Contract

- **Invariants:** every output slide maps to a Phase 51 source/hash/slide;
  text binds only declared slots; repair cannot add geometry or rewrite source;
  source and installed skill files have matching digests.
- **Failure semantics:** ambiguous mapping, source drift, unsupported asset
  replacement, QA blocker or install mismatch stops before promotion.
- **Rollback:** prior committed `window-pptx` state remains recoverable by Git
  until Phase 53 acceptance; private source/archive never changes.

## Test Seams And Critical Cases

| Behavior | Seam | Failing case | Evidence |
|---|---|---|---|
| plan-to-physical adapter | source/slot resolver | hash/slide/slot mismatch or free-text plan | adapter tests |
| QA and repair | rule-harness report | overflow, overlap, tiny text, deformation, style drift | fixture tests |
| migration | source/install parity | stale old path or digest divergence | migration tests |

## Acceptance Criteria

- [ ] AC-52-01: validated composition/adaptation plans materialize editable
  physical PPTX with complete source/slot lineage and no free-form fallback.
- [ ] AC-52-02: quality/repair harness rejects or safely repairs declared
  structural and visual failure fixtures with evidence.
- [ ] AC-52-03: concise skill workflow enforces discuss/brief lock and bounded
  progressive retrieval for a capable agent.
- [ ] AC-52-04: `pptx-studio` source/install parity passes and old production
  `window-pptx` identity is removed only after migration validation/audit.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.92
- **Boundary clarity:** 0.94
- **Constraint clarity:** 0.94
- **Acceptance clarity:** 0.91
- **Ambiguity:** 0.07

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | delivery | Must COM become a production dependency? | No; portable OPC path is default, COM stays optional certification. |
| 2 | migration | Can `window-pptx` remain a shim? | No; delete only after source/install parity and migration tests pass. |
| 3 | assembly | How are private source paths protected? | Resolve package SHA only below an operator-configured private root; lineage contains hashes/IDs, never paths or literal client copy. |
| 4 | repair | Which repairs may mutate an output? | Only compiler-owned slot `shrink-to-fit` before import; all other defects force replan/reassembly. |
