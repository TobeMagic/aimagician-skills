# Roadmap: AImagician Skills

## Overview

AImagician Skills will move from a repository concept to a reliable personal bootstrap system through staged work: define a clean asset and source model, build the one-command install core, land direct skill adapters for Codex/Claude/OpenCode, handle Gemini and plugin differences explicitly, finish verification and operator-facing UX, then grow the owned skill library with high-value personal workflows such as Windows PowerPoint COM/VBA automation. The roadmap is ordered to remove ambiguity first, then add target-specific behavior and owned skills on top of a stable install engine.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Catalog Foundation** - Define owned-skill structure, external source schema, and normalized config rules (completed 2026-03-13)
- [x] **Phase 2: Bootstrap Engine** - Build the one-command install and update workflow with cross-platform execution (completed 2026-03-14)
- [x] **Phase 3: Direct Skill Targets** - Install skills into Codex, Claude Code, and OpenCode user-level locations (completed 2026-03-14)
- [x] **Phase 4: Gemini and Plugins** - Add Gemini-native output plus capability-aware plugin and extension handling (completed 2026-03-14)
- [x] **Phase 5: Verification and Release UX** - Add doctor/list/report flows and finish the bootstrap experience (completed 2026-03-14)
- [x] **Phase 6: Add window-pptx COM/VBA PowerPoint automation skill with discuss-driven project folder workflow** - Add an owned Windows PowerPoint automation skill based on `REQUEST.md`, templates, assets, optional add-in discovery, and native COM execution (completed 2026-05-05)
- [x] **Phase 7: Bootstrap copilot fix and multi-target skill audit** - Fix copilot bootstrap (missing case "copilot"), audit all 7 CLI targets, confirm llm-know-how-wiki everywhere, record historical leftovers (completed 2026-05-11)
- [x] **Phase 8: 蜂巢 Dashboard V3** - Rewrite TUI with group-based Hive panel, source toggle, ANSI 256 colors, and clean install flow (in progress) (completed 2026-06-04)
- [x] **Phase 9: Configuration Scope Foundation** - Implement layered override YAML and independent global/project manifests (completed 2026-06-01)
- [x] **Phase 10: Source Eligibility Resolver** - Implement visible/searchable source states, default-disabled packages, include/exclude priority, and global-only command source rules (completed 2026-06-01)
- [x] **Phase 11: Previewed Managed Sync Engine** - Generate and execute selected-target sync plans that touch only Skillbee-managed items after preview confirmation (completed 2026-06-04)
- [x] **Phase 12: TUI Orchestration Console** - Expose scope, source, include/exclude, eligibility, preview, and Target × Skill report UX in the TUI (completed 2026-06-04)
- [x] **Phase 13: End-to-End Acceptance & Real Global Verification** - Verify automated and real acceptance against PRD checklist, project scope, and true global CLI skills directories (completed 2026-06-04)

## Phase Details

### Phase 1: Catalog Foundation
**Goal**: Define the repository-owned asset model, external source catalog, and validated configuration that all later install behavior depends on
**Depends on**: Nothing (first phase)
**Requirements**: [REPO-01, REPO-02, SRC-01, SRC-02, SRC-03, SRC-04]
**Success Criteria** (what must be TRUE):
  1. User can place a self-authored skill in the repository and have it discovered automatically
  2. User can declare GitHub and command-based external sources in validated configuration
  3. User can enable, disable, and target sources without editing installer code
**Plans**: 3 plans

Plans:
- [x] 01-01: Scaffold package structure, command surface, and repository conventions
- [x] 01-02: Implement owned-skill discovery plus external source schema
- [x] 01-03: Implement normalized asset model and target metadata validation

### Phase 2: Bootstrap Engine
**Goal**: Build the clone-and-run bootstrap workflow with idempotent updates and cross-platform install planning
**Depends on**: Phase 1
**Requirements**: [INST-01, INST-02, INST-03, INST-05, TARG-05]
**Success Criteria** (what must be TRUE):
  1. User can run one npm-executed bootstrap command after cloning the repo
  2. Re-running setup updates installed assets without creating duplicates
  3. The same repository configuration works on Windows and Linux
  4. Setup targets all supported CLIs by default unless the user overrides the selection
**Plans**: 3 plans

Plans:
- [x] 02-01: Build CLI entrypoint and bootstrap command UX
- [x] 02-02: Implement install planning, update logic, and cross-platform path core
- [x] 02-03: Package npm distribution and bootstrap smoke coverage

### Phase 3: Direct Skill Targets
**Goal**: Materialize configured skills into the current user's default homes for the direct skill-folder targets
**Depends on**: Phase 2
**Requirements**: [INST-04, TARG-01, TARG-02, TARG-03]
**Success Criteria** (what must be TRUE):
  1. User can install configured skills into Codex user-level locations
  2. User can install configured skills into Claude Code user-level locations
  3. User can install configured skills into OpenCode user-level locations
  4. Installed skills land in current-user directories and load automatically for those targets
**Plans**: 3 plans

Plans:
- [x] 03-01: Implement Codex adapter and current-user path writer
- [x] 03-02: Implement Claude Code and OpenCode skill adapters
- [x] 03-03: Add manifest-backed sync behavior for direct skill targets

