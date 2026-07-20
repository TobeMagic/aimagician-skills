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

- [x] **SYNC-01**: User can switch between global and project scopes and see scope-specific config, manifest, install status, preview, and report data
- [x] **SYNC-02**: User can sync only the currently selected CLI targets, leaving unselected targets untouched
- [x] **SYNC-03**: User can generate a sync plan that lists create, update, overwrite, remove, and skip operations before any filesystem write
- [x] **SYNC-04**: User must confirm the sync preview before Skillbee modifies CLI skills directories
- [x] **SYNC-05**: User can sync managed installs while preserving manual files in target CLI skills directories
- [x] **SYNC-06**: User can have stale Skillbee-managed installs removed when their source or skill is no longer eligible
- [x] **SYNC-07**: User can have manually modified Skillbee-managed installs overwritten by the resolved desired state

### TUI Orchestration UX

- [x] **TUI3-01**: User can control source enabled/default-disabled/disabled state from the TUI and persist it to override YAML
- [x] **TUI3-02**: User can set skill include/exclude from the TUI and persist it to override YAML
- [x] **TUI3-03**: User can view taxonomy groups, source groupings, source status, and eligibility status in the TUI
- [x] **TUI3-04**: User can view a pre-execution preview modal with Target × Skill operations and skip reasons
- [x] **TUI3-05**: User can view a final Target × Skill report with success, skipped, failed, removed, and overwritten statuses

### Verification & Acceptance

- [x] **ACC-01**: User can run automated tests proving include/exclude priority, default-disabled sources, and project/global manifest isolation
- [x] **ACC-02**: User can run automated tests proving selected-target sync and manual-file preservation
- [x] **ACC-03**: User can manually verify project scope installs into current `pwd` using CLI-specific project paths such as `<project>/.claude/skills`
- [x] **ACC-04**: User can run real global-directory acceptance after preview confirmation against current-user CLI skills directories
- [x] **ACC-05**: User can verify the PRD acceptance checklist in `docs/PRD.md` without unresolved gaps

## v4 Requirements (AImagician Superpower + Skillbird Consolidation)

### Identity

- [x] **V4-ID-01**: Package identity is `aimagician_superpower`
- [x] **V4-ID-02**: Daily CLI command is `skillbird`, with no documented `skillbee` compatibility path
- [x] **V4-ID-03**: Global/project config and state paths use `skillbird`, `.skillbird`, and `aimagician-superpower`

### External Sources

- [x] **V4-SRC-01**: External catalog sources default to disabled at schema and catalog level
- [x] **V4-SRC-02**: GSD, Superpowers, selected Claude, UI, and Playwright source definitions are retained as disabled references instead of default installers

### Owned Skills

- [x] **V4-SKILL-01**: `aimagician-superpower` exists as the owned workflow skill merging GSD and Superpowers process value
- [x] **V4-SKILL-02**: `skill-creator`, `mcp-builder`, `interface-design`, and `webapp-testing` exist as owned consolidated skills
- [x] **V4-SKILL-03**: `docx`, `pdf`, `pptx`, and `xlsx` are classified as owned document skills

### Taxonomy & Formatter

- [x] **V4-TAX-01**: Taxonomy has six categories: `build`, `research`, `design`, `documents`, `operate`, `strategy`
- [x] **V4-TAX-02**: `skillbird format-skills --check|--write` validates and writes owned skill classification frontmatter
- [x] **V4-TAX-03**: Search and install support category, subcategory, and tag selectors

### Documentation & GSD

- [x] **V4-DOC-01**: README describes Skillbird, the merged workflow, categories, global/project install, and external-source policy
- [x] **V4-GSD-01**: `.planning` records v4 as an active milestone with phase gates

### Completed Deep Merge & Acceptance

