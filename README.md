<h1 align="center">Skillbird</h1>

<p align="center">
  <em>AImagician Superpower: owned-skill-first workflow management for AI coding CLIs</em>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/aimagician_superpower"><img src="https://img.shields.io/npm/v/aimagician_superpower?color=22D4FF&label=version" alt="npm version" /></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-%3E%3D18-brightgreen" alt="Node" /></a>
  <img src="https://img.shields.io/badge/categories-6-FFB14A" alt="6 categories" />
</p>

<p align="center">
  <b><a href="#quick-start">Quick Start</a></b> ·
  <b><a href="#workflow">Workflow</a></b> ·
  <b><a href="#skill-consolidation">Skill Consolidation</a></b> ·
  <b><a href="#cli">CLI</a></b> ·
  <b><a href="#architecture">Architecture</a></b>
</p>

---

## What It Is

`aimagician_superpower` is the consolidated home for my AI-agent workflow skills.

The daily command is `skillbird`. It manages skills across Codex, Claude, OpenCode, Gemini, Hermes, Cursor, and Copilot with global or project-local installs.

The important change: owned skills are now the source of truth. External collections such as GSD, Superpowers, selected Claude skills, UI packs, and Playwright skills are treated as reference material unless explicitly enabled. No default external installer, no forced update hook, and no automatic upstream noise.

## Quick Start

```bash
npm install -g aimagician_superpower
skillbird
```

Use without installing:

```bash
npx aimagician_superpower@latest
```

Install the core workflow stack globally:

```bash
skillbird install aimagician-superpower skill-creator --scope global
```

Install a whole category into a project:

```bash
skillbird install --category documents --scope project --target claude
```

## Workflow

Skillbird keeps one workflow model:

1. Discuss the phase and success criteria.
2. Plan only after the phase is clear.
3. Execute with the built-in code discipline from `aimagician-superpower`.
4. Verify with tests, browser checks, or document-specific validation.
5. Resume through the GSD-style milestone state instead of scattering plans across many skills.

The central owned skill is:

| Skill | Role |
|---|---|
| `aimagician-superpower` | GSD state machine backbone + Superpowers quality gates + built-in code discipline + local workflow ownership |
| `skill-creator` | Skill authoring, merging, taxonomy, formatter rules |

## Skill Consolidation

External sources are curated into owned skills instead of installed by default.

| Source area | New owned path |
|---|---|
| GSD + Superpowers planning/execution | `aimagician-superpower` |
| Claude skill creator + Superpowers skill writing | `skill-creator` |
| Claude MCP builder + community MCP builder | `mcp-builder` |
| frontend-design, baseline-ui, accessibility, metadata, motion, design-lab, impeccable | `interface-design` |
| Claude webapp-testing + Playwright skill | `webapp-testing` |
| docx / pdf / pptx / xlsx | Owned document skills under `skills/owned` |

Six categories are used everywhere:

| Category | Scope |
|---|---|
| `build` | Coding, planning, debugging, tests, reviews, skill authoring, MCP/tools |
| `research` | Papers, literature, open-source architecture, repo evidence |
| `design` | UI, brand, accessibility, metadata, motion, image generation |
| `documents` | README, Word, PDF, PowerPoint, spreadsheets |
| `operate` | GitHub, Linear, cloud, worktrees, releases |
| `strategy` | Product, business, pricing, customers, growth |

Every owned skill is formatted with `category`, `subcategory`, and `tags` frontmatter:

```bash
skillbird format-skills --check
skillbird format-skills --write
```

## CLI

| Command | Description |
|---|---|
| `skillbird` | Open the TUI dashboard |
| `skillbird search <query>` | Search skills |
| `skillbird search --category build` | Search by category |
| `skillbird install <id> --scope global` | Install selected skills |
| `skillbird install --category documents --scope project` | Install a category bundle |
| `skillbird uninstall <id> --scope global` | Remove managed installs |
| `skillbird list --scope global` | List detected target installs |
| `skillbird inspect --scope project` | Inspect target paths and manifest state |
| `skillbird doctor --scope global` | Health check managed installs |
| `skillbird reset --target claude --scope project --install-all --yes` | Rebuild a target scope |
| `skillbird bootstrap` | Legacy all-selected bootstrap workflow |

Useful flags:

```bash
--target claude                 # repeatable single target
--targets codex,claude,cursor   # comma-separated targets
--scope global|project          # user-level or project-local install
--category build                # category selector
--subcategory browser-testing   # subcategory selector
--tag verification              # tag selector
--include-archived              # include archived skills
--json                          # machine-readable output
```

## Architecture

```text
skills/
  owned/<skill-id>/SKILL.md      owned skills, default source of truth
  archived/                      archived local skills
catalog/
  taxonomy.yaml                  six-category classification
  skills/*.yaml                  disabled external references
src/
  cli/                           skillbird command surface
  manager/                       search/install/format workflows
  bootstrap/                     target resolution and sync engine
```

State paths:

| Scope | Path |
|---|---|
| Global config | `~/.config/skillbird/global/config.yaml` |
| Global state | `~/.local/state/aimagician-superpower/manifest.json` |
| Project config | `<project>/.skillbird/config.yaml` |
| Project state | `<project>/.skillbird/manifest.json` |

## Development

```bash
npm install
npm run build
npm test
```

Run from source:

```bash
node dist/cli/index.js --help
node dist/cli/index.js search --category build
```

## License

MIT — see [LICENSE](./LICENSE).
