# Phase 5: Verification and Release UX - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase turns the bootstrap tool into an operator-friendly release by adding commands that prove what is installed and whether the target wiring is healthy.

It must let the user list or inspect installed assets per target, run a doctor-style verification flow, and understand the workflow from the README without reading source code.

It does not need to introduce a new installation engine. Phase 5 should build on the manifest, target-home, and reporting primitives that now exist.

</domain>

<decisions>
## Implementation Decisions

### Verification command surface
- The existing CLI should grow additional subcommands instead of creating a second binary
- `list`, `inspect`, and `doctor` should be first-class commands alongside `bootstrap`
- Verification commands should support machine-readable output where the bootstrap command already does

### Verification source of truth
- Doctor should inspect live target homes plus the workspace manifest instead of shelling out to the target CLIs
- List and inspect should prefer filesystem-observable state so the user can confirm what is actually present under the current user profile
- Manifest-backed data should still be shown where it clarifies what this tool manages versus what merely exists on disk

### Release UX
- README should reflect the final supported behavior after Gemini and plugin work landed
- Bootstrap output should stay concise, while `inspect` and `doctor` carry the deeper details

### Claude's Discretion
- Exact command arguments and output formatting as long as the commands stay discoverable and scriptable
- Exact separation between live detection and manifest-managed state as long as doctor can explain mismatches clearly

</decisions>

<specifics>
## Specific Ideas

- The user explicitly said the simple verification path they care about is "list the skills when I use it", so `list` needs to be fast and obvious
- Phase 4 already writes enough structure to the manifest and target reports that doctor can validate filesystem presence without re-running bootstrap
- README currently documents bootstrap well, but it does not yet teach the final operator flow for listing, inspecting, and verifying installs

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/cli/parse-cli.ts` already has a compact argument parser that can be extended to multiple commands
- `src/bootstrap/manifest.ts` now tracks managed installs across skills, Gemini extensions, and plugins
- `src/bootstrap/target-homes.ts` already centralizes all user-level install roots needed for doctor and inspect flows
- `src/bootstrap/run-bootstrap.ts` already writes plan/report JSON into the workspace for later inspection

### Established Patterns
- Existing tests already use fake homes and fixture catalogs, which is the right pattern for doctor/list coverage too
- Human-readable CLI output lives in `src/cli/index.ts`, so Phase 5 should keep all terminal rendering centralized there

### Integration Points
- Phase 5 likely needs a target inspection layer below the CLI but above the filesystem
- Doctor can reuse the manifest plus target-home resolver to compare expected managed installs against live disk state
- README updates should align with the final command surface once the CLI is complete

</code_context>

<deferred>
## Deferred Ideas

- Fancy TUI output or colored dashboards remain out of scope
- Real target-CLI process invocation for verification remains optional; filesystem-based proof is enough for v1

</deferred>

---
*Phase: 05-verification-and-release-ux*
*Context gathered: 2026-03-14*
