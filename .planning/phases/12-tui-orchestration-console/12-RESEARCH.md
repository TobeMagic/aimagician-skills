# Phase 12: TUI Orchestration Console - Research

**Researched:** 2026-06-04
**Domain:** blessed-based Node.js terminal UI for scope-aware Skillbee configuration orchestration
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Claude's Discretion
- Exact keybindings for include/exclude and preview confirmation are at Claude's discretion if they avoid conflicts and are documented in command help.
- Exact modal layout can follow existing report/source overlay patterns.
- Exact wording for eligibility reasons can use existing resolver reason strings.

### Deferred Ideas (OUT OF SCOPE)
## Deferred Ideas

- Full real global-directory verification and PRD acceptance checklist closure belong to Phase 13.
- Major TUI framework replacement is out of scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TUI3-01 | User can control source enabled/default-disabled/disabled state from the TUI and persist it to override YAML | Extend `src/tui/source-toggle.ts` from boolean toggles to tri-state source overrides, saving through scoped config helpers. |
| TUI3-02 | User can set skill include/exclude from the TUI and persist it to override YAML | Add a Skill Eligibility overlay or direct key actions that edit `includedIds`/`excludedIds` in scoped override YAML. |
| TUI3-03 | User can view taxonomy groups, source groupings, source status, and eligibility status in the TUI | Extend `ManagerSkillRecord` with source/override/eligibility fields and render badges in Cells and details in Nectar. |
| TUI3-04 | User can view a pre-execution preview modal with Target × Skill operations and skip reasons | Expose Phase 11 sync planning through manager APIs and render `create`/`overwrite`/`remove`/`skip` before writes. |
| TUI3-05 | User can view a final Target × Skill report with success, skipped, failed, removed, and overwritten statuses | Return operation-level sync execution summaries and render the existing report overlay as `Sync Complete`. |
</phase_requirements>

## Summary

Phase 12 should be planned as an integration/refinement phase, not a TUI rewrite. The blessed dashboard already has the right persistent structure: Crown header, Hive group list, Cells list/matrix, Nectar details, Guide bar, theme system, target selector, source overlay entry point, and report modal pattern. The plan should extend these existing closure-state and overlay patterns while preserving keyboard conventions and the bee visual language from `src/tui/theme.ts` and `12-UI-SPEC.md`.

The main technical gap is not blessed itself; it is the manager contract. Current manager APIs can search, install, uninstall, archive, and honor scoped `includedIds`/`excludedIds` internally, and Phase 11 exposes low-level `planManagedInstallSync()` with create/overwrite/remove/skip operations. However, `ManagerSkillRecord` does not yet expose eligibility/source state to the TUI, `sourceOverrides` are still boolean in `UserSkillConfig`, and `installSkills()` executes sync directly rather than providing a safe preview-confirm API boundary. Planning should therefore start by adding manager-level orchestration functions/data types, then wire dashboard overlays to those functions.

**Primary recommendation:** Add a thin manager orchestration facade first (`search` metadata, scoped source/skill override updates, preview plan, execute confirmed plan), then update blessed overlays/rows/reports to consume it without replacing the existing Hive/Cells/Nectar dashboard.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Node.js | project target ES2023/CommonJS | Runtime and filesystem/process APIs | Existing CLI/TUI and manager stack is Node-only. |
| TypeScript | ^5.9.2 | Strict typed implementation | Existing `tsconfig.json` uses `strict`, declarations, CommonJS. |
| blessed | ^0.1.81 | Terminal UI widgets, keys, overlays | Existing dashboard uses blessed screen/list/box/prompt and UI spec locks blessed. |
| yaml | ^2.8.2 | Read/write override YAML | Existing user config persistence uses `parse`/`stringify`. |
| zod | ^4.3.6 | Runtime config schema validation | Existing user config schema is zod strict object. |
| vitest | ^4.1.0 | Unit/integration tests | Existing `npm test` is `vitest run`. |

