---
name: aimagician-superpower
description: Use when starting or resuming substantial work, clarifying ambiguous requirements, applying spec-driven development, planning or executing a milestone, coordinating agents, debugging systematically, or closing work with verified evidence and a durable handoff.
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
    - references/capabilities/ideation-and-scope.md
    - references/capabilities/planning-modes.md
    - references/capabilities/agent-orchestration.md
    - references/capabilities/execution-modes.md
    - references/capabilities/debugging-and-forensics.md
    - references/capabilities/verification-and-uat.md
    - references/capabilities/audit-and-closure.md
    - references/capabilities/domain-gates.md
  preferred_companions:
    - cli-agent-orchestrator
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
2. Read workflow state and planning sources first: `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, the active phase specification, context, discussion log, research, plans, validation, audit, and latest summary.
3. Read project sources of truth next: `README*`, relevant `docs/`, ADRs, contributor guidance, architecture, API documentation, and repository-specific workflow files.
4. Read the project knowledge base when present: `llm-know-how-wiki`, `.llm-know-how-wiki`, `llm-wiki`, `.llm-wiki`, `wiki/`, or the documented equivalent.
5. Read current git status and separate user changes from planned work.
6. Reconcile the latest user instruction, planning artifacts, project docs, wiki, and filesystem. Newer explicit user decisions win, but contradictions that affect behavior, scope, data, risk, or acceptance must be confirmed.
7. Resume from the last verified checkpoint. Do not restart solved discovery or skip an unfinished gate.

If a source is absent, record that fact and decide whether it is blocking. Do not invent missing context. Never present a partial implementation as complete, and do not stop while accepted work remains feasible.

## Capability Routing

Load the smallest set of modules needed for the current stage.

| Need | Module |
|---|---|
| Goal alignment, boundary, risk classification, first discussion | `references/capabilities/intake-and-boundary.md` |
| State, milestone, resume, pause, progress, checkpoint | `references/capabilities/state-and-continuity.md` |
| Formal specification, ambiguity scoring, locked requirements | `references/capabilities/spec-driven-development.md` |
| Local discovery, architecture mapping, dependency and web research | `references/capabilities/research-and-discovery.md` |
| Brainstorming, alternatives, decomposition, assumption review | `references/capabilities/ideation-and-scope.md` |
| Quick, phase, MVP, TDD, repair, and reviewed plans | `references/capabilities/planning-modes.md` |
| Provider-neutral agent roles, prompts, status, independent reviews | `references/capabilities/agent-orchestration.md` |
| Sequential, autonomous, parallel, and worktree execution | `references/capabilities/execution-modes.md` |
| Reproduction, root-cause tracing, waiting, pollution, defense in depth | `references/capabilities/debugging-and-forensics.md` |
| Tests, validation, UAT, evidence, requirement traceability | `references/capabilities/verification-and-uat.md` |
| Gap audit, cleanup, learning, milestone closure, handoff | `references/capabilities/audit-and-closure.md` |
| UI, AI, security, data, documents, operations, Git and PR gates | `references/capabilities/domain-gates.md` |

Role prompt templates live under `references/roles/`. Planning templates live under `assets/templates/`. Executable checks live under `scripts/`.

## Workload And Specification Gate

Use a formal phase specification when work changes a public behavior or API, schema or stored data, security or permissions, an external integration, a UI or AI contract, production or installation state, multiple modules, multiple agents, multiple phases, or any difficult-to-reverse surface. Also use it whenever material requirements remain ambiguous.

A lightweight inline target is allowed only when all are true:

- no more than two known files are involved;
- the change is reversible and low risk;
- no public contract, data, security, permission, integration, or production behavior changes;
- no user decision remains unresolved;
- one concrete verification command can prove completion.

If any condition fails, read `references/capabilities/spec-driven-development.md` and create or update the phase specification before planning.

## Canonical Delivery Loop

### 1. Recover Context

Run the Mandatory Start And Resume Gate. Establish the last verified state, current dirty files, active blockers, and next safe action.

### 2. Establish Target And Boundary

State the measurable objective, user-visible outcome, in-scope work, non-goals, constraints, dependencies, rollback or stop conditions, and completion evidence. Classify the work as quick, phase, milestone, spike, repair, review, or follow-up.

### 3. Discuss Baseline Requirements

Ask only questions that change behavior, scope, acceptance, risk, data handling, cost, or architecture. For formal work, create a draft specification with falsifiable requirements and explicit boundaries. Capture rejected and deferred options instead of silently dropping them.

### 4. Research And Brainstorm

Inspect local code, tests, docs, configs, schemas, history, and prior artifacts before external research. Compare multiple viable approaches. Delegate broad exploration through `cli-agent-orchestrator` when it would consume substantial main-agent context. Record facts, inference, unknowns, compatibility, risks, and recommendation.

### 5. Re-Discuss And Lock

Bring back findings that affect scope, dependencies, risk, UX, data, schedule, or acceptance. Resolve blocking ambiguity. Lock the specification, boundaries, assumptions, and implementation decisions before planning. If requirements change later, update and re-lock the specification first.

### 6. Plan And Review

Map every requirement ID to one or more atomic tasks and exact verification. Order dependency waves, define file scopes, checkpoints, rollback, and integration. Run an independent plan review for substantial work; revise until requirement coverage and execution clarity pass.

### 7. Execute And Checkpoint

Read before editing, preserve user changes, follow local patterns, and keep scope surgical. Use test-first slices when behavior can be pinned down. For delegated implementation, use a fresh implementer context followed by independent specification review and then quality review. Fix and re-review before advancing.

### 8. Verify And UAT

Run narrow checks first, then the broader suite justified by blast radius. Trace requirement to task to evidence. Exercise observable UAT for user-facing behavior. Record commands, outputs, inspected artifacts, failures, skipped checks, and residual risk.

### 9. Audit

Compare the result with the locked specification, original request, non-goals, plan, and evidence. Check integration wiring, regression risk, capability preservation, stale placeholders, security, cleanup, documentation, and installation state. Classify every gap.

### 10. Handoff And Complete

Update durable state and summarize what changed, what passed, what was not verified, residual risk, current git state, and the exact next action. Completion requires accepted requirements to have passing evidence or an explicit user-approved exclusion.

## Runtime Assistance

From the installed skill directory:

```bash
node scripts/workflow.mjs status --project <path> --phase <phase>
node scripts/workflow.mjs next --project <path> --phase <phase>
node scripts/workflow.mjs validate --project <path> --phase <phase> --gate spec
node scripts/workflow.mjs validate --project <path> --phase <phase> --gate execute
node scripts/workflow.mjs trace --project <path> --phase <phase> --format json
```

`spec` checks locked requirements and ambiguity. `plan` checks requirement mapping and plan structure. `execute` additionally requires completed research, discussion, context, and accepted plans. `complete` requires passing evidence, audit, summary, and UAT when user-facing. `init` previews missing artifacts by default and writes only with `--write`. Runtime commands never install dependencies, modify hooks, commit, push, or overwrite an existing artifact.

## Companion Routing

- Broad external-agent exploration and bounded delegated roles: `cli-agent-orchestrator`.
- Parallel write lanes and worktree integration: `parallel-worktree-pr-flow`.
- Wiki, durable engineering context, secret inventory, and sensitive scans: `llm-know-how-wiki`.
- UI contracts, visual decisions, accessibility, and screenshots: `interface-design` and `webapp-testing`.
- Pull requests, CI, reviewer findings, and merge readiness: `github-pr-workflow`.
- Skill authoring and behavior evals: `skill-creator`.

The main workflow owns routing, state, requirements, and completion. Companion skills own their specialized execution details.

## Output Contract

For active work, report the objective and boundary, evidence consulted, decisions, current stage, changed files, verification result, blockers, and next action.

For closure, report requirement coverage, implementation summary, verification and UAT evidence, audit result, checks not run, residual risk, git or installation state, and handoff notes.