### Phase 4: Gemini and Plugins
**Goal**: Support Gemini with target-native output and add capability-aware plugin or extension handling across supported targets
**Depends on**: Phase 3
**Requirements**: [TARG-04, PLUG-01, PLUG-02, PLUG-03]
**Success Criteria** (what must be TRUE):
  1. User can install Gemini-compatible output from repository-managed assets
  2. User can declare plugin or extension assets separately from skills
  3. Supported targets receive plugin or extension assets through target-native behavior
  4. Unsupported targets are skipped with explicit reasons instead of failing silently
**Plans**: 3 plans

Plans:
- [x] 04-01: Implement Gemini adapter and target-native output generation
- [x] 04-02: Implement plugin and extension schema plus capability matrix
- [x] 04-03: Add supported plugin installers and explicit skip reporting

### Phase 5: Verification and Release UX
**Goal**: Give the user clear proof that setup worked and package the workflow as a polished personal bootstrap tool
**Depends on**: Phase 4
**Requirements**: [VER-01, VER-02, VER-03]
**Success Criteria** (what must be TRUE):
  1. User can list or inspect installed skills for each target after setup
  2. User can see success, failure, and skip status per target in setup output
  3. User can run a doctor or verification command to confirm target wiring
  4. The bootstrap and verification workflow is documented clearly enough for fresh-machine setup
**Plans**: 2 plans

Plans:
- [x] 05-01: Implement list, inspect, and doctor commands
- [x] 05-02: Add final reporting, verification UX, and setup documentation

## Milestone v2.0 — Skillbee V2 功能深化

### Phase 1: 数据模型与配置基建 (2026-05-27)
**Requirements:** [UCG-01, UCG-02, UCG-03]
- [x] F4: ManagerSkillRecord 扩展 customTags 字段
- [x] F5: user-config.yaml 持久化（groups / archivedIds / customTags）
- [x] F5: TUI 自定义分组展示（`@ ` 前缀）
- [x] F9: TUI 归档/取消归档（`x` 键）
- [x] Tests: user-config 模块 6 个单元测试通过

### Phase 2: TUI 品牌重塑 (Complete 2026-05-27)
- [x] F1: 蜜蜂主题 Header/配色/布局 (theme.ts, brand colors, bee ASCII, yellow accents, panel labels)
- [x] F8: 详情面板强化 (install matrix, SKILL.md preview, related skills, command panel overlay)

### Phase 3: 多选与筛选 (Complete 2026-05-27)
- [x] F2: 多 Target 选择器 (t key opens target panel, space toggle, a/A select all/none, tab cycles primaryTarget)
- [x] F6: 多维筛选器 (f key opens filter panel, ↑/↓ dimension, ←/→ cycle, status/target/tag filters)

### Phase 4: 批量操作与报告 (Complete 2026-05-27)
- [x] F3: 批量安装/卸载 — multi-target from Phase 3 enables one-action batch operations; report overlay confirms per-target results
- [x] F10: 安装报告 — modal overlay after install/uninstall shows per-target × per-skill grouped results (✓/○/✗ with skip reasons)

### Phase 5: 概览与打磨 (Complete 2026-05-27)
- [x] F7: 安装概览视图 — `v` toggles list/matrix view; matrix shows skills × selectedTargets with ✓/○/— cells; selection/batch ops work in matrix mode
- [x] P2: 多主题系统 — `T` cycles bee/monokai/nord themes; theme stored in user-config.yaml; border colors update on switch

## Progress

**Execution Order (V1):**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Catalog Foundation | 3/3 | Complete    | 2026-03-13 |
| 2. Bootstrap Engine | 3/3 | Complete    | 2026-03-14 |
| 3. Direct Skill Targets | 3/3 | Complete    | 2026-03-14 |
| 4. Gemini and Plugins | 3/3 | Complete    | 2026-03-14 |
| 5. Verification and Release UX | 2/2 | Complete    | 2026-03-14 |
| 6. Add window-pptx COM/VBA PowerPoint automation skill with discuss-driven project folder workflow | 1/1 | Complete | 2026-05-05 |
| 7. Bootstrap copilot fix and multi-target skill audit | 1/1 | Complete | 2026-05-11 |
| 8. 蜂巢 Dashboard V3 | 0/1 | Complete    | 2026-06-04 |

**Execution Order (V2):**

| Phase | Feature | Status | Completed |
|-------|---------|--------|-----------|
| 1. 数据模型与配置基建 | F4/F5/F9 | Complete | 2026-05-27 |
| 2. TUI 品牌重塑 | F1/F8 | Complete | 2026-05-27 |
| 3. 多选与筛选 | F2/F6 | Complete | 2026-05-27 |
| 4. 批量操作与报告 | F3/F10 | Complete | 2026-05-27 |
| 5. 概览与打磨 | F7/P2 | Complete | 2026-05-27 |
| 8. 蜂巢 Dashboard V3 | Groups/Source/Sync | Complete | 2026-06-04 |

### Phase 6: Add window-pptx COM/VBA PowerPoint automation skill with discuss-driven project folder workflow

