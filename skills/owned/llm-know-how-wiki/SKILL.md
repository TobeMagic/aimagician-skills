---
name: llm-know-how-wiki
description: >
  Build, maintain, query, and lint a project-local LLM-know-how-wiki: a
  persistent, compiled Markdown knowledge base with raw evidence, curated wiki
  pages, schema rules, index, and log. Use this skill whenever the user asks to
  create an LLM wiki, ingest raw docs/repos/Feishu/Linear snapshots, answer from
  an existing wiki, lint/audit wiki health, inventory project secrets into a
  controlled local vault, or turn scattered engineering context into a durable
  knowledge base. This skill should trigger even if the user only says "wiki",
  "know-how", "ingest", "digest", "secret inventory", "env 管理",
  "密钥整理", "基于 wiki 回答", "把这些文档编译进知识库", or
  "维护 LLM-know-how-wiki".
metadata:
  related_skills:
    - opensource-architecture-research
    - repo-interview-playbook
compatibility:
  tools:
    - bash
    - python
    - rg
  requires: Write access to the current project when initializing or ingesting;
    read access is enough for Answer mode
category: build
subcategory: knowledge
tags:
  - wiki
  - knowledge
  - context
---

# LLM Know-how Wiki

Use this skill to create and operate a project-local compiled knowledge base inspired by Karpathy's LLM Wiki pattern and the Hermes Agent `llm-wiki` skill. The key idea is not query-time RAG. The agent incrementally compiles raw sources into stable, interlinked Markdown pages so project knowledge compounds over time.

## Core Model

Every wiki has three core layers plus optional external-reference and local secret-management areas:

- `raw/`: append-only evidence such as repository snapshots, Feishu exports, Linear snapshots, meeting notes, APIs, PDFs, CSVs, screenshots, and imported docs.
- `wiki/`: curated, agent-maintained Markdown pages with frontmatter, links, summaries, architecture notes, API contracts, project status, runbooks, decisions, and digests.
- `SCHEMA.md`: the behavior contract that tells agents how to maintain this specific wiki: page types, tags, naming, update rules, safety rules, and operation modes.
- `external_reference_repos/open_source/`: third-party open-source repositories used only for architecture and implementation reference. Do not treat these as company services or deployment targets.
- `secrets/`: controlled local secret management. `secrets/vault.local.env` may contain real values and must stay gitignored; `secrets/registry.yaml` stores metadata only.

The navigation backbone is:

- `wiki/index.md`: content catalog. Read this first for Answer mode.
- `wiki/log.md`: recent action history. Read recent entries before changing anything.
- `wiki/log_archive/`: older log entries archived by year when `wiki/log.md` grows too large.
- `wiki/interview/`: evidence-backed interview playbooks generated from local repos and wiki pages.
- `raw/secret_inventory/`: sanitized secret scan snapshots with fingerprints and source locations, never raw values.

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

### Refresh Repos

Use Refresh Repos before repository-based Ingest when the user wants current code context across a multi-repo workspace.

Run the bundled script:

```bash
python <skill>/scripts/refresh_repos.py --workspace <workspace-root>
```

Default behavior:

- discovers git repositories under the workspace
- runs `git fetch --all --prune --tags` in each repo with `GIT_TERMINAL_PROMPT=0`
- does not run `git pull`
- does not checkout, merge, rebase, or alter the working tree
- writes a raw snapshot to `raw/repo_snapshots/<timestamp>-git-fetch.md` when a wiki root is available
- appends `wiki/log.md`

For preview:

```bash
python <skill>/scripts/refresh_repos.py --workspace <workspace-root> --dry-run --no-write-raw
```

After Refresh Repos, use Ingest to compile the snapshot into service or project pages if the status changes matter.

### Secret Inventory

Use Secret Inventory when the user wants to scan all related repositories for keys, tokens, credential URLs, `.env` values, or cache/config secrets and organize them into one managed location.

Run the bundled script:

```bash
python <skill>/scripts/secret_inventory.py --workspace <workspace-root> --wiki-root <wiki-root>
```

Default behavior:

