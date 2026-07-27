# Phase 28 Context: Weak-Model Benchmark

> **Rebaseline note (2026-07-21):** The accepted Phase 27.2 architecture changes the full-v5 execution arm from COM/fake-COM delivery evidence to real PptxGenJS + OOXML + LibreOffice + Quality-v2 evidence. Existing manifests and partial provider runs are preserved as pre-27.2/noncanonical and must not be aggregated into the formal verdict.

## Purpose

Measure whether the governed v5 Skill raises ordinary-model delivery quality and repeatability instead of merely demonstrating that a strong model can make a good deck.

## Implementation Decisions

- Preserve the formal 15 scenarios × 3 arms × 2 ordinary models × 2 repeats matrix and frozen release thresholds.
- Use the user-confirmed `opencode/deepseek-v4-flash-free` provider for an immediate diagnostic subset; never fabricate or substitute the unavailable second model.
- Benchmark `full-v5` delivery credit now requires real Phase 27.2 PptxGenJS/OOXML/LibreOffice/Poppler artifacts; RecordingPresentation remains regression-only.
- Separate three verdicts: portable engineering, human customer visual quality, and sampled real-PowerPoint compatibility.
- Permit dirty/partial diagnostic evidence only when it is explicitly noncanonical and excluded from release aggregation.

## Existing Patterns To Preserve

- Immutable FactStore authority and strict BriefPlan/DeckPlan schemas.
- Stable scenario, trial, prompt, seed, arm, model, and repeat identities.
- Exact provider event/response preservation with no post-editing.
- Deterministic scorecards, explicit unavailable/invalid/failed states, and no imputation.
- Phase 27.2 capability negotiation, candidate-only mutation, deterministic package normalization, exact OOXML inspection, isolated renderer profiles, source-hash protection, Quality-v2, and atomic evidence.
- Anonymous human-review packets that do not reveal arm/model identity.

## Allowed Scope

- Benchmark runner/evaluator/artifact/schema/fingerprint changes required for real portable full-v5 trials.
- Focused tests, model diagnostics, deterministic score aggregation, blind-review packet generation, and Phase 28 planning/evidence records.
- New noncanonical evidence directories for provider diagnostics.

## Forbidden Scope

- Lowering thresholds, changing frozen facts after observing results, or silently shrinking the formal matrix.
- Synthetic provider responses, post-edited JSON, invented human scores, or inferred PowerPoint evidence.
- Recording-COM, HTML proof, or slide screenshots credited as editable customer PPTX output.
- Automatic Office/WPS registry repair, unowned process termination, or mandatory daily COM.

## Integration And Compatibility

- Existing response-only and governed-plan scoring/report readers remain compatible.
- Full-v5 adds portable artifact digests and verification without changing raw model response contracts.
- Earlier pre-27.2 manifests remain readable but carry noncanonical engine/fingerprint status.
- Phase 29 consumes a frozen sample from the final Phase 28 packet and never rewrites canonical portable PPTX files.

## Frozen Scope

- Fifteen commercial presentation types named by the user become versioned scenario briefs.
- Three arms isolate unassisted prompting, governed planning, and the complete v5 compile/render/QA workflow.
- Two ordinary OpenCode-accessible model identities run two repeats per scenario and arm: 180 planned trials.
- Deterministic scoring and anonymized human review remain separate and are joined only after both are frozen.
- Every input, response, plan, report, artifact, and scorecard is SHA-256 addressed.

## Safety and Honesty

- The harness never fabricates model responses, PowerPoint output, human ratings, or PASS results.
- Missing/unavailable provider runs remain explicit trial statuses and count against completeness.
- Source facts are frozen and outputs must not silently invent metrics, dates, customers, or claims.
- Recording/fake-COM evidence remains useful only for legacy COM adapter regression and never substitutes for portable customer-delivery artifacts or Phase 29's sampled PowerPoint certification.

## Completion Boundary

Phase 28 may close only when the corpus, post-27.2 protocol, schemas, scoring, blind-review packet, real portable artifacts, and executable evidence are reproducible from a clean matching fingerprint. Release readiness still requires final human review, the final read-only audit, and sampled PowerPoint certification in Phase 29.
