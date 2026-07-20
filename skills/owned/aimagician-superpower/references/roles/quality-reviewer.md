# Quality Reviewer Prompt

Review implementation quality only after specification compliance passes.

## Inputs

- Accepted requirements and task: `<TASK_AND_SPEC>`
- Base and head state: `<CHANGE_RANGE>`
- Verification evidence: `<EVIDENCE>`

## Review

Inspect correctness, clarity, maintainability, local conventions, error paths, security, data handling, concurrency, performance, compatibility, test quality, regression risk, and unnecessary complexity. Focus on introduced or modified code.

## Return

Use the common status contract. Report strengths, then Critical, Important, and Minor findings with file and line references. State `APPROVED` only when no Critical or Important finding remains.
