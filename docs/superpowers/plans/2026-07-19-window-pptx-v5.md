# Window-PPTX v5.0 Verified Production Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `window-pptx` from a production handbook plus helper script into a deterministic, Windows-first presentation compiler that lets ordinary models create editable, client-delivery-quality PowerPoint decks.

**Architecture:** Models emit a versioned semantic `DeckPlan` JSON document and never invent coordinates, fonts, or colors. A pure-Python compiler selects narrative archetypes, layouts, components, themes, and content splitting rules; a transactional PowerPoint COM renderer builds editable slides; a five-layer validator and bounded repair loop gate delivery. The current script remains a compatibility facade for one milestone.

**Tech Stack:** Python 3.10+ standard library, optional `jsonschema`, Windows PowerPoint COM through pywin32, pytest/unittest-compatible tests, native PowerPoint PNG/PDF export, JSON registries.

## Global Constraints

- Scope is `skills/owned/window-pptx` plus its focused tests and v5 planning artifacts; the sibling `skills/owned/pptx` remains unchanged.
- Native Windows PowerPoint is the production renderer. Pure planning, schema, rules, registries, snapshots, and repair decisions must be testable on Linux without COM.
- Models may choose semantic roles and content blocks but may not supply raw coordinates, font sizes, colors, COM calls, or arbitrary code.
- Canonical runtime registries are JSON. The existing XLSX library is a derived human-review artifact, not runtime truth.
- Existing four template pages remain present but are marked `legacy_unverified` and excluded from automatic recommendation.
- Every one of 24 page families has at least three deterministic variants, for at least 72 layouts total.
- Initial themes are `executive-light`, `executive-dark`, `technology`, `finance-investor`, `marketing-vibrant`, `ecommerce-editorial`, `education-training`, and `public-enterprise`.
- Default geometry uses a 12-column grid, 0.5-inch horizontal and 0.4-inch vertical safe margins on 16:9, proportional scaling for custom sizes, and an 8pt spacing scale.
- Body text is at least 16pt; table, chart-label, and footnote text is at least 11pt; text below 10pt is a hard error.
- `--dry-run` performs zero writes. `--no-output-deck` may write explicitly requested reports but never a presentation.
- Source decks are never overwritten implicitly. COM sessions quit only applications proven to be owned by the tool.
- Macros are disabled during programmatic open and the previous PowerPoint automation-security setting is restored in `finally`.
- Auto-repair runs against candidate copies for at most two iterations and accepts a candidate only when weighted defects decrease without hard-gate regression.
- Hard gates require zero blockers and zero errors, successful package/COM open-save-reopen, unchanged source hash, expected editable text coverage of at least 99%, native expected chart/table coverage of 100%, and no full-slide rasterization.

---

### Task 1: Phase 22 milestone, baseline, and P0 safety foundation

**Files:**
- Modify: `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/MILESTONES.md`, `.planning/PROJECT.md`
- Create: `.planning/phases/22-window-pptx-baseline-and-safety/*`
- Create: `skills/owned/window-pptx/scripts/window_pptx/{__init__,errors,models,output_policy,com_session,cli}.py`
- Modify: `skills/owned/window-pptx/scripts/window_pptx_automation.py`
- Create: `tests/window_pptx/test_phase22_safety.py`

**Interfaces:**
- `PowerPointHandle(app: Any, owned: bool, dispatch_mode: str, cleanup_errors: list[str])`
- `OutputPolicy(source_path: Path | None, output_path: Path | None, dry_run: bool, no_output_deck: bool, allow_overwrite: bool)`
- `validate_output_policy(policy: OutputPolicy) -> None`
- `dispatch_powerpoint(attach_existing: bool, client: Any | None = None) -> PowerPointHandle`
- `macro_security(app: Any, force_disable: int = 3) -> ContextManager[None]`
- `calculate_export_size(page_width: float, page_height: float, target_long_edge: int = 1600) -> tuple[int, int]`

