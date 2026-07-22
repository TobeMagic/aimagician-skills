# CLI Agent Delegator Capability Upgrade

**Date:** 2026-07-22
**Canonical skill:** `cli-agent-delegator`
**Category:** `operate / agent-orchestration`

The recommended scope is global because the delegation policy must be available before work begins in any repository; each invocation still narrows access through its project path, source-of-truth set, and permission envelope.

## Objective

Make external CLI delegation a reliable default for broad evidence work and independent review, while keeping requirements, architecture, risk acceptance, integration, and final judgment with the main Agent.

The previous trigger was dominated by “read-only exploration.” In the observed failure, the main Agent directly scanned a multi-file set of skill, documentation, and test changes before delegating the audit. That consumed main-context budget and proved the trigger surface was too narrow.

## Capability Change

| Area | Previous behavior | Upgraded behavior |
|---|---|---|
| Trigger | Broad read-only repository exploration | Broad or multi-source discovery, deep web research, visual inspection, git/test checks, bounded short writes, and independent review |
| Provider | OpenCode explorer | OpenCode general bounded worker |
| Context | Objective, scope, safety | Full source of truth, accepted decisions, known context, required owned skills, permissions, evidence, git and child-agent policy |
| Models | Free-model list | DeepSeek V4 Flash Free by default; Agnes for vision and DeepSeek failure or rate limit |
| Waiting | Event-aware but partly ambiguous stale handling | Event-based completion with no elapsed-time deadline for a progressing run |
| Writes | Re-discuss and stop | Exact `bounded-write` mode in a clean isolated worktree; commit opt-in after review; push separately authorized |
| Review | Future task type | Plan, specification, quality, verification, phase, milestone, and completion gates |
| Severity | Mixed blocker/high/medium/low and Critical/Important/Minor | `Blocker / Important / Nitpick` |
| Validation | General spot-check | Required checks for paths, representative flow, absence claims, material findings, and decisive commands |

## Skill Architecture

`SKILL.md` owns the trigger gate, routing, controller contract, permission modes, delegation loop, quality gates, and handoff. Progressive references own:

- `prompt-contract.md`: complete prompt envelope, skill loading, permission semantics, child inheritance, progress, safety, and status;
- `discovery-and-research.md`: repository/source discovery, web research, comparison, and visual inspection;
- `bounded-operations-and-execution.md`: git/test checks, reports, bounded isolated writes, and commit policy;
- `independent-review-and-audit.md`: risk-scaled review gates and finding taxonomy;
- `providers/opencode.md`: installed syntax, model routing, event-based waiting, fallback, worktrees, and session handling;
- report templates and behavior evals.

There is no compatibility alias or tombstone for `cli-agent-orchestrator`. Catalog, docs, tests, and installed targets migrate to the new ID.

## Workflow Integration

`aimagician-superpower` now routes:

- broad evidence collection to OpenCode before the main Agent performs the scan;
- substantial plan review to a fresh OpenCode reviewer;
- short locked work, test runs, and git inspection through bounded delegation;
- substantial implementation through specification review, then quality review;
- verification through an independent verifier plus controller rerun;
- phase, milestone, and complete closure through a fresh auditor.

One- or two-file read-only lookups remain direct. A bounded quick write uses one combined pre-commit review. The full gate set applies to substantial work.

## Regression And Acceptance Evidence

Automated checks cover:

- the renamed skill and absence of the old directory;
- strong natural-language trigger phrases in frontmatter and the body;
- the exact observed multi-file-scan regression scenario;
- required skill loading and `NEEDS_CONTEXT` behavior;
- child-agent scope inheritance;
- DeepSeek/Agnes routing and current OpenCode positional prompt syntax;
- event-driven waiting without fixed elapsed deadlines;
- isolated bounded writes, commit and push separation;
- risk-scaled reviewer gates and the unified severity taxonomy;
- Skillbird operate-bundle installation under the new ID.

Final acceptance also requires formatter, targeted tests, full tests, build/typecheck, a fresh OpenCode review, and Codex/OpenCode installation verification.
