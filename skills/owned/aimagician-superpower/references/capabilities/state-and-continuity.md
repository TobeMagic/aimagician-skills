# State And Continuity

Use this module when work spans turns, phases, agents, worktrees, risky operations, or a context handoff.

## Source-Of-Truth Order

1. Latest explicit user decision.
2. Locked phase specification and accepted requirement IDs.
3. Current planning state, roadmap, phase context, and plans.
4. Project docs and knowledge base.
5. Filesystem, tests, runtime evidence, and git state.

When these disagree, do not silently choose the convenient source. Resolve material conflicts before mutation.

## Durable State Model

- `.planning/STATE.md`: active milestone or phase, status, blocker, next action, and resume checkpoint.
- `.planning/ROADMAP.md`: ordered outcomes, dependencies, requirements, and phase status.
- `.planning/REQUIREMENTS.md`: durable project requirements and acceptance IDs.
- `.planning/phases/<phase>/`: specification, discussion, research, context, plans, validation, UAT, audit, and summary.
- `.planning/.continue-here.md`: temporary handoff when a task stops mid-phase.

Follow an existing repository convention instead of creating a competing structure. The runtime accepts `PLAN.md` and `*-PLAN.md`, and accepts both `*-VALIDATION.md` and legacy `*-VERIFICATION.md`.

## Resume Protocol

1. Reload the main skill.
2. Read state, roadmap, requirements, active specification, context, discussion, research, plans, validation, audit, and summary.
3. Read project docs and the project knowledge base.
4. Inspect git status and recent relevant commits.
5. Identify the last requirement-backed checkpoint and unverified work after it.
6. Run `node scripts/workflow.mjs status ...` or `next ...` when the phase uses supported artifacts.
7. State known facts, unavailable sources, conflicts, blockers, and the next safe action.
8. Continue from the checkpoint; do not repeat solved research or skip an incomplete gate.

## Checkpoint Contract

Record after each meaningful unit:

- requirement and task IDs completed;
- files changed and files intentionally untouched;
- commands run and observed result;
- decisions or assumptions changed;
- failures, gaps, and residual risk;
- git or worktree location;
- exact next action.

## Pause And Recovery

- For a user decision, record the exact question, options, recommendation, and impact.
- For an external failure, record command shape, sanitized error, attempts, activity status, and fallback.
- For a stale plan, preserve completed evidence and re-plan only the invalidated portion.
- For user edits in overlapping files, stop, read, and integrate rather than overwrite.
- For an interrupted write operation, inspect resulting state before retrying.

Use `workflow.mjs trace` before closure so the next agent can distinguish completed implementation from unsupported claims.
