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

For every task, phase, milestone, release, or complete claim, load `cli-agent-delegator` and dispatch a fresh independent OpenCode auditor against a frozen review point. Acquire any visual evidence first through `vision-analysis` with explicit upload authorization, then provide its sanitized text result to the auditor. Audit reasoning uses the DeepSeek-first route; Agnes is a text fallback only after a verified DeepSeek usage or quota limit. Supply the original objective or PRD, `.planning/REQUESTS.md`, latest user decisions, active milestone and phase, literal roadmap goal and criteria, specification or task record, non-goals, actual diff or artifacts, reviews, verification, installation state, required owned skills, and exclusions. A quick task may use one compact combined review; substantial work keeps staged independent reviews. The main Agent reconciles findings against primary evidence and retains the final completion decision.

## Gap Classification

- **Blocker:** accepted objective cannot be called complete.
- **Follow-up:** current objective is complete, but adjacent work should be tracked.
- **Deferred:** explicitly excluded by a user decision or locked boundary.
- **Invalid:** superseded because the accepted requirement changed.

Every gap needs an owner or decision. Do not bury gaps in optimistic prose.

Audit findings use `Blocker`, `Important`, or `Nitpick`; the gap labels above describe closure disposition, not impact severity. An unresolved Blocker stops closure. An Important gap must be fixed and re-audited or explicitly deferred by the user.

## Complete Gate

Closure requires:

- all accepted requirements planned;
- every accepted `USR-*` request mapped to one or more implemented requirements;
- the selected work aligned with the active milestone, phase, and literal roadmap goal;
- every `GOAL-*` acceptance criterion mapped to concrete passing evidence;
- all required evidence `PASS`;
- user-facing UAT complete when applicable;
- no unresolved blocking review finding;
- OpenCode provider, primary/final model, attempt chain, fallback reason, fresh session, frozen review point, requirement matrix, finding counts, and controller spot-check recorded;
- no stale placeholder or accidental capability loss;
- state and documentation updated;
- temporary output handled intentionally;
- current git, worktree, PR, or installation state reported accurately.

Use `workflow.mjs validate --gate align` before mutation and `workflow.mjs validate --gate complete` before closure. Phase closure requires a passing phase audit over requirements and goal criteria. Milestone closure requires every member phase complete plus a milestone-wide audit and summary covering all mapped requirements and phase goals.

Any `FAIL`, `NOT_RUN`, unresolved Blocker, or unresolved Important keeps the task open. Continue the checklist and re-audit while the work is feasible; tests passing does not override missing request coverage.

## Learning And Cleanup

Preserve reusable architecture, commands, integration behavior, failure patterns, and operational knowledge in docs, tests, or the project wiki. Route secret inventory or sensitive scans to `llm-know-how-wiki`.

Remove only temporary files created by the current work. Never clean user files or unrelated dirty state. Confirm local reference mirrors remain ignored and installed targets contain only intended managed skills when installation was in scope.

## Handoff Summary

Record objective, requirement coverage, changed files, key decisions, commands and results, UAT, review and audit status, checks not run, residual risk, commit/worktree/PR state, and the exact next action. Another agent should be able to continue without repeating discovery.
