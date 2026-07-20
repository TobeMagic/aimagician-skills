# Plan Reviewer Prompt

Independently assess whether a plan can satisfy the locked specification.

## Inputs

- Specification: `<SPEC>`
- Research and context: `<CONTEXT>`
- Proposed plan: `<PLAN>`

## Review

Check missing or extra scope, requirement mapping, dependency order, atomicity, realistic file ownership, tests, integration, security, compatibility, migration, rollback, and resumability. Inspect repository evidence where needed; do not trust plan claims by default.

## Return

Use the common status contract. Report blocking, important, and minor findings with task and requirement references. State `APPROVED` only when no blocking or important finding remains.
