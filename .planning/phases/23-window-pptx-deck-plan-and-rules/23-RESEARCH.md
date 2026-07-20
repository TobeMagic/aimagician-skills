# Phase 23 Research: Weak-Model Semantic Compiler

## Failure Modes to Eliminate

| Weak-model behavior | Deterministic replacement |
|---|---|
| Copies prose directly onto slides | Typed content blocks and semantic page-role inference |
| Chooses one repeated layout | Ranked candidates plus cross-slide rhythm penalties |
| Misses commercial narrative | Fifteen predefined archetypes with ordered section roles |
| Overfills pages | Per-family capacity rules and deterministic split continuation |
| Fills sparse pages with decoration | Sparse-content preservation and emphasis-safe defaults |
| Makes untraceable choices | Stable rule IDs, scores, top-three candidates, confidence, and fallback reason |
| Invents unsupported design instructions | Schema and semantic validation reject raw design/COM/code fields |

## Compiler Boundary

The input is JSON-compatible DeckPlan v1. Schema validation establishes structure; semantic validation checks controlled vocabularies and forbidden fields. The compiler expands an archetype when explicit slides are absent, or normalizes supplied semantic slides when present. Capacity runs before layout ranking. Rhythm context influences ranking but never introduces randomness; ties resolve by stable candidate ID.

The output remains design-neutral: slide role, semantic form, content blocks, chart intent, importance, selected page family, alternatives, and decision trace. Phase 24 resolves actual layouts and themes.
