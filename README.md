<h1 align="center">Skillbird</h1>

<p align="center">
  <em>Owned skills that turn AI coding CLIs into evidence-driven engineering and design agents</em>
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

`aimagician_superpower` is the consolidated home for my AI-agent workflow skills. It encodes senior engineering and design procedures as progressive modules, templates, executable decision rules, and verification gates so quality depends less on a model's unstated experience.

The daily command is `skillbird`. It manages skills across Codex, Claude, OpenCode, Gemini, Hermes, Cursor, and Copilot with global or project-local installs.

The important change: owned skills are now the source of truth. External collections such as GSD, Superpowers, selected Claude skills, UI packs, and Playwright skills are curated into owned skills or kept as disabled reference material. Bootstrap installs only the active owned set by default.

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

Skillbird keeps one risk-scaled workflow model:

1. Recover the active Skill, planning state, project docs, wiki, and git context.
2. Establish the measurable target, boundary, risk, success criteria, and non-goals.
3. Discuss baseline requirements and create a draft specification when the risk gate requires it.
4. Research local evidence and current external facts, then compare viable approaches.
5. Re-discuss changed boundaries and assumptions; lock falsifiable requirements only after ambiguity passes.
6. Plan atomic requirement-backed tasks and independently review substantial plans.
7. Execute with test-first slices, checkpoints, and bounded Agent roles.
8. Review specification compliance before code quality.
9. Verify requirement-to-plan-to-evidence traceability and run user-facing UAT.
10. Audit, hand off, and close only when accepted requirements have passing evidence.

The workflow stays light for a reversible one- or two-file edit. Public APIs, schema/data changes, security, integrations, UI/AI contracts, production state, cross-module work, and multi-Agent execution use a formal `SPEC.md` with an ambiguity gate.

The installed skill includes a dependency-free runtime:

```bash
node scripts/workflow.mjs status --project <path> --phase <phase>
node scripts/workflow.mjs validate --project <path> --phase <phase> --gate spec
node scripts/workflow.mjs validate --project <path> --phase <phase> --gate execute
node scripts/workflow.mjs trace --project <path> --phase <phase> --format json
node scripts/workflow.mjs next --project <path> --phase <phase>
```

The `execute` gate requires completed research, renewed discussion, implementation context, requirement-mapped plans, and explicit plan acceptance. `init` previews project and phase artifacts and writes only with `--write`; it never overwrites existing files or follows a planning symlink outside the project. Condition-based waiting and filesystem pollution isolation are available through `wait-for.mjs` and `find-polluter.mjs`.

Engineering work also has a deterministic advisor for codebase analysis, progressive discovery, bounded prototypes, feature delivery, root-cause repair, refactoring, performance, and architecture changes:

```bash
node skills/owned/aimagician-superpower/scripts/engineering-route.mjs --kind feature --risk medium --format json
```

The route selects the required context map, design record, vertical slices, test seams, migration strategy, review axes, and completion evidence. Detailed integration decisions are recorded in [`docs/superpowers/mattpocock-engineering-capability-merge.md`](docs/superpowers/mattpocock-engineering-capability-merge.md).

The combined trigger, capability, boundary, and real-project validation is recorded in [`docs/audits/skill-capability-audit-2026-07-21.md`](docs/audits/skill-capability-audit-2026-07-21.md).

The central owned skill is:

| Skill | Role |
|---|---|
| `aimagician-superpower` | Risk-scaled SDD plus codebase exploration, progressive discovery, prototypes, engineering design, vertical delivery, root-cause debugging, technical review, traceable verification, audit, and handoff |
| `interface-design` | HTML/CSS/JS design, prototypes, UI, dashboards, repository branding, covers, posters, product demo video, creative coding, data visualization, HTML presentations, responsive browser QA, and brand routing |
| `github-readme-highstar` | README information architecture, quick-start clarity, repository visual collaboration, static hero and supplemental demo integration |
| `skill-creator` | Skill authoring, merging, taxonomy, formatter rules |

