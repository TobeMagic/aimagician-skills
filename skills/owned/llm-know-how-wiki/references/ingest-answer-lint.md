# Ingest, Answer, and Lint Workflows

## Ingest Workflow

Use Ingest to compile new evidence into durable wiki pages.

1. Resolve wiki root.
2. Orient by reading `SCHEMA.md`, `wiki/index.md`, and recent `wiki/log.md`.
3. List source files to read.
4. Read sources and summarize evidence.
5. Search existing wiki pages for overlapping concepts.
6. Plan page edits:
   - create new pages for central or recurring concepts
   - update existing pages for known concepts
   - update index
   - append log
7. Edit only curated `wiki/` pages unless importing new raw evidence or redacting unsafe raw content.
8. Run lint and sensitive scan.
9. Report changed files, verification results, and unresolved gaps.

## Ingest Heuristics

Create a page when:

- a concept/entity is central to one source
- a concept/entity appears in two or more sources
- a workflow, API contract, or decision will be reused
- the user asks for a durable page

Do not create a page for:

- passing mentions
- transient chat phrasing
- one-off todos with no durable value
- claims outside the wiki scope

When new evidence conflicts with old wiki content:

1. Compare source dates and context.
2. Preserve both claims if conflict is real.
3. Mark the affected page `confidence: medium` or `low`.
4. Add a Risks or Open questions section.
5. Surface the conflict in the ingest summary or lint report.

## Answer Workflow

Use Answer for read-only questions against the wiki.

1. Read `wiki/index.md`.
2. Select relevant pages.
3. Read selected pages.
4. Answer with citations to wiki page paths.
5. State gaps clearly.
6. Do not write files unless the user asks to file the answer.

If the user asks something that requires current external truth, browse or query the appropriate source only when allowed and necessary. Then suggest an Ingest so the new evidence becomes durable.

## Filing Valuable Answers

Only file an answer back into the wiki when it is durable:

- comparison
- architecture synthesis
- decision rationale
- investigation summary
- reusable runbook
- project status digest

File under `wiki/digest/`, `wiki/decision/`, `wiki/architecture/`, or another appropriate type. Update index and log.

## Lint Workflow

Run:

```bash
python <skill>/scripts/wiki_lint.py <wiki-root> --write-report
python <skill>/scripts/scan_sensitive.py <wiki-root>
```

Review findings in this severity order:

1. unsafe secret-looking content
2. broken links
3. missing frontmatter
4. missing index entries
5. unknown tags
6. orphan pages
7. stale pages
8. pages too large

Lint should normally create a report, not rewrite large parts of the wiki. Use later Ingest operations to fix substantial content issues.

