# Method Synthesis Workflow

Use this for baseline selection, modular method design, method transfer, protocol adaptation, and target-venue method positioning.

## Core Pattern

```text
target paper type -> strong reproducible baseline -> known limitation -> candidate module -> integration -> ablation -> contribution boundary
```

The method must have traceable sources and measurable evidence. Do not present borrowed modules, code, datasets, or ideas as original.

## Baseline Selection

Prefer baselines that are:

- relevant to the exact task
- recent enough for the target venue
- open-source or reproducible
- accepted by a credible venue
- compatible with data, compute, and timeline
- easy to extend and ablate

Rank candidates:

| Baseline | Year | Venue | Code/Data | Task match | Compute | Repro risk | Why choose |
|---|---:|---|---|---|---|---|---|

Rule: for resource-constrained papers, a slightly older reproducible baseline is often better than a newer closed method.

## Module Bank

A module is a separable component, loss, feature, data process, analysis step, or evaluation protocol that can address a baseline limitation.

| Module | Source | Target limitation | Integration point | Cost | Expected effect | Ablation | Risk |
|---|---|---|---|---|---|---|---|

Good modules:

- address a stated limitation
- can be isolated experimentally
- have precedent in related work
- fit available code/data
- do not create a second full project

Weak modules:

- only follow a trend without a task-specific reason
- conflict with baseline assumptions
- cannot be evaluated independently
- require unavailable data, compute, or annotation
- only explain one highly specific example

## Synthesis Routes

Baseline + modules:

- efficient empirical-paper route
- needs clean ablation and narrow contribution wording
- 2-3 coherent additions are usually easier to defend than many unrelated changes

Method transfer:

- borrow a method family from adjacent tasks
- explain why assumptions transfer
- compare against native-task baselines

Application adaptation:

- adapt known methods to a concrete domain or data condition
- state practical constraints and measurable value

Benchmark/resource paper:

- useful when method novelty is modest but data/evaluation contribution is strong
- needs documentation, statistics, and baseline results

Review/survey:

- useful when field is fragmented and contribution is taxonomy or synthesis
- needs systematic search discipline and clear inclusion/exclusion rules

## Result-Driven Contribution Clarification

When experiments already exist, let the verified evidence determine contribution boundaries:

- identify where the method improves, stays neutral, or fails
- align each module with the limitation it plausibly addresses
- strengthen claims only where comparison, ablation, or case analysis supports them
- state limitations near the relevant claim

This keeps the paper persuasive without inventing unsupported problems.

## Target-Venue Adaptation

Before finalizing the method section, inspect 5-10 recent accepted papers from the intended venue:

- contribution scale
- common baseline strength
- number of ablations
- figure/table density
- limitation and reproducibility style

Use the pattern to calibrate evidence depth and wording. Do not copy text, figures, or uncredited design.

## Output

Return:

- chosen baseline and backup baseline
- module bank
- synthesis route
- ablation matrix
- contribution boundary
- implementation/evidence next step