### Supporting
| Library/Module | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| `src/config/user-config.ts` | internal | Global/project scoped override YAML helpers | All durable TUI configuration writes. |
| `src/manager/manager.ts` | internal | TUI-safe orchestration boundary | Search metadata, source/skill override mutation, preview, execute confirmed sync. |
| `src/bootstrap/direct-target-sync.ts` | internal | Phase 11 operation categories | Generate create/overwrite/remove/skip operations for preview/report. |
| `src/tui/theme.ts` | internal | Bee palette, glyphs, target labels, theme presets | All new rows/overlays/status colors. |
| `src/tui/source-toggle.ts` | internal | Existing source overlay pattern | Extend to tri-state source controls. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Extend blessed dashboard | React Ink or another TUI framework | Out of scope; would violate blessed terminal UI and dashboard continuity constraints. |
| Manager facade | Directly call bootstrap internals from dashboard | Faster short-term but spreads sync safety/config rules into UI closure code. |
| Scoped YAML helpers | Mutating repo catalog defaults | Explicitly forbidden by v3 requirements and context. |
| Scrollable modal preview | Full-screen mode/fourth panel | UI spec forbids a fourth persistent panel and prefers compact overlays. |

**Installation:**
```bash
npm install
```

No new dependency should be planned for Phase 12.

## Architecture Patterns

### Recommended Project Structure
```text
src/
├── manager/
│   └── manager.ts              # Add orchestration facade/types here
├── config/
│   └── user-config.ts          # Add tri-state scoped override schema/helpers
├── tui/
│   ├── dashboard.ts            # Wire keys, rows, Nectar, preview/report overlays
│   ├── source-toggle.ts        # Extend boolean source overlay to tri-state
│   └── theme.ts                # Reuse palette/glyphs; add operation glyph helpers only if needed
└── bootstrap/
    └── direct-target-sync.ts   # Keep low-level plan/execute logic here

tests/
├── config/                     # Scoped config schema/write tests
├── manager/                    # Preview/report/eligibility contract tests
└── tui/                        # Pure row/format helpers + PTY smoke where useful
```

### Pattern 1: Manager-First Orchestration Boundary
**What:** Dashboard should call manager functions that already know scope, targets, projectDir, platform, catalog, manifests, eligibility, and sync safety.
**When to use:** For source state changes, include/exclude changes, preview generation, and confirmed sync execution.
**Example:**
```typescript
// Recommended manager surface for planning (names can vary):
await setSourceOverride({ scope, projectDir, sourceId, state: "default-disabled" });
await setSkillOverride({ scope, projectDir, assetIds, state: "include" });
const preview = await previewSkillSync({ scope, projectDir, selectedTargets, assetIds });
if (await showSyncPreview(preview)) {
  const result = await executeSkillSync(preview.confirmationToken ?? preview.request);
  showSyncReport(result);
}
```
**Confidence:** HIGH from existing manager shape and Phase 11 safety requirements.

### Pattern 2: Blessed Overlay Extension
**What:** Use centered `blessed.list` for selectable/editable state overlays and `blessed.box` for scrollable preview/report modals. Attach to parent screen, focus modal, call `screen.render()`, then `detach()` and restore `skillList.focus()`.
**When to use:** Source tri-state, skill include/exclude, sync preview, final report, command help.
**Example:**
```typescript
const previewBox = blessed.box({
  parent: screen,
  top: "center",
  left: "center",
  width: "80%",
  height: "70%",
  border: { type: "line" },
  tags: true,
  keys: true,
  vi: true,
  mouse: true,
  scrollable: true,
  alwaysScroll: true,
  label: ` ${BEE_ASCII} Sync Preview `,
  style: { bg: PALETTE.carbon, fg: PALETTE.ghostWhite, border: { fg: currentColors.brandYellow } },
  content: renderPreviewText(preview)
});
previewBox.focus();
screen.render();
previewBox.key(["escape", "q"], () => { previewBox.detach(); skillList.focus(); screen.render(); });
```
**Confidence:** HIGH from existing `showReport`, help overlay, and blessed docs.

### Pattern 3: Pure Formatting Helpers for Testability
**What:** Extract row/report/preview string builders into pure functions where possible. Current tests duplicate logic because `dashboard.ts` hides helpers; Phase 12 should export or isolate formatter functions to avoid duplication.
**When to use:** Cells rows, matrix rows, source rows, eligibility badges, preview/report text.
**Example:**
```typescript
export function summarizeOperations(operations: SyncOperation[]): Record<string, number> {
  return operations.reduce((counts, op) => ({ ...counts, [op.kind]: (counts[op.kind] ?? 0) + 1 }), {} as Record<string, number>);
}
```
**Confidence:** HIGH from current `tests/tui/group-filter.test.ts` duplicating dashboard logic.

