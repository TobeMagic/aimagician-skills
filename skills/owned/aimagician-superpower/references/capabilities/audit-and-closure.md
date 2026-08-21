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

Require a fresh independent auditor on the current host against a frozen review point for High work, phase or milestone closure, deployable postmerge closure, a project-mandated review, or an explicit user request. Foreign OpenCode (`skills/archived/cli-agent-delegator`) is opt-in only. Quick and Standard work normally close from decisive verification and the repository's actual PR protections; add a compact combined review only when the diff, risk, or project policy justifies it. Acquire visual evidence with the current model's native image tool when available; load `vision-analysis` only when the session cannot see pixels or the user asks for an Agnes evidence package, then pass the sanitized text result to the auditor. Supply only the sources that are material to the chosen tier: original objective or PRD, accepted decisions, applicable planning state, specification or task record, non-goals, actual diff or artifacts, verification, and exclusions. The main Agent reconciles findings against primary evidence and retains the final completion decision. Leftover: this repository's `workflow.mjs` `validateOpenCodeAudit` still requires the literal `Provider: OpenCode` on planning-managed complete-gate records until that gate is generalized; see `docs/RULES-AND-MEMORY.md`.

## Gap Classification

- **Blocker:** accepted objective cannot be called complete.
- **Follow-up:** current objective is complete, but adjacent work should be tracked.
- **Deferred:** explicitly excluded by a user decision or locked boundary.
- **Invalid:** superseded because the accepted requirement changed.

Every gap needs an owner or decision. Do not bury gaps in optimistic prose.

Audit findings use `Blocker`, `Important`, or `Nitpick`; the gap labels above describe closure disposition, not impact severity. An unresolved Blocker stops closure. An Important gap must be fixed and re-audited or explicitly deferred by the user.

## Complete Gate

For High or planning-managed closure, require:

- all accepted requirements planned;
- every accepted `USR-*` request mapped to one or more implemented requirements;
- the selected work aligned with the active milestone, phase, and literal roadmap goal;
- every `GOAL-*` acceptance criterion mapped to concrete passing evidence;
- all required evidence `PASS`;
- user-facing UAT complete when applicable;
- no unresolved blocking review finding;
- auditor host, model, session, frozen review point, requirement matrix, finding counts, and controller spot-check recorded;
- no stale placeholder or accidental capability loss;
- state and documentation updated;
- temporary output handled intentionally;
- current git, worktree, PR, or installation state reported accurately.

Use `workflow.mjs validate --gate align` before mutation and `workflow.mjs validate --gate complete` before closure only when the project is planning-managed or the task is High. Phase closure requires a passing phase audit over requirements and goal criteria. Milestone closure requires every member phase complete plus a milestone-wide audit and summary covering all mapped requirements and phase goals. For Quick and Standard work outside a managed plan, preserve the compact contract, decisive verification, delivery state, and explicit residual risk instead of manufacturing phase artifacts.

Any `FAIL`, `NOT_RUN`, unresolved Blocker, or unresolved Important keeps the task open. Continue the checklist and re-audit while the work is feasible; tests passing does not override missing request coverage.

## Learning And Cleanup

Preserve reusable architecture, commands, integration behavior, failure patterns, and operational knowledge in docs, tests, or the project wiki. Route secret inventory or sensitive scans to `llm-know-how-wiki`.

Remove only temporary files created by the current work. Never clean user files or unrelated dirty state. Confirm local reference mirrors remain ignored and installed targets contain only intended managed skills when installation was in scope.

## Handoff Summary

Record objective, requirement coverage, changed files, key decisions, commands and results, UAT, review and audit status, checks not run, residual risk, commit/worktree/PR state, and the exact next action. Another agent should be able to continue without repeating discovery.