- [x] **V4-MERGE-01**: Discuss and verify the final detailed merge of GSD planning and Superpowers plan-writing behavior
- [x] **V4-MERGE-02**: Discuss and verify `code-guidelines` integration as execution discipline without duplicating it into multiple skills
- [x] **V4-MERGE-03**: Audit merged skills for capability regression against reference sources
- [x] **V4-UX-01**: Verify Skillbird TUI style and category workflow through PTY smoke acceptance
- [x] **V4-UX-02**: Verify category bundle install UX for global and project scopes
- [x] **V4-ACC-01**: Accept a real global install of core workflow skills after preview confirmation
- [x] **V4-ACC-02**: Accept a real project install of one category bundle after preview confirmation

## v5 Requirements (Window-PPTX Verified Production Engine)

Completion requires the phase evidence and exit gates named in the traceability table; a unit-test implementation alone is not sufficient.

### Baseline and Safety

- [x] **V5-SAFE-01**: Strict dry-run reports intended actions without filesystem, network, COM, or presentation writes
- [x] **V5-SAFE-02**: Resolved source/output and staging guards prevent implicit source overwrite
- [x] **V5-SAFE-03**: COM session ownership is explicit, and cleanup quits only a PowerPoint application proven to be tool-owned
- [x] **V5-SAFE-04**: Programmatic opens disable macros and restore the exact prior automation-security value
- [x] **V5-SAFE-05**: PPTX/PDF outputs are written to validated candidates and atomically promoted with source-integrity evidence
- [x] **V5-SAFE-06**: Add-in listing and probing are terminal read-only inspection routes with one machine-readable result
- [x] **V5-SAFE-07**: Macro-enabled suffixes and presentation/export geometry are preserved
- [x] **V5-SAFE-08**: The baseline and real Windows safety matrix are reproducible and evidence-backed

### DeckPlan and Semantic Rules

- [x] **V5-PLAN-01**: A versioned DeckPlan schema accepts semantic intent and rejects uncontrolled raw design instructions
- [x] **V5-PLAN-02**: Fifteen common business presentation archetypes provide predefined narrative structures
- [x] **V5-PLAN-03**: Deterministic rules map content semantics to ranked page forms and chart/layout candidates
- [x] **V5-PLAN-04**: Capacity, splitting, sparse-content, and cross-slide rhythm rules govern deck density and pacing
- [x] **V5-PLAN-05**: Decision traces and low-confidence safe defaults support ordinary models reproducibly

### Design System and Layout Registries

- [x] **V5-DESIGN-01**: Eight governed themes cover light, dark, industry, audience, and scenario needs
- [x] **V5-DESIGN-02**: Twenty-four page families expose at least three deterministic variants each, for at least 72 layouts
- [x] **V5-DESIGN-03**: Design tokens govern grid, safe margins, type hierarchy, color, spacing, border, radius, shadow, and decoration
- [x] **V5-DESIGN-04**: Reusable components and asset rules enforce crop, icon, provenance, and editable-object policies
- [x] **V5-DESIGN-05**: Brand overrides and font fallbacks are deterministic and explicitly reported

### Transactional Core Renderer

- [ ] **V5-RENDER-01**: The production renderer creates editable native PowerPoint core objects
- [ ] **V5-RENDER-02**: Geometry, text, and images scale correctly across 16:9, 4:3, and custom page sizes
- [ ] **V5-RENDER-03**: Masters, footers, z-order, and grouping are generated consistently
- [ ] **V5-RENDER-04**: Compiler CLI and project runner validate, compile, render, inspect, and repair DeckPlans
- [ ] **V5-RENDER-05**: A recording fake-COM end-to-end path verifies renderer ordering without requiring Windows

### Advanced Editable Objects

- [ ] **V5-OBJECT-01**: Charts and tables use native editable PowerPoint objects with populated data
- [ ] **V5-OBJECT-02**: Processes, timelines, matrices, quadrants, funnels, and roadmaps render as editable diagrams
- [ ] **V5-OBJECT-03**: Speaker notes and hyperlinks remain available in the delivered deck
- [ ] **V5-OBJECT-04**: Motion uses controlled presets and remains off unless explicitly requested
- [ ] **V5-OBJECT-05**: PNG/PDF exports preserve page ratio and readable labels