### Anti-Patterns to Avoid
- **Calling `installSkills()` before preview confirmation:** Violates TUI3-04/SYNC-04; add preview-first flow.
- **Persisting source toggles to unscoped `user-config.yaml`:** Phase 12 must use scoped global/project override YAML.
- **Boolean source state only:** Cannot model enabled/default-disabled/disabled.
- **Embedding eligibility logic in dashboard row formatting:** Use manager-provided `eligibilityState` and reason so CLI/TUI behavior stays consistent.
- **Adding a new persistent panel:** UI spec requires preserving the three-panel dashboard.
- **Async config loads inside render loops:** Existing V3 fixed this by caching config; continue loading in refresh/mutation paths.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Terminal widgets/key handling | Raw stdin ANSI drawing | blessed widgets/key APIs | Blessed already handles focus, keys, scrollable boxes, lists, prompts, and render lifecycle. |
| Sync operation diffing | New TUI-side diff engine | `planManagedInstallSync()`/manager preview facade | Phase 11 already encodes managed-only safety and create/overwrite/remove/skip categories. |
| Scoped config paths | Ad hoc path joins in dashboard | `loadScopedUserConfig`/`saveScopedUserConfig`/`scopedUserConfigPath` | Avoid project/global scope leakage and path mistakes. |
| Eligibility rules | Dashboard checks for source enabled/include/exclude | Manager/resolver-provided eligibility state/reason | Keeps source-default-disabled, exclude priority, and global-only command rules consistent. |
| Theme colors | Inline ANSI literals | `currentColors` and `PALETTE` | Preserves bee/monokai/nord themes and UI spec. |
| Report grouping | One-off string concatenation in handlers | Pure report builder helpers | Enables unit tests and future richer operation data. |

**Key insight:** The hard part is preserving sync safety and scope correctness while presenting compact TUI affordances. Custom UI-side versions of config, eligibility, or sync planning would duplicate rules already introduced in Phases 9-11 and are likely to drift.

## Common Pitfalls

### Pitfall 1: Preview That Is Not the Executed Plan
**What goes wrong:** TUI shows a dry-run result, then re-computes a different plan at execution time after config/status changes.
**Why it happens:** Preview and execution are separate calls without a shared request snapshot.
**How to avoid:** Use one manager preview request shape and either execute the same request immediately after confirmation or return enough stable data to revalidate. At minimum, keep scope/projectDir/targets/assetIds/config inputs unchanged between preview and execute.
**Warning signs:** Preview counts differ from final report counts without a visible explanation.

### Pitfall 2: Scope Leakage Between Global and Project
**What goes wrong:** Source/include/exclude changes save to `~/.config/skillbee/user-config.yaml` or wrong scope path.
**Why it happens:** Existing source overlay takes only `configBaseDir` and uses unscoped `loadUserConfig`/`saveUserConfig`.
**How to avoid:** Update overlay options to include `scope` and `projectDir`, then use scoped config helpers.
**Warning signs:** Switching `s` does not change source/include/exclude states; project changes appear in global config.

### Pitfall 3: Boolean Source Overrides Cannot Express Default-Disabled
**What goes wrong:** Enabled/default-disabled/disabled collapses into enabled/disabled, breaking visibility/searchability and bulk eligibility.
**Why it happens:** `UserSkillConfig.sourceOverrides` is currently `Record<string, boolean>`.
**How to avoid:** Plan a schema migration to `Record<string, "enabled" | "default-disabled" | "disabled">` or equivalent typed object while preserving compatibility with existing booleans if needed.
**Warning signs:** Source overlay row can only show check/cross; no neutral state.

### Pitfall 4: Missing Eligibility Data in `ManagerSkillRecord`
**What goes wrong:** Cells/Nectar cannot show source status, override state, or exact reason without recomputing private manager logic.
**Why it happens:** Current record exposes installed/managed/available but not eligibility metadata.
**How to avoid:** Extend `ManagerSkillRecord` with fields like `sourceState`, `overrideState`, `eligibilityState`, `eligibilityReason`.
**Warning signs:** UI copies strings like `source-default-disabled` from local checks in `dashboard.ts`.

### Pitfall 5: Modal Key Conflicts and Base `q` Exit
**What goes wrong:** Pressing `q` in a modal exits the dashboard or Enter both confirms and shifts focus.
**Why it happens:** Global `screen.key` handlers remain active unless modal handlers consume workflow carefully.
**How to avoid:** Focus modal, bind modal `escape`/`q`/`enter`, avoid overloading base keys while modal is active, and detach/restore focus explicitly.
**Warning signs:** Closing preview quits whole TUI or leaves focus lost.

