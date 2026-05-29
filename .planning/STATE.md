---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Skillbee V2 - 功能深化
current_phase: 5
current_phase_name: 概览与打磨
current_plan: 1
status: completed
stopped_at: Phase 5 complete
last_updated: "2026-05-27T19:20:00+08:00"
last_activity: 2026-05-27
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 5
  completed_plans: 5
  percent: 100
---

# Project State

## Project Reference

See: docs/PRD.md (updated 2026-05-27)
See: docs/DEV-WORKFLOW.md (updated 2026-05-27)
See: .planning/PROJECT.md (updated 2026-03-13)

**Core value:** After cloning the repo, one command installs and updates the right skills into each supported CLI's user-level location with as little manual setup as possible.
**Current focus:** Skillbee V2 功能深化 complete (all 5 phases)

## Current Position

Milestone: v2.0
Current Phase: 5
Current Phase Name: 概览与打磨
Total Plans in Phase: 1
Total Phases: 5
Phase: 5 of 5 (概览与打磨)
Plan: 1 of 1
Status: Complete
Last Activity: 2026-05-27
Last Activity Description: Phase 5 complete: F7 matrix view — `v` key toggles between list and matrix views; matrix shows skills × selectedTargets with ✓/○/— per cell using formatMatrixCell + targetShortLabel; row format: `[x] skill-id  Cd:✓ Oc:✓ Cr:○ Cp:-`; navigating/filtering/selection all work in matrix mode; detail panel unchanged. P2 multi-theme — `T` key cycles through bee/monokai/nord themes; theme stored in user-config.yaml `theme` field; applied at startup from config; border colors update on theme switch; header shows current theme name.

Progress: 100%

## Accumulated Context

### Decisions

