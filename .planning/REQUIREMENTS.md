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

## v2 Requirements (Skillbee V2 功能深化)

### User Config & Groups

- [x] **UCG-01**: User can define custom tags per skill and see them merged into skill search results
- [x] **UCG-02**: User can create, edit, and delete custom groups of skills persisted to disk
- [x] **UCG-03**: User can archive and unarchive skills from TUI, hiding them by default

### TUI Branding

- [x] **TUI-01**: TUI features bee-themed branding with lively colors
- [x] **TUI-02**: Skill detail panel shows richer information including custom tags, install matrix, related skills, SKILL.md preview

### Selection & Filtering

- [x] **SEL-01**: User can select multiple CLI targets simultaneously in TUI
- [x] **SEL-02**: User can combine install status, target, and tag filters

### Batch Operations

- [x] **BAT-01**: User can install selected skills to all selected targets in one action
- [x] **BAT-02**: Post-install report summarizes results per target per skill

### Overview

- [x] **OVW-01**: User can switch to a matrix overview of skills × targets installation status

### Theming

- [x] **THM-01**: User can switch between multiple color themes (bee/monokai/nord) with `T` key
- [x] **THM-02**: Theme preference persisted in user-config.yaml and applied at startup

## v3 Requirements (Configuration Orchestration & Verified Sync)

### Configuration Layers

- [ ] **CFG-01**: User can store global override configuration at `~/.config/skillbee/global/config.yaml`
- [ ] **CFG-02**: User can store project override configuration at `<project>/.skillbee/config.yaml` for the command's current working directory
- [ ] **CFG-03**: User can store and read independent global and project manifests without cross-scope interference
- [ ] **CFG-04**: User can edit durable TUI settings that immediately persist to user override YAML without mutating repository catalog or taxonomy defaults

### Source Eligibility

- [ ] **ELIG-01**: User can keep a source visible/searchable while it is default-disabled for bulk install
- [ ] **ELIG-02**: User can treat `slavingia/skill` as a Business source that is visible/searchable but default-disabled by default
- [ ] **ELIG-03**: User can explicitly include individual skills from a default-disabled source
- [ ] **ELIG-04**: User can exclude individual skills and prevent their install even when source or include rules would otherwise select them
- [ ] **ELIG-05**: User can see an explainable reason for why a skill is eligible, skipped, removed, or blocked
- [ ] **ELIG-06**: User can see command-based sources skipped in project scope with a clear global-only reason

### Scope & Target Sync

- [ ] **SYNC-01**: User can switch between global and project scopes and see scope-specific config, manifest, install status, preview, and report data
- [ ] **SYNC-02**: User can sync only the currently selected CLI targets, leaving unselected targets untouched
- [ ] **SYNC-03**: User can generate a sync plan that lists create, update, overwrite, remove, and skip operations before any filesystem write
- [ ] **SYNC-04**: User must confirm the sync preview before Skillbee modifies CLI skills directories
- [ ] **SYNC-05**: User can sync managed installs while preserving manual files in target CLI skills directories
- [ ] **SYNC-06**: User can have stale Skillbee-managed installs removed when their source or skill is no longer eligible
- [ ] **SYNC-07**: User can have manually modified Skillbee-managed installs overwritten by the resolved desired state

### TUI Orchestration UX

- [ ] **TUI3-01**: User can control source enabled/default-disabled/disabled state from the TUI and persist it to override YAML
- [ ] **TUI3-02**: User can set skill include/exclude from the TUI and persist it to override YAML
- [ ] **TUI3-03**: User can view taxonomy groups, source groupings, source status, and eligibility status in the TUI
- [ ] **TUI3-04**: User can view a pre-execution preview modal with Target × Skill operations and skip reasons
- [ ] **TUI3-05**: User can view a final Target × Skill report with success, skipped, failed, removed, and overwritten statuses

### Verification & Acceptance

- [ ] **ACC-01**: User can run automated tests proving include/exclude priority, default-disabled sources, and project/global manifest isolation
- [ ] **ACC-02**: User can run automated tests proving selected-target sync and manual-file preservation
- [ ] **ACC-03**: User can manually verify project scope installs into current `pwd` using CLI-specific project paths such as `<project>/.claude/skills`
- [ ] **ACC-04**: User can run real global-directory acceptance after preview confirmation against current-user CLI skills directories
- [ ] **ACC-05**: User can verify the PRD acceptance checklist in `docs/PRD.md` without unresolved gaps

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hosted marketplace or web UI | v1 is a local bootstrap and sync tool, not a network service |
| Mandatory vendoring of every third-party skill source | The repository should stay config-driven by default |
| Emulating plugin support on targets that do not expose it | The project should skip unsupported capabilities instead of faking them |
| Multi-user or organization policy management | The project is explicitly single-user first for AImagician |
| Mutating repo catalog/taxonomy from TUI | TUI writes user override YAML only; repo defaults remain baseline |
| Command-based sources in project scope | User confirmed command sources are global-only |
| Deleting unmanaged files during sync | v3 safety requires preserving manual files in CLI skills directories |

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

| Requirement | V2 Phase | Status |
|-------------|----------|--------|
| UCG-01 | Phase 1 | Complete |
| UCG-02 | Phase 1 | Complete |
| UCG-03 | Phase 1 | Complete |
| TUI-01 | Phase 2 | Complete |
| TUI-02 | Phase 2 | Complete |
| SEL-01 | Phase 3 | Complete |
| SEL-02 | Phase 3 | Complete |
| BAT-01 | Phase 4 | Complete |
| BAT-02 | Phase 4 | Complete |
| OVW-01 | Phase 5 | Complete |
| THM-01 | Phase 5 | Complete |
| THM-02 | Phase 5 | Complete |

| Requirement | V3 Phase | Status |
|-------------|----------|--------|
| CFG-01 | Phase 9 | Pending |
| CFG-02 | Phase 9 | Pending |
| CFG-03 | Phase 9 | Pending |
| CFG-04 | Phase 9 | Pending |
| ELIG-01 | Phase 10 | Pending |
| ELIG-02 | Phase 10 | Pending |
| ELIG-03 | Phase 10 | Pending |
| ELIG-04 | Phase 10 | Pending |
| ELIG-05 | Phase 10 | Pending |
| ELIG-06 | Phase 10 | Pending |
| SYNC-01 | Phase 11 | Pending |
| SYNC-02 | Phase 11 | Pending |
| SYNC-03 | Phase 11 | Pending |
| SYNC-04 | Phase 11 | Pending |
| SYNC-05 | Phase 11 | Pending |
| SYNC-06 | Phase 11 | Pending |
| SYNC-07 | Phase 11 | Pending |
| TUI3-01 | Phase 12 | Pending |
| TUI3-02 | Phase 12 | Pending |
| TUI3-03 | Phase 12 | Pending |
| TUI3-04 | Phase 12 | Pending |
| TUI3-05 | Phase 12 | Pending |
| ACC-01 | Phase 13 | Pending |
| ACC-02 | Phase 13 | Pending |
| ACC-03 | Phase 13 | Pending |
| ACC-04 | Phase 13 | Pending |
| ACC-05 | Phase 13 | Pending |

**V3 Coverage:**
- v3 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-05-30 after defining v3.0 configuration orchestration requirements*
