# Execution Modes

Use this module after the specification and plan gates appropriate to the task have passed.

## Standard Execution

1. Read the exact implementation and test files before editing.
2. Confirm git status, worktree, allowed scope, and user-owned changes.
3. Select the next dependency-ready task; do not mix unrelated tasks.
4. Pin behavior with a failing test or probe when practical.
5. Implement the smallest change that satisfies the task.
6. Run the narrow check, inspect the diff, and self-review.
7. Record a requirement-backed checkpoint before the next wave.
8. Run the required independent reviews for substantial or delegated work.

## Modes

- **Quick:** a low-risk inline target with one direct verification.
- **Fast:** several simple, ordered edits with a focused check after each meaningful group.
- **Autonomous:** continue through a locked plan until complete or a blocker changes scope, risk, or acceptance.
- **Repair:** reproduce and trace before changing code; prove the regression afterward.
- **Sequential agent:** one fresh implementer per task with review loops.
- **Parallel:** independent write scopes in isolated workers with one integration owner.
- **Branch/worktree:** isolate large, risky, interrupting, or parallel work from the user's active tree.

When `.planning` uses local-private mode, every created worktree attaches to the repository's shared planning root. Planning writes are coordination events: only the integration owner or a worker with an explicit short lease and matching revision may update shared state. Provider lanes report evidence through their scoped handoff and must not race global planning files.

## Test-First Discipline

Use red-green-refactor for changed behavior when a reliable test boundary exists:

1. write the smallest failing check that represents the requirement;
2. run it and confirm failure for the expected reason;
3. implement only enough to pass;
4. run the narrow test;
5. refactor without changing behavior;
6. run nearby and broader checks based on blast radius.

Do not write tests that merely search source text when behavior can be executed. Avoid mocks that only prove the mock. Preserve the failing evidence when the defect is intermittent or environment-dependent.

## Parallel Worker Brief

Every worker receives objective, requirement and task IDs, context, allowed and forbidden files, mutation permission, dependencies, exact tests, expected output, status protocol, planning storage mode, and handoff format. Shared files, migrations, registries, planning records, and integration tests have one owner.

Use `cli-agent-delegator` when OpenCode can run a short locked implementation, git inspection, named test set, non-destructive check, or progress report. Supply required owned skills and a complete prompt contract. `read-and-run` work records before/after git status and reports generated pollution. `bounded-write` work runs only in a clean isolated worktree with exact allowed files; it stops rather than expanding scope. Local commit is opt-in after review, and push is separately authorized.

## Code Discipline

- Follow existing helpers, structured APIs, parsers, types, and naming.
- Avoid unrelated refactors, broad formatting, speculative abstraction, and silent compatibility breaks.
- Treat generated files, secrets, install roots, production data, and migrations as higher risk.
- Never continue a stale plan after new evidence invalidates it.
- Do not claim completion from an implementer report; inspect diff and evidence.

## Checkpoint

Record task and requirement IDs, files changed, diff summary, commands and results, review status, assumptions changed, open gaps, worktree/commit state, and next task.
