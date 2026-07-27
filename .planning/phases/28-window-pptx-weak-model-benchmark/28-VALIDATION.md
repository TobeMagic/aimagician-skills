# Phase 28 Validation: Weak-Model Benchmark

**Status:** Diagnostic implementation verified / Formal post-27.2 run incomplete / Release `NO_GO`

> **Rebaseline note (2026-07-21):** Fifteen scenarios, the 180-trial shape, schemas, a deterministic evaluator, a real portable full-v5 route, and three DeepSeek diagnostic scenarios now exist. The diagnostics use a dirty/missing fingerprint and one model, so they remain noncanonical until a clean two-model formal run and blind review are complete.

## Diagnostic Evidence

The raw responses originated from real `opencode/deepseek-v4-flash-free` calls. The named revisions below are deterministic latest-source replays of those preserved responses; they are useful implementation evidence, not additional formal provider trials.

| Scenario | Latest diagnostic | Automatic composite | Portable result | Diagnostic limits |
|---|---|---:|---|---|
| Business report | `window-pptx-v5-phase28-deepseek-business-visual-floor-replay-20260721-r12` | 98.75 | Evaluated; `Above Q1`, hard gate, native editability, fact and numeric safety all pass; decision closing is a native high-contrast action band; Quality-v2 weighted defects 0 | One of 180 trials; fingerprint missing; visual review still notes conservative/sparse pages |
| Product launch | `window-pptx-v5-phase28-deepseek-product-visual-floor-replay-20260721-r8` | 98.75 | Evaluated; exact `3 hours` to `35 minutes`, `40 customer teams`, compact integrations, editorial claim, compact milestone, and narrow accent rails preserved; Quality-v2 weighted defects 0 | One of 180 trials; fingerprint missing; licensed product/UI imagery remains absent and some pages remain sparse |
| Data analysis | `window-pptx-v5-phase28-deepseek-data-visual-floor-replay-20260721-r9` | 99.00 | Evaluated; `42,180 subscriptions`, contextual labels, narrow accent rails, native percentage chart with verified 0-100 axis/percent labels, and action closing preserved; Quality-v2 weighted defects 1 | One of 180 trials; fingerprint missing; missing time series correctly degrades to a statement, but methodology/annotation remains thin |

Each run summary records `run_kind=diagnostic`, `formal_benchmark_eligible=false`, `planned_trials=180`, `recorded_trials=1`, `fingerprint_status=missing`, and `release_status=incomplete`.

The repair-focused OpenCode review reused session `ses_07afb9f00ffecq2Y9LQJdzYPWC` with exact model `opencode/deepseek-v4-flash-free` and exited `0`: `DEFECTS=FIXED`, `CODE_DEFECTS=NONE_CRITICAL_OR_IMPORTANT`, `VISUAL=PARTIAL`, `PHASE28=NOT_COMPLETE`, `V5=NO_GO`. Independent decoded contact-sheet review agrees: the two targeted defects are fixed, but the three decks remain visually sparse and asset-light. Quality-v2 still lacks a generic oversized-accent geometry gate, so this residual mechanism risk remains open.

## Formal Run-Contract Hardening

- Formal mode now has a dedicated immutable run contract bound to the manifest and component fingerprint.
- Formal defaults require the complete 180-trial matrix; manifest-only, replay-only, and diagnostic-to-formal import paths are rejected.
- Resume is exact-contract only, and every trial metadata record is bound to the run-contract digest.
- These controls prove that an incomplete diagnostic cannot masquerade as a formal run; they do not prove that the formal run has occurred.

## Automatic-Score Blind Spot

The data-analysis first diagnostic scored highly even while a comma-separated value was reduced from `42,180` to `180` and contextual metric labels were weak. The regenerated semantic checks now catch generated-plan numeric/unit drift, and r9 fixes that case plus the missing percent-axis contract, but the incident proves that a high composite is not a human visual/customer-delivery verdict. Sparse pages, limited assets/UI imagery, analytical annotation, and industry specificity still require blind human review.

## Required Evidence

- [x] Fifteen frozen scenario briefs cover every required business presentation type.
- [x] Three frozen arms, two ordinary models, and two repeats produce a 180-trial manifest.
- [ ] Canonical hashes verify protocol, inputs, raw outputs, DeckPlans, reports, artifacts, reviews, and scorecards.
- [x] Missing, unavailable, invalid, and failed trials remain distinct and are never imputed.
- [x] Deterministic scoring validates facts, compilation, density, diversity, native/editable coverage, QA gates, and repeatability.
- [ ] Blind-review packets hide arm/model identity and completed reviews validate against a strict rubric schema.
- [ ] Aggregate scorecards show arm/model/scenario results, before/after deltas, completeness, and frozen threshold verdicts.
- [ ] Available ordinary-model trials and real governed PptxGenJS/OOXML/LibreOffice artifacts are reproducible; sampled PowerPoint certification is explicitly deferred to Phase 29.
- [ ] Focused and complete suites pass with no unresolved Critical or Important finding.

## Unfinished Hard Gates

- [ ] Execute the clean, immutable, complete 180-trial formal matrix.
- [ ] Execute the second frozen ordinary model (`opencode/nemotron-3-ultra-free`, or a formally refrozen replacement before the run).
- [ ] Seal a clean post-implementation component fingerprint.
- [ ] Complete anonymized human blind review; no automated score may substitute for it.
- [ ] Complete the frozen sampled read-only Microsoft PowerPoint certification in Phase 29.

## Verdict

`NO_GO`. Real DeepSeek responses now generate governed, editable PPTX/PDF/PNG evidence in three diagnostic scenarios, and the formal runner contract is fail-closed. Phase 28 remains `in progress`: the clean two-model 180-trial run, complete aggregation, blind human review, and sampled PowerPoint certification are `NOT_RUN`.
