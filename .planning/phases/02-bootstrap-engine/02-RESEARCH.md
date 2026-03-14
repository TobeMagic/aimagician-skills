# Phase 2: Bootstrap Engine - Research

**Researched:** 2026-03-14
**Domain:** Node CLI bootstrap flows, user-level workspace state, and idempotent install planning
**Confidence:** MEDIUM

<research_summary>
## Summary

Phase 2 should be implemented as a thin CLI over a reusable bootstrap engine. The CLI should parse user intent, default target selection sanely, and hand off to an engine that loads the catalog, normalizes assets, stages a user-level workspace snapshot, and updates a manifest atomically enough for safe reruns.

The key architectural move is separating repository data from user-level bootstrap state. Phase 1 already established repository-local roots and normalized asset records. Phase 2 should add a second path layer for user state and keep the engine pure enough that Phase 3 adapters can reuse the plan/apply flow when they start writing into real target homes.

**Primary recommendation:** Plan Phase 2 around three outputs: command UX, bootstrap workspace + manifest, and packaging smoke coverage.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Purpose | Why it fits |
|---------|---------|-------------|
| Node.js `fs/promises` | workspace and manifest writes | already available, enough for current file operations |
| Node.js `os` + `path` | cross-platform user-level path resolution | avoids shell-specific behavior |
| TypeScript | command and manifest typing | preserves engine contracts for later adapters |

### Supporting
| Library | Purpose | When to use |
|---------|---------|-------------|
| `vitest` | CLI and engine verification | keep the phase inside the existing test harness |
| `fast-glob` | repo-side file discovery | already used by the catalog layer |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| hand-rolled CLI parsing | `commander` | `commander` is better long-term, but Phase 2 can stay small with a typed parser and add a framework later if needed |
| user-level workspace manifest | repo-local state file | repo-local state breaks the fresh-machine and multi-clone story |
| one-step direct target writes | target-agnostic staging first | staging is the safer dependency boundary because target adapters are still pending |
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Command -> Engine -> Report
The CLI should parse flags and print results, while the engine owns planning, workspace writes, and manifest updates.

### Pattern 2: User-Level Workspace Root
Bootstrap state should live under a user-level directory, not under the repo. A single path module should resolve Windows and Linux roots consistently.

### Pattern 3: Manifest-Backed Idempotence
Each bootstrap run should write a manifest describing selected targets, staged assets, and timestamps so the next run can replace state deterministically instead of duplicating it.

### Anti-Patterns to Avoid
- Reading CLI flags directly inside the engine
- Mixing repo-local and user-level paths in the same helper
- Appending staged state without a manifest or deterministic file naming
</architecture_patterns>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: CLI parser and engine drift
If target selection is parsed in multiple places, later adapters will disagree about defaults and overrides.

### Pitfall 2: Workspace path hardcoding
Using Windows-only or Linux-only path assumptions will break fresh-machine bootstrap.

### Pitfall 3: Re-run duplication
If staged files are appended under random names, repeated bootstrap runs become impossible to reason about.
</common_pitfalls>

## Validation Architecture

Phase 2 should keep validation inside Vitest and build on the Phase 1 harness:

- Quick checks should target CLI parsing and bootstrap engine behavior
- Full checks should include the full test suite plus a built CLI smoke run
- Packaging validation should include an `npm pack --dry-run` check before phase verification

<sources>
## Sources

### Primary (HIGH confidence)
- D:/Growth_up_youth/repo/skills/src/catalog/load-catalog.ts - current catalog boundary
- D:/Growth_up_youth/repo/skills/src/catalog/normalize.ts - normalized asset pipeline
- D:/Growth_up_youth/repo/skills/.planning/ROADMAP.md - phase goal and plan split
- D:/Growth_up_youth/repo/skills/.planning/REQUIREMENTS.md - Phase 2 requirement IDs

### Secondary (MEDIUM confidence)
- Existing Node.js and npm CLI packaging conventions already reflected in the repository setup

</sources>

---
*Phase: 02-bootstrap-engine*
*Research completed: 2026-03-14*
*Ready for planning: yes*
