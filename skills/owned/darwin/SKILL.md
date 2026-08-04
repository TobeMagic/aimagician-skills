---
name: darwin
description: Use when evaluating, repairing, or improving an existing Skill through measurable baseline tests, targeted edits, independent comparison, regression checks, and a reversible keep-or-revert decision.
category: build
subcategory: skill-quality
tags:
  - skills
  - evaluation
  - optimization
  - regression
  - quality
  - rollback
compatibility:
  tools: [bash, node, python, git]
  requires: An existing Skill, observable task scenarios, a baseline version, and a reversible workspace
---

# Darwin

Improve a Skill as a validated artifact. Every change must have an observed failure or measurable quality target, a bounded edit, independent comparison, and a recorded decision. The goal is reliable behavior, not a longer instruction file.

## Trigger Boundary

Use this Skill when the user asks to optimize, audit, evaluate, evolve, benchmark, or repair an existing Skill. Use `skill-creator` for creating a new Skill from scratch. Use `aimagician-superpower` for product or code changes whose primary target is not Skill quality.

## Quality Loop

### 1. Establish The Baseline

Read the complete Skill, its linked references, scripts, assets, taxonomy entry, and existing evals. Record:

- the intended trigger and non-trigger;
- expected inputs, outputs, and boundaries;
- known failure modes;
- file size and structural checks;
- positive, negative, ambiguity, and regression scenarios.

Run the scenarios without the proposed change when practical. A baseline may be a prior committed version or a documented current behavior, but it must be reproducible enough to compare.

### 2. Diagnose One Bottleneck

Rank failures by impact on routing, correctness, safety, completeness, and maintainability. Choose one highest-value bottleneck per round. Do not change multiple unrelated dimensions in one round; otherwise a score change cannot be attributed.

Prefer explicit instructions over vague advice. Encode known failure mechanisms as trigger-condition, first repair, and fallback tables. Move bulky detail into references when it does not affect routing.

### 3. Make A Small Edit

Change the smallest file or section that addresses the selected failure. Preserve the Skill's purpose, runtime neutrality, and existing successful behaviors. Do not add an installer, update hook, telemetry, external service, or unrelated branding to improve a score.

### 4. Compare Independently

Use a fresh evaluator or separate evaluation context to compare the baseline and candidate on the same scenarios. Prefer paired comparison by the same evaluator over comparing unrelated absolute scores. Return `better`, `worse`, or `tie`, the affected scenarios, and concrete evidence.

The main Agent may inspect the evidence but must not silently replace an independent result with intuition. Critical claims require a second check or direct artifact evidence.

### 5. Keep Or Revert

- Keep only when the candidate is better or no worse without a material regression.
- Revert when the candidate is worse, breaks a boundary, or adds unrelated complexity.
- Treat a tie as a reason to simplify or stop, not to add filler.
- Preserve a traceable change record; use a reversible version-control operation rather than destructive history rewriting.

### 6. Regression And Stop Gate

After each kept edit, rerun the full targeted scenario set, formatter, parser, and any runtime checks. Stop when the target failure is fixed, two rounds produce no meaningful gain, or further changes would expand scope without evidence.

## Evaluation Dimensions

Score or assess only dimensions relevant to the Skill:

1. trigger precision and neighboring-skill routing;
2. actionable specificity;
3. workflow completeness and ordering;
4. failure handling and recovery;
5. boundary and safety clarity;
6. evidence grounding and uncertainty;
7. output contract compliance;
8. maintainability, progressive disclosure, and runtime portability;
9. regression behavior against previously passing scenarios.

Use concrete observations, not a score without an explanation. A lower absolute score from a different evaluator is not proof of regression; paired evidence or reproduced behavior is required.

## Safety And Integrity Rules

- Never self-grade an edit in the same reasoning pass and call it independent validation.
- Never optimize by copying upstream identity, promotional text, installation commands, or hidden side effects.
- Never weaken a safety boundary to pass a positive test.
- Never delete the baseline before the candidate is accepted.
- Never claim an improvement when the scenario did not run; mark it `not run`.
- If the evaluator is unavailable, perform a bounded dry run and label the result provisional.

## Output Contract

Return a concise optimization record containing:

```text
Skill:
Baseline:
Target bottleneck:
Changed files:
Scenarios run:
Evidence:
Decision: keep | revert | stop
Regressions:
Remaining uncertainty:
```

For a multi-round run, preserve a tabular history with timestamp, baseline, candidate, decision, changed dimension, evidence mode, and reason. A Skill is complete only when the acceptance target and regression checks are explicit.
