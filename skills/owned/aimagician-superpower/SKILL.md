---
name: aimagician-superpower
description: Use when starting or resuming engineering work, understanding requirements, exploring a codebase, designing or implementing changes, debugging, refactoring, reviewing code, applying spec-driven development, coordinating agents, delegating eligible short execution tasks, or claiming any task, phase, milestone, or delivery complete. Requires original-request traceability, verified evidence, a fresh independent OpenCode completion audit, and a durable handoff.
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
    - parallel-worktree-pr-flow
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

Use this skill as the control plane for substantial work. It converts an uncertain request into a source-grounded, discussed, specified, planned, implemented, independently reviewed, verified, auditable, and resumable result.

The workflow is not complete when code exists. It is complete only when every accepted requirement has evidence, unresolved gaps are explicit, and another agent can resume without reconstructing the work.

## Mandatory Start And Resume Gate

Before any non-trivial execution, and always after resume, context compaction, handoff, interruption, or uncertain repository state:

1. Read this `SKILL.md` again.
2. Read workflow state and planning sources first: `.planning/REQUESTS.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, the active task or phase specification, context, discussion log, research, plans, validation, audit, and latest summary.
3. Read project sources of truth next: `README*`, relevant `docs/`, ADRs, contributor guidance, architecture, API documentation, and repository-specific workflow files.
4. Read the project knowledge base when present: `llm-know-how-wiki`, `.llm-know-how-wiki`, `llm-wiki`, `.llm-wiki`, `wiki/`, or the documented equivalent.
5. Read current git status and separate user changes from planned work.
6. Reconcile the latest user instruction, planning artifacts, project docs, wiki, and filesystem. Newer explicit user decisions win, but contradictions that affect behavior, scope, data, risk, or acceptance must be confirmed.
7. Resume from the last verified checkpoint. Do not restart solved discovery or skip an unfinished gate.

If a source is absent, record that fact and decide whether it is blocking. Do not invent missing context. Never present a partial implementation as complete, and do not stop while accepted work remains feasible.

## Active Goal Lock

Before changing files, lock execution to the active planning target:

1. Read the active milestone and phase from `.planning/STATE.md`.
2. Read that phase's status, literal goal, requirement IDs, and success criteria from `.planning/ROADMAP.md`.
3. Confirm the phase specification repeats the same goal and requirements, and confirm `.planning/REQUIREMENTS.md` maps every requirement to that phase.
4. Run `workflow.mjs validate --gate align`. Do not edit while alignment fails.
5. Map each planned action to a `REQ-*` item or an explicit `GOAL-*` acceptance criterion. Work with no mapping is scope drift.
6. Run `workflow.mjs trace` at checkpoints and before any completion claim. A passing test is evidence for a mapped criterion, not proof that the phase goal is complete.

An off-phase task requires a controlled exception with the parent milestone, parent phase, explicit `USR-*` approval, and a return checkpoint. Resume the parent phase after the exception. Never relabel partial progress as phase or milestone completion.

## Capability Routing

Load the smallest set of modules needed for the current stage.

| Need | Module |
|---|---|
| Goal alignment, boundary, risk classification, first discussion | `references/capabilities/intake-and-boundary.md` |
| State, milestone, resume, pause, progress, checkpoint | `references/capabilities/state-and-continuity.md` |
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

## Senior Engineering Operating Standard

For any change beyond a known one-file edit, do not move from request directly to code. Establish five engineering artifacts, inline for small work or from `assets/templates/` for substantial work:

1. **Behavior contract:** observable current and target behavior, acceptance examples, invariants, and failure behavior.
2. **Context map:** active milestone, phase, literal roadmap goal, acceptance criteria, entry points, ownership boundaries, dependency direction, data/control flow, persisted state, external boundaries, build and delivery path, observability, user-visible result, and likely blast radius.
3. **Design record:** at least two materially viable designs when tradeoffs exist, chosen interfaces and test seams, compatibility, migration, rollback, security, performance, and operability.
4. **Change brief:** ordered vertical slices, exact file scope, integration points, delivery class, local-to-online verification ladder, recovery path, and evidence expected after each slice.
5. **Review record:** specification findings first, then correctness, tests, security, maintainability, extensibility, performance, operability, and diff hygiene.

Scale the detail to risk; do not skip the reasoning category. Facts need file, command, runtime, or primary-source evidence. Mark inference and unknowns explicitly. Prefer a deep module with a small stable interface over knowledge spread across many callers, but do not introduce abstraction without demonstrated leverage.

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

Every lightweight task that will end in a completion claim uses one `.planning/tasks/<id>.md` record. Preserve or link the original request, accepted decisions, requirement checklist, evidence, fresh independent OpenCode audit, model attempt provenance, finding disposition, and final decision in that file. Pure discussion or clarification without a completion claim does not create a task record.

## Canonical Delivery Loop

### 1. Recover Context

Run the Mandatory Start And Resume Gate and Active Goal Lock. Establish the last verified state, active milestone and phase, literal roadmap goal, current dirty files, active blockers, and next safe action.

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

Run the alignment gate before editing. Read before editing, preserve user changes, follow local patterns, and keep scope surgical. Deliver one end-to-end tracer slice before broadening. Agree the most public practical test seam, make the first check fail for the intended behavioral reason, then complete one red-green-refactor slice before the next. Reject tautological tests, tests that only replay mocked returns, and horizontal tests disconnected from observable behavior. Use expand-contract for wide refactors and reversible prototypes for uncertain architecture. Give each bounded implementation slice a clean context and finish it with fresh evidence plus a durable handoff; do not rely on lossy mid-slice compaction. Before the controller performs a simple short execution task, apply the `cli-agent-delegator` short-task gate. Eligible test runs, Git checks, reports, localized fixes, and scoped research are delegated by default. Visual evidence is acquired through `vision-analysis`; only sanitized text evidence is delegated for reasoning. Write work must use an exact scope in an isolated worktree. A bounded quick write gets one combined pre-commit review. Substantial delegated implementation gets a fresh implementer context, independent specification review, then quality review. Fix and re-review before advancing.

### 8. Verify And UAT

Run all practical LOCAL checks first, narrow before broad, based on the full-chain context and blast radius. Do not use repeated CI or deployment cycles to discover locally observable failures. Trace original request to requirement, roadmap goal criterion, task, and evidence. Exercise observable UAT for user-facing behavior. Record commands, outputs, inspected artifacts, failures, skipped checks, revision provenance, and residual risk. For substantial work, delegate an independent verifier through `cli-agent-delegator`, then rerun or inspect the decisive evidence yourself. For deployable work, this stage establishes premerge readiness; it is not final completion.

### 9. Audit

Compare the result with the locked specification, original request, non-goals, plan, and evidence. Check integration wiring, regression risk, capability preservation, stale placeholders, security, cleanup, documentation, installation state, delivery provenance, and recovery readiness. Use a fresh OpenCode reviewer through `cli-agent-delegator` against a frozen commit or frozen worktree for premerge review, phase audit, and milestone or completion closure. Reconcile its findings against primary evidence and classify every gap.

Every completion claim, including a bounded quick task, must use a fresh independent OpenCode session. Visual evidence is acquired through `vision-analysis` with explicit upload authorization, then passed as text to the reviewer. Audit reasoning follows the DeepSeek-first route; Agnes is a text-reasoning fallback only after a verified DeepSeek usage or quota limit. The audit freezes the reviewed commit or diff and maps `USR-* -> REQ-* -> implementation -> evidence -> audit decision`. Record provider, primary model, final model, attempt chain, fallback reason, session, run status, review point, requirement matrix, Blocker/Important/Nitpick counts, and main-Agent spot-check evidence. Tests passing alone never satisfies this gate.

Any `FAIL`, `NOT_RUN`, unresolved `Blocker`, or unresolved `Important` keeps the checklist open. Continue implementing and re-auditing while feasible. Defer an Important finding only through an explicit user decision. Stop as blocked only for a genuine external inability, not because the remaining work is inconvenient.

### 10. Handoff And Complete

Update durable state and summarize what changed, what passed, what was not verified, residual risk, current git state, and the exact next action. Non-deployable work may close after its explicit `N/A` delivery fields and independent audit pass. Deployable work remains open after merge until the implementation merge SHA, deployed artifact match, required online checks, recovery status, and a fresh postmerge independent audit are recorded. A metadata-only planning closure commit may follow; identify it separately from the implementation artifact.

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

`align` proves the selected work matches the active milestone, phase, literal roadmap goal, requirement mapping, and any controlled exception. `spec` checks locked requirements, USR source mapping, and ambiguity. `plan` checks requirement mapping and plan structure. `execute` additionally requires alignment plus completed research, discussion, context, and accepted plans. `premerge` checks the delivery contract through frozen-review readiness. `postmerge` additionally checks implementation merge SHA, deployed artifact provenance, online evidence, recovery, and closure decision. Phase `complete` requires requirement and goal-criterion evidence, a passing phase audit, summary, no unresolved Blocker or Important, and postmerge evidence when a delivery contract is present. Milestone `complete` additionally requires every member phase complete plus a milestone-wide requirement and goal audit. Task mode supports alignment, premerge, postmerge, and complete gates. `planning` supports tracked storage or a worktree-shared local-private store with explicit lock and revision control; local-private state is excluded from Git and has no automatic backup. `init` previews missing artifacts by default and writes only with `--write`. `engineering-route.mjs` returns the minimum engineering stages, artifacts, and review axes for a task type; it never edits the project. Runtime commands never install dependencies, modify hooks, commit, push, or overwrite an existing artifact.

## Companion Routing

- Broad exploration, deep research, bounded CLI work, tests, git checks, and independent reviewer roles: `cli-agent-delegator`.
- Authorized image, screenshot, diagram, and other visual evidence acquisition: `vision-analysis`; pass its text evidence to the reasoning agent.
- Parallel write lanes and worktree integration: `parallel-worktree-pr-flow`.
- Wiki, durable engineering context, secret inventory, and sensitive scans: `llm-know-how-wiki`.
- UI contracts, visual decisions, accessibility, and screenshots: `interface-design` and `webapp-testing`.
- Pull requests, CI, reviewer findings, and merge readiness: `github-pr-workflow`.
- Skill authoring and behavior evals: `skill-creator`.

The main workflow owns routing, state, requirements, and completion. Companion skills own their specialized execution details.

## Output Contract

For active work, report the objective and boundary, evidence consulted, decisions, current stage, changed files, verification result, blockers, and next action.

For closure, report requirement coverage, implementation summary, verification and UAT evidence, audit result, checks not run, residual risk, git or installation state, and handoff notes.
