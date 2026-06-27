# Skillbird

`aimagician_superpower` is an owned-skill-first workflow manager for AI coding CLIs.

Daily command:

```bash
npm install -g aimagician_superpower
skillbird
```

Without installing:

```bash
npx aimagician_superpower@latest
```

## What Changed

Skillbird no longer treats external skill repositories as default installers. GSD, Superpowers, selected Claude skills, UI packs, and browser-testing skills are curated into owned skills under `skills/owned`.

External catalog sources remain visible reference material and are disabled by default.

## Core Owned Skills

| Skill | Purpose |
|---|---|
| `aimagician-superpower` | Research-aware milestone workflow, planning, execution, verification, audit, handoff, and code discipline |
| `agentic-repo-explorer` | Delegate large repository exploration to OpenCode and summarize a decision-ready context report |
| `skill-creator` | Create, merge, classify, and verify skills |
| `interface-design` | Consolidated UI, brand DESIGN.md routing, accessibility, metadata, motion, and polish workflow |
| `webapp-testing` | Playwright and browser verification workflow |
| `mcp-builder` | MCP server and tool-schema design workflow |

## Categories

`build`, `research`, `design`, `documents`, `operate`, `strategy`.

Install by category:

```bash
skillbird install --category documents --scope project --target claude
```

Format owned skills:

```bash
skillbird format-skills --check
skillbird format-skills --write
```

## CLI

| Command | Description |
|---|---|
| `skillbird` | Open the TUI dashboard |
| `skillbird search <query>` | Search skills |
| `skillbird install <id> --scope global` | Install selected skills |
| `skillbird install --category build --scope project` | Install a category bundle |
| `skillbird uninstall <id> --scope global` | Remove managed installs |
| `skillbird list --scope global` | List detected installs |
| `skillbird inspect --scope project` | Inspect target paths and manifest state |
| `skillbird doctor --scope global` | Check managed installs |

## Development

```bash
npm install
npm run build
npm test
```
