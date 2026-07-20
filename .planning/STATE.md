---
gsd_state_version: 1.0
milestone: v5.0
milestone_name: Window-PPTX Verified Production Engine
current_phase: 25
current_phase_name: Window-PPTX Transactional Core Renderer
status: in_progress
stopped_at: Phase 24 design registries passed 148 focused and 310 full tests with two independent final reviews; Phase 25 renderer is next
last_updated: "2026-07-20T17:17:20+08:00"
last_activity: 2026-07-20
progress:
  total_phases: 29
  completed_phases: 24
  total_plans: 25
  completed_plans: 24
  percent: 83
---

# Project State

## Project Reference

See: `.planning/ROADMAP.md`
See: `.planning/REQUIREMENTS.md`
See: `README.md`

**Core value:** Skillbird manages owned skills as the default source of truth, while external skill repositories remain disabled references unless explicitly enabled.

**Current focus:** Phase 25 editable core rendering, ratio-aware geometry, master/footer/z-order/grouping behavior, project/CLI orchestration, transactional delivery integration, and recording fake-COM verification for the active `v5.0 Window-PPTX Verified Production Engine` milestone.

## Current Position

Milestone: v5.0 Window-PPTX Verified Production Engine
Current Phase: 25 of 29
Current Phase Name: Window-PPTX Transactional Core Renderer
Status: In Progress (current milestone 3/8 phases complete)
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
- Phase 25 now turns compiled semantic plans and governed layouts into editable native PowerPoint core objects through a transactional renderer.

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

## Next Actions

1. Define a pure render plan that joins compiled DeckPlan slides with governed themes, layouts, and editable component commands.
2. Implement recording fake-COM plus deterministic native text, shape, image, master, footer, z-order, and grouping operations.
3. Integrate validate/compile/render/inspect/repair orchestration with existing transactional output policy and add focused end-to-end tests.

## Blockers / Concerns

- Actual live current-user CLI homes were not mutated during automated acceptance. The same global path logic was verified through an isolated `--home` after `install --dry-run`.
- Phase 22 startup is slow on this host because installed PowerPoint add-ins load during real COM sessions; safety inspection therefore remains registry-only.
- v5.0 is active and unshipped; renderer, advanced objects, QA, benchmark, and final UAT remain required.
