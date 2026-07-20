# Audit And Closure

Use this module at task, phase, milestone, branch, review, release, or handoff closure.

## Independent Audit

Compare actual files, runtime behavior, and evidence with:

- latest accepted user objective;
- locked specification and boundaries;
- requirement and acceptance IDs;
- research facts and confirmed assumptions;
- plan tasks and dependency outcomes;
- validation and UAT evidence;
- integration wiring and installed artifacts;
- regression, security, compatibility, and migration risk;
- documentation, state, and handoff obligations.

Do not infer compliance from a completion summary. Spot-check or execute critical evidence and inspect the final diff.

## Gap Classification

- **Blocker:** accepted objective cannot be called complete.
- **Follow-up:** current objective is complete, but adjacent work should be tracked.
- **Deferred:** explicitly excluded by a user decision or locked boundary.
- **Invalid:** superseded because the accepted requirement changed.

Every gap needs an owner or decision. Do not bury gaps in optimistic prose.

## Complete Gate

Closure requires:

- all accepted requirements planned;
- all required evidence `PASS`;
- user-facing UAT complete when applicable;
- no unresolved blocking review finding;
- no stale placeholder or accidental capability loss;
- state and documentation updated;
- temporary output handled intentionally;
- current git, worktree, PR, or installation state reported accurately.

Use `workflow.mjs validate --gate complete` for supported artifacts.

## Learning And Cleanup

Preserve reusable architecture, commands, integration behavior, failure patterns, and operational knowledge in docs, tests, or the project wiki. Route secret inventory or sensitive scans to `llm-know-how-wiki`.

Remove only temporary files created by the current work. Never clean user files or unrelated dirty state. Confirm local reference mirrors remain ignored and installed targets contain only intended managed skills when installation was in scope.

## Handoff Summary

Record objective, requirement coverage, changed files, key decisions, commands and results, UAT, review and audit status, checks not run, residual risk, commit/worktree/PR state, and the exact next action. Another agent should be able to continue without repeating discovery.
