# AImagician Superpower Capability Merge

This is the maintainer audit for the owned workflow skill. Runtime guidance remains source-neutral; source history and coverage proof stay here.

## Audit Baseline

Local ignored mirrors:

- `skills/owned/aimagician-superpower/references/_external_repos/gsd-build_get-shit-done/`
- `skills/owned/aimagician-superpower/references/_external_repos/obra_superpowers/`

The mirrors live in the primary worktree and are ignored through `.git/info/exclude`; linked worktrees do not inherit these untracked directories. They are audit inputs only and are never installed or committed.

Pinned source revisions reviewed on 2026-07-20:

- GSD: `bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815`
- Superpowers: `6fd4507659784c351abbd2bc264c7162cfd386dc`

Inventory:

- GSD command files: 67
- GSD agent files: 33
- GSD workflow files under `get-shit-done/workflows`: 107 total, including 106 Markdown workflows and one JSON checkpoint template
- GSD templates: 46
- GSD executable files under `get-shit-done/bin`: 80
- GSD SDK source files: 304
- Superpowers skill roots: 14
- Code discipline material: archived in `skills/archived/code-guidelines/`

The previous owned runtime contained one router plus nine short capability modules and no owned scripts, templates, role prompts, or executable gates. It unified terminology but did not preserve the execution machinery needed to claim capability expansion.

## Final Owned Shape

| Layer | Owned implementation |
|---|---|
| Router and mandatory resume gate | `SKILL.md` |
| Intake, state, SDD, research, ideation, planning | `references/capabilities/` modules |
| Agent execution, debugging, verification, audit, domain gates | `references/capabilities/` modules |
| Provider-neutral role prompts | `references/roles/` |
| Project, phase, UI, AI, and security/ops contracts | `assets/templates/` |
| State, gate, trace, and next-action runtime | `scripts/workflow.mjs` |
| Condition waiting and test-state isolation | `scripts/wait-for.mjs`, `scripts/find-polluter.mjs` |
| Trigger and pressure scenarios | `evals/evals.json` |
| Behavioral regression evidence | `tests/skills/aimagician-superpower-runtime.test.ts` |

## Capability Routing

| Capability family | Native owner or route |
|---|---|
| Goal, boundary, risk, baseline discussion | `intake-and-boundary.md` |
| Milestones, phases, state, resume, pause, checkpoints | `state-and-continuity.md` plus workflow runtime |
| Falsifiable requirements, ambiguity interview and lock | `spec-driven-development.md` plus SPEC template and gate |
| Local mapping, dependency and current external research | `research-and-discovery.md`; broad exploration delegates to `cli-agent-orchestrator` |
| Brainstorming, assumptions, option comparison, decomposition | `ideation-and-scope.md` |
| Quick, phase, research, MVP, TDD, repair, review and ultra plans | `planning-modes.md` plus plan template and gate |
| Agent roles, model routing, status and review order | `agent-orchestration.md` plus role prompts |
| Sequential, autonomous, parallel and worktree execution | `execution-modes.md`; write lanes delegate to `parallel-worktree-pr-flow` |
| Root-cause debugging, waiting, pollution and forensics | `debugging-and-forensics.md` plus debugging scripts |
| Tests, evals, UAT, validation and requirement evidence | `verification-and-uat.md` plus trace runtime |
| Requirement audit, cleanup, learning, completion and handoff | `audit-and-closure.md` plus complete gate |
| UI, AI, security, data, docs, operations, Git and PR | `domain-gates.md` plus specialized owned skills |

## GSD Command And Workflow Coverage

The 67 command entry points and their supporting workflows contain many aliases over the same state machine. They are merged by user capability rather than copied as 67 independent skills.

