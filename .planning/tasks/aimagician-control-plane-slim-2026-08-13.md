# Task: AImagician Control-Plane Slimming

**Status:** Complete
**Risk:** Medium
**Delivery class:** Non-deployable
**Approval source:** USR-20260813-002
**Return checkpoint:** Preserve Phase 49 and resume its separate completion gate after this controlled off-phase task.

## Objective

Reduce default `aimagician-superpower` context without reducing its reachable
engineering capability. The result must prefer the shortest reliable path,
expand only for risk, and retain explicit requirement-to-evidence closure for
High and planning-managed work.

## Requirement Checklist

- [x] REQ-CONTROL-001: Replace the long entry workflow with a compact control plane.
- [x] REQ-CONTROL-002: Add one progressive-disclosure index covering all 19 existing capability modules.
- [x] REQ-CONTROL-003: Make Quick/Standard and High routes explicit, including optional specialist routes and completion safeguards.
- [x] REQ-CONTROL-004: Run a baseline audit, two improvement iterations, deterministic routing regression tests, and final static audit.
- [x] REQ-CONTROL-005: Obtain a controlled, blinded model-behavior evaluation before assigning a total Darwin effectiveness score.

## Evidence

| Requirement | Evidence | Result |
|---|---|---|
| REQ-CONTROL-001 | `skills/owned/aimagician-superpower/SKILL.md`: 117 lines, tiered routes and explicit checkpoints | PASS |
| REQ-CONTROL-002 | `references/capabilities/index.md`: 19 linked modules | PASS |
| REQ-CONTROL-003 | `quality/skill-evals/aimagician-superpower-slim-2026-08-13/evals.json` and `engineering-route.mjs` Quick/High probes | PASS |
| REQ-CONTROL-004 | baseline static 75.2/77; iteration 1 56.0/77; iteration 2 75.2/77; targeted Vitest 23/23 | PASS |
| REQ-CONTROL-005 | `quality/skill-evals/aimagician-superpower-slim-2026-08-13/experiment-r2.json`; two valid independent blind judges and fixture execution | PASS |

## Scope Boundaries

- Changed: the main AImagician entry, its capability index, a deterministic
  quality contract, and a focused regression test.
- Not changed: detailed capability modules, OpenCode and delegation Skills,
  Phase 49 files, document Skills, and installed copies.

## Completion Decision

**Status:** Complete

Darwin static score is `75.2/77`; controlled effectiveness is `10/10`; total
is `98.2/100`. The claim is limited to the three evaluated fixture routes.
