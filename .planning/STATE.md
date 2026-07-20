---
gsd_state_version: 1.0
milestone: v5.0
milestone_name: Window-PPTX Verified Production Engine
current_phase: 22
current_phase_name: Window-PPTX Baseline and Safety
status: in_progress
stopped_at: Phase 22 implementation is under verification; real Windows PowerPoint cases remain pending
last_updated: "2026-07-20T12:14:24+08:00"
last_activity: 2026-07-20
progress:
  total_phases: 29
  completed_phases: 21
  total_plans: 22
  completed_plans: 21
  percent: 72
---

# Project State

## Project Reference

See: `.planning/ROADMAP.md`
See: `.planning/REQUIREMENTS.md`
See: `README.md`

**Core value:** Skillbird manages owned skills as the default source of truth, while external skill repositories remain disabled references unless explicitly enabled.

**Current focus:** Phase 22 safety verification for the active `v5.0 Window-PPTX Verified Production Engine` milestone.

## Current Position

Milestone: v5.0 Window-PPTX Verified Production Engine
Current Phase: 22 of 29
Current Phase Name: Window-PPTX Baseline and Safety
Status: In Progress (current milestone 0/8 phases complete)
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

- Phase 22 Linux/fake-COM safety slices have independent review evidence for strict dry-run, output guards, COM ownership, macro-security restoration, terminal add-in inspection, dynamic export geometry, and transactional candidate promotion;
- the complete Phase 22 Python safety suite currently records 96 focused tests passing;
- Phase 22 remains incomplete until the pending real Windows PowerPoint cases and exit criteria in `22-VALIDATION.md` pass.

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

## Next Actions

1. Complete Phase 22 real Windows PowerPoint validation without touching source fixtures.
2. Close Phase 22 only after its transactional, package, ownership, macro-security, and source-hash exit criteria pass.
3. Begin Phase 23 DeckPlan and semantic rules only after the Phase 22 gate is evidenced.

## Blockers / Concerns

- Actual live current-user CLI homes were not mutated during automated acceptance. The same global path logic was verified through an isolated `--home` after `install --dry-run`.
- The Phase 22 implementation has Linux fake-COM and package-level evidence, but attached/isolated real PowerPoint sessions, macro-enabled formats, paths with spaces/Chinese characters, and reopen/edit checks are still pending.
- v5.0 is active and unshipped; later design, renderer, QA, benchmark, and UAT phases must not be inferred complete from the Phase 22 foundation.
