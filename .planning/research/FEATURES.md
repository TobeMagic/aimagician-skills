# Feature Research

**Domain:** personal cross-CLI skills repository and deployment toolkit
**Researched:** 2026-03-13
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| In-repo local skills directory | The repo must be the source of truth for self-authored skills | LOW | The user's explicit owned-skill path should remain stable and human-editable |
| Declarative source catalog | External skills must be addable without hand-editing install scripts each time | MEDIUM | Needs schema validation and support for GitHub or command-based sources |
| One-command install/sync | The core value is clone + run one command | MEDIUM | Must cover bootstrap, update, and re-run flows |
| Default all-target deployment | The user expects supported CLIs to be configured by default | MEDIUM | Requires per-target capability detection and a target allow/deny matrix |
| User-level installation | Skills should load automatically in the current user's environment | LOW | Path resolution must be correct on both Windows and Linux |
| Idempotent re-run behavior | Setup tools are expected to be safe to run repeatedly | MEDIUM | Requires overwrite policy, diffing, and minimal state tracking |
| Verification command | Users need a quick way to confirm installation worked | MEDIUM | Likely mix of filesystem checks and target CLI smoke checks |
| Graceful skip on unsupported capability | If a target does not support a feature, the installer must not fail the whole setup | LOW | Especially important for plugins and target-native transformations |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Unified source model across owned and external skills | Lets one repo manage everything without forcing vendoring | HIGH | Core differentiator of this project |
| Target adapter translation layer | Allows one normalized source to feed Codex, Claude, OpenCode, and Gemini despite format differences | HIGH | Especially valuable because Gemini is not a straight `SKILL.md` target |
| Capability-driven plugin installation | Lets plugin config live next to skills while remaining safe per target | MEDIUM | Useful without over-committing to universal plugin semantics |
| Dry-run install plan | Shows exactly what will be copied/changed before touching user homes | MEDIUM | Strong trust builder for repeated syncs |
| Lockfile/resolution manifest | Makes source updates and debugging reproducible | MEDIUM | Helpful once multiple third-party sources are involved |
| Doctor/report command | Gives users a single place to see path resolution, installed assets, skipped items, and warnings | MEDIUM | Strong fit for fresh-machine bootstrap scenarios |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Auto-running arbitrary third-party installer commands without guardrails | Feels convenient for external skills | High trust and security risk; hard to make reproducible | Use explicit source types, allowlists, and dry-run output |
| Mirroring every external skill repo into this repo by default | Feels like "one repo has everything" | Produces update drift and repository bloat | Keep external sources config-driven, with optional opt-in vendoring |
| Pretending all targets support the same abstraction | Simplifies marketing and CLI UX | Produces broken installs and confusing partial behavior | Expose per-target capabilities clearly |
| Cloud backend or registry for v1 | Sounds scalable | Not needed for a personal bootstrap tool and adds non-core complexity | Stay local-first with declarative files |

## Feature Dependencies

```text
[One-command install]
    -> requires -> [Source catalog]
    -> requires -> [Target capability matrix]
    -> requires -> [Adapter layer]

[Verification command]
    -> requires -> [Installed state manifest]
    -> enhances -> [One-command install]

[Plugin support]
    -> requires -> [Target capability matrix]
    -> conflicts -> [Assume file-copy-only architecture]

[Gemini support]
    -> requires -> [Translation adapter]
    -> requires -> [Target-native command/extension output]
```

### Dependency Notes

- **One-command install requires Source catalog:** the installer needs a normalized input model before it can plan anything.
- **One-command install requires Target capability matrix:** target behavior cannot stay implicit once plugins and Gemini support are included.
- **Verification command enhances One-command install:** it turns a copy operation into an actual acceptance test.
- **Plugin support conflicts with file-copy-only architecture:** plugin installation usually has more lifecycle than copying prompt files.
- **Gemini support requires a translation adapter:** official Gemini CLI docs center on `GEMINI.md`, commands, and extensions rather than `SKILL.md`.

## MVP Definition

### Launch With (v1)

- [ ] Local `skills/` directory for owned skills - this is the project's baseline asset model
- [ ] Declarative source catalog for third-party skills - needed to aggregate GitHub and command-based sources
- [ ] Install/sync command with default all-target behavior - the user's primary workflow
- [ ] Adapters for Codex, Claude, OpenCode, and Gemini - required because v1 coverage is explicit
- [ ] User-level path resolution for Windows and Linux - core compatibility requirement
- [ ] Verification command and install report - needed to confirm success by listing or checking installed assets
- [ ] Plugin schema with capability-based skip/install behavior - included because the user wants plugins where supported

### Add After Validation (v1.x)

- [ ] Dry-run with detailed diff output - add when the core install flow is stable
- [ ] Lockfile/resolution manifest - add when external sources become numerous
- [ ] Optional symlink mode - add when copy mode has already proved reliable

### Future Consideration (v2+)

- [ ] Source marketplace or discovery UI - not needed for a personal bootstrap repo
- [ ] Automatic periodic source update bot - useful later, but not core to first setup flow
- [ ] Multi-user/team policy controls - not part of the single-user v1 goal

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Local skills directory | HIGH | LOW | P1 |
| Source catalog | HIGH | MEDIUM | P1 |
| One-command install/sync | HIGH | MEDIUM | P1 |
| User-level path resolution | HIGH | MEDIUM | P1 |
| Target adapter layer | HIGH | HIGH | P1 |
| Verification command | HIGH | MEDIUM | P1 |
| Plugin schema and capability handling | MEDIUM | MEDIUM | P1 |
| Dry-run diff | MEDIUM | MEDIUM | P2 |
| Resolution lockfile | MEDIUM | MEDIUM | P2 |
| Symlink mode | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| User-level skill discovery | Claude Code supports user skills in `~/.claude/skills` | OpenCode supports user skills in `~/.config/opencode/skills` | Normalize owned/external assets and materialize into each target's expected location |
| Plugins/extensions | OpenCode supports plugin directories and multiple install paths | Gemini CLI supports extensions and commands rather than `SKILL.md` | Treat plugins/extensions as target-native capabilities, not universal copies |
| Local user instructions | Gemini CLI centers on `GEMINI.md` and commands | Codex and Claude rely on their own local conventions | Keep a common source model but allow target-native output |

## Sources

- https://docs.claude.com/en/docs/claude-code/skills
- https://opencode.ai/docs/skills
- https://opencode.ai/docs/plugins
- https://google-gemini.github.io/gemini-cli/docs/cli/commands/
- https://google-gemini.github.io/gemini-cli/docs/extensions/
- https://openai.com/index/codex-app/

---
*Feature research for: personal cross-CLI skills repository and deployment toolkit*
*Researched: 2026-03-13*
