# Phase 52: PPTX Studio Migration and Agent Workflow — Context

**Updated:** 2026-08-12  
**Specification:** `52-SPEC.md`

## Implementation Decisions

- The curated catalog is public metadata only. Private paths are resolved in-process by
  package SHA under the active private source root; the clean client folder is never a
  template search root.
- The existing cross-package OPC importer remains the materializer because it carries
  masters, layouts, themes, media, charts and relationship closure. COM is optional and
  never a delivery gate.
- `pptx-studio` agents choose narrative, certified IDs and fact/asset IDs only. The
  adapter derives actual shape IDs, source slide fingerprints and import geometry.
- An adaptation plan binds the exact value registry by SHA while remaining value-free.
- Automatic repair is deliberately limited to native text `shrink-to-fit` before import.
  Replacing pages, moving shapes, changing colors or editing OOXML after QA is forbidden.

## Existing Patterns To Preserve

- Phase 50: active/archived source separation, Agnes visual observations, hash-bound
  catalog entries and safe regions.
- Phase 51: deterministic art-direction lock, role/capacity gates, compositional IDs
  and no raw model visual authority.
- v6.1: physical dependency closure, editable/portable evidence and fail-closed output.

## Allowed Scope

- New adapter, QA harness, CLI, concise Skill/evals, focused tests and installation
  migration after proof.

## Forbidden Scope

- Any tracked private commercial source, image preview, cookie or client fact.
- PptxGenJS/raster fallback as evidence of physical page reuse.
- Retaining `window-pptx` as a post-migration production compatibility shell.

## Expected Project Context Promotion

- `NO_CHANGE` until the Phase 53 clean-room run establishes a reusable client-folder
  contract and acceptance evidence.
