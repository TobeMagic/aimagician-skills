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

- [x] **V5-RENDER-01**: The production renderer creates editable native PowerPoint core objects
- [x] **V5-RENDER-02**: Geometry, text, and images scale correctly across 16:9, 4:3, and custom page sizes
- [x] **V5-RENDER-03**: Masters, footers, z-order, and grouping are generated consistently
- [x] **V5-RENDER-04**: Compiler CLI and project runner validate, compile, render, inspect, and repair DeckPlans
- [x] **V5-RENDER-05**: A recording fake-COM end-to-end path verifies renderer ordering without requiring Windows

### Advanced Editable Objects

- [x] **V5-OBJECT-01**: Charts and tables use native editable PowerPoint objects with populated data
- [x] **V5-OBJECT-02**: Processes, timelines, matrices, quadrants, funnels, and roadmaps render as editable diagrams
- [x] **V5-OBJECT-03**: Speaker notes and hyperlinks remain available in the delivered deck
- [x] **V5-OBJECT-04**: Motion uses controlled presets and remains off unless explicitly requested
- [x] **V5-OBJECT-05**: PNG/PDF exports preserve page ratio and readable labels

### Quality Gates and Repair

- [x] **V5-QA-01**: Package, COM, geometric, visual, and deck-level snapshots form a five-layer inspection model
- [x] **V5-QA-02**: Structural, visual, editability, density, repetition, font, chart, and deck checks emit actionable findings
- [x] **V5-QA-03**: Candidate-only auto-repair is bounded, monotonic, and rejects hard-gate regressions
- [x] **V5-QA-04**: Validation reports and repair logs use stable versioned schemas
- [x] **V5-QA-05**: Customer-delivery hard gates enforce package/reopen success, source integrity, editability, and native object coverage

### Huashu Reference Assimilation and Visual Calibration

- [x] **V5-REF-01**: The Huashu source URL, full commit, reviewed subtree, source/archive hash, LICENSE hash, MIT notice, and accept/adapt/reject decisions are frozen and reproducible
- [x] **V5-REF-02**: Trusted inputs, immutable FactStore, strict model BriefPlan, deterministic NarrativePlan, canonical DeckPlan v1, and native rendering form one fail-closed authority chain
- [x] **V5-REF-03**: Twelve neutral art directions, three deterministic candidate proofs, BrandSpec, 24 governed page families, and layout/theme/component rules are machine-consumable and native-PPTX safe
- [x] **V5-REF-04**: Quality-report v2 merges narrative, compiler, renderer, preview, package, and editability findings and applies at most one pre-render and one post-render monotonic repair without rewriting facts
- [ ] **V5-REF-05**: Weak-model normalization, retries, safe defaults, progressive Skill references, and skill TDD measurably reduce schema and planning failures without accepting raw design fields
- [ ] **V5-REF-06**: Six calibration cases and all later formal trials carry complete engine, renderer, verifier, registry, schema, skill, corpus, protocol, prompt, environment, font, and asset fingerprints; PowerPoint fingerprints are mandatory only for PowerPoint-certification artifacts, and pre-Huashu evidence is noncanonical

### Portable Rendering and Cross-Engine QA

