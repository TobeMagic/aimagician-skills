---
name: aimagician-superpower
description: Use when starting or resuming engineering work, understanding requirements, exploring a codebase, designing or implementing changes, debugging, refactoring, reviewing code, applying spec-driven development, coordinating agents, delegating eligible short execution tasks, or claiming any task, phase, milestone, or delivery complete. Chooses the shortest reliable path from requirement complexity and risk; full planning and independent OpenCode audit are reserved for high-risk, phase/milestone, deployable, or explicitly requested work.
category: build
subcategory: workflow
tags:
  - workflow
  - sdd
  - planning
  - research
  - multi-agent
  - execution
  - verification
  - audit
metadata:
  capability_modules:
    - references/capabilities/intake-and-boundary.md
    - references/capabilities/state-and-continuity.md
    - references/capabilities/project-memory.md
    - references/capabilities/spec-driven-development.md
    - references/capabilities/research-and-discovery.md
    - references/capabilities/engineering-exploration.md
    - references/capabilities/prototyping-and-progressive-discovery.md
    - references/capabilities/ideation-and-scope.md
    - references/capabilities/engineering-design.md
    - references/capabilities/planning-modes.md
    - references/capabilities/agent-orchestration.md
    - references/capabilities/execution-modes.md
    - references/capabilities/engineering-delivery.md
    - references/capabilities/local-first-delivery.md
    - references/capabilities/debugging-and-forensics.md
    - references/capabilities/engineering-review.md
    - references/capabilities/verification-and-uat.md
    - references/capabilities/audit-and-closure.md
    - references/capabilities/domain-gates.md
  preferred_companions:
    - cli-agent-delegator
    - vision-analysis
    - agent-workstream-orchestrator
    - llm-know-how-wiki
    - interface-design
    - webapp-testing
    - github-pr-workflow
    - skill-creator
compatibility:
  tools: [bash, git, node]
  requires: A concrete objective, repository context, and a verifiable completion signal
---

# AImagician Superpower

Use this skill as the goal-first control plane for engineering work. It classifies each request by complexity and risk, then selects the shortest reliable path: deliver the real requirement first, add planning, review, and audit only when they materially reduce risk.

The workflow is complete when the accepted requirement is implemented and verified at a risk-appropriate level, unresolved gaps are explicit, and the handoff is durable enough for another agent to resume without reconstructing the work.

## Goal-First Triage

Classify the request before choosing a workflow. The default path is the shortest route that can complete and verify the real requirement. Do not force phase planning, OpenCode audits, wiki updates, or Linear closure onto quick work.

| Tier | Typical Scope | Default Path |
|---|---|---|
| `Quick` | Docs, config, isolated one-file or low-risk bug fix, test-only change | Minimal context -> implement -> decisive focused check -> PR or target-branch merge when ready -> optional closure |
| `Standard` | Normal feature or bug in a bounded module | One discussion round only if behavior is ambiguous -> implement -> focused tests -> PR -> merge -> optional closure |
| `High` | Cross-module, public API, schema/data migration, security, release, production or deploy behavior, multi-agent coordination | Discuss/brainstorm -> research -> design/plan -> implement -> review + full verification -> independent audit when required -> PR -> merge -> closure |

Escalate when any signal is present: unclear goal, multiple modules, public contract or schema change, data or security impact, deployment or production behavior, hard-to-reverse changes, cross-agent coordination, or the user explicitly requests review/audit. Downgrade when the same work has already been explored, scoped, or accepted.

## Adaptive Start And Resume Gate

Run the full recovery gate for High work, phase/milestone work, resume/compaction/handoff, missing context, or uncertain repository state. Quick and bounded Standard work starts from the latest request and current local evidence; read only sources that can change the next action.

