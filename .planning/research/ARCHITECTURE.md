# Architecture Research

**Domain:** personal cross-CLI skills repository and deployment toolkit
**Researched:** 2026-03-13
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```text
+--------------------------------------------------------------+
|                      Repository Assets                       |
|  local skills/ | source catalog | plugin catalog | presets   |
+--------------------------------------------------------------+
                |                     |                   |
                v                     v                   v
+--------------------------------------------------------------+
|                  Config + Normalization Layer                |
| resolve config -> validate schema -> normalize source model  |
+--------------------------------------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|                    Install Planning Engine                   |
| discover targets -> compute install plan -> detect skips     |
+--------------------------------------------------------------+
              |                  |                 |
              v                  v                 v
+----------------+ +----------------+ +----------------------+
| Codex Adapter  | | Claude Adapter | | OpenCode Adapter     |
+----------------+ +----------------+ +----------------------+
              \                  |                 /
               \                 |                /
                \                v               /
                 \     +--------------------+   /
                  ---->| Gemini Adapter     |<--
                       +--------------------+
                               |
                               v
+--------------------------------------------------------------+
|                 Filesystem Apply + Verify Layer              |
| backup/copy/write -> manifest -> target checks -> report     |
+--------------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Repository assets | Own local skills and source definitions | Versioned files under `skills/`, `catalog/`, and optional `plugins/` |
| Config + normalization | Turn mixed source definitions into one internal model | Zod-validated config loaders plus source resolvers |
| Install planning engine | Decide what to install, skip, update, or transform | Pure planning functions that return a deterministic install plan |
| Target adapters | Translate internal assets into target-native output | One adapter module per CLI |
| Apply + verify | Perform filesystem changes and acceptance checks | Copy/write engine with manifest tracking and smoke-test helpers |

## Recommended Project Structure

```text
skills/
  owned/                  # self-authored skills stored in-repo
catalog/
  skills.{json,yaml}      # external skill source definitions
  plugins.{json,yaml}     # optional plugin source definitions
src/
  cli/                    # command entrypoints
  config/                 # schema, config loading, path resolution
  sources/                # source resolvers (local, github, command)
  planner/                # install planning and diff logic
  adapters/
    codex/                # Codex-specific output rules
    claude/               # Claude-specific output rules
    opencode/             # OpenCode-specific output rules
    gemini/               # Gemini-specific output rules
  apply/                  # filesystem mutations, backup strategy
  verify/                 # list/check/doctor commands
  shared/                 # normalized types, logging, helpers
fixtures/
  targets/                # fake target homes for integration tests
scripts/
  bootstrap/              # packaging or release helpers
```

### Structure Rationale

- **`skills/` and `catalog/`:** separates owned assets from external source metadata.
- **`planner/` before `adapters/`:** keeps install logic deterministic and testable before any file writes happen.
- **`adapters/` per target:** prevents target-specific branches from leaking across the whole codebase.
- **`fixtures/targets/`:** essential for Windows/Linux path tests and non-destructive integration coverage.

## Architectural Patterns

### Pattern 1: Normalized Asset Model

**What:** Convert local skills, GitHub sources, and command-based definitions into one internal asset shape.
**When to use:** Immediately after config loading.
**Trade-offs:** Adds upfront modeling work, but avoids duplicating logic across targets.

**Example:**
```typescript
type NormalizedAsset = {
  id: string;
  kind: "skill" | "plugin";
  source: "local" | "github" | "command";
  files: Array<{ path: string; content?: string; sourcePath?: string }>;
  targets: string[];
  capabilities: string[];
};
```

### Pattern 2: Adapter Registry

**What:** Register one adapter per target with explicit capability flags.
**When to use:** During install planning and apply phases.
**Trade-offs:** Slightly more boilerplate, much cleaner target isolation.

**Example:**
```typescript
type TargetAdapter = {
  id: "codex" | "claude" | "opencode" | "gemini";
  supportsSkills: boolean;
  supportsPlugins: boolean;
  plan(asset: NormalizedAsset, ctx: InstallContext): PlannedAction[];
};
```

### Pattern 3: Plan Then Apply

**What:** Compute a full action plan before writing any files.
**When to use:** Every install/update/sync command.
**Trade-offs:** Slightly more code than direct copy, but far safer and easier to debug.

## Data Flow

### Request Flow

```text
[User Command]
  -> [CLI Entry]
  -> [Config Loader]
  -> [Source Resolver]
  -> [Install Planner]
  -> [Target Adapter]
  -> [Filesystem Apply]
  -> [Verification]
  -> [Report Output]
```

### State Management

```text
[Config Files]
    -> [Normalization]
    -> [Install Manifest / Lockfile]
    -> [Verification Report]
```

### Key Data Flows

1. **Owned skill sync:** local repository skill -> normalized asset -> target adapter -> user home directory.
2. **External source sync:** catalog entry -> fetch/resolve -> normalized asset -> adapter translation -> user home directory.
3. **Verification flow:** installed manifest -> target-specific checker -> human-readable doctor output.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-50 skills | Single package and local manifest are enough |
| 50-300 assets | Add lockfile, cache, and better source resolution deduplication |
| 300+ assets or many sources | Introduce incremental sync and stronger source pinning |

### Scaling Priorities

1. **First bottleneck:** repeated external source fetches - fix with cache and resolution manifests.
2. **Second bottleneck:** adapter branching complexity - fix with explicit capability schemas and test fixtures.

## Anti-Patterns

### Anti-Pattern 1: Hardcoded Paths Everywhere

**What people do:** Scatter `~/.claude/skills`, `.codex`, and other paths throughout the codebase.
**Why it's wrong:** Path logic becomes impossible to audit and cross-platform bugs multiply.
**Do this instead:** Centralize path resolution and expose it through target adapters.

### Anti-Pattern 2: Generic Installer With Hidden Target Branches

**What people do:** Put all targets into one huge `install()` function with `if target === ...` branches.
**Why it's wrong:** Every new target breaks existing ones and tests become unreadable.
**Do this instead:** Keep a planner core plus per-target adapter modules.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| GitHub | Fetch source repositories or release assets | Needs auth and rate-limit handling for private or heavy use |
| npm registry | Distribute the bootstrap CLI | Best fit for `npx ...@latest` usage |
| Target CLIs | Verification and capability probing | Should be optional but useful for `doctor` and smoke tests |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| config -> planner | typed objects | Keep planner pure and deterministic |
| planner -> adapters | planned asset actions | Adapters should not fetch sources themselves |
| apply -> verify | manifest/report objects | Verification should consume what apply produced |

## Sources

- https://docs.claude.com/en/docs/claude-code/skills
- https://opencode.ai/docs/skills
- https://opencode.ai/docs/plugins
- https://google-gemini.github.io/gemini-cli/docs/extensions/
- https://google-gemini.github.io/gemini-cli/docs/cli/commands/
- https://google-gemini.github.io/gemini-cli/docs/core/persona/
- https://openai.com/index/codex-app/

---
*Architecture research for: personal cross-CLI skills repository and deployment toolkit*
*Researched: 2026-03-13*