**Goal:** Add an owned `window-pptx` skill that guides Windows desktop PowerPoint COM/VBA automation from a project folder containing `REQUEST.md`, templates, assets, data, notes, and output requirements
**Requirements**: TBD
**Depends on:** Phase 5
**Success Criteria** (what must be TRUE):
  1. User can prepare a folder with `REQUEST.md`, templates, assets, and data for a PowerPoint automation job
  2. The skill forces or reuses a discuss pass before real PPT edits to confirm source deck, output policy, macro/add-in policy, and acceptance checks
  3. The skill provides a Windows-native pywin32 helper for add-in discovery and minimal COM smoke editing
  4. iSlide/OKPlus are documented as optional discovered add-ins, while native PowerPoint COM remains the default execution path
**Plans:** 1 plan

Plans:
- [x] 06-01: Add window-pptx skill, helper script, folder contract, and bootstrap documentation

### Phase 7: Bootstrap copilot fix and multi-target skill audit

**Goal:** Fix copilot bootstrap install bug and audit all 7 CLI targets' skill installations
**Depends on:** Phase 6
**Requirements**: N/A (bug fix and audit)
**Success Criteria** (what must be TRUE):
  1. Copilot target receives full bootstrap installs (all owned + catalog skills)
  2. All 7 CLI targets verified: skills installed, manifest synced, llm-know-how-wiki present
  3. Historical leftovers documented per target
  4. Feishu/Lark skill source configured with larksuite/lark-cli, default disabled
**Plans:** 1 plan

Plans:
- [x] 07-01: Fix copilot bootstrap, audit targets, record context in .planning

### Phase 8: 蜂巢 Dashboard V3

**Goal:** Rewrite TUI with group-based Hive panel, source toggle, ANSI 256 colors, and clean install flow
**Depends on:** Phase 7
**Requirements**: PRD §2.1-§4.4
**Success Criteria** (what must be TRUE):
  1. Hive panel shows predefined taxonomy groups (Coding/Research/Design/Documents/Operations/Business) with skill counts
  2. Splash screen renders with correct ANSI 256 colors (amber 214, carbon 235, etc.)
  3. Source toggle (S key) lists external sources and allows enabling/disabling
  4. Install flow cleans stale skills from target directories before installing
  5. Skills without taxonomy entries are hidden (except archived)
**Plans:** 1/1 plans complete

Plans:
- [x] 08-01: V3 dashboard rewrite with groups, source toggle, color fixes, and install sync


## Milestone v3.0 — Configuration Orchestration & Verified Sync

### Phase 9: Configuration Scope Foundation

**Goal:** Implement the PRD's layered configuration model with global/project override YAML and independent manifests.
**Depends on:** Phase 8
**Requirements:** [CFG-01, CFG-02, CFG-03, CFG-04]
**Success Criteria** (what must be TRUE):
  1. Global override config reads/writes `~/.config/skillbee/global/config.yaml`
  2. Project override config reads/writes `<project>/.skillbee/config.yaml` based on the command's current working directory
  3. Global and project manifests are separate and cannot overwrite each other
  4. Durable TUI/config changes write user override YAML only, not repo catalog/taxonomy defaults
**Plans:** 1 plan

Plans:
- [x] 09-01: Scope-aware config and manifest foundation

### Phase 10: Source Eligibility Resolver

**Goal:** Resolve catalog defaults plus user overrides into an explainable install eligibility set.
**Depends on:** Phase 9
**Requirements:** [ELIG-01, ELIG-02, ELIG-03, ELIG-04, ELIG-05, ELIG-06]
**Success Criteria** (what must be TRUE):
  1. Sources can remain visible/searchable while default-disabled for bulk install
  2. `slavingia/skill` is represented as a Business source that is visible/searchable but default-disabled
  3. `include` can select individual skills from default-disabled sources
  4. `exclude` prevents install regardless of source state or include rules
  5. Every eligible/skipped/removed/blocked decision has a user-visible reason
  6. Command-based sources are skipped in project scope with a clear global-only reason
**Plans:** 1 plan

Plans:
- [x] 10-01: Source eligibility and explanation resolver

### Phase 11: Previewed Managed Sync Engine

**Goal:** Convert resolved desired state into preview-confirmed filesystem sync that only affects selected CLI targets and Skillbee-managed items.
**Depends on:** Phase 10
**Requirements:** [SYNC-01, SYNC-02, SYNC-03, SYNC-04, SYNC-05, SYNC-06, SYNC-07]
**Success Criteria** (what must be TRUE):
  1. Sync planning is scoped to the current global/project scope and selected CLI targets
  2. Preview lists create/update/overwrite/remove/skip operations before any write
  3. No CLI skills directory is modified until preview is confirmed
  4. Manual files in target skills directories survive sync and cleanup
  5. Stale Skillbee-managed installs are removed when no longer eligible
  6. Modified Skillbee-managed installs are overwritten by the resolved desired state
**Plans:** 1/1 plans complete

Plans:
- [x] 11-01: Preview and managed-only sync engine

### Phase 12: TUI Orchestration Console

**Goal:** Make the TUI a frontend for scope-aware configuration orchestration, preview, and reporting.
**Depends on:** Phase 11
**Requirements:** [TUI3-01, TUI3-02, TUI3-03, TUI3-04, TUI3-05]
**Success Criteria** (what must be TRUE):
  1. User can switch scope and see scope-specific config, manifest, status, preview, and report information
  2. User can toggle source enabled/default-disabled/disabled state and persist it immediately to override YAML
  3. User can set skill include/exclude and persist it immediately to override YAML
  4. TUI displays taxonomy groups, source groupings, source status, and eligibility reasons
  5. Install/sync shows a pre-execution Target × Skill preview and a final Target × Skill report
