# AImagician Skills

## What This Is

AImagician Skills is a personal skills repository and deployment toolkit for AI coding CLIs. It lets AImagician keep self-authored skills in-repo, register external skill sources from GitHub or install commands, and sync the supported skills into user-level directories for tools like Codex, Claude, OpenCode, and Gemini with a single command.

The product is for one primary user first: AImagician. The goal is to make a fresh machine setup trivial: clone the repo, run one bootstrap command, and have the preferred skills loaded by default in every supported CLI.

## Core Value

After cloning the repo, one command installs and updates the right skills into each supported CLI's user-level location with as little manual setup as possible.

## Requirements

### Validated

(None yet - ship to validate)

### Active

- [ ] Keep self-authored skills inside this repository under `skills/`
- [ ] Support external skill sources through configuration, including GitHub sources and command-based installers
- [ ] Provide one bootstrap command to install or update supported skills for supported CLIs
- [ ] Install to the current user's default skill locations so tools load them automatically
- [ ] Support both Windows and Linux in the same project

### Out of Scope

- Unsupported CLI plugin installation - skip instead of forcing incompatible behavior
- A hosted marketplace or web UI - local CLI-first workflow is the priority for v1
- Deep plugin lifecycle management across every CLI - plugin support is conditional and secondary to skills deployment

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
- **Install Scope**: Must install into the current user's directories - skills should load by default without project-local setup
- **Target Diversity**: Codex, Claude, OpenCode, and Gemini may have different skill and plugin directory conventions - the system must normalize this through configuration
- **Workflow**: Bootstrap should be one command after `git clone` - setup friction defeats the main purpose of the project
- **Repository Shape**: External skills should usually stay config-driven rather than mirrored - reduces maintenance and keeps the repo focused on owned assets

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Project lives in the `skills/` subdirectory as its own repository root | The user wants a dedicated skills project inside a larger workspace, not project planning at the workspace root | - Pending |
| Self-authored skills are stored in-repo under `skills/` | Owned skills should be versioned and maintained directly in the repository | - Pending |
| Third-party skills are primarily referenced through configuration | Avoids unnecessary vendoring while still allowing unified deployment | - Pending |
| v1 targets Codex, Claude, OpenCode, and Gemini | The user wants broad coverage immediately and expects the integration effort to be manageable | - Pending |
| Plugins are conditional by target support | Prevents brittle installs on CLIs that do not expose plugin support | - Pending |
| Verification is done by listing skills in each CLI | This matches the user's real acceptance test for successful installation | - Pending |

---
*Last updated: 2026-03-13 after initialization*
