---
title: Deployment Mapping
type: runbook
status: active
created: {{DATE}}
updated: {{DATE}}
tags: [runbook, deployment, ci-cd]
sources: []
confidence: medium
---

# Deployment Mapping

## Source Priority

1. Wiki metadata/runbook
2. Repository CI/CD config
3. Live cloud config
4. Fallback defaults

## Repositories

### <owner/repo>

```yaml
repo: <owner/repo>
default_pr_base: dev
deploy_triggers:
  - branch: dev
    environment: staging
    provider: cloud-build
    project: <gcp-project>
    region: <region>
    service: <cloud-run-service-or-gke-workload>
    trigger: <trigger-name-or-id>
    url: <url-or-unknown>
  - branch: main
    environment: prod
    provider: cloud-build
    project: <gcp-project>
    region: <region>
    service: <cloud-run-service-or-gke-workload>
    trigger: <trigger-name-or-id>
    url: <url-or-unknown>
```

## Conflicts

## Verification Notes

## Related

## Sources