**Plans:** 1/1 plans complete

Plans:
- [x] 12-01: TUI orchestration controls, preview, and reports

### Phase 13: End-to-End Acceptance & Real Global Verification

**Goal:** Prove the full PRD through automated tests, manual TUI verification, project-scope installs, and real global-directory acceptance after preview confirmation.
**Depends on:** Phase 12
**Requirements:** [ACC-01, ACC-02, ACC-03, ACC-04, ACC-05]
**Success Criteria** (what must be TRUE):
  1. Automated tests cover include/exclude priority, default-disabled sources, project/global manifest isolation, selected-target sync, and manual-file preservation
  2. Project scope installs into current `pwd` using CLI-specific project paths such as `<project>/.claude/skills`
  3. Command sources skip in project scope with clear reasons
  4. Real global-directory acceptance runs against current-user CLI skills directories only after preview confirmation
  5. `docs/PRD.md` acceptance checklist has no unresolved implementation or verification gaps
**Plans:** 1/1 plans complete

Plans:
- [x] 13-01: Automated, TUI, project-scope, and real global acceptance

## v3.0 Progress

| Phase | Feature | Status | Completed |
|-------|---------|--------|-----------|
| 9. Configuration Scope Foundation | Config/manifest layers | Complete | 2026-06-01 |
| 10. Source Eligibility Resolver | Source states + include/exclude | Complete | 2026-06-01 |
| 11. Previewed Managed Sync Engine | Preview + managed-only sync | Complete    | 2026-06-04 |
| 12. TUI Orchestration Console | TUI controls + reports | Complete    | 2026-06-04 |
| 13. End-to-End Acceptance & Real Global Verification | Automated + real acceptance | Complete    | 2026-06-04 |

**V3 Coverage:**
- v3 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0

## Milestone v4.0 — AImagician Superpower + Skillbird Consolidation

### Phase 14: Skillbird Identity Foundation

**Goal:** Rename package, command, config paths, state paths, and visible CLI/TUI identity from Skillbee to Skillbird / `aimagician_superpower`.
**Depends on:** Phase 13
**Requirements:** [V4-ID-01, V4-ID-02, V4-ID-03]
**Status:** Complete
**Success Criteria**:
  1. Package identity is `aimagician_superpower`
  2. Daily command is `skillbird`
  3. Global/project config and state paths no longer use `.skillbee` or `aimagician-skills`

### Phase 15: External Source Quarantine

**Goal:** Keep external sources as visible references while disabling their default install behavior.
**Depends on:** Phase 14
**Requirements:** [V4-SRC-01, V4-SRC-02]
**Status:** Complete
**Success Criteria**:
  1. Catalog schema defaults external sources to disabled
  2. GSD, Superpowers, selected Claude, UI, and Playwright source files are disabled by default
  3. Users can still explicitly enable sources through overrides

### Phase 16: Owned Skill Consolidation Pass 1

**Goal:** Add the first owned consolidated skills without losing the strongest external workflows.
**Depends on:** Phase 15
**Requirements:** [V4-SKILL-01, V4-SKILL-02, V4-SKILL-03]
**Status:** Complete
**Success Criteria**:
  1. `aimagician-superpower` owns the GSD + Superpowers workflow backbone
  2. `skill-creator`, `mcp-builder`, `interface-design`, and `webapp-testing` exist as owned consolidated skills
  3. `docx`, `pdf`, `pptx`, and `xlsx` are treated as owned document skills

### Phase 17: Six-Category Taxonomy + Formatter

**Goal:** Replace old group names with six categories and add a formatter that writes category frontmatter.
**Depends on:** Phase 16
**Requirements:** [V4-TAX-01, V4-TAX-02, V4-TAX-03]
**Status:** Complete
**Success Criteria**:
  1. Taxonomy categories are `build`, `research`, `design`, `documents`, `operate`, and `strategy`
  2. `skillbird format-skills --check|--write` validates owned skill frontmatter
  3. Category, subcategory, and tag selectors work for search and install

### Phase 18: README + Milestone Handoff

**Goal:** Update repository-facing documentation and GSD milestone state for the consolidation.
**Depends on:** Phase 17
**Requirements:** [V4-DOC-01, V4-GSD-01]
**Status:** Complete
**Success Criteria**:
  1. README explains the merged workflow, Skillbird, global/project install, categories, and external-source policy
  2. `.planning` records v4 as the active milestone with phase gates

### Phase 19: Deep Workflow Merge Review

**Goal:** Discuss and verify the detailed merge of GSD planning, Superpowers planning/writing, and `code-guidelines` execution discipline so capability expands instead of shrinking.
**Depends on:** Phase 18
**Requirements:** [V4-MERGE-01, V4-MERGE-02, V4-MERGE-03]
**Status:** Complete
**Completed:** 2026-06-14
**Success Criteria**:
  1. GSD remains the canonical milestone/phase state machine
  2. Superpowers planning/write-plan behavior is folded into the canonical workflow
  3. `code-guidelines` execution discipline is folded into `aimagician-superpower`

### Phase 20: Skillbird UX Acceptance Loop

