# Topic, Baseline, and Module Workflow

Use this workflow to turn a vague research direction into a feasible publishable method plan.

## Topic Positioning

A usable topic has:

- a known task or application scenario
- accessible data
- known metrics
- prior papers to compare with
- at least one feasible baseline
- a story that can be explained without exaggeration

Avoid topics where:

- no review or adjacent field exists
- no dataset exists and data construction is too large
- no metric exists and metric design is itself a major project
- the method would require unrealistic compute
- the only evidence is subjective impression

If the user must stay in a risky topic, narrow it to a smaller task.

## Baseline Selection

Baseline is the foundation. Prefer a baseline that is:

- recent enough
- relevant to the exact task
- open-source or reproducible
- accepted by a credible venue
- compatible with available data and compute
- easy to extend and ablate

Rank candidates:

| Baseline | Year | Venue | Code | Dataset match | Compute | Repro risk | Why choose |
|---|---:|---|---|---|---|---|---|

Practical rule:

- a slightly older but reproducible baseline is often better than a newer closed method
- top venue is useful, but reproducibility and task fit matter more for execution

## Module Candidate Bank

A module is a smaller component or design idea that can be added to or substituted inside the baseline.

For each candidate:

| Module | Source | Claimed role | Implementation cost | Expected metric effect | Ablation proof | Risk |
|---|---|---|---|---|---|---|

Good modules:

- solve a known weakness
- are separable enough for ablation
- have precedent in related work
- are implementable in the current codebase
- do not require a full new system

Bad modules:

- only sound fashionable
- cannot be isolated experimentally
- conflict with baseline assumptions
- require unavailable data or compute

## Method Design

Build a defensible chain:

```text
Problem limitation -> baseline weakness -> module rationale -> measurable expected change -> experiment proof
```

Example structure:

- Baseline handles the main task.
- Module A addresses data noise / temporal redundancy / feature alignment / domain shift / long-tail cases.
- Module B addresses efficiency / robustness / interpretability.
- Combined method has a single coherent story, not a random stack.

## Implementation Plan

Before coding:

- reproduce baseline
- freeze baseline config
- write an experiment log template
- add one module at a time
- run smoke tests
- run full experiments only after smoke tests pass

Keep variants explicit:

- `baseline`
- `baseline+A`
- `baseline+B`
- `baseline+A+B`
- optional modified module variants

## Story Feasibility Check

Before writing:

- Can each module be explained with a real limitation?
- Is there a paper that supports this limitation?
- Does the ablation prove the component matters?
- Does the case study visually support the story?
- Are limitations honestly stated?

If not, revise the method or reduce the claim.