- [x] **V5-PORT-01**: RenderPlan execution is backend-neutral, governed `auto` generation selects PptxGenJS without COM, and unsupported required capabilities fail before candidate or process mutation
- [x] **V5-PORT-02**: PptxGenJS 4.0.1 generates identity-bound native editable text, shapes, images, tables, charts, diagrams, notes, links, masters, and footers across supported page ratios without whole-slide raster fallback
- [x] **V5-PORT-03**: Normalized OOXML packages are byte-deterministic for an identical RenderPlan and environment fingerprint while preserving candidate-only validation, source hashes, and atomic promotion
- [x] **V5-PORT-04**: A RenderPlan-aware OOXML inspector fails closed on package, relationship, identity, content, media, chart, table, note, link, master, or embedded-data mismatches before promotion
- [x] **V5-PORT-05**: Isolated LibreOffice Impress and Poppler rendering produces page-count- and ratio-correct PDF/PNG proof without modifying the canonical PPTX, and its real PNG output feeds Quality-v2 hard gates
- [x] **V5-PORT-06**: HTML is generated deterministically from RenderPlan and governed tokens for proof and QA only; model-authored HTML/CSS and HTML-as-canonical-PPTX-intermediate are rejected
- [x] **V5-PORT-07**: PowerPoint doctor and certification accurately diagnose early/late binding, use only safely owned sessions, never repair the registry automatically, and certify portable artifacts read-only without becoming a daily delivery dependency
- [x] **V5-PORT-08**: Public backend and verification options, capability decisions, staged verification results, and Node/PptxGenJS/LibreOffice/Poppler/font/OS fingerprints are stable, machine-readable, and backward-compatible with legacy COM report readers
- [x] **V5-PORT-09**: Six calibration scenarios produce real portable PPTX, PDF, slide PNG, contact-sheet, OOXML, and Quality-v2 evidence with all portable customer hard gates passing; PowerPoint evidence remains a later sampled release gate

### Weak-Model Benchmark

- [ ] **V5-BENCH-01**: Fifteen business scenarios cover the required commercial presentation types
- [ ] **V5-BENCH-02**: Three frozen arms, two ordinary models, and defined repeats support controlled comparison
- [ ] **V5-BENCH-03**: Deterministic checks and blind human review produce comparable delivery scores
- [ ] **V5-BENCH-04**: Inputs, model outputs, generated artifacts, and scorecards carry frozen hashes
- [ ] **V5-BENCH-05**: Release thresholds quantify improvement, reliability, and customer-delivery readiness

### Cross-Engine Acceptance and Closure

- [ ] **V5-UAT-01**: A real portable-engine matrix covers formats, sizes, fonts, and path variants, while read-only PowerPoint certification covers a frozen 10% sample plus every high-risk capability sample
- [ ] **V5-UAT-02**: Ten-run portable reliability, locking, source protection, format/path, isolated LibreOffice, and optional PowerPoint ownership cases pass without hidden state or process leakage
- [ ] **V5-UAT-03**: Canonical portable outputs, exports, contact sheets, and quality reports exist for all benchmark scenarios, with PowerPoint comparison evidence for the frozen certification sample
- [ ] **V5-UAT-04**: A final read-only OpenCode audit is independently checked against repository and runtime evidence
- [ ] **V5-UAT-05**: The Skill and references describe the compiler, weak-model mode, QA loop, failures, and output contract
- [ ] **V5-UAT-06**: v5.0 closes only when every customer-delivery hard gate and mapped requirement has fresh evidence

## v5.1 Requirements (Window-PPTX Reference-Grade Visual Engine)

### Reference Contract and TemplatePack

- [ ] **V51-REF-01**: The authorized `工作总结.pptx` reference is packaged with provenance, hash, license/authorization status, slide inventory, stable shape-slot map, and visual baseline evidence
- [ ] **V51-TPL-01**: A portable OOXML TemplatePack adapter replaces governed editable text/data slots while preserving masters, layouts, groups, gradients, connectors, charts, media, crop geometry, and all unbound package parts
- [ ] **V51-TPL-02**: TemplatePack adaptation is atomic, source-safe, deterministic for the same input, rejects stale slot hashes/capacity violations, and emits a machine-readable adaptation report
- [ ] **V51-TPL-03**: The first 15-slide work-summary acceptance deck uses new content, remains editable, opens in LibreOffice/PowerPoint-compatible OOXML, and retains non-slot decorative visual similarity of at least 0.98

### DesignPack and Visual Planning