**Goal:** Build a development and acceptance loop for Skillbird behavior and styling.
**Depends on:** Phase 19
**Requirements:** [V4-UX-01, V4-UX-02]
**Status:** Complete
**Completed:** 2026-06-14
**Success Criteria**:
  1. TUI styling and category workflow are verified in a PTY smoke test
  2. Category bundle install and project/global behavior are accepted end to end

### Phase 21: Real Install Acceptance

**Goal:** Verify selected global/project installs on real target homes after preview confirmation.
**Depends on:** Phase 20
**Requirements:** [V4-ACC-01, V4-ACC-02]
**Status:** Complete
**Completed:** 2026-06-14
**Success Criteria**:
  1. A global install of core workflow skills succeeds
  2. A project install of document or build category skills succeeds
  3. External default-disabled sources do not mutate target homes unless explicitly enabled

## Milestone v5.0 — Window-PPTX Verified Production Engine

The v5 milestone lowers model-dependence by moving narrative patterns, layout selection, design tokens, editability rules, portable native rendering, and cross-engine delivery checks into deterministic code and registries. It is active and unshipped.

### Phase 22: Window-PPTX Baseline and Safety

**Goal:** Establish a reproducible capability baseline and make every legacy helper route safe before expanding the renderer.
**Depends on:** Phase 21
**Requirements:** [V5-SAFE-01, V5-SAFE-02, V5-SAFE-03, V5-SAFE-04, V5-SAFE-05, V5-SAFE-06, V5-SAFE-07, V5-SAFE-08]
**Status:** Complete
**Completed:** 2026-07-20
**Success Criteria**:
  1. Strict dry-run performs no writes, network access, or COM dispatch and emits one stable summary.
  2. Resolved paths, staging guards, candidate validation, atomic promotion, and pre/post hashes protect source decks.
  3. Attached PowerPoint sessions are preserved, isolated owned sessions are cleaned up, and macro security is restored exactly.
  4. Focused Linux/fake-COM tests and the real Windows PowerPoint safety matrix both pass with recorded evidence.
**Plans:** 1/1 complete. The 13-case native Windows matrix passed twice consecutively.

### Phase 23: DeckPlan and Semantic Rules

**Goal:** Compile versioned semantic content into deterministic narratives, page roles, ranked layouts, and capacity-safe slide sequences.
**Depends on:** Phase 22
**Requirements:** [V5-PLAN-01, V5-PLAN-02, V5-PLAN-03, V5-PLAN-04, V5-PLAN-05]
**Status:** Complete
**Completed:** 2026-07-20
**Success Criteria**:
  1. DeckPlan v1 rejects raw coordinates, arbitrary colors/fonts, COM calls, and uncontrolled code.
  2. Fifteen business archetypes and semantic mapping rules cover the required deck categories.
  3. Capacity splitting, sparse-content preservation, rhythm, decision traces, and low-confidence defaults are deterministic.
**Plans:** 1/1 complete. The semantic compiler passes all focused and full window-pptx gates.

### Phase 24: Design System and Layout Registries

**Goal:** Provide governed themes, components, assets, and page variants so ordinary models select and combine instead of designing from zero.
**Depends on:** Phase 23
**Requirements:** [V5-DESIGN-01, V5-DESIGN-02, V5-DESIGN-03, V5-DESIGN-04, V5-DESIGN-05]
**Status:** Complete (2026-07-20)
**Success Criteria**:
  1. Eight named themes resolve deterministic tokens, brand overrides, contrast, and font fallbacks.
  2. Twenty-four page families provide at least three validated variants each, for at least 72 layouts.
  3. Component and asset policies enforce safe margins, type minima, crop-not-stretch, provenance, and legacy-template quarantine.
**Plans:** 1/1 complete. The final focused suite passes 148 tests, the complete window-pptx suite passes 310 tests, and two independent reviews returned ✅.

### Phase 25: Transactional Core Renderer

**Goal:** Render compiled slides into editable native PowerPoint shapes through a transactional, ratio-aware project runner and CLI.
**Depends on:** Phase 24
**Requirements:** [V5-RENDER-01, V5-RENDER-02, V5-RENDER-03, V5-RENDER-04, V5-RENDER-05]
**Status:** Complete
**Completed:** 2026-07-20
**Success Criteria**:
  1. Core text, shapes, images, masters, footers, grouping, and z-order are editable and deterministic.
  2. Geometry works for 16:9, 4:3, and custom page sizes without fixed-pixel distortion.
  3. Recording fake-COM end-to-end tests verify compiler-to-renderer sequencing before Windows execution.
**Plans:** 1/1 complete. The final focused suite passes 45 tests, the complete window-pptx suite passes 357 tests, and OpenCode session `ses_080fbf8a0ffeOTdhl4bQB77twz` returned PASS with no actionable findings.

### Phase 26: Advanced Editable Objects

**Goal:** Add native charts, tables, diagrams, notes, links, controlled motion, and ratio-aware exports without rasterizing editable content.
**Depends on:** Phase 25
**Requirements:** [V5-OBJECT-01, V5-OBJECT-02, V5-OBJECT-03, V5-OBJECT-04, V5-OBJECT-05]
**Status:** Complete
**Completed:** 2026-07-20
**Success Criteria**:
  1. Expected charts and tables remain native and their data remains editable.
  2. Common business diagrams render as grouped native objects with governed geometry.
  3. Notes, links, optional motion presets, PNG, and PDF work across supported page ratios.
