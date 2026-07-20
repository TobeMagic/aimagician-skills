# Phase 23 Validation: DeckPlan and Semantic Rules

**Status:** Active / Incomplete

## Required Evidence

- [ ] DeckPlan schema parses and validates representative minimal and full plans.
- [ ] Raw coordinates, colors, fonts, COM instructions, arbitrary code, and unknown top-level fields are rejected.
- [ ] All 15 archetypes are unique, loadable, and compile into ordered slide roles.
- [ ] Semantic mapping covers sequence, comparison, parallel points, KPI, trend, composition, matrix, risk, recommendation, and sparse content.
- [ ] Ranking is deterministic, exposes the top three, and uses a safe fallback below the confidence threshold.
- [ ] Capacity splitting preserves every content item and creates stable continuation slides.
- [ ] Sparse content is preserved rather than padded.
- [ ] Rhythm rules penalize excessive repeated families without breaking semantic fitness.
- [ ] JSON artifacts and decision traces are serializable and stable.
- [ ] Focused and complete window-pptx suites pass with no unresolved Critical or Important finding.

## Verdict

Not ready to close; implementation has not started.
