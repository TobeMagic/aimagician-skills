# Phase 1: Catalog Foundation - Research

**Researched:** 2026-03-13
**Domain:** TypeScript CLI repository modeling, configuration schema design, and cross-target asset catalogs
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

**CRITICAL:** These decisions came from discuss-phase and must be honored by the planner.

### Locked Decisions
- Self-authored skills live under `skills/owned/<skill>/SKILL.md`
- Third-party skills are config-driven by default and should not be mirrored into the repository unless explicitly chosen later
- Skill identifiers use stable kebab-case slugs
- Catalog content is directory-based rather than one giant top-level file
- YAML is the primary human-maintained format
- Catalog entries are source-centric: one source record can describe one or more assets from that source
- The project keeps one canonical catalog rather than Windows/Linux or target-specific overlay catalogs in v1 foundation work
- Default behavior is "install to all supported targets"
- Overrides should support both source-level and asset-level target declarations
- Unsupported capabilities should use `skip + warn`, not hard failure
- Skills and plugins/extensions should use the same target expression style, but live in separate catalog sections

### Claude's Discretion
- Exact subdirectory names inside the catalog area
- Exact YAML field names and nesting, as long as they support the decisions above
- Whether unresolved external source version policy is represented as an optional field now or finalized during research/planning

### Deferred Ideas (OUT OF SCOPE)
- Exact default version pinning policy for external sources was left open and should be finalized during research/planning inside this phase

</user_constraints>

<research_summary>
## Summary

Phase 1 should be planned as a schema-first repository modeling phase, not as an installer phase. The best approach is to establish one normalized asset model that can represent owned skills, external sources, and future plugin/extension assets without forcing later phases to reinterpret the repository shape.

The project research already confirms that the target CLIs diverge in how they consume user-level assets. That makes Phase 1's job clear: define the repository layout, catalog structure, target declaration grammar, and validation boundaries in a way that later adapters can consume cleanly. The safest approach is a small TypeScript codebase with strong validation, YAML catalogs, and a source-centric registry with explicit target metadata.

**Primary recommendation:** Plan Phase 1 around three outputs: repository directory conventions, a normalized config schema, and fixture-backed validation for parsing and path rules.
</research_summary>

<standard_stack>
## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Node.js | 24.14.0 LTS | Runtime for bootstrap tooling | Aligns with `npx` distribution and cross-platform filesystem work |
| TypeScript | 5.9.3 | Typed implementation language | Strongly reduces schema and adapter drift |
| Zod | 4.3.6 | Schema validation | Standard fit for catalog/config validation before any file writes |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| fs-extra | 11.3.4 | Filesystem helpers | For directory setup and future safe copy behavior |
| fast-glob | 3.3.3 | File discovery | For scanning `skills/owned` and catalog directories |
| yaml | 2.8.2 | YAML parsing/stringify | For the human-maintained catalog format |
| @iarna/toml | 2.2.5 | TOML parsing | For future Codex config interaction and validation helpers |
| vitest | 4.1.0 | Test framework | For schema and fixture-based validation in this phase |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Zod | JSON Schema + Ajv | Ajv is stronger for formal schemas, but Zod is faster for TS-first iteration |
| Directory-based YAML catalogs | Single JSON file | JSON is simpler for tooling, but worse for long-term hand maintenance |
| Source-centric registry | Asset-per-entry registry | Asset-per-entry is explicit, but source metadata duplication grows quickly |

**Installation:**
```bash
npm install commander zod fs-extra fast-glob yaml @iarna/toml
npm install -D typescript vitest tsx tsup @types/node
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```text
skills/
  owned/
catalog/
  skills/
  plugins/
src/
  config/
  catalog/
  model/
  shared/
tests/
  fixtures/
```

### Pattern 1: Normalized Asset Model
**What:** Represent owned skills, third-party skill sources, and future plugin assets with one shared internal type system.
**When to use:** Immediately after catalog parsing.
**Example:**
```typescript
type AssetKind = "skill" | "plugin";

type CatalogAsset = {
  id: string;
  kind: AssetKind;
  targets?: string[];
  source?: string;
};
```

### Pattern 2: Schema-First Catalog Parsing
**What:** Validate YAML catalog files into typed objects before any planning or installation logic touches them.
**When to use:** Every catalog load.
**Example:**
```typescript
import { z } from "zod";

