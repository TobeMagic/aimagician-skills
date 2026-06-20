# Phase 21 Install Acceptance

**Date:** 2026-06-14
**Milestone:** v4.0 AImagician Superpower + Skillbird Consolidation
**Requirements:** V4-ACC-01, V4-ACC-02

## Safety Boundary

The acceptance path performs real filesystem writes, but uses isolated `--home` and `--project` directories. This exercises the same global/project target path logic without mutating the operator's actual `~/.claude`, `~/.codex`, or other live CLI homes in a non-interactive test run.

The required preview-confirmation loop is:

1. Run `install --dry-run --json` and inspect the planned installed/skipped assets.
2. Apply the same selector without `--dry-run`.
3. Verify files and manifests exist in the expected target homes.

## Global Install Acceptance

Covered by `tests/acceptance/v4-skillbird-acceptance.test.ts`.

Preview command shape:

```bash
skillbird install --category build --scope global --target claude --home <isolated-home> --dry-run --json
```

Apply command shape:

```bash
skillbird install --category build --scope global --target claude --home <isolated-home> --json
```

Acceptance evidence:

- Preview reports `dryRun: true`.
- Apply reports `dryRun: false`.
- Installed core workflow skills include:
  - `aimagician-superpower`
  - `skill-creator`
  - `webapp-testing`
- Disabled external `playwright-skill` is skipped with `source-default-disabled`.
- Apply writes:
  - `<isolated-home>/.claude/skills/aimagician-superpower/SKILL.md`
  - `<isolated-home>/.local/state/aimagician-superpower/manifest.json`

## Project Install Acceptance

Covered by `tests/acceptance/v4-skillbird-acceptance.test.ts`.

Preview command shape:

```bash
skillbird install --category documents --scope project --project <project> --target claude --home <isolated-home> --dry-run --json
```

Apply command shape:

```bash
skillbird install --category documents --scope project --project <project> --target claude --home <isolated-home> --json
```

Acceptance evidence:

- Preview reports `dryRun: true`.
- Apply reports `dryRun: false`.
- Document bundle includes:
  - `docx`
  - `pdf`
  - `pptx`
  - `xlsx`
- Apply writes:
  - `<project>/.claude/skills/docx/SKILL.md`
  - `<project>/.skillbird/manifest.json`

## Outcome

- V4-ACC-01: Complete. Global install behavior is accepted through preview then real apply in an isolated current-user home.
- V4-ACC-02: Complete. Project install behavior is accepted through preview then real apply in an isolated project directory.
