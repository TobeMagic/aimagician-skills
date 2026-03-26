# Output Package

A complete research package should produce both data artifacts and judgment artifacts.

## Data artifacts

- `raw/*.jsonl`
- `processed/literature_matrix.csv`
- `processed/theme_summary.json`
- `processed/source_summary.json`

## Judgment artifacts

- innovation map
- curated reading list
- code or system mapping
- coverage gap register
- workflow or protocol notes

## Minimum standard

Do not call the work “systematic” unless it has:

1. multi-source retrieval
2. a deduplicated matrix
3. a shortlist or triage layer
4. explicit coverage boundaries
5. a concrete downstream decision or recommendation

## Reusable layout

The target repository should end up with:

```text
docs/deep_research/
  profiles/
  queries/
  raw/
  processed/
  runs/
  README.md
  paper_triage_template.csv
```

Additional interpretation documents should live beside those folders, not hidden elsewhere.