- discovers git repositories under the workspace, using the same safe discovery style as Refresh Repos
- scans text/config files, `.env*`, `.npmrc`, `.pypirc`, `.netrc`, Terraform variable/state files, credential-looking filenames, and targeted high-risk cache/config files
- copies unique detected values into `secrets/vault.local.env`
- appends metadata only to `secrets/registry.yaml`
- writes a sanitized raw report to `raw/secret_inventory/<timestamp>-secret-scan.md`
- appends `wiki/log.md`
- does not modify the source files where the secret was found
- does not print or write raw secret values outside `secrets/vault.local.env`

Useful variants:

```bash
python <skill>/scripts/secret_inventory.py --workspace <workspace-root> --dry-run --json
python <skill>/scripts/secret_inventory.py --workspace <workspace-root> --no-write-vault
python <skill>/scripts/secret_inventory.py --workspace <workspace-root> --strict
```

After Secret Inventory, create or update `wiki/runbook/secret_management.md` only with safe metadata: secret ids, env keys, owning service, purpose, source locations, loading instructions, and rotation notes. Do not copy raw values from `secrets/vault.local.env` into `wiki/`, `raw/`, reports, chat, or issue trackers.

### Reference Repos

Use Reference Repos when the user wants to pull, update, or compare external open-source projects.

Run the bundled script:

```bash
python <skill>/scripts/external_reference_repos.py --wiki-root <wiki-root> add https://github.com/owner/repo.git
python <skill>/scripts/external_reference_repos.py --wiki-root <wiki-root> snapshot github__owner__repo
```

Default behavior:

- clones external repositories into `external_reference_repos/open_source/<host>__<owner>__<repo>/`
- stores source URL, path, ref, head, and license file metadata in `external_reference_repos/manifest.json`
- writes shallow raw inventories to `raw/external_reference_repos/`
- appends `wiki/log.md`
- does not create service pages for external repositories

Curated architecture comparisons belong under `wiki/reference/`, usually after one or more snapshots have been captured.

For deep open-source architecture comparison with confirmed research objects, module taxonomy, heatmaps, and phased delivery, use the related `opensource-architecture-research` skill. Keep cloned source repositories under `external_reference_repos/open_source/` and put curated reports under `wiki/reference/<feature_slug>/`.

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

Raw files are normally append-only. If a safety scan finds passwords, tokens, cookies, private keys, signed download URLs, or credential-like account data outside the controlled local vault, either run Secret Inventory or redact the value and record the action in metadata/log.

### Workflow Activity Record

Use this when another skill or workflow needs to leave an audit trail without creating a curated wiki page.

```bash
python <skill>/scripts/record_activity.py --wiki-root <wiki-root> \
  --operation LINEAR_WORKFLOW \
  --issue LUC-123 \
  --repo owner/repo \
  --branch LUC-123-short-title \
  --summary "Started issue from latest dev branch"
```

The script writes `raw/workflow_activity/<timestamp>-<slug>.md` and appends `wiki/log.md`. Use it after Linear state changes, branch creation, PR creation, reviewer-bot review checks, merge decisions, and final status updates.

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
- real secret values outside `secrets/vault.local.env`

Lint reports go under `wiki/digest/lint-YYYY-MM-DD.md` and `wiki/log.md` should receive an entry.

### Log Archive

Use Log Archive when `wiki/log.md` grows too large, lint reports `WARN large_page log.md`, or recent context is hard to scan.

Run a dry run first:

```bash
python <skill>/scripts/archive_log.py <wiki-root> --dry-run
```

Then archive if the plan is reasonable:

```bash
python <skill>/scripts/archive_log.py <wiki-root>
```

Default behavior:

- keeps the most recent log entries in `wiki/log.md` using a default recent window of roughly 200 lines
- moves older dated entries into `wiki/log_archive/YYYY.md`
- preserves the audit trail instead of deleting history
- adds an archive pointer section to `wiki/log.md`
- appends a `LOG_ARCHIVE` entry describing what moved
- does not add archive pages to `wiki/index.md`

Use `--keep-lines <n>` when the project needs a larger or smaller recent window. Keep enough recent entries to understand the last active workflow, but do not keep months of old operational noise in the hot log.

## Page Types

Default engineering page types:

