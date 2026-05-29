# Wiki Schema Guide

Use this reference when creating or updating `SCHEMA.md` and curated wiki pages.

## Required Root Layout

```text
LLM-know-how-wiki/
  raw/
    external_reference_repos/
    gcloud_inventory/
    workflow_activity/
  external_reference_repos/
    README.md
    manifest.json
    open_source/
  wiki/
    service/
    architecture/
    api/
    project/
    reference/
    runbook/
    decision/
    digest/
    interview/
    log_archive/
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
type: service | architecture | api | project | reference | runbook | decision | digest | interview | index | log
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
deploy_triggers: []
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

### Reference

Use for external open-source repositories and architecture comparisons.

Sections:

- Purpose
- Source repositories
- Architecture patterns
- Useful ideas
- Differences from this project
- Risks or non-transferable parts
- Related
- Sources

### Runbook

Use for repeated project-local operational actions. Runbooks are where repository-specific or company-specific operating context belongs: cloud resource maps, local dev setup, deployment checks, troubleshooting, incident response, and escalation paths.

Sections:

- When to use
- Scope and prerequisites
- Commands or checks
- Expected result
- Failure modes
- Escalation
- Related
- Sources

Project-specific infrastructure context should be a runbook, not a reusable skill reference. Keep generic command safety in skills and put resource names, regions, namespaces, service maps, and local conventions in `wiki/runbook/`.

Deployment branch-to-environment mappings should live in `wiki/runbook/deployment_mapping.md`, `wiki/runbook/deployment_overview.md`, or the relevant `wiki/service/<service>.md`. Use `references/deployment-metadata.md` for the recommended fields.

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

### Interview

Use for repo-backed interview preparation artifacts: project stories, technical highlights, question banks, resume bullets, and evidence maps.

Sections depend on the concrete artifact, but every interview page should preserve:

- target repo or service
- target role or company profile when known
- source paths and wiki pages
- confidence or confirmation-needed notes
- boundaries for claims that should not be overstated

## Index Rules

`wiki/index.md` should list every curated wiki page except `wiki/log.md`. Each row should include path, one-line summary, and tags.

When a page is created, renamed, archived, or substantially changed, update the index in the same operation.

## Log Rules

`wiki/log.md` is the recent hot log. Normal operations append to it. When it grows too large, use Log Archive mode to move older entries to `wiki/log_archive/YYYY.md` while preserving the audit trail.

Recommended entry:

```markdown
- YYYY-MM-DD INGEST
  - sources:
    - raw/path.md
  - updated:
    - wiki/path.md
  - notes: One concise sentence.
```

Use operation labels: `INIT`, `RAW_IMPORT`, `INGEST`, `ANSWER_FILED`, `LINT`, `SAFETY_REDACTION`, `REFERENCE_REPO`, `REFERENCE_REPO_REFRESH`, `REFERENCE_REPO_SNAPSHOT`, `LINEAR_WORKFLOW`, `GITHUB_PR_WORKFLOW`, `WORKFLOW_ACTIVITY`, `ARCHIVE`.

### Log Archive

Archive old log entries when lint reports `WARN large_page log.md` or when loading the log consumes too much context.

```bash
python <skill>/scripts/archive_log.py <wiki-root> --dry-run
python <skill>/scripts/archive_log.py <wiki-root>
```

Archive behavior:

- Keep a recent window in `wiki/log.md` for fast orientation.
- Move older dated entries into `wiki/log_archive/YYYY.md`.
- Add an archive pointer section in `wiki/log.md`.
- Append a `LOG_ARCHIVE` entry.
- Do not list archive files in `wiki/index.md`; they are audit storage, not curated content.

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
- reference
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
- opensource
- external
- github
- workflow
- log
- archive
- interview
- career
- gcloud
- cloud-run
- gke
- cloud-sql
- cloud-storage
- vpc
- unknown
