# AImagician Skills

## What This Is

AImagician Skills / Skillbee is a local-first personal skill configuration orchestrator for AI coding CLIs. It lets AImagician keep self-authored skills in-repo, register external skill sources from GitHub or install commands, persist user intent in YAML, preview safe sync plans, and install the resolved skill set into global or project-level CLI skill directories.

The product is for one primary user first: AImagician. The v3.0 goal is to make Skillbee trustworthy as a configuration console: catalog defaults remain searchable, user overrides decide what is eligible, project/global scopes are isolated, and real installs happen only after preview confirmation.

## Core Value

Skillbee resolves catalog defaults plus user YAML overrides into safe, previewed, repeatable sync plans for the selected CLI targets and scope.

## Requirements

### Validated

(None yet - ship to validate)

### Active

- [ ] Implement global/project independent scopes with separate override YAML and manifests
- [ ] Resolve source enablement plus skill include/exclude into an explainable install eligibility set
- [ ] Preserve searchable default-disabled sources such as `slavingia/skill` while preventing bulk install by default
- [ ] Add preview-confirmed sync that touches only selected CLI targets and only Skillbee-managed items
- [ ] Provide TUI controls for scope, source state, include/exclude, preview, and Target × Skill reports
- [ ] Run unit, integration, TUI, project-scope, and real global-directory acceptance against the PRD

### Out of Scope

- Unsupported CLI plugin installation - skip instead of forcing incompatible behavior
- A hosted marketplace or web UI - local CLI-first workflow is the priority for v1
- Deep plugin lifecycle management across every CLI - plugin support is conditional and secondary to skills deployment


## Current Milestone: v3.0 Configuration Orchestration & Verified Sync

**Goal:** Implement the full `docs/PRD.md` configuration-orchestration model and verify it end-to-end against project and real global CLI skill directories.

**Target features:**
- Layered config model: repo defaults, user override YAML, scope manifests, transient TUI state
- Global and project scope isolation with CLI-specific target paths
- Source visible/searchable state, default-disabled packages, and include/exclude resolution
- Preview-confirmed sync that touches only selected CLI targets and only Skillbee-managed items
- TUI controls and reports for scope, source state, eligibility reasons, preview, and Target × Skill outcomes
- Automated and real acceptance for manual-file preservation, project/global isolation, command-source global-only behavior, and real global installs

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

---
*Last updated: 2026-05-30 after starting v3.0 configuration orchestration milestone*
