# Deployment Metadata

Use this reference when compiling deployment triggers, branch-to-environment mappings, Cloud Build/GitHub Actions metadata, Cloud Run/GKE targets, and verification fields into the project wiki.

## Purpose

The project wiki is the first source that workflow skills should consult for expected deployment behavior. Live cloud state can prove what happened, but the wiki should describe what is expected to happen.

## Recommended Location

Prefer one of:

- `wiki/runbook/deployment_mapping.md` for cross-repo deployment mapping;
- `wiki/runbook/deployment_overview.md` for broader release/deploy process;
- `wiki/service/<service>.md` when the mapping belongs to one deployable service.

## Source Priority

When resolving expected deployment behavior:

1. Read wiki deployment metadata/runbooks first.
2. Check repository CI/CD config such as Cloud Build triggers, GitHub Actions, deploy scripts, or Terraform.
3. Check live cloud config such as Cloud Build triggers and service annotations.
4. Use fallback defaults only when the first three sources are absent or inconclusive.

Fallback defaults:

- `dev` -> staging;
- `main` -> prod;
- `master` -> prod.

If sources conflict, record the conflict and use `confidence: low` until a human resolves it.

## Template

Use this page shape:

````markdown
---
title: Deployment Mapping
type: runbook
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [runbook, deployment, gcloud, ci-cd]
sources:
  - raw/repo_snapshots/<snapshot>.md
  - raw/gcloud_inventory/<snapshot>.md
confidence: medium
---

# Deployment Mapping

## Source Priority

1. Wiki metadata/runbook
2. Repository CI/CD config
3. Live cloud config
4. Fallback defaults

## Repositories

### owner/repo

```yaml
repo: owner/repo
default_pr_base: dev
deploy_triggers:
  - branch: dev
    environment: staging
    provider: cloud-build
    project: <gcp-project>
    region: <region>
    service: <cloud-run-service-or-gke-workload>
    trigger: <cloud-build-trigger-name-or-id>
    url: <service-url-or-unknown>
    provenance:
      expected_commit_source: github
      build_source: cloud-build
      deployed_artifact: cloud-run-revision
  - branch: main
    environment: prod
    provider: cloud-build
    project: <gcp-project>
    region: <region>
    service: <cloud-run-service-or-gke-workload>
    trigger: <cloud-build-trigger-name-or-id>
    url: <service-url-or-unknown>
    provenance:
      expected_commit_source: github
      build_source: cloud-build
      deployed_artifact: cloud-run-revision
```

## Conflicts

- Describe any mismatch between wiki expectations, repo CI/CD config, and live cloud triggers.

## Verification Notes

- Note whether commit SHA/build ID/image digest/revision labels are available.
- If metadata is missing, recommend adding labels or annotations such as `commit_sha`, `branch`, and `build_id`.
````

## Safety

Do not store secrets, private env values, tokens, signed URLs, or credentials in deployment runbooks, raw reports, logs, or registry metadata. Store real values only in the ignored local vault under `secrets/`, when the user explicitly wants local secret management.

Deployment metadata pages should store resource names, project IDs, regions, trigger names, service names, URLs, commit SHAs, env variable names, secret ids, fingerprints, and non-secret labels. Use Secret Inventory for collecting scattered real values into `secrets/vault.local.env`.
