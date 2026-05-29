# Paper Writing and Figures Workflow

Use this for manuscript structure, figures, tables, translation, polishing, and similarity hygiene.

## Target-Venue First

Before final drafting, choose a target venue or at least a venue tier.

Collect 5-10 accepted papers from:

- the same journal/conference
- the same task
- the same dataset or method family
- recent years

Analyze:

- section order
- contribution wording
- figure/table count
- experiment depth
- related-work organization
- limitation style
- reference density
- data/code/ethics statement style

Imitate structure and expectations, not wording.

## IMRaD Default

Most empirical papers can start from:

- Title
- Abstract
- Introduction
- Related Work
- Method
- Experiments
- Analysis / Ablation / Case Study
- Limitations or Discussion when expected
- Conclusion
- References
- Supplementary material when useful

Section roles:

- Abstract: problem, method, key evidence, scope
- Introduction: CARS-style territory, gap, contribution
- Related Work: method families and remaining gap
- Method: data flow, components, assumptions
- Experiments: setup, comparison, ablation, cases
- Discussion/Limitations: what the evidence means and does not mean
- Conclusion: concise result and future work

## Three Core Figures

Plan these early:

1. Problem or overview figure
   - shows the task or gap
   - understandable without method details

2. Method/framework figure
   - shows data flow and components
   - avoid one unreadable giant diagram

3. Result/case figure
   - shows why the method helps
   - connects to quantitative or qualitative evidence

Optional:

- dataset/statistics figure
- failure case figure
- efficiency/robustness figure
- workflow or taxonomy figure for review papers

## Tables

Common tables:

- main comparison table
- ablation table
- dataset statistics table
- complexity/runtime table
- venue-specific checklist table
- human evaluation table when applicable

Every table should support a claim.

## Paragraph Logic

For each paragraph:

```text
topic sentence -> evidence/citation -> interpretation -> link to next point
```

Avoid paragraphs that only list papers. Related work should compare method families and expose the remaining gap.

## Language and Polish

For English papers:

- entry-level targets: clear and correct English may be enough
- mid/high-tier: polish logic, transitions, and claim precision, not just grammar
- disclose AI use if the venue requires it

For Chinese papers:

- use the official template when required
- check formal academic style, punctuation, numbering, captions, references, and author information

## Similarity Hygiene

Before submission:

- rewrite from understanding
- cite borrowed ideas and methods
- verify captions and figure labels are original
- avoid copied related-work phrasing
- check abstract and conclusion carefully

A low similarity score is not enough. The manuscript must be attributable and truthful.