**Plans:** 1/1 complete. The focused suite passes 28 tests, the complete window-pptx suite passes 385 tests, and final OpenCode review returned PASS with no Critical or Important findings.

### Phase 27: Quality Gates and Repair

**Goal:** Inspect five quality layers and repair only safe, measurable defects on isolated candidates.
**Depends on:** Phase 26
**Requirements:** [V5-QA-01, V5-QA-02, V5-QA-03, V5-QA-04, V5-QA-05]
**Status:** Complete
**Completed:** 2026-07-20
**Success Criteria**:
  1. Stable schemas describe package, COM, geometry, visual, deck, editability, and compatibility findings.
  2. Repair runs at most twice and accepts changes only when weighted defects decrease without hard-gate regression.
  3. Customer-delivery gates reject package/reopen failures, source mutation, rasterized slides, missing native objects, and insufficient editable text coverage.
**Plans:** 1/1 complete. The quality pipeline suite passes 19 tests and the complete window-pptx suite passes 404 tests. Multiple OpenCode free-model sessions read the review packet but returned no textual verdict; the mandatory final independent verdict remains Phase 29 gate `V5-UAT-04`.

### Phase 27.1: Huashu Design Reference Assimilation and Visual Calibration (INSERTED)

**Goal:** Convert the strongest Huashu design-planning principles into independently authored, deterministic native-PPTX contracts that raise ordinary-model quality without weakening the DeckPlan raw-design boundary.
**Depends on:** Phase 27
**Requirements:** [V5-REF-01, V5-REF-02, V5-REF-03, V5-REF-04, V5-REF-05, V5-REF-06]
**Status:** Implementation Complete / Evidence Carried Forward
**Success Criteria**:
  1. The upstream source, full commit, archive/tree/license hashes, review subtree, license notice, and accept/adapt/reject decisions are reproducible.
  2. FactStore, BriefPlan, NarrativePlan, BrandSpec, art-direction, layout-selection, QA v2, and two-stage repair contracts are strict, deterministic, and preserve DeckPlan v1 compatibility.
  3. Six independent calibration scenarios produce same-input before/after artifacts, and no external runtime, prompt, media, named style, or HTML-to-PPTX engine is copied.
  4. Phase 28 rejects pre-Huashu evidence and mixed engine/registry/schema/skill/prompt/environment fingerprints.
**Plans:** 1/3 formally complete; implementation tasks in Plans 02-03 are locally verified and their remaining evidence is carried forward without being marked PASS. The full Window-PPTX suite passes 505 historical pre-27.2 tests; six refreshed deterministic calibration packets cover 8-10 slides and 5-7 layout families. The earlier 180-trial manifest remains preserved but becomes pre-27.2/noncanonical after the rendering architecture changes. Portable real-artifact proof moves to Phase 27.2, and the ordinary-model comparison plus clean formal fingerprints move to Phase 28. A later DeepSeek read-only audit completed, but it predates the final portable implementation and cannot satisfy Phase 29's final audit gate.

### Phase 27.2: Portable PptxGenJS Backend and Cross-Engine QA (INSERTED)

**Goal:** Remove COM from governed daily delivery by rendering canonical RenderPlans to deterministic native-editable OOXML, validating the package semantically, and proving the result through an isolated second renderer while retaining PowerPoint as an explicit legacy backend and sampled release certifier.
**Depends on:** Phase 27.1 local implementation; Phase 27.1's formal ordinary-model evidence may remain open because Phase 28 owns it.
**Requirements:** [V5-PORT-01, V5-PORT-02, V5-PORT-03, V5-PORT-04, V5-PORT-05, V5-PORT-06, V5-PORT-07, V5-PORT-08, V5-PORT-09]
**Status:** Complete
**Completed:** 2026-07-21
**Success Criteria**:
  1. Governed `auto` execution uses PptxGenJS 4.0.1 directly from RenderPlan and never silently invokes COM, rasterizes a slide, or accepts an unsupported required capability.
  2. The normalized PPTX is byte-deterministic, identity-bound, native-editable, atomically promoted, and rejected by stable OOXML semantic findings when it diverges from RenderPlan.
  3. Isolated LibreOffice/Poppler rendering produces ratio- and page-count-correct proof artifacts without resaving the PPTX, and Quality-v2 fails closed on missing or invalid rendered evidence.
  4. Six real portable calibration packets pass all portable hard gates; HTML remains proof-only, and PowerPoint doctor/certification is safe, optional, read-only, and non-mutating.
**Plans:** 3/3 complete. The frozen portable calibration produces 56 pages across six scenarios and passes 6/6 package, OOXML semantic, LibreOffice, Poppler, Quality-v2, source-integrity, and byte-determinism gates. The portable engine supports 16:9, 4:3, and custom ratios and seals 200 root evidence hashes; the frozen Window-PPTX suite passes 602/602 and root Vitest passes 101/101. OpenCode session `ses_07c11cc8bffe8HmjcQX73B1We4` independently confirms engineering PASS, visual FAIL, and release NO_GO. Manual review remains deliberately separate: the visual floor improved materially (empty decoration frames 14→0, orphan agenda continuations 2→0, generic classifier titles 28→0, big-number/KPI pages 0→14), but all six decks still fail the requested customer-delivery/senior-designer visual bar. PowerPoint certification and formal weak-model/blind-review evidence remain `NOT_RUN`, so v5.0 is not shippable.

