---
name: gcloud-ops-workflow
description: Use when inspecting, debugging, inventorying, or safely operating
  Google Cloud resources with gcloud, especially Cloud Run, GKE, GCS/Cloud
  Storage, VPC, Cloud SQL, logging, infrastructure runbooks, or wiki-recorded
  cloud ops workflows.
metadata:
  related_skills:
    - llm-know-how-wiki
    - composio-tool-router
    - github-pr-workflow
compatibility:
  tools:
    - bash
    - gcloud
    - gsutil
    - kubectl
    - python
  requires: Authenticated gcloud account and explicit project/region/zone for real
    cloud operations
category: operate
subcategory: cloud
tags:
  - gcloud
  - cloud-run
  - gke
  - environment-specific
---

# Gcloud Ops Workflow

Use this skill for Google Cloud inspection, debugging, and guarded operations. The default mode is read-only. Treat production resources as high-risk unless the human explicitly says otherwise.

Do not load it merely because a repository has deployment files. Use it only when the accepted task needs Google Cloud evidence or a guarded Google Cloud operation.

## First Reads

- Always read [`references/safety-rules.md`](./references/safety-rules.md) before running cloud commands.
- Read the service-specific reference before acting: Cloud Run, GKE, Cloud Storage, VPC, Cloud SQL, or Logging.
- For build/deploy verification, read [`references/build-deploy-provenance.md`](./references/build-deploy-provenance.md).
- For project-specific conventions, read the local `LLM-know-how-wiki` if present. Look for `wiki/runbook/*infra*`, `wiki/runbook/*operations*`, `wiki/api/service_endpoint_inventory.md`, and `wiki/index.md`.

## Core Rules

- Prefer read-only commands: `describe`, `list`, `get-iam-policy`, `logs read`, `kubectl get`, `kubectl describe`, `kubectl logs`.
- Use explicit `--project`, `--region`, `--zone`, `--cluster`, and namespace flags. Do not rely on ambient defaults for real operations.
- Do not use `gcloud config` or `gcloud auth list` to infer a target or as routine evidence. Diagnose authentication only after a target-scoped command fails, and never include account identity, configuration paths, or token metadata in a handoff.
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

## Operation Checkpoints

### 1. Bind The Target

Record project, environment, region or zone, resource identity, user question, and read-only versus mutation classification before the first cloud command.

### 2. Prove Before Mutation

For any change, show the exact command, blast radius, rollback or roll-forward path, preconditions, and verification target; wait for explicit approval.

### 3. Reconcile Deployment Evidence

Compare the expected commit or artifact with build, revision, and runtime evidence. Return `MATCH`, `MISMATCH`, `UNKNOWN`, or `CONFLICT`; do not infer production state from branch naming alone.

### 4. Record A Safe Handoff

Store only resource identity, commands, timestamps, redacted findings, and verification state in the project runbook or activity record.

**CHECKPOINT:** A cloud action may advance only when explicit target flags, least-privilege command, evidence destination, and any required human approval are all present.

**CHECKPOINT:** Confirm every listed resource belongs to the resolved project/environment before interpreting logs, IAM, traffic, or deployment state.

**CHECKPOINT:** If a write, destructive action, or rollback decision is not explicitly authorized, stop at the read-only diagnosis and return the exact approval question.

## Failure Handling

| Trigger | First response | Fallback |
|---|---|---|
| Project, location, resource, or environment mapping is unknown | Inspect the project runbook, repository config, and read-only inventory | Ask for the missing selector; do not use ambient gcloud defaults |
| Authentication, permission, or API query fails | Record the redacted error and the least-privilege missing permission | Stop mutation and provide the exact read-only recovery or escalation step |
| Mutation plan, deploy provenance, or rollback path is incomplete | Stop before execution and show the unproven condition | Produce a read-only diagnosis and wait for explicit approval or a revised plan |

When environment evidence is conflicting, stop the mutation path and report `CONFLICT` with the bounded read-only commands needed to resolve it.

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
