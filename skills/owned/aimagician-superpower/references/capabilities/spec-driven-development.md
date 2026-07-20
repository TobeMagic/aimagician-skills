# Spec-Driven Development

Use this module when a task requires a formal, falsifiable contract before implementation.

## Formal-Spec Triggers

A phase specification is mandatory for public behavior or APIs, schemas or migrations, security or permissions, external integrations, UI or AI contracts, production or installation state, multiple modules, multiple agents, multiple phases, destructive effects, difficult rollback, or material ambiguity.

## Draft-To-Lock Workflow

1. Create a draft specification after the baseline requirement discussion.
2. Ground the current state in code, docs, tests, runtime evidence, and prior decisions.
3. Research viable approaches and hidden constraints.
4. Re-discuss findings that change WHAT, WHY, boundaries, risk, or acceptance.
5. Score clarity and resolve blocking questions.
6. Set status to `Locked` only when the gate passes or the user explicitly records an exception with its risk.
7. Discuss implementation choices and write context only after requirements are locked.
8. If a locked requirement changes, return the specification to `Draft`, update it, and re-run downstream plan checks.

## Ambiguity Model

Score each dimension from 0.0 to 1.0:

| Dimension | Weight | Minimum | Meaning |
|---|---:|---:|---|
| Goal clarity | 0.35 | 0.75 | The measurable outcome is specific |
| Boundary clarity | 0.25 | 0.70 | In-scope and out-of-scope work are explicit |
| Constraint clarity | 0.20 | 0.65 | Compatibility, data, performance, and operational limits are known |
| Acceptance clarity | 0.20 | 0.70 | A verifier can produce pass/fail evidence |

`ambiguity = 1 - (0.35*goal + 0.25*boundary + 0.20*constraint + 0.20*acceptance)`

The lock gate requires ambiguity at or below 0.20 and every dimension at or above its minimum.

## Interview Loop

Use at most 2-3 meaningful questions per round. Rotate perspectives rather than repeating generic clarification:

1. **Reality:** What exists, what is missing, and what triggered the work?
2. **Simplification:** What is the smallest outcome that solves the core problem?
3. **Boundary:** What must not be included, and where does the phase stop?
4. **Failure:** What result would a verifier reject, and what edge case invalidates the requirement?
5. **Closure:** What unresolved point could still make the planner choose incorrectly?

Re-score after each round. After six rounds, either continue discussion, explicitly record a user-approved exception, or abandon the spec. High-risk work cannot auto-accept an unresolved blocking question.

## Requirement Contract

Every requirement needs a stable ID and all three state lines:

- **Current:** evidence-backed behavior before the phase.
- **Target:** specific behavior after the phase.
- **Acceptance:** a concrete pass/fail check.

Reject vague requirements such as "improve quality" or "make it faster". Replace them with an observable threshold, state transition, output, error behavior, or user scenario.

The specification must also contain goal, background, in-scope and out-of-scope boundaries, constraints, acceptance checkboxes, blocking questions, ambiguity report, and decision log.

## Downstream Gates

- Discussion treats locked requirements and boundaries as immutable until the specification is revised.
- Research may add evidence but may not silently change the contract.
- Plans must cite requirement IDs.
- Implementers receive the exact relevant requirements and accepted plan task.
- Specification reviewers inspect actual changes rather than trusting implementation summaries.
- Verification records one evidence status for every requirement.
- Completion fails while any accepted requirement is unplanned, failed, not run, or unsupported.

Use `workflow.mjs validate --gate spec`, then `trace`, to enforce the machine-checkable subset.