- [ ] Write tests proving source overwrite rejection, extension preservation, read-only add-in routing, one JSON payload, aspect-ratio export sizing, owned-instance cleanup, attached-instance preservation, fallback ownership, macro-security restoration, and strict dry-run zero writes.
- [ ] Run `python3 -m pytest tests/window_pptx/test_phase22_safety.py -q` and confirm failures are caused by missing interfaces.
- [ ] Implement the focused package and turn the current script into a compatible facade without changing legacy flag names.
- [ ] Run the focused test file, Python compilation, `--help`, and existing TypeScript typecheck/build/test suite.
- [ ] Record baseline commands, OpenCode session metadata, known PTY EPIPE flake, and Phase 22 validation evidence.
- [ ] Commit as `feat(window-pptx): establish v5 safety foundation`.

### Task 2: Phase 23 DeckPlan v1, archetypes, and semantic rule compiler

**Files:**
- Create: `skills/owned/window-pptx/schemas/deck-plan.v1.schema.json`
- Create: `skills/owned/window-pptx/registries/archetypes.json`
- Create: `skills/owned/window-pptx/scripts/window_pptx/{deck_plan,registry,rules,capacity}.py`
- Create: `tests/window_pptx/test_deck_plan_rules.py`
- Create: `.planning/phases/23-window-pptx-deck-plan-and-rules/*`

**Interfaces:**
- `load_deck_plan(path: Path) -> DeckPlan`
- `validate_deck_plan(document: Mapping[str, Any]) -> list[PlanIssue]`
- `compile_deck_plan(plan: DeckPlan, registries: RegistrySet) -> CompiledDeck`
- `rank_layout_candidates(slide: SlidePlan, context: SelectionContext) -> list[LayoutCandidate]`
- `split_content(slide: SlidePlan, capacity: CapacityRule) -> list[SlidePlan]`

- [ ] Add failing tests for all 15 archetypes, schema rejection, deterministic tie-breaking, top-three decision traces, low-confidence fallback, semantic mapping, capacity splitting, sparse-content preservation, and cross-slide rhythm.
- [ ] Implement the versioned models, registry loader, 15 archetypes, semantic rules, and exact capacity limits from the global constraints.
- [ ] Emit `decision-trace.json` with rule IDs, scores, selected candidate, rejected candidates, confidence, and fallback reason.
- [ ] Run focused tests and schema self-validation, then commit as `feat(window-pptx): add declarative deck compiler`.

### Task 3: Phase 24 themes, components, layouts, and asset policy

**Files:**
- Create: `skills/owned/window-pptx/registries/{themes,components,layouts,legacy-templates}.json`
- Create: `skills/owned/window-pptx/scripts/window_pptx/{themes,layouts,assets}.py`
- Create: `tests/window_pptx/test_design_registries.py`
- Create: `.planning/phases/24-window-pptx-design-system/*`

**Interfaces:**
- `resolve_theme(theme_id: str, brand: BrandOverrides | None, fonts: set[str]) -> ResolvedTheme`
- `resolve_layout(layout_id: str, slide_size: SlideSize) -> ResolvedLayout`
- `validate_registry_bundle(bundle: RegistrySet) -> list[RegistryIssue]`
- `choose_asset(intent: AssetIntent, manifest: AssetManifest) -> AssetChoice`

- [ ] Add failing tests asserting eight themes, 24 families, at least three variants per family, unique stable IDs, valid fallbacks, normalized geometry, safe margins, font minima, contrast tokens, crop-not-stretch policy, provenance requirements, and legacy quarantine.
- [ ] Implement 72 or more original layout definitions and reusable text, card, KPI, image, icon, chart, table, process, timeline, matrix, footer, and decoration components.
- [ ] Implement deterministic brand overrides and font fallback with explicit reporting.
- [ ] Run registry tests plus JSON parsing over every registry and commit as `feat(window-pptx): add deterministic design system`.

