# AImagician Skills

Personal skills repository and bootstrap toolkit for AI coding CLIs.

## What This Repo Does

This repo is your personal skills distribution layer:

- keep your own skills in-repo
- declare third-party skill sources from GitHub
- declare command-based upstream installers such as GSD when an upstream project already ships its own install command
- install skills into user-level locations for supported CLIs
- generate Gemini-native output from repository-managed skills
- install supported plugin assets where the target exposes a stable user-level plugin path

## Current Support

| Capability | Status | Notes |
|------------|--------|-------|
| Owned skills | supported | loaded from `skills/owned/*` |
| GitHub skill sources | supported | repo is materialized and copied into target homes |
| Command skill sources | supported | delegated upstream installer execution, currently used for GSD-style packages |
| Codex skills | supported | installs to `~/.codex/skills` |
| Claude Code skills | supported | installs to `~/.claude/skills` |
| OpenCode skills | supported | installs to `~/.config/opencode/skills` |
| Gemini skills | supported | generated as native extensions under `~/.gemini/extensions` |
| Hermes skills | supported | installs to `~/.hermes/skills` |
| Plugin catalog | supported | declare under `catalog/plugins/*.yaml` |
| OpenCode plugins | supported | GitHub-backed JavaScript or TypeScript file assets install to `~/.config/opencode/plugins` |
| Claude plugins | explicit skip | bootstrap reports skip because the documented flow is marketplace- and consent-driven |
| Gemini plugin catalog assets | explicit skip | Phase 4 Gemini support is for generated skill extensions, not plugin catalog installs |

## Quick Start

Clone the repo, install dependencies, build, then run bootstrap:

```bash
npm install
npm run build
npm run bootstrap
```

If you publish this package, the intended operator flow is also:

```bash
npx aimagician-skills@latest bootstrap
```

## Core Commands

Bootstrap:

```bash
npm run bootstrap
node dist/cli/index.js bootstrap --target claude
node dist/cli/index.js bootstrap --targets codex,claude,opencode,gemini,hermes --json
node dist/cli/index.js bootstrap --target claude --home /tmp/test-home
```

List detected assets from the current user profile:

```bash
node dist/cli/index.js list
node dist/cli/index.js list --target gemini --json
node dist/cli/index.js list --target claude --home /tmp/test-home
```

Inspect detailed target state:

```bash
node dist/cli/index.js inspect
node dist/cli/index.js inspect --targets codex,opencode
node dist/cli/index.js inspect --target claude --home /tmp/test-home
```

Verify managed installs against live target homes:

```bash
node dist/cli/index.js doctor
node dist/cli/index.js doctor --target claude --json
node dist/cli/index.js doctor --target claude --home /tmp/test-home
```

## Typical Workflow

1. Clone this repo.
2. Add your own skills under `skills/owned/`, or add source definitions under `catalog/skills/` and `catalog/plugins/`.
3. Run bootstrap.
4. Run `list` to see what is present under the current user profile.
5. Run `doctor` if you want to verify that managed installs recorded in the manifest still exist on disk.

If you want the full Chinese explanation of the YAML config scheme and the exact live catalog now checked into this repo, read:

- [docs/CATALOG-CONFIG.md](D:\Growth_up_youth\repo\skills\docs\CATALOG-CONFIG.md)

If you want a Chinese explanation of how GSD is designed, why `$gsd-*` commands can take parameters, and how the main workflows connect, read:

- [docs/GSD-WORKFLOW.md](D:\Growth_up_youth\repo\skills\docs\GSD-WORKFLOW.md)

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

Files under `catalog/skills/*.yaml` and `catalog/plugins/*.yaml` are live config.

## Add Your Own Skill

Create a directory under `skills/owned/` and put a `SKILL.md` in it:

```text
skills/owned/my-review-workflow/SKILL.md
```

