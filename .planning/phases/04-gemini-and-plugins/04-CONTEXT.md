# Phase 4: Gemini and Plugins - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase adds the first Gemini-native install path and turns plugin or extension assets from catalog metadata into target-aware install behavior.

It must make Gemini a real output target instead of a deferred placeholder. It also needs a capability-aware plugin or extension pipeline so supported targets receive plugin-like assets through their native shape while unsupported targets are skipped explicitly.

It does not need to finish operator-facing list, inspect, or doctor UX. Those remain Phase 5 work.

</domain>

<decisions>
## Implementation Decisions

### Gemini target shape
- Gemini should stop being a deferred target in bootstrap results
- Gemini output should use Gemini CLI's native extension loading model instead of pretending `SKILL.md` can be copied directly
- Repository-managed skills targeted to Gemini should be transformed into Gemini-compatible extension directories during install
- Gemini installs should land under the current user's Gemini home rather than repository-local directories

### Plugin and extension handling
- Plugin assets remain declared separately from skill assets through `catalog/plugins/*.yaml`
- The installer should evaluate plugin or extension support per target instead of assuming every target consumes the same asset shape
- Targets that do not expose a stable automation path for plugin or extension assets should be skipped with explicit reasons
- Supported plugin or extension installs should be manifest-backed so repeated bootstrap runs can update managed installs safely

### Reporting and safety
- Bootstrap output should distinguish installed, deferred, and skipped plugin or extension work per target
- Skip reasons should be specific enough to explain whether the target lacks the capability entirely or the current project does not automate that target's native flow yet
- Existing managed skill sync behavior for Codex, Claude Code, and OpenCode must stay intact

### Claude's Discretion
- Exact generated Gemini extension file layout as long as it matches Gemini's native load model
- Exact capability-matrix representation as long as install and skip behavior stay deterministic
- Exact manifest additions and report wording as long as plugin or extension outcomes are inspectable

</decisions>

<specifics>
## Specific Ideas

- Gemini CLI documentation points to a user-level `.gemini/extensions` load path and a `gemini-extension.json` manifest, which is a better fit than forcing a `GEMINI.md`-only abstraction
- OpenCode already has a documented global plugins directory under the current user's config home, which makes it a strong candidate for the first real plugin target
- Claude Code plugin support exists, but the automation contract needs to stay honest if the native install path is marketplace- or consent-driven rather than a stable file-copy target

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/bootstrap/target-homes.ts` already resolves direct skill homes and should extend naturally into Gemini and plugin-capable homes
- `src/bootstrap/direct-target-sync.ts` already handles managed directory sync for skill targets and can likely be generalized or complemented for plugin-capable targets
- `src/catalog/load-catalog.ts`, `src/catalog/normalize.ts`, and `src/model/assets.ts` already separate skills from plugins at the catalog boundary
- `src/model/targets.ts` already exposes capability metadata that can grow into explicit plugin or extension support

### Established Patterns
- Phase 3 resolved concrete source directories before writing into target homes
- Phase 3 used fake user homes and workspace overrides for isolated tests instead of touching the real machine profile
- Bootstrap reporting already returns structured target reports and command reports, so Phase 4 should extend that output rather than introducing a separate reporting path

### Integration Points
- Gemini-native output likely belongs next to target-home resolution plus direct-target apply logic
- Plugin or extension capability checks likely belong in planning or apply code close to target reports
- Existing bootstrap and smoke tests should extend to cover Gemini output generation, plugin installs, and explicit skips

</code_context>

<deferred>
## Deferred Ideas

- User-facing list, inspect, and doctor commands remain Phase 5
- Link mode, revision locking, and source caching remain later work
- Any target-native Claude plugin flow that still depends on interactive approval can remain an explicit skip until the tool has a safe automation contract

</deferred>

---
*Phase: 04-gemini-and-plugins*
*Context gathered: 2026-03-14*
