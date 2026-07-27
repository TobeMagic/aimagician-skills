---
name: cli-agent-delegator
description: MANDATORY CLI delegation and prompt-contract gate. Use before the main Agent directly performs broad or multi-source exploration, repository scanning, architecture mapping, deep web research, image or visual inspection, independent plan/code/spec/verification/audit review, or a bounded short task such as git inspection, test execution, reporting, or isolated low-risk implementation that an external CLI agent can handle. Prefer OpenCode, put cli-agent-delegator plus every domain skill in REQUIRED_SKILLS, require actual Skill tool calls before worker action, then validate critical claims. Keep one- or two-file lookups and core product or architecture decisions with the main Agent.
category: operate
subcategory: agent-orchestration
tags:
  - cli-agent
  - multi-agent
  - delegation
  - orchestration
  - opencode
  - exploration
  - research
  - review
  - verification
compatibility:
  tools: [bash, git, opencode]
  requires: A bounded objective, source of truth, permission mode, allowed scope, forbidden scope, required skills, and expected evidence
---

# CLI Agent Delegator

Use external CLI agents as bounded workers while the main Agent keeps the scarce work: requirement reconciliation, product and architecture judgment, risk decisions, result validation, integration, and completion accountability.

OpenCode is the current provider. It can explore, research, inspect images, run checks, produce reports, review work, and perform a small isolated write task when the controller supplies an exact contract. Future CLI agents can implement the same delegation contract under `references/providers/`.

## Delegation-First Trigger Gate

Before the main Agent starts a broad scan or mechanical verification, ask whether a CLI worker can return the needed evidence without consuming the main context window. Delegate first when any of these is true:

- relevant context spans many unknown files, modules, repositories, documents, logs, issues, APIs, or web sources;
- the task is repository mapping, implementation-location discovery, dependency or data-flow tracing, deep research, comparison, or image understanding;
- a fresh independent context should review a plan, specification, diff, verification record, phase, milestone, or completion claim;
- a bounded worker can inspect git state, run tests, monitor a check, collect failures, or turn raw output into a report;
- a short, low-risk implementation has an exact write scope and can run in an isolated worktree.

This gate applies even when the user says only “check,” “inspect,” “research,” “review,” “verify,” or “audit.” Do not let the main Agent silently perform a multi-file or multi-source scan that should have been delegated.

Do not delegate a lookup limited to one or two known files, a tiny fact already in context, user discussion, unresolved product choices, architecture ownership decisions, security acceptance, or final completion judgment.

## Worker-Side Loading Gate

Do not rely on worker self-selection from task wording. For every OpenCode or other CLI-worker exploration, research, review, git inspection, test execution, reporting, verification, audit, or bounded-work task, the controller must put `cli-agent-delegator` and every domain skill in `REQUIRED_SKILLS`. The worker must then invoke the Skill tool for each named skill before substantive reads, commands, or edits. Mentioning a skill in prose does not satisfy this gate. If a named skill cannot be loaded, return `NEEDS_CONTEXT` instead of improvising a workflow.

## Capability Routing

Load only the references needed for the delegated role.

| Need | Reference |
|---|---|
| Required prompt envelope, skill loading, permissions, child-agent inheritance, status, validation | `references/prompt-contract.md` |
| Broad repository or source exploration, web research, comparison, visual or image understanding | `references/task-types/discovery-and-research.md` |
| Git inspection, tests, progress reports, non-destructive checks, bounded isolated writes | `references/task-types/bounded-operations-and-execution.md` |
| Plan, specification, quality, verification, phase, milestone, or completion review | `references/task-types/independent-review-and-audit.md` |
| OpenCode preflight, models, command syntax, event-based waiting, fallback, session handling | `references/providers/opencode.md` |
| General handoff report | `references/report-templates/delegation-report.md` |
| Reviewer and auditor report | `references/report-templates/review-report.md` |

## Controller Contract

The main Agent always owns:

1. the latest user objective and accepted decisions;
2. source-of-truth selection and conflict resolution;
3. task decomposition and whether delegation is appropriate;
4. allowed and forbidden scope, permission mode, git policy, and stop conditions;
5. provider and model routing;
6. prompt completeness and required skill selection;
7. progress observation and failure classification;
8. spot-checking critical claims and rerunning decisive checks;
9. accepting, rejecting, or reconciling findings;
10. integration, user communication, and the final completion claim.

Delegation never transfers accountability. A confident worker report is evidence to inspect, not authority.

## Permission Modes

Choose exactly one mode and state it in the prompt:

