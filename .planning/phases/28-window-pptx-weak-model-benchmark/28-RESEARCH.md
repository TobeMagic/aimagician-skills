# Phase 28 Research: Controlled PPTX Skill Evaluation

> **Rebaseline note (2026-07-21):** The experimental design remains 15 scenarios × 3 arms × 2 frozen ordinary models × 2 repeats. The `full-v5` renderer/verifier fingerprint and evidence contract must be regenerated after Phase 27.2; all earlier manifests are noncanonical for release comparison.

## Objective

Determine how to execute the frozen ordinary-model experiment without confusing deterministic Skill calibration, Recording-COM plans, portable customer artifacts, human visual acceptance, or sampled PowerPoint compatibility.

## Local Evidence

- `scenarios.json` already contains all fifteen requested commercial types with stable fact IDs, prohibited claims, beats, expected forms, and slide ranges.
- `protocol.json` already freezes three arms, two ordinary model IDs, two repeats, prompt contracts, scoring weights, and release thresholds; `build_trial_manifest()` deterministically produces 180 identities.
- `run_window_pptx_benchmark.py` preserves prompts, OpenCode events/stderr/metadata, exact responses, derived plans, hashes, and scorecards and distinguishes unavailable/invalid/failed/evaluated states.
- `benchmark.py` now routes `full-v5` diagnostics through the Phase 27.2 portable renderer and stages real native PPTX/PDF/PNG/contact-sheet/OOXML/Quality-v2 evidence; RecordingPresentation remains regression-only and receives no delivery credit.
- Phase 27.2 now provides the reusable real path: PptxGenJS backend negotiation, deterministic normalization, exact OOXML inspection, isolated LibreOffice/Poppler rendering, Quality-v2, source-integrity checks, transaction promotion, contact sheets, and artifact inventories.
- `opencode/deepseek-v4-flash-free` is live and completed the Phase 27.2 read-only audit. `opencode/nemotron-3-ultra-free` is frozen in the protocol but is not currently proven available.
- The repository worktree is dirty by design, so any immediate model run is diagnostic and cannot satisfy the formal clean-fingerprint aggregate.

## Options

| Option | Benefit | Failure mode | Decision |
|---|---|---|---|
| Run the existing benchmark unchanged | Fast provider signal | Mislabels Recording-COM plans as full-v5 delivery evidence | Reject for full-v5 credit |
| Render HTML or slide screenshots after model output | Easy visual packet | Breaks native editability and canonical PPTX contract | Reject |
| Add a second benchmark-only portable renderer | Isolated code | Duplicates Phase 27.2 safety logic and will drift | Reject |
| Reuse Phase 27.2 portable execution from the benchmark runner | Real native artifacts with existing gates | Requires artifact/schema/score integration and slower trials | Accept |
| Wait for a clean worktree and both providers before any run | Formal purity | Delays detection of provider/prompt/integration failures | Reject for diagnostics; require for formal closure |

## Recommendation

The portable orchestration layer and diagnostic/formal separation are implemented and have generated three real-response DeepSeek diagnostics. Next seal a clean component fingerprint, execute the immutable complete 180-trial contract with both frozen models, and complete blind review. Preserve the diagnostic evidence for failure analysis only, and leave Phase 28 open until those formal gates pass.

The diagnostic loop also established an evaluation warning: automatic composites can overstate correctness when semantic parsing itself is incomplete. The first data-analysis result scored highly despite losing the thousands component in `42,180`; generated-plan numeric checks were extended and the latest replay fixes it, but blind visual/content review remains a separate required gate.

## Experimental Unit

One trial is the immutable tuple `(benchmark_version, scenario_id, arm_id, model_id, repeat_index)`. Its identifier and seed derive from canonical JSON so reruns cannot silently change grouping or randomization.

## Arms

1. `unassisted-json`: a minimal output contract with no archetype, mapping, design-registry, or QA guidance. Invalid or non-JSON output is a measured failure, not repaired by the harness.
2. `governed-plan`: the model receives the strict DeckPlan contract, scenario-safe structure choices, and weak-model step sequence; deterministic compilation is evaluated, but candidate QA/repair is not credited.
3. `full-v5`: the same governed planning input continues through registry-bound RenderPlan, PptxGenJS native-object rendering, deterministic OOXML normalization and semantic inspection, isolated LibreOffice/Poppler proof rendering, Quality-v2, bounded repair, and transaction evidence. Fake-COM and optional PowerPoint certification are not credited as daily delivery artifacts.

The prompt prefix, scenario brief, model identity, repeat count, and token budget remain frozen within an arm. Provider metadata is recorded rather than normalized away.

## Scenario Coverage

The corpus covers business reporting, project proposal, product launch, market analysis, sales proposal, investor pitch, annual review, strategic planning, data analysis, research report, training, brand introduction, project kickoff, operations retrospective, and e-commerce/marketing planning.

Each scenario contains an audience, decision objective, required narrative beats, key facts with stable fact IDs, prohibited inventions, expected archetype, expected semantic forms, slide-count range, language, and asset availability. Content is synthetic and license-safe.

## Scoring

Deterministic scores include response validity, DeckPlan validity, fact retention, prohibited-claim violations, compile success, capacity/splitting compliance, family/layout diversity, OOXML-native/editable coverage, portable hard-gate pass, artifact completeness, and repeat agreement. A missing output receives no imputed score.

Blind human review uses anonymized trial labels and a stable rubric: narrative clarity, content accuracy, visual hierarchy, layout fitness/variety, readability, chart/diagram appropriateness, brand consistency, editability, and customer-delivery readiness. Reviewers must not see arm or model identity.

## Release Thresholds

- all 15 scenarios represented in the frozen corpus;
- 100% manifest/hash verification for recorded artifacts;
- at least 95% full-v5 DeckPlan validity and compile success across available trials;
- at least 95% full-v5 customer hard-gate pass after repair on real portable PptxGenJS/OOXML/LibreOffice evidence;
- at least 95% fact retention with zero prohibited numeric invention in release candidates;
- full-v5 deterministic composite at least 15 points above unassisted and 8 above governed-plan;
- full-v5 customer-delivery human score at least 4.0/5 and at least 0.5 above unassisted;
- repeat standard deviation no greater than 0.35/5 for customer-delivery review;
- no unresolved Critical or Important audit finding.

Provider unavailability does not lower thresholds; it leaves the benchmark incomplete.

PowerPoint is not required for every Phase 28 trial. Phase 29 freezes a 10% sample plus every high-risk capability sample and requires those artifacts to open read-only without repair prompts, export the expected page count and ratio, pass Quality-v2 Critical gates, and leave no unowned process residue.

## Assumptions To Confirm

- DeepSeek remains callable for the diagnostic subset long enough to preserve real responses; provider rate limits remain an observed status rather than a reason to fabricate output.
- The second frozen model may be unavailable; this blocks formal completeness but not diagnostic implementation testing.
- A clean post-implementation commit/fingerprint will be created before the formal run; the current dirty fingerprint is intentionally ineligible.
- Human reviewers and a Windows PowerPoint sample are external Phase 28/29 inputs and remain `NOT_RUN` until actually executed.
