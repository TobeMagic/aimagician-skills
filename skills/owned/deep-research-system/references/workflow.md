# Research Workflow

Use this workflow whenever you build or extend a docs-first literature research system.

## 1. Define the decision

Write down:

- what decision this research must support
- what bottleneck or uncertainty triggered the research
- whether the goal is innovation scouting, paper comparison, venue targeting, or system design

If the research does not lead to a concrete decision, the scope is too vague.

## 2. Build a profile or query registry

Start from:

- `assets/template_profile.json`
- `assets/starter_query_registry.json`

Cover at least these layers:

- core method
- adjacent alternatives
- failure-mode-specific modules
- benchmarks and evaluation protocol
- venue or application narrative

## 3. Run automated retrieval first

Prefer the bundled pipeline:

```bash
bash scripts/run_all_sources.sh <registry> <output-root>
```

The first pass should prioritize wide recall, not perfect precision.

## 4. Build a deduplicated matrix

Use `build_literature_matrix.py` to merge sources into one matrix.
The matrix is the shared evidence layer. Do not synthesize from isolated raw files.

## 5. Triage, then synthesize

Split papers into:

- must-read
- maybe
- background

Then write:

- innovation map
- curated reading list
- code or system mapping
- coverage gap register

## 6. Record coverage gaps honestly

If a source is blocked, manual-only, or requires credentials:

- do not hide it
- do not imply it was covered automatically
- record it in the coverage gap register

## 7. Reuse, do not restart

For a new research direction:

1. create a new profile
2. write outputs to a new `runs/<name>/` or separate output root
3. keep the same pipeline and artifact structure

The system should become a reusable research backbone, not a one-off study.
