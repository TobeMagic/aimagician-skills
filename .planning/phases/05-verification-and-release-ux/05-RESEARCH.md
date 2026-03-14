# Phase 5: Verification and Release UX - Research

**Researched:** 2026-03-14
**Domain:** operator-facing verification, inspection, and final CLI UX
**Confidence:** HIGH

<research_summary>
## Summary

Phase 5 should stay inside the tool's own state model. The project already knows target homes, managed install paths, and the latest bootstrap plan/report, so the most reliable v1 verification flow is: inspect target homes directly, compare what exists on disk against the manifest, and expose that through dedicated commands. This avoids coupling release verification to ever-changing external CLI commands while still giving the user concrete proof under their current profile.

The command surface can stay small. `list` should answer "what is present per target?", `inspect` should answer "what exactly is happening for this target?", and `doctor` should answer "is the managed wiring healthy right now?" The README then needs to document the end-to-end operator flow: clone, bootstrap, list, inspect, doctor.

**Primary recommendation:** build one shared inspection layer and expose it through `list`, `inspect`, and `doctor`, then update bootstrap help and README to make those commands the default verification story.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Purpose | Why it fits |
|---------|---------|-------------|
| Node.js `fs/promises` | inspect live target homes and manifest paths | already used throughout bootstrap |
| Node.js `path` | derive target-relative labels and roots | needed for cross-platform inspection output |
| TypeScript | typed CLI results and doctor status models | keeps command output stable and testable |

### Supporting
| Library | Purpose | When to use |
|---------|---------|-------------|
| Existing Vitest suite | command parsing and fake-home verification | the current harness already covers CLI and bootstrap behavior well |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| filesystem + manifest inspection | invoking each target CLI to list assets | brittle, slower, and tied to external command contracts |
| dedicated verification binary | extend current CLI | extra package surface without real user value |
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Shared Inspection Core
One module should scan target homes, load the manifest, and produce normalized inspection results. All three commands can then render or filter the same data differently.

### Pattern 2: Command-Specific Views over the Same Data
`list` should be concise, `inspect` should be detailed, and `doctor` should summarize pass/fail plus mismatches, but they should all read the same underlying inspection structure.

### Pattern 3: Keep Verification Honest
Doctor should distinguish between "managed install expected but missing" and "unmanaged content exists". That gives the user usable debugging signals without pretending this tool owns everything in those directories.

### Anti-Patterns to Avoid
- Re-running bootstrap from doctor just to infer current state
- Hiding unmanaged content completely when listing target homes
- Baking README examples that no longer match the implemented command surface
</architecture_patterns>

## Validation Architecture

Phase 5 should extend the existing CLI and fake-home test strategy:

- add parser and CLI rendering tests for `list`, `inspect`, and `doctor`
- add fake-home inspection tests that verify managed installs, unmanaged content, and missing-managed-path failures
- keep the compiled bootstrap smoke test green after command-surface expansion

<sources>
## Sources

### Primary (HIGH confidence)
- D:/Growth_up_youth/repo/skills/.planning/PROJECT.md - operator goal and v1 framing
- D:/Growth_up_youth/repo/skills/.planning/REQUIREMENTS.md - VER-01 through VER-03
- D:/Growth_up_youth/repo/skills/src/bootstrap/manifest.ts - managed install source of truth
- D:/Growth_up_youth/repo/skills/src/bootstrap/target-homes.ts - live target home locations
- D:/Growth_up_youth/repo/skills/src/bootstrap/run-bootstrap.ts - latest bootstrap report persistence
- D:/Growth_up_youth/repo/skills/src/cli/index.ts - current human-readable output layer
- D:/Growth_up_youth/repo/skills/tests/cli/bootstrap-command.test.ts - current CLI command testing pattern

</sources>

---
*Phase: 05-verification-and-release-ux*
*Research completed: 2026-03-14*
*Ready for planning: yes*
