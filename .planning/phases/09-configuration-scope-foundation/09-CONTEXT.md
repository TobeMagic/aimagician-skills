# Phase 9: Configuration Scope Foundation - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 9 delivers the configuration-scope foundation for Skillbee v3.0. It must add scope-aware user override YAML while preserving the existing scoped workspace/manifest foundation. This phase should not implement source eligibility resolution, sync preview execution, or TUI orchestration controls beyond making durable config APIs available for later phases.

</domain>

<decisions>
## Implementation Decisions

### Scope model
- Use the existing `InstallScope` model: `global` and `project` are independent scopes.
- Global override YAML path is `~/.config/skillbee/global/config.yaml` using the active platform `configBaseDir`.
- Project override YAML path is `<project>/.skillbee/config.yaml`, where `<project>` is explicit `projectDir` when provided, otherwise the current working directory.
- Existing workspace/manifest infrastructure may remain JSON-backed for now; this phase must ensure global and project manifests are resolved independently and cannot overwrite each other.

### Config API shape
- Prefer additive scope-aware APIs in `src/config/user-config.ts` rather than breaking existing callers immediately.
- Preserve existing `loadUserConfig(configBaseDir)` and `saveUserConfig(configBaseDir, config)` behavior as compatibility wrappers for the global/default config path if needed.
- Add explicit resolver/load/save APIs that accept `{ scope, configBaseDir, projectDir }` or equivalent concrete options.
- Durable TUI/config mutations must write user override YAML only, never repository catalog or taxonomy files.

### Migration and compatibility
- Existing `user-config.yaml` format remains loadable.
- Missing scoped config files should return `defaultUserConfig()`.
- Directory creation should happen on save, not on read.
- Use the existing YAML formatting style and schema validation patterns from `user-config.ts`.

### Testing expectations
- Unit tests must prove global config resolves to `skillbee/global/config.yaml`.
- Unit tests must prove project config resolves to `<project>/.skillbee/config.yaml`.
- Tests must prove global and project config writes do not affect each other.
- Existing tests for archive IDs, groups, tags, theme, and source overrides must continue passing.
- Manager/TUI consumers do not need full v3 UI behavior in this phase, but the new scoped config APIs must be available for later phases.

### Claude's Discretion
- Claude may choose exact TypeScript type names and helper decomposition, as long as the public behavior above is testable.
- Claude may keep manifest file format as existing JSON in Phase 9, because the acceptance criterion is independence, not YAML manifest migration.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/config/user-config.ts` already owns YAML-backed user config schema, defaults, load/save helpers, and mutation helpers for groups, archived IDs, custom tags, theme, and `sourceOverrides`.
- `src/model/scopes.ts` exports `installScopes`, `InstallScope`, and related validators.
- `src/bootstrap/workspace.ts` already resolves scoped workspaces and manifests; project scope currently uses `<projectDir || cwd>/.aimagician-skills/manifest.json`, global uses `platformContext.workspaceRoot`.
- `src/shared/platform.ts` resolves `configBaseDir`, `stateBaseDir`, `workspaceRoot`, and env overrides for tests.
- `src/bootstrap/target-homes.ts` already uses scope/project inputs for target path resolution.

### Established Patterns
- Config tests use temp directories via `mkdtemp` and cleanup in `tests/config/user-config.test.ts`.
- Manager integration tests already pass fake platform roots and explicit `scope` / `projectDir` in `tests/manager/manager-operations.test.ts`.
- Existing config schema is strict and versioned; new scope behavior should be explicit and tested rather than implicit path string manipulation in callers.

### Integration Points
- `src/config/user-config.ts` is the primary Phase 9 modification point.
- `src/tui/dashboard.ts` and `src/tui/source-toggle.ts` currently load global config directly and will need scoped APIs in later phases.
- `src/manager/manager.ts` currently loads user config from `platformContext.configBaseDir` and should be able to consume the new scoped config API when source eligibility and sync phases need it.
- `src/bootstrap/workspace.ts` and `src/bootstrap/manifest.ts` provide manifest independence; Phase 9 should verify rather than replace them unless required.

</code_context>

<specifics>
## Specific Ideas

Use the PRD-approved layered model: repository defaults, user override YAML, scope manifest, and transient TUI session state. Phase 9 only implements the user override YAML and manifest scope foundation.

</specifics>

<deferred>
## Deferred Ideas

- Source visible/searchable default-disabled behavior belongs to Phase 10.
- Include/exclude final eligibility priority belongs to Phase 10.
- Preview-confirmed managed sync belongs to Phase 11.
- TUI orchestration controls and reports belong to Phase 12.
- Real global CLI acceptance belongs to Phase 13.

</deferred>
