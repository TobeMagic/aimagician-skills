# Literature Workflow

Use this for literature search, paper collection, reading strategy, field mapping, and review-vs-research-paper decisions.

## Search Strategy

Start with a clear question, then expand:

```text
topic words -> synonyms -> task/dataset/metric words -> method names -> authors -> venues -> citation chains
```

Recommended sources:

- Chinese literature: CNKI, Wanfang/VIP when available, official journal sites, school library databases
- English literature: Google Scholar or equivalent, Web of Science, Scopus, OpenAlex, Crossref, publisher pages
- Computer science: OpenReview, ACL Anthology, CVF, IEEE Xplore, ACM Digital Library, arXiv, DBLP
- Venue metadata: official journal/conference sites, Web of Science Master Journal List, Scopus Sources, CCF list, NPPA journal query, CAS partition/warning list where applicable

Access policy:

- Prefer legal access: institutional subscription, library delivery, OA PDF, preprint, author homepage, interlibrary loan, or asking authors.
- Do not recommend illegal paywall bypass.
- Record access gaps honestly.

## Search Log

Maintain a search log when the task is more than quick advice:

| Date | Database/source | Query | Filters | Hits | Kept | Notes |
|---|---|---|---|---:|---:|---|

For review/survey papers, define inclusion/exclusion criteria before screening. If the work is systematic or evidence-heavy, use PRISMA-style tracking: identification, screening, eligibility, included.

## Review vs Research Papers

Use review papers to build:

- field history
- taxonomy
- open problems
- datasets and metrics
- method families
- representative papers
- venue patterns

Use research papers to learn publishable contribution structure:

- problem statement
- gap framing
- method contribution
- experimental proof
- limitations
- figures/tables
- target-venue taste

If no review exists:

- search adjacent fields
- use top-paper introductions as mini-reviews
- build a manual taxonomy from research papers
- flag the direction as higher risk

## Reading Order

Default:

1. 2-3 review papers or closest substitutes.
2. accessible papers to learn the basic task and evidence pattern.
3. target-venue papers to learn accepted contribution scale.
4. recent strong papers to learn baselines, metrics, and framing.
5. papers with code/data to anchor execution.

For rapid recognition, do not over-read before finding a feasible baseline and venue. For high-quality targets, read stronger papers deeply and map contribution patterns.

## Fast Triage

For each paper:

1. Read title, abstract, conclusion.
2. Skim introduction for problem/gap.
3. Check method figure and main experiment table.
4. Check dataset, metrics, code/data availability.
5. Decide role: must-read, baseline, module, comparison, target-style, background, or discard.

Deep-read only when it supports idea selection, method synthesis, evidence design, venue choice, or contribution framing.

## Reading Matrix

Use this CSV schema:

```csv
id,title,year,venue,level,topic,problem,gap,method,dataset,metrics,baselines,ablation,case_study,code_url,pdf_url,role,notes
```

`role` should be one of:

- review
- baseline
- module
- comparison
- target-venue-style
- top-framing
- background
- rejected-but-relevant

## Literature Map

Output:

- Chinese/English keyword dictionary
- field taxonomy
- dataset/metric table
- baseline candidates
- module candidate bank
- target venue patterns
- must-read list
- gaps and controversies
- source limitations and search date

Do not claim completeness unless the search protocol supports it.
