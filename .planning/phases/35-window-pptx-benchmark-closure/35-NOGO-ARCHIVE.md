# Phase 35 NO_GO Archive Checkpoint

**Recorded:** 2026-07-29
**Disposition:** `NO_GO` / superseded by the v6.0 quality reset
**Archive branch:** `archive/window-pptx-v5.1-no-go-20260729`
**Original v5 branch checkpoint:** `feat/window-pptx-v5@70d1b6762acdbe0732a502e8d1e151f3957323eb`

## Why This State Is Archived

The current v5.1 worktree contains useful portable rendering, composition,
asset-materialization, Quality v3, and blind-review infrastructure, but its
generated decks do not meet the user's accepted reference-grade visual bar.
The user explicitly replaced the unfinished human-review release path with a
new v6.0 quality-first milestone. This checkpoint preserves the exact v5.1
work without declaring Phase 35 complete or advancing `feat/window-pptx-v5`.

## Fresh Baseline

- Python collection: `792` tests.
- Python result after running the suite in filesystem-safe shards:
  `789 passed`, `3 failed`.
- Vitest: `108 passed`.
- TypeScript typecheck: PASS.
- TypeScript build: PASS.
- Skillbird formatter check: `23` skills checked, no issues.
- `git diff --check`: PASS.
- Private/credential path inventory: no `.private`, cookie, credential,
  password, token, or secret path found in the changed/untracked scope.

The first monolithic Python run exceeded the command timeout on the
Windows-mounted filesystem. The suite was then completed in smaller shards;
the slow benchmark file passed `42/42` in 725.57 seconds.

## Known Failing Tests

1. `test_generation_binds_materialized_cover_to_image_led_layout`
   - `cta.decision-three` leaves multiple governed text slots unfilled.
2. `test_prose_only_trend_gets_editable_directional_motif_without_fake_data`
   - The test expects `BASELINE`; the implementation emits `START`.
3. `test_real_training_and_ecommerce_packets_pass_quality_gates`
   - Only one of the two calibration packets passes the current quality gate.

These failures are part of the archived `NO_GO` state. They must be repaired
and reverified on the v6 branch; they must not be rewritten as historical
passes.

## Archive Contract

- The archive commit and annotated tag preserve this worktree and this
  baseline report.
- `feat/window-pptx-v5` remains at the original checkpoint above.
- No archive artifact authorizes release, default-branch merge, or a claim
  that v5.1 reached the reference-grade target.
