# Phase 50: Asset Curation and Visual Catalog - Context

**Updated:** 2026-08-11
**Specification:** `50-SPEC.md`

## Locked Requirements

- V7-CURATE-01, V7-CATALOG-01, V7-VISION-01, V7-REGION-01 and V7-QUERY-01.
  `50-SPEC.md` is normative.

## Project Context Intake

| Source ID | Path | Policy | Read result | Conflict or assumption |
|---|---|---|---|---|
| SRC-STATE | `.planning/STATE.md` | MUST_READ | v7 / Phase 50 active | NONE |
| SRC-PROJECT | `.planning/PROJECT.md` | MUST_READ | owned Skill delivery and ignored private assets | NONE |
| SRC-CONTEXT | `.planning/CONTEXT.md` | MUST_READ | CTX-DEC-007 through 009 govern migration/catalog | NONE |
| SRC-ROADMAP | `.planning/ROADMAP.md` | MUST_READ | GOAL-50-01 through GOAL-50-05 | NONE |
| SRC-REQUIREMENTS | `.planning/REQUIREMENTS.md` | MUST_READ | five v7 requirements map to Phase 50 | NONE |
| SRC-V61 | `.planning/phases/49-window-pptx-v61-physical-template-assembly/49-SPEC.md` | READ_IF_RELEVANT | stable physical-library/private-root boundary | no physical assembler edits in Phase 50 |
| SRC-PRIVATE | original local `.../window-pptx/.private/sources/gaojie` | READ_ONLY before archive | 29 category dirs, 377 packages, about 1.4GB | source root is outside the new worktree |

- Read the most recent relevant checkpoint first for orientation.
- Resolve conflicts by authority, not filesystem time or document recency.
- Stop and discuss material uncertainty before implementation.

## Implementation Decisions

- Introduce a new `pptx_studio` private-catalog boundary, keeping legacy
  `window_pptx` imports read-only until Phase 52.
- Treat the active category names in USR-V7-01 as a closed allowlist.
- Perform no archive mutation until dry-run plan, source manifest and recovery
  command all pass; apply only with exact path/hash revalidation.
- Render once through existing portable LibreOffice proof. Agnes sees only
  selected PNGs and normalized textual observations are stored privately.
- Build region candidates from source OOXML shape bounds and declared safety
  rules; vision informs semantic tags, never geometry/editability claims.

## Existing Patterns To Preserve

- Content-addressed private source identity, ignored `.private/`, relative
  locators, deterministic JSON, `resolve_private_root` precedence and
  portable LibreOffice proof.
- Phase 49 security: clean client folders cannot contain or be searched for
  templates; no arbitrary model geometry/style/code; COM stays optional.

## Allowed Scope

- Phase 50 planning, schemas, `pptx_studio` catalog/curation/query modules,
  CLI, focused tests and private artifacts exclusively under explicit root.

## Forbidden Scope

- Actual page/component assembly, `window-pptx` public rename/removal,
  generation harness and release. Credentials, original private bytes, archive
  payload, screenshots and Agnes request contents are forbidden in Git.

## Integration And Compatibility

- Existing public `window_pptx` APIs remain unchanged. The Phase 50 local
  catalog uses a new schema namespace and has no client-folder discovery.
- The external private root may be the existing original worktree path during
  migration; it is not copied into or symlinked into this branch.

## Expected Project Context Promotion

- `PROMOTE CTX-PPTX-STUDIO-001`: three-level retrieval, rendered-image visual
  grounding and recoverable archive invariants after evidence proves them.
