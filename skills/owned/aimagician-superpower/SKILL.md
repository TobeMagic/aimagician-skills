---
name: aimagician-superpower
description: Use when starting or resuming substantial work, shaping ambiguous goals, planning a milestone, executing multi-phase implementation, or closing work with research, verification, audit, and handoff discipline.
category: build
subcategory: workflow
tags:
  - workflow
  - planning
  - research
  - execution
  - verification
  - audit
metadata:
  capability_modules:
    - references/capabilities/intake-and-boundary.md
    - references/capabilities/state-and-continuity.md
    - references/capabilities/research-and-discovery.md
    - references/capabilities/ideation-and-scope.md
    - references/capabilities/planning-modes.md
    - references/capabilities/execution-modes.md
    - references/capabilities/verification-and-uat.md
    - references/capabilities/audit-and-closure.md
    - references/capabilities/domain-gates.md
  preferred_companions:
    - skill-creator
    - webapp-testing
    - interface-design
compatibility:
  tools: [bash, git]
  requires: A concrete objective, repository context, and a verifiable completion signal
---

# AImagician Superpower

Use this skill as the operating system for serious work. It turns an ambiguous request into a researched, discussed, executable, verified, and recoverable delivery loop.

The skill is not a proposal generator. It is a disciplined workflow for preserving intent, avoiding capability loss, and proving completion.

## Capability Routing

Read these modules only when the task needs their detail. The main loop below is the default path; modules are specialized guidance for larger, riskier, or resumable work.

| Need | Module |
|---|---|
| Goal alignment, scope boundaries, first discussion, phase kickoff | `references/capabilities/intake-and-boundary.md` |
| Milestone state, phase artifacts, resume, pause, progress, checkpoints | `references/capabilities/state-and-continuity.md` |
| Local discovery, codebase mapping, dependency checks, web research | `references/capabilities/research-and-discovery.md` |
| Brainstorming, alternatives, decomposition, assumption review | `references/capabilities/ideation-and-scope.md` |
| Phase planning, plan review, MVP/TDD/research planning modes | `references/capabilities/planning-modes.md` |
| Execution modes, small changes, parallel workers, branch/worktree discipline | `references/capabilities/execution-modes.md` |
| Verification, UAT, eval review, regression checks, evidence capture | `references/capabilities/verification-and-uat.md` |
| Audit, cleanup, closure summary, learning extraction, handoff | `references/capabilities/audit-and-closure.md` |
| Domain gates for code, UI, docs, security, operations, and reviews | `references/capabilities/domain-gates.md` |

## Core Standard

Every substantial task must produce answers to these questions before implementation starts:

1. What is the real goal?
2. What is explicitly in scope?
3. What is explicitly out of scope?
4. What constraints, risks, dependencies, and user preferences matter?
5. What evidence will prove completion?
6. What durable context is needed so the work can survive interruption or handoff?

If any answer is missing and materially changes the implementation, discuss it before planning.

## Operating Loop

Use this loop for each meaningful unit of work.

### 1. Establish Target And Boundary

- Restate the objective in concrete terms.
- Identify the smallest useful delivery unit.
- Define success criteria, non-goals, user-visible behavior, and rollback or stop conditions.
- Detect whether this is a quick task, a phase, or a milestone.
- For resumable work, read existing `.planning/STATE.md`, roadmap, prior context, open plans, validation notes, and recent summaries before asking new questions.

### 2. Discuss Baseline Requirements

- Ask only questions that change scope, behavior, acceptance, or risk.
- Prefer concrete options with tradeoffs over open-ended interviews.
- Capture decisions, assumptions, rejected options, and deferred ideas.
- Do not allow scope creep to enter the current phase silently; record it as a future item.
- If the user says not to write a spec, still produce a concise implementation plan before editing.

### 3. Research And Brainstorm

- First inspect local code, docs, tests, configs, schemas, tickets, wiki pages, and prior planning artifacts.
- Use web research when facts may be current, when third-party APIs or packages are involved, when recommendations affect cost or architecture, or when local evidence is insufficient.
- Generate multiple viable approaches before choosing one. Compare them by complexity, maintainability, verification cost, compatibility, and user fit.
- Record assumptions that need confirmation before planning.
- For package or tool choices, verify that the dependency exists, is compatible with the runtime, and is appropriate for the repo.

### 4. Re-Discuss Boundaries And Assumptions

- Bring research findings back to the user when they change scope, risk, timeline, dependency choice, UX, data handling, or acceptance.
- Lock the chosen direction, explicit non-goals, and assumptions.
- If research invalidates the original request, recommend the smallest corrected path.
- If the next step is still ambiguous, continue discussion instead of planning.

### 5. Plan

- Write a plan only after target, boundary, research, and assumptions are stable.
- Keep one plan for one delivery unit; do not split the same workflow across parallel plan systems.
- Include file or module scope, ordered tasks, dependency waves, exact verification commands, acceptance criteria, and checkpoint rules.
- Make each task atomic enough to execute and verify independently.
- Include rollback or recovery notes when the work touches shared infrastructure, data, installation paths, secrets, or user-visible behavior.
- Review the plan against the verification dimensions before editing.

### 6. Execute

