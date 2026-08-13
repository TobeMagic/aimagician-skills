---
name: aimagician-superpower
description: Use when starting or resuming engineering work, understanding a requirement, exploring a codebase, implementing changes, debugging, refactoring, reviewing, applying specification-driven delivery, or deciding whether a task, phase, milestone, or release is complete. Selects the shortest reliable engineering path from scope and risk; expands into planning, research, specialist routes, and independent audit only when they materially protect the requested outcome.
category: build
subcategory: workflow
tags:
  - workflow
  - engineering
  - planning
  - delivery
  - sdd
  - research
  - multi-agent
  - execution
  - verification
  - audit
metadata:
  capability_index: references/capabilities/index.md
compatibility:
  tools: [bash, git, node]
  requires: A concrete objective, repository context when code changes, and a verifiable completion signal
---

# AImagician Superpower

This is the engineering control plane. It decides the smallest reliable route to the real outcome; it does not re-teach every engineering technique. Read [the capability index](references/capabilities/index.md) only for the capability required by the next decision or action.

## 1. Classify Before Acting

State the objective, observable acceptance signal, allowed scope, forbidden scope, and one decisive verification. Then choose a tier.

| Tier | Use when | Minimum route |
|---|---|---|
| `Quick` | Known, reversible, isolated and low-risk change | Read only material local context -> make a surgical change -> run the decisive check -> deliver. |
| `Standard` | Bounded feature, fix, or review with a known module | Resolve only behavior-changing ambiguity -> map the affected path -> implement -> focused verification -> deliver. |
| `High` | Cross-module/public contract, data or schema, security, deployable behavior, difficult reversal, phase/milestone, or material uncertainty | Align and discuss -> research/design/plan -> implement in checkpoints -> review and risk-scaled verification -> audit/close. |

Escalate for an unclear objective, public or stored-data contract, security, production behavior, broad blast radius, irreversible operation, or explicit review/audit request. Downgrade when existing evidence has already answered the question. Do not force planning records, a wiki, a worktree, external agents, or an independent audit on a `Quick` task.

A new or changed callable/API contract is `Standard` at minimum, even when the implementation is isolated; escalate it to `High` when it is a released/public contract or crosses a High-risk surface.

**CHECKPOINT - start:** do not edit until the tier, acceptance signal, and file or behavior boundary are clear. Ask a question only when the answer can change behavior, scope, architecture, safety, or acceptance.

## 2. Recover Only the Context That Matters

For a new `Quick` task, read the request and the known local target. For `Standard`, add the nearest implementation, tests, and repository conventions needed to make the next decision. Reuse evidence already collected instead of scanning again.

For `High`, phase, milestone, resumed, or context-poor work, first read this file, the latest user decision, current repository state, and the active task or handoff. When planning is adopted, read `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/CONTEXT.md`, the active specification or roadmap, and only the project docs/wiki pages they route to. When `.planning/memory/` exists, read `memory.md` and today's note only when the task needs continuity; memory never overrides accepted requirements, source code, or runtime evidence.

If a material uncertainty remains, discuss it before mutation. Never invent missing context, restart proven discovery, or treat a summary as proof.

## 3. Use the Matching Delivery Loop

### 1. Quick and Standard

1. Lock a compact behavior contract: target, acceptance, scope, non-goals, and check.
2. Read the smallest relevant implementation and test surface; follow established local patterns.
3. Make the narrowest change that meets the contract.
4. Run focused verification proportional to blast radius; inspect the diff for unrelated changes.
5. Deliver through the repository's normal branch or PR path. Treat Linear, wiki, reports, and other administrative closure as optional post-delivery work.

### 2. High, phase, milestone, or deployable work

1. Align the active goal, requirement IDs, boundaries, and acceptance evidence. Each planned action must map to an accepted requirement or goal criterion.
2. Discuss the problem and alternatives. Research only the unknowns that can alter scope, design, migration, security, rollout, or acceptance.
3. Re-discuss material findings, then lock requirements, assumptions, and non-goals before planning.
4. Design and plan vertical slices with test seams, failure behavior, recovery, and risk-appropriate delivery evidence.
5. Implement one observable slice at a time. Keep evidence linked to the criterion it proves.
6. Review specification compliance before general code quality; run the local-to-online verification ladder required by the delivery class.
7. Audit requirement coverage before claiming completion. A passing test proves only its mapped criterion, not the whole phase or milestone.

