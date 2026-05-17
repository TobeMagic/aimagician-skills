# Cloud Run

## Read-Only Checks

```bash
gcloud run services list --project <project> --region <region>
gcloud run services describe <service> --project <project> --region <region> --format=yaml
gcloud run revisions list --service <service> --project <project> --region <region>
gcloud run services get-iam-policy <service> --project <project> --region <region>
```

## Logs

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="<service>"' \
  --project <project> \
  --limit 100 \
  --freshness 2h \
  --format=json
```

## What To Capture

- service name and URL;
- region;
- latest ready revision;
- traffic split;
- service account email;
- env var names, not values;
- VPC connector name if present;
- recent errors with timestamps.

## Common Diagnoses

- URL works but API fails: check revision logs, env var names, service account, Cloud SQL connector, VPC connector.
- New deploy not receiving traffic: check traffic split and latest ready revision.
- Cold start or timeout: check concurrency, timeout, min instances, startup logs.

