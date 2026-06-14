# Phase 11: Previewed Managed Sync Engine - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Convert the Phase 10 resolved desired install state into a deterministic, previewable managed sync plan, then execute only confirmed operations for the current scope and selected CLI targets. This phase owns managed filesystem sync safety; TUI presentation of preview/report details belongs to Phase 12.

</domain>

<decisions>
## Implementation Decisions

### Preview and execution contract
- Sync must expose a pure preview operation list before filesystem writes.
- Preview operations must distinguish create, overwrite/update, remove, and skip outcomes.
- Existing sync behavior must reuse the same operation plan so preview and apply cannot drift.
- Existing bootstrap/run behavior must not regress: selected targets still sync, stale managed installs are removed, and manifest results remain compatible with current callers.

### Safety boundaries
- Sync may only remove paths previously recorded as Skillbee-managed installs and only when the destination is inside that target's allowed roots.
- Managed installs recorded outside allowed roots must be reported as skipped rather than removed.
- Manual files and unmanaged directories in CLI skill homes must survive cleanup.
- Unselected targets must remain untouched.

### Scope behavior
- Current global/project scope determines the manifest and desired install set before this phase receives sync inputs.
- Phase 11 should preserve scope separation from Phase 9 rather than introducing cross-scope manifest behavior.
- Command-source project-scope skip decisions come from Phase 10 eligibility and should appear as skip/explainable outcomes where surfaced.

### Claude's Discretion
- Exact TypeScript type names and internal helper decomposition are at Claude's discretion if the public preview/apply semantics stay stable.
- Exact ordering within operation groups may be deterministic and implementation-defined, but tests should cover the user-visible operation categories.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product requirements
- `.planning/ROADMAP.md` §Phase 11 — Phase goal, dependencies, and success criteria for previewed managed sync.
- `.planning/REQUIREMENTS.md` §Scope & Target Sync — SYNC-01 through SYNC-07 requirements.
- `docs/PRD.md` — v3 configuration orchestration and verified sync acceptance expectations.

### Upstream phase context
- `.planning/phases/09-configuration-scope-foundation/09-CONTEXT.md` — Scope-aware config and manifest separation decisions.
- `.planning/phases/10-source-eligibility-resolver/10-CONTEXT.md` — Eligibility, include/exclude, default-disabled, and skip reason decisions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/bootstrap/direct-target-sync.ts` contains managed install sync and should be the primary integration point for preview/apply planning.
- `src/bootstrap/source-resolution.ts` produces `ResolvedManagedInstall` records used as desired state.
- `src/bootstrap/manifest.ts` defines `BootstrapManifestManagedInstall`, the authority for previously managed installs.

### Established Patterns
- Sync planning is manifest-backed: stale removals are based on previous manifest records, not directory scans.
- Target safety is enforced with `allowedRootsByTarget` and selected target filtering.
- Bootstrap tests use temporary homes and fixture catalogs for offline verification.

### Integration Points
- `runBootstrap` consumes managed sync results to write manifests and target reports.
- Phase 12 TUI will consume preview/report capabilities rather than reimplement sync diff logic.

</code_context>

<specifics>
## Specific Ideas

The user explicitly asked to continue from the failing `planManagedInstallSync` test and implement preview operation lists while preserving existing sync behavior.

</specifics>

<deferred>
## Deferred Ideas

- Rich TUI preview modal and final Target × Skill report are Phase 12 concerns.
- Real global-directory acceptance is Phase 13.

</deferred>

---

*Phase: 11-previewed-managed-sync-engine*
*Context gathered: 2026-06-04*
