# Paper Writing and Figures Workflow

Use this workflow for writing the paper story, section structure, figure/table plan, translation, polishing, and similarity hygiene.

## Target-Venue First

Before drafting, pick a target venue or at least a venue tier.

Collect 5-10 accepted papers from:

- same journal/conference
- same task
- same dataset or method family
- recent years

Analyze:

- section order
- contribution wording
- figure/table count
- experiment style
- related-work organization
- limitation style
- reference density

Imitate structure and expectations, not wording.

## Paper Story Chain

Use this chain:

```text
Real problem -> limitation of existing methods -> proposed idea -> why it should work -> evidence -> limitation
```

For each claim, attach evidence:

| Claim | Evidence | Section | Figure/Table |
|---|---|---|---|

Avoid claims that are only rhetorical.

## Standard Small-Paper Structure

Default structure:

- Title
- Abstract
- Introduction
- Related Work
- Method
- Experiments
- Analysis / Ablation / Case Study
- Conclusion
- References
- Optional appendix or supplementary material

Section roles:

- Abstract: plain-language problem, method, key evidence, result
- Introduction: context, gap, contribution
- Related Work: method families and what remains unsolved
- Method: data flow and components
- Experiments: setup, comparison, ablation, cases
- Conclusion: concise summary and limitations/future work

## Three Core Figures

Plan these early:

1. Problem/abstract figure
   - shows what problem is being solved
   - should be understandable without method details

2. Method/framework figure
   - shows data flow
   - use overview first, then detailed submodules if needed
   - avoid a single unreadable giant model diagram

3. Result/case figure
   - shows why the method helps
   - should connect to comparison or qualitative analysis

Optional:

- dataset/statistics figure
- failure case figure
- efficiency/robustness figure

## Tables

Common tables:

- main comparison table
- ablation table
- dataset statistics table
- complexity/parameter/runtime table
- user/human evaluation table if applicable

Every table should support a paper claim.

## Writing by Structural Imitation

For each section:

1. Identify 2-3 target papers with similar section style.
2. Extract the logic pattern, not sentences.
3. Write from the user's actual method and results.
4. Add citations where ideas or comparisons come from.
5. Check whether every paragraph advances the story.

Do not paste-and-rewrite paragraphs from papers. Similarity tools are not a license to copy.

## Language and Polish

For English papers:

- lower-tier: clear and correct English may be enough
- mid-tier: use AI polish plus human review where possible
- top-tier: use expert academic polishing if available

For Chinese papers:

- logic, wording, and formal style matter
- avoid machine-translated awkward phrasing
- use official Word template when required

## Similarity Hygiene

Before submission:

- check obvious copied phrases
- rewrite related work from understanding
- ensure abstract and conclusion are original
- cite all borrowed ideas
- verify figure/table captions are not copied

Passing a similarity score is not enough. The work must be genuinely attributable and truthful.
