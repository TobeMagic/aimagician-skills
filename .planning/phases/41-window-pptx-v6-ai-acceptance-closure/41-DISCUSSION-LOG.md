# Phase 41 Discussion Log

## Decisions

- Replace the historical human-only v5 gate with the user's three-context
  AI-only v6 contract.
- Preserve all failed rounds and their exact hashes.
- Treat reference/candidate misattribution and invented unseen details as
  invalid review evidence.
- Use fresh GPT-5.5 visual contexts for the final blind matrix and fresh
  OpenCode Agnes for the independent completion audit.

## Assumptions

- A reviewer may use a different lens but must use the same frozen rubric and
  thresholds.
- The final aggregate is computed from accepted review JSON, never from prose.

## Rejected Options

- Lowering thresholds after a failure.
- Reusing Direct Agnes scores that cite the wrong attachment.
- Manual aesthetic scoring or a two-reviewer fallback.

## Deferred Work

- Cross-provider reviewer diversity beyond the currently available
  visual-capable routes.