| Source command/workflow family | Result | Status |
|---|---|---|
| `new-project`, `new-milestone`, `phase`, `manager`, `progress`, `health`, `stats` | Project/milestone/phase state, progress, health, and next-action model | Native + runtime |
| `pause-work`, `resume-work`, `thread`, `workspace`, `workstreams`, `surface` | Resume checkpoints, handoff, isolated lanes, workstream ownership | Native + delegated worktrees |
| `spec-phase`, `discuss-phase`, assumption/advisor modes, `ns-context`, `profile-user` | Draft-to-lock requirements, ambiguity scoring, implementation discussion, durable preferences | Native + SPEC gate |
| `explore`, `map-codebase`, `spike`, project/phase/domain research | Bounded local research and delegated broad exploration with validated reports | Native + delegated exploration |
| `ns-ideate`, `sketch`, brainstorming and advisor flows | Alternative generation, simplification, boundary/failure perspectives, convergence | Native |
| `plan-phase`, `mvp-phase`, `ultraplan-phase`, plan convergence, gap planning | Requirement-backed plans, dependency waves, independent plan review, gap closure | Native + plan gate |
| `quick`, `fast`, `autonomous`, `execute-phase` | Risk-scaled execution modes, test-first slices, checkpoints, stop-on-stale-plan | Native |
| `workstreams`, parallel execution, workspace commands | Disjoint write scopes, controller ownership, integration order | Delegated to owned worktree flow |
| `add-tests`, test audit and Nyquist flows | Test-first implementation, behavior tests, test-gap review | Native |
| `verify-work`, `validate-phase`, `audit-uat`, `eval-review`, UI review | Narrow-to-broad validation, requirement evidence, UAT, UI/AI contract review | Native + runtime + domain routes |
| `audit-milestone`, `audit-fix`, `complete-milestone`, `milestone-summary` | Traceability audit, gap classification, closure, archive and handoff | Native + complete gate |
| `debug`, `forensics` and debug-session workflows | Reproduction, evidence preservation, root-cause tracing, hypothesis tests, repair proof | Native + scripts |
| `secure-phase` | Threat, permission, secret, dependency, failure-default and recovery gates | Native + secret/wiki route |
| `ai-integration-phase`, `eval-review` | AI input/output/tool contracts, cost/latency/fallback, datasets, metrics and thresholds | Native AI extension |
| `ui-phase`, `ui-review` | UI states, design system, accessibility, responsive and browser evidence contracts | Native UI extension + design/testing routes |
| `capture`, `inbox`, `review-backlog`, `import`, `ingest-docs`, `extract-learnings`, `docs-update` | Deferred capture, evidence ingestion, learning and durable wiki/docs updates | Native state/audit + wiki route |
| `code-review`, `review`, `pr-branch`, `ship` | Findings-first review, branch/PR/CI readiness and final release evidence | Native review gates + GitHub route |
| `config`, `settings`, namespaced helper commands | Workflow policy represented by skill rules and repository state, without source-specific command aliases | Semantics retained |
| `update`, source cleanup, distribution and community helpers | Upstream maintenance rather than end-user professional guidance | Discarded noise |

## GSD Agent Coverage

The 33 source agents are consolidated into ten provider-neutral roles. Specialization remains in the brief and domain contract rather than in branded agent identities.

| Owned role | Source agent capabilities absorbed |
|---|---|
| Researcher | project/phase/domain/advisor research, codebase and pattern mapping, framework and AI/UI research |
| Requirements analyst | assumptions analysis, user-profile constraints, falsifiability and ambiguity review |
| Planner | roadmap, phase plan, eval plan, integration and gap planning |
| Plan reviewer | plan checker, decision coverage, dependency and execution readiness |
| Implementer | executor and bounded code fixer behavior with test/self-review contract |
| Specification reviewer | requirement compliance and integration contract checking |
| Quality reviewer | code review, security, maintainability, compatibility and test quality |
| Verifier | phase verifier, integration checker, eval/UI/security evidence inspection |
| Debugger | debugger and debug-session management with evidence-preserving escalation |
| Auditor | milestone, evaluation, UI, security, documentation and final coverage audits |

Document classifier/writer/synthesizer/verifier behavior is routed to project docs, the wiki workflow, and document skills. Intelligence updating becomes explicit research refresh; it is not an automatic environment mutation.

