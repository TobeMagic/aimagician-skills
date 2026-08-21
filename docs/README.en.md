# Skillbird

`aimagician_superpower` is an owned-skill-first workflow system for AI coding CLIs. It packages engineering, research, design, document, operations, and strategy guidance as progressive modules with executable checks and evidence gates.

<p align="center">
  <img src="./assets/skillbird-readme-hero.webp" alt="Skillbird local-first skill registry syncing an owned catalog to AI coding agents" width="100%" />
</p>

<p align="center">
  <img src="./assets/skillbird-readme-demo.gif" alt="Skillbird demo showing category selection and synchronized agent targets" width="100%" />
</p>

Daily command:

```bash
npm install -g aimagician_superpower
skillbird
```

Without installing:

```bash
npx aimagician_superpower@latest
```

## Source Of Truth

The current active set is `skills/owned`, plus always-on habits in `rules/owned` and memory policy in `memory/owned`. External catalog entries remain disabled references, and archived Skills remain recoverable under `skills/archived` without entering the default install set.

The repository currently contains 23 active owned Skills across six categories:

`build`, `research`, `design`, `documents`, `operate`, `strategy`.

Evaluation corpora live under `quality/skill-evals` and are not installed into runtime Skill directories. User memory lives under `~/.skillbird/memory/`; project memory lives under `.planning/memory/`. Later agents should start from [`RULES-AND-MEMORY.md`](RULES-AND-MEMORY.md). Skillbird still syncs skills only; rule and memory projection to CLI targets is a later engine slice.

## Always-On Rules And Memory

| Asset | Role |
|---|---|
| `code-guidelines` | Think, smallest change, surgical diffs |
| `review-before-edit` | Show files, diff, and blast radius before mutating |
| `native-capability-first` | Native vision and host tools before substitute skills |
| `host-native-delegation` | Current host subagent; foreign CLI is opt-in |
| `git-safety` | Commit when asked; no force-push of main/master; no secrets |
| `memory-pointer` | User store `~/.skillbird/memory/` and project store `.planning/memory/` |
| `project-memory-policy` | Read/write policy and templates for those stores |

`cli-agent-delegator` is archived. Load it only when the user names OpenCode or another foreign CLI.

## Core Routes

| Skill | Purpose |
|---|---|
| `aimagician-superpower` | Risk-scaled engineering workflow, project memory, exploration, design, implementation, debugging, verification, audit, and handoff |
| `agent-workstream-orchestrator` | Host-native tracked sessions, optional worktrees, integration, and resumable handoffs |
| `vision-analysis` | Fallback Agnes image understanding when this session cannot see pixels, or when an Agnes evidence package is requested |
| `interface-design` | HTML/CSS/JS visual work, repository branding, prototypes, dashboards, motion, and browser/media QA |
| `github-readme-highstar` | README information architecture, repository visual integration, and GitHub delivery QA |
| `skill-optimizer` | Darwin baseline/treatment evaluation and independent Skill improvement |

Native editable PowerPoint remains owned by `pptx-studio`. HTML visual exploration and HTML-first presentation output remain owned by `interface-design`; they are not a replacement for an editable Office deliverable.

## CLI

| Command | Description |
|---|---|
| `skillbird` | Open the TUI dashboard |
| `skillbird search <query>` | Search owned and eligible catalog entries |
| `skillbird install <id> --scope global` | Install selected Skills globally |
| `skillbird install --category build --scope project` | Install a category bundle into the current project |
| `skillbird uninstall <id> --scope global` | Remove a managed install |
| `skillbird list --scope global` | Inspect target installations |
| `skillbird inspect --scope project` | Inspect project paths and manifests |
| `skillbird doctor --scope global` | Check managed content and target health |
| `skillbird --agent capabilities` | Return the versioned non-interactive contract |

Write operations preview by default in Agent mode and require `--yes` to apply:

```bash
skillbird --agent list --scope global --target codex
skillbird --agent doctor --scope global --target opencode
skillbird --agent install aimagician-superpower --scope global --target codex
skillbird --agent install aimagician-superpower --scope global --target codex --yes
```

## Development

```bash
npm install
npm run build
npm test
```

The reproducible README demo source is [`assets/skillbird-readme-demo.html`](assets/skillbird-readme-demo.html). The static hero and GIF are repository-relative so forks remain renderable without external attachments.

## References

- [Rules and memory](RULES-AND-MEMORY.md)
- [Capability audit](audits/skill-capability-audit-2026-07-21.md)
- [HTML design boundary](design/html-universal-design-capability-merge.md)
- [Runtime purity and memory audit](audits/skill-runtime-purity-memory-2026-08-11.md)

## License

MIT — see [LICENSE](../LICENSE).
