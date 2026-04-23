# Principles Checklist

## 1) Think Before Coding

- Problem statement is explicit and testable.
- Ambiguities are listed.
- Assumptions are documented.
- Tradeoffs are explicit.

## 2) Simplicity First

- Proposed change is the minimal path to green.
- No speculative abstractions.
- No new configuration unless strictly required.

## 3) Surgical Changes

- Diff only touches relevant files/lines.
- No unrelated refactors or formatting-only churn.
- Existing behavior outside scope remains unchanged.

## 4) Goal-Driven Execution

- A failing check exists before fix (test or reproducible command).
- A passing check exists after fix.
- Validation covers the original failure mode.

## Commit quality gate

- Commit message describes intent and scope.
- Patch can be reviewed in minutes.
- Rollback risk is low because blast radius is small.
