# Phase 4: Gemini and Plugins - Research

**Researched:** 2026-03-14
**Domain:** Gemini-native output plus capability-aware plugin and extension handling
**Confidence:** MEDIUM

<research_summary>
## Summary

Phase 4 should stop treating Gemini as a deferred placeholder and instead install Gemini-compatible output through the Gemini CLI extension model. The most practical target-native shape is a generated extension directory under the user's `.gemini/extensions` home with a `gemini-extension.json` manifest and copied repository skill content bundled as agent skills. That keeps the current repository skill model intact while still using Gemini's documented native load path.

Plugin handling should become target-capability driven instead of all-or-nothing. OpenCode has a documented user-level global plugins directory, so it is the strongest direct plugin target. Claude Code exposes plugin settings and discovery flows, but current documentation emphasizes marketplace configuration and explicit consent, which makes blind non-interactive installation a bad fit for this phase. The safe implementation path is: support direct plugin installs where the target exposes a stable filesystem contract, and emit explicit skip reasons where the target requires interactive or marketplace-managed consent.

**Primary recommendation:** split Phase 4 into three concerns: Gemini target-home + extension generation, capability-aware plugin planning/reporting, and concrete plugin apply behavior for targets with stable user-level install paths.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Purpose | Why it fits |
|---------|---------|-------------|
| Node.js `fs/promises` (`mkdir`, `cp`, `rm`, `writeFile`, `readdir`) | Gemini extension generation and plugin copy/sync | already powers the Phase 3 direct-sync path |
| Node.js `path` | target-home and destination layout | required for Windows and Linux user-level installs |
| TypeScript | capability matrix, manifest evolution, report typing | keeps target-specific behavior explicit and testable |

### Supporting
| Library | Purpose | When to use |
|---------|---------|-------------|
| Existing manifest writer/reader | track managed Gemini/plugin installs across reruns | reuse instead of creating a parallel state store |
| `vitest` | fake-home bootstrap verification | already covers direct target sync and command-source behavior |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Generated Gemini extension directories | writing one giant `~/.gemini/GEMINI.md` | loses per-skill structure and does not map cleanly from repository assets |
| capability-aware plugin routing | pretending every plugin can be copied like a skill | hides target differences and makes skips impossible to explain |
| OpenCode file-copy installs | shelling out to target CLIs for every plugin | less deterministic and harder to test in isolated fake homes |
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Target-Native Output Per Capability
Skill-folder targets can keep using directory sync, Gemini should use generated extensions, and plugin-capable targets should use their documented plugin home instead of reusing the skill installer path.

### Pattern 2: Capability Matrix Drives Install or Skip
Each target should resolve capability support for `skill`, `plugin`, and `extension` work before apply begins. Unsupported or non-automatable combinations should show explicit skip reasons in reports.

### Pattern 3: Manifest-Backed Managed Installs Beyond Skills
The Phase 3 manifest already tracks managed direct installs. Phase 4 should extend that model to Gemini extensions and plugin destinations so reruns remain idempotent and safe.

### Anti-Patterns to Avoid
- Reusing the skill-folder sync path for Gemini without generating a native extension shape
- Claiming Claude plugins are installed when the documented flow still depends on marketplace configuration or consent
- Dropping plugin installs outside manifest tracking and then being unable to prune stale managed content safely
</architecture_patterns>

<capability_matrix>
## Target Capability Findings

### Gemini CLI
- Official docs describe personal context under `~/.gemini/GEMINI.md`, but extensions live under `~/.gemini/extensions`
- Official extension docs require a `gemini-extension.json` manifest and support bundling agent skills inside the extension
- This makes Gemini extension generation the cleanest mapping from repository-managed skills to Gemini-native output

### OpenCode
- Official docs describe a global plugins directory at `~/.config/opencode/plugins`
- That gives the project a stable user-level destination for plugin assets without inventing a marketplace abstraction

### Claude Code
- Official docs expose plugin settings like `enabledPlugins` and `extraKnownMarketplaces`
- Official docs also mention discovery and installation through the plugin manager plus consent-driven marketplace flows
- That is enough to model support metadata and explicit skips, but not enough to justify silent file-copy installation claims for this phase
</capability_matrix>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Conflating Gemini skills with a top-level `GEMINI.md`
Gemini supports global context files, but repository-managed skills need per-asset structure. A generated extension package matches that better.

### Pitfall 2: Treating plugin assets like skills
OpenCode plugins and Claude marketplace plugins do not share the same lifecycle as copied `SKILL.md` directories.

### Pitfall 3: Reporting only success or failure
Phase 4 needs explicit skips. Without them, users cannot tell whether a plugin was ignored because the target lacks the capability or because automation is intentionally deferred.
</common_pitfalls>

## Validation Architecture

Phase 4 should extend the existing isolated-home Vitest strategy:

- add fake-home Gemini tests that verify generated extension manifests and copied skill payloads under `.gemini/extensions`
- add plugin-focused tests that cover OpenCode plugin destinations plus explicit skip reporting for unsupported or deferred target/capability combinations
- keep using workspace and GitHub override hooks so tests never depend on the real user profile or live network clones

<sources>
## Sources

### Primary (HIGH confidence)
- https://geminicli.com/docs/extensions/extension-reference/ - Gemini extension manifest, load path, and bundled agent-skill model
- https://geminicli.com/docs/core/cli-config/ - Gemini home/config conventions including `.gemini`
- https://opencode.ai/docs/plugins/ - OpenCode global plugin directory and plugin structure
- https://docs.anthropic.com/en/docs/claude-code/settings - Claude Code plugin-related settings and consent-driven marketplace notes
- D:/Growth_up_youth/repo/skills/src/bootstrap/run-bootstrap.ts - current deferred Gemini path and target reporting
- D:/Growth_up_youth/repo/skills/src/bootstrap/target-homes.ts - existing direct target-home resolver
- D:/Growth_up_youth/repo/skills/src/bootstrap/direct-target-sync.ts - current manifest-backed directory sync implementation
- D:/Growth_up_youth/repo/skills/src/model/targets.ts - capability matrix primitives already present
- D:/Growth_up_youth/repo/skills/src/model/assets.ts - current asset kinds and normalized asset shape
- D:/Growth_up_youth/repo/skills/tests/bootstrap/direct-target-sync.test.ts - isolated fake-home coverage pattern

### Secondary (MEDIUM confidence)
- https://code.claude.com/docs/en/plugins - Claude Code plugin discovery and install workflow details

</sources>

---
*Phase: 04-gemini-and-plugins*
*Research completed: 2026-03-14*
*Ready for planning: yes*
