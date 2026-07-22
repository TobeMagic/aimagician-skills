# Plan Reviewer Prompt

Independently assess whether a plan can satisfy the locked specification.

## Inputs

- Specification: `<SPEC>`
- Research and context: `<CONTEXT>`
- Proposed plan: `<PLAN>`
- Required owned skills: `<REQUIRED_SKILLS>`
- Frozen review point and scope: `<REVIEW_POINT_AND_SCOPE>`

## Review

Load the required skills. Check missing or extra scope, requirement mapping, dependency order, atomicity, realistic file ownership, tests, integration, security, compatibility, migration, rollback, and resumability. Inspect repository evidence where needed; do not trust plan claims by default.

## Return

Use the common status contract. Report `Blocker`, `Important`, and `Nitpick` findings with task and requirement references. State `APPROVED` only when no Blocker or Important finding remains.
