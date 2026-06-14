# Phase 12: TUI Orchestration Console - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the existing blessed-based Skillbee TUI a frontend for v3 scope-aware configuration orchestration, source/include/exclude controls, eligibility visibility, preview confirmation, and final Target × Skill reporting. This phase changes TUI and manager-facing orchestration UX; the Phase 11 sync engine and Phase 13 real global acceptance remain separate concerns.

</domain>

<decisions>
## Implementation Decisions

### Dashboard continuity
- Keep the existing 蜂巢 Dashboard V3 structure: Hive / Cells / Nectar panels, bee theme, amber accents, multi-target selection, source toggle, and matrix/list modes.
- Add orchestration features by extending existing blessed overlays and manager operations rather than replacing the TUI architecture.
- Preserve existing keyboard conventions where possible; new actions should be discoverable in the existing `?` command help.

### Scope and configuration controls
- Scope switching remains visible in the header and should drive scope-specific config, manifest, install status, preview, and report data.
- Source state controls should support enabled/default-disabled/disabled semantics and persist to scoped override YAML, not repo catalog defaults.
- Skill include/exclude controls should persist to scoped override YAML and be reflected in visible eligibility reasons.

### Preview and report UX
- Install/sync actions must show a pre-execution Target × Skill preview modal before filesystem writes.
- Preview rows should use Phase 11 operation categories: create, overwrite, remove, skip.
- Final report should show per-target success, skipped, failed, removed, and overwritten statuses where the manager/sync layer provides them.
- If operation detail is not yet exposed at the exact desired granularity, TUI should present the strongest available safe summary and keep the implementation ready for richer operation data.

### Claude's Discretion
- Exact keybindings for include/exclude and preview confirmation are at Claude's discretion if they avoid conflicts and are documented in command help.
- Exact modal layout can follow existing report/source overlay patterns.
- Exact wording for eligibility reasons can use existing resolver reason strings.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product requirements
- `.planning/ROADMAP.md` §Phase 12 — Phase goal and success criteria.
- `.planning/REQUIREMENTS.md` §TUI Orchestration UX — TUI3-01 through TUI3-05.
- `docs/PRD.md` — v3 orchestration and verified sync acceptance expectations.

### Upstream phase context
- `.planning/phases/08-蜂巢-dashboard-v3/08-CONTEXT.md` — Existing dashboard layout and visual direction.
- `.planning/phases/09-configuration-scope-foundation/09-CONTEXT.md` — Scope-aware config and manifest separation.
- `.planning/phases/10-source-eligibility-resolver/10-CONTEXT.md` — Eligibility, include/exclude, and default-disabled semantics.
- `.planning/phases/11-previewed-managed-sync-engine/11-CONTEXT.md` — Preview operation and managed sync safety decisions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/tui/dashboard.ts` contains the current blessed Dashboard with Hive/Cells/Nectar panels, keybindings, progress animation, report overlays, and manager calls.
- `src/tui/source-toggle.ts` contains the current external source toggle overlay and should be extended or replaced for tri-state source semantics.
- `src/manager/manager.ts` contains scoped search/install/uninstall/archive operations and is the right boundary for TUI orchestration.
- `src/config/user-config.ts` contains scoped user override config persistence.

### Established Patterns
- TUI uses blessed overlays for source toggles, reports, target selection, filter panels, and help.
- TUI state is held in closure variables inside `runDashboard` and reloaded via manager functions after mutations.
- Theme styling should use `currentColors`, `PALETTE.carbon`, and existing bee glyph conventions.

### Integration Points
- Install key handler in `dashboard.ts` is the main insertion point for preview confirmation.
- `showSourceToggle` and command help are insertion points for source/config UX.
- Manager search records already include installed/managed/available targets and eligibility-related data can be surfaced there.

</code_context>

<specifics>
## Specific Ideas

Use compact modal overlays rather than a new full-screen mode. Prefer Target × Skill matrices and short reason strings because the terminal UI has limited width.

</specifics>

<deferred>
## Deferred Ideas

- Full real global-directory verification and PRD acceptance checklist closure belong to Phase 13.
- Major TUI framework replacement is out of scope.

</deferred>

---

*Phase: 12-tui-orchestration-console*
*Context gathered: 2026-06-04*