1. Read this `SKILL.md` again before substantive action when context is missing or execution is resumed.
2. Read the latest explicit user request, current git status, and the most recent relevant phase/task/handoff record first. Recent records are navigation aids: they identify the active target, latest checkpoint, and likely source paths.
3. When `.planning/memory/` exists, read `memory.md`, today's note, and only the older note explicitly routed by them or the active task. Memory accelerates recovery but never outranks accepted requirements, canonical project context, code, or runtime evidence.
4. For planning-managed work, resolve authority by reading `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/CONTEXT.md`, the active roadmap/specification, and the requirement records routed by the recent record. `PROJECT.md` defines product intent and boundaries; `CONTEXT.md` is the canonical project-wide architecture, invariants, adopted decisions, verification baseline, and source index.
5. Read project docs and the project knowledge base only when routed by `PROJECT.md`, `CONTEXT.md`, the active work, or a material uncertainty. Do not bulk-load all historical phases, memory notes, or wiki pages.
6. Reconcile sources by authority, not recency alone. A newer explicit user decision wins; a recent summary or memory entry cannot silently override an accepted specification, canonical decision, or runtime evidence.
7. Discuss any unresolved material uncertainty before mutation. Material means it can change observable behavior, architecture, interfaces, stored data, security, scope, acceptance, or an irreversible action. A local, reversible implementation assumption may proceed only when it is recorded and cannot alter those surfaces.
8. Resume from the last verified requirement-backed checkpoint. Do not restart solved discovery or skip a gate that remains relevant.

If adopted `.planning/PROJECT.md` or `.planning/CONTEXT.md` is absent or invalid, alignment blocks phase/milestone/High/resumed execution until repaired. Isolated Quick work may proceed without adopting planning, provided it does not touch shared architecture and its compact contract records the assumption. Never invent missing context. Never present a partial implementation as complete.

## Task Contract Instead Of Universal Goal Lock

For Quick/Standard requests, define a compact contract before editing: objective, acceptance signal, file scope, forbidden scope, and decisive verification. Do not require `.planning/REQUESTS.md`, roadmap alignment, or gate records.

For phase/milestone/High work, use the Active Goal Lock below.

## Active Goal Lock

For phase/milestone/High work, lock execution to the active planning target before changing files:

1. Read the active milestone and phase from `.planning/STATE.md`.
2. Read `.planning/PROJECT.md` and `.planning/CONTEXT.md`, then the active phase's status, literal goal, requirement IDs, and success criteria from `.planning/ROADMAP.md`.
3. Confirm the phase specification repeats the same goal and requirements, and confirm `.planning/REQUIREMENTS.md` maps every requirement to that phase.
4. Run `workflow.mjs validate --gate align`. Do not edit while alignment or the adopted project-context contract fails.
5. Map each planned action to a `REQ-*` item or an explicit `GOAL-*` acceptance criterion. Work with no mapping is scope drift.
6. Run `workflow.mjs trace` at checkpoints and before any completion claim. A passing test is evidence for a mapped criterion, not proof that the phase goal is complete.
7. At phase closure, promote durable architecture, invariant, interface, verification-baseline, or source index changes into `.planning/CONTEXT.md`; record `NONE` with evidence when no promotion is needed.

An off-phase task requires a controlled exception with the parent milestone, parent phase, explicit `USR-*` approval, and a return checkpoint. Do not apply this lock to standalone Quick/Standard tasks unless the project itself is phase-managed.

## Capability Routing

Load the smallest set of modules needed for the current stage.

| Need | Module |
|---|---|
| Goal alignment, boundary, risk classification, first discussion | `references/capabilities/intake-and-boundary.md` |
| State, milestone, resume, pause, progress, checkpoint | `references/capabilities/state-and-continuity.md` |
| Durable project decisions, bounded daily notes, promotion, forgetting, and resume context | `references/capabilities/project-memory.md` |
| Formal specification, ambiguity scoring, locked requirements | `references/capabilities/spec-driven-development.md` |
| Local discovery, architecture mapping, dependency and web research | `references/capabilities/research-and-discovery.md` |
| Repository map, entry points, dependencies, data/control flow, blast radius | `references/capabilities/engineering-exploration.md` |
| Progressive discovery, durable vocabulary, uncertainty maps, prototypes, and context-budget discipline | `references/capabilities/prototyping-and-progressive-discovery.md` |
| Brainstorming, alternatives, decomposition, assumption review | `references/capabilities/ideation-and-scope.md` |
| Domain model, interfaces, invariants, test seams, alternatives, migration design | `references/capabilities/engineering-design.md` |
| Quick, phase, MVP, TDD, repair, and reviewed plans | `references/capabilities/planning-modes.md` |
| Provider-neutral agent roles, prompts, status, independent reviews | `references/capabilities/agent-orchestration.md` |
| Sequential, autonomous, parallel, and worktree execution | `references/capabilities/execution-modes.md` |
| Feature, bug, refactor, performance, architecture, prototype, merge playbooks | `references/capabilities/engineering-delivery.md` |
| Local-first context, CI, preview, deployment, artifact provenance, and postmerge closure | `references/capabilities/local-first-delivery.md` |
| Reproduction, root-cause tracing, waiting, pollution, defense in depth | `references/capabilities/debugging-and-forensics.md` |
| Specification review, engineering quality review, severity, remediation | `references/capabilities/engineering-review.md` |
| Tests, validation, UAT, evidence, requirement traceability | `references/capabilities/verification-and-uat.md` |
| Gap audit, cleanup, learning, milestone closure, handoff | `references/capabilities/audit-and-closure.md` |
| UI, AI, security, data, documents, operations, Git and PR gates | `references/capabilities/domain-gates.md` |