- `service`: one local service/repo/component
- `architecture`: cross-service flow, runtime model, protocol, system design
- `api`: API contract, endpoint inventory, event/message schema
- `project`: Linear/Feishu/project status, roadmap, delivery context
- `reference`: external open-source reference projects and architecture comparisons
- `runbook`: project-local operating procedures such as local dev, deployment, cloud infrastructure, troubleshooting, incident checks, and repeated commands
- `decision`: ADRs and trade-offs
- `digest`: periodic or thematic synthesis
- `interview`: repo-backed interview playbooks, project stories, question banks, and resume bullets
- `index` and `log`: navigation and audit files

Use [`references/wiki-schema-guide.md`](./references/wiki-schema-guide.md) for page templates and tag rules.

## Project Runbooks

Runbooks belong in `wiki/runbook/`, not in reusable skills. A skill can define a generic workflow, but project-specific resource names, service maps, regions, namespaces, URLs, and escalation paths should live in the project wiki.

Good runbook topics:

- `local_development.md`
- `deployment_overview.md`
- `deployment_mapping.md`
- `environment_variables.md`
- `gcloud_infra_playbook.md`
- `<service>_operations.md`
- `troubleshooting.md`

When another skill asks for project-specific context, read `wiki/index.md` and the relevant runbook pages before acting.

For deployment-trigger and environment mapping metadata, use [`references/deployment-metadata.md`](./references/deployment-metadata.md). This gives Linear, GitHub, and gcloud workflows a shared project-local source of truth before they fall back to repo config or cloud live state.

## Source Adapters

Use [`references/source-adapters.md`](./references/source-adapters.md) when ingesting:

- repository snapshots
- Feishu wiki/docs/base exports
- Linear issue snapshots
- Cloud Run or deployment metadata
- API docs
- external open-source reference repositories
- screenshots or binary assets

Do not live-inspect Cloud Run or external systems unless the user explicitly asks. If deployment metadata is imported from docs, store only service name and URL unless the schema permits more.

## Safety Rules

- Real secrets, tokens, passwords, cookies, private keys, and full credential-like env values may only live in the controlled local vault: `secrets/vault.local.env` or another ignored `secrets/*.local.env` file.
- Never store raw secret values in `wiki/`, `raw/`, `secrets/registry.yaml`, logs, reports, chat responses, or issue trackers.
- `secrets/registry.yaml` stores metadata only: env key, secret id, kind, fingerprint, source refs, status, and rotation notes.
- Secret scan reports must use fingerprints and redacted previews, not raw values.
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

# Fetch latest remote refs for all repos and record raw snapshot
python <skill>/scripts/refresh_repos.py --workspace <workspace-root>

# Preview repository discovery without fetching
python <skill>/scripts/refresh_repos.py --workspace <workspace-root> --dry-run --no-write-raw

# Add an external open-source reference repository
python <skill>/scripts/external_reference_repos.py --wiki-root <wiki-root> add https://github.com/owner/repo.git

# Capture a shallow raw inventory for later comparison
python <skill>/scripts/external_reference_repos.py --wiki-root <wiki-root> snapshot github__owner__repo

# Record workflow activity into raw/ and wiki/log.md
python <skill>/scripts/record_activity.py --wiki-root <wiki-root> --operation WORKFLOW_ACTIVITY --summary "Recorded activity"

# Lint structure and links
python <skill>/scripts/wiki_lint.py <wiki-root>

# Write a lint report into wiki/digest/
python <skill>/scripts/wiki_lint.py <wiki-root> --write-report

# Scan for obvious secrets
python <skill>/scripts/scan_sensitive.py <wiki-root>

# Inventory workspace secrets into the local controlled vault
python <skill>/scripts/secret_inventory.py --workspace <workspace-root> --wiki-root <wiki-root>
```

## References

- [`references/ingest-answer-lint.md`](./references/ingest-answer-lint.md): detailed workflows
- [`references/wiki-schema-guide.md`](./references/wiki-schema-guide.md): schema, frontmatter, page templates
- [`references/source-adapters.md`](./references/source-adapters.md): source-specific ingest rules
- [`references/deployment-metadata.md`](./references/deployment-metadata.md): repo deployment mappings, triggers, environments, and provenance fields
