# Project Memory

## Authority

This is a recovery index. Explicit user decisions, `.planning/PROJECT.md`, `.planning/CONTEXT.md`, accepted requirements, current code, and runtime evidence take precedence.

## Architecture And Invariants

| Fact | Evidence | Status |
|---|---|---|
| Active distributable Skills live in `skills/owned`; archived capabilities live in `skills/archived` and are not installed | Repository layout and bootstrap tests | Verified |
| Always-on generic habits live in `rules/owned` (6 rules); they are not skills and are not in the default install set | `docs/RULES-AND-MEMORY.md`, `tests/rules/owned-rules.test.ts` | Accepted |
| Memory policy lives in `memory/owned/project-memory-policy`; live stores are `~/.skillbird/memory/` and `.planning/memory/` | `USR-20260811-001` plus 2026-08-19 lock | Accepted |
| Default worker is the current host's native subagent; `cli-agent-delegator` is archived | Commit `8444d68`, CTX-DEC-010 | Accepted |
| Runtime Skill packages contain capability instructions and helpers; behavioral eval corpora live under `quality/skill-evals` | `USR-20260811-001` | Accepted |
| The catalog has six top-level categories: build, research, design, documents, operate, strategy | `catalog/taxonomy.yaml` | Verified |
| Active owned skill count is 23 | `skills/owned`, `skillbird format-skills --check` | Verified |
| Installed Codex and OpenCode Skill trees must mirror the owned catalog and prune unmanaged Skill directories | bootstrap and doctor behavior | Accepted |
| Skillbird does not yet project rules or memory onto CLI homes | `src/model/targets.ts` still skill/plugin; leftover in `docs/RULES-AND-MEMORY.md` | Open |

## Accepted Preferences

| Preference | Source | Scope |
|---|---|---|
| Use the shortest reliable engineering path scaled by risk; management closure follows core delivery | `aimagician-superpower` and user workflow decisions | Repository |
| Linear uses Composio CLI and remains optional to core delivery | `.planning/preferences/linear.md` | Repository |
| Durable project memory uses `.planning/memory/memory.md` plus bounded daily notes | `USR-20260811-001` | Repository |
| Native vision and host subagent before substitute skills or foreign CLIs | `rules/owned/native-capability-first`, `host-native-delegation` | Cross-project |

## Active Risks And Open Decisions

| Item | Owner | Evidence / decision needed |
|---|---|---|
| The presentation capability is scheduled for a later `pptx-studio` migration; do not fold that migration into unrelated Skill cleanup | Future milestone | `.planning/PROJECT.md` and `.planning/CONTEXT.md` |
| Skillbird rule/memory CLI projection is not implemented | Later engine slice | `docs/RULES-AND-MEMORY.md` leftovers |
| `workflow.mjs` complete-gate still requires `Provider: OpenCode` | Next optimization | `validateOpenCodeAudit` |

## Recent Resume Points

| Date | Task | Daily note |
|---|---|---|
| 2026-08-21 | Living docs + rules/memory context for later agents | `2026-08-21.md` |
| 2026-08-11 | Runtime-pure Skills, project memory, and session orchestration | `2026-08-11.md` |
