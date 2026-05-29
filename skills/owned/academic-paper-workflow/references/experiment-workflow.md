# Experiment Workflow

Use this for comparison experiments, ablation, qualitative case analysis, metrics, robustness, and reproducibility logs.

## Evidence Before Claims

Start from the contribution-evidence map:

```text
claim -> required evidence -> dataset/split -> metric -> baseline -> figure/table
```

Do not write claims first and hunt for selective support later.

## Experiment Package

A publishable empirical paper usually needs:

- main comparison experiments
- ablation experiments
- qualitative cases or error analysis
- robustness, sensitivity, efficiency, or statistical analysis when the target venue expects it
- reproducibility details

The venue ladder determines depth. Stronger venues require stronger comparisons, clearer protocols, and more transparent limitations.

## Comparison Experiments

Define:

- datasets and splits
- metrics
- comparison methods
- source of each number: paper-reported, official leaderboard, or locally reproduced
- tuning budget
- hardware/software environment
- inclusion/exclusion criteria

Fair comparison rules:

- include recent relevant methods and strong known baselines where feasible
- label reproduced vs paper-reported numbers
- explain exclusions explicitly
- use comparable tuning budgets
- do not call the comparison SOTA or comprehensive unless the set actually supports that claim

## Ablation Experiments

Default matrix:

| Variant | Component A | Component B | Component C | Metric 1 | Metric 2 | Notes |
|---|---|---|---|---:|---:|---|
| Baseline | no | no | no | | | |
| +A | yes | no | no | | | |
| +B | no | yes | no | | | |
| +A+B | yes | yes | no | | | |
| Full | yes | yes | yes | | | |

If components interact, explain the interaction and why independent ablation is not meaningful.

## Case Study and Error Analysis

Choose cases by stated criteria:

- representative typical cases
- hard cases
- improvement cases
- failure cases

Do not call cases random unless they were sampled randomly. Include at least one limitation or failure case when making broad claims.

## Metrics and Statistics

Use field-standard metrics first. If no standard exists:

- borrow from adjacent tasks
- justify validity
- add qualitative or human evaluation if appropriate
- state limitations of the metric

For statistical claims:

- state N, split, seed, and test where relevant
- avoid "significant" unless a test supports it
- keep a source of truth for numbers

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

Record failed runs. Final claims must not contradict known failures.

## Weak Results Route

If results are weak:

- reduce venue ambition
- narrow claims
- add error analysis
- choose a more appropriate baseline or dataset
- convert to a finding, limitation, or application paper if defensible

Do not hide material failures while making contradicted claims.