### Task 4: Phase 25 transactional core renderer and CLI

**Files:**
- Create: `skills/owned/window-pptx/scripts/window_pptx/{renderer,geometry,text,images,masters,project}.py`
- Extend: `skills/owned/window-pptx/scripts/window_pptx/cli.py`
- Modify: `skills/owned/window-pptx/scripts/window_pptx_automation.py`
- Update: `skills/owned/window-pptx/templates/{REQUEST,MODULES}.md`
- Create: `tests/window_pptx/test_renderer_core.py`
- Create: `.planning/phases/25-window-pptx-core-renderer/*`

**Interfaces:**
- `render_deck(compiled: CompiledDeck, session: PowerPointHandle, output: OutputPolicy) -> RenderResult`
- `render_slide(slide: CompiledSlide, presentation: Any, context: RenderContext) -> SlideRenderResult`
- `save_candidate(presentation: Any, policy: OutputPolicy) -> CandidateResult`
- CLI subcommands: `doctor`, `project init`, `plan validate`, `render`, `inspect`, `repair`, `roundtrip`, `benchmark`, `addins list`, `addins probe`.

- [ ] Add failing Linux tests using recording fakes for shape order, geometry scaling, text styling, image crop, grouping, master/footer creation, candidate-save sequence, and legacy flag translation.
- [ ] Implement the core renderer and a generated project runner that validates and renders a DeckPlan instead of printing a placeholder.
- [ ] Preserve 16:9, 4:3, and custom sizes without fixed coordinates or export distortion.
- [ ] Run focused tests and a fake-COM end-to-end render, then commit as `feat(window-pptx): add transactional core renderer`.

### Task 5: Phase 26 advanced editable objects

**Files:**
- Create: `skills/owned/window-pptx/scripts/window_pptx/{charts,tables,diagrams,notes,motion,exports}.py`
- Create: `tests/window_pptx/test_advanced_objects.py`
- Create: `.planning/phases/26-window-pptx-advanced-objects/*`

**Interfaces:**
- `render_chart(spec: ChartSpec, slide: Any, context: RenderContext) -> ShapeRef`
- `render_table(spec: TableSpec, slide: Any, context: RenderContext) -> ShapeRef`
- `render_diagram(spec: DiagramSpec, slide: Any, context: RenderContext) -> list[ShapeRef]`
- `apply_notes(slide: Any, notes: str) -> None`
- `apply_motion(slide: Any, motion: MotionSpec) -> list[EffectRef]`

- [ ] Add failing recording-COM tests for native chart workbook population, editable tables, flows, timelines, matrices, quadrants, funnels, roadmaps, notes, links, controlled animation presets, and page-ratio-aware PNG/PDF export.
- [ ] Implement native objects without rasterizing editable content; keep animation off unless explicitly requested.
- [ ] Run focused tests and commit as `feat(window-pptx): render advanced editable objects`.

### Task 6: Phase 27 five-layer QA and bounded repair

**Files:**
- Create: `skills/owned/window-pptx/schemas/validation-report.v1.schema.json`
- Create: `skills/owned/window-pptx/scripts/window_pptx/{snapshot,package_qa,com_qa,visual_qa,deck_qa,repair}.py`
- Create: `tests/window_pptx/test_qa_and_repair.py`
- Create: `.planning/phases/27-window-pptx-quality-and-repair/*`

**Interfaces:**
- `inspect_package(path: Path) -> DeckSnapshot`
- `inspect_com(presentation: Any) -> DeckSnapshot`
- `validate_deck(snapshot: DeckSnapshot, profile: QualityProfile) -> ValidationReport`
- `plan_repairs(report: ValidationReport, plan: DeckPlan) -> list[RepairAction]`
- `repair_candidate(source: Path, actions: Sequence[RepairAction], max_iterations: int = 2) -> RepairResult`

