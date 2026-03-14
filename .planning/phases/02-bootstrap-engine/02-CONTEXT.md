# Phase 2: Bootstrap Engine - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase turns the Phase 1 catalog model into an actual bootstrap workflow. It must give the repository a real CLI entrypoint, a target-selection UX, a user-level bootstrap workspace, and idempotent install planning that can be rerun safely on Windows and Linux.

It does not yet need to materialize assets into Codex, Claude Code, OpenCode, or Gemini homes. That direct target writing remains Phase 3 and Phase 4 work. Phase 2 is responsible for the reusable engine that those target adapters will call.

</domain>

<decisions>
## Implementation Decisions

### CLI and command surface
- The primary user-facing command in this phase should be `bootstrap`
- The command should default to all supported targets and allow explicit target filtering from the CLI
- The command output should be readable enough for a fresh-machine setup flow, even before target-specific writers exist

### Bootstrap engine behavior
- The engine should create a user-level workspace for manifests and staged bootstrap data
- Re-running bootstrap should update that workspace deterministically instead of appending duplicate state
- The engine should consume the Phase 1 catalog and normalization layer directly rather than inventing a second config path

### Cross-platform path policy
- Windows and Linux must be handled through one shared path abstraction
- Repo-local paths should stay separate from user-level bootstrap state paths
- The path model should leave room for later target-specific adapters without rewriting the bootstrap workspace rules

### Packaging expectations
- The package metadata should support an `npm` / `npx` execution path
- Phase 2 should add smoke coverage that proves the built CLI can execute a bootstrap run in a test harness

### Claude's Discretion
- Exact bootstrap workspace directory name under the user profile
- Exact manifest schema as long as it supports idempotent reruns
- Exact CLI subcommands and flag names beyond the required `bootstrap` and target selection flow

</decisions>

<specifics>
## Specific Ideas

- The user ultimately wants a one-command clone-and-run setup, so this phase should feel like a real bootstrap flow rather than a pure internal refactor
- The most valuable outputs here are a stable command surface and a stateful apply layer that later target adapters can reuse
- Since target-specific writes are deferred, this phase should stage normalized data into a user-level workspace and report the selected targets clearly

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/catalog/load-catalog.ts` already discovers owned skills and loads external YAML catalogs
- `src/catalog/normalize.ts` already turns active sources into target-aware internal assets
- `src/model/targets.ts` already defines supported targets and shared target selection helpers
- `src/shared/paths.ts` already centralizes repository-local paths

### Established Patterns
- Phase 1 introduced schema-first loading and fixture-backed tests
- Repository conventions and catalog boundaries are now stable, so Phase 2 can build engine behavior on top of them

### Integration Points
- Phase 2 should expose a reusable bootstrap runner that Phase 3 target adapters can call
- Packaging work here should preserve the current `aimagician-skills` bin entry and extend it into a real command surface

</code_context>

<deferred>
## Deferred Ideas

- Direct writes into Codex, Claude Code, and OpenCode homes stay in Phase 3
- Gemini-native output stays in Phase 4
- Plugin materialization stays capability-gated and remains Phase 4 work

</deferred>

---
*Phase: 02-bootstrap-engine*
*Context gathered: 2026-03-14*
