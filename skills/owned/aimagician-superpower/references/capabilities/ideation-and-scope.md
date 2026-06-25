# Ideation And Scope

Use this module when the task needs alternatives, design exploration, feature shaping, decomposition, or assumption analysis before planning.

## Intent

Generate better options without losing the user's real goal. The output should narrow the work toward an executable direction, not expand it indefinitely.

## Process

1. Understand the current product, codebase, and user goal.
2. Identify independent subsystems or phases.
3. Ask focused questions only where answers change implementation.
4. Propose two or three viable approaches with tradeoffs.
5. Compare by user value, implementation cost, risk, verification cost, maintainability, and compatibility.
6. Recommend one approach and state why.
7. Lock assumptions and non-goals before planning.

## Assumption Review

Look for assumptions about:

- target users and workflows;
- data ownership and privacy;
- permission or authentication boundaries;
- performance and scale;
- responsive or accessibility expectations;
- deployment environment;
- migration or compatibility requirements;
- acceptable manual steps;
- deadline or budget.

Mark each assumption as confirmed, inferred, risky, or deferred.

## Decomposition

Split the work when:

- multiple independent systems are involved;
- verification would be too broad for one pass;
- user decisions are needed between stages;
- one part can deliver value before the rest;
- failure in one part should not block another.

Each phase should have a user-visible outcome, files likely to change, acceptance checks, and a clear completion signal.

## Option Quality

Good options are concrete and comparable. Avoid false choices such as "do it properly" versus "do it quickly." Each option should name the implementation shape, tradeoff, risk, and verification path.