### 3. Requirement Evidence Map

Keep a lightweight map from each accepted requirement to its implementation slice and fresh verification evidence. An unmapped action is scope drift; an unmapped requirement keeps the delivery open.

### 4. Delivery Gate

Use the route helper when it reduces ambiguity:

```bash
node scripts/engineering-route.mjs --kind <feature|bug|refactor|architecture|prototype> --risk <low|medium|high>
node scripts/workflow.mjs validate --project <repo> --phase <phase> --gate <align|spec|plan|execute|premerge|postmerge|complete>
```

For planning-managed High work, the alignment gate must pass before edits, and requirement tracing must be refreshed at checkpoints and closure. Promote durable architecture, invariant, interface, or verification-baseline decisions to `.planning/CONTEXT.md`; explicitly record when nothing requires promotion.

**CHECKPOINT - pre-delivery:** confirm the requested outcome, mapped evidence, and only the verification gates required by current risk before opening a PR or merge path.

## 4. Route Capabilities and Specialists on Demand

The index groups the detailed modules by decision surface. Load the smallest applicable module, not the whole directory.

| Need now | Read first |
|---|---|
| Objective, scope, assumptions, risk, or continuation | [Intake and continuity](references/capabilities/index.md#intake-and-continuity) |
| Formal requirements, research, discovery, or design decision | [Understand and decide](references/capabilities/index.md#understand-and-decide) |
| Feature, bug, refactor, migration, or execution mode | [Build and change](references/capabilities/index.md#build-and-change) |
| Tests, review, UAT, audit, or handoff | [Verify and close](references/capabilities/index.md#verify-and-close) |
| UI, AI, security, data, documents, operations, Git/PR, or third-party SaaS | [Specialist gates](references/capabilities/index.md#specialist-gates) |

Use another owned Skill only when its domain is actually present: `interface-design` for HTML visual work, `webapp-testing` for browser evidence, `github-pr-workflow` for PR operations, `composio-tool-router` for third-party SaaS, `llm-know-how-wiki` for a requested or material project knowledge base, and the relevant document/cloud/vision Skill for those surfaces. They are conditional routes, never default preflight.

## 5. Verify, Close, and Report Honestly

Choose checks that prove the contract, run local checks before expensive remote loops when practical, and stop once sufficient evidence exists. Increase breadth only for a larger blast radius, a failed signal, a merge protection, or an identified risk. Do not use repeated deployment as a substitute for local diagnosis.

For `High`, phase, milestone, deployable, or explicitly audited work, independently review requirement coverage before closure. Keep the checklist open for any `NOT_RUN`, failed, or unmapped criterion. Report facts, inference, skipped checks, blockers, residual risks, and the next owner/action.

**CHECKPOINT - completion:** every accepted requirement has fresh evidence, or is explicitly incomplete. A partial implementation, a green unrelated test suite, or an unavailable optional tool is not completion.

## Failure Handling and Escalation

| Trigger | Stop condition | Fallback |
|---|---|---|
| Objective, boundary, or acceptance is materially ambiguous | Do not mutate the affected decision. | Discuss the ambiguity, then re-lock the contract. |
| Evidence conflicts or a check fails | Do not close from the failed signal. | Preserve it, identify the earliest controllable cause, repair, and rerun the affected check. |
| Discovery expands beyond the task boundary | Stop broad mapping. | Return to the objective, take the smallest distinguishing probe, and defer unrelated mapping. |
| Planning context is missing for a planning-managed target | Do not start High/phase mutation. | Repair or confirm the source of truth. |
| Specialist tool or reviewer is unavailable | Do not block non-required core delivery. | Record the limitation and use a proportionate local alternative. |

## Completion Contract

At a decision point, report: selected tier, objective and boundary, evidence used, material uncertainty or decision, next action, and only the routes or checks that are actually needed. At delivery, report changed behavior, verification evidence, skipped checks and why, remaining risks, and completion status.