## Superpowers Skill Coverage

| Source skill | Merge result |
|---|---|
| `brainstorming` | Reality, simplification, boundary, failure and closure perspectives; alternatives before plan; visual work routed to interface design |
| `writing-plans` | Exact files, atomic tasks, test steps, commands, requirement mapping and independent plan review |
| `executing-plans` | Task checkpoints, stop-on-blocker, stale-plan protection and handoff |
| `subagent-driven-development` | Fresh bounded implementer, four statuses, specification review before quality review, fix/re-review loops |
| `dispatching-parallel-agents` | Independence test, disjoint write scopes, one integration controller |
| `test-driven-development` | Red-green-refactor behavior and anti-pattern checks |
| `systematic-debugging` | Four-stage diagnosis, root-cause tracing, defense in depth, condition waiting and polluter isolation |
| `verification-before-completion` | Fresh evidence outranks claims; complete gate rejects `FAIL` and `NOT_RUN` |
| `using-git-worktrees` | Safety semantics retained; mechanics delegated to the owned parallel worktree skill |
| `requesting-code-review`, `receiving-code-review` | Evidence-backed findings, severity, correction and re-review |
| `finishing-a-development-branch` | Integration, verification, cleanup and accurate branch/PR handoff |
| `writing-skills` | Remains owned by `skill-creator`; not duplicated in the workflow runtime |
| `using-superpowers` | Replaced by the source-neutral mandatory start/resume and capability router |

## Script And Template Decisions

Retained as owned, dependency-free behavior:

- artifact initialization with preview and no overwrite;
- controlled Markdown specification and plan validation;
- an execution-readiness gate that requires research, renewed discussion, implementation context, and accepted plans;
- requirement-to-plan-to-evidence traceability;
- gate-driven status and next-action routing;
- condition-based command waiting with diagnostic timeout;
- filesystem polluter isolation that preserves evidence;
- canonical-path checks that reject initialization through a planning symlink outside the project;
- project, state, roadmap, specification, context, discussion, research, plan, validation, UAT, audit, summary, UI, AI, and security/ops templates;
- provider-neutral role prompts and status protocol.

Delegated rather than duplicated:

- broad CLI-agent execution;
- parallel worktree and PR integration;
- secret inventory, vault and cache scanning;
- browser, visual, document, cloud and PR-specific execution.

Discarded:

- external installers and marketplace wiring;
- automatic updates and hook injection;
- source-specific namespace aliases and branding;
- telemetry, release, community and upstream repository maintenance scripts;
- environment mutation used only to bootstrap the source frameworks;
- the visual companion local server, while retaining its design-discussion outcome through the owned interface workflow.

## Why The Result Is More Than A Union

The final owned system combines capabilities that were previously disconnected:

1. Risk classification prevents heavyweight ceremony for a tiny edit while enforcing formal contracts for dangerous work.
2. Research can revise a draft, but a second discussion and numeric ambiguity gate are required before lock.
3. Stable requirement IDs flow through plans, implementation briefs, independent reviews, validation, audit, and completion.
4. Agent roles are provider-neutral and can use multiple CLI backends without changing the workflow contract.
5. Specification compliance is reviewed before quality, preventing well-written code from hiding the wrong behavior.
6. Runtime commands make state and evidence machine-checkable while leaving all writes explicit and non-destructive.
7. Specialized owned skills extend the workflow without duplicating their implementation or injecting full schemas into the core context.

The acceptance test is behavioral, not line-count parity: zero unmapped user-facing capability families, passing runtime gates and traceability tests, all pressure scenarios covered, source-neutral installed content, and no copied local source mirrors.

## Regression Rule

When editing the owned workflow:

- keep runtime instructions, templates, prompts, and scripts source-neutral;
- add or update behavior tests for executable contracts;
- update pressure scenarios when trigger behavior changes;
- keep source proof in this document, tests, archive notes, or ignored mirrors;
- never claim preservation from string presence alone;
- never install ignored mirrors into target Agent homes.
