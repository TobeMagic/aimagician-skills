---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 7
current_phase_name: Bootstrap copilot fix and multi-target skill audit
current_plan: 1
status: completed
stopped_at: Phase 7 complete
last_updated: "2026-05-11T06:30:00+08:00"
last_activity: 2026-05-11
progress:
  total_phases: 7
  completed_phases: 7
  total_plans: 16
  completed_plans: 16
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-13)

**Core value:** After cloning the repo, one command installs and updates the right skills into each supported CLI's user-level location with as little manual setup as possible.
**Current focus:** Phase 7 complete; all 7 CLI targets bootstrapped and audited; copilot bootstrap bug fixed

## Current Position

Current Phase: 7
Current Phase Name: Bootstrap copilot fix and multi-target skill audit
Current Plan: 1
Total Plans in Phase: 1
Total Phases: 7
Phase: 7 of 7 (Bootstrap copilot fix and multi-target skill audit)
Plan: 1 of 1 in current phase
Status: Complete
Last Activity: 2026-05-11
Last Activity Description: Fixed copilot bootstrap (missing case "copilot" in source-resolution.ts), audited 7 CLI targets, confirmed llm-know-how-wiki present everywhere, recorded historical leftovers per target

Progress: 100%

## Accumulated Context

### Decisions

- [Phase 1]: Owned skills are discovered from `skills/owned/*/SKILL.md`
- [Phase 1]: External sources live in directory-based YAML catalogs under `catalog/skills` and `catalog/plugins`
- [Phase 1]: Target rules default to all supported CLIs and can be overridden at source or asset level
- [Phase 1]: Unsupported capabilities remain in normalized target state so later installers can skip and warn explicitly
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

Last session: 2026-05-11T06:30:00+08:00
Stopped at: Phase 7 complete
Resume file: .planning/ROADMAP.md
