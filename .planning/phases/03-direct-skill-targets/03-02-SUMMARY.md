---
phase: 03-direct-skill-targets
plan: 02
subsystem: direct-skill-sync
tags: [copy-sync, github, claude, opencode]
provides:
  - Copy-based direct skill sync for Codex, Claude Code, and OpenCode
  - GitHub-backed skill directory resolution
  - End-to-end fake-home coverage across all direct targets
affects: [bootstrap, source-resolution, testing]
tech-stack:
  added: []
  patterns:
    - Resolve source directories before target adapters write anything
    - Reuse one copy-based sync path across all direct targets
key-files:
  created:
    - src/bootstrap/direct-target-sync.ts
    - src/bootstrap/source-resolution.ts
  modified:
    - src/bootstrap/run-bootstrap.ts
    - tests/bootstrap/direct-target-sync.test.ts
key-decisions:
  - Owned skills and GitHub-backed skills both flow through the same resolved-directory sync path
  - Direct target sync copies whole skill directories, not just `SKILL.md`
patterns-established:
  - GitHub repo overrides can redirect source resolution into local fixtures for offline verification
  - Direct target sync prunes only managed directories for selected targets
duration: "41 min"
completed: 2026-03-14
---

# Phase 3: direct-skill-targets Summary

**Shared copy-based sync for owned and GitHub-backed skills across all direct targets**

## Performance
- **Duration:** 41 min
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Built a reusable copy-based direct sync layer for Codex, Claude Code, and OpenCode
- Added GitHub source materialization so external skill directories resolve before sync
- Covered owned-skill installs, GitHub-backed installs, stale prune behavior, and target-selective reruns with isolated fake-home tests

## Task Commits
1. **Task 1: Build shared direct skill sync logic for target homes** - `50dc105`
2. **Task 2: Wire Claude Code and OpenCode apply behavior** - `50dc105`
3. **Task 3: Expand fake-home integration tests across all direct targets** - `50dc105`

## Files Created/Modified
- `src/bootstrap/direct-target-sync.ts` - Applies copy-based sync and stale-managed prune per target
- `src/bootstrap/source-resolution.ts` - Resolves owned and GitHub-backed skill directories for sync
- `src/bootstrap/run-bootstrap.ts` - Orchestrates source resolution plus direct apply
- `tests/bootstrap/direct-target-sync.test.ts` - Verifies all direct targets, prune behavior, and selected-target updates

## Decisions & Deviations
- GitHub resolution stayed `git`-based for runtime behavior, while tests use explicit repo overrides for offline reliability
- Command-based skill sources were not forced into the direct folder sync path and stayed delegated installer work

## Next Phase Readiness
- Phase 3 no longer depends on repository-local staging alone; it now writes real target-home skill directories
- The same source-resolution boundary can feed Gemini-native generation in Phase 4
