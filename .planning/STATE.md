---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Configuration Orchestration & Verified Sync
current_phase: 9
current_phase_name: Configuration Scope Foundation
current_plan: 0
status: defining-requirements
stopped_at: Milestone v3.0 started; requirements and roadmap defined from docs/PRD.md
last_updated: "2026-05-30T19:30:00+08:00"
last_activity: 2026-05-30
progress:
  total_phases: 13
  completed_phases: 7
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: docs/PRD.md (updated 2026-05-30)
See: docs/DEV-WORKFLOW.md (updated 2026-05-27)
See: .planning/PROJECT.md (updated 2026-05-30)

**Core value:** Skillbee resolves catalog defaults plus user YAML overrides into safe, previewed, repeatable sync plans for the selected CLI targets and scope.
**Current focus:** v3.0 Configuration Orchestration & Verified Sync — implement PRD configuration layers, project/global scopes, eligibility rules, preview-confirmed sync, and real acceptance.

## Current Position

Milestone: v3.0
Current Phase: 9
Current Phase Name: Configuration Scope Foundation
Total Plans in Phase: 0
Total Phases: 13
Phase: 9 of 13 (Configuration Scope Foundation)
Plan: —
Status: Defining requirements / roadmap initialized
Last Activity: 2026-05-30
Last Activity Description: Started v3.0 milestone from docs/PRD.md configuration-orchestration requirements: global/project scopes, user override YAML, source default-disabled visibility, include/exclude priority, preview-confirmed managed sync, selected-target execution, command-source global-only behavior, real global acceptance, and Target × Skill reports.

Progress: 0%

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
- [V2 Phase 2]: Detail panel shows cross-target install matrix (all 7 targets with ✓/○/- cells), related skills sorted by tag overlap, SKILL.md preview for owned skills
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
- [V3 Phase 8]: Hive panel shows predefined taxonomy groups (Coding/Research/Design/Documents/Operations/Business) instead of dynamic tags
- [V3 Phase 8]: `slavingia-skills` source disabled by default — Business group skills (validate-idea, grow-sustainably, etc.) hidden
- [V3 Phase 8]: Source toggle feature (S key) lists external sources with ✅/❌, persists to user-config.yaml `sourceOverrides`
- [V3 Phase 8]: BEE_SPLASH fixed from broken `{amber}` tags to correct `{214-fg}` ANSI 256 syntax
- [V3 Phase 8]: `SELECTED_LIST_STYLE` converted to `getSelectedListStyle(colors)` function for dynamic theme updates
- [V3 Phase 8]: All panels now have explicit `bg: PALETTE.carbon` for consistent dark background
- [V3 Phase 8]: `userConfig` cached in dashboard state to avoid async re-loading on every render
- [V3 Phase 8]: `syncManagedInstalls()` replaces `copyManagedInstalls()` — cleans stale skills from target directories
- [V3 Phase 8]: Taxonomy-based filtering: skills without taxonomy entries are hidden (except archived)

### Roadmap Evolution

- Phase 6 added: Add window-pptx COM/VBA PowerPoint automation skill with discuss-driven project folder workflow
- Phase 6 completed: added `window-pptx`, bundled helper script, project template, and docs
- Phase 7 added: Bootstrap copilot fix and multi-target skill audit
- Phase 7 completed: fixed copilot install, audited all targets, recorded leftovers
- Phase 8 added: 蜂巢 Dashboard V3 — group-based Hive, source toggle, ANSI 256 colors, install sync

### Blockers/Concerns

- User needs to verify TUI with `npm start` — splash color rendering, group-based Hive, source toggle
- Full `window-pptx` runtime verification requires native Windows, desktop PowerPoint, and pywin32
- A future milestone can focus on source caching, lockfiles, link mode, or richer plugin automation if needed

## Session Continuity

Last session: 2026-05-30T17:40:00+08:00
Stopped at: V3 implementation complete, awaiting user TUI verification
Resume file: .planning/ROADMAP.md
