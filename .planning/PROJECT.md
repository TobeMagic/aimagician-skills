# AImagician Skills

## What This Is

AImagician Skills / Skillbee is a local-first personal skill configuration orchestrator for AI coding CLIs. It lets AImagician keep self-authored skills in-repo, register external skill sources from GitHub or install commands, persist user intent in YAML, preview safe sync plans, and install the resolved skill set into global or project-level CLI skill directories.

The product is for one primary user first: AImagician. The active v6.1 goal is
to stabilize certified physical-page assembly so a medium-capability Codex
agent can generate a reference-grade editable PPTX from a complete requirement
pack. The approved next milestone renames the specialized Skill to
`pptx-studio` and completely removes the `window-pptx` identity.

## Core Value

Skillbird resolves catalog defaults plus user YAML overrides into safe, previewed, repeatable sync plans. For v5.0, the same safety discipline extends to semantic PowerPoint planning, deterministic design selection, portable native-editable OOXML rendering, cross-engine verification, and hard-gated customer delivery.

## Requirements

### Validated

- [x] v4.0 Skillbird consolidation and install acceptance are shipped with audit evidence.
- [x] Phase 22 Linux/fake-COM safety slices have focused tests and independent review evidence.

### Active

- [ ] Require discussion-locked ProjectBriefPack v1 inputs and realistic source-bound scenario packs.
- [ ] Build a private, entitlement-aware template library with certified complete-work visual spines and TemplatePack v2.
- [ ] Use Codex GPT-5.5 medium for constrained narrative and visual selection without arbitrary design code or invented facts.
- [ ] Produce complete work-report, campus-competition, and academic-defense flagship decks.
- [ ] Ship only after portable engineering gates and three independent AI-only reference-parity reviews pass.

### Out of Scope

- Unsupported CLI plugin installation - skip instead of forcing incompatible behavior
- A hosted marketplace or web UI - local CLI-first workflow is the priority for v1
- Deep plugin lifecycle management across every CLI - plugin support is conditional and secondary to skills deployment


## Current Milestone: v6.1 Window-PPTX Physical Template Assembly

**Goal:** Prove that `gpt-5.6-terra` medium can select only eligible certified
pages and physically assemble a 15-slide work-report deck with complete OPC
closure, native editability, bounded package size, clean-room provenance, and
independent AI acceptance.

**Target features:**
- Correct per-slide template metadata and direct-use eligibility
- Deterministic role/capacity/semantic/style selection
- Owner-relative recursive OPC import and conservative dependency deduplication
- Native slot adaptation with immutable-fact and capacity guards
- Recursive relationship, lineage, size, editability, and portability QA
- Clean-room Codex generation plus three anonymous visual reviews and a fresh
  frozen-point completion audit

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
| v6.0 requires a Locked ProjectBriefPack | Content truth and unresolved client decisions must be settled before design | Active |
| v6.0 uses complete works as visual spines | Reference-grade rhythm and motif continuity cannot come from isolated generic cards | Active |
| v6.0 uses GPT-5.5 medium inside constrained schemas | Strong visual judgment is allowed without raw coordinates, OOXML, HTML, code, or invented facts | Active |
| v6.0 keeps portable native PPTX canonical | COM remains optional diagnostics and cannot block daily delivery | Active |
| v6.0 gates promotion on engineering plus independent AI evidence | Automatic scores alone previously concealed visible quality failures | Active |
| v6.1 permits only direct-use physical lineage for acceptance | Reference-only pages and generated visual fallbacks cannot prove template reuse | Active |
| The next milestone uses `pptx-studio` and removes `window-pptx` completely | The capability is a full design studio, not a Windows/COM-specific tool; dual public identities are explicitly rejected | Accepted |

---
*Last updated: 2026-08-08 after locking v6.1 physical assembly stabilization*