### Pitfall 6: Report Understates Remove/Overwrite
**What goes wrong:** Final report says only installed/skipped, hiding removals/overwrites.
**Why it happens:** Existing `InstallSkillsResult` only exposes `installed` and `skipped`, while Phase 12 requires removed/overwritten statuses.
**How to avoid:** Add operation-level result data to manager execution return, derived from Phase 11 sync operations.
**Warning signs:** `Sync Complete` cannot count remove/overwrite separately.

## Code Examples

Verified patterns from current project and blessed docs.

### Scoped Config Read/Write Pattern
```typescript
const config = await loadScopedUserConfig({
  configBaseDir: platformContext.configBaseDir,
  scope,
  projectDir: options.projectDir
});
config.includedIds = [...new Set([...config.includedIds, ...assetIds])].sort();
config.excludedIds = config.excludedIds.filter((id) => !assetIds.includes(id));
await saveScopedUserConfig({
  configBaseDir: platformContext.configBaseDir,
  scope,
  projectDir: options.projectDir
}, config);
```

### Existing Overlay Lifecycle Pattern
```typescript
const reportBox = blessed.box({
  parent: screen,
  top: "center",
  left: "center",
  width: "70%",
  height: "60%",
  border: { type: "line" },
  scrollable: true,
  alwaysScroll: true,
  keys: true,
  vi: true,
  mouse: true,
  tags: true,
  label: " Report "
});
reportBox.focus();
screen.render();
reportBox.key(["escape", "q"], () => { reportBox.detach(); screen.render(); });
```

### Phase 11 Operation Categories
```typescript
export type ManagedInstallSyncOperation =
  | { kind: "create" | "overwrite"; target: SupportedTarget; assetId: string; destinationPath: string }
  | { kind: "remove"; target: SupportedTarget; assetId: string; destinationPath: string }
  | { kind: "skip"; target: SupportedTarget; assetId: string; reason: "outside-allowed-roots" };
```

### Cells Matrix Row Extension Pattern
```typescript
return `${prefix} ${displayId}  ${cells}  eligibility:${skill.eligibilityReason ?? skill.eligibilityState}`;
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Dynamic tag Hive | Taxonomy group Hive | V3 Phase 8 | Phase 12 should keep groups and add source grouping/status, not revert to tags. |
| Unscoped user config | Scoped global/project override YAML | Phase 9 | Every durable source/include/exclude/archive change must pass scope/projectDir. |
| Hidden disabled sources | Visible/searchable default-disabled sources with explicit include | Phase 10 | TUI must show visible but ineligible skills with reasons. |
| Direct install writes | Previewed managed sync operations | Phase 11 | TUI install/sync must preview before writes. |
| Installed/skipped report | Operation-level report | Phase 12 target | Need success/skipped/failed/removed/overwritten counts. |

**Deprecated/outdated:**
- Boolean `sourceOverrides` is insufficient for Phase 12 tri-state UI; plan schema update/migration.
- `installSkills()` as a direct TUI mutation entry point is insufficient unless it gains preview-confirm support or is wrapped by new preview/execute APIs.
- Current source overlay using unscoped `loadUserConfig`/`saveUserConfig` conflicts with Phase 9.

## Open Questions

1. **Does Phase 11 already expose a manager-level preview API outside `direct-target-sync.ts`?**
   - What we know: `planManagedInstallSync()` exists at bootstrap level; current `manager.ts` `installSkills()` calls `syncManagedInstalls()` directly after resolving installs.
   - What's unclear: Whether untracked newer files in the active branch add preview manager functions not in the read snapshot.
   - Recommendation: Planner should allocate first task to inspect and add/reuse manager preview/execute APIs before UI work.

2. **Exact source tri-state schema shape**
   - What we know: `sourceOverrides` currently validates as `Record<string, boolean>`; requirements need enabled/default-disabled/disabled.
   - What's unclear: Whether catalog default `enabled: false` should be rendered as `default-disabled` or whether explicit `disabled` should hide/search-block a source.
   - Recommendation: Use string union states in scoped config and map old booleans for compatibility: `true -> enabled`, `false -> disabled`; absent -> catalog default/default-disabled.

3. **Final report failure granularity**
   - What we know: Current sync operations are synchronous filesystem operations that can throw; current result type lacks per-operation failed records.
   - What's unclear: Whether Phase 12 should catch per operation and continue or preserve fail-fast behavior.
   - Recommendation: Keep manager fail-safe; if execution throws, show `Operation failed: {reason}`. If operation-level results are easy, return failed rows; otherwise document strongest safe summary per context.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest ^4.1.0 |
| Config file | `/mnt/d/Growth_up_youth/repo/skills/vitest.config.ts` |
| Quick run command | `npm run typecheck && npx vitest run tests/config/user-config.test.ts tests/manager/manager-operations.test.ts tests/tui/group-filter.test.ts` |
| Full suite command | `npm test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| TUI3-01 | Source tri-state changes persist to scoped override YAML | unit/integration | `npx vitest run tests/config/user-config.test.ts tests/tui/source-toggle.test.ts` | ❌ Wave 0 for source-toggle test |
| TUI3-02 | Include/exclude/default skill overrides persist and affect eligibility | manager integration | `npx vitest run tests/manager/manager-operations.test.ts` | ✅ extend existing |
| TUI3-03 | Rows/details expose groups, source, status, eligibility reasons | TUI pure formatter unit | `npx vitest run tests/tui/group-filter.test.ts tests/tui/orchestration-format.test.ts` | ❌ Wave 0 for formatter test |
| TUI3-04 | Preview modal is generated before writes and includes create/overwrite/remove/skip | manager integration + PTY smoke | `npx vitest run tests/manager/manager-operations.test.ts tests/tui/tui-pty-smoke.test.ts` | ✅ extend existing |
| TUI3-05 | Final report includes success/skipped/failed/removed/overwritten | TUI formatter + manager integration | `npx vitest run tests/tui/orchestration-format.test.ts tests/manager/manager-operations.test.ts` | ❌ Wave 0 for formatter test |

