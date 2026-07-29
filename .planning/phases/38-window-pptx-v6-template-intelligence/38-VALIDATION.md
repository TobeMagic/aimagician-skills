# Phase 38 Validation

**Status:** PASS
**Validated:** 2026-07-30
**Branch:** `feat/window-pptx-v6`

## Requirement Evidence

| Requirement | Result | Evidence |
|---|---|---|
| V6-LIB-01 | PASS | Registry v3 joins certified spines and 84 executable candidates while preserving v1 loaders and quarantining uncertified legacy items. |
| V6-DESIGN-01 | PASS | Selection accepts stable IDs and grounded bindings only; raw geometry, style, code, OOXML, HTML, unknown IDs, unsupported facts, and capacity violations fail closed. |
| V6-DECK-01 | PASS | Three spine manifests govern anatomy, art direction, motif, density, cadence, family compatibility, alternatives, and portable materialization. |

## Fresh Checks

| Check | Result |
|---|---|
| `test_template_intelligence.py` | 14/14 PASS |
| Combined v6 focused tests | 23/23 PASS |
| Complete Window-PPTX regression | 871/871 PASS in two filesystem-safe shards |
| Phase 38 workflow spec/plan/execute | PASS/PASS/PASS |
| Skillbird formatter | 23 checked; no changes or issues |
| `git diff --check` | PASS |

## Fail-Closed Boundaries

- Automatic selection is certified-only and dependency-closed.
- No private credential or unlicensed template byte is required.
- Physical source packages remain immutable and hash-bound.
- Registered composition is native/editable; whole-slide raster fallback is
  forbidden.
- `NO_FIT` is returned instead of arbitrary cross-family improvisation.
