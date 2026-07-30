# Phase 47 fresh independent evidence audit

Load `cli-agent-delegator` and `aimagician-superpower`, then return the audit
verdict without calling filesystem or shell tools. The controller already
reproduced the evidence below against the frozen review-worktree immediately
before this fresh context. The runtime independently fingerprints the
worktree before and after your response.

## Goals

- GOAL-47-01: fifteen locked realistic briefs with complete real-scenario
  truth, anatomy, material roles, prohibitions, and stable digests.
- GOAL-47-02: real ordinary-model run, exact facts once, 4-8 registered
  semantic groups, no visual/code/invention authority, unavailability explicit.
- GOAL-47-03: fifteen editable PPTX/manifests and portable complete render
  evidence, no package/external-link/note/raster failure.
- GOAL-47-04: fresh isolated visual AI finds no Blocker/Important and rejects
  mechanical one-layout recoloring.

## Reproduced evidence

- `verify_window_pptx_v6_scenario_suite.py` independently opened every final R7
  plan, brief, PPTX zip package, manifest, proof directory, and accepted raw
  review. Result:
  `PASS`, 15 scenarios, 292 portable pages, 15 strict visual passes, mean
  4.643, zero failures.
- Expected page counts all matched: 15/18/19 for the three flagships and 20
  for each of the other twelve. All 15 PPTX hashes matched their manifests.
- Each PPTX had `native_editable=true`,
  `whole_slide_rasterization=false`, complete notes, at least two native
  objects per slide, no external relationship, readable PDF proof, and exact
  slide PNG count.
- The twelve commercial decks had exactly four `section` and three `appendix`
  roles, twelve distinct scenario signatures, and four actual semantic
  families: comparison, matrix, metric-ledger, process.
- DeepSeek report:
  model `opencode/deepseek-v4-flash-free`, one attempted scenario,
  provider status `unavailable`, record status `UNAVAILABLE`, `NO_RESPONSE`;
  it is never presented as PASS.
- Fallback report:
  model `opencode/nemotron-3-ultra-free`, status PASS, 15 scenarios,
  15 passed, pass rate 1.0. Each accepted record has fact coverage 1.0 and
  4-8 groups. `evaluate_ordinary_plan` validates the BriefPlan schema against
  the FactStore and exact observed-vs-expected fact set; missing, duplicate,
  unknown, or unsupported content fails.
- Visual runner enumerates exactly 15 complete A/B/C groups and starts one
  separate direct `analyze.mjs` subprocess per deck. It saves raw provider
  JSON per deck; there is no shared reviewer conversation.
- Accepted deck scores:
  4.5, 4.8, 4.2, 4.8, 4.6, 4.8, 4.7, 4.6, 4.7, 4.8, 4.75, 4.8, 4.6, 4.5,
  4.5. Every selected payload has `reference_grade_craft=true`, status PASS,
  and zero Blocker/Important.
- Three R7 OCR/protocol false positives were not edited. The common review
  protocol was clarified, then each deck was sent through a new direct vision
  subprocess; the suite verifier records those new raw JSON paths. It rejects
  malformed JSON, status/score mismatch, reference-grade false, or any serious
  finding.
- Leakage scan operates only on visible OOXML `<a:t>` text and finds none of
  the internal evaluation strings. It does not confuse the standard PowerPoint
  `Slide Number Placeholder` shape name with customer-visible text.
- Regression reproduction:
  reference anchors + ordinary suite + weak-model generation pipeline +
  TemplatePack = `94 passed in 160.90s`.
- Controller observed the review worktree unchanged during generation,
  rendering, visual review, final verifier, and regression run. The audit
  runtime supplies its own before/after fingerprint gate.

## Decision

Assess goal coverage and whether the evidence exposes gaming, unsupported
claims, or unresolved delivery defects. Output a compact goal table, findings
as Blocker/Important/Nitpick, and verdict. Return `DONE` only if all four goals
are evidenced and there is zero Blocker/Important; otherwise `NEEDS_WORK`.
