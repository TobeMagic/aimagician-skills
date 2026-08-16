# Phase 50: UAT

**Updated:** 2026-08-12

## Scenarios

### UAT-01: Complete Active-Library Catalog

- **Starting state:** active private source has the approved curated scope.
- **Action:** compile the active library and require the visual-observation
  index to be complete.
- **Expected visible result:** every catalog page has local render evidence and
  a hash-bound observation.
- **Expected side effect:** deterministic local catalog and observation index
  are available for retrieval; no client worktree is scanned.
- **Result:** PASS
- **Evidence:** 294 decks / 491 pages / 839 safe regions; 491/491 observations
  complete and bound to the catalog render hashes.

### UAT-02: Role-Aware Page Retrieval

- **Starting state:** compiled catalog plus complete observation index.
- **Action:** issue deterministic bounded queries for cover, contents, section,
  three-item, team, timeline, process, business model, map, and closing roles.
- **Expected visible result:** each query returns three eligible candidates,
  with the canonical role family ranked first.
- **Expected side effect:** results contain explanation scores only; no source
  bytes or client-folder lookup is needed.
- **Result:** PASS
- **Evidence:** ten role queries passed; a CLI cover smoke query returned three
  candidates with `eligible`, canonical-role, and visual-role reasons.

### UAT-03: Safety and Invalid-Input Boundaries

- **Starting state:** synthetic catalog/visual fixtures.
- **Action:** exercise missing render evidence, source-root escape, hash
  mismatch, forbidden egress values, image-only pages, and invalid query modes.
- **Expected visible result:** compiler, observation normalizer, region
  extractor, or query rejects the invalid input deterministically.
- **Expected side effect:** none; no archive recovery or external upload occurs.
- **Result:** PASS
- **Evidence:** focused test suite: 29 passed.

### UAT-04: Recoverability Without Mutation

- **Starting state:** applied private archive manifest.
- **Action:** run archive verification and `recover --dry-run`.
- **Expected visible result:** matching archived package records are recoverable
  in principle, but source/archive paths remain unchanged.
- **Expected side effect:** no recovery operation is applied.
- **Result:** PASS
- **Evidence:** private verifier and dry-run reported pass; live source/archive
  package counts remained 294/83.

## UAT Decision

**Status:** PASS
**Residual risk:** visual description quality is catalog infrastructure only;
actual deck assembly and artistic-output acceptance are intentionally deferred
to later phases.
