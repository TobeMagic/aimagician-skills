<p align="center">
  <img src="./assets/readme-cover.webp" alt="Skillbee cover" width="100%" />
</p>

<h1 align="center">🐝 Skillbee</h1>

<p align="center">
  <em>Personal skill manager, catalog, and deployment toolkit for AI CLI tools</em>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/skillbee"><img src="https://img.shields.io/npm/v/skillbee?color=22D4FF&label=version" alt="npm version" /></a>
  <a href="https://www.npmjs.com/package/skillbee"><img src="https://img.shields.io/npm/dm/skillbee?color=3EA4FF" alt="npm downloads" /></a>
  <a href="../LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
</p>

<p align="center">
  <b><a href="#quick-start">Quick Start</a></b> ·
  <b><a href="#cli-commands">CLI</a></b> ·
  <b><a href="#owned-skills">Skills</a></b>
</p>

> Chinese-first full docs: [../README.md](../README.md)

---

## Quick Start

```bash
npm install -g skillbee
skillbee
```

Or:

```bash
npx skillbee@latest
```

Install everything to all CLIs:

```bash
npx skillbee@latest bootstrap
```

---

## Local Development

Clone and run from source:

```bash
git clone https://github.com/TobeMagic/aimagician-skills.git
cd aimagician-skills
npm install
npm run build

# Launch the Dashboard TUI
node .

# Or install all skills to all targets
npm run bootstrap
```

Development workflow:

```bash
npm run typecheck     # Fast type-check (no build)
npm run build         # Full build (clean + compile)
npm test              # Run unit tests
npm link              # Make 'skillbee' available globally
```

After making changes, rebuild and test:

```bash
npm run build && npm test
node .
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `skillbee` | Open Dashboard TUI |
| `skillbee search <query>` | Search catalog |
| `skillbee install <id> --target <t>` | Install a skill |
| `skillbee uninstall <id>` | Remove a skill |
| `skillbee bootstrap` | Full install to all CLIs |
| `skillbee list` | List installed per target |
| `skillbee inspect --target <t>` | Inspect target directory |
| `skillbee doctor` | Health check |
| `skillbee reset --target <t>` | Reset and reinstall |

---

## Dashboard TUI

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate skills |
| `space` | Multi-select |
| `i` `u` | Install / uninstall |
| `t` | Target multi-select |
| `tab` | Cycle primary target |
| `f` | Filter panel |
| `v` | Toggle list / matrix view |
| `/` | Search |
| `x` | Archive toggle |
| `g` | Global / project scope |
| `a` | Show / hide archived |
| `T` | Cycle theme |
| `?` | Help |
| `q` | Quit |

---

## Owned Skills

`academic-paper-workflow`, `baseline-ui`, `cloudflare-image-gen`, `code-guidelines`, `deep-research-system`, `design-lab`, `design-md-brand-router`, `gcloud-ops-workflow`, `github-pr-workflow`, `github-readme-highstar`, `linear-issue-workflow`, `llm-know-how-wiki`, `modelscope_imagegen`, `multilingual-diversity-loop`, `opensource-architecture-research`, `parallel-worktree-pr-flow`, `repo-interview-playbook`, `window-pptx`.

Total resolved catalog: **56+ skills**.

---

## Docs

- [CATALOG-CONFIG.md](./CATALOG-CONFIG.md) — YAML catalog reference
- [GSD-WORKFLOW.md](./GSD-WORKFLOW.md) — GSD workflow docs
- [DOC-STYLE.md](./DOC-STYLE.md) — Bilingual doc style guide
