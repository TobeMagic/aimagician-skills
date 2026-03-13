# Phase 1: Catalog Foundation - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase defines how owned skills, third-party source definitions, and target metadata are organized in the repository. It does not implement installation yet; it locks the repository and catalog shape that later phases will build on.

</domain>

<decisions>
## Implementation Decisions

### Repository layout
- Self-authored skills live under `skills/owned/<skill>/SKILL.md`
- Third-party skills are config-driven by default and should not be mirrored into the repository unless explicitly chosen later
- Skill identifiers use stable kebab-case slugs

### Source catalog structure
- Catalog content is directory-based rather than one giant top-level file
- YAML is the primary human-maintained format
- Catalog entries are source-centric: one source record can describe one or more assets from that source
- The project keeps one canonical catalog rather than Windows/Linux or target-specific overlay catalogs in v1 foundation work

### Target mapping rules
- Default behavior is "install to all supported targets"
- Overrides should support both source-level and asset-level target declarations
- Unsupported capabilities should use `skip + warn`, not hard failure
- Skills and plugins/extensions should use the same target expression style, but live in separate catalog sections

### Claude's Discretion
- Exact subdirectory names inside the catalog area
- Exact YAML field names and nesting, as long as they support the decisions above
- Whether unresolved external source version policy is represented as an optional field now or finalized during research/planning

</decisions>

<specifics>
## Specific Ideas

- The repository is a personal bootstrap system first, not a public marketplace
- Third-party sources should stay lightweight by default; configuration is preferred over vendoring
- The user expects later phases to turn this structure into a clone-and-run setup flow with default all-target deployment

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- No implementation code exists yet; this phase is starting from planning artifacts only

### Established Patterns
- The project is greenfield, so Phase 1 can define the initial repository and catalog conventions
- Existing planning documents already assume a clear split between owned assets, external sources, and target adapters

### Integration Points
- Later phases will consume this structure to power the bootstrap engine and target adapters
- Research already identified Codex, Claude Code, OpenCode, and Gemini as the core target set to support

</code_context>

<deferred>
## Deferred Ideas

- Exact default version pinning policy for external sources was left open and should be finalized during research/planning inside this phase

</deferred>

---
*Phase: 01-catalog-foundation*
*Context gathered: 2026-03-13*
