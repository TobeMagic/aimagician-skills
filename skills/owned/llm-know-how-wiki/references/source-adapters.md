# Source Adapters

Use this reference to choose how to treat different raw evidence.

## Repository Snapshot

Good raw inputs:

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

If deployment metadata comes from docs, store only stable operational metadata:

- service name
- URL
- platform if already stated
- environment label
- owning repo if already stated

Do not live-inspect Cloud Run, Kubernetes, secrets, IAM, or env vars unless the user explicitly asks.

Never store secret env var values.

## Images, PDFs, and Binary Assets

Store raw files under `raw/assets/` or a source-specific folder.

For curated wiki pages:

- summarize the durable meaning
- link to the raw asset path
- do not rely on temporary external URLs

If image content is needed for evidence, inspect the image and cite the raw path.

