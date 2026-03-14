# Phase 3: Direct Skill Targets - Research

**Researched:** 2026-03-14
**Domain:** direct skill-folder installs for Codex, Claude Code, and OpenCode
**Confidence:** MEDIUM

<research_summary>
## Summary

Phase 3 should extend the existing bootstrap engine with a copy-based direct sync layer for the three CLIs that already consume user-level skill directories directly. The safest structure is still plan-then-apply: resolve skill sources into concrete directories first, resolve target homes centrally, then copy managed skill directories into each selected target and prune only the directories the manifest previously owned.

The practical path model is stable enough to implement now. On this machine, Codex already uses `~/.codex/skills`, Claude Code already uses `~/.claude/skills`, and OpenCode configuration already lives under `~/.config/opencode`, which aligns with a native `~/.config/opencode/skills` target. Copy mode is the right v1 default because it keeps user-level installs self-contained and avoids symlink edge cases on Windows.

**Primary recommendation:** Build Phase 3 around three outputs: target-home resolution, source-to-directory materialization, and manifest-backed direct sync with prune protection for unmanaged content.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Purpose | Why it fits |
|---------|---------|-------------|
| Node.js `fs/promises` (`mkdir`, `cp`, `rm`, `readdir`) | target-home sync and prune behavior | already available and enough for directory copy workflows |
| Node.js `path` + existing platform helpers | cross-platform target-home resolution | keeps Windows and Linux logic centralized |
| TypeScript | manifest, resolver, and adapter typing | preserves clear contracts between planning and apply layers |

### Supporting
| Library | Purpose | When to use |
|---------|---------|-------------|
| Node.js `child_process` | GitHub source resolution through `git` | use for runtime repo materialization until a cache/lockfile phase exists |
| `vitest` | direct sync and prune verification | keeps the new behavior inside the current automated harness |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| copy mode installs | symlink or junction installs | link mode is useful later, but adds Windows-specific edge cases and is already a v2 requirement |
| manifest-scoped prune | delete all unknown directories under target homes | broad deletion is unsafe because users may already have unmanaged skills installed |
| fetch-inside-adapter | source resolution before adapters | adapters stay simpler when they only receive concrete source directories |
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Resolve Sources Before Target Writes
Owned skills and GitHub assets should become concrete source directories before target sync begins. Adapters should not fetch or infer repo structure on their own.

### Pattern 2: Central Target Registry
Codex, Claude Code, and OpenCode should share one typed target-home resolver so Phase 4 and Phase 5 can reuse the same paths for verification commands.

### Pattern 3: Manifest-Backed Managed Prune
The bootstrap manifest should record which target directories were managed in the previous run. The next run can then remove only those stale managed directories and leave user-owned content alone.

### Anti-Patterns to Avoid
- Hardcoding target directories inline inside `runBootstrap`
- Deleting every directory under a target skills root
- Copying only `SKILL.md` when the source skill directory may include scripts, templates, or references
</architecture_patterns>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Path assumptions that leak host OS behavior
If Windows and Linux target homes are assembled ad hoc, tests will pass on the current machine and fail elsewhere.

### Pitfall 2: Partial skill copies
Many skills depend on sibling files under the skill directory. Copying only `SKILL.md` breaks those skills silently.

### Pitfall 3: Pruning unmanaged user content
Removing directories purely because they are not selected in the current run is dangerous unless the manifest proves the tool created them previously.
</common_pitfalls>

## Validation Architecture

Phase 3 should keep verification inside Vitest and continue using temporary repositories plus isolated fake home directories:

- Quick checks should cover target-home resolution and direct sync behavior
- Integration checks should verify copy/update/prune semantics across multiple runs
- The built CLI smoke test should switch to an isolated fake home through environment overrides before Phase 3 apply logic lands

<sources>
## Sources

### Primary (HIGH confidence)
- Local installation inspection on 2026-03-14: `C:\Users\AImagician\.codex\skills`
- Local installation inspection on 2026-03-14: `C:\Users\AImagician\.claude\skills`
- Local installation inspection on 2026-03-14: `C:\Users\AImagician\.config\opencode`
- D:/Growth_up_youth/repo/skills/.planning/ROADMAP.md - Phase 3 goal and plan split
- D:/Growth_up_youth/repo/skills/.planning/REQUIREMENTS.md - Phase 3 requirement IDs
- D:/Growth_up_youth/repo/skills/src/bootstrap/run-bootstrap.ts - current apply entrypoint
- D:/Growth_up_youth/repo/skills/src/bootstrap/plan-bootstrap.ts - current plan shape

### Secondary (MEDIUM confidence)
- https://open-code.ai/docs/skills/ - corroborates native OpenCode skill directory conventions, but the page is marked unofficial

</sources>

---
*Phase: 03-direct-skill-targets*
*Research completed: 2026-03-14*
*Ready for planning: yes*
