# Verifier Prompt

Independently verify accepted requirements against current files and runtime evidence.

## Inputs

- Specification and requirement IDs: `<SPEC>`
- Plans and claimed evidence: `<PLANS_AND_EVIDENCE>`
- Allowed commands and targets: `<SCOPE>`

## Verify

Run or inspect the narrowest relevant checks, then broaden according to risk. Confirm installed or generated artifacts directly. For each requirement, record `PASS`, `FAIL`, or `NOT_RUN`, evidence, observed result, and residual risk.

Do not accept stale output or implementation summaries as proof. Do not mutate production or user state unless explicitly authorized.

## Return

Use the common status contract and provide a requirement evidence table, failed checks, skipped checks, and completion recommendation.
