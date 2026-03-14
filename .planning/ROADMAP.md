# Roadmap: AImagician Skills

## Overview

AImagician Skills will move from a repository concept to a reliable personal bootstrap system in five phases: define a clean asset and source model, build the one-command install core, land direct skill adapters for Codex/Claude/OpenCode, handle Gemini and plugin differences explicitly, and finish with verification and operator-facing UX. The roadmap is ordered to remove ambiguity first, then add target-specific behavior on top of a stable install engine.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Catalog Foundation** - Define owned-skill structure, external source schema, and normalized config rules (completed 2026-03-13)
- [x] **Phase 2: Bootstrap Engine** - Build the one-command install and update workflow with cross-platform execution (completed 2026-03-14)
- [x] **Phase 3: Direct Skill Targets** - Install skills into Codex, Claude Code, and OpenCode user-level locations (completed 2026-03-14)
- [x] **Phase 4: Gemini and Plugins** - Add Gemini-native output plus capability-aware plugin and extension handling (completed 2026-03-14)
- [ ] **Phase 5: Verification and Release UX** - Add doctor/list/report flows and finish the bootstrap experience

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
- [ ] 05-01: Implement list, inspect, and doctor commands
- [ ] 05-02: Add final reporting, verification UX, and setup documentation

## Progress

**Execution Order:**
Phases execute in numeric order: 2 -> 2.1 -> 2.2 -> 3 -> 3.1 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Catalog Foundation | 3/3 | Complete    | 2026-03-13 |
| 2. Bootstrap Engine | 3/3 | Complete    | 2026-03-14 |
| 3. Direct Skill Targets | 3/3 | Complete    | 2026-03-14 |
| 4. Gemini and Plugins | 3/3 | Complete    | 2026-03-14 |
| 5. Verification and Release UX | 0/2 | Not started | - |
