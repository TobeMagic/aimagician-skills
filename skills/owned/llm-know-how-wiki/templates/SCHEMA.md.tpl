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
- `raw/secret_inventory/` stores sanitized secret inventory snapshots with fingerprints and source locations, never raw secret values.
- `secrets/vault.local.env` is the controlled local vault for real secret values and must stay ignored by git.
- `secrets/registry.yaml` stores secret metadata only: env keys, ids, fingerprints, source refs, status, and rotation notes.
- `wiki/` is curated knowledge. Create and update wiki pages during Ingest and Lint.
- `wiki/reference/` stores curated comparisons and architecture notes derived from external reference repositories.
- `wiki/interview/` stores evidence-backed repo interview playbooks, project stories, question banks, and resume bullets.
- `wiki/index.md` is the catalog and must be updated when pages are added, renamed, archived, or substantially changed.
- `wiki/log.md` is the recent action history and must receive one new entry for each Init, Ingest, Lint, and safety redaction operation.
- `wiki/log_archive/` stores older log entries by year when `wiki/log.md` grows too large for useful context loading.

## Hard Rules

1. Store real secrets, tokens, passwords, private keys, cookies, and full credential-like environment values only in `secrets/vault.local.env` or another ignored `secrets/*.local.env` vault file.
2. Do not store raw secret values in `wiki/`, `raw/`, `secrets/registry.yaml`, logs, reports, chat responses, or issue trackers.
3. Prefer "Unknown from current docs" over guessing.
4. Every curated wiki page must have YAML frontmatter.
5. Every Ingest must update `wiki/index.md` and append `wiki/log.md`.
6. Answer mode is read-only unless the human explicitly asks to file the answer.
7. New tags must be added to this schema before broad use.
8. Do not treat repositories under `external_reference_repos/` as local services or deployment targets.

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

Check missing frontmatter, broken wikilinks, missing index entries, orphan pages, stale pages, oversized pages, unknown tags, and secret-looking content outside the controlled local vault.

Write lint reports to `wiki/digest/lint-YYYY-MM-DD.md` and append `wiki/log.md`.

### Secret Inventory

Use Secret Inventory to scan project repositories for keys, tokens, credential URLs, `.env` values, and high-risk cache/config files.

1. Discover repositories under the workspace.
2. Scan source/config files while skipping dependency and build output directories.
3. Copy unique real values to `secrets/vault.local.env`.
4. Append metadata only to `secrets/registry.yaml`.
5. Write sanitized reports to `raw/secret_inventory/`.
6. Append `wiki/log.md`.
7. Do not modify source files unless the human asks for a separate redaction pass.
8. Do not print raw secret values.

### Log Archive

Use Log Archive when `wiki/log.md` is too large, usually after lint reports `WARN large_page log.md`.

1. Run `archive_log.py <wiki-root> --dry-run`.
2. If the archive plan is reasonable, run `archive_log.py <wiki-root>`.
3. Keep recent entries in `wiki/log.md`.
4. Move older dated entries to `wiki/log_archive/YYYY.md`.
5. Preserve the audit trail; do not delete log history.
6. Add or refresh the archive pointer section in `wiki/log.md`.
7. Do not add archive files to `wiki/index.md`.

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
type: service | architecture | api | project | reference | runbook | decision | digest | interview | index | log
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
- log
- archive
- secret
- env
- credential
- interview
- career
- gcloud
- cloud-run
- gke
- cloud-sql
- cloud-storage
- vpc
- unknown
