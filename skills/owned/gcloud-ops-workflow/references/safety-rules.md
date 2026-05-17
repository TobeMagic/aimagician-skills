# Gcloud Safety Rules

## Default Posture

Default to read-only inspection. Cloud state is mutable, shared, and often production-critical.

## Required Context

Before running real cloud commands, identify:

- project ID;
- account from `gcloud auth list --filter=status:ACTIVE`;
- region or zone;
- environment label, if known;
- resource name;
- whether the operation is read-only or mutating.

## Secret Handling

Never print or store:

- secret values;
- full environment variable values;
- database passwords;
- tokens, cookies, private keys, signed URLs;
- service account key JSON.

Allowed to record:

- service names and URLs;
- bucket names;
- Cloud SQL instance names and connection names;
- service account emails;
- env var names without values;
- IAM member names when needed for diagnosis.

## Mutating Commands Need Approval

Do not run these without explicit human approval:

- `gcloud run deploy`, `update`, `delete`, `services replace`;
- `gcloud container clusters update/delete`;
- `kubectl apply`, `delete`, `rollout restart`, `scale`, `patch`;
- `gcloud storage rm`, `buckets delete`, IAM changes;
- `gcloud compute firewall-rules create/update/delete`;
- `gcloud sql instances patch/delete`, `sql users set-password`;
- any `set-iam-policy`, `add-iam-policy-binding`, or `remove-iam-policy-binding`.

For any mutation, first show:

- exact command;
- target project and resource;
- expected effect;
- rollback path;
- verification command.

## Wiki Recording

Record meaningful investigations as:

- `raw/gcloud_inventory/<timestamp>-inventory.md` for broad snapshots;
- `raw/workflow_activity/<timestamp>-*.md` for action logs;
- `wiki/log.md` entry with operation label `GCLOUD_INVENTORY` or `GCLOUD_OPS_WORKFLOW`.

