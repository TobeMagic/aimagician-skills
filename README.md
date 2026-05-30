
<h1 align="center">🐝 Skillbee</h1>

<p align="center">
  <em>Personal skill manager, catalog, and deployment toolkit for AI CLI tools</em>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/skillbee"><img src="https://img.shields.io/npm/v/skillbee?color=22D4FF&label=version" alt="npm version" /></a>
  <a href="https://www.npmjs.com/package/skillbee"><img src="https://img.shields.io/npm/dm/skillbee?color=3EA4FF" alt="npm downloads" /></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-%3E%3D18-brightgreen" alt="Node" /></a>
  <img src="https://img.shields.io/badge/targets-7-FFB14A" alt="7 targets" />
  <img src="https://img.shields.io/badge/skills-56%2B-FF6A20" alt="56+ skills" />
</p>

<p align="center">
  <b><a href="#quick-start">Quick Start</a></b> ·
  <b><a href="#features">Features</a></b> ·
  <b><a href="#dashboard-tui">Dashboard</a></b> ·
  <b><a href="#cli-commands">CLI</a></b> ·
  <b><a href="#architecture">Architecture</a></b> ·
  <b><a href="#faq">FAQ</a></b> ·
  <b><a href="#contributing">Contributing</a></b>
</p>

<br>

> **One command** to install, update, and manage skills across all your AI CLI tools — Codex, Claude, OpenCode, Gemini, Hermes, Cursor, and Copilot.

English quick start: [docs/README.en.md](./docs/README.en.md)