- [ ] **V51-DESIGN-01**: Four governed DesignPacks cover all fifteen commercial scenarios with explicit themes, page families, variants, capacities, pacing, asset requirements, and safe fallbacks
- [ ] **V51-DESIGN-02**: AssetPlan and VisualPlan form deterministic seams between narrative planning and rendering; ordinary models choose semantic intent/fact IDs but never raw coordinates, fonts, colors, HTML, OOXML, or executable code
- [ ] **V51-DESIGN-03**: Content semantics map to ranked component compositions, including hero, KPI, comparison, process, timeline, matrix, roadmap, chart, table, product, case, team, risk, summary, and CTA forms
- [ ] **V51-DESIGN-04**: Text, numbers, charts, tables, processes, and core shapes remain editable; decorative SVG/PNG/photos/illustrations remain traceable and replaceable

### Visual Quality and Weak-Model Reliability

- [ ] **V51-QA-01**: Visual regression checks reject sparse, repetitive, low-coverage, low-entropy, misaligned, overflowing, overlapping, distorted, unreadable, incompatible, or non-editable output
- [ ] **V51-QA-02**: Auto-repair can safely adjust text fit, split/merge choices, asset fallback, alignment, crop, density, and variant choice without changing immutable facts
- [ ] **V51-QA-03**: Historical sparse r12 output fails the new reference-grade profile, while accepted TemplatePack/DesignPack outputs pass structural, editable, render, and visual gates
- [ ] **V51-BENCH-01**: DeepSeek V4 Flash Free completes four representative scenario trials before a refrozen two-model formal benchmark
- [ ] **V51-UAT-01**: Blind review averages at least 4.2/5 with no relevant dimension below 4, and every accepted requirement has fresh reproducible evidence

## v6.0 Requirements (Template-Intelligence Quality Reset)

| Requirement | Current | Target | Acceptance |
|---|---|---|---|
| **V6-BRIEF-01** | v5 briefs are shallow and allow generation without a full discussion-locked client contract | ProjectBriefPack v1 owns facts, sources, assets, audience, goals, timing, anatomy, decisions, prohibitions, rubric, status, and lock digest | `Draft` and `NeedsDiscussion` formal generation fail; only a complete `Locked` pack produces a plan |
| **V6-CORPUS-01** | Fifteen scenarios average few facts and usually have no required assets | Three complete realistic flagships plus twelve locked skeletons cover all accepted scenarios | Every scenario validates; all accepted flagship facts, sources, asset roles, slide budgets, and decisions are present |
| **V6-ASSET-01** | No governed private commercial-template acquisition boundary exists | Entitled assets use ignored private storage, host-scoped auth, redirect stripping, quarantine, provenance, rights, and resumable state | No credential/private byte is staged; auth, redirect, quarantine, rights, and resume tests pass |
| **V6-LIB-01** | Four legacy single-slide files are unverified and disconnected from generation | Stable catalog IDs, TemplatePack v2 slots, dedupe, dependency closure, retrieval, and Registry v3 make certified templates selectable | Old registries remain compatible; certified items are queryable and uncertified legacy items are never auto-selected |
| **V6-DESIGN-01** | Ordinary models rely on deterministic but visually shallow composition rules | GPT-5.5 medium creates grounded NarrativePlan, TemplateSelectionPlan, and SlideBlueprint from visual candidates | Unknown IDs, raw coordinates, raw OOXML/HTML/code, unsupported claims, and capacity violations fail closed |
| **V6-DECK-01** | Generated decks omit or weaken directory, section rhythm, motif continuity, and complete-work art direction | Cover, directory, chapter pages, evidence body, decision/conclusion, closing, appendix, theme, motif, grid, type, imagery, and pacing are governed | All three flagships pass anatomy, rhythm, diversity, consistency, and reference-parity inspection |
| **V6-PORT-01** | Portable rendering is editable but v5.1 visual quality is rejected | Complete-work OOXML materialization preserves masters, themes, groups, crops, charts/workbooks, tables, media, and unrelated parts | Three flagship PPTX files open, render, remain editable, and pass OOXML/source-integrity checks without COM |
| **V6-PORT-02** | v5 cross-engine closure never started | Portable reliability covers repeated runs, paths, ratios, fonts, source protection, locks, and isolated rendering | Every mandatory portable case passes; real PowerPoint remains optional diagnostics only |
| **V6-QA-01** | Repair is broad and can accumulate redundant component fixes | One deterministic local repair, one same-family reselection, and one visual replan are the complete bounded loop | Repair is monotonic, fact-safe, art-direction-safe, capped, and rejects unresolved candidates |
| **V6-EVID-01** | Automatic scores obscure visible quality failures | Every delivery carries hashes, lineage, PPTX/PDF/PNG/contact sheet, structural/editability reports, and anonymous before/after evidence | Exact artifacts reproduce and all reviewer packets rehash successfully |
| **V6-DOC-01** | Skill docs describe v5 compiler and human-review closure | Skill docs make quality-first generation, brief discussion, private library, GPT-5.5 route, QA, failures, and output bundle executable | Formatter and workflow behavior evals pass and no stale v5 default remains |
| **V6-UAT-01** | v5.1 human review is `NOT_RUN` and generated trials are rejected by the user | Three fresh isolated visual-capable AIs perform anonymous reference-parity review | At least 2/3 parity PASS; overall `>=4.3`, dimensions `>=4.1`, flagships `>=4.2`, zero two-reviewer Blocker/Important consensus |
| **V6-AUDIT-01** | No v6 completion audit exists | A fresh OpenCode Agnes audit maps original requests through requirements, implementation, tests, artifacts, and UAT | Every requirement is `PASS` and no Blocker or Important remains |
| **V6-REL-01** | v5.1 remains `NO_GO` | v6.0 closes and becomes merge-ready only after all hard gates pass | Any `FAIL`, `NOT_RUN`, unmapped requirement, Blocker, or Important keeps the milestone open |

