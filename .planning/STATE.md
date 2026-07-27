---
gsd_state_version: 1.0
milestone: v5.1
milestone_name: Window-PPTX Reference-Grade Visual Engine
current_phase: 32
current_phase_name: Composition Grammar and Generated Reference Floor
status: in_progress
stopped_at: Phase 31 engineering proof complete; Phase 32 consulting tracer r2 passes engineering gates but remains below reference-grade visual acceptance
last_updated: "2026-07-27T23:00:00+08:00"
last_activity: 2026-07-27
progress:
  total_phases: 37
  completed_phases: 28
  total_plans: 34
  completed_plans: 31
  percent: 76
---

# Project State

## Project Reference

See: `.planning/ROADMAP.md`
See: `.planning/REQUIREMENTS.md`
See: `README.md`

**Core value:** Skillbird manages owned skills as the default source of truth, while external skill repositories remain disabled references unless explicitly enabled.

**Current focus:** v5.1 Phase 31 now has source-derived trusted masks,
same-renderer non-slot similarity, a one-command golden replay, and two
byte-identical 15-slide candidates. The minimum page similarity is `0.9968`
outside masks. Phase 32 has started with a real 12-slide Chinese consulting
proposal grammar tracer; r2 passes portable gates and improves structured
editable density, but manual contact-sheet review remains
`PARTIAL_NOT_REFERENCE_GRADE`. PowerPoint is optional sampled certification,
not a daily hard dependency.

## Current Position

Milestone: v5.0 Window-PPTX Verified Production Engine
Current Phase: 28 (v5 phase 9 of 10)
Current Phase Name: Window-PPTX Weak-Model Benchmark
Status: In Progress (current milestone 7/10 phases complete)
Last Activity: 2026-07-21

Foundation completed:

- package identity renamed to `aimagician_superpower`;
- daily CLI command renamed to `skillbird`;
- config paths moved to `skillbird` / `.skillbird`;
- global state path moved to `aimagician-superpower`;
- external catalog sources default to disabled;
- six-category taxonomy introduced;
- `skillbird format-skills --check|--write` implemented;
- search/install selectors added for category, subcategory, and tags;
- first consolidated owned skills added:
  - `aimagician-superpower`
  - `skill-creator`
  - `mcp-builder`
  - `interface-design`
  - `webapp-testing`
- document skills `docx`, `pdf`, `pptx`, `xlsx` are owned and categorized;
- README and planning docs updated for the new workflow.
- Phase 19 deep merge audit completed:
  - GSD state machine remains canonical;
  - Superpowers planning/writing quality gates are folded into `aimagician-superpower`;
  - `code-guidelines` execution discipline is folded into `aimagician-superpower`;
  - merged skill regression coverage added.
- Phase 20 Skillbird UX acceptance completed:
  - PTY smoke asserts Skillbird launch;
  - dashboard source acceptance binds category styling text;
  - category bundle preview/apply covered for global and project scopes.
- Phase 21 install acceptance completed:
  - isolated global home install preview/apply verifies core workflow skills;
  - isolated project install preview/apply verifies document bundle.

Active v5 foundation:

- Phase 22 is complete with 105 focused Python tests and two consecutive native Windows PowerPoint runs against the final reviewed code passing 13/13 cases;
- the Windows matrix proves strict dry-run, pre-COM output guards, COM ownership, macro-security restoration, registry-only add-in inspection, transactional PPTX/PPTM/PDF behavior, dynamic export geometry, source hashes, and cleanup;
- Phase 23 is complete with a strict DeckPlan v1 schema, 15 business archetypes, semantic/chart mapping, density-aware lossless splitting, dominant multi-block semantics, rhythm control, and explainable low-confidence fallback;
- Phase 24 is complete with 8 themes, 24 families, 72 variants, 582/582 service paths, governed grid/type/color/spacing/effects, deterministic brand/font behavior, safe asset policy, runtime registry gates, and legacy quarantine;
- Phase 25 is complete with a pure governed render plan, native editable text/shape/image output, deterministic master/footer/group/z-order behavior, strict asset evidence, COM preflight, recording fake COM, transactional saving, 45 focused tests, 357 full tests, and final OpenCode PASS;
- Phase 26 is complete with native editable charts/tables, six deterministic diagram families, notes, safe links, opt-in motion, ratio-aware PNG/PDF routes, 28 focused tests, 385 full tests, and final OpenCode PASS;
- Phase 27 is complete with stable five-layer reports, fail-closed native-object fidelity checks, hard delivery gates, bounded exception-safe repair, atomic audit artifacts, 19 focused tests, and 404 full tests.
- Phase 27.1 local implementation adds immutable FactStore-to-BriefPlan-to-NarrativePlan authority, 12 deterministic art directions, six-color BrandSpec/font/asset/pattern gates with provenance hashes, passive governed SVG assets, pre-save quality report v2, canonical content-safe repair, orchestration-observed post-save candidate reinspection, progressive weak-model guidance, six deterministic calibration packets, typed component fingerprints, and a threshold/artifact/PPTX-PNG-blind-review-gated 180-trial contract. The complete Window-PPTX suite passes 505 tests; actual PowerPoint and ordinary-model evidence are still absent.
- Phase 27.2 is complete with backend-neutral RenderPlan execution, PptxGenJS 4.0.1 native OOXML generation, deterministic packaging, semantic OOXML inspection, isolated LibreOffice/Poppler rendering, proof-only HTML, optional safe PowerPoint certification, and six 6/6 portable calibration packets across 56 pages.
- Phase 27.2 manual review remains `FAIL_CUSTOMER_DELIVERY_VISUAL_BAR`: empty frames, orphan agendas, and generic headings were fixed, but asset coverage, content-to-visual mapping, analytical annotation, training pedagogy, and industry differentiation remain below the senior-designer target.
- Phase 28 is active. Preserved real DeepSeek responses now regenerate real editable portable artifacts for business-report r12 (98.75), product-launch r8 (98.75), and data-analysis r9 (99.00); all three latest diagnostics pass portable hard gates and generated-plan numeric safety, but each is one of 180, fingerprint-missing, formally ineligible, and release-incomplete.
- The latest visual-floor iteration preserves the source-grounded `Above Q1` relative label, makes plain claims editorial rather than quotation-like, caps three label-only cards at 1.88 inches, converts one-event timelines into compact native milestone bands, replaces large empty accent panels with governed narrow rails, emits high-contrast decision/action bands, verifies native percentage axes/labels, and searches same-family capacity-safe variants before generic fallback.
- Phase 28's formal runner now requires an immutable contract bound to the complete manifest and clean fingerprint, exact-contract resume, and per-trial contract digests; it rejects partial, manifest-only, replay-only, and diagnostic-to-formal promotion paths.
- The data-analysis iteration exposed an automatic-score blind spot: a high early score coexisted with `42,180` being reduced to `180`. The latest r9 fixes that defect and the missing percentage-axis contract, but automatic scoring remains separate from blind human customer-delivery review.

## Decisions