Then rerun bootstrap:

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
```

For GitHub sources, `assets` is optional. If you omit it, bootstrap expands the whole parent directory declared in `github.path`.

Field notes:

- `repo`: GitHub repo in `owner/name` format
- `ref`: optional branch, tag, or commit
- `path`: optional parent directory inside the repo that contains the assets you want to scan
- `assets`: optional for both `github` and `command`
- `assets[].id`: optional local asset id; if omitted, it is derived from `assets[].path`
- `assets[].kind`: optional; inferred from whether the file lives under `catalog/skills` or `catalog/plugins`
- `assets[].path`: path to the source asset inside the repo, relative to `github.path`

`id` vs `path`:

- `path` answers "where is the source asset"
- `id` answers "what local name should this project use"
- if you do not need renaming, omit `id` and let it follow the directory or file name from `path`

When `assets` is omitted:

- skill catalogs scan first-level directories under `github.path` and keep the ones that contain `SKILL.md`
- plugin catalogs scan first-level directories and first-level JavaScript or TypeScript files under `github.path`
- command catalogs treat the whole source as one logical asset and default its id to the source `id`

Common GitHub source shapes:

Default all assets:

```yaml
sources:
  - id: claude-official
    type: github
    github:
      repo: anthropics/skills
      ref: main
      path: skills
```

Single asset:

```yaml
sources:
  - id: claude-official
    type: github
    github:
      repo: anthropics/skills
      ref: main
      path: skills
    assets:
      - path: docx
```

Multiple assets:

```yaml
sources:
  - id: claude-official
    type: github
    github:
      repo: anthropics/skills
      ref: main
      path: skills
    assets:
      - path: docx
      - path: pdf
      - path: xlsx
```

`assets` is always an array:

- one asset means one `-` item under `assets:`
- multiple assets means multiple `-` items under `assets:`

## Add a Command-Based Skill Source

In this repo, `command` is mainly for upstream installers like GSD.

That means:

- bootstrap does not copy a local `SKILL.md` directory
- it executes the upstream install command directly
- the upstream installer may write Claude `skills`, `commands`, `agents`, `hooks`, or other files under the target home

Declare it under `catalog/skills/`, for example:

```text
catalog/skills/gsd.yaml
```

Then add:

```yaml
sources:
  - id: gsd
    type: command
    enabled: true
    description: Install or update Get Shit Done across Claude, Codex, OpenCode, and Gemini
    command:
      run: npx get-shit-done-cc --all --global
```

If you omit `assets` on a command source, this project treats it as one logical installed pack and uses the source id as the asset id. For the current repo, that is the intended shape for `gsd`.

At runtime, delegated installers receive:

- `AIMAGICIAN_TARGETS`
- `AIMAGICIAN_SOURCE_ID`
- `AIMAGICIAN_ASSET_IDS`
- `AIMAGICIAN_WORKSPACE_ROOT`
- `AIMAGICIAN_HOME_DIR`
- `AIMAGICIAN_CODEX_SKILLS_DIR`
- `AIMAGICIAN_CLAUDE_SKILLS_DIR`
- `AIMAGICIAN_OPENCODE_SKILLS_DIR`
- `AIMAGICIAN_GEMINI_EXTENSIONS_DIR`

And when you override home with `--home`, the installer also receives a rewritten `HOME` and the common user-directory variables for that platform.

For command-based sources like GSD, `list` and `inspect` show them under `command sources` / `command installs`. They may not appear under `skills:` because the upstream installer is free to manage commands, agents, hooks, and support files outside the plain skills directory.

Current GSD default in this repo uses the all-target installer, so the upstream command itself installs Claude, Codex, OpenCode, and Gemini in one run:

```bash
npx get-shit-done-cc --all --global
```

## Example: Only Use Anthropic Official Claude Skills

Create:

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
```

Then run:

```bash
npm run bootstrap -- --target claude
```

Reference:

- Anthropic official skills repo: `https://github.com/anthropics/skills`

If you only want a subset, add explicit `assets` entries and point `path` at the skill directory name, for example `docx`, `pdf`, or `xlsx`.

Single official skill:

```yaml
sources:
  - id: claude-official
    type: github
    targets:
      include:
        - claude
    github:
      repo: anthropics/skills
      ref: main
      path: skills
    assets:
      - path: docx
```

Multiple official skills:

```yaml
sources:
  - id: claude-official
    type: github
    targets:
      include:
        - claude
    github:
      repo: anthropics/skills
      ref: main
      path: skills
    assets:
      - path: docx
      - path: pdf
      - path: xlsx
```