- [ ] Add failing tests for package integrity, relationships, text overflow, off-canvas shapes, overlap allowlists, alignment, margins, density, font availability, contrast, image deformation, chart labels, repeated layouts, placeholders, editability, hard gates, candidate-copy isolation, defect monotonicity, and idempotent second repair.
- [ ] Implement five QA layers and safe repairs only; unsafe operations remain human-review issues and fail customer-delivery gates.
- [ ] Produce stable `validation-report.json` and `repair-log.json` documents that validate against their schemas.
- [ ] Run focused tests and commit as `feat(window-pptx): add quality gates and repair loop`.

### Task 7: Phase 28 benchmark fixtures and before/after evaluation

**Files:**
- Create: `skills/owned/window-pptx/benchmarks/{manifest,tasks,expected,scorecards}/**`
- Create: `skills/owned/window-pptx/scripts/window_pptx/benchmark.py`
- Create: `tests/window_pptx/test_benchmark_contract.py`
- Create: `.planning/phases/28-window-pptx-weak-model-benchmark/*`

**Interfaces:**
- `load_benchmark_manifest(path: Path) -> BenchmarkManifest`
- `run_benchmark(manifest: BenchmarkManifest, arm: str, model: str, repeats: int) -> BenchmarkResult`
- `score_delivery(result: BenchmarkResult) -> DeliveryScore`

- [ ] Add failing tests for 15 scenario coverage, three frozen arms, exact model IDs, deterministic input hashes, repeat counts, hidden expectations, score aggregation, artifact hashes, and release-threshold evaluation.
- [ ] Add 15 original briefs and expected semantic assertions; mark five stress cases for three repeats across two ordinary models and three arms.
- [ ] Implement a harness that can prepare prompts, capture DeckPlans, run the compiler, and aggregate deterministic and blinded-review scores without embedding credentials.
- [ ] Run the contract tests and at least one local dry-run preparation for every task, then commit as `test(window-pptx): add weak-model benchmark`.

### Task 8: Phase 29 Windows UAT, documentation, audit, and milestone closure

**Files:**
- Rewrite: `skills/owned/window-pptx/SKILL.md`
- Update: `skills/owned/window-pptx/references/**`
- Create: `.planning/phases/29-window-pptx-acceptance-and-closure/*`
- Create: `.planning/milestones/v5.0-MILESTONE-AUDIT.md`
- Update: `.planning/{STATE,ROADMAP,REQUIREMENTS,MILESTONES,PROJECT}.md`

- [ ] Run full Python tests, TypeScript typecheck/build/tests, formatter checks, skill content regression tests, all JSON schema/registry checks, CLI smoke tests, and package integrity checks.
- [ ] Run real Windows PowerPoint UAT for isolated and attached sessions, Chinese/space paths, 16:9/4:3/custom sizes, `.pptx/.pptm`, missing font/add-in cases, source locking, reopen/edit sentinels, and ten consecutive runs.
- [ ] Generate canonical outputs for all 15 scenarios, contact sheets, reports, and before/after scorecards; perform the agreed blind human final review.
- [ ] Ask OpenCode for a final strict read-only audit and independently verify every critical claim.
- [ ] Rewrite the Skill around the compiler workflow, weak-model mode, design rules, QA loop, failure handling, and output contract while keeping progressive disclosure through references.
- [ ] Close only when all hard gates pass; otherwise leave v5 active and record exact blocked requirements.
- [ ] Commit as `docs(window-pptx): close verified v5 milestone` only after verification evidence is fresh.

## Recovery And Rollback

- Each task is a separate commit and cannot start until its focused tests and review pass.
- Real COM work always uses disposable test projects and candidate outputs; source fixtures are immutable and checked by SHA-256.
- If a task invalidates an earlier public interface, update the plan and all dependent tasks before editing further.
- If Windows UAT is unavailable, Phase 29 remains active and v5.0 must not be marked shipped.
