# Project Research Summary

**Project:** AImagician Skills
**Domain:** personal cross-CLI skills repository and deployment toolkit
**Researched:** 2026-03-13
**Confidence:** MEDIUM

## Executive Summary

This project is best treated as a local-first installer/orchestrator, not just a content repository. The owned skills themselves can live in-repo, but the real product value is a normalized source catalog plus an adapter-driven sync engine that can install into each target CLI's user-level home with one command after clone.

Research supports a TypeScript/Node CLI distributed through npm because the desired UX is explicitly `npx ...@latest` style and the problem is mostly cross-platform filesystem work, schema validation, and target-specific translation. The biggest architectural risk is assuming every target works like Claude-style `SKILL.md`; official docs show that OpenCode and Claude are close to that model, while Gemini leans on commands, `GEMINI.md`, and extensions, and Codex support is real but less publicly documented than the others. The roadmap should therefore start with a normalized asset model and target capability matrix before implementation branches into adapters.

- Product type: personal bootstrap CLI plus curated skill repository
- Recommended approach: normalized catalog -> install planner -> target adapters -> verification
- Main risk: false abstraction across targets, especially for Gemini and plugins

## Key Findings

### Recommended Stack

Use a single TypeScript package on Node.js 24.14.0 LTS with strict schema validation and adapter isolation. Commander, Zod, fs-extra, fast-glob, and execa cover most of the core needs without over-engineering.

**Core technologies:**
- **Node.js**: runtime and distribution via npm/npx - matches the intended bootstrap UX
- **TypeScript**: typed config and adapter boundaries - reduces cross-target path mistakes
- **Commander**: CLI command surface - good fit for install/sync/verify/doctor flows
- **Zod**: config validation - catches bad source and target definitions before mutation

### Expected Features

The table stakes are straightforward: local skills, a source catalog, one-command install, user-level path writes, all-target defaults, and verification. The main differentiator is one normalized source model that can feed multiple target adapters without forcing every third-party skill into the repository.

**Must have (table stakes):**
- Local owned skills directory
- Config-driven external source registry
- One-command install/sync to user-level target directories
- Adapters for Codex, Claude, OpenCode, and Gemini
- Verification/doctor output after install

**Should have (competitive):**
- Capability-aware plugin handling
- Dry-run plan output
- Resolved source manifest or lockfile

**Defer (v2+):**
- Cloud registry or marketplace features
- Automated source update bots

### Architecture Approach

The architecture should be a small monolith with clean internal boundaries: repository assets, config normalization, install planner, per-target adapters, and apply/verify layers. This keeps the first version shippable while still acknowledging that Gemini and plugins require target-native behavior rather than blind copying.

**Major components:**
1. **Asset catalog** - owned skills plus third-party source definitions
2. **Install planner** - turns config into a deterministic action plan
3. **Target adapters** - materialize Codex, Claude, OpenCode, and Gemini outputs correctly
4. **Apply/verify layer** - writes files safely and proves the install worked

### Critical Pitfalls

1. **Assuming all targets consume `SKILL.md`** - prevent this with an explicit capability matrix and Gemini-specific adapter logic
2. **Hardcoded path assumptions** - centralize Windows/Linux path resolution
3. **Destructive re-runs** - keep manifests/backups and make sync idempotent
4. **Treating plugins like skills** - separate plugin lifecycle from prompt-only skill copying
5. **Untrusted external source execution** - keep source resolution explicit and traceable

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Core Catalog and Planning Engine
**Rationale:** Everything depends on a stable internal model.
**Delivers:** Config schema, owned-skill discovery, external source definitions, target capability matrix, and dry planning.
**Addresses:** core table-stakes install model
**Avoids:** target-format confusion and hardcoded paths

### Phase 2: Skills Install Adapters
**Rationale:** Once planning exists, direct skill targets can be implemented safely.
**Delivers:** Codex, Claude, and OpenCode skill sync plus install manifest tracking.
**Uses:** path resolution, planner, adapter registry
**Implements:** apply/verify core with safe re-runs

### Phase 3: Gemini and Plugin Handling
**Rationale:** Gemini and plugins are the main capability outliers.
**Delivers:** Gemini-native translation plus capability-aware plugin install/skip logic.
**Uses:** target adapter extension points
**Implements:** target-specific transformations rather than blind copies

### Phase 4: Verification, Bootstrap UX, and Packaging
**Rationale:** The product promise is clone + one command + confidence it worked.
**Delivers:** `npx` bootstrap UX, `doctor`, `list-targets`, verification reports, and documentation.
**Uses:** completed adapters and install manifest
**Implements:** actual user-facing finish quality

### Phase Ordering Rationale

- Planning and normalization must come first because all targets diverge.
- Direct-copy style targets should be implemented before Gemini translation to reduce moving parts.
- Plugin support should wait until the core skills path is stable.
- Verification and packaging close the loop on the user's real acceptance test.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** Codex target details should be validated against the active CLI/runtime because public docs are lighter than Claude/OpenCode/Gemini
- **Phase 3:** Gemini translation shape needs exact implementation choices between commands, `GEMINI.md`, and extensions

Phases with standard patterns (skip research-phase):
- **Phase 1:** config schema, normalization, and planning are conventional local CLI patterns
- **Phase 4:** packaging and doctor/report flows are straightforward once adapters exist

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Current package/runtime versions were verified |
| Features | MEDIUM | Strongly grounded in the user's workflow plus target docs |
| Architecture | MEDIUM | Derived from clear target differences and installer best practices |
| Pitfalls | MEDIUM | High-confidence themes, but Codex target details still need practical validation |

**Overall confidence:** MEDIUM

### Gaps to Address

- Codex target support should be validated with a real smoke test against the installed CLI because public path/config docs are thinner than the others.
- Gemini support needs a final decision on whether the first implementation writes commands, extensions, or both.

## Sources

### Primary (HIGH confidence)
- https://nodejs.org/en/about/previous-releases - Node.js LTS baseline
- https://docs.claude.com/en/docs/claude-code/skills - Claude Code skills model
- https://opencode.ai/docs/skills - OpenCode skills model
- https://opencode.ai/docs/plugins - OpenCode plugin model
- https://google-gemini.github.io/gemini-cli/docs/extensions/ - Gemini extension model
- https://google-gemini.github.io/gemini-cli/docs/cli/commands/ - Gemini command model
- https://google-gemini.github.io/gemini-cli/docs/core/persona/ - Gemini global `GEMINI.md` model

### Secondary (MEDIUM confidence)
- https://openai.com/index/codex-app/ - recent OpenAI statement that Codex uses skills
- Local observation from installed Windows user homes under `C:\Users\AImagician`

### Tertiary (LOW confidence)
- Public Codex documentation for exact user-level skill discovery paths remains thinner than the other targets and should be validated during implementation

---
*Research completed: 2026-03-13*
*Ready for roadmap: yes*
