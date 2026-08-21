# Rules And Memory

Canonical context for later agents. Read this before changing owned habits, memory policy, Skillbird projection, or default delegation.

Runtime skills stay under `skills/owned`. Always-on habits are **rules**, not skills. Durable facts live in **memory stores**, not in skill bodies.

## Owned Asset Layout

```text
skills/owned/<id>/SKILL.md          23 active skills; default install set
skills/archived/<id>/               recoverable; not installed by default
rules/owned/<id>/RULE.md            6 always-on generic rules
memory/owned/project-memory-policy/ templates and read/write policy
```

`package.json` `files` already ships `skills`, `rules`, and `memory`. Skillbird still installs **skills only**. Projecting rules into Cursor `.mdc`, Claude rules / `CLAUDE.md`, Codex `AGENTS.md`, and writing memory templates into live stores is a later engine slice. Until then, copy or point hosts at `rules/owned` by hand if a session has no other rule channel.

## Always-On Rules

All six are generic. They stay out of any one product codebase. NestJS, Rainbow, Cookie self-test, and casperdai-pages remain project-local.

| ID | Path | Contract |
|---|---|---|
| `code-guidelines` | `rules/owned/code-guidelines/RULE.md` | Think, smallest change, extract after a second use, surgical diffs, verifiable goal |
| `review-before-edit` | `rules/owned/review-before-edit/RULE.md` | File list, before/after, blast radius; wait for 改吧 / 执行 / 按这个改 |
| `native-capability-first` | `rules/owned/native-capability-first/RULE.md` | Native vision and host tools before substitute skills |
| `host-native-delegation` | `rules/owned/host-native-delegation/RULE.md` | Current host subagent only; foreign CLI is opt-in |
| `git-safety` | `rules/owned/git-safety/RULE.md` | Commit when asked; no force-push of main/master; no secrets |
| `memory-pointer` | `rules/owned/memory-pointer/RULE.md` | Where to read and write the two memory stores |

`alwaysApply: true` on every rule. Do not reinstall these IDs as skills.

## Delegation

Default worker is the current host's native subagent (Cursor Agent, Claude Task, Codex subagent, and so on). The controller keeps architecture, risk, reconciliation, validation, and completion.

Do not start OpenCode, Codex, or Cursor as a **foreign** CLI unless the user names that runtime. The former default OpenCode runner lives at `skills/archived/cli-agent-delegator`. Restore or load it only for explicit foreign-CLI work.

Every worker prompt names `OBJECTIVE`, `ALLOWED_SCOPE`, `FORBIDDEN_SCOPE`, `PERMISSION_MODE`, and `STATUS_PROTOCOL` (`DONE` \| `DONE_WITH_CONCERNS` \| `NEEDS_CONTEXT` \| `BLOCKED`).

## Vision

If this session can read pixels, inspect locally. Load `vision-analysis` only when the current model or worker cannot see images, or the user asks for an Agnes evidence package. Pass the sanitized text report downstream; do not attach original images to a text-only worker.

## Memory Stores

Policy: `memory/owned/project-memory-policy/MEMORY.md`.

| Store | Paths |
|---|---|
| User | `~/.skillbird/memory/memory.md`, `~/.skillbird/memory/YYYY-MM-DD.md` |
| Project | `.planning/memory/memory.md`, `.planning/memory/YYYY-MM-DD.md` |

Resume order: user `memory.md`, then project `memory.md`, then today's notes. Do not scan every daily note.

Authority order: accepted requirements, current code, runtime evidence, then memory. Memory never overrides those.

Write durable facts that prevent rediscovery. Never store secrets, tokens, cookies, private raw data, or full transcripts. Do not create `.planning` for a Quick task.

## Skill Trigger Tightening

| Skill | When to load |
|---|---|
| `aimagician-superpower` | High, SDD, phase, milestone, audit, or an explicit plan/complete request. Quick/Standard coding uses the owned rules |
| `agent-workstream-orchestrator` | Tracked multi-session or multi-lane work on the **current** host |
| `vision-analysis` | No native vision, or an Agnes evidence package was requested |
| `pdf` / `docx` / `xlsx` | Those files are the work |
| `github-pr-workflow` | GitHub PR/MR work is actually in use |

The owned catalog currently contains 23 active skills. `cli-agent-delegator` is archived.

## Leftovers For The Next Engine Slice

Do not treat these as current default policy. They are the next optimization surface.

1. **Rule and memory sync.** Skillbird `capabilityKinds` / `assetKinds` are still skill/plugin. `rulesDir` exists on inspect reports but is unused. Add projection: Cursor `.cursor/rules/*.mdc`, Claude rules or a managed `CLAUDE.md` block, Codex `AGENTS.md` markers. Bootstrap must not clobber live user files.
2. **Complete-gate provider.** `skills/owned/aimagician-superpower/scripts/workflow.mjs` `validateOpenCodeAudit` still requires the literal `Provider: OpenCode` and an OpenCode session string on planning-managed High closure. Templates still seed that value. Generalize the gate to the actual auditor host after tests are updated. Until then, filling this repository's complete gate may still write `Provider: OpenCode` even when dispatch was host-native.
3. **Historical audits.** `docs/audits/*` and `.planning/phases/*` prompts record the old OpenCode-default world. Leave them. Do not rewrite history to match this file.

## Locked Decisions (do not reopen unless asked)

- Archive `cli-agent-delegator` as a default skill.
- Rules are generic only.
- Content first; Skillbird sync engine later.
- Memory: both user (`~/.skillbird/memory/`) and project (`.planning/memory/`).
- Do not rewrite the archived delegator into a multi-provider adapter set.

## Pointers

- User-facing: root [`README.md`](../README.md), English [`docs/README.en.md`](README.en.md)
- Planning: [`.planning/CONTEXT.md`](../.planning/CONTEXT.md) `CTX-ARCH-003`, `CTX-AGENT-001`, `CTX-AGENT-002`, `CTX-DEC-010`
- Archive note: [`skills/archived/ARCHIVE.md`](../skills/archived/ARCHIVE.md)
- Historical OpenCode runner: [`docs/audits/cli-agent-delegator-upgrade-2026-07-22.md`](audits/cli-agent-delegator-upgrade-2026-07-22.md)
