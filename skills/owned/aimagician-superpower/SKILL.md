---
name: aimagician-superpower
description: Use when starting or resuming substantial work, planning a milestone, merging/refactoring skills, executing multi-phase implementation, or when the user wants GSD-style discuss-plan-execute verification without external installers or hook injection.
category: build
subcategory: workflow
tags:
  - gsd
  - superpowers
  - planning
  - verification
metadata:
  merged_from:
    - gsd
    - using-superpowers
    - writing-plans
    - executing-plans
    - code-guidelines
  preferred_companions:
    - test-driven-development
    - verification-before-completion
compatibility:
  tools: [bash, git]
  requires: A concrete objective, repository context, and a verifiable completion signal
---

# AImagician Superpower

This is the owned workflow entrypoint for serious work. It takes the useful parts of GSD and Superpowers, but keeps ownership local: no external installer, no forced hooks, and no scattered default planning skills.

## Source Decisions

- GSD provides the canonical milestone state machine: discuss, plan, execute, verify, audit.
- Superpowers `writing-plans` is folded into GSD phase planning: file map, concrete steps, exact commands, explicit acceptance criteria, and self-review for missing coverage.
- Superpowers `executing-plans` is folded into GSD execution: follow the active plan, checkpoint after meaningful tasks, and stop on blockers that would change the plan.
- `code-guidelines` is folded into this skill as the default execution discipline: read first, keep changes small, scope files tightly, and verify with concrete evidence.
- External installers, auto-update hooks, community commands, and forced shell integration are excluded.

## Core Contract

Use one loop for each meaningful unit of work:

1. Discuss
   - Confirm the real objective, constraints, success criteria, and risky assumptions.
   - If the user asks to avoid a spec, produce an implementation plan directly.
   - Split large work into phases that can be reviewed independently.
   - Capture durable context in `.planning/phases/<phase>/<phase>-CONTEXT.md` when the phase is large or resumable.
   - Preserve key questions, decisions, and rejected options in `<phase>-DISCUSSION-LOG.md` when discussion affects implementation choices.
2. Plan
   - Write the smallest plan that preserves capability and makes verification clear.
   - Prefer GSD's milestone/phase state model for durable work.
   - Integrate Superpowers planning discipline into the phase plan instead of creating duplicate plan folders.
   - Use `<phase>-RESEARCH.md` for implementation research, dependency assessment, and external reference notes.
   - Write `PLAN.md` with a file map, ordered tasks, exact commands, expected outputs, acceptance criteria, and rollback or checkpoint notes.
   - Run the plan through the 8 Verification Dimensions before execution.
3. Execute
   - Follow the built-in code discipline: read first, keep edits scoped, avoid unrelated churn.
   - Use tests or probes before implementation when behavior can be pinned down.
   - Preserve user changes in dirty worktrees.
   - Execute by dependency waves when tasks can be parallelized safely; later waves must wait for files or decisions produced by earlier waves.
   - Keep commits/checkpoints atomic when the surrounding workflow asks for commit discipline.
4. Verify
   - Run the narrowest useful verification first, then broader checks when blast radius justifies it.
   - Do not claim completion without command output or a concrete manual check.
   - Record validation gaps and evidence in `<phase>-VALIDATION.md` for non-trivial phases.
   - Use `<phase>-UAT.md` for user-facing acceptance, manual probes, or conversational acceptance results.
5. Handoff
   - Summarize what changed, what passed, and what remains uncertain.
   - Update milestone state when work crosses a phase boundary.

## Milestone Model

Use a single active milestone for a coherent initiative. Suggested files:

- `.planning/MILESTONES.md` for milestone index and phase gates.
- `.planning/ROADMAP.md` for ordered phases and current status.
- `.planning/STATE.md` for current phase, next action, and resumable context.
- `.planning/phases/<nn>-<slug>/PLAN.md` only after discuss is complete for that phase.

Phase gates:

