---
gsd_state_version: 1.0
milestone: v5.0
milestone_name: Window-PPTX Verified Production Engine
current_phase: 23
current_phase_name: Window-PPTX DeckPlan and Semantic Rules
status: in_progress
stopped_at: Phase 22 passed two consecutive native Windows UAT runs; Phase 23 compiler implementation is next
last_updated: "2026-07-20T13:42:21+08:00"
last_activity: 2026-07-20
progress:
  total_phases: 29
  completed_phases: 22
  total_plans: 23
  completed_plans: 22
  percent: 76
---

# Project State

## Project Reference

See: `.planning/ROADMAP.md`
See: `.planning/REQUIREMENTS.md`
See: `README.md`

**Core value:** Skillbird manages owned skills as the default source of truth, while external skill repositories remain disabled references unless explicitly enabled.

**Current focus:** Phase 23 DeckPlan v1, business archetypes, semantic mapping, capacity rules, and deterministic decision traces for the active `v5.0 Window-PPTX Verified Production Engine` milestone.

## Current Position

Milestone: v5.0 Window-PPTX Verified Production Engine
Current Phase: 23 of 29
Current Phase Name: Window-PPTX DeckPlan and Semantic Rules
Status: In Progress (current milestone 1/8 phases complete)
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
- Phase 23 now moves content planning and layout-choice inputs into a versioned semantic DeckPlan compiler with deterministic weak-model defaults.

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

## Next Actions

1. Implement DeckPlan v1 validation with explicit rejection of raw coordinates, colors, fonts, COM calls, and arbitrary code.
2. Add and test 15 commercial narrative archetypes plus deterministic semantic-to-page and chart/layout ranking rules.
3. Add capacity splitting, sparse-content preservation, cross-slide rhythm, top-three decision traces, and low-confidence safe defaults.

## Blockers / Concerns

- Actual live current-user CLI homes were not mutated during automated acceptance. The same global path logic was verified through an isolated `--home` after `install --dry-run`.
- Phase 22 startup is slow on this host because installed PowerPoint add-ins load during real COM sessions; safety inspection therefore remains registry-only.
- v5.0 is active and unshipped; the semantic compiler, design registries, renderer, advanced objects, QA, benchmark, and final UAT remain required.