- [Phase 1]: Owned skills are discovered from `skills/owned/*/SKILL.md`
- [Phase 1]: External sources live in directory-based YAML catalogs under `catalog/skills` and `catalog/plugins`
- [Phase 1]: Target rules default to all supported CLIs and can be overridden at source or asset level
- [Phase 1]: Unsupported capabilities remain in normalized target state so later installers can skip and warn explicitly
- [V2 Phase 1]: Custom tags stored in user-config.yaml under `customTags` key, merged into ManagerSkillRecord at search time
- [V2 Phase 1]: User archive state stored in user-config.yaml `archivedIds` instead of manifest, so it survives re-installs
- [V2 Phase 1]: Custom groups stored in user-config.yaml under `groups`, displayed in TUI group panel with `@ ` prefix
- [V2 Phase 1]: TUI archive/unarchive via `x` key — reads current archive state from the selected skill and toggles it
- [V2 Phase 2]: theme.ts created with bee brand constants (COLORS, SELECTED_LIST_STYLE, formatMatrixCell, targetShortLabel)
- [V2 Phase 2]: Header redesigned with 🐝 prefix + yellow color accents + status info (scope/target/archived/query/selected)
- [V2 Phase 2]: All panel labels prefixed with 🐝, selected items use yellow highlight, installed=green, archived=cyan, unavailable=gray
- [V2 Phase 2]: Detail panel shows cross-target install matrix (all 7 targets with ✓/○/- cells), related skills sorted by tag overlap, SKILL.md preview for owned skills (async read from skills/owned/{id}/SKILL.md)
- [V2 Phase 2]: ? and Ctrl+/ open keyboard shortcuts overlay with grouped command reference
- [V2 Phase 2]: SKILL.md preview is async — loaded after initial render so the UI is never blocked
- [V2 Phase 2]: ownedSkillsRoot from shared/paths.ts used for SKILL.md lookup; external/command skills skip preview
- [V2 Phase 2]: The pre-existing bootstrap-smoke test failure is unrelated to V2 changes (shell compatibility)
- [V2 Phase 3]: F2 replaces single `target` variable with `selectedTargets: Set<SupportedTarget>` + `primaryTarget` for display
- [V2 Phase 3]: `tab` now cycles primaryTarget within the selected targets set instead of cycling through all targets
- [V2 Phase 3]: `t` key opens blessed list overlay with checkbox items; `a`/`A` for select all/none; enter/escape to confirm
- [V2 Phase 3]: F6 `FilterState` defined at module level with 3 dimensions: installedStatus, filterTarget, tag
- [V2 Phase 3]: Filter panel uses blessed.box with ▶ indicator for active dimension; ↑/↓ navigate dimensions, ←/→/space cycle values
- [V2 Phase 3]: All operations (install, uninstall, search, archive) use the full selectedTargets set
- [V2 Phase 3]: Filter state shown in header as compact S:/T:/tag: prefixes when active; `[filtered]` badge in status bar
- [V2 Phase 4]: F3 batch install/uninstall leverages existing multi-target support from Phase 2 — no extra UI beyond the report overlay
- [V2 Phase 4]: F10 report is a blessed.box modal overlay (dismissable on any keypress) showing per-target grouping of ✓/○/✗ results with skip reasons
- [V2 Phase 4]: `buildInstallReport` and `buildUninstallReport` return plain strings; `showReport` renders them in the overlay
- [V2 Phase 4]: Report only shows for mutate() operations (install/uninstall), not for toggleArchive or resetCursor
- [V2 Phase 5]: F7 matrix view shows skills × selectedTargets with ✓/○/— cells, toggled via `v` key
- [V2 Phase 5]: F7 uses the same blessed.list widget with formatted string rows (no separate widget needed)
- [V2 Phase 5]: P2 multi-theme defines 3 presets (bee/monokai/nord) in theme.ts, stored in user-config.yaml
- [V2 Phase 5]: `T` key cycles themes and saves to config; `currentColors` variable replaces inline COLORS references in overlay boxes
- [Phase 2]: `bootstrap` is the primary command and defaults to all supported targets
- [Phase 2]: Bootstrap writes manifest-backed user-level workspace state before direct target adapters exist
- [Phase 2]: Workspace roots can be overridden for isolated smoke runs through environment variables
- [Phase 3]: Codex, Claude Code, and OpenCode now sync managed skill directories directly into current-user homes
- [Phase 3]: Direct target sync prunes only stale managed directories and preserves unmanaged user content
- [Phase 3]: GitHub-backed skills resolve through workspace source materialization, while command-based skill sources execute as delegated installers
- [Phase 3]: Built CLI smoke runs can override catalog roots, GitHub source paths, and fake user homes for offline verification
- [Phase 4]: Gemini now installs generated native extensions under the current user's `.gemini/extensions` home
- [Phase 4]: Bootstrap reports plugin installs and explicit skip reasons separately from target summaries
- [Phase 4]: OpenCode now receives managed plugin file installs under the user-level plugins directory
- [Phase 5]: The CLI now exposes `list`, `inspect`, and `doctor` commands backed by live-home and manifest inspection
- [Phase 5]: README now documents the final bootstrap and verification flow instead of the intermediate Phase 3 state
- [Phase 6]: `window-pptx` is an owned skill for Windows desktop PowerPoint COM/VBA automation using a `REQUEST.md` project-folder workflow
- [Phase 6]: iSlide/OKPlus are optional discovered add-ins; native PowerPoint COM remains the default execution path
- [Phase 7]: Copilot bootstrap broken due to missing `case "copilot"` in `resolveSkillInstallDestination`; fixed by adding copilot branch
- [Phase 7]: Historical skill leftovers: codex (GSD×36), claude (Lark×24), copilot (GSD×36), hermes (Lark×24 + 内置×25 + 系统×2); opencode/gemini/cursor clean
- [Phase 7]: `llm-know-how-wiki` present in all 5 main CLI targets
- [Phase 7]: Feishu/Lark skill source set to `larksuite/lark-cli` defaulting to disabled

### Roadmap Evolution

- Phase 6 added: Add window-pptx COM/VBA PowerPoint automation skill with discuss-driven project folder workflow
- Phase 6 completed: added `window-pptx`, bundled helper script, project template, and docs
- Phase 7 added: Bootstrap copilot fix and multi-target skill audit
- Phase 7 completed: fixed copilot install, audited all targets, recorded leftovers

### Blockers/Concerns

- No blocking milestone gaps remain
- Full `window-pptx` runtime verification requires native Windows, desktop PowerPoint, and pywin32
- A future milestone can focus on source caching, lockfiles, link mode, or richer plugin automation if needed

## Session Continuity

Last session: 2026-05-27T19:20:00+08:00
Stopped at: V2 milestone complete (all 5 phases)
Resume file: .planning/ROADMAP.md
