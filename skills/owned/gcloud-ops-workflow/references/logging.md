# Logging

## Scoped Queries

Always bound logs by project, resource, service, and time.

Cloud Run:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="<service>" AND severity>=ERROR' \
  --project <project> \
  --freshness 2h \
  --limit 100
```

GKE container:

```bash
gcloud logging read \
  'resource.type="k8s_container" AND resource.labels.namespace_name="<namespace>" AND resource.labels.container_name="<container>" AND severity>=ERROR' \
  --project <project> \
  --freshness 2h \
  --limit 100
```

Cloud SQL:

```bash
gcloud logging read \
  'resource.type="cloudsql_database" AND resource.labels.database_id=~"<instance>" AND severity>=ERROR' \
  --project <project> \
  --freshness 6h \
  --limit 100
```

## What To Capture

- query used;
- time window;
- error timestamps;
- service/resource names;
- concise error signatures.

Redact payloads that include credentials, cookies, user PII, request bodies, or signed URLs.