Role prompt templates live under `references/roles/`. Planning templates live under `assets/templates/`. Executable checks live under `scripts/`.

## Engineering Standards, Scaled By Risk

Apply engineering quality with the minimum artifacts that materially improve correctness. Do not generate ceremony for quick work.

- `Quick`: one inline behavior contract, a decisive verification command, and a surgical diff.
- `Standard`: inline or template-backed context map, design options when a meaningful tradeoff exists, and a change brief.
- `High`: use the durable templates for context map, design record, change brief, and review record.

For Standard and High work, do not move from request directly to code without the relevant reasoning. A named artifact is required only when it reduces risk or preserves a decision that must survive the current task:

1. **Behavior contract:** observable current and target behavior, acceptance examples, invariants, and failure behavior.
2. **Context map:** active milestone, phase, literal roadmap goal, acceptance criteria, entry points, ownership boundaries, dependency direction, data/control flow, persisted state, external boundaries, build and delivery path, observability, user-visible result, and likely blast radius.
3. **Design record:** at least two materially viable designs when tradeoffs exist, chosen interfaces and test seams, compatibility, migration, rollback, security, performance, and operability.
4. **Change brief:** ordered vertical slices, exact file scope, integration points, delivery class, local-to-online verification ladder, recovery path, and evidence expected after each slice.
5. **Review record:** specification findings first, then correctness, tests, security, maintainability, extensibility, performance, operability, and diff hygiene.

Scale the detail to risk. For High work, do not skip the reasoning category. Facts need file, command, runtime, or primary-source evidence. Mark inference and unknowns explicitly. Prefer a deep module with a small stable interface over knowledge spread across many callers, but do not introduce abstraction without demonstrated leverage.

Durable engineering artifacts use `assets/templates/engineering-context-map.md`, `assets/templates/engineering-design-record.md`, `assets/templates/engineering-change-brief.md`, and `assets/templates/engineering-review.md`. When the destination is clear but the route is still foggy, use `assets/templates/progressive-discovery-map.md`. When one uncertainty must be tested cheaply, use `assets/templates/engineering-prototype-brief.md`.

## Workload And Specification Gate

Use a formal phase specification when work changes a public behavior or API, schema or stored data, security or permissions, an external integration, a UI or AI contract, production or installation state, multiple modules, multiple agents, multiple phases, or any difficult-to-reverse surface. Also use it whenever material requirements remain ambiguous.

A lightweight inline target is allowed only when all are true:

- no more than two known files are involved;
- the change is reversible and low risk;
- no public contract, data, security, permission, integration, or production behavior changes;
- no user decision remains unresolved;
- one concrete verification command can prove completion.

If any condition fails, read `references/capabilities/spec-driven-development.md` and create or update the phase specification before planning.

Create a `.planning/tasks/<id>.md` record only when the project is planning-managed, the work is phase/milestone/High, or the user explicitly asks for a durable record. Quick/Standard completion may use the PR description and verification evidence instead. Pure discussion or clarification without a completion claim does not create a task record.

## Default Delivery Path

For `Quick` and `Standard` requests, run this path and stop when the requirement is verified:

1. **Lock target:** objective, acceptance signal, file scope, and decisive verification.
2. **Execute:** implement with minimal context and keep the diff surgical.
3. **Verify:** run only the commands that prove the target behavior.
4. **Deliver:** create a PR or push to the target branch; wait only for checks that are actual merge protections.
5. **Close:** update Linear, wiki, or reports only when a ticket or explicit user request exists; use OpenCode + Composio CLI for mechanical closure after merge.

