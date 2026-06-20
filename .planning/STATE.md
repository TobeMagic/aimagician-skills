---
gsd_state_version: 1.0
milestone: v4.0
milestone_name: AImagician Superpower + Skillbird Consolidation
current_phase: 21
current_phase_name: Milestone Closure
status: complete
stopped_at: v4 milestone complete; all requirements have audit or acceptance evidence
last_updated: "2026-06-14T12:19:42+08:00"
last_activity: 2026-06-14
progress:
  total_phases: 21
  completed_phases: 21
  total_plans: 21
  completed_plans: 21
  percent: 100
---

# Project State

## Project Reference

See: `.planning/ROADMAP.md`
See: `.planning/REQUIREMENTS.md`
See: `README.md`

**Core value:** Skillbird manages owned skills as the default source of truth, while external skill repositories remain disabled references unless explicitly enabled.

**Current focus:** milestone closure and future follow-up selection after v4 consolidation.

## Current Position

Milestone: v4.0
Current Phase: 21
Current Phase Name: Real Install Acceptance
Status: Complete
Last Activity: 2026-06-14

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

## Next Actions

1. Use `.planning/milestones/v4.0-MILESTONE-AUDIT.md` as the final requirement-by-requirement closure record.
2. Pick the next milestone only after reviewing any remaining v3 legacy requirements that should be retired or migrated into v5.

## Blockers / Concerns

- Actual live current-user CLI homes were not mutated during automated acceptance. The same global path logic was verified through an isolated `--home` after `install --dry-run`.