## Example: Add a Supported OpenCode Plugin

OpenCode plugins currently work when the asset is a JavaScript or TypeScript file.

Create:

```text
catalog/plugins/opencode-tools.yaml
```

with:

```yaml
sources:
  - id: opencode-tools
    type: github
    enabled: true
    targets:
      include:
        - opencode
    github:
      repo: owner/opencode-plugins
      ref: main
      path: plugins
    assets:
      - path: audit-helper.ts
```

Then run:

```bash
npm run bootstrap -- --target opencode
```

That installs the plugin file into:

```text
~/.config/opencode/plugins/audit-helper.ts
```

## Example: Declare Anthropic Official Claude Plugins

Claude plugin entries can be tracked in `catalog/plugins/`, but bootstrap will report an explicit skip rather than pretending they were installed.

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
      path: external_plugins
```

What happens today:

- the plugin metadata is valid in this repo
- bootstrap reports why Claude plugin automation was skipped
- you should still use Claude Code's native plugin flow for actual installation

This default-all form maps directly to the official directory layout, where `external_plugins/<plugin-id>/` is the unit you want to track.

Single official plugin:

```yaml
sources:
  - id: claude-official-plugins
    type: github
    targets:
      include:
        - claude
    github:
      repo: anthropics/claude-plugins-official
      ref: main
      path: external_plugins
    assets:
      - path: github
```

Multiple official plugins:

```yaml
sources:
  - id: claude-official-plugins
    type: github
    targets:
      include:
        - claude
    github:
      repo: anthropics/claude-plugins-official
      ref: main
      path: external_plugins
    assets:
      - path: github
      - path: linear
      - path: playwright
```

According to Anthropic's official plugin directory flow:

```text
/plugin install {plugin-name}@claude-plugin-directory
```

References:

- Anthropic official plugin directory: `https://github.com/anthropics/claude-plugins-official`
- Anthropic official skills repo: `https://github.com/anthropics/skills`

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

Supported target names:

- `codex`
- `claude`
- `opencode`
- `gemini`
- `hermes`

## Override Home

If you do not pass anything, the CLI uses the current user's `~/`.

If you want an isolated target home without writing an extra wrapper script, pass `--home`:

```bash
node dist/cli/index.js bootstrap --target claude --home /tmp/test-home
node dist/cli/index.js list --target claude --home /tmp/test-home
node dist/cli/index.js doctor --target claude --home /tmp/test-home
```

That makes the CLI behave as if `~/` were `/tmp/test-home`.

For command-based sources, `--home` also rewrites the process environment that installer scripts usually read, including:

- `AIMAGICIAN_HOME_DIR`
- `HOME`
- `USERPROFILE`
- `APPDATA`
- `LOCALAPPDATA`
- `XDG_CONFIG_HOME`
- `XDG_STATE_HOME`
- `AIMAGICIAN_HERMES_SKILLS_DIR`

## User-Level Locations

Bootstrap currently writes to these user-level locations:

- Codex skills: `~/.codex/skills`
- Claude Code skills: `~/.claude/skills`
- OpenCode skills: `~/.config/opencode/skills`
- OpenCode plugins: `~/.config/opencode/plugins`
- Gemini generated skill extensions: `~/.gemini/extensions`
- Hermes skills: `~/.hermes/skills`

Bootstrap state is written to:

- Windows: `%LOCALAPPDATA%\\aimagician-skills`
- Linux: `$XDG_STATE_HOME/aimagician-skills` or `~/.local/state/aimagician-skills`

For isolated runs:

```bash
AIMAGICIAN_HOME_DIR=/tmp/aimagician-home \
AIMAGICIAN_CONFIG_HOME=/tmp/aimagician-home/.config \
AIMAGICIAN_WORKSPACE_ROOT=/tmp/aimagician-skills \
node dist/cli/index.js bootstrap --targets claude,gemini
```

## Verify

After bootstrap, the recommended verification flow is:

```bash
node dist/cli/index.js list
node dist/cli/index.js inspect --target gemini
node dist/cli/index.js doctor
```

Project verification:

```bash
npm test
npm run build
```
