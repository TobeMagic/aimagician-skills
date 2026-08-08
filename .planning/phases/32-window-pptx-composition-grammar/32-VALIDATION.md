# Phase 32 Validation: CompositionPlan and Reference-Grade Floor

**Status:** Implementation complete; reference-grade visual acceptance open
**Date:** 2026-07-28
**Engineering verdict:** `PASS`
**Art/release verdict:** `NO_GO`

## Delivered

- `CompositionPlan v1` with source/fact trace, registered layouts and exact
  slot bindings, density/emphasis/energy, motif, asset fallback, repair
  variants, and raw-geometry rejection.
- `consulting-executive` DesignPack v2 with a 12-column grid, type/spacing/
  surface tokens, warm-ivory/navy/teal/copper palette roles, four
  Knowledge-Wayfinding motifs, choreography, and quality thresholds.
- Source-bound 14-page consulting choreography with 10-day baseline, 5-day
  target, traceable `-50%`, four-step operating loop, four workstreams,
  five-stage/six-month delivery rail, governance, risk/action, three decision
  gates, and closing CTA.
- Direct Agnes Vision/Image provider adapters with explicit route authority,
  HTTPS, session-bound Data-URI probe, strict JSON, bounded normalization,
  cache/replay, redacted failures, and Base64 asset manifests.
- QualityReport v3 with six axes, four pass states, visual hard gates, R2
  migration, and at most two monotonic fact-protected CompositionPlan repairs.
- Portable renderer support for CompositionPlan metadata, editable
  Knowledge-Wayfinding art, process/timeline/matrix geometry, localized
  evidence tags, and OOXML verification of the new child geometry and alpha.

## Real artifacts

| Iteration | Engineering | Agnes art | PPTX SHA-256 | Outcome |
|---|---:|---:|---|---|
| R3 | PASS | 5/5 FAIL | `7101f97318500f2bd2825c6e8dbb6cfaf60c2556f6efddea84ed92e6401052f1` | First 14-page composition |
| R4 | PASS, v2 defect 155 | FAIL; deck axes `68/59/62/55/57/60` | `670d3057131d7168b73aac980a5e5c79b4ea94966aeeac5ed45fd8cbc067d117` | Fixed slots, hierarchy, evidence tags |
| R5 | PASS, v2 defect 2 | not final-reviewed | `9877f1a1ec1e83fe15a82887c92fe2bc72a8319e796dcb6ea649bb5e0c9d4611` | Content-scale and CTA repair |
| R6 | PASS, v2 defect 2 | FAIL; deck axes `68/72/75/60/65/70` | `299bcc03eaddb7ee2919e01e305e3cb3cb8792c929e343b5133aa0243a3bd32b` | Final fact-trace and vector-art calibration |

Final local paths:

- `.planning/evidence/phase32-consulting-tracer-r6/output/consulting-proposal-r6.pptx`
- `.planning/evidence/phase32-consulting-tracer-r6/contact-sheet.png`
- `.planning/evidence/phase32-consulting-tracer-r6/.window-pptx/audits/composition-plan.json`
- `.planning/evidence/phase32-consulting-tracer-r6/.window-pptx/audits/agnes-review-r6.json`
- `.planning/evidence/phase32-consulting-tracer-r6/.window-pptx/audits/quality-report.v3.json`

R6 contains 14 slides, eight layout signatures, 15.0 average editable/visual
objects, seven native editable diagrams, and required-fact coverage `1.0`.
Deterministic OOXML semantic inspection and isolated LibreOffice/Ghostscript
proof both passed. The final external-score-capped Quality v3 result is
`68.33`, `engineering_passed=true`, `visual_passed=false`,
`art_review_status=FAIL`, and `release_passed=false`.

## Before/after

R2/R3 depended on generic page-family resolution and faint decorative object
counts. R6 now has an executable composition contract, exact slot
materialization, ten-to-five-to-minus-fifty evidence hierarchy, numbered
process/governance/decision structures, visible teal/copper wayfinding rails,
stronger section stages, localized evidence tags, and a direct pixel-review
loop.

