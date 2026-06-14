# Phase 8: 蜂巢 Dashboard V3

## Status: In Progress

## Goals

1. **Group-based Hive panel**: Replace dynamic tag extraction with predefined taxonomy groups (Coding/Research/Design/Documents/Operations/Business)
2. **Source toggle**: Allow users to enable/disable external skill sources via TUI (S key)
3. **ANSI 256 color fix**: Fix splash screen and panel color rendering with correct `{214-fg}` syntax
4. **Install flow improvement**: Use `syncManagedInstalls()` to clean stale skills from target directories
5. **Taxonomy-based filtering**: Only show skills that have taxonomy entries (except archived)

## Changes Made

### `catalog/skills/slavingia-skills.yaml`
- Set `enabled: false` — Business group skills (validate-idea, grow-sustainably, etc.) hidden by default
- Source can be re-enabled via TUI source toggle

### `src/tui/theme.ts`
- Fixed `BEE_SPLASH` color tags from `{amber}` to `{${PALETTE.amber}-fg}` (ANSI 256 syntax)
- Converted `SELECTED_LIST_STYLE` to `getSelectedListStyle(colors: ThemeColors)` function
- Added `bg: PALETTE.carbon` to panel styles

### `src/tui/dashboard.ts`
- Replaced `allTags`/`selectedTags` with `allGroups`/`selectedGroups` (TaxonomyGroup[])
- Replaced `extractAllTags()` with `extractAllGroups()` — returns taxonomy groups
- Replaced `countSkillsPerTag()` with `countSkillsPerGroup()` — counts by group
- Replaced `filterSkillsByTags()` with `filterSkillsByGroups()` — filters by group
- `renderHivePanel()` now shows group names with skill counts
- Cached `userConfig` in dashboard state
- Added `bg: PALETTE.carbon` to all panels
- Added `S` key handler for source toggle overlay

### `src/tui/source-toggle.ts` (NEW)
- Source toggle overlay UI
- Lists all external sources with ✅/❌ status
- Space to toggle, Enter to confirm, Esc to cancel
- Persists overrides to `user-config.yaml` `sourceOverrides`

### `src/config/user-config.ts`
- Added `sourceOverrides: Record<string, boolean>` to schema and interface
- Default value: `{}`

### `src/manager/manager.ts`
- Added taxonomy-based filtering: `skill.archived || taxonomy.skills[skill.id] !== undefined`
- Replaced `copyManagedInstalls()` with `syncManagedInstalls()` for clean installs
- Added `createAllowedRootsByTarget()` helper (was already in run-bootstrap.ts)

### `tests/tui/group-filter.test.ts` (RENAMED from tag-filter.test.ts)
- Tests for `extractAllGroups()` and `filterSkillsByGroups()`
- All 10 tests pass

## Key Decisions

1. **Taxonomy as source of truth**: Skills not in taxonomy.yaml are hidden (except archived)
2. **Source-level disable**: `slavingia-skills` disabled at source level, not individual skill removal
3. **Group-based filtering**: Hive panel uses `skill.group` (predefined), not `skill.tags` (fine-grained)
4. **Sync install**: `syncManagedInstalls()` cleans stale skills before installing
5. **Dynamic styles**: `getSelectedListStyle(colors)` function updates with theme changes

## Test Results

- Build: ✅ passes
- Group filter tests: ✅ 10/10 pass
- Manager operations tests: ✅ 4/4 pass
- Bootstrap sync tests: ✅ 5/5 pass
- User config tests: ✅ 6/6 pass
- Taxonomy tests: ✅ 1/1 pass
- Source catalog tests: ✅ 2/2 pass

## Next Steps

1. User runs `npm start` to verify TUI
2. Verify splash screen renders with correct colors
3. Verify Hive panel shows groups (not tags)
4. Test source toggle (S key) to enable/disable slavingia-skills
5. Test install flow with sync (should clean stale skills)
