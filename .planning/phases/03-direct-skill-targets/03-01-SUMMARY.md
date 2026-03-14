---
phase: 03-direct-skill-targets
plan: 01
subsystem: direct-target-homes
tags: [codex, target-homes, platform]
provides:
  - Centralized direct target-home resolution
  - Bootstrap target reporting for direct versus deferred targets
  - Fake-home test isolation for direct target work
affects: [bootstrap, cli, testing]
tech-stack:
  added: []
  patterns:
    - One typed target-home registry for Codex, Claude Code, and OpenCode
    - Fake-home overrides instead of touching the real user profile in tests
key-files:
  created:
    - src/bootstrap/target-homes.ts
  modified:
    - src/shared/platform.ts
    - src/bootstrap/run-bootstrap.ts
    - tests/bootstrap/direct-target-sync.test.ts
key-decisions:
  - Direct target homes are resolved from one central module instead of hardcoded strings scattered through bootstrap logic
  - Gemini stays explicit and deferred in target reports rather than pretending a Phase 4 adapter already exists
patterns-established:
  - Bootstrap preview and apply results both expose per-target status
  - Tests isolate direct target writes under fake homes using environment and platform overrides
duration: "24 min"
completed: 2026-03-14
---

# Phase 3: direct-skill-targets Summary

**Central target-home resolution and the first real direct-target bootstrap path**

## Performance
- **Duration:** 24 min
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Added one typed target-home resolver for Codex, Claude Code, and OpenCode
- Extended bootstrap results so direct targets report `planned` or `synced`, while Gemini reports `deferred`
- Locked the new path layer behind fake-home integration coverage instead of mutating the real user profile

## Task Commits
1. **Task 1: Add centralized direct target-home resolution** - `50dc105`
2. **Task 2: Integrate Codex direct sync into bootstrap apply flow** - `50dc105`
3. **Task 3: Add isolated Codex direct sync coverage** - `50dc105`

## Files Created/Modified
- `src/bootstrap/target-homes.ts` - Resolves current-user skill roots for Codex, Claude Code, and OpenCode
- `src/shared/platform.ts` - Adds home/config overrides needed for isolated direct-target execution
- `src/bootstrap/run-bootstrap.ts` - Exposes target status reporting from bootstrap
- `tests/bootstrap/direct-target-sync.test.ts` - Establishes fake-home coverage for direct target paths

## Decisions & Deviations
- The first target-home layer landed for all three direct targets at once because the path abstraction was shared and small
- Target reporting was added early so later sync work and smoke tests could assert target-level outcomes directly

## Next Phase Readiness
- The engine now has a stable path boundary for all direct skill-folder targets
- Later direct sync logic can reuse one target-home registry instead of rebuilding path rules
