# Domain Gates

Use this module to add specialized contracts without creating a competing workflow.

## Code And API

- Preserve existing architecture, types, error contracts, compatibility, and public behavior unless the specification changes them.
- Test success, invalid input, error propagation, boundary values, and relevant concurrency.
- For API or schema changes, specify consumers, versioning, migration, rollback, and observability.

## UI And Frontend

Create a UI contract for substantial visual work: target users, flows, states, design system, typography, color, spacing, copy, accessibility, responsive behavior, loading, empty, error, and interaction acceptance. Route detailed design and visual review to `interface-design`; route browser evidence to `webapp-testing`.

## AI And Evaluation

Create an AI contract when outputs depend on a model: task definition, model/provider constraints, input and output schema, grounding, prompt or tool boundaries, safety, latency/cost, fallback, deterministic components, eval dataset, metrics, thresholds, failure examples, and human review. Verification must compare implemented evals with the contract rather than reporting a few successful samples.

## Security, Secrets, And Permissions

Threat-model trust boundaries, authentication, authorization, secret flow, sensitive logs, dependency risk, abuse cases, least privilege, failure defaults, rotation, and rollback. Never record secret values in planning or evidence. Route inventory, vault, cache, and sensitive scans to `llm-know-how-wiki`.

## Data And Migration

Specify old and new shape, volume, invariants, backfill, idempotency, partial failure, compatibility window, verification queries, rollback, and data-retention effects. Test upgrade and recovery, not only the final schema.

## Documents And Generated Assets

Preserve source templates and styles, validate generated structure, open or render the output, check content and layout, and record exact deliverable paths. Avoid unrelated binary churn.

## Operations And Installation

Prefer read-only inventory first. Confirm target, permission, blast radius, maintenance window, dry run, rollback, observability, and post-change verification before mutation. Installation must preview managed paths and preserve unmanaged files.

## Git, Worktrees, PR, And Review

Protect dirty user work, use isolated worktrees for interrupting or parallel work, keep commits scoped, and inspect integration results. Route parallel worktrees to `parallel-worktree-pr-flow` and PR/CI/reviewer closure to `github-pr-workflow`.