## Canonical Delivery Loop

Use this full loop for High or planning-managed work. Quick and Standard work use the Default Delivery Path, borrowing only the loop stages that materially improve the acceptance signal. Do not read this section as a universal checklist.

### 1. Recover Context

Run the Adaptive Start And Resume Gate and, for phase/milestone work, Active Goal Lock. Establish the last verified state, active milestone and phase, literal roadmap goal, current dirty files, active blockers, and next safe action.

### 2. Establish Target And Boundary

State the measurable objective, user-visible outcome, active milestone and phase, literal roadmap goal, in-scope work, non-goals, constraints, dependencies, rollback or stop conditions, and completion evidence. Classify the work as quick, phase, milestone, spike, repair, review, or follow-up.

### 3. Discuss Baseline Requirements

Ask only questions that change behavior, scope, acceptance, risk, data handling, cost, or architecture. For formal work, create a draft specification with falsifiable requirements and explicit boundaries. Capture rejected and deferred options instead of silently dropping them.

### 4. Research And Brainstorm

Inspect known local sources directly, but do not spend the main context window on a broad multi-file or multi-source scan. Build the objective-sized context map: entry points, module boundaries, data/control flow, side effects, dependency direction, state, external boundaries, build and deployment path, observability, user-visible result, patterns, and blast radius. Mark every full-chain surface `APPLICABLE`, `NOT_APPLICABLE`, or `UNKNOWN`; resolve unknowns that can change scope, design, migration, security, deployment, or acceptance before planning. Use `assets/templates/engineering-context-map.md` when the map must survive the current context. For very large or uncertainty-heavy work, also map the destination, known decisions, current frontier, fog, blockers, and smallest next probe; do not fabricate a full plan through unknown territory. Compare multiple viable approaches. Before broad repository exploration, deep web research, large evidence collection, or visual inspection, load `cli-agent-delegator` and delegate the bounded evidence task to OpenCode. Supply the relevant owned skills and source of truth, then spot-check claims that affect design. Record facts, inference, unknowns, compatibility, risks, and recommendation.

### 5. Re-Discuss And Lock

Bring back findings that affect scope, dependencies, risk, UX, data, schedule, or acceptance. Resolve blocking ambiguity. Lock the specification, boundaries, assumptions, and implementation decisions before planning. If requirements change later, update and re-lock the specification first.

### 6. Plan And Review

Define the behavior contract, durable domain vocabulary, invariants, interfaces, failure semantics, and highest observable test seams. For meaningful design choices, compare at least two structurally different options before committing. Map every requirement ID to vertical slices and exact verification. Classify delivery as `Deployable` or `Non-deployable`; define LOCAL, CI/PREMERGE, risk-based PREVIEW, and POSTMERGE evidence, plus every `ONLINE_ONLY` exception and its failure response. Order dependency waves, define file scopes, checkpoints, migration, rollback or roll-forward, and integration. If one material uncertainty remains, route it to a disposable logic, integration, UI, or operations prototype with an evidence stop condition before production planning. For substantial work, use `cli-agent-delegator` to run a fresh independent plan reviewer; revise until no Blocker or Important finding remains.

### 7. Execute And Checkpoint

For High or planning-managed work, run the alignment gate before editing. Read before editing, preserve user changes, follow local patterns, and keep scope surgical. Deliver one end-to-end tracer slice before broadening. Agree the most public practical test seam, make the first check fail for the intended behavioral reason, then complete one red-green-refactor slice before the next. Reject tautological tests, tests that only replay mocked returns, and horizontal tests disconnected from observable behavior. Use expand-contract for wide refactors and reversible prototypes for uncertain architecture. Give each bounded implementation slice a clean context and finish it with fresh evidence plus a durable handoff; do not rely on lossy mid-slice compaction. Before the controller performs a simple short execution task, apply the `cli-agent-delegator` short-task gate. Eligible test runs, Git checks, reports, localized fixes, and scoped research are delegated by default. Visual evidence is acquired through `vision-analysis`; only sanitized text evidence is delegated for reasoning. Write work must use an exact scope in an isolated worktree. A bounded quick write gets a combined pre-commit review only when the diff, risk, or project policy warrants it. Substantial delegated implementation gets a fresh implementer context, independent specification review, then quality review. Fix and re-review before advancing.

