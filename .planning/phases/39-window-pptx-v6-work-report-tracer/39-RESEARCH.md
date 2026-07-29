# Phase 39 Research

## Objective

Determine the smallest native-editable implementation that reproduces the
reference deck's senior art-direction logic while preserving a complete,
decision-oriented 32-slide work report.

## Local Evidence

- Authorized reference:
  `.planning/references/pptx/工作总结.pptx`
- Reference SHA-256:
  `59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839`
- Locked scenario:
  `annual-work-report`
- Reference baseline:
  `.planning/evidence/phase38-reference-baseline/contact-sheet.png`
- Accepted visual logic: warm ivory, institutional green, restrained gold,
  editorial whitespace, radial section motif, high-contrast evidence pages.

## Options

1. Copy physical slides and replace text. Rejected because capacity, dependency,
   and editability behavior would remain brittle.
2. Render HTML screenshots. Rejected because editability and canonical PPTX
   semantics would be lost.
3. Use registered native compositions governed by the accepted spine. Chosen
   because it preserves editable charts/tables and deterministic geometry.

## Recommendation

Use a 32-slide registered renderer with a mandatory directory, four section
dividers, three semantically distinct case studies, eight or more native
charts, decision/roadmap pages, closing, and four fact-bound appendices.

## Assumptions To Confirm

- Synthetic client facts are evaluation fixtures, not real commercial claims.
- The reference is an art-direction authority, not a source of facts.
- Portable rendering is sufficient for release; COM remains optional.
