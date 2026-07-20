# Agent Orchestration

Use this module when an external CLI agent or fresh subagent can reduce context pressure, provide specialization, or create independent review evidence.

## Controller Responsibilities

The coordinating agent owns objective, boundaries, source-of-truth context, task decomposition, provider choice, permissions, prompt quality, progress monitoring, result validation, integration, and final completion. Delegation never transfers accountability.

Use prompt templates under `references/roles/`. Each dispatch includes the exact task, relevant requirements, accepted decisions, allowed and forbidden scope, mutation permission, tests, output format, and escalation rule. Do not tell an agent to rediscover context the controller already has.

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

## Provider And Model Selection

Use `cli-agent-orchestrator` for provider preflight and execution. Prefer a strong available free model for broad exploration, a capable reasoning model for architecture and review, and a fast model for mechanical work with a complete specification. Escalate model capability when a role reports reasoning limits; do not retry the same insufficient context unchanged.

For long-running CLI agents, monitor activity events and wait while progress continues. Do not impose a fixed wall-clock stop on an active run. Classify stale, permission, model, command, and provider failures explicitly.

## Parallel Safety

Parallelize only independent tasks with disjoint write scopes and defined integration order. Use `parallel-worktree-pr-flow` for write-capable lanes. Keep shared-file edits sequential. One coordinator integrates and verifies the combined result.
