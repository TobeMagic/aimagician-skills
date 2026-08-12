# Phase 51: Composition Retrieval and Governed Adaptation — Context

**Updated:** 2026-08-12
**Specification:** `51-SPEC.md`

## Locked Requirements

- `V7-COMPOSE-01` and `V7-ADAPT-01` are implemented before public migration.
- Preserve Phase 50's exact active scope, private-root isolation, hash-bound
  observations, canonical role precedence, and no client-folder traversal.
- Retain the user decision that a model selects reusable assets and bindings;
  it never creates raw PPTX geometry, color/font directives or OOXML.

## Project Context Intake

| Source ID | Path | Policy | Read result | Conflict or assumption |
|---|---|---|---|---|
| SRC-CTX-007 | `.planning/CONTEXT.md` | MUST_READ | public target is `pptx-studio`, no compatibility shim | migration deferred |
| SRC-CTX-008 | `.planning/CONTEXT.md` | MUST_READ | private Gaojie source/archive stays local | active scope preserved |
| SRC-CTX-009 | `.planning/CONTEXT.md` | MUST_READ | deck/page/region reuse is the governing taxonomy | used directly |
| SRC-P50 | `50-SPEC.md`, `50-SUMMARY.md` | MUST_READ | catalog/observations/query are complete | stable input contracts |
| SRC-V61 | Phase 49 specification | READ_IF_RELEVANT | physical full-page importer exists | do not modify in Phase 51 |

## Implementation Decisions

1. A caller supplies a locked composition intent: target slides, bounded
   candidate IDs, an anchor page, and explicit catalog-derived style
   signatures. Compiler validates rather than searches files.
2. Selection precedence is `exact_deck` → `page` → `component`; lower modes
   require explicit opt-in per target slide.
3. The fact registry owns values; adaptation plans reference fact/asset IDs
   only. No free-form replacement text appears in the plan.
4. A component adaptation target is a Phase 50 safe region; a whole-page
   target receives only declared source-page bindings. PPTX mutation remains
   absent from this phase.

## Existing Patterns To Preserve

- `query_catalog` validates declared input and has no filesystem/model access.
- Hash/source identity is content-addressed and deterministic JSON is sorted.
- CLI uses atomic JSON output and returns stable `*_INVALID` error codes.

## Allowed Scope

- New `pptx_studio` composition/adaptation modules, schemas, CLI wiring,
  focused tests and Phase 51 planning/evidence.

## Forbidden Scope

- `window_pptx` legacy behavior, source PPTX bytes, private archive layout,
  installed skills, source rename/removal, and final deck rendering/QA.

## Integration And Compatibility

- Phase 52 will consume only a validated Phase 51 governed adaptation plan.
- Phase 51 must not require a direct private path inside a clean client folder.

## Expected Project Context Promotion

- `PROMOTE CTX-PPTX-STUDIO-010`: three-layer composition precedence, derived
  style lock, and fact-ID-only adaptation contract when this phase closes.