### 8. Verify And UAT

Run all practical LOCAL checks first, narrow before broad, based on the full-chain context and blast radius. Do not use repeated CI or deployment cycles to discover locally observable failures. For planning-managed work, trace original request to requirement, roadmap goal criterion, task, and evidence; otherwise retain the compact task contract and decisive evidence. Exercise observable UAT for user-facing behavior. Record commands, outputs, inspected artifacts, failures, skipped checks, revision provenance, and residual risk. For substantial work, delegate an independent verifier through `cli-agent-delegator`, then rerun or inspect the decisive evidence yourself. For deployable work, this stage establishes premerge readiness; it is not final completion when online evidence is an accepted requirement.

### 9. Audit

When an audit trigger applies, compare the result with the locked specification, original request, non-goals, plan, and evidence. Check integration wiring, regression risk, capability preservation, stale placeholders, security, cleanup, documentation, installation state, delivery provenance, and recovery readiness. Use a fresh OpenCode reviewer through `cli-agent-delegator` against a frozen commit or frozen worktree for premerge review, phase audit, and milestone or completion closure. Reconcile its findings against primary evidence and classify every gap.

An independent OpenCode audit is required for High work, phase/milestone closure, deployable postmerge closure, or explicit user request. Quick/Standard work does not require it; targeted verification plus PR/CI is the normal completion evidence. Visual evidence is acquired through `vision-analysis` with explicit upload authorization, then passed as text to the reviewer. The controller explicitly selects the best suitable free audit model and ordered fallbacks for the task; the runtime appends Agnes once as the final fallback. The audit freezes the reviewed commit or diff and maps `USR-* -> REQ-* -> implementation -> evidence -> audit decision`. Record selection rationale, declared/effective chain, provider, primary model, final model, attempt transitions, fallback reason, session, run status, review point, requirement matrix, Blocker/Important/Nitpick counts, and main-Agent spot-check evidence. Tests passing alone never satisfies an independent audit gate.

Any `FAIL`, `NOT_RUN`, unresolved `Blocker`, or unresolved `Important` keeps the checklist open. Continue implementing and re-auditing while feasible. Defer an Important finding only through an explicit user decision. Stop as blocked only for a genuine external inability, not because the remaining work is inconvenient.

### 10. Handoff And Complete

Update durable state and summarize what changed, what passed, what was not verified, residual risk, current git state, and the exact next action. Quick/Standard work closes when the acceptance signal is verified and delivery is complete. High non-deployable work may close after its explicit `N/A` delivery fields and independent audit pass. Deployable work remains open after merge until the implementation merge SHA, deployed artifact match, required online checks, recovery status, and a fresh postmerge independent audit are recorded. A metadata-only planning closure commit may follow; identify it separately from the implementation artifact.

## Runtime Assistance

From the installed skill directory:

```bash
node scripts/workflow.mjs status --project <path> --phase <phase>
node scripts/workflow.mjs next --project <path> --phase <phase>
node scripts/workflow.mjs planning --project <path> --action status
node scripts/workflow.mjs planning --project <path> --action init --mode tracked --write
node scripts/workflow.mjs planning --project <path> --action init --mode local-private --write
node scripts/workflow.mjs planning --project <worktree> --action attach --write
node scripts/workflow.mjs planning --project <path> --action lock --owner <owner> --expected-revision <n> --write
node scripts/workflow.mjs planning --project <path> --action unlock --lease <lease> --outcome updated --write
node scripts/workflow.mjs validate --project <path> --phase <phase> --gate align
node scripts/workflow.mjs validate --project <path> --phase <phase> --gate spec
node scripts/workflow.mjs validate --project <path> --phase <phase> --gate execute
node scripts/workflow.mjs validate --project <path> --phase <phase> --gate premerge
node scripts/workflow.mjs validate --project <path> --phase <phase> --gate postmerge
node scripts/workflow.mjs trace --project <path> --phase <phase> --format json
node scripts/workflow.mjs init --project <path> --task <task-id> --write
node scripts/workflow.mjs status --project <path> --task <task-id>
node scripts/workflow.mjs validate --project <path> --task <task-id> --gate align
node scripts/workflow.mjs validate --project <path> --task <task-id> --gate premerge
node scripts/workflow.mjs validate --project <path> --task <task-id> --gate postmerge
node scripts/workflow.mjs validate --project <path> --task <task-id> --gate complete
node scripts/workflow.mjs init --project <path> --milestone <milestone-id> --write
node scripts/workflow.mjs validate --project <path> --milestone <milestone-id> --gate complete
node scripts/engineering-route.mjs --kind feature --risk medium --format json
node scripts/engineering-route.mjs --kind refactor --risk high
node scripts/engineering-route.mjs --kind discovery --risk high --format json
node scripts/engineering-route.mjs --kind prototype --risk medium
```

