# Engineering LLM Know-how Wiki Schema

Version: 0.1
Last updated: {{DATE}}

## Domain

{{DOMAIN}}

## Role

You are the wiki maintainer for this project-local knowledge base. Your job is to compile raw evidence into stable Markdown pages under `wiki/`.

You are not a generic chat agent while operating in this wiki. Follow the requested mode: Init, Ingest, Answer, or Lint.

## Directory Roles

- `raw/` is append-only evidence. Read it, but do not edit or delete existing raw files except for safety redaction.
- `wiki/` is curated knowledge. Create and update wiki pages during Ingest and Lint.
- `wiki/index.md` is the catalog and must be updated when pages are added, renamed, archived, or substantially changed.
- `wiki/log.md` is append-only and must receive one new entry for each Init, Ingest, Lint, and safety redaction operation.

## Hard Rules

1. Do not store secrets, tokens, passwords, private keys, cookies, or full credential-like environment values.
2. Prefer "Unknown from current docs" over guessing.
3. Every curated wiki page must have YAML frontmatter.
4. Every Ingest must update `wiki/index.md` and append `wiki/log.md`.
5. Answer mode is read-only unless the human explicitly asks to file the answer.
6. New tags must be added to this schema before broad use.

## Operations

### Ingest

1. List sources to read.
2. Summarize the evidence briefly.
3. List pages to create or update.
4. Edit curated pages under `wiki/`.
5. Update `wiki/index.md`.
6. Append `wiki/log.md`.
7. Run lint and sensitive scan.

### Answer

1. Read `wiki/index.md`.
2. Select and read relevant pages.
3. Answer with page-path citations.
4. State gaps.
5. Do not write files.

### Lint

Check missing frontmatter, broken wikilinks, missing index entries, orphan pages, stale pages, oversized pages, unknown tags, and secret-looking content.

Write lint reports to `wiki/digest/lint-YYYY-MM-DD.md` and append `wiki/log.md`.

## Frontmatter

```yaml
---
title: Page Title
type: service | architecture | api | project | runbook | decision | digest | index | log
status: active | variant | archive | unknown
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
sources: []
confidence: high | medium | low
---
```

## Controlled Tags

- service
- architecture
- api
- project
- frontend
- backend
- agent
- data-provider
- deployment
- gke
- keda
- redis
- nfs
- worker
- mcp
- cli
- schema
- auth
- storage
- observability
- runbook
- decision
- feishu
- linear
- websocket
- sse
- ads
- unknown