## Skill Consolidation

External sources are curated into owned skills instead of installed by default.

| Source area | New owned path |
|---|---|
| GSD + Superpowers planning/execution | `aimagician-superpower` |
| CLI agent orchestration, preferring OpenCode for broad read-only exploration | `cli-agent-orchestrator` |
| Composio SaaS tool routing and MCP-light discovery | `composio-tool-router` |
| Claude skill creator + Superpowers skill writing | `skill-creator` |
| Claude MCP builder + community MCP builder | `mcp-builder` |
| frontend-design, design-md brand routing, UI/UX, prototypes, dashboards, data visualization, HTML presentations, accessibility, motion, design-lab, impeccable | `interface-design` |
| Claude webapp-testing + Playwright skill | `webapp-testing` |
| docx / pdf / pptx / xlsx | Owned document skills under `skills/owned` |

Six categories are used everywhere:

| Category | Scope |
|---|---|
| `build` | Coding, planning, debugging, tests, reviews, skill authoring, MCP/tools |
| `research` | Papers, literature, open-source architecture, repo evidence |
| `design` | HTML visual design, prototypes, UI/UX, dashboards, data visualization, HTML presentations, brand routing, accessibility, motion, image generation |
| `documents` | README, Word, PDF, PowerPoint, spreadsheets |
| `operate` | GitHub, Linear, cloud, worktrees, releases, CLI agent orchestration, Composio tool routing |
| `strategy` | Product, business, pricing, customers, growth |

Every owned skill is formatted with `category`, `subcategory`, and `tags` frontmatter:

```bash
skillbird format-skills --check
skillbird format-skills --write
```

### HTML And PowerPoint Boundary

`interface-design` owns browser-native visual work and rendered visual assets: apps, prototypes, landing pages, dashboards, interactive reports, repository covers, autoplay GIF heroes, posters, product showcases, deterministic demo video, creative coding, data visualization, narrated motion, and HTML slides. `github-readme-highstar` owns the surrounding README structure and integration.

Ordinary native editable `.pptx`, slide masters, Office compatibility, and PowerPoint QA remain owned by `pptx` or `window-pptx`. When a user explicitly requires HTML as the presentation source, `interface-design` also owns HTML-first PDF and PPTX derivatives. HTML-first PPTX has two explicit modes: native editable DOM-to-PowerPoint objects, or visually faithful image-backed slides. The agent must select editability versus fidelity before implementation.

The HTML design skill includes layout, component, and 40-direction pattern libraries; content-to-pattern decision rules; three-direction comparison and live tweak scaffolds; device frames; browser Deck, PDF, editable/fidelity PPTX, GIF/MP4/alpha overlays, provider-neutral narration, audio mixing, semantic motion-review packages, and visual-quality workflows; plus a deterministic Playwright/ffmpeg renderer, optional project render adapters, and a read-only router:

```bash
node skills/owned/interface-design/scripts/design-router.mjs --task dashboard --deliverable html --signals trends,comparison --format json
node skills/owned/interface-design/scripts/design-router.mjs --task readme-cover --deliverable image --signals developer-tool,terminal --format json
node skills/owned/interface-design/scripts/design-router.mjs --task product-demo --deliverable video --signals workflow,motion --format json
node skills/owned/interface-design/scripts/design-router.mjs --task product-demo --deliverable gif --signals workflow,motion --format json
node skills/owned/interface-design/scripts/design-router.mjs --task html-presentation --deliverable pptx --pipeline html-first --pptx-mode editable --format json
node skills/owned/interface-design/scripts/render-motion-media.mjs --input demo.html --output-dir assets --name demo --formats poster,mp4,gif
node skills/owned/interface-design/scripts/export-html-deck-pptx.mjs --slides slides --out deck.pptx --mode editable
```

See [`docs/design/html-universal-design-capability-merge.md`](docs/design/html-universal-design-capability-merge.md) for the capability analysis and boundary decisions.

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
