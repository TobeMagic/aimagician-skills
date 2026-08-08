# Phase 31 Validation: Trusted Visual Preservation and Golden Replay

**Status:** Engineering complete; independent reviewer unavailable
**Date:** 2026-07-27
**Release verdict:** `NO_GO` (Phase 32+ and visual review remain open)

## Implemented

- Source-only OOXML geometry inventory for nested groups, rotations, flips, and
  relationship-resolved chart frames.
- Manifest-carried masks that the loader recomputes from the authorized
  source and rejects on any mismatch.
- Same-renderer PNG comparison outside trusted masks with the frozen
  `0.98 / 0.02 / 8 / 0.80` profile.
- Read-only inventory CLI and one-command golden replay CLI.
- Compact schemas for inventory, similarity, and golden replay.
- Two-run reproducibility proof for the institutional 15-slide candidate.

## Fresh evidence

Golden command:

```bash
python skills/owned/window-pptx/scripts/run_window_pptx_golden_replay.py \
  --template-pack institutional-work-summary-v1 \
  --bindings skills/owned/window-pptx/evals/v5.1-work-summary-bindings.json \
  --output-dir .planning/evidence/phase31-golden-replay-a
```

The same command was repeated in `phase31-golden-replay-b`.

- source SHA-256:
  `59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839`
- candidate SHA-256, both runs:
  `32f3cd10ced049ec055143f6034a3126f10d3fbaa204870a49f3708e4a663382`
- candidate bytes: identical
- compact manifest bytes: identical
- renderer:
  `LibreOffice 25.2.3.2 520(Build:2) + Ghostscript 10.05.1 @ 144dpi`
- minimum page similarity outside masks: `0.996825819`
- maximum changed-pixel ratio outside masks: `0.004855397`
- maximum mask coverage: `0.725517940`
- reference-grade complexity:
  `56.467` average objects, `12` layout signatures, `4` charts, `29` media
- source and candidate hashes unchanged across proof rendering

Focused tests:

```text
17 passed in 17.77s
92 passed in 20.27s
695 passed, 9 skipped in 817.68s
```

The full suite includes portable rendering, OOXML, template adaptation,
quality, and regression coverage.

## Reviewer routing

- `opencode/deepseek-v4-flash-free` returned explicit rate-limit errors in
  both the title and main streams on two attempts.
- `agnes/agnes-2.0-flash` loaded all three required skills during the planning
  review but looped through repository discovery without producing a verdict;
  the run was terminated.
- A second scoped Agnes code-audit run inspected the Phase 31/32 propagation
  paths and corrected its own suspected `BriefGeneration` field finding, but
  again did not produce the required final verdict after ten minutes; it was
  terminated to avoid further repository I/O contention.
- No independent approval is claimed. The engineering evidence is complete,
  but the Phase 31 independent-review checkbox remains open until a provider
  returns an actual scoped verdict.

## Honest boundary

Masked similarity proves that declared edits did not materially disturb
rendered pixels outside trusted editable regions under one portable renderer.
It does not prove native PowerPoint pixel identity or customer visual approval.
