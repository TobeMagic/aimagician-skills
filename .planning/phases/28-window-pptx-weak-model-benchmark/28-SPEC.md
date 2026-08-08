# Phase 28 Specification: Weak-Model Benchmark and Real Portable Trial Evidence

**Status:** Locked
**Risk:** high
**User-facing:** yes
**Requirements:** 5

## Goal

Measure whether the governed Window-PPTX Skill raises the quality and repeatability of ordinary-model output across the user's fifteen commercial presentation types, using real provider responses and real portable PPTX/PDF/PNG evidence. Keep deterministic scoring, human visual review, and sampled PowerPoint certification as separate gates.

## Background

The repository already contains a frozen fifteen-scenario corpus, three-arm protocol, two ordinary-model identities, two repeats, strict response ingestion, deterministic plan scoring, schemas, anonymized review contracts, and a 180-trial manifest. Phase 27.2 has now completed the PptxGenJS/OOXML/LibreOffice/Poppler delivery chain.

The benchmark `full-v5` evaluator now stages real portable PptxGenJS/OOXML/LibreOffice/Poppler/Quality-v2 artifacts. Three preserved real `opencode/deepseek-v4-flash-free` responses have been replayed against the latest source as noncanonical diagnostics. Their missing clean fingerprint, single-model coverage, and absent human reviews prevent formal aggregation; the second frozen model may remain unavailable.

## Requirements

### V5-BENCH-01: Frozen Commercial Scenario Coverage

**Current:** Fifteen scenario records and strict loaders/tests exist, but their formal release fingerprint predates the final Phase 27.2 engine and must be revalidated.

**Target:** Fifteen immutable, synthetic, license-safe scenario briefs cover business reporting, project proposals, product launches, market analysis, sales, investor pitches, annual reviews, strategy, data analysis, research, training, brand introductions, kickoffs, operations reviews, and e-commerce/marketing.

**Acceptance:** Every scenario has stable fact IDs, required/prohibited claims, narrative beats, expected archetype/forms, slide-count range, audience, language, asset condition, and canonical hashes. Corpus drift invalidates the run.

### V5-BENCH-02: Controlled Ordinary-Model Trial Matrix

**Current:** The three arms, two model identities, two repeats, prompt contracts, seeds, and 180 deterministic trial IDs exist. One model is currently confirmed available, and three of its real responses have latest-source full-v5 diagnostic artifacts; the complete controlled provider matrix has not run.

**Target:** Freeze three unequal-capability arms (`unassisted-json`, `governed-plan`, `full-v5`), two ordinary OpenCode model identities, two repeats, stable prompts, seeds, trial IDs, timeout policy, and a 180-trial manifest.

**Acceptance:** The harness invokes only the requested model identity and preserves provider events, stderr, metadata, exact response, response hash, prompt hash, and trial identity. Unavailable, timeout, invalid, failed, and evaluated are distinct; no response is fabricated or post-edited.

### V5-BENCH-03: Deterministic and Blind Human Evaluation

**Current:** Deterministic scorecard and blind-review schemas/packet helpers exist, but no post-27.2 completed human review set exists. The data-analysis diagnostic demonstrated that a high automatic composite can conceal a generated-plan numeric defect, so automated calibration must not substitute for blind review.

**Target:** Score response validity, fact retention, invention safety, compilation, archetype/semantic fit, capacity, rhythm, native editability, portable hard gates, artifact completeness, and repeat agreement. Stage anonymized PPTX/PNG review packets for human scoring without revealing arm or model identity.

**Acceptance:** Deterministic metrics reproduce from sealed artifacts. Completed human sheets validate against the frozen rubric and cannot be synthesized by the harness. Automated structure PASS is never treated as visual acceptance.

### V5-BENCH-04: Real Portable Full-v5 Evidence and Complete Fingerprints

**Current:** The benchmark evaluator uses the verified portable renderer and stages real PPTX/PDF/PNG/contact-sheet/OOXML/Quality-v2 evidence for full-v5 diagnostics. The worktree is dirty, no clean post-implementation benchmark fingerprint exists, and these one-model diagnostic artifacts are formally ineligible.

**Target:** For every evaluated `full-v5` response, run the canonical RenderPlan through PptxGenJS 4.0.1, deterministic OOXML normalization, RenderPlan-aware OOXML inspection, isolated LibreOffice/Poppler proof, Quality-v2, bounded repair, and atomic promotion. Stage PPTX, PDF, every page PNG, contact sheet, reports, repair log, manifests, and hashes.

**Acceptance:** Recording/fake-COM may test legacy adapters but is never credited as full-v5 delivery evidence. A formal run requires a clean, matching fingerprint bundle covering engine, registry, schema, Skill, corpus, protocol, prompts, thresholds, dependencies, model/provider, environment, fonts, assets, and portable runtime. Artifacts outside the governed trial root or with stale hashes are rejected.