- `strict-read-only`: inspect sources and return findings; no writes or mutating commands.
- `read-and-run`: run explicitly allowed non-destructive checks. Test caches or artifacts may appear; capture before/after git state and report pollution without deleting it unless authorized.
- `bounded-write`: edit only named paths inside an isolated worktree created by the main Agent or `parallel-worktree-pr-flow`. The prompt must list allowed files, tests, git policy, and forbidden operations.

For `bounded-write`, do not permit edits in a dirty user worktree. Local commit is allowed only when the prompt explicitly grants it and an independent review has passed. Push, merge, reset, cleanup of user files, system package installation, production mutation, and secret access each require separate explicit authorization.

## Required Prompt Contract

Before running a worker, read `references/prompt-contract.md` and provide its complete envelope. At minimum include:

- role, objective, deliverable, and review point;
- source-of-truth files plus already accepted decisions;
- required owned skills and why each is needed;
- known context so the worker does not rediscover solved facts;
- allowed scope, forbidden scope, permission mode, and command classes;
- exact write scope and git policy when writes are allowed;
- tests, evidence, output format, severity taxonomy, status protocol, and stop conditions.

The prompt must require the worker to load every named skill before doing substantive work. If a required skill or source is unavailable, it returns `NEEDS_CONTEXT` instead of improvising. Any child agent inherits the same scope, permissions, source of truth, safety rules, and output contract; child delegation is forbidden unless the controller explicitly allows it.

## Delegation Loop

1. **Classify.** Choose discovery/research, bounded operation/execution, or independent review/audit.
2. **Protect macro reasoning.** Keep unresolved requirements, architecture tradeoffs, risk acceptance, and final decisions with the main Agent.
3. **Lock the contract.** Define sources, skills, scope, permission mode, commands, evidence, git policy, and escalation.
4. **Select provider and model.** Read `references/providers/opencode.md`. Use DeepSeek V4 Flash Free for ordinary non-visual tasks. Use Agnes for visual input and as the normal fallback when DeepSeek is unavailable, rate-limited, or fails.
5. **Preflight.** Verify the CLI, version, installed syntax, model availability, target path, required skills, and worktree state.
6. **Run non-interactively.** Use the installed CLI syntax and detailed positional prompt. Keep logs attached.
7. **Wait by events.** Continue while logs, tool calls, stage transitions, file references, session changes, or provider activity show progress. Do not stop an active worker because a fixed number of seconds elapsed.
8. **Classify failure.** Stop only on process exit, clear command/provider/permission error, user cancellation, or confirmed stale state. Never start a fallback while the first process is alive.
9. **Validate.** Check scope compliance and spot-check claims that affect design or completion, including paths, symbols, imports, “no tests” claims, Blocker/Important findings, and the decisive verification command.
10. **Iterate narrowly.** Send one focused follow-up when a bounded gap remains. Re-discuss if the gap changes scope, permissions, accepted behavior, or risk.
11. **Handoff.** Return the worker status, model, run health, findings, controller validation, unresolved uncertainty, and next decision.

## Independent Quality Gates

Use risk-scaled independent review rather than forcing the same ceremony onto every task:

- read-only one- or two-file lookup: no forced delegation;
- bounded quick write: one combined pre-commit specification and quality review;
- substantial work: independent plan review before execution, specification review before quality review, independent verification, phase audit, and milestone or completion audit;
- high-risk security, data, concurrency, migration, or architecture work: add focused reviewers where their axes are genuinely independent.

Review findings use exactly `Blocker`, `Important`, or `Nitpick`. A Blocker stops progression. An Important finding is fixed and re-reviewed, or deferred only by an explicit user decision. A Nitpick is non-blocking but recorded when useful.

## Main-Agent Validation Protocol

Do not repeat the whole delegated scan. Validate the claims that could change the decision:

- open representative paths and verify cited symbols or lines exist;
- trace at least one claimed import, caller, data path, or integration edge;
- challenge claims that a file, test, dependency, or behavior does not exist;
- reproduce every Blocker and material Important finding where feasible;
- rerun the narrow command that determines pass or fail;
- distinguish worker fact, worker inference, and controller-confirmed evidence.

If validation contradicts the worker, the main Agent resolves it from primary evidence and records the discrepancy.

## Output Contract

Every delegation handoff includes:

- task ID, role, objective, provider, model, and permission mode;
- source of truth, required skills loaded, allowed and forbidden scope;
- command shape, run status, activity evidence, retries, and failure classification;
- files inspected or changed and commands executed;
- structured result, findings, uncertainty, and recommended action;
- controller spot-checks and any corrected worker claims;
- session export status when export was authorized;
- final status: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.
