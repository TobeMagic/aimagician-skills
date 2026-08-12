# Phase 52: PPTX Studio Migration and Agent Workflow — Validation

**Updated:** 2026-08-12

## Requirement Evidence

| Requirement | Status | Evidence | Observed result |
|---|---|---|---|
| V7-QA-01 | PASS (focused) | 47 PPTX Studio focused tests | Native text/image replacement, physical importer, LibreOffice open, lineage SHA and placeholder failure fixture pass. |
| V7-SKILL-01 | PARTIAL | `skills/owned/pptx-studio/SKILL.md` and evals | Concise governed workflow exists; installer/source parity remains pending. |
| V7-MIGRATE-01 | NOT_RUN | Flag-day migration | Old production tree is intentionally retained until runtime and install parity proof. |

## Goal Evidence

| Goal criterion | Status | Evidence | Observed result |
|---|---|---|---|
| AC-52-01 | PASS (fixture) | 47 focused tests | Real PPTX fixture is assembled through OPC import, opens editably, and has page/slot/asset lineage. |
| AC-52-02 | PASS (bounded fixture) | placeholder/value-drift tests | Changed registry value and post-assembly placeholder fail closed; only shrink-to-fit is recorded as safe repair. |
| AC-52-03 | PARTIAL | public Skill/evals | Contract is written; installation and agent replay still pending. |
| AC-52-04 | NOT_RUN | migration test | Must be verified only after flag-day move. |

## Commands

| Command | Result | Notes |
|---|---|---|
| `pytest -q tests/window_pptx/test_pptx_studio_{curation,catalog,regions,rendering,observations,visual_batches,query,composition,adaptation,physical_adapter}.py` | PASS | 47 passed on 2026-08-12. |
| `workflow validate --phase 52 --gate align` | PASS | Initial phase alignment passed before implementation. |
| `workflow validate --phase 52 --gate spec` | PASS | Locked Phase 52 specification passed on 2026-08-12. |

## Gaps And Residual Risk

- The new public skill is not yet installed or source/install parity checked.
- The old source identity is intentionally still present, so flag-day migration and
  broad regression checks are required.
- The adapter has fixture proof only; Phase 53 must prove a clean 15-page Codex run
  with independent visual review.
