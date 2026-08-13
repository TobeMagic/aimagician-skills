# Cloud SQL

## Read-Only Checks

```bash
gcloud sql instances list --project <project>
gcloud sql instances describe <instance> --project <project> --format=yaml
gcloud sql databases list --instance <instance> --project <project>
gcloud sql users list --instance <instance> --project <project>
gcloud sql backups list --instance <instance> --project <project>
gcloud sql operations list --instance <instance> --project <project> --limit 20
```

## What To Capture

- instance name, region, database version, state;
- connection name;
- public/private IP presence, not passwords;
- backup enabled/latest backup;
- maintenance window;
- authorized networks count, not sensitive details unless needed;
- database and user names when relevant.

## Safety

Never record passwords or connection strings with credentials.

Do not run password resets, instance patches, deletes, imports, exports, or failover commands without explicit approval.

For a deletion rollback plan, verify the backup ID or name first, then name the actual restore form accurately. Recovery is itself a mutation and needs separate approval:

```bash
gcloud sql backups restore <backup-id-or-name> \
  --restore-instance=<new-or-approved-target-instance> \
  --project <project>
```

Do not invent a `gcloud sql restore-backup` command. Restoring over an existing production target carries its own blast radius; prefer a new target instance unless the approved recovery plan requires otherwise.

## Common Diagnoses

- App cannot connect: check connection name, private/public IP mode, service account IAM, VPC connector, Cloud SQL Auth Proxy config.
- Latency/spikes: check operations, CPU/memory metrics in console or monitoring, slow logs if enabled.
- Migration risk: check backups and recent operations first.
