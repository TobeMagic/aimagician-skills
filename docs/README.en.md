# Skillbird

`aimagician_superpower` is an owned-skill-first expert workflow system for AI coding CLIs. Engineering and design judgment is encoded in progressive modules, structured artifacts, executable decision rules, and evidence gates instead of being left to model intuition.

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
| `aimagician-superpower` | Risk-scaled SDD, codebase exploration, engineering design, vertical delivery, debugging, review, verification, audit, and handoff |
| `cli-agent-orchestrator` | Orchestrate external CLI agents for bounded multi-agent work; prefer OpenCode for broad read-only exploration and context gathering |
| `composio-tool-router` | Route SaaS tool discovery and execution through Composio CLI with service-scoped lookup and schema-on-demand |
| `skill-creator` | Create, merge, classify, and verify skills |
| `interface-design` | Universal HTML/CSS/JS design for prototypes, UI, dashboards, data visualization, marketing pages, HTML presentations, brand routing, and browser QA |
| `webapp-testing` | Playwright and browser verification workflow |
| `mcp-builder` | MCP server and tool-schema design workflow |

## Expert Capability Routes

The engineering advisor covers analysis, feature work, bugs, refactors, performance, and architecture:

```bash
node skills/owned/aimagician-superpower/scripts/engineering-route.mjs --kind refactor --risk high --format json
```

The design advisor maps content and artifact requirements to HTML layout/component patterns and quality gates:

```bash
node skills/owned/interface-design/scripts/design-router.mjs --task dashboard --deliverable html --signals trends,comparison --format json
```

`interface-design` owns browser-native artifacts and HTML slides. Editable `.pptx`, slide masters, Office compatibility, and native PowerPoint QA remain owned by `pptx` or `window-pptx`; hybrid work uses a structured handoff between them.

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
