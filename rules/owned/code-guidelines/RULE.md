---
name: code-guidelines
description: Default coding discipline for implementation, fixes, and refactors
alwaysApply: true
---

# Code Guidelines

1. Think before coding. State goal, out-of-scope, assumptions, and the check that proves done. Ask only when the answer changes the implementation.
2. Simplicity first. Smallest change that solves the current problem. No speculative adapters, config layers, or future-proofing.
3. Implement next to the caller. Extract a helper only after a second real use, or when the logic needs its own tests. Do not split one-line object assembly into a new file.
4. Surgical diffs. Touch only required lines. Mention unrelated problems; do not fix them in the same change.
5. Goal-driven. Turn "do X" into a verifiable goal. Reproduce a bug when practical, then make that check pass. Follow existing local patterns.

Report: target, key changes, verification command and result, residual risk.
