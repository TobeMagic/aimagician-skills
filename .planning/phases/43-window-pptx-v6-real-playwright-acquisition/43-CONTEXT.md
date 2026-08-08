# Phase 43 Context

**Status:** Complete
**Specification:** `43-SPEC.md`

## Inputs

- USR-V6-11 and USR-V6-12
- Phase 37 acquisition/catalog safety contracts
- Phase 42 reopened ground truth
- user-provided private request-header file

## Decisions carried forward

- normal browser entitlement only;
- `.private/` owns credentials, previews, packages, state, and review images;
- route-aware taxonomy, preview-first selection, pinned cookie-free CDN;
- no Phase 44 visual-quality claim from acquisition thumbnails.

## Implementation Decisions

- Category keys include normalized route and numeric category ID.
- CDN requests are cookie-free and bounded; authenticated navigation stays in
  the ephemeral browser context.
- Preview selection uses deterministic exact/near dedupe plus farthest-first
  traversal.
- Resume reconciles valid bytes and repairs missing/corrupt candidates.

## Existing Patterns To Preserve

- Phase 37 dry-run, quarantine, rights, redaction, atomic-write, and private
  credential boundaries.
- Stable machine-readable finding codes and fail-closed package validation.

## Allowed Scope

- Phase 43 planning, adapter/diversity code, library wiring, and
  acquisition/private-guard tests.

## Forbidden Scope

- Private Cookie values, package bytes, previews, source URLs, access-control
  bypass, redistribution, or Phase 44 product-quality claims.

## Integration And Compatibility

- State schema v2 replaces lossy numeric-only discovery while preserving valid
  artifact hash reconciliation.
- Phase 44 consumes the private asset index and sanitized aggregate evidence.

## Handoff

Phase 44 receives a validated private package set and sanitized aggregate
counts. It must quarantine, render, visually route, deduplicate, and certify
pages before Phase 45 may materialize them.
