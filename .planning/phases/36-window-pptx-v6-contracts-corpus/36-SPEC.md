# Phase 36: v6 Contracts and Realistic Corpus - Specification

**Created:** 2026-07-29
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Requirements:** 3

## Goal

Replace the shallow v5.1 benchmark contract with a discussion-locked,
source-bound ProjectBriefPack v1 and a realistic fifteen-scenario corpus that
can drive reference-grade template selection without invented facts.

## Background

The archived v5.1 worktree contains portable rendering, CompositionPlan,
Quality v3, asset materialization, and blind-review infrastructure, but the
user rejected its sparse generated decks. The fresh archive baseline collects
792 Python tests, with 789 passing and three known regressions. The current
fifteen-scenario benchmark averages few facts and usually has no mandatory
assets, so it cannot represent a real client request or reliably drive
reference-grade visual selection.

The user approved a v6 reset that first uses Codex GPT-5.5 medium, complete
realistic briefs, mandatory deck anatomy, and licensed complete-work visual
spines. Weak-model distillation is deferred to v6.1.

## Requirements

### V6-BRIEF-01: Discussion-Locked ProjectBriefPack

- **Source requests:** USR-V6-03, USR-V6-04, USR-V6-10
- **Current:** v5 brief inputs do not require a complete audience, decision,
  source, asset, anatomy, prohibition, rubric, and discussion-lock contract.
- **Target:** ProjectBriefPack v1 owns RawIntakeManifest, facts, sources,
  assets, audience, goals, timing, brand constraints, slide budget, anatomy,
  decisions, prohibitions, rubric, unresolved questions, state, and lock hash.
- **Acceptance:** `Draft` and `NeedsDiscussion` formal generation fail and
  emit discussion questions only; a complete `Locked` pack validates and
  produces a stable digest.

### V6-CORPUS-01: Realistic Fifteen-Scenario Corpus

- **Source requests:** USR-V6-03, USR-V6-04, USR-V6-06
- **Current:** existing scenarios average few facts, lack required assets, and
  produce short sparse decks without realistic customer constraints.
- **Target:** three complete flagships and twelve locked skeletons cover all
  accepted business, campus, research, training, brand, and marketing
  scenarios with detailed facts, sources, materials, copy direction, decisions,
  deck anatomy, and acceptance rubrics.
- **Acceptance:** all fifteen packs validate; every accepted flagship number,
  source boundary, asset role, slide budget, decision, limitation, and
  prohibited claim is present and hash-bound.

### V6-DOC-01: Executable Quality-First Skill Contract

- **Source requests:** USR-V6-01, USR-V6-02, USR-V6-05, USR-V6-07,
  USR-V6-08, USR-V6-09, USR-V6-10
- **Current:** the Skill still defaults to v5 ordinary-model and human-review
  assumptions and does not expose the v6 brief or private-library workflow.
- **Target:** the Skill routes default generation through the quality-first
  GPT-5.5 workflow and documents discussion lock, private acquisition,
  template intelligence, native output, bounded repair, AI-only review,
  failure behavior, and evidence bundle.
- **Acceptance:** Skill formatting and behavior evals pass; no default path
  claims that v5.1, COM, HTML conversion, or human scoring owns v6 delivery.

## Boundaries

### In Scope

- v6 planning state, request ledger, requirements, and Phase 36 evidence;
- private-asset ignore and staged secret/binary guard;
- ProjectBriefPack v1 schema, state transitions, validator, CLI, and tests;
- tracked synthetic scenario facts, sources, asset requirements, lock reports,
  and acceptance rubrics;
- repair of the three archived deterministic regression failures.

### Out Of Scope

- authenticated Gaojie acquisition, which begins in Phase 37;
- TemplatePack v2 materialization and Registry v3, which begin in Phase 38;
- final GPT-5.5 deck generation and AI-only release scoring;
- weak-model distillation, which belongs to v6.1.

## Constraints

- Facts, units, dates, academic results, limitations, and sources are
  immutable after lock.
- Private bytes and credentials never enter git, command arguments, logs, or
  evidence.
- The v5.1 archive and original v5 branch remain unchanged.
- Native-editable portable PPTX remains canonical; COM is optional diagnostics
  and HTML remains proof-only.
- Synthetic business and campus facts are labeled synthetic; public academic
  metadata receives real citations and no unsupported SOTA claim.
- Work on the Windows-mounted filesystem uses test shards when monolithic
  commands exceed the five-minute tool limit.

## Engineering Contract

- **Domain terms and owners:** ProjectBriefPack owns intake and lock state;
  FactStore owns immutable content; SourceManifest and AssetManifest own
  provenance and rights; the project CLI owns normalization and lock commands.
- **Invariants:** Formal output requires `Locked`; every claim links to facts
  or sources; lock digest changes on any authoritative input change; private
  paths and secret literals fail closed.
- **Interfaces and compatibility:** New v1 schemas and project CLI are
  additive. Existing BriefPlan, DeckPlan, RenderPlan, and legacy CLI exports
  remain available during expand-contract migration.
- **Failure semantics:** Invalid or unresolved input returns structured
  questions/findings and produces no formal plan or PPTX.
- **Migration and rollback:** v6 runs on its feature branch. The immutable v5.1
  archive/tag is the rollback and comparison point.

## Test Seams And Critical Cases

| Behavior | Observable Seam | Failing Case | Evidence |
|---|---|---|---|
| V6-BRIEF-01 | ProjectBriefPack validator and CLI | Draft pack passed to formal plan | Focused state/CLI tests |
| V6-CORPUS-01 | Corpus loader and schema validation | Missing flagship metric, source, asset, or anatomy role | Fifteen-pack corpus test |
| V6-DOC-01 | Skill workflow and formatter | Stale human-review or ordinary-model default | Skill eval and formatter |
| Safety enabling work | staged-asset guard CLI | `.private`, credential literal, key, or binary staged | Guard unit and temp-git tests |
| Archived regressions | existing public generation/quality seams | CTA, trend label, or calibration failure remains | Three focused regression tests |

## Acceptance Criteria

- [ ] V6-BRIEF-01 has concrete passing evidence.
- [ ] V6-CORPUS-01 has concrete passing evidence.
- [ ] V6-DOC-01 has concrete passing evidence.
- [ ] The staged-secret guard passes its focused and staged-index tests.
- [ ] The three archived regression tests pass without weakening Quality v3.
- [ ] All Window-PPTX tests, Vitest, typecheck, build, formatter, and diff
      checks pass.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.98
- **Boundary clarity:** 0.96
- **Constraint clarity:** 0.95
- **Acceptance clarity:** 0.97
- **Ambiguity:** 0.035

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | Reality | Why did v5.1 fail despite automatic passes? | Visual evidence showed sparse, repetitive, shallow decks and unrealistic briefs |
| 2 | Simplification | Which model owns v6.0? | Codex GPT-5.5 medium first; weak models move to v6.1 |
| 3 | Boundary | Is COM required? | No; portable native PPTX is canonical and COM is optional diagnostics |
| 4 | Content | What counts as a real requirement? | A complete synthetic standardized client brief with detailed facts, sources, assets, copy direction, and decisions |
| 5 | Review | Who scores release quality? | Three independent fresh visual-capable AIs; no human score or override |
| 6 | Security | How are commercial templates handled? | Entitled assets remain private, ignored, rights-bound, quarantined, and never committed by default |
