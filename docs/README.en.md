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
| `aimagician-superpower` | Risk-scaled SDD, codebase exploration, progressive discovery, prototypes, engineering design, vertical delivery, debugging, review, verification, audit, and handoff |
| `cli-agent-delegator` | Delegate broad discovery, deep research, bounded short git/test/write work, reasoning over acquired visual evidence, and independent review to OpenCode while the main Agent retains final judgment |
| `vision-analysis` | Acquire consent-gated image evidence through the direct Agnes API and return sanitized provenance for downstream reasoning |
| `system-prompt-engineering` | Design and audit system prompts with routed guidance for tools, delegation, safety, memory, search, channels, coding agents, and evaluation |
| `composio-tool-router` | Route SaaS tool discovery and execution through Composio CLI with service-scoped lookup and schema-on-demand |
| `skill-creator` | Create, merge, classify, and verify skills |
| `skill-optimizer` | Audit and improve Skills with controlled baseline/treatment tests, independent review, and no automatic Git mutation |
| `knowledge-distillation` | Turn long-form sources into traceable executable Skill systems |
| `perspective-distillation` | Build evidence-backed person or topic perspective Skills with ethical and uncertainty boundaries |
| `interface-design` | Universal HTML/CSS/JS design for prototypes, UI, dashboards, repository covers, posters, product video, creative coding, data visualization, marketing pages, HTML presentations, brand routing, and browser/media QA |
| `github-readme-highstar` | README information architecture, quick-start clarity, repository visual collaboration, and final Markdown integration |
| `webapp-testing` | Playwright and browser verification workflow |
| `mcp-builder` | MCP server and tool-schema design workflow |

## Expert Capability Routes

The engineering advisor covers analysis, progressive discovery, bounded prototypes, feature work, bugs, refactors, performance, and architecture:

```bash
node skills/owned/aimagician-superpower/scripts/engineering-route.mjs --kind refactor --risk high --format json
node skills/owned/aimagician-superpower/scripts/engineering-route.mjs --kind prototype --risk medium --format json
```

The design advisor maps content and artifact requirements to HTML layout/component patterns and quality gates:

```bash
node skills/owned/interface-design/scripts/design-router.mjs --task dashboard --deliverable html --signals trends,comparison --format json
node skills/owned/interface-design/scripts/design-router.mjs --task readme-cover --deliverable image --signals developer-tool,terminal --format json
node skills/owned/interface-design/scripts/design-router.mjs --task product-demo --deliverable video --signals workflow,motion --format json
```

`interface-design` owns browser-native artifacts, rendered still/video assets, and HTML slides. Its standard single-file slide player includes keyboard, wheel, touch, overview-card, full-screen, progress, hash, persistence, and print behavior, with fidelity PPTX export from the live HTML stage. Editable `.pptx`, slide masters, Office compatibility, and native PowerPoint QA remain owned by `pptx` or `pptx-studio`; editable HTML-first PPTX uses independent slide files, while hybrid native work uses a structured handoff.

The catalog contains 26 active owned Skills. Full upstream repositories used for consolidation remain ignored audit references and are not installed or packaged. The distillation, optimization, HTML presentation, and YapCLI validation record is in [`audits/distillation-and-html-presentation-optimization-2026-07-27.md`](audits/distillation-and-html-presentation-optimization-2026-07-27.md).

The full trigger, capability, boundary, and YapCLI validation report is in [`audits/skill-capability-audit-2026-07-21.md`](audits/skill-capability-audit-2026-07-21.md).

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
| `skillbird --agent capabilities` | Return the versioned non-interactive Agent contract |

Agent mode emits stable ANSI-free JSON. Read commands execute immediately; write commands preview unless `--yes` is present:

```bash
skillbird --agent list --scope global --target codex
skillbird --agent install aimagician-superpower --scope global --target codex
skillbird --agent install aimagician-superpower --scope global --target codex --yes
```

## Development

```bash
npm install
npm run build
npm test
```
