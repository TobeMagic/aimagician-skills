# Literature Workflow

Use this workflow for literature search, paper collection, reading strategy, field mapping, and review-vs-research-paper decisions.

## Search Plan

Start with keyword search, then refine by author, year, venue, abstract keyword, dataset, method name, and citation chain.

Recommended sources:

- Chinese literature: CNKI, school library databases, official journal sites
- English literature: Google Scholar or equivalent, Web of Science, OpenAlex, arXiv, publisher pages
- CS-specific: OpenReview, ACL Anthology, CVF, IEEE/ACM pages when accessible
- Journal metadata: CNKI, LetPub/JCR/CAS, CCF, official school lists

Access policy:

- Prefer legal access: institutional subscriptions, library, OA PDF, arXiv/preprint, author homepage, interlibrary loan, or asking authors.
- Do not recommend illegal paywall bypass.
- Record access gaps honestly.

## Review vs Research Papers

Use review papers to build the field map:

- field history
- taxonomy
- open problems
- datasets
- metrics
- method families
- representative papers

Use research papers to understand individual publishable contributions:

- problem statement
- method contribution
- experimental proof
- venue taste
- figures/tables

If no review exists:

- search adjacent fields
- use top paper introductions as mini-reviews
- build a manual taxonomy from research papers
- flag the direction as high-risk if no adjacent scaffold exists

## Reading Order

Default order:

1. 2-3 review papers or closest substitutes
2. low-bar or accessible papers to learn the minimum paper structure
3. target-venue papers to learn what the intended journal accepts
4. recent top papers to learn stronger baselines, framing, and comparison standards

For graduation-only tasks, do not over-read top papers before finding a feasible baseline.

For PhD/top-tier tasks, read top papers deeply and map contribution patterns.

## Fast Triage

For each paper:

1. Read title, abstract, conclusion.
2. Skim introduction for problem relevance.
3. Check method figure and experiment table.
4. Check dataset and metrics.
5. Check code availability.
6. Decide: must-read, maybe, background, or discard.

Read deeply only if it helps one of:

- field map
- baseline selection
- module candidate
- metric/dataset decision
- target venue writing pattern
- comparison table

## Reading Matrix

Use this CSV schema:

```csv
id,title,year,venue,level,topic,problem,method,dataset,metrics,baselines,ablation,case_study,code_url,pdf_url,role,notes
```

`role` should be one of:

- review
- baseline
- module
- comparison
- target-venue-style
- top-framing
- background

## Literature Map

The literature map should include:

- keyword dictionary in Chinese and English
- field taxonomy
- dataset/metric table
- baseline candidates
- module candidate bank
- target venues observed in the field
- must-read list
- gaps and blocked sources

Do not claim completeness. State search date and source limitations.