---

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Dashboard TUI](#dashboard-tui)
- [CLI Commands](#cli-commands)
- [Architecture](#architecture)
- [Support Matrix](#support-matrix)
- [Owned Skills](#owned-skills)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

```bash
# Install globally
npm install -g skillbee

# Launch the Dashboard TUI
skillbee

# Or try without installing:
npx skillbee@latest
```

**First time?** The Dashboard opens in your terminal. Browse 56+ skills, filter by target or tag, select multiple, and install them all at once.

Want everything everywhere?

```bash
npx skillbee@latest bootstrap
```

That's it — that single command installs all owned skills and resolves catalog sources across every supported CLI on your machine.

---

## Features

| | Capability | Details |
|---|---|---|
| 🎛️ | **Dashboard TUI** | Keyboard-driven terminal UI — navigate, select, filter, install, uninstall |
| 🎯 | **Multi-target install** | Deploy skills to 7+ CLI tools simultaneously |
| 🔎 | **Smart filtering** | Filter by status (installed/missing), target, tags, or search query |
| 👁️ | **List + Matrix views** | `v` to toggle between list mode and target × skill matrix |
| 🎨 | **Multi-theme** | `T` cycles through bee / monokai / nord — persisted in config |
| 📦 | **Batch operations** | Select multiple skills, install or uninstall to all chosen targets at once |
| 🚀 | **Bootstrap mode** | Single command to install everything to every CLI |
| 📋 | **Install report** | Per-target × per-skill result overlay after batch operations |
| 📁 | **Global / Project scope** | Install at user level or per-project |
| 🗂️ | **Archive management** | Hide skills you don't use, toggle visibility with `a` |

---

## Dashboard TUI

Press `?` anytime inside the TUI for the full command reference.

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate skill list |
| `space` | Multi-select / deselect |
| `i` `u` | Install / uninstall selected to targets |
| `t` | Open target multi-select panel |
| `tab` | Cycle single target (within selected set) |
| `f` | Open multi-dimension filter (status / target / tag) |
| `v` | Toggle list / matrix overview view |
| `/` | Search skills by name, tag, or description |
| `x` | Archive / unarchive selected skill |
| `g` | Toggle global / project scope |
| `a` | Toggle archived skill visibility |
| `T` | Cycle theme (bee / monokai / nord) |
| `?` | Show keyboard shortcut reference |
| `q` | Quit |

After install/uninstall, a **report overlay** shows per-target × per-skill results:
- **✓** success &nbsp; **○** skipped &nbsp; **✗** failed

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `skillbee` | Open Dashboard TUI |
| `skillbee search <query>` | Search skills in catalog |
| `skillbee install <id> --target <t>` | Install a specific skill |
| `skillbee uninstall <id>` | Remove a skill |
| `skillbee bootstrap` | Install all skills to all targets |
| `skillbee list` | List installed skills per target |
| `skillbee inspect --target <t>` | Inspect target skill directory |
| `skillbee doctor` | Health check |
| `skillbee reset --target <t>` | Reset and reinstall on a target |

**Flags:**
- `--scope global|project` — install at user level or project-local
- `--dry-run --json` — preview changes without touching files
- `--targets codex,claude,opencode` — comma-separated target list

Examples:

```bash
# Search for paper-related skills in project scope
skillbee search paper --scope project

# Install a specific skill to two targets
skillbee install deep-research-system --target claude --target opencode --scope global

# Full bootstrap to specific targets (dry-run)
skillbee bootstrap --targets codex,claude,opencode --dry-run --json
```

---

## Architecture

```
skills/
  owned/<skill-id>/SKILL.md     # 17 self-authored skill packages
  archived/                      # Archived skills (hidden by default)
catalog/
  skills/*.yaml                  # External skill source definitions (GitHub, command)
  plugins/*.yaml                 # Plugin/extension source references
  taxonomy.yaml                  # Global tags & classification tree
dist/                            # Compiled TypeScript → JS output
docs/                            # Documentation assets & guides
```

**Core flow:**

```
owned skills + catalog sources + command sources
        │
        ▼
   Bootstrap Engine
   (plan → resolve → validate)
        │
        ▼
   Target directories
   (codex / claude / opencode / gemini / hermes / cursor / copilot)
```

Install state is tracked via a **bootstrap manifest** at `~/.local/state/aimagician-skills/manifest.json`. Re-running bootstrap updates existing installs without duplicating.

---

## Support Matrix

| Capability | Status | Notes |
|---|---|---|
| Owned skills | ✅ | `skills/owned/*` synced to all targets |
| GitHub skill sources | ✅ | Cloned from remote, installed per target |
| Command sources | ✅ | Delegated to upstream installer |
| Codex | ✅ | `~/.codex/skills` |
| Claude Code | ✅ | `~/.claude/skills` |
| OpenCode skills | ✅ | `~/.config/opencode/skills` |
| OpenCode plugins | ✅ | `~/.config/opencode/plugins` |
| Gemini extensions | ✅ | `~/.gemini/extensions` |
| Hermes | ✅ | `~/.hermes/skills` |
| Cursor | ✅ | `~/.cursor/skills` |
| Copilot | ✅ | `~/.copilot/skills` |
| Claude plugins | ⏭️ | Skipped — uses marketplace flow |
| Gemini plugin catalog | ⏭️ | Skipped — extension-only |

**Bootstrap state path:**
- Linux: `~/.local/state/aimagician-skills/manifest.json`
- Windows: `%LOCALAPPDATA%\aimagician-skills\manifest.json`

---

## Owned Skills

Skills shipped with the package:

| Skill | Description |
|-------|-------------|
| `academic-paper-workflow` | End-to-end academic paper workflow |
| `baseline-ui` | UI validation for Tailwind CSS projects |
| `cloudflare-image-gen` | Image generation via Cloudflare Workers AI |
| `code-guidelines` | Coding standards & minimal-diff guidance |
| `deep-research-system` | Multi-source literature research system |
| `design-lab` | UI design exploration with multiple variations |
| `design-md-brand-router` | Branded DESIGN.md style management |
| `gcloud-ops-workflow` | Google Cloud operations runbook |
| `github-pr-workflow` | PR creation, review & management |
| `github-readme-highstar` | High-star README generation |
| `linear-issue-workflow` | Linear issue lifecycle management |
| `llm-know-how-wiki` | Persistent LLM knowledge base |
| `modelscope_imagegen` | Image generation via ModelScope |
| `multilingual-diversity-loop` | Multi-language output diversity |
| `opensource-architecture-research` | Open-source architecture comparison |
| `parallel-worktree-pr-flow` | Multi-worktree parallel development |
| `repo-interview-playbook` | Interview preparation from repos |
| `window-pptx` | Windows PowerPoint automation |

Total resolved catalog: **56+ skills** (owned + external sources).

---

## FAQ

**Q: What CLIs does Skillbee support?**
A: Codex, Claude, OpenCode, Gemini, Hermes, Cursor, and Copilot.

**Q: How do I install just one skill?**
A: `skillbee install <skill-id> --target <target>` or use the TUI (`space` to select, `i` to install).

**Q: Will bootstrap overwrite my existing skills?**
A: Bootstrap tracks state via a manifest. It updates existing installs without duplicating or overwriting unrelated files.

**Q: Can I install skills per-project?**
A: Yes. Use `--scope project` (CLI) or press `g` (TUI) to toggle between global and project scope.

**Q: How do I add my own skills?**
A: Create a skill directory under `skills/owned/<your-skill>/` with a `SKILL.md`, add it to the catalog, and run bootstrap.

---

## Contributing

PRs and issues are welcome.

```bash
npm run build    # Compile TypeScript
npm test         # Run tests
```

- README changes should also be reflected in `docs/README.en.md`
- See individual skill docs for skill-specific contribution guidelines

## License

MIT — see [LICENSE](./LICENSE).
