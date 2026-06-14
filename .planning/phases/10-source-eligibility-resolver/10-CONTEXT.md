# Phase 10: Source Eligibility Resolver - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 10 resolves catalog defaults plus scoped user override YAML into an explainable skill eligibility model. It does not execute filesystem sync or build the final TUI preview; those are Phase 11 and Phase 12.

</domain>

<decisions>
## Implementation Decisions

### Eligibility Rules
- `exclude` is strongest: excluded skills are never eligible even if source enabled or skill included.
- Explicit `include` can make a skill from a default-disabled source eligible.
- Enabled/default-enabled sources contribute eligible skills unless excluded.
- Disabled/default-disabled sources remain visible/searchable but are not bulk-install eligible unless a skill is explicitly included.
- Command-based/generated sources are global-only for install eligibility; in project scope they are skipped with reason `command-source-global-only`.
- Every decision must carry a reason string usable by CLI/TUI reports.

### Config Layer
- User include/exclude and source overrides live in scoped user override YAML from Phase 9.
- Repository catalog/taxonomy remains read-only baseline.
- Use existing source override plumbing where possible; extend schema minimally.

### Claude's Discretion
- Function names and exact type shape are at Claude discretion, but tests must assert the PRD-visible behavior and reason strings.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/config/user-config.ts` now exposes scoped user config and `sourceOverrides`.
- `src/bootstrap/plan-bootstrap.ts` and `src/catalog/*` normalize catalog sources and planned assets.
- `src/manager/manager.ts` is the best integration point for search/install/archive behavior.
- `src/model/scopes.ts` exposes `InstallScope`.

### Established Patterns
- Tests use Vitest with temp directories and real filesystem fixtures.
- Manager tests create local owned/catalog/external fixtures.

### Integration Points
- Extend `UserSkillConfig` for skill include/exclude.
- Add eligibility resolver module under `src/config` or `src/manager`.
- Update manager search/install dry-run paths to report eligibility state/reasons.

</code_context>

<specifics>
## Specific Ideas

Use reason strings: `source-enabled`, `source-default-enabled`, `source-default-disabled`, `source-disabled`, `skill-included`, `skill-excluded`, `command-source-global-only`.

</specifics>

<deferred>
## Deferred Ideas

Filesystem preview/execution and TUI modal rendering are deferred to Phase 11/12.

</deferred>
