# Phase 20 UX Acceptance: Skillbird Loop

**Date:** 2026-06-14
**Milestone:** v4.0 AImagician Superpower + Skillbird Consolidation
**Requirements:** V4-UX-01, V4-UX-02

## UX Scope

Phase 20 verifies the user-facing Skillbird loop after the Skillbee rename:

- TUI opens with Skillbird identity.
- Category-oriented navigation is visible in the PTY smoke path.
- Category bundle install works through CLI selectors.
- Global and project scopes can be previewed before apply.

## TUI Acceptance

Coverage:

- `tests/tui/tui-pty-smoke.test.ts`

Assertions:

- PTY dashboard output contains `Skillbird`.
- PTY dashboard does not hit `Maximum call stack size exceeded`.
- Category styling text is bound through `src/tui/dashboard.ts` and checked by the v4 acceptance test.

This keeps the terminal launch path under PTY smoke while avoiding brittle assertions against blessed alternate-screen rendering, where panel labels are not consistently emitted into captured text.

## Category Bundle Acceptance

Coverage:

- `tests/acceptance/v4-skillbird-acceptance.test.ts`

Scenarios:

1. Global build bundle:
   - command path: `install --category build --scope global --target claude --home <isolated-home> --dry-run --json`
   - preview confirms owned workflow skills:
     - `aimagician-superpower`
     - `skill-creator`
     - `webapp-testing`
   - preview confirms disabled external source skip:
     - `playwright-skill (source-default-disabled)`
   - apply writes to the configured global target home and manifest path.

2. Project documents bundle:
   - command path: `install --category documents --scope project --project <project> --target claude --home <isolated-home> --dry-run --json`
   - preview confirms document skills:
     - `docx`
     - `pdf`
     - `pptx`
     - `xlsx`
   - apply writes to `<project>/.claude/skills` and `<project>/.skillbird/manifest.json`.

Targeted verification:

```bash
npx vitest run tests/acceptance/v4-skillbird-acceptance.test.ts
```

Result: 1 test file, 3 tests passed.

## Outcome

- V4-UX-01: Complete. Skillbird TUI launch is covered by PTY smoke; category styling is covered by dashboard source acceptance and category install UX tests.
- V4-UX-02: Complete. Category bundle preview/apply works for global and project scopes.