### v6 recovery requirements

| Requirement | Acceptance |
|---|---|
| **V6R-GROUND-01** | Planning and Skill docs state the actual physical/code/alias inventory, invalidate the former GO, and map Phases 42–48 without contradictory completion claims |
| **V6R-ACQ-01** | A real Playwright adapter and deterministic browser fixture prove authenticated state, full category/pagination discovery, same-origin download, resume, dedupe, redaction, disk guard, and fail-closed site drift; external sync remains `NEEDS_AUTH` until the private credential file exists |
| **V6R-MINE-01** | Real private packages are passively quarantined, rendered, page-inventoried, deduplicated, classified, and a rights-bound 300–500-page core is certified |
| **V6R-MAT-01** | Production consumes TemplateSelectionPlan and SlideBlueprint; every selected physical or registered candidate has exact materializer evidence and unknown/unmaterialized choices fail |
| **V6R-ANCHOR-01** | Work-report, campus-competition, and academic-defense anchors use actual certified candidates and pass anatomy, editability, artifact, and reference-grade pixel review |
| **V6R-WEAK-01** | All fifteen realistic scenarios run through the accepted system and ordinary models are measured against the strong-author baseline without raw geometry/style authority |
| **V6R-UAT-01** | Three fresh independent image-capable AI contexts review full-resolution anonymous artifacts; any unresolved Blocker or Important fails |
| **V6R-REL-01** | A fresh OpenCode completion audit maps every original/latest user request to implementation and evidence; missing auth, private acquisition, materialization, anchor visual review, or ordinary-model evidence keeps v6 open |

### Superseded v5 intent

- V5-UAT-01 intent is subsumed by V6-PORT-01; mandatory PowerPoint sampling is
  removed.
- V5-UAT-02 intent is subsumed by V6-PORT-02.
- V5-UAT-03 intent is subsumed by V6-EVID-01.
- V5-UAT-04 intent is subsumed by V6-AUDIT-01.
- V5-UAT-05 intent is subsumed by V6-DOC-01.
- V5-UAT-06 intent is subsumed by V6-REL-01.

