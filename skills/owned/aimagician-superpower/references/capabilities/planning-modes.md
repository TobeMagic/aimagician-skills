# Planning Modes

Use this module after target, boundary, research, and assumptions are stable.

## Standard Plan

A complete plan names:

- objective and non-goals;
- file and module scope;
- ordered tasks;
- dependency waves;
- data or state changes;
- test strategy;
- exact verification commands;
- manual acceptance checks;
- rollback or recovery notes;
- checkpoint rules.

## Plan Modes

Choose the mode that fits the work:

- Quick plan: one or two edits with a narrow verification command.
- Phase plan: a structured task list for a `.planning/phases/<phase>/PLAN.md` file.
- Research plan: a plan whose first deliverable is a research note and recommendation.
- MVP plan: vertical slices that prove the end-to-end workflow early.
- TDD plan: failing test, minimal implementation, passing test, refactor, broader verification.
- Repair plan: reproduce, isolate cause, patch, regression test, audit related behavior.
- Review plan: findings first, then fixes or follow-up tasks.
- Gap-closure plan: map failed validation or audit gaps to the smallest correcting tasks.

## Planning Rules

- Do not plan before the user-impacting boundary is clear.
- Do not split one workflow across multiple competing plans.
- Keep tasks independently executable and verifiable.
- Place dependency work before dependents.
- Include exact commands, expected outcomes, and artifact paths.
- Include acceptance criteria that are observable.
- If the user rejects a plan assumption, update only the affected tasks.

## Plan Review

Before execution, check:

1. Every requirement maps to a task or explicit non-goal.
2. Every risky assumption is confirmed, mitigated, or documented.
3. File scope is narrow and realistic.
4. Verification covers behavior, integration, and regression risk.
5. Rollback or recovery is defined for shared state.
6. The plan can be resumed by another agent.

## Plan Artifacts

For durable plans, use:

- `PLAN.md` for tasks;
- `RESEARCH.md` for evidence and alternatives;
- `VALIDATION.md` for command results;
- `UAT.md` for acceptance scenarios;
- `AUDIT.md` for coverage and risk review;
- `SUMMARY.md` for handoff.