### Phase 28: Weak-Model Benchmark

**Goal:** Measure whether the governed v5 workflow improves ordinary-model quality and repeatability across common business scenarios.
**Depends on:** Phase 27.2 and a clean post-27.2 component fingerprint
**Requirements:** [V5-BENCH-01, V5-BENCH-02, V5-BENCH-03, V5-BENCH-04, V5-BENCH-05]
**Status:** In Progress / Diagnostic Implementation Verified / Release `NO_GO`
**Success Criteria**:
  1. Fifteen frozen scenario briefs cover business reports, proposals, launches, analysis, sales, investors, reviews, strategy, research, training, brand, kickoff, operations, and marketing/e-commerce.
  2. Three arms, two ordinary models, repeats, deterministic scoring, and blind review are reproducible from frozen hashes.
  3. The full-v5 arm uses real PptxGenJS, OOXML, LibreOffice, and Quality-v2 evidence; fake-COM artifacts are not credited as customer delivery evidence.
  4. Release thresholds demonstrate quality, safety, editability, and repeatability improvement without imputing unavailable trials.
**Progress:** The real portable full-v5 path and immutable formal run-contract checks are implemented. Preserved real DeepSeek responses regenerate latest-source business-report r12 (98.75), product-launch r8 (98.75), and data-analysis r9 (99.00) visual-floor diagnostic packets with editable PPTX and portable hard-gate passes. The latest rule/compiler/backend layer adds source-grounded relative metric labels, same-family capacity repair, editorial statements, compact label cards and milestones, governed narrow accent/action rails, and verified native percentage-chart axes/labels. All 212 recorded inventory entries independently match their SHA-256 and size contracts. Every packet remains one of 180, fingerprint-missing, and formally ineligible; the data-analysis iterations also proved that high automatic scores can conceal parser defects, so blind review remains mandatory. The clean complete 180-trial matrix, second model/Nemotron, blind review, and sampled PowerPoint certification are `NOT_RUN`.

### Phase 29: Cross-Engine Acceptance, PowerPoint Sampling, and Closure

**Goal:** Prove portable production reliability across the complete benchmark, certify a frozen sample read-only in real PowerPoint, publish canonical evidence, and close only when every hard gate passes.
**Depends on:** Phase 28
**Requirements:** [V5-UAT-01, V5-UAT-02, V5-UAT-03, V5-UAT-04, V5-UAT-05, V5-UAT-06]
**Status:** Never started / cancelled / replaced by v6 phases / not complete
**Success Criteria**:
  1. The portable matrix and ten-run reliability cases pass for paths, formats, ratios, fonts, locks, isolated LibreOffice profiles, source protection, and edit sentinels.
  2. All fifteen canonical portable outputs have exports, contact sheets, reports, hashes, and final human review evidence; a frozen 10% sample plus every high-risk capability sample passes read-only PowerPoint certification without repair prompts or process residue.
  3. The final post-implementation OpenCode audit is independently verified and the Skill documents portable delivery, capability failures, legacy COM, and sampled certification.
  4. v5.0 remains active if any mapped requirement or customer-delivery hard gate lacks fresh evidence.

## v5.0 Progress

| Phase | Status | Completed |
|-------|--------|-----------|
| 22. Baseline and Safety | Complete | 2026-07-20 |
| 23. DeckPlan and Semantic Rules | Complete | 2026-07-20 |
| 24. Design System and Layout Registries | Complete | 2026-07-20 |
| 25. Transactional Core Renderer | Complete | 2026-07-20 |
| 26. Advanced Editable Objects | Complete | 2026-07-20 |
| 27. Quality Gates and Repair | Complete | 2026-07-20 |
| 27.1 Huashu Design Reference Assimilation and Visual Calibration | Implementation Complete / Evidence Carried Forward | — |
| 27.2 Portable PptxGenJS Backend and Cross-Engine QA | Complete | 2026-07-21 |
| 28. Weak-Model Benchmark | In Progress / Diagnostic Implementation Verified / NO_GO | — |
| 29. Cross-Engine Acceptance, PowerPoint Sampling, and Closure | Planned | — |

**Current milestone:** 7/10 phases complete. Repository total: 31 phase entries, 28 complete. Phase 28 diagnostics validate the portable path but do not count as formal benchmark completion; customer visual acceptance, the complete two-model matrix, clean fingerprint, blind review, and Phase 29 certification remain open.

## Milestone v5.1 — Window-PPTX Reference-Grade Visual Engine

v5.1 supersedes the unshipped v5.0 visual architecture while retaining its portable transaction, OOXML, editability, and verification foundations.

### Phase 30: Reference Visual Baseline and Contracts

**Goal:** Freeze the authorized reference, measurable visual floor, TemplatePack/DesignPack contracts, and failure examples.
**Depends on:** v5.0 portable engineering foundation
**Requirements:** [V51-REF-01, V51-DESIGN-01, V51-DESIGN-02, V51-QA-01, V51-QA-03]
**Status:** Complete

### Phase 31: Authorized TemplatePack and Portable OOXML Adapter

**Goal:** Produce the first reference-grade 15-slide editable work-summary deck without COM.
**Depends on:** Phase 30
**Requirements:** [V51-TPL-01, V51-TPL-02, V51-TPL-03, V51-DESIGN-04]
**Status:** Complete

