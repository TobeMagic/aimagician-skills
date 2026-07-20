# Ideation And Scope

Use this module to expand the option space briefly, then converge on the smallest defensible implementation direction.

## Brainstorming Loop

1. Ground the discussion in the user objective and current system.
2. Separate WHAT/WHY questions from HOW decisions.
3. Generate two or three viable shapes when architecture, workflow, or UX has real alternatives.
4. Compare user value, complexity, risk, compatibility, migration, maintenance, and verification.
5. Identify the irreducible core and optional extensions.
6. Recommend one direction with concrete reasoning.
7. Re-discuss findings that change boundaries, behavior, data, dependencies, or acceptance.
8. Lock the chosen direction and move rejected or deferred ideas outside the active phase.

## Assumption Analysis

Inspect assumptions about users, permissions, data ownership, privacy, scale, performance, accessibility, responsive behavior, deployment, compatibility, migration, manual steps, cost, schedule, and recovery.

Mark each assumption as:

- **Confirmed:** explicitly supported by the user or source of truth.
- **Inferred:** supported by evidence but not explicitly locked.
- **Risky:** likely to change implementation or acceptance if wrong.
- **Deferred:** intentionally outside the current delivery unit.

Risky assumptions must be confirmed, researched, or converted into an acceptance check before planning.

## Decomposition

Split work when independent outcomes, decision gates, separate owners, conflicting write scopes, broad verification, or staged value justify it. Each phase needs a measurable outcome, requirement IDs, dependencies, explicit boundary, verification, and completion signal.

Do not split a tightly coupled vertical slice merely to create more phases. Prefer the smallest end-to-end slice that proves the architecture early.

## Visual And Domain Exploration

For visual work, preserve the visual-question and comparison protocol but route detailed design exploration to `interface-design`. Use real screenshots, references, or prototypes when visual evidence is necessary. Do not start a separate local visual service merely to satisfy the workflow.
