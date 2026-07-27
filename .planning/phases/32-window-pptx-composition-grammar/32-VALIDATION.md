# Phase 32 Validation: Consulting Proposal Grammar Tracer

**Status:** First tracer implemented; visual acceptance remains open
**Date:** 2026-07-27
**Release verdict:** `NO_GO`

## Implemented tracer

- Registered `consulting-project-proposal-v1` with twelve bounded recipes and
  exactly one capacity-safe wildcard fallback.
- Propagated recipe identifiers through `VisualPlan`, `DeckPlan`, and
  `RenderPlan` as deterministic layout-variant seeds.
- Added source-preserving Chinese list extraction for process, timeline,
  matrix, governance, and risk/action pages.
- Localized governed role titles and supporting text.
- Added a reproducible twelve-slide Chinese consulting-proposal fixture,
  compact result manifest, and selected contact-sheet preview.

## Real artifact

- PPTX:
  `.planning/evidence/phase32-consulting-tracer-r2/output/consulting-proposal.pptx`
- PPTX SHA-256:
  `18627091c2a01d895def85621bb6d2bdb44e58de7588fa92104f221ae40f91ca`
- committed preview:
  `skills/owned/window-pptx/evals/previews/consulting-project-proposal-r2.png`
- layout signatures: `6 -> 9`
- average editable/visual objects: `12.417 -> 14.25`
- rich-slide ratio: `1.0`
- automatic Quality Report v2: PASS
- manual visual verdict: `PARTIAL_NOT_REFERENCE_GRADE`

The tracer proves that the recipe and CJK structuring chain works. It does not
yet match the art direction, information hierarchy, and visual density of the
authorized work-summary reference.

## Regression evidence

```text
72 passed
92 passed
695 passed, 9 skipped in 817.68s
108 passed (repository Vitest suite)
TypeScript typecheck: PASS
TypeScript build: PASS
Skillbird format-skills: 23 checked, 0 issues
composition public API smoke test: PASS
```

The first Vitest invocation inherited a PATH without a `python` executable
(`python3` was present) and therefore failed one unrelated secret-inventory
test with `spawn python ENOENT`. Repeating the unchanged suite with the
repository's Miniforge Python directory on PATH passed all 108 tests.

## Reviewer route

- `opencode/deepseek-v4-flash-free` was rate limited.
- The Agnes connector did not prove image-input support for the attached
  contact sheet.
- Two Agnes code-review attempts loaded the required skills and inspected the
  implementation but did not return a final scoped verdict.
- No independent visual or code approval is claimed.

## Acceptance gaps

1. Recipe-aware component composition instead of seed-only influence.
2. Stronger cover, section, and hero-page visual anchors.
3. Evidence callouts and clearer business-message hierarchy.
4. An automatic gate for advanced diagrams with too few meaningful nodes.
5. A working independent image-review route or recorded human review.
6. Cross-scenario proof beyond project proposals.
