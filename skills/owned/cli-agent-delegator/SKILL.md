---
name: cli-agent-delegator
description: Use for broad or multi-source exploration, repository scanning, architecture mapping, deep web research, image inspection, independent plan/code/spec/verification review, bounded git/test/report/write work, or whenever a locked simple short execution task can be offloaded. Prefer OpenCode, require cli-agent-delegator plus all domain skills to be loaded, and validate critical claims; require a fresh completion audit only for high-risk, planning-managed, deployable, policy-required, or explicitly requested work.
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
  - short-task
compatibility:
  tools: [bash, git, opencode]
  requires: A bounded objective, source of truth, permission mode, allowed scope, forbidden scope, required skills, and expected evidence
---

# CLI Agent Delegator

Use external CLI agents as bounded workers while the main Agent keeps the scarce work: requirement reconciliation, product and architecture judgment, risk decisions, result validation, integration, and completion accountability.

OpenCode is the current provider. It can explore, research, reason over sanitized visual evidence, run checks, produce reports, review work, and perform a small isolated write task when the controller supplies an exact contract. Pixel understanding is acquired through the owned `vision-analysis` skill before OpenCode reasoning. Future CLI agents can implement the same delegation contract under `references/providers/`.

## Delegation-First Trigger Gate

Before the main Agent starts a broad scan or mechanical verification, ask whether a CLI worker can return the needed evidence without consuming the main context window. Delegate first when any of these is true:

- relevant context spans many unknown files, modules, repositories, documents, logs, issues, APIs, or web sources;
- the task is repository mapping, implementation-location discovery, dependency or data-flow tracing, deep research, comparison, or image understanding;
- a fresh independent context should review a plan, specification, diff, verification record, phase, milestone, or completion claim;
- a bounded worker can inspect git state, run tests, monitor a check, collect failures, or turn raw output into a report;
- a short, low-risk implementation has an exact write scope and can run in an isolated worktree.

This gate applies even when the user says only “check,” “inspect,” “research,” “review,” “verify,” “audit,” “run the tests,” “fix this small issue,” or “update this file.” Do not let the main Agent silently perform mechanical work that satisfies the short-task gate or a multi-file or multi-source scan that should have been delegated.

Do not delegate a lookup limited to one or two known files, a tiny fact already in context, user discussion, unresolved product choices, architecture ownership decisions, security acceptance, or final completion judgment.

## Default Short-Task Gate

Delegate a simple short task by default when all of these are true:

1. the objective, accepted behavior, and completion evidence are already locked;
2. the task is local, independently verifiable, and does not require architecture or product judgment;
3. allowed files, commands, services, and data classes can be stated exactly;
4. no migration, production mutation, secret handling, destructive cleanup, security acceptance, or user-owned dirty work is exposed;
5. the controller can review the result without repeating the whole task.

Typical eligible work includes:

- Git status, diff, branch, commit, generated-file, and pre-commit inspection;
- named tests, lint, typecheck, build, smoke checks, log monitoring, and concise reports;
- a localized documentation, configuration, formatting, or low-risk bug fix with explicit acceptance;
- scoped web research, source comparison, artifact inspection, or image understanding;
- requirement, plan, diff, verification, phase, milestone, or completion review.

If a supposedly short task discovers unresolved behavior, architecture, security, migration, destructive action, secret access, production impact, or required scope expansion, the worker returns `NEEDS_CONTEXT`. The controller resolves the decision before any new dispatch.

## Worker-Side Loading Gate

Do not rely on worker self-selection from task wording. For every OpenCode or other CLI-worker exploration, research, review, git inspection, test execution, reporting, verification, audit, or bounded-work task, the controller must put `cli-agent-delegator` and every domain skill in `REQUIRED_SKILLS`. The worker must then invoke the Skill tool for each named skill before substantive reads, commands, or edits. Mentioning a skill in prose does not satisfy this gate. If a named skill cannot be loaded, return `NEEDS_CONTEXT` instead of improvising a workflow.

## Capability Routing

Load only the references needed for the delegated role.

