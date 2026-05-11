---
name: llm-know-how-wiki
description: |
  Build, maintain, query, and lint a project-local LLM-know-how-wiki: a persistent, compiled Markdown knowledge base with raw evidence, curated wiki pages, schema rules, index, and log. Use this skill whenever the user asks to create an LLM wiki, ingest raw docs/repos/Feishu/Linear snapshots, answer from an existing wiki, lint/audit wiki health, or turn scattered engineering context into a durable knowledge base. This skill should trigger even if the user only says "wiki", "know-how", "ingest", "digest", "基于 wiki 回答", "把这些文档编译进知识库", or "维护 LLM-know-how-wiki".
compatibility:
  tools: [bash, python, rg]
  requires: Write access to the current project when initializing or ingesting; read access is enough for Answer mode
---

# LLM Know-how Wiki

Use this skill to create and operate a project-local compiled knowledge base inspired by Karpathy's LLM Wiki pattern and the Hermes Agent `llm-wiki` skill. The key idea is not query-time RAG. The agent incrementally compiles raw sources into stable, interlinked Markdown pages so project knowledge compounds over time.

## Core Model

Every wiki has three layers:

- `raw/`: append-only evidence such as repository snapshots, Feishu exports, Linear snapshots, meeting notes, APIs, PDFs, CSVs, screenshots, and imported docs.
- `wiki/`: curated, agent-maintained Markdown pages with frontmatter, links, summaries, architecture notes, API contracts, project status, runbooks, decisions, and digests.
- `SCHEMA.md`: the behavior contract that tells agents how to maintain this specific wiki: page types, tags, naming, update rules, safety rules, and operation modes.

The navigation backbone is:

- `wiki/index.md`: content catalog. Read this first for Answer mode.
- `wiki/log.md`: append-only action history. Read recent entries before changing anything.

## Resolve The Wiki Root

The target wiki is project-local, not hardcoded to this skill directory.

Resolve the wiki root in this order:

1. Use the explicit path if the user provides one.
2. Use `LLM_WIKI_ROOT` if the environment variable is set and the user has not provided a path.
3. Search upward from the current working directory for the nearest `LLM-know-how-wiki/`.
4. If none exists and the user asks to create/init/build a wiki, create `./LLM-know-how-wiki/` in the current working directory.
5. If none exists and the user asks Answer/Lint against a wiki, explain that no project-local wiki was found and offer to initialize one.

Do not default to `~/wiki`. This skill is designed for per-project engineering knowledge bases.

Use the bundled initializer when possible:

```bash
python <skill>/scripts/init_wiki.py --domain "<short domain>"
```

## Always Orient First

Before any Ingest, Answer, or Lint against an existing wiki:

1. Read `SCHEMA.md`.
2. Read `wiki/index.md`.
3. Read the last 20-30 lines of `wiki/log.md`.
4. If the wiki has many pages, use `rg` across `wiki/` for the topic before creating new pages.

This prevents duplicates, broken conventions, and stale assumptions.

## Operating Modes

### Init

Use Init when the project has no wiki or the user asks to create one.

1. Resolve the target root.
2. Run `scripts/init_wiki.py`.
3. Create or confirm:
   - `raw/`
   - `wiki/`
   - `SCHEMA.md`
   - `README.md`
   - `wiki/index.md`
   - `wiki/log.md`
   - `wiki/overview.md`
4. Tell the user the wiki root and first suggested ingest targets.

### Ingest

Use Ingest when the user provides raw files, folders, repo context, Feishu exports, Linear snapshots, or asks to compile evidence into the wiki.

1. List the exact source paths you will read.
2. Read the sources and summarize the evidence briefly.
3. Decide which wiki pages to create or update. Prefer updating existing pages over duplicating concepts.
4. Before broad edits, state the intended file plan.
5. Write curated knowledge only under `wiki/`.
6. Update `wiki/index.md` for new or substantially changed pages.
7. Append `wiki/log.md` with sources, updated pages, and notes.
8. Run:
   ```bash
   python <skill>/scripts/wiki_lint.py <wiki-root>
   python <skill>/scripts/scan_sensitive.py <wiki-root>
   ```
9. Report changed files and verification results.

Raw files are normally append-only. If a safety scan finds passwords, tokens, cookies, private keys, signed download URLs, or credential-like account data, redact them and record the redaction in metadata/log.

### Answer

Use Answer when the user asks questions about a project/domain covered by an existing wiki.

1. Read `wiki/index.md` and pick relevant pages.
2. Read only the needed pages, plus recent `wiki/log.md` if freshness matters.
3. Answer from the compiled `wiki/` layer first.
4. Cite page paths in the response.
5. Do not modify files in Answer mode unless the user explicitly asks to file the answer back into the wiki.
6. If information is missing or stale, say so and suggest an Ingest or Lint follow-up.

### Lint

Use Lint when the user asks to check health, consistency, links, or safety.

Run the bundled lint:

```bash
python <skill>/scripts/wiki_lint.py <wiki-root> --write-report
python <skill>/scripts/scan_sensitive.py <wiki-root>
```

Check for:

- missing frontmatter
- broken wikilinks
- missing index entries
- orphan pages
- stale pages
- page size over threshold
- unknown tags
- unsafe secret-looking content

Lint reports go under `wiki/digest/lint-YYYY-MM-DD.md` and `wiki/log.md` should receive an entry.

## Page Types

Default engineering page types:

- `service`: one local service/repo/component
- `architecture`: cross-service flow, runtime model, protocol, system design
- `api`: API contract, endpoint inventory, event/message schema
- `project`: Linear/Feishu/project status, roadmap, delivery context
- `runbook`: operations, local dev, deployment, troubleshooting
- `decision`: ADRs and trade-offs
- `digest`: periodic or thematic synthesis
- `index` and `log`: navigation and audit files

Use [`references/wiki-schema-guide.md`](./references/wiki-schema-guide.md) for page templates and tag rules.

## Source Adapters

Use [`references/source-adapters.md`](./references/source-adapters.md) when ingesting:

- repository snapshots
- Feishu wiki/docs/base exports
- Linear issue snapshots
- Cloud Run or deployment metadata
- API docs
- screenshots or binary assets

Do not live-inspect Cloud Run or external systems unless the user explicitly asks. If deployment metadata is imported from docs, store only service name and URL unless the schema permits more.

## Safety Rules

- Never store secrets, tokens, passwords, cookies, private keys, or full credential-like env values.
- Never silently overwrite raw evidence.
- Prefer "Unknown from current docs" over guessing.
- Keep every curated page traceable through `sources:` frontmatter and a Sources section.
- Keep pages scannable. Split pages that grow too large.
- Do not create pages for passing mentions. Create pages for central concepts, recurring entities, or durable decisions.

## Useful Commands

```bash
# Initialize or reuse a project-local wiki
python <skill>/scripts/init_wiki.py --domain "engineering context"

# Find wiki root from the current project
python <skill>/scripts/init_wiki.py --print-root --no-create

# Lint structure and links
python <skill>/scripts/wiki_lint.py <wiki-root>

# Write a lint report into wiki/digest/
python <skill>/scripts/wiki_lint.py <wiki-root> --write-report

# Scan for obvious secrets
python <skill>/scripts/scan_sensitive.py <wiki-root>
```

## References

- [`references/ingest-answer-lint.md`](./references/ingest-answer-lint.md): detailed workflows
- [`references/wiki-schema-guide.md`](./references/wiki-schema-guide.md): schema, frontmatter, page templates
- [`references/source-adapters.md`](./references/source-adapters.md): source-specific ingest rules

