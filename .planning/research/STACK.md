# Stack Research

**Domain:** personal cross-CLI skills repository and deployment toolkit
**Researched:** 2026-03-13
**Confidence:** MEDIUM

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Node.js | 24.14.0 LTS | Runtime for the bootstrap CLI | Best fit for `npx ...@latest` delivery, strong cross-platform filesystem APIs, and matches the ecosystem used by several target CLIs |
| TypeScript | 5.9.3 | Implementation language | Gives strong typing for adapter/config models and reduces mistakes across target-specific path rules |
| Commander | 14.0.3 | CLI argument parsing | Mature CLI ergonomics for commands like `install`, `sync`, `verify`, `list-targets`, and `doctor` |
| Zod | 4.3.6 | Config and manifest validation | Essential for validating source definitions, target capabilities, and plugin entries before touching user directories |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| fs-extra | 11.3.4 | Safe copy/remove/ensure-dir helpers | Use for idempotent sync operations, backups, and directory bootstrapping |
| fast-glob | 3.3.3 | File discovery | Use for scanning local `skills/`, target trees, and source manifests efficiently |
| yaml | 2.8.2 | YAML parsing | Use if the repository supports YAML-based catalogs or per-target definitions |
| @iarna/toml | 2.2.5 | TOML parsing | Use for Codex-related config integration when reading or patching `config.toml` |
| jsonc-parser | 3.3.1 | JSON-with-comments parsing | Useful for target configs that allow comments or trailing commas |
| execa | 9.6.1 | Process execution | Use for target-aware verification commands such as `codex`, `claude`, `opencode`, or `gemini` smoke checks |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| tsx 4.21.0 | Local TypeScript execution | Good for development scripts and fixture verification without a build step |
| tsup 8.5.1 | Build and bundle CLI package | Simple packaging for npm distribution across Windows and Linux |
| vitest 4.1.0 | Unit/integration tests | Strong fit for config validation, path resolution, and adapter matrix tests |

## Installation

```bash
# Core
npm install commander zod

# Supporting
npm install fs-extra fast-glob yaml @iarna/toml jsonc-parser execa

# Dev dependencies
npm install -D typescript tsx tsup vitest @types/node
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Node.js CLI | Python CLI | Use Python only if the project must share logic with an existing Python automation stack |
| TypeScript | Plain JavaScript | Use plain JS only for a throwaway internal script with no adapter growth expected |
| Single-package monorepo-style layout | Full workspace/monorepo | Use a full monorepo only if you later split adapters into independently published packages |
| Built-in fs + fs-extra | Shell scripts only | Use shell-only tooling only for target-specific helper scripts, not the core installer |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Shell-only installation logic | Breaks quickly across Windows/Linux and makes path quoting fragile | A Node.js installer with explicit path APIs |
| Assuming every target consumes `SKILL.md` the same way | Gemini CLI favors `GEMINI.md`, commands, and extensions; plugin models differ by target | A capability matrix plus adapter layer |
| Mirroring every third-party skill repo by default | Creates update drift and unnecessary repository bloat | Config-driven source references with optional vendoring |
| Symlink-only deployment as the default | Windows permissions and cross-filesystem behavior are brittle | Copy by default, optional link mode later |

## Stack Patterns by Variant

**If a target supports direct skill folders:**
- Use copy-based adapters that materialize canonical directories
- Because the deployment model is simple, debuggable, and easy to verify

**If a target uses commands/extensions instead of `SKILL.md`:**
- Use a translation adapter that emits target-native files from normalized source metadata
- Because one shared internal model is still possible even when the target format differs

**If a target supports plugins/MCP separately from skills:**
- Use a distinct plugin pipeline and schema
- Because plugin lifecycle, installation, and verification differ from prompt-only skills

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| node@24.14.0 LTS | typescript@5.9.3 | Stable modern baseline for current cross-platform CLI work |
| commander@14.0.3 | node@24.14.0 LTS | No special caveats for this project shape |
| vitest@4.1.0 | typescript@5.9.3 | Good fit for mixed unit and filesystem-heavy integration tests |

## Sources

- https://nodejs.org/en/about/previous-releases - verified current LTS baseline
- https://www.npmjs.com/package/typescript - verified TypeScript version
- https://www.npmjs.com/package/commander - verified Commander version
- https://www.npmjs.com/package/zod - verified Zod version
- https://www.npmjs.com/package/vitest - verified Vitest version
- https://www.npmjs.com/package/tsup - verified tsup version
- https://docs.claude.com/en/docs/claude-code/skills - verified Claude Code user-level skills model
- https://opencode.ai/docs/skills - verified OpenCode user-level skills model
- https://opencode.ai/docs/plugins - verified OpenCode plugin model and directories
- https://google-gemini.github.io/gemini-cli/docs/extensions/ - verified Gemini extension model
- https://google-gemini.github.io/gemini-cli/docs/cli/commands/ - verified Gemini command model
- https://openai.com/index/codex-app/ - verified recent OpenAI references to skills in Codex
- Local observation: `C:\Users\AImagician\.codex`, `C:\Users\AImagician\.claude`, and `C:\Users\AImagician\.gemini` confirm current Windows user-level homes in this environment

---
*Stack research for: personal cross-CLI skills repository and deployment toolkit*
*Researched: 2026-03-13*
