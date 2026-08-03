# Local-First Full-Chain Delivery

Use this module when a change can reach CI, preview, staging, production, an installation target, or another shared environment. The objective is not to avoid online verification. It is to arrive there with the locally observable chain already understood and verified, so remote feedback is reserved for behavior that cannot be reproduced locally.

## Full-Chain Context Gate

Before implementation, map every applicable surface:

1. **Entry:** user action, command, request, event, or scheduler.
2. **Orchestration:** controller, workflow, route, state machine, or job.
3. **Domain behavior:** decisions, invariants, transformations, and failure semantics.
4. **State:** persistence, cache, migrations, queues, generated artifacts, and cleanup.
5. **External boundaries:** APIs, SaaS tools, cloud resources, permissions, and secrets.
6. **Build and delivery:** build graph, packaging, CI, preview, deployment, and rollback.
7. **Observability:** logs, metrics, traces, health checks, alerts, and operator controls.
8. **User-visible result:** output, UI, compatibility, documentation, and support impact.

Mark each surface `APPLICABLE`, `NOT_APPLICABLE`, or `UNKNOWN`, with evidence. An unresolved `UNKNOWN` blocks planning when it can change scope, architecture, migration, security, deployment, or acceptance.

## Verification Ladder

Classify the work as `Deployable` or `Non-deployable` and plan the corresponding ladder.

### 1. LOCAL

Complete every locally observable check before opening or updating the delivery path:

- static checks, unit and integration tests;
- local builds, packaging, migrations, fixtures, and smoke tests;
- local service or browser flows when practical;
- security, compatibility, performance, and failure-path probes justified by risk;
- generated artifact inspection and clean-worktree checks.

Do not use repeated remote CI or deployment as a substitute for missing local setup. If a check cannot run locally, record it as an `ONLINE_ONLY` exception with reason, owner, target environment, expected evidence, and failure response.

### 2. CI / PREMERGE

Run repository-required CI and independent review against a frozen commit or frozen worktree. Confirm:

- the reviewed revision is the revision proposed for merge;
- all accepted requirements map to implementation and evidence;
- generated or packaged artifacts correspond to that revision;
- no unresolved Blocker or Important finding remains.

The premerge decision is either `MERGE_READY` or `NOT_READY`.

### 3. PREVIEW

Use preview or staging when risk, repository policy, migrations, integrations, infrastructure, or user-visible behavior justify it. Record `N/A` only with a concrete rationale.

Preview evidence does not replace local evidence or postmerge production evidence.

### 4. POSTMERGE

For deployable work, completion occurs only after:

- the implementation merge SHA is recorded;
- the deployed artifact or release is proven to derive from that SHA, or an approved provenance exception is documented;
- required online smoke, health, integration, migration, and user-visible checks pass;
- a fresh independent completion audit reviews the original request, planning checklist, merged revision, and online evidence.

Keep the planning checklist open between merge and online confirmation. A closure-only planning commit may follow the implementation deployment; record that it is metadata-only.

## Online-Only Contract

Every online-only check records:

| Check | Why local is insufficient | Target | Expected evidence | Failure response | Owner |
|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD |

`ONLINE_ONLY` is an explicit exception, not a generic skip state.

## Failure And Recovery

If postmerge verification fails:

1. reopen or keep open the affected requirement and delivery checklist;
2. preserve the failed revision, environment, evidence, and impact;
3. follow the repository's documented rollback, roll-forward, mitigation, or incident procedure;
4. do not invent a generic automatic rollback;
5. rerun the affected local, CI, preview, and postmerge checks after remediation;
6. obtain a fresh independent audit before closure.

Use `Recovery status: COMPLETE` only when the selected recovery path and its verification are evidenced. Otherwise the task remains incomplete.

## Evidence Integrity

Evidence must identify the command or probe, environment, revision or artifact, observed result, and timestamp when relevant. A passing test name without output or revision provenance is not enough for a deployable completion claim.
