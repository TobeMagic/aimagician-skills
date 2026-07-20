---
gsd_state_version: 1.0
milestone: v5.0
milestone_name: Window-PPTX Verified Production Engine
current_phase: 27
current_phase_name: Window-PPTX Quality Gates and Repair
status: in_progress
stopped_at: Phase 26 advanced objects passed 28 focused and 385 full tests plus final OpenCode PASS; Phase 27 five-layer QA is next
last_updated: "2026-07-20T19:02:10+08:00"
last_activity: 2026-07-20
progress:
  total_phases: 29
  completed_phases: 26
  total_plans: 27
  completed_plans: 26
  percent: 90
---

# Project State

## Project Reference

See: `.planning/ROADMAP.md`
See: `.planning/REQUIREMENTS.md`
See: `README.md`

**Core value:** Skillbird manages owned skills as the default source of truth, while external skill repositories remain disabled references unless explicitly enabled.

**Current focus:** Phase 27 five-layer quality inspection, stable reports, customer-delivery hard gates, and bounded monotonic candidate repair for the active `v5.0 Window-PPTX Verified Production Engine` milestone.

## Current Position

Milestone: v5.0 Window-PPTX Verified Production Engine
Current Phase: 27 of 29
Current Phase Name: Window-PPTX Quality Gates and Repair
Status: In Progress (current milestone 5/8 phases complete)
Last Activity: 2026-07-20

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
- Phase 27 now adds five-layer inspection, stable report schemas, hard delivery gates, and bounded monotonic repair.

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

## Next Actions

1. Define stable five-layer quality snapshots, finding codes, severity weights, and customer-delivery hard gates.
2. Implement geometry, density, repetition, font, chart, editability, compatibility, and package checks against plans and rendered presentations.
3. Add candidate-only repairs with a maximum of two passes, monotonic weighted-score acceptance, rollback, and versioned reports/logs.

## Blockers / Concerns

- Actual live current-user CLI homes were not mutated during automated acceptance. The same global path logic was verified through an isolated `--home` after `install --dry-run`.
- Phase 22 startup is slow on this host because installed PowerPoint add-ins load during real COM sessions; safety inspection therefore remains registry-only.
- v5.0 is active and unshipped; QA, benchmark, and final Windows UAT remain required.
