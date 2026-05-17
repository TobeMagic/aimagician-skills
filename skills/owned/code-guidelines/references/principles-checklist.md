# Code Guidelines Checklist

## Before Editing

- What is the exact goal?
- What is explicitly out of scope?
- What assumptions am I making?
- What ambiguity would change the implementation?
- What verification will prove the task is done?

## During Editing

- Prefer existing code patterns.
- Keep the diff focused on the task.
- Avoid new abstractions unless they remove real current complexity.
- Do not clean up unrelated code.
- Preserve user or teammate changes.

## Verification

- Run the narrowest meaningful command first.
- Broaden verification when shared behavior or user-facing flows changed.
- If verification cannot run, state why.
- If the result is partial, state the residual risk.

## Review Before Final

- Every changed line should trace back to the task.
- The solution should be simpler than the problem deserves, not simpler than correctness requires.
- Final answer should include target, changes, verification, and relevant risk.

