# Engineering Review

Use this module for plans, implementation diffs, refactors, bug fixes, and pre-closure audits. Findings lead; summaries follow.

## Fix The Review Point

Record the exact base and current commit, merge base and target when relevant, diff or file set, generated artifact, or working-tree state under review. Do not let the review point move while findings are being produced. Identify:

- the accepted specification, issue, or user objective;
- repository standards, architecture records, and local patterns;
- tests and runtime evidence already available;
- changes explicitly outside review scope.

Do not review an agent summary instead of the code and evidence.

## Two-Pass Review

### Pass 1: Specification Compliance

Check requirement coverage, observable behavior, boundaries, non-goals, integration wiring, compatibility, migration, and acceptance evidence. Report missing behavior, extra behavior, or divergence before style concerns.

### Pass 2: Engineering Standards

Review:

- correctness, state transitions, edge cases, errors, retries, cleanup, and concurrency;
- security, permissions, validation, sensitive data, and trust boundaries;
- test quality, behavior coverage, determinism, and meaningful failure reasons;
- maintainability, domain language, interface size, locality, duplication, and hidden coupling;
- extensibility only for credible change axes, not speculative frameworks;
- performance, resource lifecycle, scale assumptions, and measurement;
- operability, logging, metrics, rollout, rollback, and diagnosis;
- diff hygiene, dead code, temporary diagnostics, generated churn, and documentation accuracy.

Treat the two passes as independent axes: a specification-complete implementation can still fail engineering standards, and an elegant implementation can still be the wrong behavior. For substantial work, use fresh reviewer contexts for the two passes. Parallel independent quality reviews are useful when security, data, concurrency, or architecture risk is high, but the main agent must reconcile duplicate or contradictory findings.

## Smell Tests

Investigate when a change has a broad interface hiding little behavior, knowledge duplicated across callers, tests tied to private structure, a boolean that encodes multiple states, shotgun edits for one concept, compatibility code with no removal path, errors swallowed without policy, or an abstraction introduced before a second real use.

## Finding Format

Each finding includes:

- severity: blocker, high, medium, or low;
- concrete path and line or symbol;
- violated requirement, invariant, or engineering principle;
- user or system impact;
- evidence or reproduction;
- smallest credible remediation and required verification.

Do not inflate severity, report preferences as defects, or bury a blocker under general praise. When no finding remains, say so and name residual test gaps or uncertainty.

Use `assets/templates/engineering-review.md` for durable review evidence. A review is closed only after accepted findings are fixed and re-reviewed, explicitly deferred, or rejected with evidence.
