# AImagician Superpower Capability Merge

This document records the merge audit for maintainers. It is not runtime skill guidance.

## Source Inventory

Local ignored mirrors used for audit:

- `skills/owned/aimagician-superpower/references/_external_repos/gsd-build_get-shit-done/`
- `skills/owned/aimagician-superpower/references/_external_repos/obra_superpowers/`

Inventory at merge time:

- GSD command files: 67
- GSD agent files: 33
- GSD workflow files under `get-shit-done/workflows`: 107
- Superpowers skill roots: 14
- Code discipline material: archived in `skills/archived/code-guidelines/`

The mirrors are intentionally excluded from git and filtered from target installation. Runtime skill modules must stay source-neutral.

## Runtime Module Mapping

| Capability family | Runtime owned module |
|---|---|
| Phase discussion, gray-area discovery, context capture, scope creep control | `references/capabilities/intake-and-boundary.md` |
| Milestone state, roadmap, phase artifacts, resume, pause, progress, checkpoints | `references/capabilities/state-and-continuity.md` |
| Local discovery, codebase mapping, dependency research, web verification | `references/capabilities/research-and-discovery.md` |
| Brainstorming, alternatives, decomposition, assumption analysis | `references/capabilities/ideation-and-scope.md` |
| Research planning, phase planning, plan review, MVP mode, TDD mode, gap planning | `references/capabilities/planning-modes.md` |
| Execute-plan discipline, dependency waves, autonomous/fast/quick modes, parallel workers, worktrees | `references/capabilities/execution-modes.md` |
| Verify work, UAT, eval review, regression evidence, failed-check handling | `references/capabilities/verification-and-uat.md` |
| Audit milestone, audit fixes, cleanup, extraction of learnings, completion summary | `references/capabilities/audit-and-closure.md` |
| Code review, debugging, UI review, docs update, security, operations, PR/review gates | `references/capabilities/domain-gates.md` |

## Source Capability Coverage

| Source area | Preserved capability |
|---|---|
| GSD `discuss-phase`, `discuss-phase-assumptions`, `discuss-phase-power` | Target and boundary before planning; adaptive questioning; decision capture; assumptions and deferred ideas. |
| GSD `plan-phase`, `ultraplan-phase`, `plan-review-convergence`, `plan-milestone-gaps` | Research-aware planning; dependency waves; exact file scope; plan review loop; gap closure planning. |
| GSD `execute-phase`, `execute-plan`, `do`, `fast`, `quick`, `autonomous` | Mode-based execution; checkpoints; stale-plan stop conditions; narrow verification after each unit. |
| GSD `verify-work`, `verify-phase`, `validate-phase`, `audit-uat`, `eval-review` | Evidence-first verification; UAT scenarios; validation artifacts; eval and regression review. |
| GSD `audit-milestone`, `audit-fix`, `complete-milestone`, `milestone-summary` | Requirement coverage audit; gap classification; milestone closeout; handoff summary. |
| GSD `new-milestone`, `new-project`, `phase`, `add-phase`, `progress`, `pause-work`, `resume-project` | Durable state, roadmap, phase lifecycle, progress, pause, and resume. |
| GSD `map-codebase`, `ingest-docs`, `docs-update`, `extract-learnings` | Codebase mapping, evidence ingestion, documentation updates, reusable learning capture. |
| GSD `code-review`, `review`, `review-backlog`, `pr-branch`, `ship` | Review flow, backlog handling, branch/PR readiness, shipping checks. |
| GSD `debug`, `forensics`, `diagnose-issues`, `node-repair` | Reproduction-first debugging, root-cause tracing, repair verification. |
| GSD `secure-phase`, security auditor agent | Secrets, environment, and security review gates. |
| GSD UI commands and UI agents | UI research, accessibility, visual verification, and frontend audit routing. |
| GSD research, planning, verifier, executor, audit, doc, and domain agents | Converted into module-level role guidance and parallel-worker rules instead of separate runtime agents. |
| Superpowers `brainstorming` | Alternatives before plan, one-question-at-a-time discussion, decomposition, design approval when needed. |
| Superpowers `writing-plans` | Executable plans with file maps, precise tasks, verification commands, and self-review. |
| Superpowers `executing-plans` | Task-by-task execution, checkpoints, stop-on-blocker behavior, handoff format. |
| Superpowers `test-driven-development` | TDD plan mode and regression-check discipline. |
| Superpowers `systematic-debugging` | Reproduce, isolate, trace, patch cause, regression check. |
| Superpowers `verification-before-completion` | No completion claim without concrete evidence and audit. |
| Superpowers `subagent-driven-development`, `dispatching-parallel-agents` | Parallel worker split rules, write scopes, coordinator review, integration order. |
| Superpowers review and branch finishing skills | Review posture, PR/branch readiness, closure checks. |
| Superpowers `writing-skills` | Kept in `skill-creator`, not duplicated here. |

## Removed From Runtime

- Source branding and history.
- External installation commands.
- Automatic update behavior.
- Hook mutation behavior.
- Marketplace/plugin wiring.
- Community command surfaces that are not part of the owned workflow.

## Regression Rule

When editing `aimagician-superpower`, keep the runtime skill body and capability modules source-neutral. Merge proof belongs in docs, tests, archive notes, or local ignored mirrors.
