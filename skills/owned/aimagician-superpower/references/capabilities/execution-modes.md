# Execution Modes

Use this module when carrying a plan through edits, commands, reviews, and checkpoints.

## Standard Execution

1. Read the relevant files before editing.
2. Confirm current git status and protect user changes.
3. Execute the next task only.
4. Keep edits small and local to the planned scope.
5. Run the narrow verification for that task.
6. Checkpoint the result before moving to the next dependency wave.

## Mode Selection

- Quick mode: small, low-risk change with direct verification.
- Fast mode: several simple edits with one focused test pass after each meaningful group.
- Autonomous mode: continue through a locked plan until a blocker changes scope, risk, or acceptance.
- Repair mode: reproduce the defect first, then patch and prove the regression.
- Parallel mode: split independent tasks across isolated workers only when file scopes do not conflict.
- Branch/worktree mode: use isolated workspaces when changes are large, risky, or parallel.

## Parallel Worker Rules

Use parallel workers only when:

- tasks are independent;
- write scopes are explicit;
- each worker has clear acceptance checks;
- integration order is defined;
- one coordinator reviews and merges returned work.

Each worker brief should include objective, files allowed, files forbidden, tests to run, expected output, and handoff format.

## Code Discipline

- Prefer existing local patterns and helpers.
- Avoid speculative abstractions.
- Keep unrelated refactors out of the change.
- Use structured parsers or APIs instead of fragile string manipulation when available.
- Add comments only where they clarify non-obvious logic.
- Preserve formatting outside edited areas.
- Do not continue executing a stale plan after a new blocker invalidates it.

## Checkpoint Content

Record:

- task completed;
- files changed;
- commands run;
- result;
- problems found;
- assumptions updated;
- next task.
