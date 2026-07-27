# Phase 28 Discussion Log: Weak-Model Benchmark

**Status:** Diagnostic implementation verified; formal benchmark and release remain open
**Date:** 2026-07-21

## User Inputs

- The target is not merely good output from a top model; ordinary models must benefit from Skill-owned planning, templates, design rules, and repair.
- Multiple commercial PPT types and actual generated PPTX files must be tested rather than stopping at an architecture report.
- `opencode/deepseek-v4-flash-free` is currently available and should be used.
- COM necessity, coverage, HTML-to-PPT alternatives, other libraries, and remaining blockers must be evaluated honestly.
- Continue implementation rather than only proposing work.

## Decisions

1. Phase 27.2 closes the portable engineering foundation, not the v5 visual/release milestone.
2. Phase 28 retains the 180-trial formal design; no threshold or model count is weakened because one provider is currently unavailable.
3. DeepSeek runs now as real but explicitly noncanonical diagnostic evidence because the worktree is dirty and the second model/human review are missing.
4. The existing benchmark `full-v5` RecordingPresentation path must be replaced with real portable artifacts before any full-v5 trial receives delivery credit.
5. The benchmark reuses Phase 27.2 PptxGenJS, deterministic OOXML, semantic inspection, isolated LibreOffice/Poppler, Quality-v2, and transaction code instead of forking a benchmark-only renderer.
6. Automated structure PASS, customer visual PASS, and real PowerPoint certification remain distinct results.
7. HTML stays proof-only. Common editable objects use PptxGenJS/OOXML; COM remains an explicit legacy capability route and a sampled read-only Phase 29 certifier.
8. Provider timeout/unavailability, invalid JSON, portable failure, missing review, and dirty fingerprint remain explicit states; nothing is imputed.

## Assumptions

- DeepSeek remains callable for at least a bounded diagnostic subset.
- Phase 27.2 portable contracts are reusable without weakening their transaction or source-integrity gates.
- The current dirty worktree is acceptable only for diagnostic evidence and will be replaced by a clean fingerprint before formal aggregation.
- Human reviewers and Windows PowerPoint access are later external inputs, not simulated capabilities.

## Rejected Options

- Running the current RecordingPresentation path and calling it full-v5 delivery evidence.
- Converting arbitrary model-authored HTML into slide screenshots or canonical PPTX pages.
- Reducing the formal matrix to one model or weakening thresholds after provider failures.
- Fabricating unavailable responses, reviews, or PowerPoint results.
- Creating a second portable renderer inside the benchmark instead of reusing Phase 27.2.

## Deferred Work

- Availability of the second frozen ordinary model.
- A clean post-implementation component fingerprint.
- Completed blind human reviews.
- Phase 29 real Microsoft PowerPoint sample and final audit.

None of these is inferred as PASS during the DeepSeek diagnostic subset.

## 2026-07-21 Implementation Update

- The full-v5 benchmark path now stages real governed PptxGenJS PPTX, semantic OOXML inspection, LibreOffice PDF/PNG proofs, contact sheets, Quality-v2, repair logs, manifests, and hashes; RecordingPresentation no longer receives customer-delivery credit.
- Real DeepSeek responses were preserved for business-report, product-launch, and data-analysis scenarios, then deterministically replayed against the latest source as business r12, product r8, and data r9.
- The latest diagnostics score 98.75, 98.75, and 99.00 respectively and pass portable hard gates, but every summary is explicitly `diagnostic`, `formal_benchmark_eligible=false`, fingerprint `missing`, and release `incomplete`.
- Exact value/unit binding, thousands separators, explicit parallel-list extraction, contextual metric labels, categorical chart routing, native editability accounting, portable font fallback, and safer sparse-page rhythm were strengthened in response to observed failures.
- The first data-analysis score exposed an automatic-score blind spot: a high score coexisted with `42,180` being reduced to `180`. Generated-plan numeric safety was extended and the latest r9 fixes the defect plus the missing percentage-axis contract, but human visual review remains mandatory.
- The formal runner now writes an immutable run contract tied to the manifest and clean fingerprint, requires all 180 trials, binds trial metadata to the contract digest, allows only exact resume, and rejects replay/manifest-only/diagnostic imports in formal mode.

## 2026-07-21 Visual-Floor and COM Update

- Ordinary statements are separated from quotations, three short authored labels select a compact 1.88-inch tile recipe, and one-node timeline/roadmap content renders as a compact left-aligned native milestone band.
- Closing objectives use governed Chinese/English decision-versus-action titles and high-contrast native action bands; no hyperlink means no fake button semantics.
- Shared-percent charts preserve authored category order and carry a fail-closed native 0-100 axis, 20-point major ticks, `Percent` title, and literal percent label formats through PptxGenJS, COM, and OOXML inspection.
- A seeded text composition that misses capacity now searches serviceable same-family variants and prefers the highest safe type scale before generic fallback. The product diagnostic caught and verified this regression path.
- The first final OpenCode visual audit caught a generic `Measure 2` metric label and large empty accent panels. Source-present relative qualifiers now produce labels such as `Above Q1`, and statement/KPI/CTA accents are constrained to narrow registered rails; business r12, product r8, and data r9 preserve the original responses while verifying the fixes.
- The three latest root/trial inventories contain 212 SHA-256/size entries and were independently recomputed with zero mismatches.
- Final related Python regression passes 317/317 on the last weak-model/layout source; the earlier full-suite baseline passes 668/668. Root typecheck/build pass, and the final Vitest run passes 108/108 after managed-source installation excludes local `node_modules`/Python bytecode and the full-package smoke budget is aligned with its measured 3650-file package operation.
- Repair-focused OpenCode session `ses_07afb9f00ffecq2Y9LQJdzYPWC` on exact `opencode/deepseek-v4-flash-free` exits 0 with `DEFECTS=FIXED`, no Critical/Important code defect, `VISUAL=PARTIAL`, `PHASE28=NOT_COMPLETE`, and `V5=NO_GO`. Independent contact-sheet review agrees; a generic oversized-accent Quality-v2 geometry gate remains future work.
- `TYPE_E_CANTLOADLIBRARY (0x80029C4A)` is attributed to a stale WPS TypeLib reference on the PowerPoint `_Application` interface path. Microsoft `MSPPT.OLB` and late-bound `IDispatch` work; the doctor remains read-only and performs no registry repair.
- COM is retained only for physical template/macro/template-output/animation/native-grouping capability lanes and sampled PowerPoint fidelity certification. It is not required for daily generation and cannot guarantee every internal PowerPoint feature.
- HTML remains a deterministic proof view, not a canonical PPTX intermediate. PptxGenJS plus OOXML inspection and LibreOffice/Poppler proof remains the default; python-pptx, Open XML SDK/direct PresentationML, LibreOffice UNO, and licensed Aspose are documented as bounded alternatives rather than silent fallbacks.

## Current Gate Decision

Phase 28 stays `in progress` and v5.0 stays `NO_GO`. The formal 180-trial run, second model/Nemotron, clean fingerprint, blind review, and Phase 29 sampled PowerPoint certification remain unexecuted.
