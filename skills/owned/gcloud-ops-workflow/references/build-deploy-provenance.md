# Build / Deploy Provenance

Use this reference to answer: "Did this branch push or merge deploy the expected commit to the expected environment?"

## Branch-To-Environment Mapping

Resolve the expected deployment mapping in this order:

1. Project `LLM-know-how-wiki` deployment metadata/runbooks.
2. Repository CI/CD files such as Cloud Build triggers, GitHub Actions, deploy scripts, or Terraform.
3. Live cloud config such as Cloud Build trigger branch filters and service annotations.
4. Fallback defaults.

Fallback defaults:

- `dev` -> staging;
- `main` -> prod;
- `master` -> prod.

Do not assume `dev` is the only deploy branch.

If sources conflict, return `UNKNOWN` or a conflict-specific finding until a human resolves the expected mapping. Do not silently choose live state over wiki or wiki over live state.

## Verification Inputs

Collect:

- expected branch and commit SHA;
- target environment;
- mapping source and confidence;
- GCP project, region/zone, and service/workload;
- Cloud Build trigger name or ID if known;
- expected service URL if known.

## Cloud Build Checks

```bash
gcloud builds list \
  --project <project> \
  --filter='substitutions.BRANCH_NAME="<branch>" OR source.repoSource.branchName="<branch>"' \
  --limit 20 \
  --format='table(id,status,createTime,finishTime,substitutions.SHORT_SHA,substitutions.COMMIT_SHA,substitutions.BRANCH_NAME,substitutions.TRIGGER_NAME)'

gcloud builds describe <build-id> \
  --project <project> \
  --format=json
```

From the build, capture:

- build ID and status;
- source branch;
- commit SHA or short SHA;
- trigger name/ID;
- built image or artifact digest;
- start and finish time.

## Cloud Run Deployment Checks

```bash
gcloud run services describe <service> \
  --project <project> \
  --region <region> \
  --format=json

gcloud run revisions list \
  --service <service> \
  --project <project> \
  --region <region> \
  --format='table(metadata.name,status.conditions[0].status,status.conditions[0].reason,metadata.creationTimestamp,spec.containers[0].image)'
```

Capture:

- service URL;
- latest ready revision;
- traffic target revision;
- deployed image and digest when available;
- revision labels/annotations that include commit or build metadata.

## GKE Deployment Checks

```bash
kubectl get deploy <deployment> -n <namespace> -o json
kubectl rollout status deploy/<deployment> -n <namespace>
```

Capture:

- deployment namespace/name;
- image and digest;
- rollout status;
- pod template labels/annotations with commit/build metadata when available.

## Verdict

Return one of:

- `MATCH`: expected commit matches Cloud Build source and deployed artifact/revision.
- `MISMATCH`: deployed artifact/revision points to a different commit or build.
- `UNKNOWN`: metadata is missing or ambiguous.
- `CONFLICT`: wiki expectations, repo CI/CD config, and live cloud state disagree about the target environment or trigger.

Always explain what evidence supports the verdict and what evidence is missing.

## Linear / Wiki Record

If verification is part of a Linear issue, comment:

```text
Deployment verification:
- environment:
- branch:
- expected commit:
- build:
- deployed revision/image:
- URL:
- verdict:
- notes:
```

Also record the activity in `LLM-know-how-wiki`.