`align` proves the selected work matches the active milestone, phase, literal roadmap goal, requirement mapping, and any controlled exception. `spec` checks locked requirements, USR source mapping, and ambiguity. `plan` checks requirement mapping and plan structure. `execute` additionally requires alignment plus completed research, discussion, context, and accepted plans. `premerge` checks the delivery contract through frozen-review readiness. `postmerge` additionally checks implementation merge SHA, deployed artifact provenance, online evidence, recovery, and closure decision. Phase `complete` requires requirement and goal-criterion evidence, a passing phase audit, summary, project-context promotion or explicit no-change, no unresolved Blocker or Important, and postmerge evidence when a delivery contract is present. Milestone `complete` additionally requires every member phase complete, a milestone-wide requirement and goal audit, and a milestone-level project-context promotion or explicit no-change decision. Task mode supports alignment, premerge, postmerge, and complete gates. `planning` supports tracked storage or a worktree-shared local-private store with explicit lock and revision control; local-private state is excluded from Git and has no automatic backup. `init` previews missing artifacts by default and writes only with `--write`. `engineering-route.mjs` returns the tier, shortest default path, and risk-scaled stages, artifacts, and review axes for a task type; it never edits the project. Runtime commands never install dependencies, modify hooks, commit, push, or overwrite an existing artifact.

## Companion Routing

- Broad exploration, deep research, bounded CLI work, tests, git checks, and independent reviewer roles: `cli-agent-delegator`.
- Authorized image, screenshot, diagram, and other visual evidence acquisition: `vision-analysis`; pass its text evidence to the reasoning agent.
- Independent tracked sessions, provider routing, parallel write lanes, and optional worktree integration: `agent-workstream-orchestrator`.
- Wiki, durable engineering context, secret inventory, and sensitive scans: `llm-know-how-wiki`.
- UI contracts, visual decisions, accessibility, and screenshots: `interface-design` and `webapp-testing`.
- Pull requests, CI, reviewer findings, and merge readiness: `github-pr-workflow`.
- Skill authoring and behavior evals: `skill-creator`.

The main workflow owns routing, state, requirements, and completion. Companion skills own their specialized execution details.

## Failure Handling And Completion Checkpoint

- Missing or conflicting material context: stop mutation and discuss the decision; do not convert uncertainty into an implementation assumption.
- Tool, agent, CI, tracker, or reviewer unavailable: distinguish an actual acceptance or merge protection from optional ceremony, use the safest fallback, and keep core delivery moving when correctness is still provable.
- Test passes but requirement mapping, user-visible behavior, or integration wiring is absent: keep the task open and repair the gap.
- Delegated result conflicts with primary evidence: controller evidence wins after reproduction; record the discrepancy.
- Scope drift or unrelated dirty files: isolate the task, preserve user changes, and return to the locked objective.
- Online-only evidence unavailable: close only the locally provable stage; never claim deployable completion without the accepted online gate.

Before any completion claim, answer with evidence: Is every accepted requirement covered? Is the observable result verified at the correct risk tier? Are Blocker and Important findings zero or explicitly accepted by the user? Is the delivered commit or artifact identified? Can another agent resume from durable state without reconstructing hidden assumptions? Any `no` keeps the checklist open.

## Output Contract

For active work, report the objective and boundary, evidence consulted, decisions, current stage, changed files, verification result, blockers, and next action. Quick/Standard closure may be one concise paragraph when no durable record was requested. Do not create Linear, wiki, or report work before the implementation and its necessary verification unless that information is needed to understand the requirement.

For closure, report requirement coverage, implementation summary, verification and UAT evidence, audit result, checks not run, residual risk, git or installation state, and handoff notes.
