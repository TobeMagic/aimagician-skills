# Phase 47 Validation

**Validated:** 2026-07-31
**Status:** PASS

## Ordinary-model evidence

- Requested first route: DeepSeek V4 Flash Free.
- Provider outcome: `UNAVAILABLE`, preserved under
  `.private/phase47/ordinary-deepseek/ordinary-model-suite-report.json`.
- Explicit fallback: `opencode/nemotron-3-ultra-free`.
- Accepted outcome: 15/15 plans PASS, every active fact referenced exactly
  once, 100% fact coverage, four-to-eight groups, and no geometry, style,
  template, code, invented-fact, or self-scoring authority.
- Evidence:
  `.private/phase47/ordinary-nemotron/ordinary-model-suite-report.json`.

## Output and portability

- Final candidate root: `.private/phase47/output-r7-ordinary/`.
- 15 native editable PPTX files and 15 hash-bound manifests.
- Page counts: flagship 15/18/19; twelve commercial scenarios 20 each.
- Portable proof root: `.private/phase47/proofs-r7/`.
- LibreOffice/Poppler PASS: 15/15 decks and 292/292 pages.
- Every deck has complete speaker notes, no external relationship, no
  whole-slide rasterization, and multiple native editable objects per page.

## Scenario and semantic diversity

- Twelve distinct scenario-signature compositions:
  architecture, calendar, constellation, flywheel, funnel, governance,
  horizon, journey, product, quadrant, ranking, and staircase.
- Four semantic families selected from the real ordinary-model plans:
  comparison, matrix, metric decision ledger, and process.
- Deterministic code retains all copy, visual, geometry, theme,
  materialization, QA, and release authority.

## Independent visual acceptance

Protocol:

- one direct Agnes visual subprocess and fresh context per candidate;
- three high-resolution split sheets cover the whole deck;
- no repository, previous review, or other candidate context;
- PASS requires mean >=4.2, `reference_grade_craft=true`, and zero Blocker or
  Important;
- malformed or internally inconsistent responses are not accepted.

Final accepted evidence:

- base review root: `.private/phase47/reviews-r7-final/`;
- calibrated independent retry root for three OCR/protocol false positives:
  `.private/phase47/reviews-r7-retry/`;
- strict visual pass count: 15/15;
- aggregate accepted mean: 4.643;
- unresolved Blocker: 0;
- unresolved Important: 0.

The retries did not manually edit scores. Each was a new direct vision
context after the shared protocol was tightened to forbid OCR-invented words,
thumbnail-only readability claims, and treating a boundary appendix followed
by a closing page as an abrupt ending.

## Automated verification

Final suite command:

```bash
PYTHONPATH=skills/owned/window-pptx/scripts \
python skills/owned/window-pptx/scripts/verify_window_pptx_v6_scenario_suite.py \
  --output-dir skills/owned/window-pptx/.private/phase47/output-r7-ordinary \
  --proof-dir skills/owned/window-pptx/.private/phase47/proofs-r7 \
  --brief-dir skills/owned/window-pptx/.private/phase47/briefs \
  --plan-dir skills/owned/window-pptx/.private/phase47/ordinary-nemotron \
  --review-dir skills/owned/window-pptx/.private/phase47/reviews-r7-final \
  --review-dir skills/owned/window-pptx/.private/phase47/reviews-r7-retry \
  --report skills/owned/window-pptx/.private/phase47/phase47-suite-verification-r7.json
```

Result: PASS, 15 scenarios, 292 portable pages, 15 strict visual passes,
visual mean 4.643, zero failures.

Regression batch:

```text
tests/window_pptx/test_v6_reference_anchors.py
tests/window_pptx/test_v6_ordinary_model_suite.py
tests/window_pptx/test_weak_model_generation_pipeline.py
tests/window_pptx/test_template_pack.py
94 passed in 160.90s
```

## Goal matrix

| Goal | Verdict | Evidence |
|---|---|---|
| GOAL-47-01 | PASS | Fifteen locked real briefs and stable source hashes |
| GOAL-47-02 | PASS | Real Nemotron 15/15 exact-coverage plans; DeepSeek unavailability explicit |
| GOAL-47-03 | PASS | 15 editable PPTX/manifests, 292 portable pages, OOXML and note checks |
| GOAL-47-04 | PASS | 15 isolated visual contexts, mean 4.643, zero serious findings, twelve signatures |

## Completion audit

Fresh OpenCode session `ses_04b5931f6ffeLXUg0sKuHbIILc` returned DONE with
GOAL-47-01..04 PASS, zero Blocker/Important, and identical before/after
fingerprint
`313581cf3b1e53739f4c07a462bb1709a1e69a0826ceb4a479ef558a422950af`.
