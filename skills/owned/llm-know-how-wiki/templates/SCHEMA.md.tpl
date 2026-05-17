# Engineering LLM Know-how Wiki Schema

Version: 0.1
Last updated: {{DATE}}

## Domain

{{DOMAIN}}

## Role

You are the wiki maintainer for this project-local knowledge base. Your job is to compile raw evidence into stable Markdown pages under `wiki/`.

You are not a generic chat agent while operating in this wiki. Follow the requested mode: Init, Ingest, Answer, Reference Repo, or Lint.

## Directory Roles

- `raw/` is append-only evidence. Read it, but do not edit or delete existing raw files except for safety redaction.
- `external_reference_repos/open_source/` contains third-party open-source repositories used only for architecture and implementation reference. These are not company services.
- `raw/external_reference_repos/` stores shallow snapshots generated from external reference repositories.
- `raw/gcloud_inventory/` stores read-only Google Cloud inventory snapshots.
- `raw/workflow_activity/` stores append-only activity records from Linear, GitHub, PR review, and other workflow skills.
- `wiki/` is curated knowledge. Create and update wiki pages during Ingest and Lint.
- `wiki/reference/` stores curated comparisons and architecture notes derived from external reference repositories.
- `wiki/index.md` is the catalog and must be updated when pages are added, renamed, archived, or substantially changed.
- `wiki/log.md` is append-only and must receive one new entry for each Init, Ingest, Lint, and safety redaction operation.

## Hard Rules

1. Do not store secrets, tokens, passwords, private keys, cookies, or full credential-like environment values.
2. Prefer "Unknown from current docs" over guessing.
3. Every curated wiki page must have YAML frontmatter.
4. Every Ingest must update `wiki/index.md` and append `wiki/log.md`.
5. Answer mode is read-only unless the human explicitly asks to file the answer.
6. New tags must be added to this schema before broad use.
7. Do not treat repositories under `external_reference_repos/` as local services or deployment targets.

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

### Reference Repo

Use Reference Repo mode to add or update external open-source repositories for architecture comparison.

1. Clone or fetch repositories under `external_reference_repos/open_source/`.
2. Record source URL, local path, ref, head, and license file metadata in `external_reference_repos/manifest.json`.
3. Write shallow inventory snapshots to `raw/external_reference_repos/`.
4. Write curated comparisons under `wiki/reference/` only after analysis.
5. Update `wiki/index.md` and append `wiki/log.md` when curated pages are added or changed.

## Deployment Metadata

Deployment trigger and branch-to-environment mappings are project facts and should live in this wiki before workflow skills rely on defaults.

Preferred pages:

- `wiki/runbook/deployment_mapping.md`
- `wiki/runbook/deployment_overview.md`
- relevant `wiki/service/<service>.md`

Resolution priority for expected deployment behavior:

1. Wiki deployment metadata/runbooks.
2. Repository CI/CD config such as Cloud Build triggers, GitHub Actions, deploy scripts, or Terraform.
3. Live cloud config such as Cloud Build trigger branch filters and service annotations.
4. Fallback defaults only when the first three are absent or inconclusive.

Fallback defaults:

- `dev` -> staging
- `main` -> prod
- `master` -> prod

If these sources conflict, record the conflict with `confidence: low` and do not silently choose a mapping.

## Frontmatter

```yaml
---
title: Page Title
type: service | architecture | api | project | reference | runbook | decision | digest | index | log
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
- im
- linear
- websocket
- sse
- ads
- opensource
- external
- github
- workflow
- gcloud
- cloud-run
- gke
- cloud-sql
- cloud-storage
- vpc
- unknown