### Sampling Rate
- **Per task commit:** `npm run typecheck && npx vitest run <changed-area tests>`
- **Per wave merge:** `npm test`
- **Phase gate:** Full suite green plus manual TUI smoke for source/preview/report overlays before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/tui/source-toggle.test.ts` — covers TUI3-01 tri-state row/state persistence helpers if overlay logic is extracted.
- [ ] `tests/tui/orchestration-format.test.ts` — covers TUI3-03/TUI3-04/TUI3-05 pure row, preview, and report text builders.
- [ ] `tests/manager/manager-operations.test.ts` extensions — cover preview-before-write, include/exclude priority, source default-disabled, and report operation counts.
- [ ] Export or move pure TUI helpers out of `dashboard.ts` so tests do not duplicate implementation logic.

## Sources

### Primary (HIGH confidence)
- `/mnt/d/Growth_up_youth/repo/skills/.planning/phases/12-tui-orchestration-console/12-CONTEXT.md` — locked decisions, phase boundary, deferred scope.
- `/mnt/d/Growth_up_youth/repo/skills/.planning/phases/12-tui-orchestration-console/12-UI-SPEC.md` — terminal layout, keybindings, overlay, copy, color contracts.
- `/mnt/d/Growth_up_youth/repo/skills/.planning/REQUIREMENTS.md` — TUI3-01 through TUI3-05 and v3 scope/sync requirements.
- `/mnt/d/Growth_up_youth/repo/skills/src/tui/dashboard.ts` — current blessed dashboard structure, state, overlays, rows, keybindings.
- `/mnt/d/Growth_up_youth/repo/skills/src/tui/source-toggle.ts` — current source overlay, boolean override limitation.
- `/mnt/d/Growth_up_youth/repo/skills/src/tui/theme.ts` — bee palette, glyphs, themes, matrix helpers.
- `/mnt/d/Growth_up_youth/repo/skills/src/manager/manager.ts` — scoped search/install/archive, eligibility internals, current result shape.
- `/mnt/d/Growth_up_youth/repo/skills/src/config/user-config.ts` — scoped YAML paths and current schema.
- `/mnt/d/Growth_up_youth/repo/skills/src/bootstrap/direct-target-sync.ts` — create/overwrite/remove/skip operation categories.
- Blessed official GitHub README/API docs — screen lifecycle, widgets, list/box/prompt, key handling, render/destroy behavior.

### Secondary (MEDIUM confidence)
- `/mnt/d/Growth_up_youth/repo/skills/docs/PRD.md` — v2/v3 product intent and acceptance language; some old file-path details have been superseded by Phases 9-12.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified in `package.json`, `tsconfig.json`, UI spec, and existing source.
- Architecture: HIGH — phase context locks extension of existing blessed dashboard; integration points are visible in source.
- Pitfalls: HIGH — derived from current code gaps vs Phase 12 requirements.
- Blessed API details: MEDIUM-HIGH — verified through official GitHub docs via WebFetch; project already uses these APIs successfully.

**Research date:** 2026-06-04
**Valid until:** 2026-07-04 for project-specific architecture; 2026-06-18 for current branch integration details if Phase 11 APIs change.
