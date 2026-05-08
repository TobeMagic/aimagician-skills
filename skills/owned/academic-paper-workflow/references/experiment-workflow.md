# Experiment Workflow

Use this workflow for comparison experiments, ablation, qualitative case analysis, metrics, and experiment logs.

## Experiment Package

A small publishable paper usually needs:

- comparison experiments
- ablation experiments
- case studies or qualitative analysis
- optional robustness/efficiency/sensitivity experiments

The experiment plan must connect directly to the paper claims.

## Comparison Experiments

Purpose: prove the full method is competitive.

Define:

- datasets and splits
- metrics
- comparison methods
- source of each number: paper-reported or locally reproduced
- tuning budget
- hardware/software environment

Comparison selection should be fair:

- include recent relevant methods
- include strong known baselines
- include target-venue expectations
- explain exclusions explicitly
- do not call the set "SOTA comparison" unless it actually covers the strongest methods

Venue-aware comparison intensity:

- top/PhD target: recent top papers and strong baselines are required
- SCI/Q2-Q3 or equivalent: include recent higher-level and same-level methods where possible
- graduation-safe lower-level target: include enough recognized baselines to establish validity
- EI/short papers: may use fewer comparisons, but claims must be narrower

## Ablation Experiments

Purpose: prove each component contributes.

Default matrix:

| Variant | Component A | Component B | Component C | Metric 1 | Metric 2 | Notes |
|---|---|---|---|---:|---:|---|
| Baseline | no | no | no | | | |
| +A | yes | no | no | | | |
| +B | no | yes | no | | | |
| +A+B | yes | yes | no | | | |
| Full | yes | yes | yes | | | |

If components interact:

- explain the interaction
- group components only when there is a real conceptual reason
- include a note saying why independent ablation is not meaningful if that is true

## Case Study / Qualitative Analysis

Purpose: show examples where the method helps.

Choose cases with a stated criterion:

- representative typical cases
- hard cases
- failure cases
- improvement cases

Do not claim random selection unless it was actually random.

Recommended case package:

- input
- baseline result
- proposed method result
- ground truth if available
- short explanation of why the proposed result is better
- at least one limitation or failure case for stronger papers

## Metrics

Use field-standard metrics first.

If no standard metric exists:

- borrow from adjacent tasks
- justify why the metric matches the goal
- add human evaluation or qualitative analysis if needed
- do not invent a metric without explaining validity

## Reproducibility Log

Keep one log per run:

```yaml
run_id:
date:
git_commit:
variant:
dataset:
split:
seed:
config:
hardware:
command:
metrics:
notes:
failure:
```

Record failed runs. You do not need to publish every failure, but final claims must not contradict known failures.

## Integrity Rules

- Do not deliberately under-tune baselines.
- Do not mix paper-reported and reproduced numbers without labeling.
- Do not omit a stronger baseline while implying comprehensive comparison.
- Do not change metrics after seeing results without documenting why.
- Do not cherry-pick case studies while calling them random.
- Do not fabricate missing experiments.

If results are weak:

- reduce target venue ambition
- narrow claims
- add analysis explaining where the method helps
- choose a more appropriate baseline or dataset
