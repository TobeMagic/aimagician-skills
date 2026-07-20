# AImagician Skills

## What This Is

AImagician Skills / Skillbee is a local-first personal skill configuration orchestrator for AI coding CLIs. It lets AImagician keep self-authored skills in-repo, register external skill sources from GitHub or install commands, persist user intent in YAML, preview safe sync plans, and install the resolved skill set into global or project-level CLI skill directories.

The product is for one primary user first: AImagician. The active v5.0 goal is to make the owned `window-pptx` skill a verified production engine while preserving the shipped Skillbird configuration and installation foundation.

## Core Value

Skillbird resolves catalog defaults plus user YAML overrides into safe, previewed, repeatable sync plans. For v5.0, the same safety discipline extends to semantic PowerPoint planning, deterministic design selection, native editable rendering, and hard-gated customer delivery.

## Requirements

### Validated

- [x] v4.0 Skillbird consolidation and install acceptance are shipped with audit evidence.
- [x] Phase 22 Linux/fake-COM safety slices have focused tests and independent review evidence.

### Active

- [ ] Complete Phase 22 real Windows PowerPoint safety and transactional acceptance.
- [ ] Compile versioned semantic DeckPlans through deterministic narrative, layout, capacity, and fallback rules.
- [ ] Provide eight themes and at least 72 governed layout variants across 24 page families.
- [ ] Render editable PowerPoint objects transactionally and validate package, COM, visual, and deck quality.
- [ ] Benchmark three generation arms across two ordinary models and 15 business scenarios.
- [ ] Ship only after the Windows acceptance matrix and customer-delivery hard gates pass.

### Out of Scope

- Unsupported CLI plugin installation - skip instead of forcing incompatible behavior
- A hosted marketplace or web UI - local CLI-first workflow is the priority for v1
- Deep plugin lifecycle management across every CLI - plugin support is conditional and secondary to skills deployment


## Current Milestone: v5.0 Window-PPTX Verified Production Engine

**Goal:** Move presentation quality from model improvisation into a versioned compiler, design system, layout/component registries, native renderer, bounded repair loop, and reproducible weak-model benchmark.

**Target features:**
- Strict dry-run, source/output protection, COM ownership, macro-security restoration, and transactional candidate promotion
- DeckPlan schema, 15 business archetypes, semantic layout ranking, capacity splitting, rhythm, and weak-model fallbacks
- Eight themes, 24 layout families, at least 72 deterministic variants, reusable components, and brand/font fallbacks
- Native editable charts, tables, diagrams, notes, links, controlled motion, and ratio-aware exports
- Five-layer quality inspection with bounded monotonic repair and stable report schemas
- Fifteen-scenario, three-arm weak-model benchmark plus final Windows PowerPoint acceptance

## Context

This project is intended to live in the `skills/` subdirectory of an existing workspace, as its own repository and planning root. The repository combines two concerns:

1. A home for AImagician's own skills, stored locally in the repo.
2. A configurable distribution layer for third-party or open-source skills that should not necessarily be vendored into the repository.

The expected usage flow is concrete and simple:

- Clone the repository on a new machine.
- Run one setup command, likely in an `npx ...@latest` style.
- Let the script read configuration, determine which targets are supported, and copy or install skills into each target CLI's user-level directories.
- Verify installation by listing available skills inside each CLI when needed.

Third-party skills may come from GitHub repositories or from existing install commands. For first release, skills are the primary concern; plugins can be modeled in config and installed only for CLIs that actually support them. For targets where support is missing, the installer should skip gracefully.

The user expects all major targets to be covered in v1 because the integration is mostly straightforward file copying once the path and format expectations are known.

## Constraints

- **Platform**: Must work on Windows and Linux - the installer needs cross-platform path handling and shell-safe behavior
- **Install Scope**: Must support both global user-level installs and project-level installs under the command's current working directory
- **Target Diversity**: Codex, Claude, OpenCode, and Gemini may have different skill and plugin directory conventions - the system must normalize this through configuration
- **Workflow**: Bootstrap should be one command after `git clone` - setup friction defeats the main purpose of the project
- **Repository Shape**: External skills should usually stay config-driven rather than mirrored - reduces maintenance and keeps the repo focused on owned assets
- **Safety**: Sync may only overwrite or remove Skillbee-managed items recorded in manifest or carrying a managed marker
- **Execution Gate**: TUI configuration changes persist immediately, but filesystem writes require an explicit preview confirmation

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Project lives in the `skills/` subdirectory as its own repository root | The user wants a dedicated skills project inside a larger workspace, not project planning at the workspace root | - Pending |
| Self-authored skills are stored in-repo under `skills/` | Owned skills should be versioned and maintained directly in the repository | - Pending |
| Third-party skills are primarily referenced through configuration | Avoids unnecessary vendoring while still allowing unified deployment | - Pending |
| v1 targets Codex, Claude, OpenCode, and Gemini | The user wants broad coverage immediately and expects the integration effort to be manageable | - Pending |
| Plugins are conditional by target support | Prevents brittle installs on CLIs that do not expose plugin support | - Pending |
| Verification is done by listing skills in each CLI | This matches the user's real acceptance test for successful installation | - Pending |
| Real global acceptance is allowed after preview confirmation | The user wants true end-to-end validation against current-user CLI skills directories | - Pending |
| `exclude` is the strongest eligibility rule | Prevents unwanted skills from being installed even when sources or includes would otherwise select them | - Pending |
| Project and global scopes are independent | The user wants current-project installs such as `<project>/.claude/skills` without affecting global CLI homes | - Pending |
| v3.0 treats Skillbee as configuration orchestration first | The PRD requires YAML intent, eligibility resolution, preview, and managed sync rather than direct install side effects | - Pending |
| v5.0 uses semantic DeckPlan input | Ordinary models should choose governed semantic roles, not invent raw coordinates, fonts, or colors | Active |
| v5.0 keeps native PowerPoint as production renderer | Client deliverables require editable objects and real PowerPoint compatibility | Active |
| v5.0 gates promotion on measurable evidence | Package validity, source integrity, editability, and reopen checks must precede delivery | Active |

---
*Last updated: 2026-07-20 after starting the v5.0 Window-PPTX Verified Production Engine milestone*
