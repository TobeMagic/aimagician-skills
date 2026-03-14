# Requirements: AImagician Skills

**Defined:** 2026-03-13
**Core Value:** After cloning the repo, one command installs and updates the right skills into each supported CLI's user-level location with as little manual setup as possible.

## v1 Requirements

### Repository

- [x] **REPO-01**: User can keep self-authored skills inside this repository in a stable directory that the installer scans automatically
- [x] **REPO-02**: User can add or update owned skills without editing installer source code

### Sources

- [x] **SRC-01**: User can register an external GitHub skill source in configuration
- [x] **SRC-02**: User can register an external command-based source in configuration
- [x] **SRC-03**: User can enable or disable an individual external source without deleting its definition
- [x] **SRC-04**: User can declare which target CLIs each skill or source should deploy to

### Installation

- [x] **INST-01**: User can clone the repository and run one bootstrap command to install configured assets
- [x] **INST-02**: User can re-run the bootstrap command to update existing installs without duplicating installed assets
- [x] **INST-03**: User can run the same project on Windows and Linux with the same repository configuration
- [x] **INST-04**: User can install into the current user's default target locations so skills load automatically
- [x] **INST-05**: User can invoke the bootstrap workflow through an npm-executed command in an `npx ...@latest` style

### Targets

- [x] **TARG-01**: User can install configured skills into Codex
- [x] **TARG-02**: User can install configured skills into Claude Code
- [x] **TARG-03**: User can install configured skills into OpenCode
- [x] **TARG-04**: User can install Gemini-compatible output even when the source asset originates as a repository skill
- [x] **TARG-05**: User can default installation to all supported CLIs and still override target selection when needed

### Plugins

- [x] **PLUG-01**: User can declare plugin or extension assets separately from skill assets in configuration
- [x] **PLUG-02**: User can install plugin or extension assets only for targets that support them
- [x] **PLUG-03**: User can see when a plugin or extension asset was skipped because a target does not support that capability

### Verification

- [x] **VER-01**: User can list or inspect what skills were installed for each target after running setup
- [x] **VER-02**: User can see which targets succeeded, failed, or were skipped in the latest setup run
- [x] **VER-03**: User can use a doctor or verification command to confirm that configured targets are wired correctly

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
| REPO-01 | Phase 1 | Complete |
| REPO-02 | Phase 1 | Complete |
| SRC-01 | Phase 1 | Complete |
| SRC-02 | Phase 1 | Complete |
| SRC-03 | Phase 1 | Complete |
| SRC-04 | Phase 1 | Complete |
| INST-01 | Phase 2 | Complete |
| INST-02 | Phase 2 | Complete |
| INST-03 | Phase 2 | Complete |
| INST-04 | Phase 3 | Complete |
| INST-05 | Phase 2 | Complete |
| TARG-01 | Phase 3 | Complete |
| TARG-02 | Phase 3 | Complete |
| TARG-03 | Phase 3 | Complete |
| TARG-04 | Phase 4 | Complete |
| TARG-05 | Phase 2 | Complete |
| PLUG-01 | Phase 4 | Complete |
| PLUG-02 | Phase 4 | Complete |
| PLUG-03 | Phase 4 | Complete |
| VER-01 | Phase 5 | Complete |
| VER-02 | Phase 5 | Complete |
| VER-03 | Phase 5 | Complete |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-14 after Phase 5 completion*
