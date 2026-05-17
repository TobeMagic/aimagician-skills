# Source Adapters

Use this reference to choose how to treat different raw evidence.

## Repository Snapshot

Good raw inputs:

- git fetch snapshots from `scripts/refresh_repos.py`
- `rg --files`
- `README.md`
- package manifests
- service docs
- deployment manifests
- API/router directories
- git remote/branch/status summaries

Create or update:

- `wiki/service/<service>.md`
- `wiki/architecture/system_overview.md`
- `wiki/runbook/local_development.md`
- `wiki/runbook/deployment_overview.md`
- `wiki/runbook/troubleshooting.md`

Do not infer production deployment state from local files unless explicitly documented.

## Repository Freshness

Before relying on local repository code in a multi-repo workspace, run:

```bash
python <skill>/scripts/refresh_repos.py --workspace <workspace-root>
```

This updates remote-tracking refs with `git fetch --all --prune --tags` and writes an append-only raw snapshot when a wiki root exists.

Safety boundaries:

- Fetch only. Do not pull, merge, rebase, checkout, reset, or stash.
- Use `--dry-run --no-write-raw` when the user only wants a preview.
- If a repo has no remote, record `skipped_no_remote`.
- If a repo has uncommitted files, keep them untouched and record the dirty count.
- If fetch fails because credentials are missing, record the failure. Do not ask Git to prompt interactively.

Useful follow-up pages:

- `wiki/service/<service>.md` for branch/remote context changes
- `wiki/digest/<date>-repo_refresh.md` for broad refresh summaries
- `wiki/project/<project>_status.md` when repo freshness affects delivery status

## External Open-Source Reference Repositories

Good raw inputs:

- repositories cloned by `scripts/external_reference_repos.py`
- `external_reference_repos/manifest.json`
- snapshots under `raw/external_reference_repos/`
- README, architecture docs, package manifests, source tree inventory, examples

Storage rules:

- clone third-party projects under `external_reference_repos/open_source/<host>__<owner>__<repo>/`
- do not place external projects beside company service repositories
- do not create `wiki/service/` pages for external projects
- record URL, local path, ref, head, and license metadata in `external_reference_repos/manifest.json`
- use `raw/external_reference_repos/` for shallow snapshots

Create or update:

- `wiki/reference/<topic>.md` for architecture comparison and transferable patterns
- `wiki/architecture/<topic>.md` only when the comparison directly informs this project's architecture
- `wiki/digest/<date>-reference_repos.md` for broad survey summaries

Safety boundaries:

- avoid authenticated clone URLs and redact credentials from URLs
- treat external repos as reference material, not trusted runtime code
- cite license files when borrowing implementation ideas
- separate "useful idea" from "safe to adopt here"; not every OSS pattern transfers

## Feishu Wiki / Docs / Base Exports

Good raw inputs:

- exported Markdown docs
- Base table `records.md`
- metadata manifests

Create or update:

- architecture pages for system docs
- API pages for interface docs
- project pages for project-management tables
- runbooks for operations docs
- digest pages for broad compile passes

Safety:

- redact signed download URLs, authcode URLs, cookies, tokens, passwords, account credentials, and private links where needed
- do not preserve Feishu temporary auth codes in curated wiki pages

## Linear Snapshots

Use Linear as current issue-tracking evidence when the snapshot is recent.

Create or update:

- `wiki/project/<team_or_product>_status.md`
- current risk digest
- release/project status pages

Keep issue IDs, titles, status, priority, assignee, milestone, updated date, and URL. Avoid importing private descriptions or signed attachments unless the user explicitly asks and safety rules allow it.

## Workflow Activity

Use `scripts/record_activity.py` when another skill needs to leave an operational audit trail without creating a curated wiki page.

Good inputs:

- Linear issue identifier or URL
- GitHub PR URL
- repo and branch
- one-line summary
- short Markdown details

Create:

- `raw/workflow_activity/<timestamp>-<slug>.md`
- appended `wiki/log.md` entry

Use operation labels such as:

- `LINEAR_WORKFLOW`
- `GITHUB_PR_WORKFLOW`
- `WORKFLOW_ACTIVITY`

Do not use workflow activity records as a substitute for curated pages when the knowledge is durable. If the activity reveals a reusable pattern or decision, follow with an Ingest into `wiki/runbook/`, `wiki/project/`, or `wiki/decision/`.

## API Docs

Create:

- `wiki/api/api_contract_catalog.md`
- endpoint-specific pages when one API is large or high-risk
- message-schema pages for SSE/WebSocket/event contracts

Capture:

- base paths
- methods
- request/response shape
- event types
- compatibility risks
- ownership and source docs

Avoid copying long examples unless the example itself is the contract.

## Deployment Metadata

If deployment metadata comes from docs, repo CI/CD files, or cloud inventory, store only stable operational metadata:

- service name
- URL
- platform if already stated
- environment label
- owning repo if already stated
- branch-to-environment mapping
- deploy trigger name or ID
- non-secret provenance fields such as commit SHA, build ID, image digest, or revision name

Do not live-inspect Cloud Run, Kubernetes, secrets, IAM, or env vars unless the user explicitly asks.

Never store secret env var values.

Expected deployment behavior should be resolved in this order:

1. Existing wiki deployment metadata/runbooks.
2. Repository CI/CD config.
3. Live cloud config from explicit inventory or inspection.
4. Fallback defaults such as `dev` -> staging and `main`/`master` -> prod.

If the sources disagree, create or update a conflict note in `wiki/runbook/deployment_mapping.md` with `confidence: low`.

## Gcloud Inventory

Use `gcloud-ops-workflow/scripts/gcloud_inventory.sh` for read-only cloud snapshots.

Good raw inputs:

- `raw/gcloud_inventory/<timestamp>-inventory.md`
- Cloud Run service list/describe output with URLs and revision names
- GKE deployment/pod/events summaries
- Cloud Storage bucket metadata
- VPC subnet/firewall/route summaries
- Cloud SQL instance metadata
- scoped Cloud Logging error summaries

Create or update:

- `wiki/api/service_endpoint_inventory.md` for stable Cloud Run service names and URLs
- `wiki/runbook/deployment_overview.md` for deployment topology
- `wiki/runbook/<service>_operations.md` for repeated operational checks
- `wiki/digest/<date>-gcloud_inventory.md` for broad inventory passes

Safety:

- never store secret values, service account keys, signed URLs, database passwords, cookies, or full env values
- store env var names only
- prefer resource names, URLs, region/zone, status, and recent error signatures
- mutating cloud actions belong in workflow activity records with explicit human approval noted

## Images, PDFs, and Binary Assets

Store raw files under `raw/assets/` or a source-specific folder.

For curated wiki pages:

- summarize the durable meaning
- link to the raw asset path
- do not rely on temporary external URLs

If image content is needed for evidence, inspect the image and cite the raw path.
