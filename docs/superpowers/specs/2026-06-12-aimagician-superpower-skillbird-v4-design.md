# AImagician Superpower / Skillbird v4 Design

## Purpose

v4 turns the current Skillbee repository into `aimagician_superpower`, with `skillbird` as the daily CLI/TUI manager. The goal is to remove noisy upstream installers, make owned skills the default source of truth, merge overlapping workflows from GSD, Superpowers, and selected Claude skills, and keep external sources as disabled reference material unless deliberately curated into `skills/owned`.

## Confirmed Direction

- Product/package identity: `aimagician_superpower`.
- Daily CLI/TUI command: `skillbird`.
- No backward compatibility for `skillbee`, `.skillbee`, or old state paths.
- Default install source: `skills/owned` only.
- External catalogs remain available but disabled by default.
- Local external clones live under `.planning/references/external-skills/` and are excluded from git via `.git/info/exclude`.
- Brand direction: restrained "computer magician white dove" visual system, not a generic bird theme.
- Six category model: Build, Research, Design, Documents, Operate, Strategy.
- Skill frontmatter gets only classification fields: `category`, `subcategory`, `tags`.
- Bundles are auto-derived from owner skill frontmatter, not from a separate bundle file.

## External Source Decisions

| Source | Decision | Notes |
|---|---|---|
| `gsd-build/get-shit-done` and local GSD snapshot | Keep as reference and absorb | MIT according to npm metadata. Use GSD's milestone/phase/plan/execute/verify state model as the main workflow backbone. |
| `obra/superpowers` | Keep as reference and absorb | MIT. Absorb process gates such as brainstorming, writing plans, execution discipline, and verification into the unified workflow. |
| `anthropics/skills` | Partially absorb | `skill-creator`, `frontend-design`, `mcp-builder`, and `webapp-testing` have Apache-2.0 license files and may be curated. `docx`, `pdf`, `pptx`, and `xlsx` contain restrictive license text and are not copied by this implementation plan. If the user manually places those skills in `skills/owned`, Skillbird will classify and manage them. |
| `lackeyjb/playwright-skill` | Absorb into `webapp-testing` | MIT. Do not keep as a separate owner skill. |
| `ibelick/ui-skills` | Absorb into unified UI skill | MIT. Merge baseline, accessibility, metadata, and motion-performance guidance into one interface skill. |
| `pbakaus/impeccable` | Absorb into unified UI skill | Apache-2.0. Use as a UI quality reference. |
| `0xdesign/design-plugin` | Reference only or discard | No license found in the local clone. Do not vendor content directly. |
| `jakubkrehel/make-interfaces-feel-better` | Reference only or discard | No license found in the local clone. Do not vendor content directly. |
| `wshobson/agents` | Discard as a source | Too broad for owner-only workflow. WCAG ideas can be represented in the unified UI skill. |
| `ComposioHQ/awesome-claude-skills` | Discard as a source | 864 connector/automation skills create catalog noise. |
| `larksuite/lark-cli` | Discard | Not needed, and clone failed during reference collection. |
| `slavingia/skills` | Discard | Strategy/Business external source is not desired. |
| `ui-ux-pro-max-skill` | Discard | Command-based installer conflicts with owner-only default behavior. |

## Target Owner Skill Set

| Category | Owner skills |
|---|---|
| Build | `aimagician-superpower`, `code-guidelines`, `skill-creator`, `mcp-builder`, `webapp-testing` |
| Research | `academic-paper-workflow`, `deep-research-system`, `opensource-architecture-research`, `llm-know-how-wiki` |
| Design | `interface-design`, `design-md-brand-router`, `cloudflare-image-gen`, `modelscope_imagegen` |
| Documents | `window-pptx`, `github-readme-highstar`; user-provided `docx`, `pdf`, `pptx`, and `xlsx` are managed if present |
| Operate | `github-pr-workflow`, `linear-issue-workflow`, `gcloud-ops-workflow`, `parallel-worktree-pr-flow` |
| Strategy | `repo-interview-playbook`, `multilingual-diversity-loop` |

## Workflow Consolidation

### `aimagician-superpower`

This becomes the single owner workflow skill for planning and execution. It uses GSD as the planning state backbone and folds Superpowers into internal quality gates.

Required subflows:

- `discuss`: gather requirements and identify scope.
- `new-milestone`: open a milestone in `.planning`.
- `plan`: create phase plans in `.planning/phases`, using GSD structure and Superpowers' plan completeness checks.
- `execute`: execute phase plans with checkpointing and optional parallelism.
- `verify`: run acceptance, test, and completion checks.
- `debug`: run systematic debugging when implementation or tests fail.
- `pause/resume/progress`: preserve and restore working context.

Removed as separate default skills:

- All `gsd-*` wrapper skills.
- Superpowers `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `verification-before-completion`, and related process skills as standalone installs.
- Upstream maintenance/community commands such as update, join-discord, settings, and set-profile.

### `skill-creator`

Claude's Apache-2.0 `skill-creator` is the primary source for skill authoring. Superpowers `writing-skills` contributes skill testing, trigger-description optimization, and pressure-case ideas. The owner version also understands Skillbird classification requirements.

### `interface-design`

This replaces scattered UI/design skills with one main interface skill. It absorbs:

- Claude `frontend-design`
- `baseline-ui`
- `fixing-accessibility`
- `fixing-metadata`
- `fixing-motion-performance`
- `impeccable`
- high-value ideas from `design-lab` and `make-interfaces-feel-better` only when they can be rewritten safely

### `webapp-testing`

This becomes the only browser/webapp testing entry. It absorbs Playwright automation guidance and local webapp validation workflows.

## Skillbird Manager Requirements

Skillbird must support:

- Global and project scopes using `~/.config/skillbird` and `<project>/.skillbird`.
- Owner-only default bootstrap.
- External source visibility with disabled state by default.
- Single-skill install.
- Category, subcategory, and tag installation derived from frontmatter.
- Multi-select TUI installation by category or individual skill.
- Formatter/check command that validates and optionally fixes `category`, `subcategory`, and `tags` in owner skills.
- TUI theme migration from bee/hive language to restrained white-dove magician branding.

## README Requirements

The README should use high-star repository structure and explain:

- What `aimagician_superpower` is.
- Why `skillbird` exists.
- How owner skills, disabled external sources, and reference material relate.
- How the workflow merges GSD, Superpowers, and selected Claude skill practices.
- How to install globally or in a project scope.
- How to install by skill, category, subcategory, or tag.
- How to run formatter, doctor, list, and acceptance checks.
- That external document skills can be manually enabled or provided by the user, but are not bundled as copied owner content by this implementation.

## v4 Milestone Phases

### Phase 14: External Source Triage and Owner Inventory

Disable or discard noisy external sources, preserve local references outside git tracking, and encode the owner inventory and source decisions.

Acceptance:

- External catalogs are disabled by default.
- Feishu/Lark, Composio, slavingia, UI Pro Max, and broad agent collections do not participate in default install.
- GSD, Superpowers, Claude Apache skills, Playwright, and UI references are available only as curation inputs.

### Phase 15: Brand and Path Migration to Skillbird

Rename package, CLI, config paths, state paths, docs, tests, and TUI labels from Skillbee to Skillbird / AImagician Superpower.

Acceptance:

- `skillbird` is the primary binary.
- `skillbee` is not documented or retained as a compatibility path.
- Config and project paths use `skillbird` / `.skillbird`.
- Tests cover the new paths.

### Phase 16: Unified AImagician Superpower Workflow

Create the main owner workflow skill and absorb GSD/Superpowers planning behavior into one entry.

Acceptance:

- One main planning/execution skill replaces scattered GSD/Superpowers default installs.
- Plans live under `.planning/phases`.
- The plan flow includes discuss, plan, execute, verify, debug, pause, resume, and progress.

### Phase 17: Owner Skill Consolidation

Merge duplicate external and current skills into the target owner set.

Acceptance:

- UI skills are consolidated into `interface-design`.
- Browser testing is consolidated into `webapp-testing`.
- Skill authoring is consolidated into `skill-creator`.
- Removed/absorbed skills no longer appear as separate default owner installs.

### Phase 18: Category Formatter and Auto Bundles

Add classification frontmatter and derive install bundles from owner skill metadata.

Acceptance:

- Each owner skill has `category`, `subcategory`, and `tags`.
- CLI and TUI can install by category, subcategory, tag, or explicit skill id.
- The formatter can report and fix missing or invalid classification fields.

### Phase 19: White Dove TUI and README Rewrite

Apply restrained white-dove magician branding and rewrite README using the high-star structure.

Acceptance:

- TUI no longer uses bee/hive branding.
- README documents install, scope, category bundles, external disabled source policy, and workflow consolidation.
- README examples use `skillbird`.

### Phase 20: End-to-End Acceptance

Verify the full migration and management loop.

Acceptance:

- Build and test suites pass.
- CLI search/install/list/doctor/reset work with the new naming and paths.
- Project/global scope installs remain isolated.
- Owner-only bootstrap works.
- External disabled sources stay out of default install.
- Formatter and TUI smoke tests pass.

## Open Constraints

- Restricted external document skills are not copied by this implementation. If the user provides them in `skills/owned`, the manager should classify and install them like any other owner skill.
- Reference clones are local discussion artifacts and should not be committed.
- Current worktree contains unrelated uncommitted changes. Implementation must avoid reverting or overwriting those changes.

