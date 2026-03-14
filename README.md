# AImagician Skills

Personal skills repository and bootstrap toolkit for AI coding CLIs.

## Current Scope

This repository currently provides:

- repo-owned skill discovery under `skills/owned/*/SKILL.md`
- YAML catalogs for external skill and plugin sources
- target-aware normalization for supported CLIs
- a bootstrap command that stages manifest-backed workspace state
- direct user-level skill sync for Codex, Claude Code, and OpenCode from owned and GitHub-backed skill sources
- delegated execution for command-based skill sources when a source provides its own installer command

Gemini remains deferred to a later phase. Command-based sources are executed as delegated installers instead of being materialized through the direct folder sync path.

## Install

```bash
npm install
npm run build
```

## Bootstrap

Run the default bootstrap command:

```bash
npm run bootstrap
```

Target selection defaults to all supported CLIs. To narrow the run:

```bash
node dist/cli/index.js bootstrap --targets claude,opencode
```

For a dry run:

```bash
node dist/cli/index.js bootstrap --dry-run
```

For machine-readable output:

```bash
node dist/cli/index.js bootstrap --json
```

Current direct-target behavior:

- `codex` -> installs skills into `~/.codex/skills`
- `claude` -> installs skills into `~/.claude/skills`
- `opencode` -> installs skills into `~/.config/opencode/skills`
- `gemini` -> deferred until Gemini-native output lands

## User-Level Workspace

Bootstrap state is written to a user-level workspace:

- Windows: `%LOCALAPPDATA%\\aimagician-skills`
- Linux: `$XDG_STATE_HOME/aimagician-skills` or `~/.local/state/aimagician-skills`

For tests or isolated runs, override the workspace root with:

```bash
AIMAGICIAN_WORKSPACE_ROOT=/tmp/aimagician-skills node dist/cli/index.js bootstrap
```

To redirect direct-target writes into a fake user home during tests:

```bash
AIMAGICIAN_HOME_DIR=/tmp/aimagician-home \
AIMAGICIAN_CONFIG_HOME=/tmp/aimagician-home/.config \
AIMAGICIAN_WORKSPACE_ROOT=/tmp/aimagician-skills \
node dist/cli/index.js bootstrap --target claude
```

## Verify

```bash
npm test
npm run build
```
