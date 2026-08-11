# Project Memory

## Authority

This is a recovery index. Explicit user decisions, `.planning/PROJECT.md`, `.planning/CONTEXT.md`, accepted requirements, current code, and runtime evidence take precedence.

## Architecture And Invariants

| Fact | Evidence | Status |
|---|---|---|
| Active distributable Skills live in `skills/owned`; archived capabilities live in `skills/archived` and are not installed | Repository layout and bootstrap tests | Verified |
| Runtime Skill packages contain capability instructions and helpers; behavioral eval corpora live under `quality/skill-evals` | `USR-20260811-001` | Accepted |
| The catalog has six top-level categories: build, research, design, documents, operate, strategy | `catalog/taxonomy.yaml` | Verified |
| Installed Codex and OpenCode Skill trees must mirror the owned catalog and prune unmanaged Skill directories | bootstrap and doctor behavior | Accepted |

## Accepted Preferences

| Preference | Source | Scope |
|---|---|---|
| Use the shortest reliable engineering path scaled by risk; management closure follows core delivery | `aimagician-superpower` and user workflow decisions | Repository |
| Linear uses Composio CLI and remains optional to core delivery | `.planning/preferences/linear.md` | Repository |
| Durable project memory uses `.planning/memory/memory.md` plus bounded daily notes | `USR-20260811-001` | Repository |

## Active Risks And Open Decisions

| Item | Owner | Evidence / decision needed |
|---|---|---|
| The presentation capability is scheduled for a later `pptx-studio` migration; do not fold that migration into unrelated Skill cleanup | Future milestone | `.planning/PROJECT.md` and `.planning/CONTEXT.md` |

## Recent Resume Points

| Date | Task | Daily note |
|---|---|---|
| 2026-08-11 | Runtime-pure Skills, project memory, and session orchestration | `2026-08-11.md` |