const SourceSchema = z.object({
  id: z.string().regex(/^[a-z0-9-]+$/),
  type: z.enum(["github", "command", "local"]),
  assets: z.array(z.object({
    id: z.string(),
    kind: z.enum(["skill", "plugin"]),
    targets: z.array(z.string()).optional()
  }))
});
```

### Pattern 3: Directory-Constrained Discovery
**What:** Discover owned skills only from locked repository roots such as `skills/owned/`.
**When to use:** During startup and validation.
**Example:**
```typescript
const ownedSkillPattern = "skills/owned/*/SKILL.md";
```

### Anti-Patterns to Avoid
- **Mixing owned and third-party content in one tree:** later source updates become ambiguous
- **Letting target-specific fields leak into the base catalog shape:** adapters should interpret target differences, not the core schema
- **Post-parse validation only in business logic:** invalid config should fail at the boundary
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing and emitting | Custom line-based parser | `yaml` | Comments, anchors, and formatting edge cases are not worth reimplementing |
| Deep config validation | Ad hoc `if` checks everywhere | Zod schemas | Gives clear errors and reusable typed parsing |
| File tree discovery | Manual recursive traversal everywhere | `fast-glob` | Cleaner pattern matching and fewer path bugs |

**Key insight:** This phase is mostly about boundaries. Off-the-shelf parsing and validation tools prevent the catalog model from becoming implicit and brittle.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Source Identity vs Asset Identity Drift
**What goes wrong:** A source record and the assets it provides start sharing unclear IDs, causing collisions and confusing target overrides.
**Why it happens:** Teams skip a clear distinction between source IDs and asset IDs.
**How to avoid:** Require a stable source ID plus stable per-asset IDs beneath it.
**Warning signs:** Repeated slugs or target overrides that cannot tell whether they apply to a source or asset.

### Pitfall 2: Catalog Shape Optimized for v1 Only
**What goes wrong:** The initial catalog works for owned skills but cannot express plugins or multi-asset sources cleanly.
**Why it happens:** The phase is scoped narrowly and people over-minimize the schema.
**How to avoid:** Keep the base model extensible enough for skill and plugin sections from day one.
**Warning signs:** Separate one-off fields start appearing for each new source type.

### Pitfall 3: Validation Added Too Late
**What goes wrong:** Invalid YAML or unsupported target names are only caught during later install phases.
**Why it happens:** Early planning treats catalog work as "just files".
**How to avoid:** Make parsing and validation an explicit deliverable in Phase 1.
**Warning signs:** The only way to validate config is by running the future installer.
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources and current ecosystem usage:

### Directory-rooted owned skill discovery
```typescript
// Source: project research recommendation built on fast-glob usage patterns
import fg from "fast-glob";

const ownedSkillFiles = await fg("skills/owned/*/SKILL.md", { dot: false });
```

### YAML catalog load
```typescript
// Source: yaml package usage pattern
import { parseDocument } from "yaml";

const doc = parseDocument(fileContents);
const raw = doc.toJS();
```

### Schema validation boundary
```typescript
// Source: Zod official package pattern
const parsed = SourceSchema.safeParse(raw);
if (!parsed.success) {
  throw new Error(parsed.error.issues.map(issue => issue.message).join("; "));
}
```
</code_examples>

<sota_updates>
## State of the Art (2024-2025)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Loose JSON config with manual checks | Schema-first typed config | Became common across TS tooling by 2024-2025 | Better errors and safer refactors |
| Single massive config files | Smaller domain-focused config surfaces | Ongoing | Better maintenance for human-edited repos |
| Assuming all AI CLIs consume the same local format | Adapter-aware local asset modeling | Became necessary as Gemini/extensions diverged | Catalogs should stay target-agnostic where possible |

**New tools/patterns to consider:**
- Typed catalog loaders with Zod-style schemas
- Source-centric registries that enumerate multiple assets cleanly

**Deprecated/outdated:**
- Implicit config inferred from directory guesses only
- Unvalidated freeform target strings
</sota_updates>

<open_questions>
## Open Questions

1. **What exact directory name should the catalog root use?**
   - What we know: the user wants a directory-based catalog, not one giant file
   - What's unclear: whether it should be `catalog/skills/*.yaml`, `catalog/sources/*.yaml`, or a similar variant
   - Recommendation: let the planner choose a clean convention as long as owned skills remain under `skills/owned/`

2. **Should version policy become an optional field in Phase 1?**
   - What we know: the user did not lock a default pinning strategy yet
   - What's unclear: whether Phase 1 should only reserve schema space for this or fully model it now
   - Recommendation: include optional version fields in the schema if it does not complicate the phase, but avoid forcing pinning behavior yet
</open_questions>

## Validation Architecture

Phase 1 should establish test infrastructure for schema and fixture validation:

- Use `vitest` as the baseline test framework
- Quick validation should cover catalog parsing and owned-skill discovery
- Full validation should cover fixture repositories and representative YAML catalogs
- Wave 0 should install test tooling if the repository is still empty

<sources>
## Sources

### Primary (HIGH confidence)
- https://nodejs.org/en/about/previous-releases - runtime baseline
- https://www.npmjs.com/package/zod - schema validation package version and usage
- https://www.npmjs.com/package/yaml - YAML parsing package version and usage
- https://www.npmjs.com/package/fast-glob - file discovery package version and usage
- https://www.npmjs.com/package/vitest - test framework version and usage
- D:/Growth_up_youth/repo/skills/.planning/research/SUMMARY.md - project-specific target and architecture findings

### Secondary (MEDIUM confidence)
- https://docs.claude.com/en/docs/claude-code/skills - confirms direct-skill target expectations that later phases must feed
- https://opencode.ai/docs/skills - confirms direct-skill target expectations that later phases must feed
- https://google-gemini.github.io/gemini-cli/docs/extensions/ - confirms why the catalog must stay extensible for non-`SKILL.md` targets

### Tertiary (LOW confidence - needs validation)
- Codex target-specific public docs are thinner; exact downstream adapter assumptions should be validated in later phases
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: TypeScript + schema validation for repository modeling
- Ecosystem: Zod, YAML, fast-glob, Vitest
- Patterns: normalized asset model, source-centric catalogs, directory-constrained discovery
- Pitfalls: identity drift, premature schema minimization, late validation

**Confidence breakdown:**
- Standard stack: HIGH - package/runtime versions verified
- Architecture: MEDIUM - derived from project research plus locked phase decisions
- Pitfalls: MEDIUM - strong patterns, but future adapter work may reveal extra constraints
- Code examples: MEDIUM - based on current library usage patterns rather than copied reference apps

**Research date:** 2026-03-13
**Valid until:** 2026-04-12
</metadata>

---
*Phase: 01-catalog-foundation*
*Research completed: 2026-03-13*
*Ready for planning: yes*
