# Idea Selection Workflow

Use this for idea, topic, innovation, publication strategy choice, and paper feasibility.

## Idea Must Be Publishable, Not Just Interesting

A paper idea needs:

- a recognizable task, question, or application scenario
- a literature neighborhood with recent papers
- accessible data or evidence
- accepted metrics or defensible evaluation criteria
- at least one baseline or comparison group
- a gap that can be stated without exaggeration
- a venue tier where the evidence level is realistic

Avoid or narrow ideas where data, metric, baseline, or ethical approval would become the whole project.

## Candidate Scorecard

Score each candidate from 1 to 5:

| Idea | Field fit | Novelty room | Baseline/data availability | Evidence cost | Venue fit | Timeline risk | Overall route |
|---|---:|---:|---:|---:|---:|---:|---|

Interpretation:

- high field fit + high baseline/data availability = rapid route candidate
- high novelty + high evidence cost = slow/high-quality candidate
- low novelty + strong evidence = application or incremental venue candidate
- low data/baseline availability = rescue only if the user has unique assets

## Source of Ideas

Search for ideas in:

- recent review papers and "future work" sections
- accepted papers from target venues
- benchmark leaderboards and dataset limitations
- baseline failure cases
- adjacent-field methods that can transfer cleanly
- real application constraints that current methods ignore

Do not invent novelty from buzzwords. Novelty must survive a related-work check.

## Direction Choice

Rapid recognition route:

- choose a hot or established topic with many recent papers
- use public datasets and reproducible baselines
- prefer small, defensible improvements
- select a venue with clear scope fit and realistic review time

High-quality target route:

- choose a sharper gap with stronger novelty
- add robust comparisons, ablations, limitations, and reproducibility
- invest in contribution framing, figures, and writing
- keep a fallback deadline before the first submission

Rescue route:

- reduce task scope
- convert an overlarge idea into a focused case study, benchmark, application, or short paper
- lower venue ambition before lowering integrity

## Innovation Check

A contribution is credible when it answers:

```text
What is missing? -> What do we add? -> Why should it work? -> What evidence proves it? -> Where does it not apply?
```

Common contribution types:

- new method component
- method transfer to a new task/domain
- better training/evaluation protocol
- dataset/resource
- benchmark or taxonomy
- empirical finding or failure analysis
- system/application integration with measurable value

Weak innovation signals:

- only combining trendy terms
- only changing names
- no ablation path
- no target-venue papers with similar contribution scale
- claim depends on unverified "first/SOTA/universal" wording

## Output

Return:

- candidate ideas and scores
- recommended route: fast, high-quality, rescue, or hold
- missing validation papers/data/baselines
- first concrete next step
