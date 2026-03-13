# Pitfalls Research

**Domain:** personal cross-CLI skills repository and deployment toolkit
**Researched:** 2026-03-13
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Assuming All Targets Consume `SKILL.md`

**What goes wrong:**
The installer copies the same folder structure everywhere and silently produces non-working installs on targets that expect different native formats.

**Why it happens:**
Claude-style skills feel like the common denominator, so teams over-generalize.

**How to avoid:**
Create an explicit capability matrix and keep Gemini-specific translation in its own adapter.

**Warning signs:**
- Target support is described as "just copy it" without a format check
- Gemini is treated as a plain skill folder target
- Plugin and skill handling share one filesystem path abstraction

**Phase to address:**
Phase 1 and Phase 2

---

### Pitfall 2: Hardcoded Path Assumptions

**What goes wrong:**
Installs work on one machine but fail on Linux, WSL, or alternative home/config layouts.

**Why it happens:**
Developers test only on their own workstation and bake path strings into scripts.

**How to avoid:**
Centralize homedir/XDG resolution, keep path policy in adapters, and cover Windows plus Linux fixtures in tests.

**Warning signs:**
- Path separators appear in config examples
- Install logic shells out to `cp` or `mkdir -p` as the core implementation
- Verification only checks local developer paths

**Phase to address:**
Phase 1

---

### Pitfall 3: Destructive Re-Runs Without State

**What goes wrong:**
Re-running setup overwrites user-customized content or leaves stale artifacts behind.

**Why it happens:**
The first version optimizes for "copy files fast" and skips manifests, backups, and diffing.

**How to avoid:**
Track what the installer wrote, back up touched files when needed, and make sync idempotent by design.

**Warning signs:**
- No manifest or report of previous install outputs
- Update flow is described as "delete target dir and re-copy"
- There is no dry-run or doctor command

**Phase to address:**
Phase 2 and Phase 4

---

### Pitfall 4: Treating Plugins Like Skills

**What goes wrong:**
Plugin installs fail or partially work because target-specific lifecycle and config requirements are ignored.

**Why it happens:**
From the user's point of view both are "things I want loaded", but the target CLIs separate them.

**How to avoid:**
Define plugins as a separate asset kind with capability-gated install behavior and explicit skip messages.

**Warning signs:**
- One config field is used for both skills and plugins with no target metadata
- Plugin install has no verification path
- The installer cannot explain why a plugin was skipped

**Phase to address:**
Phase 3

---

### Pitfall 5: Untrusted External Source Execution

**What goes wrong:**
The bootstrap command runs arbitrary third-party commands or pulls drifting content with no traceability.

**Why it happens:**
Convenience wins over reproducibility during early prototypes.

**How to avoid:**
Prefer GitHub/file sources, require explicit command-based source definitions, and record resolved versions or commit SHAs.

**Warning signs:**
- External command sources are allowed without review or prompt
- There is no lockfile or resolution report
- Verification cannot tell which source revision was installed

**Phase to address:**
Phase 2 and Phase 4

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Copy-only install with no manifest | Faster first implementation | Hard to update, rollback, or verify | Only for the first local spike, not for shipped v1 |
| One generic target adapter | Less code initially | Becomes unreadable and brittle fast | Never once Gemini/plugin support is included |
| No source pinning | Minimal config | Drift and hard-to-reproduce installs | Acceptable only for owned local skills |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GitHub sources | Always clone latest default branch | Allow pinning to commit/tag and record the resolved revision |
| npm-delivered bootstrap | Assuming shell behavior is the same on PowerShell and bash | Keep core logic in Node APIs, not shell fragments |
| Target CLI verification | Trusting file copies as proof of success | Add CLI-aware checks where available and clear fallback checks otherwise |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Re-fetch every external source on every run | Slow setup after a few sources | Add cache or source resolution manifest | Around 10+ external sources |
| Deep target rescans for every action | Install time grows non-linearly | Plan once, then apply in batches | Around dozens of assets per target |
| Rewriting full trees for tiny updates | Stale state and slow syncs | Diff target contents before applying | Noticeable after repeated updates |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Executing arbitrary external installer commands by default | Remote code execution in user context | Require explicit trust and surface command previews |
| Overwriting user-level config files blindly | Breaks existing local setups | Scope writes narrowly and back up touched files |
| Treating third-party prompts as trusted | Supply-chain style prompt injection risk | Track source origin and keep external skills opt-in |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Silent skips | User thinks setup worked when it did not | Print per-target applied/skipped summaries |
| Hidden path logic | User cannot debug missing skills | Add `doctor` and `show-paths` commands |
| Target names that do not match actual behavior | Confusion and false expectations | Document exact capability differences per target |

## "Looks Done But Isn't" Checklist

- [ ] **Codex support:** verify the installer writes into the actual active user home and not just a guessed path
- [ ] **Claude support:** verify the target skill appears where Claude Code expects it and can be discovered
- [ ] **OpenCode support:** verify skills and plugins go to their correct directories independently
- [ ] **Gemini support:** verify the generated output uses Gemini-native commands/extensions rather than raw `SKILL.md`
- [ ] **Update flow:** verify re-running install does not duplicate or orphan assets

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong target format | MEDIUM | Add adapter translation, clean bad output, re-run sync |
| Path mismatch | LOW | Fix centralized path resolution and re-run verification |
| Destructive overwrite | HIGH | Restore from backups or reinstall target-specific assets from manifest |
| Unsafe external source | HIGH | Remove source, revoke trust, and reinstall from known-good revisions |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Assuming all targets consume `SKILL.md` | Phase 1 | Capability matrix exists and Gemini is handled separately |
| Hardcoded path assumptions | Phase 1 | Windows and Linux path tests pass |
| Destructive re-runs without state | Phase 2 | Manifest-backed re-run produces clean diff |
| Treating plugins like skills | Phase 3 | Plugin plan shows target-specific behavior and skip reasons |
| Untrusted external source execution | Phase 4 | Source revisions and command trust are visible in reports |

## Sources

- https://docs.claude.com/en/docs/claude-code/skills
- https://opencode.ai/docs/skills
- https://opencode.ai/docs/plugins
- https://google-gemini.github.io/gemini-cli/docs/extensions/
- https://google-gemini.github.io/gemini-cli/docs/cli/commands/
- https://openai.com/index/codex-app/
- Local environment observations from `C:\Users\AImagician\.codex`, `C:\Users\AImagician\.claude`, and `C:\Users\AImagician\.gemini`

---
*Pitfalls research for: personal cross-CLI skills repository and deployment toolkit*
*Researched: 2026-03-13*