### V5-BENCH-05: Honest Aggregation and Release Thresholds

**Current:** Aggregation, completeness gates, artifact digests, frozen thresholds, and an immutable formal run-contract schema exist. The latest three diagnostic summaries correctly report one of 180 trials, fingerprint missing, and release incomplete; the complete two-model/human-review aggregate is absent.

**Target:** Aggregate by arm, model, scenario, and repeat without imputing missing trials. Preserve frozen release thresholds and produce completeness, deltas, uncertainty/repeat evidence, visual review results, and a release status.

**Acceptance:** Formal Phase 28 closure requires the complete two-model matrix, hash-complete real portable artifacts, required human blind review, and every frozen threshold. Provider unavailability, dirty fingerprints, missing reviews, visual failure, or partial diagnostics leave Phase 28 incomplete and v5.0 NO_GO.

## Diagnostic Versus Formal Runs

A dirty-worktree or one-model subset may run as explicitly noncanonical diagnostic evidence so implementation and provider compatibility can be tested. It must:

- use a new evidence directory and preserve all raw provider output;
- state selected versus planned trials and never extrapolate to the 180-trial aggregate;
- carry `formal_benchmark_eligible=false` or an equivalent incomplete status;
- keep PowerPoint certification and human blind review `NOT_RUN`;
- never overwrite or merge with a formal clean-fingerprint run.

The first diagnostic target is a representative multi-scenario DeepSeek subset after the full-v5 portable artifact path is implemented and tested.

## Boundaries

### In Scope

- Post-27.2 corpus/protocol/schema/fingerprint revalidation.
- Real OpenCode ordinary-model execution and raw evidence preservation.
- Real portable full-v5 artifact generation and deterministic scoring.
- Partial diagnostic runs and the complete formal 180-trial contract.
- Anonymized review packet generation and validated human scores.
- Aggregate threshold and completeness reporting.

### Out Of Scope

- Fabricating a second model response when its provider is unavailable.
- Treating deterministic calibration as model execution.
- Crediting Recording-COM, HTML proofs, or slide screenshots as customer PPTX delivery.
- Automatically repairing model prose or editing raw responses after receipt.
- Treating LibreOffice rendering as Microsoft PowerPoint certification.
- Closing v5.0 before Phase 29's real PowerPoint sample and final audit.

## Constraints

- Immutable facts remain the sole authority; the ordinary model only selects allowed fact IDs and registered semantics in `full-v5`.
- The model never emits coordinates, fonts, colors, executable JavaScript, OOXML, HTML/CSS, COM code, or arbitrary templates.
- PptxGenJS/LibreOffice/Poppler execution must reuse Phase 27.2 capability, transaction, isolation, source-hash, and cleanup contracts.
- Full-v5 trials fail closed when portable artifacts or semantic checks fail; they do not fall back to COM.
- Thresholds, prompts, and model identities cannot be changed after results are observed.
- Dirty or partial runs are diagnostic only and cannot satisfy V5-BENCH-01..05.

## Acceptance Criteria

- [ ] V5-BENCH-01 corpus and scenario hash coverage pass.
- [ ] V5-BENCH-02 complete controlled provider matrix and raw-evidence preservation pass.
- [ ] V5-BENCH-03 deterministic scoring and completed blind human review pass.
- [ ] V5-BENCH-04 every available full-v5 trial has verified real portable artifacts under a clean complete fingerprint.
- [ ] V5-BENCH-05 complete non-imputed aggregation meets all frozen release thresholds.

## Known External Blockers

- The second ordinary model identity is not currently proven available.
- A clean post-27.2 commit/fingerprint is not yet available because the implementation worktree is intentionally dirty.
- Human blind review and Phase 29 PowerPoint sampling require later external execution.

These blockers do not prevent an explicitly noncanonical DeepSeek diagnostic subset, but they prevent Phase 28 closure.

## Blocking Questions

- None.

## Ambiguity Report

**Goal clarity:** 0.99
**Boundary clarity:** 0.98
**Constraint clarity:** 0.98
**Acceptance clarity:** 0.97
**Ambiguity:** 0.02

## Decision Log

- Preserve the 15 × 3 × 2 × 2 formal design and do not lower it after observing provider availability.
- Use `opencode/deepseek-v4-flash-free` now for diagnostic trials because the user confirmed it is available.
- Replace RecordingPresentation evidence in the `full-v5` benchmark path with real Phase 27.2 portable artifacts before crediting any full-v5 trial.
- Keep automated engineering, human visual quality, and PowerPoint compatibility as three separate verdicts.
- Keep partial/dirty evidence useful for debugging but ineligible for release aggregation.
