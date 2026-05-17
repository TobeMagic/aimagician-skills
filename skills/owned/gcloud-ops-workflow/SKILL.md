---
name: gcloud-ops-workflow
description: Use when inspecting, debugging, inventorying, or safely operating Google Cloud resources with gcloud, especially Cloud Run, GKE, GCS/Cloud Storage, VPC, Cloud SQL, logging, infrastructure runbooks, or wiki-recorded cloud ops workflows.
metadata:
  related_skills:
    - llm-know-how-wiki
    - linear-issue-workflow
    - github-pr-workflow
compatibility:
  tools: [bash, gcloud, gsutil, kubectl, python]
  requires: Authenticated gcloud account and explicit project/region/zone for real cloud operations
---

# Gcloud Ops Workflow

Use this skill for Google Cloud inspection, debugging, and guarded operations. The default mode is read-only. Treat production resources as high-risk unless the human explicitly says otherwise.

## First Reads

- Always read [`references/safety-rules.md`](./references/safety-rules.md) before running cloud commands.
- Read the service-specific reference before acting: Cloud Run, GKE, Cloud Storage, VPC, Cloud SQL, or Logging.
- For build/deploy verification, read [`references/build-deploy-provenance.md`](./references/build-deploy-provenance.md).
- For project-specific conventions, read the local `LLM-know-how-wiki` if present. Look for `wiki/runbook/*infra*`, `wiki/runbook/*operations*`, `wiki/api/service_endpoint_inventory.md`, and `wiki/index.md`.

## Core Rules

- Prefer read-only commands: `describe`, `list`, `get-iam-policy`, `logs read`, `kubectl get`, `kubectl describe`, `kubectl logs`.
- Use explicit `--project`, `--region`, `--zone`, `--cluster`, and namespace flags. Do not rely on ambient defaults for real operations.
- Never record secret values. Record resource names, URLs, service accounts, env var names, and connection names only.
- Before any mutating command, show the exact command, blast radius, rollback path, and required confirmation.
- Do not run destructive commands such as `delete`, `set-iam-policy`, `deploy`, `update`, `sql users set-password`, or `kubectl apply/delete` without explicit human approval.
- For automatic deployments, resolve branch-to-environment mapping from the project `LLM-know-how-wiki` first, then repo CI/CD config, then live cloud config. Use defaults such as `dev` -> staging and `main`/`master` -> prod only as fallback.
- Record meaningful cloud inspection or operation results into the project `LLM-know-how-wiki`.

## Standard Workflow

1. **Context**
   - Identify project, region/zone, environment, service/resource name, and question.
   - Confirm whether the task is read-only or mutating.

2. **Inventory**
   - Use `scripts/gcloud_inventory.sh` for a safe shallow snapshot when broad context is useful.
   - Store snapshots under `raw/gcloud_inventory/` when a wiki root is available.

3. **Focused Debug**
   - Cloud Run: service, revision, traffic, URL, logs, env var names.
   - GKE: cluster, namespace, deployment, pod, events, logs, KEDA, service account.
   - Cloud Storage: bucket metadata, IAM, object prefix checks, lifecycle.
   - VPC: subnet, firewall, routes, NAT, Serverless VPC connector.
   - Cloud SQL: instance health, backups, connections, private IP, IAM.
   - Logging: scoped error queries with time bounds.
   - Build/deploy provenance: Cloud Build trigger/build, source commit, artifact/image digest, Cloud Run/GKE deployed revision, service URL, and MATCH/MISMATCH/UNKNOWN verdict.

4. **Plan Mutations**
   - For deploy/update/delete/IAM/password/network changes, produce a plan first.
   - Wait for explicit human approval before executing.

5. **Record**
   - Write a workflow activity or inventory snapshot to `LLM-know-how-wiki`.
   - Include commands run, resource names, timestamps, and findings.

## Useful Command

```bash
./scripts/gcloud_inventory.sh --project <project-id> --region <region> --wiki-root <wiki-root>
```

The script is read-only. It redacts obvious secret-looking env values and appends `wiki/log.md` when `--wiki-root` is provided.

## References

- [`references/safety-rules.md`](./references/safety-rules.md)
- [`references/cloud-run.md`](./references/cloud-run.md)
- [`references/gke.md`](./references/gke.md)
- [`references/cloud-storage.md`](./references/cloud-storage.md)
- [`references/vpc.md`](./references/vpc.md)
- [`references/cloud-sql.md`](./references/cloud-sql.md)
- [`references/logging.md`](./references/logging.md)
- [`references/build-deploy-provenance.md`](./references/build-deploy-provenance.md)
