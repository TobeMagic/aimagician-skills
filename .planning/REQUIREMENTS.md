# Requirements: AImagician Skills

**Defined:** 2026-03-13
**Core Value:** After cloning the repo, one command installs and updates the right skills into each supported CLI's user-level location with as little manual setup as possible.

## v1 Requirements

### Repository

- [ ] **REPO-01**: User can keep self-authored skills inside this repository in a stable directory that the installer scans automatically
- [ ] **REPO-02**: User can add or update owned skills without editing installer source code

### Sources

- [ ] **SRC-01**: User can register an external GitHub skill source in configuration
- [ ] **SRC-02**: User can register an external command-based source in configuration
- [ ] **SRC-03**: User can enable or disable an individual external source without deleting its definition
- [ ] **SRC-04**: User can declare which target CLIs each skill or source should deploy to

### Installation

- [ ] **INST-01**: User can clone the repository and run one bootstrap command to install configured assets
- [ ] **INST-02**: User can re-run the bootstrap command to update existing installs without duplicating installed assets
- [ ] **INST-03**: User can run the same project on Windows and Linux with the same repository configuration
- [ ] **INST-04**: User can install into the current user's default target locations so skills load automatically
- [ ] **INST-05**: User can invoke the bootstrap workflow through an npm-executed command in an `npx ...@latest` style

### Targets

- [ ] **TARG-01**: User can install configured skills into Codex
- [ ] **TARG-02**: User can install configured skills into Claude Code
- [ ] **TARG-03**: User can install configured skills into OpenCode
- [ ] **TARG-04**: User can install Gemini-compatible output even when the source asset originates as a repository skill
- [ ] **TARG-05**: User can default installation to all supported CLIs and still override target selection when needed

### Plugins

- [ ] **PLUG-01**: User can declare plugin or extension assets separately from skill assets in configuration
- [ ] **PLUG-02**: User can install plugin or extension assets only for targets that support them
- [ ] **PLUG-03**: User can see when a plugin or extension asset was skipped because a target does not support that capability

### Verification

- [ ] **VER-01**: User can list or inspect what skills were installed for each target after running setup
- [ ] **VER-02**: User can see which targets succeeded, failed, or were skipped in the latest setup run
- [ ] **VER-03**: User can use a doctor or verification command to confirm that configured targets are wired correctly

## v2 Requirements

### Installation UX

- **INST-06**: User can run a dry-run command that shows the planned file and target changes before applying them
- **INST-07**: User can choose link mode instead of copy mode for supported local setups

### Source Management

- **SRC-05**: User can lock external sources to resolved revisions and update them intentionally
- **SRC-06**: User can cache previously fetched external sources for faster repeated installs

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hosted marketplace or web UI | v1 is a local bootstrap and sync tool, not a network service |
| Mandatory vendoring of every third-party skill source | The repository should stay config-driven by default |
| Emulating plugin support on targets that do not expose it | The project should skip unsupported capabilities instead of faking them |
| Multi-user or organization policy management | The project is explicitly single-user first for AImagician |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 0
- Unmapped: 21

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after initial definition*
