# Phase 22 Context: Window-PPTX Baseline and Safety

**Milestone:** v5.0 Window-PPTX Verified Production Engine
**Status:** Active / Incomplete
**Started:** 2026-07-19

## User Intent

The requested outcome is not merely a better prompt for a top model. The `window-pptx` Skill must carry enough narrative, design, layout, rendering, and verification knowledge that an ordinary model can repeatedly produce an editable, client-delivery-quality PPTX.

The target workflow therefore moves open-ended decisions out of model improvisation and into:

- predefined business narrative archetypes;
- semantic content-to-page rules;
- governed themes, components, and layout variants;
- native PowerPoint rendering contracts;
- deterministic checks and bounded repair;
- weak-model benchmarks and real Windows acceptance.

## Phase Boundary

Phase 22 establishes the baseline and P0 safety boundary before any compiler, registry, renderer, or repair expansion. It covers only:

- strict dry-run and one-result routing;
- resolved source/output/staging guards;
- explicit PowerPoint COM ownership;
- macro-security disable/restore;
- terminal read-only add-in inspection;
- suffix and export-geometry preservation;
- candidate-first validation and atomic promotion;
- reproducible Linux/fake-COM and real Windows evidence.

Phase 22 does not claim the design system, 72-layout registry, semantic compiler, advanced editable objects, five-layer QA, benchmark, or final UAT are implemented.

## Locked Decisions

1. Models may provide semantic content and intent, but may not invent coordinates, raw colors, fonts, COM calls, or arbitrary code.
2. Native Windows PowerPoint remains the production renderer because customer deliverables must stay editable and PowerPoint-compatible.
3. Dry-run performs zero writes, network work, and COM dispatch.
4. Source decks are never implicitly overwritten. Output promotion is candidate-first and source integrity is checked before and after promotion.
5. Only a PowerPoint application proven to be created by the tool may be quit by cleanup.
6. Programmatic deck opens force macro disable and restore the captured automation-security value in `finally`.
7. The four historical template pages remain legacy/unverified and will not become automatic recommendations in v5.
8. v4.0 remains shipped history; v5.0 is active and cannot be called shipped until Phase 29 hard gates pass.

## Acceptance Posture

Linux unit tests and recording fakes prove Python-side control flow, invariants, and write ordering. They do not prove real COM registration, session isolation, Office Trust Center behavior, file locking, macro-enabled package handling, fonts, or PowerPoint reopen/editability. Those cases remain explicit Windows validation work.

## Sources of Truth

- Approved implementation plan: `docs/superpowers/plans/2026-07-19-window-pptx-v5.md`
- Phase requirement map: `.planning/REQUIREMENTS.md`
- Focused implementation/review reports: `.superpowers/sdd/task-1*-report.md` and `.superpowers/sdd/task-1*-review.md`
- Phase validation contract: `22-VALIDATION.md`
