# Wiki Schema Guide

Use this reference when creating or updating `SCHEMA.md` and curated wiki pages.

## Required Root Layout

```text
LLM-know-how-wiki/
  raw/
  wiki/
    service/
    architecture/
    api/
    project/
    runbook/
    decision/
    digest/
    index.md
    log.md
    overview.md
  SCHEMA.md
  README.md
```

The exact subdirectories can be adjusted by domain, but keep `raw/`, `wiki/`, `SCHEMA.md`, `wiki/index.md`, and `wiki/log.md`.

## Frontmatter

Every curated wiki page should start with:

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

For service pages, add:

```yaml
repo_path: <relative or absolute path>
repo_remote: <origin URL or unknown>
current_branch: <branch or unknown>
cloud_run: []
```

Use `confidence: high` only for well-supported, source-backed claims. Use `medium` for single-source but plausible synthesis. Use `low` when the page is a starting map or contains unresolved uncertainty.

## Page Type Defaults

### Service

Use for a local repository or deployable component.

Sections:

- Purpose
- Runtime
- Main entrypoints
- Dependencies
- Provides
- Consumes
- Deployment
- Known risks and follow-ups
- Related
- Sources

### Architecture

Use for cross-service systems, runtime models, protocol boundaries, or data flows.

Sections:

- Summary
- Participants
- Flow
- Contracts
- Risks
- Related
- Sources

### API

Use for endpoint catalogs, event schemas, message formats, or integration contracts.

Sections:

- Scope
- Global conventions
- Endpoints or messages
- Request/response notes
- Compatibility risks
- Related
- Sources

### Project

Use for Linear/Feishu/project status and delivery context.

Sections:

- Snapshot
- Workstreams
- Current read
- Risks
- Related
- Sources

### Runbook

Use for repeated operational actions.

Sections:

- When to use
- Commands or checks
- Expected result
- Failure modes
- Escalation
- Related
- Sources

### Decision

Use ADR style when a choice is made or a trade-off matters.

Sections:

- Context
- Decision
- Alternatives
- Consequences
- Revisit trigger
- Sources

### Digest

Use for weekly, ingest, lint, or thematic summaries.

Sections:

- Summary
- Key updates
- Risks or gaps
- Links
- Sources

## Index Rules

`wiki/index.md` should list every curated wiki page except `wiki/log.md`. Each row should include path, one-line summary, and tags.

When a page is created, renamed, archived, or substantially changed, update the index in the same operation.

## Log Rules

`wiki/log.md` is append-only.

Recommended entry:

```markdown
- YYYY-MM-DD INGEST
  - sources:
    - raw/path.md
  - updated:
    - wiki/path.md
  - notes: One concise sentence.
```

Use operation labels: `INIT`, `RAW_IMPORT`, `INGEST`, `ANSWER_FILED`, `LINT`, `SAFETY_REDACTION`, `ARCHIVE`.

## Link Rules

Prefer `[[relative/path.md]]` links inside `wiki/`.

Every new page should link to at least one related page. For strongly connected concepts, add backlinks from existing pages when practical.

## Tag Rules

Tags must be controlled by `SCHEMA.md`. Add a tag to the schema before using it widely.

Useful engineering tags:

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

