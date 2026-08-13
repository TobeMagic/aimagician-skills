---
name: agent-workstream-orchestrator
description: Use when work can be split into independently tracked agent sessions, when a bounded task should run outside the controller context, or when multiple read or write lanes need coordinated execution. Routes work by coupling and risk across the current agent, fresh Codex sessions, OpenCode, optional worktrees, integration branches, and pull requests; do not use for a single tightly coupled task that is faster and safer in the current session.
category: operate
subcategory: agent-orchestration
tags:
  - multi-agent
  - workstreams
  - sessions
  - codex
  - opencode
  - worktree
  - integration
compatibility:
  tools: [bash, git, python]
  requires: A bounded objective, explicit ownership, and a verifiable handoff
---

# Agent Workstream Orchestrator

Coordinate independent work without forcing every task into a worktree or pull-request topology. The controller keeps requirement authority, architectural decisions, integration, and completion claims. Worker sessions receive bounded context, produce evidence, and never redefine the parent goal.

## Trigger And Non-Trigger

Use this Skill when at least one condition holds:

- a task is independent enough to run in a fresh session without sharing live reasoning state;
- broad exploration, testing, Git inspection, research, or a bounded edit would consume the controller context;
- two or more lanes can progress concurrently with explicit ownership;
- an isolated write needs a branch or worktree;
- multiple outputs need integration, conflict control, or a unified acceptance pass;
- a paused or background session must be tracked and resumed safely.

Do not use it for one external worker, one short tightly coupled edit, a single known-file check, a decision that depends on unresolved user intent, or work whose files, state, and acceptance cannot be partitioned. In those cases, keep the work in the controller and resolve the boundary first. `cli-agent-delegator` can dispatch one bounded worker without creating a durable workstream registry.

## Control Contract

Before delegation, lock these fields:

1. parent objective and requirement IDs, when they exist;
2. worker objective and explicit non-goals;
3. allowed read and write scope;
4. source-of-truth files and required Skills;
5. dependencies and expected output;
6. decisive validation and stop conditions;
7. whether the worker may edit, commit, push, or only report.

The controller owns ambiguity resolution, architecture, security-sensitive decisions, cross-lane tradeoffs, integration, and the final claim. A worker result is evidence, not authority.

## Route By Coupling, Risk, And Cost

Choose the least expensive isolation that preserves correctness.

| Work | Default execution | Isolation |
|---|---|---|
| Independent exploration, research, review, or report | OpenCode through `cli-agent-delegator`; Codex when deeper reasoning is required | Fresh session, read-only, no worktree |
| Short test, Git inspection, lint, bounded mechanical update | OpenCode through `cli-agent-delegator` | Fresh session; exact write scope if edits are allowed |
| Complex design or core implementation | Fresh Codex session | Worktree when writes overlap controller state |
| Independent bounded implementation | Codex or OpenCode selected by difficulty | Tracked session plus worktree and branch |
| Shared, high-coupling architecture or migration | Controller | Sequential; delegate evidence collection only |
| Multiple isolated write lanes requiring one delivery | Mixed providers by lane | Worktrees, integration owner, then PR if the repository uses PRs |

Provider choice is dynamic. Use task difficulty, available tools, model capability, quota, and required modality. OpenCode model selection and fallback belong to `cli-agent-delegator`; do not hard-code one provider here.

## Progressive Disclosure

Read only the reference needed for the chosen route:

- session state, prompts, checkpoints, resume, and handoff: `references/session-lifecycle.md`;
- coupling analysis, ownership, and isolation choice: `references/routing-and-isolation.md`;
- worktree, integration, conflicts, commits, and PRs: `references/worktree-and-integration.md`;
- registry location and schema: `references/state-storage.md`.

Use `assets/workstream-registry.template.json` and `assets/workstream-handoff.template.md` only when durable tracking is warranted. A single delegated read-only task can be tracked in the parent task record instead.

## Execution Loop