These mappings preserve intent only. Phase 29 never started and supplies no v5
implementation or evidence.

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
| V5-RENDER-01 | Phase 25 | Complete |
| V5-RENDER-02 | Phase 25 | Complete |
| V5-RENDER-03 | Phase 25 | Complete |
| V5-RENDER-04 | Phase 25 | Complete |
| V5-RENDER-05 | Phase 25 | Complete |
| V5-OBJECT-01 | Phase 26 | Complete |
| V5-OBJECT-02 | Phase 26 | Complete |
| V5-OBJECT-03 | Phase 26 | Complete |
| V5-OBJECT-04 | Phase 26 | Complete |
| V5-OBJECT-05 | Phase 26 | Complete |
| V5-QA-01 | Phase 27 | Complete |
| V5-QA-02 | Phase 27 | Complete |
| V5-QA-03 | Phase 27 | Complete |
| V5-QA-04 | Phase 27 | Complete |
| V5-QA-05 | Phase 27 | Complete |
| V5-REF-01 | Phase 27.1 | Complete |
| V5-REF-02 | Phase 27.1 | Complete |
| V5-REF-03 | Phase 27.1 | Complete — portable native-PPTX proof closed in Phase 27.2 |
| V5-REF-04 | Phase 27.1 | Complete |
| V5-REF-05 | Phase 27.1 | Partial — ordinary-model comparison carried to Phase 28 |
| V5-REF-06 | Phase 27.1 | Partial — clean post-27.2 formal benchmark NOT_RUN |
| V5-PORT-01 | Phase 27.2 | Complete |
| V5-PORT-02 | Phase 27.2 | Complete |
| V5-PORT-03 | Phase 27.2 | Complete |
| V5-PORT-04 | Phase 27.2 | Complete |
| V5-PORT-05 | Phase 27.2 | Complete |
| V5-PORT-06 | Phase 27.2 | Complete |
| V5-PORT-07 | Phase 27.2 | Complete |
| V5-PORT-08 | Phase 27.2 | Complete |
| V5-PORT-09 | Phase 27.2 | Complete — portable hard gates PASS; manual senior-designer visual bar remains a v5 milestone blocker |
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
- v5 requirements: 59 total
- Mapped to exactly one phase: 59
- Complete: 36
- Partial: 3
- In Progress: 9
- Planned: 11
- Open: 23
- Unmapped: 0

| Requirement | V6 Phase | Status |
|-------------|----------|--------|
| V6-BRIEF-01 | Phase 36 | Complete |
| V6-CORPUS-01 | Phase 36 | Complete |
| V6-ASSET-01 | Phase 37 | Complete via recovery Phase 43 |
| V6-LIB-01 | Phase 37 | Complete via recovery Phases 43–44 |
| V6-DESIGN-01 | Phase 38 | Complete via recovery Phases 45–47 |
| V6-DECK-01 | Phase 38 | Complete via recovery Phases 46–48 |
| V6-PORT-01 | Phase 39 | Complete via recovery Phases 45–48 |
| V6-PORT-02 | Phase 40 | Complete via recovery Phase 48 |
| V6-QA-01 | Phase 39 | Complete via recovery Phases 45–48 |
| V6-EVID-01 | Phase 39 | Complete via recovery Phases 43–48 |
| V6-DOC-01 | Phase 36 | Complete |
| V6-UAT-01 | Phase 41 | Complete via stricter recovery Phase 48 |
| V6-AUDIT-01 | Phase 41 | Complete via fresh recovery Phase 48 audit |
| V6-REL-01 | Phase 41 | Complete via recovery Phase 48 |
| V6R-GROUND-01 | Phase 42 | Complete |
| V6R-ACQ-01 | Phase 43 | Complete |
| V6R-MINE-01 | Phase 44 | Complete |
| V6R-MAT-01 | Phase 45 | Complete |
| V6R-ANCHOR-01 | Phase 46 | Complete |
| V6R-WEAK-01 | Phase 47 | Complete |
| V6R-UAT-01 | Phase 48 | Complete |
| V6R-REL-01 | Phase 48 | Complete |

**V6 Coverage:**
- v6 requirements: 22 total
- Mapped to exactly one primary phase: 22
- Complete and still accepted, including recovery evidence: 22
- Reopened/in progress/planned: 0
- Unmapped: 0

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-07-30 after v6 quality rejection and milestone reopening*