- [Phase 14]: No `skillbee` compatibility command is retained or documented.
- [Phase 14]: Project scope uses `<project>/.skillbird`.
- [Phase 14]: Global state uses `~/.local/state/aimagician-superpower`.
- [Phase 15]: External sources are reference material by default, not installers.
- [Phase 16]: GSD remains the workflow state machine backbone.
- [Phase 16]: Superpowers process gates are merged into `aimagician-superpower`, not installed as separate default skills.
- [Phase 16]: `code-guidelines` execution discipline is folded into `aimagician-superpower`.
- [Phase 17]: Categories are `build`, `research`, `design`, `documents`, `operate`, and `strategy`.
- [Phase 17]: Bundles are derived from taxonomy selectors instead of a separate bundle file.
- [Phase 19]: GSD planning artifacts and Superpowers plan-writing checks are merged into `aimagician-superpower`.
- [Phase 19]: Source noise such as external installers, update hooks, and community commands remains excluded.
- [Phase 20]: `install --dry-run` is supported for previewing category bundle installs.
- [Phase 21]: Non-interactive acceptance uses isolated `--home` and `--project` paths to avoid mutating live CLI homes.
- [Phase 22]: A model may emit semantic intent, but v5 owns coordinates, typography, colors, capacity, and repair decisions in deterministic rules and registries.
- [Phase 22]: Source decks are protected by resolved-path and hash checks; deliverables are promoted only from validated candidates.
- [Phase 22]: The unsafe OpenCode suggestion to expose a `--legacy-v4` bypass was rejected; compatibility must not bypass v5 safety gates.
- [Phase 22]: Add-in inventory and plugin probing are registry-only terminal routes because live enumeration can load third-party code and block unattended PowerPoint.
- [Phase 22]: Native Windows acceptance must pass twice consecutively with disposable Chinese/space paths and no process residue before a phase can close.
- [Phase 23]: Publicly constructed DeckPlan models are normalized and revalidated before compilation; typed models are not a validation bypass.
- [Phase 23]: Every page-form decision records its dominant semantic block, top candidates, rule IDs, confidence, and fallback reason.
- [Phase 23]: Mixed text/items split without duplication or loss, and every part obeys both item-count and density-unit limits.
- [Phase 24]: Layout margins remain absolute at 0.5in/0.4in across supported page sizes; gutters derive from the 8pt spacing system.
- [Phase 24]: Runtime registry caches fail closed when loaders, readers, files, or owning-module registry paths change.
- [Phase 24]: Asset kinds and styles are normalized before policy checks so case or whitespace cannot bypass raster-resolution gates.
- [Phase 25]: Public render plans are exact-bound back to selected registry slots, component rules, themes, font inventory, and governed asset evidence before COM mutation.
- [Phase 25]: Governed rendering deletes template slides and unmanaged master shapes; template geometry may inform page size but cannot leak uncontrolled visual content.
- [Phase 25]: DeckPlan, output, template, slide-size, route, and asset-manifest preflight complete before PowerPoint dispatch; the CLI compiles model input exactly once.
- [Phase 26]: Advanced chart, table, and diagram commands are re-derived from canonical semantic blocks; grouped diagram hyperlinks are applied to editable child shapes and chart gaps never invent zeroes.
- [Phase 26]: Motion is off by default, only two governed presets are allowed, and every advanced COM failure stops before candidate saving.
- [Phase 27]: Repair may change only registered candidate page size, geometry, fonts, names, and tags; it is capped at two passes, keeps rename last, and rolls back any non-monotonic or exception-raising pass.
- [Phase 27]: Native chart/table/diagram data and transaction evidence fail closed, while pre/post-save hard-gate errors atomically persist their report and repair log.
- [Phase 27.1]: Huashu is a pinned method reference only; no runtime, prompts, named styles, media, fonts, or HTML conversion code are imported.
- [Phase 27.1]: The default ordinary-model route controls only fact IDs and registered semantic hints; immutable facts and deterministic registries own prose, narrative, art direction, layout, and repair.
- [Phase 27.1]: A complete benchmark cannot advance to human review without a clean, post-Huashu, internally matching fingerprint; provider-unavailable trials and dirty calibration are never imputed as success.
- [Phase 27.1]: Human blind scoring is rejected until hash-verified readable OOXML PPTX and PNG evidence is staged under anonymized review paths.
- [Phase 27.2]: DeckPlan and RenderPlan remain canonical; governed `auto` generation uses PptxGenJS, while COM remains an explicit legacy and sampled-certification adapter.
- [Phase 27.2]: Portable customer delivery fails closed on OOXML semantic checks, isolated LibreOffice PDF/PNG rendering, and Quality-v2; it does not fall back silently to COM or raster slides.
- [Phase 27.2]: HTML is a deterministic RenderPlan-derived proof and QA view only, never the canonical PPTX intermediate or model-authored layout surface.
- [Phase 27.2]: Portable diagrams use editable child shapes plus stable logical-group metadata. Native grouping, motion, SmartArt, physical template import, and macro-enabled output remain capability-gated COM routes.
- [Phase 27.2]: PowerPoint certification is read-only and sampled. It never rewrites the portable canonical artifact, never kills an unowned process, and never performs automatic registry repair.
- [Phase 27.2]: Portable engineering PASS and manual visual acceptance are separate verdicts. The phase requirements pass on 6/6 deterministic real-artifact packets, while the v5 milestone remains blocked by the explicit manual visual failure and later blind review.
- [Phase 28]: Real-response dirty-worktree diagnostics may validate provider integration, portable generation, and rule fixes, but cannot enter the formal aggregate or change the release verdict.
- [Phase 28]: Formal mode is an immutable 180-trial contract tied to a clean fingerprint; exact resume is allowed, while partial selection, replay/manifest-only operation, and diagnostic import fail closed.
- [Phase 28]: Automatic composites are engineering signals, not visual acceptance. Blind human review remains mandatory after the score blind spot observed in the first data-analysis diagnostic.