The result is materially more stable and editable, but it still does not match
the authorized work-summary reference's image-led art direction, oversized
typographic compositions, dense data storytelling, and page-specific visual
anchors. The final Agnes review also produced contact-sheet-scale false
positives: the visible `BUILD / WHAT` label was reported as misspelled and the
three visible decision labels on slide 13 were reported missing. Those claims
were rejected instead of triggering invented content. The lower business-
evidence and rhythm scores remain useful signals, but Agnes findings require
local pixel/fact verification before repair.

## Verification completed

```text
Composition/DesignPack/Agnes/Quality focused tests: 30 passed
Portable and composition focused tests: 60 passed, 6 skipped
Portable regression subset: 53 passed, 6 skipped
Agnes adapter tests: 8 passed
PptxGenJS native semantic deterministic test: 1 passed
Complete Window-PPTX suite: 711 passed, 9 skipped
Root Vitest: 108 passed
TypeScript typecheck: PASS
Repository build: PASS
Skillbird format check: 23 checked, 0 issues
Phase 32 workflow trace: 7/7 requirements PASS
PptxGenJS worker doctor: protocol 1.0, backend 4.0.1, Node v20.19.2
R6 OOXML semantic validation: PASS
R6 LibreOffice PDF/Ghostscript PNG proof: PASS
R6 QualityReport v2 hard gates: PASS
Direct Agnes Data-URI probe and final deck review: completed, verdict FAIL
OpenCode Agnes independent code review ses_05b3687dcffe9ljse434fHSYOA:
implementation PASS, 0 Critical, 0 Important, 3 Minor
```

## Requirement evidence

| Requirement | Status | Evidence | Observed |
|---|---|---|---|
| P32-COMP-01 | PASS | CompositionPlan schema/models/compiler seam and focused tests | Exact registered slots materialize into the 14-page RenderPlan |
| P32-DESIGN-01 | PASS | consulting DesignPack v2, Knowledge-Wayfinding editable motif, R6 proof | Pack contract is deterministic; final art review remains FAIL |
| P32-NARRATIVE-01 | PASS | R6 narrative/composition manifests and required-fact coverage | 14 pages, coverage 1.0, traceable 10→5→-50% |
| P32-ASSET-01 | PASS | R6 asset plan and native fallback bindings | Every required intent is native-materialized; generated hero media is still a next-phase gap |
| P32-AGNES-01 | PASS | direct Data-URI probe, R4/R6 review JSON, adapter tests | Route/caching/redaction/schema boundary works; R6 verdict is FAIL |
| P32-QA-01 | PASS | QualityReport v3 schema, R2 rejection tests, R6 external-capped report | Four pass states work; R6 release_passed=false |
| P32-REPAIR-01 | PASS | monotonic/fact-drift/repeated-candidate repair tests | Two-round cap and rollback invariants pass |

The independent review's three Minor observations are accepted tracer
constraints rather than release blockers: the `-50%` derived-fact binding,
conservative fixed R2 migration scores, and frozen tracer numbering. The
review explicitly distinguishes implementation `PASS` from visual/release
`NO_GO`.

## Remaining gaps and next plan

1. Materialize optional Agnes/ModelScope hero/background assets into
   AssetPlan/RenderPlan rather than stopping at provider capability.
2. Add a licensed/reference-derived visual anchor library: editorial photos,
   lighthouse/portal equivalents, icon families, data-viz callouts, and
   page-specific crops.
3. Add composition-specific visual variants beyond registry geometry:
   asymmetric data stories, oversized typography, image-led covers/sections,
   colored chart panels, and authored connector systems.
4. Calibrate Agnes against frozen reference/R2/R6 sets; its R6 score regressed
   despite verified fixes, so automatic score stability is not yet proven.
5. Add human blind review (`>=4.2/5`, no axis `<4`) before reference-grade
   release.
6. Run Phase 33 multi-scenario rollout only after the consulting art floor is
   accepted; do not copy current vector treatment to all scenarios.

No default-branch merge or reference-grade claim is authorized by this
validation.
