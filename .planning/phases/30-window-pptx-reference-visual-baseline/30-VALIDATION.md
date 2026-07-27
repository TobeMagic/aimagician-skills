# Phase 30 Validation

**Status:** PARTIAL PASS
**Date:** 2026-07-27

## Accepted evidence

- Authorized TemplatePack source SHA-256:
  `59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839`.
- The registered pack exposes 220 shape slots and 36 chart/workbook slots.
- No-op adaptation is byte-identical.
- Full adaptation changes only the 15 declared slide parts, four chart parts,
  and four embedded workbooks.
- Reference-grade r10 renders through LibreOffice 25.2.3.2 and Ghostscript
  10.05.1 without COM. Candidate hash remains stable before and after proof.
- r10 has 15 slides, 56.467 average objects per slide, 12 layout signatures,
  4 editable charts, 4 embedded workbooks, 29 media assets, 114 groups, and
  335 decorative primitives.
- The source-domain residual scan is empty.
- A TemplatePack compatibility rule clamps individual display-title characters
  to 92 pt and switches them to a portable East Asian fallback, preventing
  missing calligraphic fonts from producing whole-slide overlaps.
- The generated route now compiles a deterministic editable art-direction
  layer and rejects decks below object-density, composition-variation, or
  rich-slide coverage floors.
- Reviewer routing now prefers Agnes for pixel-level UAT only after an explicit
  image-attachment capability probe. DeepSeek is reserved for code and
  contract auditing and is forbidden as a visual fallback.

## Primary deliverable

- `.planning/evidence/v5.1-reference-grade-work-summary-r10/output/window-pptx-v5.1-reference-grade-work-summary-r10.pptx`
- `.planning/evidence/v5.1-reference-grade-work-summary-r10/output/window-pptx-v5.1-reference-grade-work-summary-r10.pdf`
- `.planning/evidence/v5.1-reference-grade-work-summary-r10/contact-sheet.png`

## Remaining gates

- A quantitative non-slot visual-similarity metric is not yet implemented.
- The four DeepSeek diagnostic trials completed technically, but the generated
  DesignPack-only contact sheets remain below the supplied reference's visual
  bar. They are not accepted as customer-grade evidence.
- Blind human review and the formal benchmark remain pending.
- OpenCode 1.17.6 currently exposes `agnes/agnes-2.0-flash`, but the
  2026-07-27 PNG-attachment probe reported that the model does not support
  image input. The Agnes visual verdict is therefore `NOT_RUN`, not a pass or
  fail. A provider/model with verified image input or a human reviewer is still
  required.
- Native PowerPoint sampling remains optional and `NOT_RUN`; COM is not a
  blocker for the portable TemplatePack deliverable.