### Quality Gates and Repair

- [ ] **V5-QA-01**: Package, COM, geometric, visual, and deck-level snapshots form a five-layer inspection model
- [ ] **V5-QA-02**: Structural, visual, editability, density, repetition, font, chart, and deck checks emit actionable findings
- [ ] **V5-QA-03**: Candidate-only auto-repair is bounded, monotonic, and rejects hard-gate regressions
- [ ] **V5-QA-04**: Validation reports and repair logs use stable versioned schemas
- [ ] **V5-QA-05**: Customer-delivery hard gates enforce package/reopen success, source integrity, editability, and native object coverage

### Weak-Model Benchmark

- [ ] **V5-BENCH-01**: Fifteen business scenarios cover the required commercial presentation types
- [ ] **V5-BENCH-02**: Three frozen arms, two ordinary models, and defined repeats support controlled comparison
- [ ] **V5-BENCH-03**: Deterministic checks and blind human review produce comparable delivery scores
- [ ] **V5-BENCH-04**: Inputs, model outputs, generated artifacts, and scorecards carry frozen hashes
- [ ] **V5-BENCH-05**: Release thresholds quantify improvement, reliability, and customer-delivery readiness

### Windows Acceptance and Closure

- [ ] **V5-UAT-01**: A real Windows PowerPoint matrix covers isolated/attached sessions, formats, sizes, fonts, add-ins, and path variants
- [ ] **V5-UAT-02**: Ten-run reliability, locking, source protection, and format/path cases pass without hidden state leakage
- [ ] **V5-UAT-03**: Canonical outputs, exports, contact sheets, and quality reports exist for all benchmark scenarios
- [ ] **V5-UAT-04**: A final read-only OpenCode audit is independently checked against repository and runtime evidence
- [ ] **V5-UAT-05**: The Skill and references describe the compiler, weak-model mode, QA loop, failures, and output contract
- [ ] **V5-UAT-06**: v5.0 closes only when every customer-delivery hard gate and mapped requirement has fresh evidence

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
| CFG-01 | Phase 9 | Complete |
| CFG-02 | Phase 9 | Complete |
| CFG-03 | Phase 9 | Complete |
| CFG-04 | Phase 9 | Complete |
| ELIG-01 | Phase 10 | Complete |
| ELIG-02 | Phase 10 | Complete |
| ELIG-03 | Phase 10 | Complete |
| ELIG-04 | Phase 10 | Complete |
| ELIG-05 | Phase 10 | Complete |
| ELIG-06 | Phase 10 | Complete |
| SYNC-01 | Phase 11 | Complete |
| SYNC-02 | Phase 11 | Complete |
| SYNC-03 | Phase 11 | Complete |
| SYNC-04 | Phase 11 | Complete |
| SYNC-05 | Phase 11 | Complete |
| SYNC-06 | Phase 11 | Complete |
| SYNC-07 | Phase 11 | Complete |
| TUI3-01 | Phase 12 | Complete |
| TUI3-02 | Phase 12 | Complete |
| TUI3-03 | Phase 12 | Complete |
| TUI3-04 | Phase 12 | Complete |
| TUI3-05 | Phase 12 | Complete |
| ACC-01 | Phase 13 | Complete |
| ACC-02 | Phase 13 | Complete |
| ACC-03 | Phase 13 | Complete |
| ACC-04 | Phase 13 | Complete |
| ACC-05 | Phase 13 | Complete |

**V3 Coverage:**
- v3 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0

