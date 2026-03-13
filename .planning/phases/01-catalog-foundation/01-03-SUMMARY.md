---
phase: 01-catalog-foundation
plan: 03
subsystem: catalog
tags: [targets, normalization, capability-matrix]
provides:
  - Shared target selection grammar for skills and plugins
  - Normalized target-aware asset model
  - Source and asset override merge logic with capability warnings
affects: [bootstrap, adapters, plugins]
tech-stack:
  added: []
  patterns:
    - Default-to-all target selection with explicit overrides
    - Capability metadata preserved for later skip-and-warn installers
key-files:
  created:
    - src/model/targets.ts
    - src/model/assets.ts
    - src/catalog/normalize.ts
    - tests/catalog/target-mapping.test.ts
    - tests/fixtures/catalog/target-overrides.yaml
  modified: []
key-decisions:
  - Asset-level include lists override source-level include lists while exclude lists accumulate
  - Unsupported capabilities stay attached to normalized target state instead of deleting targets early
patterns-established:
  - Normalization emits deterministic effective targets plus per-target warnings
  - Skills and plugins share one target expression style end to end
duration: "2 min"
completed: 2026-03-13
---

# Phase 1: catalog-foundation Summary

**Normalized target-aware asset model with default-all deployment rules and capability-preserving override merges**

## Performance
- **Duration:** 2 min
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Defined the shared supported-target and capability matrix types for later adapters
- Normalized source and asset target declarations into deterministic effective target sets
- Backed source override, asset override, and unsupported-capability behavior with executable fixture tests

## Task Commits
1. **Task 1: Define normalized asset and target types** - `03c02ee`
2. **Task 2: Implement target normalization and override merging** - `dfe7d03`
3. **Task 3: Add fixture-backed override tests** - `26712de`

## Files Created/Modified
- `src/model/targets.ts` - Declares supported CLIs, capabilities, and reusable target selection helpers
- `src/model/assets.ts` - Defines normalized asset output for later installer phases
- `src/catalog/normalize.ts` - Merges source-level and asset-level target declarations into effective target states
- `tests/catalog/target-mapping.test.ts` - Verifies default-all behavior, overrides, and skip-and-warn metadata

## Decisions & Deviations
- Asset-level include overrides intentionally replace source-level include lists so a single asset can opt into a narrower or different target set cleanly
- None otherwise - the plan executed as written once the normalized model was in place

## Next Phase Readiness
- Phase 2 can consume normalized assets without reinterpreting target YAML
- Later direct-skill and plugin adapters already have the capability metadata needed for explicit skip-and-warn behavior
