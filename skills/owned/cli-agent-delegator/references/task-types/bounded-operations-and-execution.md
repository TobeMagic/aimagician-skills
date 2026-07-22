# Bounded Operations And Execution

Use this task family when OpenCode can perform a short, well-specified unit of mechanical engineering work while the main Agent retains design and final judgment.

## Suitable Tasks

- inspect `git status`, a named diff, branch state, changed-file list, or commit metadata;
- run named tests, typecheck, lint, build, format check, smoke check, or non-destructive diagnostic;
- monitor a long-running check and return progress, failures, affected tests, and a concise report;
- compare command output or artifacts with explicit acceptance criteria;
- inspect pre-commit readiness and identify accidental scope or generated pollution;
- make a short low-risk implementation in a clean isolated worktree when behavior, files, tests, and permissions are already locked.

Do not delegate unresolved architecture, product behavior, broad refactors, production operations, secret handling, destructive cleanup, publishing, merging, or pushing as a “simple task.”

## Git And Test Inspection

The prompt must name the exact repository/worktree and the intended review point. For test execution, include exact commands or an allowed command class, expected success condition, known environment constraints, and whether build/test artifacts are expected.

Use `read-and-run`. Capture before/after git status. Return:

- command and exit status;
- concise relevant output, failing test names, and first actionable error;
- whether the failure appears introduced, pre-existing, flaky, environmental, or unknown;
- files or artifacts created by the command;
- checks not run and why;
- recommended next diagnostic or correction.

Do not mutate tests merely to make them pass. Do not clean generated output unless the controller explicitly names the paths and authorizes removal.

## Bounded Write Gate

All conditions must hold:

1. the controller has resolved requirements and design decisions;
2. the task is short and independently verifiable;
3. the controller created a clean isolated worktree or routed through `parallel-worktree-pr-flow`;
4. `WRITE_SCOPE` is the exact write scope and lists every allowed path;
5. tests and expected behavior are explicit;
6. no public contract, migration, security boundary, production state, or user-owned dirty work is silently exposed;
7. the worker must stop if correctness requires scope expansion.

The worker reads required skills first, inspects local patterns, applies the smallest coherent change, runs the named checks, reviews its own diff, and returns changed paths plus evidence. It does not redesign the task while coding.

## Commit Policy

Default is `no-commit`. A local commit is allowed only when:

- the prompt says `local-commit-after-review`;
- an independent combined review for a quick write, or specification then quality review for substantial work, has passed;
- git status contains only allowed changes;
- the exact commit message policy is supplied.

Push is never implied by commit permission.

## Controller Checks

The main Agent verifies the review point, changed paths, diff scope, decisive command output, and any claimed environmental failure. For writes, inspect the actual diff rather than accepting the worker summary.
