# AImagician Skills

Personal skills repository and bootstrap toolkit for AI coding CLIs.

## What This Repo Does

This repo is meant to be your personal skills distribution layer:

- keep your own skills in-repo
- declare third-party skill sources from GitHub
- declare command-based installers for sources that already ship their own install command
- sync selected skills into user-level directories for supported CLIs

Current direct install targets:

- `codex` -> `~/.codex/skills`
- `claude` -> `~/.claude/skills`
- `opencode` -> `~/.config/opencode/skills`

Current implementation status:

| Area | Status | Notes |
|------|--------|-------|
| Owned skills | supported | copied from `skills/owned/*` |
| GitHub skill sources | supported | repo is resolved, skill directories are copied into target homes |
| Command skill sources | supported | command is executed as a delegated installer |
| Plugin catalog | supported | can be declared under `catalog/plugins/*.yaml` |
| Plugin installation | not yet | planned for Phase 4 |
| Gemini output | not yet | planned for Phase 4 |

## Quick Start

Clone the repo, install dependencies, build, then run bootstrap:

```bash
npm install
npm run build
npm run bootstrap
```

To install only for one CLI:

```bash
npm run bootstrap -- --target claude
```

To install for multiple targets:

```bash
node dist/cli/index.js bootstrap --targets codex,claude,opencode
```

Dry run:

```bash
node dist/cli/index.js bootstrap --dry-run
```

JSON output:

```bash
node dist/cli/index.js bootstrap --json
```

## Typical Workflow

The normal operator flow is:

1. Clone this repo.
2. Add your own skills under `skills/owned/`, or add source definitions under `catalog/skills/` and `catalog/plugins/`.
3. Build the project.
4. Run bootstrap once.
5. Open your target CLI and use its native skill list command to confirm the new skills are visible.

In practice, the only recurring command is usually:

```bash
npm run bootstrap
```

## Repository Layout

```text
skills/
  owned/
    my-skill/
      SKILL.md
catalog/
  skills/
    *.yaml
  plugins/
    *.yaml
```

Important: files under `catalog/skills/*.yaml` and `catalog/plugins/*.yaml` are live config, not docs-only examples.

## Add Your Own Skill

Create a directory under `skills/owned/` and put a `SKILL.md` in it:

```text
skills/owned/my-review-workflow/SKILL.md
```

After that, rerun bootstrap:

```bash
npm run bootstrap
```

The directory name becomes the installed skill id.

## Add a GitHub Skill Source

Create a YAML file under `catalog/skills/`, for example:

```text
catalog/skills/my-github-source.yaml
```

Then add:

```yaml
sources:
  - id: my-github-source
    type: github
    enabled: true
    github:
      repo: owner/repo
      ref: main
      path: skills
    assets:
      - id: some-skill
        kind: skill
        path: some-skill/SKILL.md
```

Field notes:

- `repo`: GitHub repo in `owner/name` format
- `ref`: optional branch, tag, or commit
- `path`: optional base directory inside the repo
- `assets[].id`: local skill id used by this project
- `assets[].path`: path to the skill directory or `SKILL.md` inside the source repo

## Add a Command-Based Skill Source

If a third-party source already provides its own installer command, declare it under `catalog/skills/`, for example:

```text
catalog/skills/upstream-installer.yaml
```

Then add:

```yaml
sources:
  - id: upstream-installer
    type: command
    enabled: true
    targets:
      include:
        - claude
        - opencode
    command:
      run: node scripts/install-upstream.js
      cwd: .
    assets:
      - id: upstream-helper
        kind: skill
```

At runtime, the command gets target-aware environment variables:

- `AIMAGICIAN_TARGETS`
- `AIMAGICIAN_SOURCE_ID`
- `AIMAGICIAN_ASSET_IDS`
- `AIMAGICIAN_WORKSPACE_ROOT`
- `AIMAGICIAN_HOME_DIR`
- `AIMAGICIAN_CODEX_SKILLS_DIR`
- `AIMAGICIAN_CLAUDE_SKILLS_DIR`
- `AIMAGICIAN_OPENCODE_SKILLS_DIR`

This is useful when the upstream project already knows how to install itself and you just want this repo to orchestrate it.

## Example: Only Use Anthropic Official Claude Skills

If you only want a small subset from Anthropic's official skills repo, create:

```text
catalog/skills/claude-official.yaml
```

with:

```yaml
sources:
  - id: claude-official
    type: github
    enabled: true
    targets:
      include:
        - claude
    github:
      repo: anthropics/skills
      ref: main
      path: skills
    assets:
      - id: docx
        kind: skill
        path: docx/SKILL.md
      - id: pdf
        kind: skill
        path: pdf/SKILL.md
      - id: pptx
        kind: skill
        path: pptx/SKILL.md
      - id: xlsx
        kind: skill
        path: xlsx/SKILL.md
```

Then run:

```bash
npm run bootstrap -- --target claude
```

This tells the project:

- only sync to `claude`
- pull skills from `anthropics/skills`
- only install the assets you listed

Reference:

- Anthropic official skills repo: `https://github.com/anthropics/skills`

## Example: Declare Anthropic Official Claude Plugins

Plugin installation is not implemented in this project yet, but you can already track plugin intent under `catalog/plugins/`.

Create:

```text
catalog/plugins/claude-official-plugins.yaml
```

with:

```yaml
sources:
  - id: claude-official-plugins
    type: github
    enabled: true
    targets:
      include:
        - claude
    github:
      repo: anthropics/claude-plugins-official
      ref: main
      path: plugins
    assets:
      - id: example-plugin
        kind: plugin
        path: example-plugin
```

What this means today:

- the plugin metadata is valid in this repo
- target rules are normalized correctly
- bootstrap will not install the plugin yet

If you need official Claude plugins right now, use Claude Code's native plugin marketplace directly. According to Anthropic's official plugin directory README:

```text
/plugin install {plugin-name}@claude-plugin-directory
```

References:

- Anthropic official plugin directory: `https://github.com/anthropics/claude-plugins-official`
- Anthropic official skills repo: `https://github.com/anthropics/skills`

## Example: Only Anthropic Official Skills Plus Plugin Declarations

If your goal is "I only want Claude official skills and Claude official plugins", the repo setup is:

1. Create `catalog/skills/claude-official.yaml` with the skills you want from `anthropics/skills`.
2. Create `catalog/plugins/claude-official-plugins.yaml` with the plugin entries you want from `anthropics/claude-plugins-official`.
3. Run:

```bash
npm run bootstrap -- --target claude
```

What happens today:

- official Anthropic skills are installed into your user-level Claude skills directory
- plugin entries are tracked in config, but this project does not install them yet
- for plugins, use Claude Code's native install flow until Phase 4 lands

## Target Selection

You can scope a source or asset to specific CLIs:

```yaml
targets:
  include:
    - claude
    - opencode
```

Or exclude one:

```yaml
targets:
  exclude:
    - gemini
```

Current supported target names:

- `codex`
- `claude`
- `opencode`
- `gemini`

## User-Level Workspace

Bootstrap state is written to a user-level workspace:

- Windows: `%LOCALAPPDATA%\\aimagician-skills`
- Linux: `$XDG_STATE_HOME/aimagician-skills` or `~/.local/state/aimagician-skills`

For tests or isolated runs:

```bash
AIMAGICIAN_WORKSPACE_ROOT=/tmp/aimagician-skills node dist/cli/index.js bootstrap
```

To redirect direct-target writes into a fake user home:

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
