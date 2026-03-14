# Phase 3: Direct Skill Targets - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase makes the bootstrap workflow write real skill directories into the current user's default homes for the direct skill-folder targets: Codex, Claude Code, and OpenCode.

It must turn owned and repository-resolved skill assets into concrete directories that those CLIs load automatically. It also needs idempotent sync behavior so re-running bootstrap updates managed skills and removes stale managed installs without touching unrelated user content.

It does not need to solve Gemini-native output, plugin installation, or link-mode installs. Those remain later-phase work.

</domain>

<decisions>
## Implementation Decisions

### Target homes and path policy
- Codex should install into the current user's `.codex/skills` directory
- Claude Code should install into the current user's `.claude/skills` directory
- OpenCode should install into the current user's `.config/opencode/skills` directory
- Target-home resolution should be centralized instead of scattering target paths across the bootstrap engine

### Direct skill sync behavior
- Phase 3 should copy concrete skill directories into target homes rather than introducing link mode
- Managed installs should be identified by skill directory name under each target's skills root
- Re-running bootstrap should replace managed skill directories deterministically and prune managed directories that are no longer selected
- Unmanaged directories already present in a target home must not be deleted

### Source resolution strategy
- Owned skills should sync from `skills/owned/<skill-id>`
- GitHub-backed skill assets should resolve to a concrete skill directory before any target adapter writes run
- Asset-level paths should support both explicit `.../SKILL.md` references and directory-style defaults based on the asset id
- Command-based sources can remain delegated installer actions when configured, but direct folder materialization is the required path for this phase

### Bootstrap integration
- The existing `runBootstrap` entrypoint should stay the single apply path
- The Phase 2 workspace manifest should grow to describe direct-target installs so Phase 3 can prune stale managed directories safely
- Default target selection must still allow `gemini`, but Gemini should remain an explicit non-direct skip until Phase 4 lands

### Claude's Discretion
- Exact internal module layout for source resolvers versus target adapters
- Exact manifest field additions as long as they support deterministic sync and safe pruning
- Exact CLI/reporting shape for showing synced versus deferred targets

</decisions>

<specifics>
## Specific Ideas

- Local installation inspection on this machine already shows `C:\Users\AImagician\.codex\skills` and `C:\Users\AImagician\.claude\skills` in active use
- Local installation inspection also shows OpenCode config rooted at `C:\Users\AImagician\.config\opencode`, so Phase 3 should treat `skills` under that root as the native OpenCode target
- The most important operator outcome is simple: clone repo, run bootstrap, then the target CLI can list skills immediately from its normal user-level location

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/bootstrap/run-bootstrap.ts` is already the central apply entrypoint
- `src/bootstrap/plan-bootstrap.ts` already converts catalog state into selected assets
- `src/catalog/load-catalog.ts` already exposes owned skills plus active external sources
- `src/catalog/normalize.ts` already carries target-aware external asset metadata
- `src/shared/platform.ts` already resolves cross-platform user-level state roots and should extend naturally into target-home resolution

### Established Patterns
- Phase 2 kept planning pure and pushed writes into the bootstrap layer
- Current tests already use temporary repositories and workspace overrides, so Phase 3 should add isolated fake home directories rather than touching real user homes in automation

### Integration Points
- Phase 3 should add a target-home resolver, a source-resolution layer for direct skill installs, and a direct-sync apply step under `runBootstrap`
- The CLI preview/reporting in `src/cli/index.ts` should expose enough Phase 3 output to show which direct targets were synced and which were deferred

</code_context>

<deferred>
## Deferred Ideas

- Gemini-native rendering and install behavior stay in Phase 4
- Plugin and extension installers stay in Phase 4
- Link mode, source caching, and locked revisions stay in later milestone work

</deferred>

---
*Phase: 03-direct-skill-targets*
*Context gathered: 2026-03-14*
