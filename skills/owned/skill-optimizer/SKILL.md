---
name: skill-optimizer
description: Maintainer-only. Use when auditing, scoring, testing, or improving an existing Agent Skill, including "optimize this skill", "skill review", "skill quality audit", "skill score", "优化 skill", or "达尔文". Do not use to create a new Skill from source material, review ordinary application code, or score a normal delivery.
category: build
subcategory: skills
tags:
  - skills
  - optimization
  - evaluation
  - quality
  - runtime-neutral
  - maintainer-only
metadata:
  capability_modules:
    - references/rubric.md
    - references/experiment-protocol.md
    - references/runtime-neutrality.md
    - assets/templates/experiment-record.json
    - assets/templates/judge-contract.md
  preferred_companions:
    - skill-creator
compatibility:
  tools: [bash, file, agent]
  requires: One or more existing Skill directories and representative user prompts
---

# Skill Optimizer

Improve an existing Skill through measured behavior changes, not prose expansion. Structural quality is a diagnostic signal; the deciding evidence is whether representative tasks become more correct, complete, efficient, and safely routed.

Do not load this during ordinary engineering, research, or design work. It is a maintenance workflow for the Skill system itself.

## Boundary

- Use `skill-creator` to create or merge Skills; use this Skill after a runnable draft exists.
- Use `knowledge-distillation` or `perspective-distillation` when the input is source material rather than an existing Skill.
- Review application code with the engineering workflow, not this rubric.
- Default to a no-commit, no-branch, no-install workflow. Git mutation requires explicit user authorization.

## Inputs

Lock these before scoring:

1. Skill path and intended runtimes.
2. Claimed user outcome and trigger boundary.
3. Two or three representative prompts, including one ambiguity or non-trigger case.
4. Allowed file scope and whether edits are authorized.
5. Required human checkpoints and acceptance evidence.

If the target or representative prompts are missing, inspect the Skill and propose prompts for confirmation before an expensive behavioral evaluation.

## Optimization Loop

### 0. Snapshot

Record the current file hashes or a read-only Git diff. Do not clean, stash, branch, commit, revert, or overwrite unrelated changes. Create a temporary comparison copy outside the Skill only when the user authorizes edits.

### 1. Static Baseline

Run:

```bash
node scripts/audit-skill.mjs --skill <skill-dir> --format json
```

Score dimensions 1-7 and 9 with `references/rubric.md`. Treat missing dimension 8 as `NOT_RUN`; do not manufacture a total score.

### 2. Behavioral Baseline

For each accepted prompt, collect in `assets/templates/experiment-record.json`:

- a baseline response without the target Skill;
- a with-Skill response with the same task, context, tools, and budget;
- factual or executable evidence;
- an independent comparison that is blind to version labels and follows `assets/templates/judge-contract.md`.

At least one prompt must run as a full test. If more than 30% of evaluations are dry runs, mark the effectiveness result invalid. Read `references/experiment-protocol.md`.

**CHECKPOINT:** present the baseline, test prompts, dominant weighted gaps, and uncertainty before editing.

### 3. One-Variable Improvement

Choose the highest weighted observed gap. Change one dimension or one tightly coupled workflow cluster:

- trigger precision and frontmatter;
- explicit workflow inputs and outputs;
- failure branches and recovery;
- human checkpoints;
- executable commands, schemas, or examples;
- progressive references or scripts;
- architecture and duplication;
- behavioral effectiveness;
- anti-pattern and risk guardrails.

Keep the change within the approved scope. Do not add bulk content that no task loads.

### 4. Re-evaluate

Run the same static audit and behavioral prompts with fresh evaluators. Keep a change only when:

1. the target behavior improves;
2. no trigger, safety, or runtime-neutrality regression appears;
3. the weighted score strictly improves when dimension 8 is available;
4. the Skill remains proportionate and navigable.

If evidence regresses, restore only the optimizer's changed files from the recorded snapshot. Never reset the repository.

### 5. Stop And Report

Run at most three rounds. Stop earlier when two consecutive accepted rounds each improve the total by less than two points, or when the remaining gap needs a product decision rather than more instructions.

**CHECKPOINT:** show the diff, before/after evidence, unresolved gaps, and recommendation. Do not install, commit, or publish without a separate request.

## Failure Handling

| Trigger | First response | Fallback |
|---|---|---|
| No executable or factual oracle exists | Define observable output assertions | Mark subjective criteria and require two independent judges |
| External evaluator is unavailable | Preserve prompts and run static checks | Mark dimension 8 `NOT_RUN`; do not claim improvement |
| Evaluators disagree | Compare concrete omissions and regressions | Ask for human judgment on the disputed criterion |
| Target Skill over-triggers | Add explicit non-triggers and sibling routing | Re-run ambiguity and negative prompts |
| A resource path is missing | Repair or remove the reference | Fail the static gate until every shipped path resolves |
| Change grows the Skill without behavior gain | Revert only that change from the snapshot | Move durable detail to a referenced module if still necessary |
| Worktree contains user changes | Limit reads and edits to approved files | Stop if isolation cannot be proven |

## Prohibited Actions

- Do not optimize by adding generic advice, decorative scoring, or repeated summaries.
- Do not let the same agent write, execute, and judge every result without independent review.
- Do not compare different prompts, contexts, models, budgets, or tool access as if they were controlled.
- Do not use a dry run as proof of effectiveness.
- Do not hard-code one agent runtime unless the Skill intentionally targets only that runtime.
- Do not add installer commands, update hooks, creator promotion, or source-repository branding to the runtime Skill.
- Do not mutate Git history, branches, commits, installs, or user files by default.

## Completion Contract

Return:

- target and accepted prompt set;
- static dimension scores with evidence;
- baseline versus with-Skill results;
- experiment mode and evaluator independence;
- accepted and rejected changes by round;
- runtime-neutrality and source-neutrality findings;
- unresolved risks;
- exact validation commands;
- a completed `assets/templates/optimization-report.md` report.

An improved static score without better task behavior is not a successful optimization.