- `discuss`: requirements and tradeoffs are explicit.
- `plan`: implementation and verification are concrete.
- `execute`: code/docs/data are changed.
- `accept`: tests and user-facing acceptance are complete.
- `audit`: milestone capability and requirement coverage are checked before closure.

## Planning Artifacts

Use these names when durable state matters:

- `<phase>-CONTEXT.md`: objective, constraints, current repo state, assumptions, and success criteria.
- `<phase>-DISCUSSION-LOG.md`: questions asked, answers received, alternatives rejected, and decisions made.
- `<phase>-RESEARCH.md`: reference review, API/package choices, compatibility notes, and risk findings.
- `PLAN.md`: implementation tasks, file map, commands, dependency waves, and acceptance criteria.
- `<phase>-VALIDATION.md`: verification commands, manual checks, findings, and unresolved risks.
- `<phase>-UAT.md`: user-visible acceptance scenarios, outcomes, and follow-up fixes.

## 8 Verification Dimensions

Before executing a non-trivial phase, check the plan against:

1. Requirement coverage: every stated requirement maps to work or an explicit non-goal.
2. Task atomicity: each task can be completed and verified without hidden scope.
3. Dependency ordering: prerequisite work appears earlier, and dependency waves are clear.
4. File scope: expected files are named, and unrelated churn is excluded.
5. Verification commands: tests, builds, lint, probes, or manual checks are concrete.
6. Context fit: the plan can survive context resets through `.planning` artifacts.
7. Gap detection: ambiguous assumptions are called out before execution.
8. Regression safety: existing capability from merged sources is preserved or intentionally replaced.

## Package Legitimacy

When a plan introduces or updates packages, tools, CLIs, or external services:

- prefer existing repo dependencies and local helpers first;
- verify the package is real, maintained enough for the task, and compatible with the runtime;
- record why it is needed in research or the plan;
- stop for a human checkpoint if installation fails, licensing is unclear, or the dependency changes architecture.

## Built-In Code Discipline

Use this discipline for every non-trivial code change:

1. Think before coding
   - State assumptions, constraints, tradeoffs, and risky unknowns before editing when they affect implementation.
   - Ask only when a missing answer would materially change the solution.
2. Simplicity first
   - Make the smallest workable change that satisfies the current goal.
   - Prefer existing local patterns, helpers, and dependencies over new abstractions.
3. Surgical changes
   - Touch only files required for the task.
   - Do not reformat, rename, or refactor unrelated code.
   - Preserve user edits and dirty worktree state.
4. Goal-driven verification
   - Define what proves completion.
   - Run the narrowest useful verification first, then broaden when blast radius justifies it.
   - Report command results, manual checks, and residual risk clearly.

## Consolidation Rules

- Keep GSD as the state machine backbone.
- Fold Superpowers quality gates into this workflow instead of installing Superpowers as a command source.
- Keep code discipline here instead of installing `code-guidelines` as a separate active skill.
- Prefer owned skills over external catalog sources. External sources are references until explicitly enabled.
- Merge duplicate workflows by outcome, not by source repository.
- Do not downgrade a merged skill until a regression audit shows the old workflow is either preserved here or intentionally moved to another owned skill.

## When To Escalate To Companion Skills

- `test-driven-development`: when behavior can be specified with a failing test.
- `systematic-debugging`: when a failure is unknown or not reproducible.
- `verification-before-completion`: before marking work complete.
- `skill-creator`: when adding or changing owned skills.
- `github-readme-highstar`: when README quality is part of acceptance.

## Output Contract

For a phase or milestone update, provide:

- current phase and status;
- decisions made;
- files changed;
- verification run and result;
- next phase or explicit residual risk.

For milestone closure, add a requirement-by-requirement audit and call out any capability regression against the reference sources before marking the milestone complete.

## Anti-Patterns

- Installing external workflow frameworks by default.
- Maintaining parallel plan systems for the same phase.
- Letting auto-update hooks mutate the environment.
- Splitting one workflow into many tiny skills when a single phase contract is clearer.