### Phase 32: VisualPlan, DesignPack v2, and Renderer v2

**Goal:** Compile narrative intent into real component compositions and editable native rendering.
**Depends on:** Phase 31
**Requirements:** [V51-DESIGN-01, V51-DESIGN-02, V51-DESIGN-03, V51-DESIGN-04]
**Status:** Complete — superseded failing R6 with accepted Phase 33/34
reference-method candidates

### Phase 33: Multi-Scenario DesignPacks and Asset System

**Goal:** Complete four extensible DesignPacks and governed asset acquisition/fallback strategies for all fifteen scenarios.
**Depends on:** Phase 32
**Requirements:** [V51-DESIGN-01, V51-DESIGN-03, V51-DESIGN-04]
**Status:** Complete — four DesignPack v2 systems and governed asset
materialization implemented and verified

### Phase 34: Visual Regression, Auto-Repair, and Four-Scenario UAT

**Goal:** Reject the old sparse floor, repair bounded visual defects, and pass four representative real-artifact scenarios.
**Depends on:** Phase 33
**Requirements:** [V51-QA-01, V51-QA-02, V51-QA-03, V51-BENCH-01]
**Status:** Complete — four representative candidates pass portable,
Quality v3, and direct Agnes gates

### Phase 35: Weak-Model Benchmark and Cross-Engine Closure

**Goal:** Refreeze the benchmark, execute ordinary-model trials, complete blind review, and close only with fresh cross-engine evidence.
**Depends on:** Phase 34
**Requirements:** [V51-BENCH-01, V51-UAT-01]
**Status:** `NO_GO` / superseded by v6.0 / not complete. The current work is
preserved at archive commit `e4ed78c` and annotated tag
`window-pptx-v5.1-no-go-20260729`. The final baseline collects 792 Python
tests, with 789 passing and three known regressions. The user rejected the
generated visual floor and replaced the unfinished human-review closure path
with a new quality-first, AI-only v6 milestone.

## Milestone v6.0 — Window-PPTX Template-Intelligence Quality Reset

v6.0 prioritizes reference-grade customer delivery with Codex GPT-5.5 medium,
realistic locked briefs, licensed complete-work visual spines, certified
template intelligence, native-editable portable PPTX, bounded repair, and
independent AI-only visual acceptance. Weak-model distillation is deferred to
v6.1.

### Phase 36: v6 Contracts and Realistic Corpus

**Goal:** Lock ProjectBriefPack v1, private-asset safety, three complete
flagships, twelve realistic skeletons, and v6 traceability.
**Depends on:** v5.1 `NO_GO` archive
**Requirements:** [V6-BRIEF-01, V6-CORPUS-01, V6-DOC-01]
**Status:** Complete — 2026-07-29

### Phase 37: Secure Acquisition and Catalog

**Goal:** Build entitlement-aware private acquisition, quarantine, content
addressing, stable metadata, and a resumable queryable catalog.
**Depends on:** Phase 36
**Requirements:** [V6-ASSET-01, V6-LIB-01]
**Status:** Complete — 2026-07-29

### Phase 38: Certified Template Intelligence

**Goal:** Add TemplatePack v2, Registry v3, ArtDirectionProfile, semantic
retrieval, and certified complete-work visual spines.
**Depends on:** Phase 37 `SEED_READY`; full sync may continue
**Requirements:** [V6-LIB-01, V6-DESIGN-01, V6-DECK-01]
**Status:** Complete — 2026-07-30

### Phase 39: Work-Report Flagship Tracer

**Goal:** Generate the 28-main-slide plus 4-appendix work-report flagship with
GPT-5.5 medium and reference-grade editable output.
**Depends on:** Phase 38
**Requirements:** [V6-DESIGN-01, V6-DECK-01, V6-PORT-01, V6-QA-01,
V6-EVID-01]
**Status:** Complete — 2026-07-30

### Phase 40: Campus and Academic Flagship Tracers

**Goal:** Generate the complete campus-competition and academic-defense decks
from locked facts and licensed visual spines.
**Depends on:** Phase 39 and licensed flagship spines
**Requirements:** [V6-PORT-01, V6-PORT-02, V6-QA-01, V6-EVID-01]
**Status:** Complete — 2026-07-30

### Phase 41: AI-Only Acceptance and Closure

**Goal:** Close only after engineering gates, three independent visual-capable
AI reviews, reference-parity thresholds, and a fresh Agnes completion audit.
**Depends on:** Phases 39–40
**Requirements:** [V6-PORT-02, V6-EVID-01, V6-DOC-01, V6-UAT-01,
V6-AUDIT-01, V6-REL-01]
**Status:** In Progress — blind UAT PASS; completion audit pending

## v6.0 Progress

| Phase | Status | Completed |
|-------|--------|-----------|
| 36. Contracts and Realistic Corpus | Complete | 2026-07-29 |
| 37. Secure Acquisition and Catalog | Complete | 2026-07-29 |
| 38. Certified Template Intelligence | Complete | 2026-07-30 |
| 39. Work-Report Flagship | Complete | 2026-07-30 |
| 40. Campus and Academic Flagships | Complete | 2026-07-30 |
| 41. AI-Only Acceptance and Closure | In Progress | — |