| Need | Reference |
|---|---|
| Required prompt envelope, skill loading, permissions, child-agent inheritance, status, validation | `references/prompt-contract.md` |
| Broad repository or source exploration, web research, comparison, visual or image understanding | `references/task-types/discovery-and-research.md` |
| Direct authorized image understanding and visual evidence provenance | companion skill `vision-analysis` |
| Git inspection, tests, progress reports, non-destructive checks, bounded isolated writes | `references/task-types/bounded-operations-and-execution.md` |
| Ready-to-fill contracts for Git/test reports, localized fixes, research, visual inspection, and pre-commit review | `references/task-types/quick-task-recipes.md` |
| Plan, specification, quality, verification, phase, milestone, or completion review | `references/task-types/independent-review-and-audit.md` |
| OpenCode ready-to-run commands, command syntax, diagnostic preflight, models, event-based waiting, fallback, session handling | `references/providers/opencode.md` |
| Cached free-model inventory, explicit controller routing, ordered fallbacks, current positional syntax, streaming, and attempt provenance | `scripts/opencode-run.mjs` |
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
- `bounded-write`: edit only named paths inside isolation selected by the main Agent or `agent-workstream-orchestrator`. The prompt must list allowed files, tests, git policy, and forbidden operations.

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
4. **Select evidence and reasoning routes.** Read `references/providers/opencode.md`. Visual tasks first load `vision-analysis` and obtain authorized textual evidence through its Agnes backend. For every OpenCode run, the controller inspects the cached or refreshed free-model inventory, judges task difficulty and capability needs, records a short rationale, and explicitly supplies the best suitable primary model plus any ordered fallbacks. Do not hard-code a global quality ranking.
5. **Use the known-good fast path.** Prefer `scripts/opencode-run.mjs`, which caches verbose model metadata and uses the current positional prompt syntax. Use `--list-models` without routine version/help probes; refresh only after configuration changes, stale inventory, or model errors. Do not repeat binary, version, model-list, or help probes before routine execution. Every run supplies `--model`; repeat `--fallback-model` only for controller-approved alternatives. Review and audit tasks also pass `--review-ref <git-ref>` or `--review-worktree <path>` so the runtime fingerprints the exact review point.
6. **Run non-interactively.** Keep logs attached. The runtime follows the declared order. A usage/quota event invalidates the model's declared quota scope, model absence invalidates that model, and authentication invalidates that provider. OpenCode Zen models share one policy-defined quota scope; non-Zen providers use model-specific scopes. Network failures retry the same model three times, while permission, syntax, and worker-quality failures stop. The runtime appends Agnes once as the final fallback when available; Agnes rate limits remain active and retry by events until success or cancellation.
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

Require a fresh independent OpenCode audit for High work, phase/milestone closure, deployable postmerge closure, project policy, or explicit user request. A bounded quick write normally closes with controller verification and the repository's actual merge protections; add one compact combined review when the diff or discovered risk justifies it. Substantial work keeps independent staged reviewers and adds a final whole-result audit. Pure discussion without a completion claim is exempt.

Review findings use exactly `Blocker`, `Important`, or `Nitpick`. A Blocker stops progression. An Important finding is fixed and re-reviewed, or deferred only by an explicit user decision. A Nitpick is non-blocking but recorded when useful.

## Completion Audit When Required

Use a fresh OpenCode session with an explicitly controller-selected free reasoning model and ordered fallback chain. Choose for audit complexity, context size, tool support, and current availability; record the rationale and declared chain. The runtime appends Agnes as the final fallback when available, but Agnes is not the mandatory primary. For visual deliverables, obtain authorized observable evidence through `vision-analysis` and include its sanitized report in the fresh final audit. Freeze the exact commit with `--review-ref` or the exact stable worktree with `--review-worktree`; a fingerprint change invalidates the audit. Include the original request or PRD, accepted decisions, `.planning/REQUESTS.md`, requirement IDs, implementation, verification, UAT, documentation, installation state, and existing findings.

The auditor returns:

- one row per accepted requirement with `PASS`, `FAIL`, or `NOT_RUN`;
- findings using only `Blocker`, `Important`, or `Nitpick`;
- evidence paths and commands;
- missing, extra, shallow, or incorrectly narrowed behavior;
- model-selection rationale, declared and effective model chain, primary and final model, transition reasons, attempt chain, final recommendation, and OpenCode session ID.

The controller reproduces every Blocker and material Important finding where feasible and spot-checks each completion-critical PASS. `FAIL`, `NOT_RUN`, unresolved Blocker, or unresolved Important means continue the checklist and re-audit. Do not replace requirement coverage with a test-success summary.

## Main-Agent Validation Protocol

Do not repeat the whole delegated scan. Validate the claims that could change the decision:

- open representative paths and verify cited symbols or lines exist;
- trace at least one claimed import, caller, data path, or integration edge;
- challenge claims that a file, test, dependency, or behavior does not exist;
- reproduce every Blocker and material Important finding where feasible;
- rerun the narrow command that determines pass or fail;
- distinguish worker fact, worker inference, and controller-confirmed evidence.

If validation contradicts the worker, the main Agent resolves it from primary evidence and records the discrepancy.

## Failure Handling Checkpoint

- Explicit quota or model failure: preserve the prompt contract and continue through the declared fallback chain.
- Healthy progress events: keep waiting; elapsed time alone is not failure.
- Repeated no-progress events, malformed output, or scope drift: stop that attempt, classify the failure, and retry once with a corrected bounded prompt or different model.
- Material uncertainty: return `NEEDS_CONTEXT`; the controller decides or discusses before any write.
- Contradictory completion claim: return `DONE_WITH_CONCERNS` and require controller reproduction. Never promote it to `DONE` from worker confidence alone.

Before accepting the handoff, confirm the effective model, session, permissions, changed files, decisive evidence, and controller spot-check are all present.

## Output Contract

Every delegation handoff includes:

- task ID, role, objective, provider, model, and permission mode;
- source of truth, required skills loaded, allowed and forbidden scope;
- command shape, model-selection rationale, declared/effective model chain, primary model, final model, transitions, attempt chain, fallback reason, run status, activity evidence, retries, and failure classification;
- files inspected or changed and commands executed;
- structured result, findings, uncertainty, and recommended action;
- controller spot-checks and any corrected worker claims;
- session export status when export was authorized;
- final status: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.
