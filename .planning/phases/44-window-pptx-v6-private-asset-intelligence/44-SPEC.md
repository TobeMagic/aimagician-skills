# Phase 44: Private Asset Intelligence - Specification

**Created:** 2026-07-30
**Status:** Locked
**Risk:** high
**User-facing:** no
**Requirements:** 1
**Original requests:** USR-V6-11, USR-V6-12

## Goal

Turn the authenticated private package set into a visually reviewed,
structurally verified, semantically routed and deduplicated 300–500-page
private template core whose complete layouts and support assets cannot be
accidentally mixed.

## Background

Phase 43 acquired 377 valid package artifacts. Passive intelligence accepts
and renders 356 packages into 620 slide images while 17 remain quarantined and
four are rejected. The former score-only q0.75 core selected 312 pages, but a
full-coverage independent pixel review found that the mixed pool contained
only 136 complete layouts, 103 useful specialty/support pages, and 73 pages
that must be excluded. A quality number alone therefore cannot certify
art-direction or routing.

## Requirements

### V6R-MINE-01: Full-coverage private asset intelligence and certification

- **Current:** Packages render and expose structural metadata, but the former
  312-page core mixed complete layouts, components, posters, watermarked pages,
  duplicates, and low-art-direction material.
- **Target:** Quarantine and render all accepted packages; bind an exact
  full-coverage visual disposition; route layouts and named support pools
  separately; exclude every serious visual defect; deduplicate across all
  routed pages; and certify 300–500 pages or an exhaustive quality shortfall.
- **Acceptance:** GOAL-44-01 through GOAL-44-04 pass with private evidence,
  focused tests, complete contact sheets, independent pixel review, and a
  fresh OpenCode completion audit.

## Boundaries

### In Scope

- Passive package quarantine and bounded OOXML structural inspection.
- Isolated rendering, deterministic fingerprinting, cross-pool dedupe, semantic
  pool routing, rights/provenance binding, contact sheets, and visual review.
- Review of the q0.75 core and the complete 0.65–0.75 supplement band.

### Out Of Scope

- Materializing selected pages into generated decks; Phase 45 owns that bridge.
- Committing credentials, source URLs, previews, package bytes, rendered pages,
  or any redistributable private asset.
- Lowering the art-direction bar merely to reach a numeric page target.

## Constraints

- Every visual disposition is bound to an ordered page-set digest and must be a
  complete non-overlapping partition.
- Blocker and Important pages cannot survive through weighting or fallback.
- `complete-layout` and support/specialty pools have separate retrieval routes.
- Template placeholder copy is not itself a defect; portrait posters and
  visible third-party watermarks are hard rejects.
- Private-use authorization is recorded with redistribution disabled.
- Contact-sheet coverage must match candidate IDs exactly once.

## Engineering Contract

- **Domain terms and owners:** package quarantine owns safety; OOXML inspection
  owns structure/editability; rendered PNG owns visual evidence; disposition
  owns pool/deny policy; certification owns provenance and rights binding.
- **Invariants:** no unreviewed page is certified; no denied page is searchable;
  no support page auto-selects as an ordinary layout; no duplicate has two
  canonical identities.
- **Interfaces and compatibility:** v1 preliminary order remains digest-bound;
  certified output advances to v2 with layout/support/deny collections.
- **Failure semantics:** drift, incomplete partition, missing render, invalid
  rights scope, or unresolved serious visual finding fails closed.
- **Migration and rollback:** v1 core remains reproducible from the private
  index; remove the v2 report to rerun, never delete source packages.

## Test Seams And Critical Cases

| Behavior | Observable Seam | Failing Case | Evidence |
|---|---|---|---|
| V6R-MINE-01 | fixture index, disposition parser, dedupe, contact sheets, real private report | drift, overlap, missing page, mixed pool, unbound rights, incomplete visual coverage | `44-VALIDATION.md` |

## Acceptance Criteria

- [ ] V6R-MINE-01 has passing evidence for GOAL-44-01 through GOAL-44-04.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.96
- **Boundary clarity:** 0.96
- **Constraint clarity:** 0.95
- **Acceptance clarity:** 0.95
- **Ambiguity:** 0.04

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | Visual quality | Can q0.75 alone certify a page? | No; every candidate needs rendered-pixel disposition. |
| 2 | Reuse | Are components failed layouts? | No; useful components move to named support pools. |
| 3 | Safety | Can serious defects remain with low weight? | No; Blocker and Important are excluded from every retrieval path. |
| 4 | Quantity | May weak pages return to reach 300? | No; review the full supplement band and report an honest shortfall if needed. |
| 5 | Rights | What scope is certified? | Private user-authorized use only; redistribution remains false. |
