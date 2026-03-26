# Deep Research

This directory holds a reusable docs-first literature research system.

Recommended starting steps:

1. Edit `profiles/template_profile.json` or `queries/query_registry.json`
2. Run the retrieval pipeline
3. Review `processed/literature_matrix.csv`
4. Write an innovation map, curated reading list, and coverage gap register

Typical command:

```bash
bash scripts/run_all_sources.sh queries/query_registry.json .
```
