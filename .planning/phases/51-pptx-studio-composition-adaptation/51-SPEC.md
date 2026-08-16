# Phase 51: Composition Retrieval and Governed Adaptation — Specification

**Created:** 2026-08-12
**Milestone:** v7 PPTX Studio Curated Composition
**Roadmap phase:** 51
**Status:** Locked
**Risk:** High
**User-facing:** no
**Requirements:** 2
**Requirement IDs:** V7-COMPOSE-01, V7-ADAPT-01

## Goal

Make the curated catalog choose an exact deck, a coherent set of

## Background

Phase 50 supplies a local-only catalog of safe deck/page/region candidates,
render-backed visual observations and deterministic role retrieval. It does
not choose a reusable whole deck versus coherent page set versus component,
does not lock a visual direction, and does not make model fact choices safe to
materialize. v6.1 proves physical full-page assembly but not flexible,
catalog-governed composition.

## Requirements

### V7-COMPOSE-01: Deterministic composition mode and art direction

- **Source requests:** USR-V7-01
- **Current:** page and region queries are independent and can yield visually
  incompatible candidates or accidental component overuse.
- **Target:** an explicit composition request selects exactly one mode per
  target slide: `exact_deck`, `page`, or `component`. It locks an anchor page
  and a declared allowlist of catalog-derived style signatures. Selection is
  deterministic, capacity-aware, provenance-complete and bounded.
- **Acceptance:** exact-deck reuse is preferred when an ordered source deck
  covers the requested roles; otherwise page reuse is preferred; component
  reuse is allowed only when explicitly requested and a safe eligible region
  exists. Unknown candidates, style drift, duplicate source positions,
  insufficient capacity and unregistered source categories fail closed.

### V7-ADAPT-01: Fact-bound governed adaptation plan

- **Source requests:** USR-V7-01
- **Current:** no portable contract constrains an authoring model's content
  replacements to declared source regions, capacities and client inputs.
- **Target:** compile a composition decision plus named fact and asset
  registry into an adaptation plan that contains only source IDs, declared
  region IDs, named fact/asset IDs and safe operation kinds. It carries source
  hashes and style-lock evidence, but no raw OOXML, geometry, font, color, or
  free-form text fields.
- **Acceptance:** every content binding resolves to an eligible selected page
  or component region, has sufficient declared capacity, uses a known fact or
  asset, and matches the selection mode. Unsupported operation, unbound text,
  raw visual implementation field, duplicate target, source mutation or style
  violation fails before any materializer is called.

## Boundaries

### In Scope

- Pure local selection and adaptation compiler under `scripts/pptx_studio/`.
- Versioned request/result schemas and CLI commands that consume compiled
  catalog/observation JSON only.
- Stable source, page, region, fact, asset and style-signature provenance.
- Focused synthetic fixtures and an actual private local smoke composition.

### Out Of Scope

- Importing or writing PPTX packages, OOXML slot replacement, public Skill
  rename, installed Skill synchronization, final QA/repair, or clean-room
  client generation. These are Phases 52–53.
- Scanning client folders, calling a model, reading private files from a query,
  or sending data externally.

## Constraints

- Private assets remain ignored/local; tracked artifacts contain only schemas,
  code, synthetic tests and sanitized counts/digests.
- Source category metadata remains stronger than vision prose for structural
  roles; visual descriptions only enrich compatibility.
- A style fallback must be declared explicitly by a caller as a catalog-derived
  signature; it is never inferred or randomly selected.
- Whole-page selection retains a source page exactly once per target slide;
  physical assembly is deferred to a later phase.

## Engineering Contract

- **Domain terms and owners:** `CompositionRequest` is model/agent input;
  `CompositionPlan` is compiler output; `FactRegistry`/`AssetRegistry` are
  locked client inputs; `GovernedAdaptationPlan` is materializer input.
- **Invariants:** one target-slide ID per decision; candidate IDs must resolve
  in the supplied catalog; every selected page observes active scope and the
  locked style signature; source identities are preserved; no operation can
  change a source or geometry/style primitive.
- **Interfaces and compatibility:** Phase 51 reads `pptx-studio-catalog.v1`
  and Phase 50 observations. It adds composition/adaptation v1 contracts but
  does not alter v6.1 APIs or installed Skill behavior.
- **Failure semantics:** `CompositionError` or `AdaptationError` with stable
  codes; no best-effort fallback, filesystem discovery, or output write.
- **Migration and rollback:** all changes are additive in `pptx_studio`; a
  normal Git revert restores the Phase 50-only state without touching private
  source/archive state.

## Test Seams And Critical Cases

| Behavior | Observable seam | Failing case | Evidence |
|---|---|---|---|
| mode hierarchy | `compile_composition` | exact deck incomplete, candidate/page mismatch, duplicate source position | composition tests |
| art-direction lock | `style_signature` / compiler | undeclared signature, incompatible fallback, missing observation | composition tests |
| safe adaptation | `compile_adaptation` | raw geometry/color/text, unknown fact/asset/region, capacity overflow | adaptation tests |
| deterministic CLI | `compose` / `adapt` commands | repeated serialized request differs, private/client locator supplied | CLI smoke + focused tests |

## Acceptance Criteria

- [x] AC-51-01: composition is deterministic, bounded and produces ordered
  exact-deck/page/component decisions with stable candidate provenance.
- [x] AC-51-02: one catalog-derived art-direction signature is locked and any
  cross-signature use is explicitly allowlisted, recorded and test-covered.
- [x] AC-51-03: adaptation plans bind only declared fact/asset IDs to safe
  selected page/region targets with capacity evidence; prohibited fields fail.
- [x] AC-51-04: focused tests, local smoke composition and a fresh independent
  audit have no unresolved Blocker or Important finding.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.95
- **Boundary clarity:** 0.95
- **Constraint clarity:** 0.94
- **Acceptance clarity:** 0.93
- **Ambiguity:** 0.06

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | capability boundary | How can model choice remain flexible without raw design authority? | Accept only bounded candidate and registry IDs; compiler owns compatibility and validation. |
| 2 | style direction | How is coherent art direction preserved across reused pages? | Lock a catalog-derived anchor signature with explicit fallback signatures only. |