1. **Partition:** identify independent outputs and shared surfaces. If ownership cannot be made exclusive, keep that work sequential.
2. **Register:** record session ID, provider/model, objective, scope, dependencies, status, last activity, evidence target, and optional branch/worktree.
3. **Prompt:** provide the source of truth, required Skills, exact commands or interfaces already known, prohibited actions, and output format. Do not make the worker rediscover stable context.
4. **Launch:** start the smallest sufficient agent. Writes require an isolated scope; overlapping writes require separate worktrees or serialization.
5. **Observe by events:** continue waiting while logs, tool calls, file changes, or session events show progress. Time alone is not failure. Intervene on explicit errors, repeated no-progress cycles, scope drift, or a real blocker.
6. **Validate:** inspect changed files and rerun decisive evidence in the controller or an independent verifier. Spot-check claims that affect architecture, security, data, or completion.
7. **Integrate:** combine lanes in dependency order, resolve shared surfaces once, run integration checks, and create or merge PRs only when the repository workflow requires them.
8. **Close:** update each workstream status and handoff. The parent requirement remains open until integrated behavior, not worker activity, is verified.

## Checkpoints

Do not advance a lane unless the current checkpoint passes:

- `READY`: objective, scope, authority, dependencies, and evidence are explicit.
- `RUNNING`: the registered session exists and activity remains within scope.
- `HANDOFF`: output, changed files, commands, failures, assumptions, and residual risk are recorded.
- `INTEGRATED`: the controller inspected the diff and ran the parent-level decisive check.
- `CLOSED`: no unresolved Blocker or Important finding remains and the parent checklist is updated.

## Scope And Handoff Validation

### 1. Freeze Each Lane

Record the selected source roots, command classes, forbidden roots, and expected evidence before launch. A read-only lane does not gain access to sibling workstreams, installed copies, or broad repository scans merely because they are convenient.

### 2. Reject Drift Early

If a worker attempts an unlisted path, command, or write, stop that lane and mark its handoff invalid. Preserve only the minimal incident evidence; do not merge conclusions from the drifted run.

### 3. Re-issue The Smallest Contract

Narrow the objective to known paths, or move the unresolved architecture decision to the controller. Restart only after the revised contract and decisive evidence are explicit.

**CHECKPOINT:** `HANDOFF` requires a scope-conformant tool trace as well as output, changed-file, command, and risk evidence.

**CHECKPOINT:** `READY` is invalid until the lane has an explicit owner, allowed roots, forbidden roots, command class, and parent-level acceptance evidence.

**CHECKPOINT:** `INTEGRATED` is invalid until the controller has inspected the integrated diff and rerun the parent-level decisive check.

When a lane cannot produce a scope-conformant trace, stop integration and fall back to a controller-owned, known-path check or a newly isolated lane.

## Failure Handling

| Trigger | First response | Fallback |
|---|---|---|
| Worker asks a material product or architecture question | Pause the lane and obtain a controller decision | Re-prompt with the accepted decision or keep the question with the controller |
| Worker drifts outside scope or conflicts with local evidence | Stop or discard that lane's unaccepted result | Tighten scope and restart from a clean checkpoint; never average conflicting claims |
| Session is silent but still emits progress events | Keep waiting; do not terminate from an arbitrary short timeout | Continue event observation until a clear error, repeated no-progress cycle, or explicit cancellation |
| No progress events and no output | Inspect session state and request one status update | Restart or reassign only after the lane is confirmed stalled |
| Model/quota failure or conflicting write scopes | Preserve the contract and serialize affected work | Apply the approved provider fallback or isolate the lanes in worktrees |
| Tests pass but requirements are not covered | Keep the parent requirement open | Repair implementation or acceptance evidence before closure |

## Runtime Helpers

```bash
python scripts/workstream_registry.py init --root <project> --write
python scripts/workstream_registry.py add --root <project> --id <id> --objective "<objective>" --provider opencode --mode read-only --write
python scripts/workstream_registry.py update --root <project> --id <id> --status running --session <session-id> --write
python scripts/workstream_registry.py list --root <project>
python scripts/workstream_registry.py validate --root <project>
python scripts/bootstrap_worktrees.py --registry-file <registry.json> --validate
python scripts/inspect_workstreams.py --registry-file <registry.json>
```

Commands preview by default where mutation is possible and require `--write` or the helper-specific execution flag. They do not launch agents, delete worktrees, commit, push, merge, or install dependencies.

## Output Contract

Report the parent objective, route decision, workstream table, source context, session/provider identity, status and activity, changed files, evidence, integration result, unresolved findings, and exact next action. Do not equate session completion, a commit, or green tests with parent requirement completion.