| Requirement | V4 Phase | Status |
|-------------|----------|--------|
| V4-ID-01 | Phase 14 | Complete |
| V4-ID-02 | Phase 14 | Complete |
| V4-ID-03 | Phase 14 | Complete |
| V4-SRC-01 | Phase 15 | Complete |
| V4-SRC-02 | Phase 15 | Complete |
| V4-SKILL-01 | Phase 16 | Complete |
| V4-SKILL-02 | Phase 16 | Complete |
| V4-SKILL-03 | Phase 16 | Complete |
| V4-TAX-01 | Phase 17 | Complete |
| V4-TAX-02 | Phase 17 | Complete |
| V4-TAX-03 | Phase 17 | Complete |
| V4-DOC-01 | Phase 18 | Complete |
| V4-GSD-01 | Phase 18 | Complete |
| V4-MERGE-01 | Phase 19 | Complete |
| V4-MERGE-02 | Phase 19 | Complete |
| V4-MERGE-03 | Phase 19 | Complete |
| V4-UX-01 | Phase 20 | Complete |
| V4-UX-02 | Phase 20 | Complete |
| V4-ACC-01 | Phase 21 | Complete |
| V4-ACC-02 | Phase 21 | Complete |

**V4 Coverage:**
- v4 requirements: 20 total
- Complete: 20
- Open: 0

| Requirement | V5 Phase | Status |
|-------------|----------|--------|
| V5-SAFE-01 | Phase 22 | Complete |
| V5-SAFE-02 | Phase 22 | Complete |
| V5-SAFE-03 | Phase 22 | Complete |
| V5-SAFE-04 | Phase 22 | Complete |
| V5-SAFE-05 | Phase 22 | Complete |
| V5-SAFE-06 | Phase 22 | Complete |
| V5-SAFE-07 | Phase 22 | Complete |
| V5-SAFE-08 | Phase 22 | Complete |
| V5-PLAN-01 | Phase 23 | Complete |
| V5-PLAN-02 | Phase 23 | Complete |
| V5-PLAN-03 | Phase 23 | Complete |
| V5-PLAN-04 | Phase 23 | Complete |
| V5-PLAN-05 | Phase 23 | Complete |
| V5-DESIGN-01 | Phase 24 | Complete |
| V5-DESIGN-02 | Phase 24 | Complete |
| V5-DESIGN-03 | Phase 24 | Complete |
| V5-DESIGN-04 | Phase 24 | Complete |
| V5-DESIGN-05 | Phase 24 | Complete |
| V5-RENDER-01 | Phase 25 | In Progress |
| V5-RENDER-02 | Phase 25 | In Progress |
| V5-RENDER-03 | Phase 25 | In Progress |
| V5-RENDER-04 | Phase 25 | In Progress |
| V5-RENDER-05 | Phase 25 | In Progress |
| V5-OBJECT-01 | Phase 26 | Planned |
| V5-OBJECT-02 | Phase 26 | Planned |
| V5-OBJECT-03 | Phase 26 | Planned |
| V5-OBJECT-04 | Phase 26 | Planned |
| V5-OBJECT-05 | Phase 26 | Planned |
| V5-QA-01 | Phase 27 | Planned |
| V5-QA-02 | Phase 27 | Planned |
| V5-QA-03 | Phase 27 | Planned |
| V5-QA-04 | Phase 27 | Planned |
| V5-QA-05 | Phase 27 | Planned |
| V5-BENCH-01 | Phase 28 | Planned |
| V5-BENCH-02 | Phase 28 | Planned |
| V5-BENCH-03 | Phase 28 | Planned |
| V5-BENCH-04 | Phase 28 | Planned |
| V5-BENCH-05 | Phase 28 | Planned |
| V5-UAT-01 | Phase 29 | Planned |
| V5-UAT-02 | Phase 29 | Planned |
| V5-UAT-03 | Phase 29 | Planned |
| V5-UAT-04 | Phase 29 | Planned |
| V5-UAT-05 | Phase 29 | Planned |
| V5-UAT-06 | Phase 29 | Planned |

**V5 Coverage:**
- v5 requirements: 44 total
- Mapped to exactly one phase: 44
- Complete: 18
- In Progress: 5
- Planned: 21
- Open: 26
- Unmapped: 0

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-07-20 after defining v5.0 Window-PPTX requirements*