- Read relevant implementation code before changing it.
- Make the smallest change that satisfies the verified plan.
- Prefer existing local patterns, helpers, tests, and dependencies.
- Preserve user edits and dirty worktree state.
- Avoid unrelated cleanup, formatting churn, broad renames, or speculative abstractions.
- Use tests or probes before implementation when behavior can be pinned down.
- Checkpoint after meaningful units of work, especially before risky edits or phase transitions.

### 7. Verify

- Run the narrowest useful verification first.
- Broaden to typecheck, lint, build, integration, browser, document, or manual acceptance checks when the blast radius justifies it.
- Do not claim completion without command output, inspected artifacts, or a concrete manual check.
- Record validation gaps, skipped checks, flaky results, and residual risk.
- For user-facing work, define observable acceptance scenarios and verify them directly.

### 8. Audit

- Compare the result against the original goal, locked assumptions, success criteria, and non-goals.
- Check requirement coverage, integration wiring, regression risk, unverified claims, and TODO or placeholder debt.
- Confirm that no prior capability was accidentally removed unless the user explicitly accepted that tradeoff.
- If gaps remain, classify them as blocker, follow-up, or intentionally deferred.

### 9. Handoff And Complete

- Summarize what changed, what passed, what was not verified, and what remains.
- Update durable state when the work crosses a phase or milestone boundary.
- Include enough detail for another agent to resume without re-discovering the same facts.
- For closure, provide a concise completion summary with evidence, residual risk, and next recommended action.

## Durable Artifacts

Use durable artifacts when work is large, resumable, risky, or spans multiple turns.

- `.planning/STATE.md`: current phase, status, next action, active assumptions, and resumable context.
- `.planning/ROADMAP.md`: ordered phases, dependencies, and status.
- `.planning/phases/<phase>/<phase>-CONTEXT.md`: objective, constraints, decisions, success criteria, and non-goals.
- `.planning/phases/<phase>/<phase>-DISCUSSION-LOG.md`: questions, answers, rejected options, and deferred ideas.
- `.planning/phases/<phase>/<phase>-RESEARCH.md`: local evidence, external research, alternatives, dependency checks, and risk findings.
- `.planning/phases/<phase>/PLAN.md`: executable task plan, file map, verification commands, acceptance criteria, and checkpoints.
- `.planning/phases/<phase>/<phase>-VALIDATION.md`: command results, manual checks, evidence, gaps, and residual risk.
- `.planning/phases/<phase>/<phase>-UAT.md`: user-visible acceptance scenarios and outcomes.
- `.planning/phases/<phase>/<phase>-AUDIT.md`: requirement coverage, regression review, and closure decision.
- `.planning/phases/<phase>/<phase>-SUMMARY.md`: handoff-ready completion summary.

For small tasks, keep artifacts inline in the conversation unless persistence is needed.

## Verification Dimensions

Before executing a non-trivial plan, check:

1. Requirement coverage: every stated requirement maps to work or an explicit non-goal.
2. Boundary clarity: scope, non-goals, and assumptions are locked.
3. Research adequacy: local and external evidence are sufficient for the chosen path.
4. Alternative review: credible options were compared before selection.
5. Task atomicity: each task can be completed and verified independently.
6. Dependency ordering: prerequisite work appears earlier, and dependency waves are clear.
7. File scope: expected files or modules are named, and unrelated churn is excluded.
8. Verification commands: tests, builds, probes, or manual checks are concrete.
9. Context fit: another agent can resume from artifacts without re-asking solved questions.
10. Regression safety: existing capability is preserved or intentionally replaced.

## Research Rules

- Browse when information is time-sensitive, high-stakes, externally sourced, package-specific, API-specific, or likely to have changed.
- Use primary sources for technical claims whenever practical.
- Clearly separate facts from inferences.
- Do not let research become implementation. Research ends with options, recommendation, assumptions, and planning inputs.
- If research is inconclusive, state what was checked and choose the safest next step or ask for a targeted decision.

## Execution Discipline

Use this discipline for every non-trivial code or document change:

1. Think before editing
   - State assumptions, constraints, and risky unknowns when they affect implementation.
   - Ask only when the missing answer materially changes the solution.
2. Simplicity first
   - Prefer the smallest workable change.
   - Prefer local conventions over new abstractions.
3. Surgical edits
   - Touch only files required for the task.
   - Do not reformat or refactor unrelated code.
   - Preserve dirty worktree changes that are not yours.
4. Evidence-driven completion
   - Define what proves done.
   - Run the checks.
   - Report the result and any remaining uncertainty.

## Related Owned Skills

- Use `skill-creator` when adding, merging, or rewriting owned skills.
- Use `webapp-testing` when a browser, screenshot, console, network, or responsive check is part of acceptance.
- Use `interface-design` when the task changes UI, visual language, accessibility, metadata, motion, or brand style.
- Use `github-readme-highstar` when README quality is part of acceptance.

## Output Contract

For active work, report:

- objective and boundary;
- research or evidence used;
- decisions made;
- plan or execution status;
- files changed;
- verification run and result;
- residual risk or next action.

For closure, report:

- completion summary;
- requirement and acceptance coverage;
- verification evidence;
- audit outcome;
- handoff notes.
