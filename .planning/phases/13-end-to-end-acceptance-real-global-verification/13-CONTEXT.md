# Phase 13: End-to-End Acceptance & Real Global Verification - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove the v3 PRD end-to-end through automated tests, project-scope acceptance, command-source project-scope skips, documentation checklist closure, and a clearly gated real global-directory verification path. This phase verifies and closes gaps; it should not introduce new product capabilities beyond fixes required to pass acceptance.

</domain>

<decisions>
## Implementation Decisions

### Automated acceptance first
- Prioritize automated tests for include/exclude priority, default-disabled sources, project/global manifest isolation, selected-target sync, manual-file preservation, preview no-write behavior, and TUI helper behavior.
- Use project-scope temporary directories for filesystem acceptance wherever possible.
- Treat command-source project-scope skip behavior as an explicit acceptance item.

### Real global-directory verification gate
- Do not mutate real current-user CLI directories without explicit user confirmation.
- Provide a documented/manual checklist or dry-run path for real global acceptance after preview confirmation.
- If automation can safely run against temp homes, use temp homes; if it must touch actual `~/.claude`, `~/.codex`, etc., stop and ask.

### PRD closure
- Update `docs/PRD.md` acceptance/checklist sections so implemented and verified items have no unresolved gaps.
- Phase 13 can add verification notes or scripts if needed, but should avoid broad rewrites.

### Claude's Discretion
- Exact test file placement and helper names are at Claude's discretion if every ACC requirement is traceable.
- Minor implementation fixes discovered during acceptance may be made if they directly close Phase 13 gaps.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product requirements
- `.planning/ROADMAP.md` §Phase 13 — Phase goal and success criteria.
- `.planning/REQUIREMENTS.md` §Verification & Acceptance — ACC-01 through ACC-05.
- `docs/PRD.md` — v3 PRD checklist and acceptance expectations.

### Upstream phase outputs
- `.planning/phases/09-configuration-scope-foundation/09-VERIFICATION.md` — scope/config verification state.
- `.planning/phases/10-source-eligibility-resolver/10-VERIFICATION.md` — eligibility verification state.
- `.planning/phases/11-previewed-managed-sync-engine/11-VERIFICATION.md` — sync preview verification state.
- `.planning/phases/12-tui-orchestration-console/12-VERIFICATION.md` — TUI orchestration verification state.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/config/user-config.test.ts` covers scoped config behavior.
- `tests/manager/manager-operations.test.ts` covers project/global manager operations, eligibility, and reset behavior.
- `tests/bootstrap/direct-target-sync.test.ts` covers managed sync preview/apply behavior.
- `tests/tui/source-toggle.test.ts` and `tests/tui/group-filter.test.ts` cover TUI pure helpers.

### Established Patterns
- Acceptance tests use temporary directories and fixture catalogs to avoid modifying real user homes.
- Manager APIs accept platform overrides, projectDir, catalog overrides, and GitHub repo overrides for hermetic tests.
- Real global writes are sensitive and should be manually gated.

### Integration Points
- PRD checklist is in `docs/PRD.md`.
- Completion state is tracked by `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, and phase verification artifacts.

</code_context>

<specifics>
## Specific Ideas

Use a final acceptance test suite or targeted additions to existing tests rather than a large new harness. Document real global verification as a gated checklist unless the user explicitly approves running it against actual home directories.

</specifics>

<deferred>
## Deferred Ideas

- Future hardening can add transactional copy/rename and richer global acceptance automation.
- Hosted marketplace, multi-user policy, and new target adapters remain out of scope.

</deferred>

---

*Phase: 13-end-to-end-acceptance-real-global-verification*
*Context gathered: 2026-06-04*