## Next Actions

1. Obtain an actual independent Phase 31 code/contract verdict after the
   DeepSeek free route stops rate-limiting or another scoped reviewer works.
2. Continue Phase 32 from recipe seeds to recipe-owned component compositions,
   cover anchors, evidence annotations, and empty-diagram rejection.
3. Regenerate the consulting tracer until manual contact-sheet review reaches
   the reference-grade bar.
4. Expand to the remaining three UAT scenarios only after the first lane
   passes; then refreeze the two-model benchmark.

## Blockers / Concerns

- Actual live current-user CLI homes were not mutated during automated acceptance. The same global path logic was verified through an isolated `--home` after `install --dry-run`.
- Phase 22 startup is slow on this host because installed PowerPoint add-ins load during real COM sessions; safety inspection therefore remains registry-only.
- v5.0 is active and unshipped. Portable QA is complete, but manual customer visual acceptance failed; visual remediation, the formal benchmark, blind review, and final cross-engine UAT remain required.
- Microsoft `MSPPT.OLB` and late-bound PowerPoint automation work, but early-bound pywin32 `_Application.QueryInterface` fails with `TYPE_E_CANTLOADLIBRARY` because the interface registry points to a stale, missing WPS TypeLib. This does not block portable delivery; it remains a sampled-certification concern.
- OpenCode `opencode/deepseek-v4-flash-free` completed read-only session `ses_07d23c7d0ffetnEwNzbfy0zA2b`. Its findings were independently checked and some inaccurate capability claims were rejected; it is research evidence, not the final post-implementation `V5-UAT-04` audit.
- Phase 27.2 OpenCode 1.17.6 re-audit session `ses_07c11cc8bffe8HmjcQX73B1We4` confirmed portable engineering PASS, customer visual FAIL, release NO_GO, reconciled planning state, 602/602 regression, and present V5-PORT-07 evidence. It remains Phase 27.2 review evidence; Phase 29 owns the final post-benchmark `V5-UAT-04` audit.
- Phase 28 repair-focused OpenCode session `ses_07afb9f00ffecq2Y9LQJdzYPWC` on `opencode/deepseek-v4-flash-free` confirmed both targeted defects fixed and no Critical/Important code defect, while retaining `VISUAL=PARTIAL`, `PHASE28=NOT_COMPLETE`, and `V5=NO_GO`; it is diagnostic review, not the Phase 29 final audit.
- The second frozen benchmark model remains unavailable/unreliable, so the complete 180-trial comparison and human blind review are still `NOT_RUN`.
- OpenCode 1.17.6 exposes `agnes/agnes-2.0-flash`, but the 2026-07-27
  attachment probe explicitly rejected image input. Reviewer routing therefore
  fails closed: Agnes visual UAT remains `NOT_RUN`, DeepSeek cannot substitute
  for pixel judgment, and only a successfully probed vision model or human
  reviewer may close the visual gate.
- The Phase 31 post-implementation DeepSeek review was attempted again on
  2026-07-27 and both title/main streams returned explicit rate-limit errors.
  An earlier Agnes planning review loaded all required skills but looped
  without a verdict. No independent approval is claimed.
- Phase 28's three latest DeepSeek visual-floor diagnostics (business r12, product r8, data r9) are deliberately noncanonical: no clean component fingerprint exists, only one model and one full-v5 trial per scenario are represented, and automatic composites do not satisfy customer visual review.
- Phase 29 sampled PowerPoint certification is `NOT_RUN`; the stale WPS TypeLib that breaks early-bound COM does not block portable daily delivery but remains relevant to that sample.
