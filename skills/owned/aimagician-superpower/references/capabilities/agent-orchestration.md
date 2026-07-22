# Agent Orchestration

Use this module when an external CLI agent or fresh subagent can reduce context pressure, provide specialization, or create independent review evidence.

## Controller Responsibilities

The coordinating agent owns objective, boundaries, source-of-truth context, task decomposition, provider choice, permissions, prompt quality, progress monitoring, result validation, integration, and final completion. Delegation never transfers accountability. Keep unresolved product and architecture decisions, risk acceptance, and final completion judgment with the controller.

Use prompt templates under `references/roles/` together with the full envelope in `cli-agent-delegator/references/prompt-contract.md`. Each dispatch includes the exact task, source of truth, relevant requirements, accepted decisions, known context, required owned skills, allowed and forbidden scope, permission mode, write scope, commands, tests, git policy, output format, status and severity protocol, and escalation rule. The worker loads every named skill before substantive work or returns `NEEDS_CONTEXT`. Do not tell an agent to rediscover context the controller already has.

## Role Routing

- **Researcher:** broad read-only evidence collection and architecture mapping.
- **Requirements analyst:** falsifiability, boundary, ambiguity, and assumption review.
- **Planner:** requirement-backed task and dependency design.
- **Plan reviewer:** independent completeness and executability review.
- **Implementer:** one bounded task with tests and self-review.
- **Specification reviewer:** actual-change comparison with accepted requirements.
- **Quality reviewer:** maintainability, correctness, security, tests, and regression review after specification compliance passes.
- **Verifier:** execute or inspect evidence without trusting implementation claims.
- **Debugger:** reproduce and trace root cause before proposing a patch.
- **Auditor:** final cross-task requirement and integration assessment.

## Status Protocol

Every delegated role returns exactly one status:

- `DONE`: assigned outcome completed with evidence.
- `DONE_WITH_CONCERNS`: completed, but correctness or scope concerns require controller review.
- `NEEDS_CONTEXT`: specific missing information prevents responsible continuation.
- `BLOCKED`: a dependency, permission, architecture decision, or repeated failure prevents completion.

The report also includes work performed, files inspected or changed, commands and results, findings, uncertainty, and recommended next action. Never treat silence or a confident prose summary as `DONE`.

## Implementation Review Loop

For each substantial implementation task:

1. Dispatch one implementer with fresh bounded context.
2. Resolve `NEEDS_CONTEXT` or `BLOCKED`; do not force a blind retry.
3. Require implementation tests and self-review.
4. Dispatch an independent specification reviewer against actual files and behavior.
5. Return gaps to the implementer, then repeat specification review until it passes.
6. Dispatch an independent quality reviewer only after specification compliance passes.
7. Fix important quality findings and re-review.
8. Mark the task complete only after both review gates pass.
9. After all tasks, run a whole-change verifier or auditor.

## Risk-Scaled Review Gates

- A one- or two-file read-only lookup needs no forced delegation.
- A bounded quick write gets one combined pre-commit specification and quality review.
- Substantial work gets independent plan review, specification review, quality review, verification, phase audit, and milestone or completion audit.
- Security, data, concurrency, migration, and architecture risk may add focused independent reviewers.

Findings use `Blocker`, `Important`, or `Nitpick`. A Blocker stops progression. An Important finding is fixed and re-reviewed or deferred only by explicit user decision. A Nitpick is non-blocking.

## Provider And Model Selection

Use `cli-agent-delegator` for provider preflight and execution. Use DeepSeek V4 Flash Free for ordinary non-visual work and Agnes for visual input or when DeepSeek is unavailable, rate-limited, or fails. Escalate model capability when a role reports reasoning limits; do not retry the same insufficient context unchanged.

For long-running CLI agents, monitor activity events and wait while progress continues. Do not impose a fixed wall-clock stop on an active run. Classify stale, permission, model, command, and provider failures explicitly.

The controller validates decision-changing claims without repeating the whole scan: check cited paths and symbols, one representative dependency or data path, every material “not found” claim, Blocker and Important findings, and the decisive verification command.

## Parallel Safety

Parallelize only independent tasks with disjoint write scopes and defined integration order. Use `parallel-worktree-pr-flow` for write-capable lanes. Keep shared-file edits sequential. One coordinator integrates and verifies the combined result. Child agents are forbidden by default; when allowed, they inherit the exact source of truth, skills, scope, permissions, command policy, evidence, and stop rules.
