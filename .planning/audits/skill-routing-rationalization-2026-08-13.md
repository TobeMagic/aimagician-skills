# Skill Routing Rationalization: 2026-08-13

## Decision

Retain `cli-agent-delegator`. It owns an executable external-worker runtime:
model inventory and routing, event-based execution, quota fallback, frozen
review points, visual-evidence handoff, and bounded worker contracts. Moving
those into `aimagician-superpower` would make the engineering control plane
provider-specific and harder to maintain.

## Boundary Changes

- `aimagician-superpower` decides whether delegation has a net benefit.
- `cli-agent-delegator` applies only after the controller has decided to
  dispatch an external CLI worker.
- `agent-workstream-orchestrator` applies only to multiple lanes, durable
  sessions, worktree isolation, or integration; one worker does not need a
  registry.
- Prompt-level scope manifests are evidence controls, not tool-level sandboxes.
  Unattended security-sensitive or independent audit work requires runtime
  isolation before its result is accepted.

## Routing Tiers

| Tier | Skills | Default |
|---|---|---|
| Core runtime | Engineering, CLI delegation, orchestration, design, visual evidence, web testing, PR and SaaS routing | Route when task capability matches |
| Maintainer | `skill-creator`, `skill-optimizer` | Only when changing the Skill system |
| On-demand specialist | Academic, interview, perspective, explicit architecture research, GCP operations | Only on explicit domain need |

## Deferred Work

Do not archive `gcloud-ops-workflow` without evidence that GCP is no longer
used. It is classified as environment-specific instead. Runtime permission
isolation for OpenCode remains a prerequisite for unattended independent audit
evidence.
