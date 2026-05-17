# Cloud Storage

Cloud Storage may be accessed by `gcloud storage` or `gsutil`; prefer `gcloud storage` for new workflows.

## Read-Only Checks

```bash
gcloud storage buckets list --project <project>
gcloud storage buckets describe gs://<bucket> --project <project>
gcloud storage ls gs://<bucket>/<prefix> --project <project>
gcloud storage buckets get-iam-policy gs://<bucket> --project <project>
gcloud storage buckets describe gs://<bucket> --format=json
```

## What To Capture

- bucket name and location;
- storage class;
- uniform bucket-level access setting;
- lifecycle and retention policy presence;
- IAM bindings when relevant;
- object prefix existence and sample object names.

## Safety

Do not run `rm`, `mv`, lifecycle changes, IAM writes, or retention changes without explicit approval.

Avoid recording signed URLs.

