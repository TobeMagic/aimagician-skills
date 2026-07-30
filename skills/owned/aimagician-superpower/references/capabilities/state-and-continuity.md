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

## Planning Storage Modes

Choose one planning mode per Git repository:

- **Tracked:** `.planning/` is ordinary versioned project state. Use this when planning history should travel with clones and reviews.
- **Local-private:** every worktree's `.planning` points to one shared store under the repository's Git common directory. The runtime adds `/.planning` to the common `info/exclude`, so the planning state stays local and does not appear in commits.

Local-private mode deliberately has no automatic backup. Warn that deleting the clone or Git common directory deletes the planning history. If durability is needed, select tracked mode or explicitly export approved records.

Use the runtime instead of constructing links by hand:

```bash
node scripts/workflow.mjs planning --project <path> --action init --mode local-private --write
node scripts/workflow.mjs planning --project <worktree> --action attach --write
node scripts/workflow.mjs planning --project <path> --action status
```

All worktrees resolve to the same local-private root. Before a writer changes shared planning state, acquire a short lease with the observed revision. Unlock with `outcome=updated` to advance the revision, or `outcome=unchanged` when no durable state changed. A revision mismatch or existing live lock stops the write; reread and reconcile rather than overwriting concurrent updates.

## Resume Protocol

1. Reload the main skill.
2. Read state, roadmap, requirements, active specification, context, discussion, research, plans, validation, audit, and summary. Extract the active milestone, phase, literal roadmap goal, `GOAL-*` criteria, and `REQ-*` set.
3. Read project docs and the project knowledge base.
4. Inspect git status and recent relevant commits.
5. Identify the last requirement-backed checkpoint and unverified work after it.
6. Run `node scripts/workflow.mjs validate ... --gate align`, then `status ...` or `next ...` when the work uses supported artifacts.
7. State known facts, unavailable sources, conflicts, blockers, and the next safe action.
8. Continue from the checkpoint; do not repeat solved research or skip an incomplete gate.

When planning is local-private, run `planning --action attach --write` after creating or entering a new worktree, then acquire a lease before updating shared planning records.

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

## Drift And Exception Control

- Keep the active milestone, phase, literal roadmap goal, requirement IDs, and goal criteria visible in every checkpoint.
- Map each changed file and verification action to a requirement or goal criterion. Unmapped work is drift until justified.
- A test result proves only the criterion it exercises. It cannot replace goal acceptance or requirement coverage.
- Off-phase work requires a controlled exception with parent milestone, parent phase, explicit `USR-*` approval, and a return checkpoint.
- Do not advance phase or milestone status while `validate --gate align` reports drift.
