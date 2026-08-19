# Independent Review And Audit

Use this task family to create a fresh evidence-based challenge to a plan, implementation, verification record, phase, milestone, or completion claim. The reviewer never substitutes for the main Agent's final judgment.

## Risk-Scaled Gates

| Work class | Required independent gate |
|---|---|
| One- or two-file read-only lookup | None |
| Bounded quick write | Decisive controller verification; add one combined pre-commit review only when project policy, diff risk, or a user request justifies it |
| Substantial implementation | Plan review before execution; specification review; quality review; verifier |
| Phase closure | Phase auditor after verification |
| Milestone, release, deployable postmerge, or High completion claim | Fresh whole-result auditor |
| High-risk security, data, concurrency, migration, or architecture work | Additional focused reviewer where the axis is independent |

Use a fresh OpenCode session or context for each logically independent review pass. Do not ask the implementer to approve its own work.

Every audit-required row uses a fresh OpenCode session, an explicitly controller-selected free model chain, and original-request traceability. Visual evidence comes from `vision-analysis`; the controller then selects the text reviewer for the audit's difficulty and records the rationale. For Quick and Standard closure, passing the decisive behavior check plus the repository's actual merge protections is sufficient unless a required audit trigger applies.

## Freeze The Review Point

Every prompt names the exact:

- user objective and latest accepted decisions;
- specification, requirements, non-goals, and source of truth;
- base/head commits, merge base, named diff, worktree state, plan, artifact set, or installation target;
- allowed review paths and excluded user-owned changes;
- existing evidence and checks the reviewer may run.

Do not let the review point change during the pass. Review actual files and evidence, not an implementation summary.

Use the owned runner binding:

- `--review-ref <git-ref>` resolves the commit and creates a temporary detached worktree for the review;
- `--review-worktree <path>` fingerprints the exact worktree before and after the review.

The runtime fails the review if the fingerprint changes. Record the resolved commit and fingerprint in the report. Do not accept a free-form `REVIEW_POINT` label as proof that the reviewed files were frozen.

## Review Roles

### Plan Reviewer

Check requirement mapping, missing or extra scope, dependency order, task atomicity, realistic ownership, test seams, integration, security, compatibility, migration, rollback, resumability, and whether the plan can be executed without inventing design decisions.

### Specification Reviewer

Compare actual behavior and files with accepted requirements. Find missing, incorrect, or extra behavior; altered contracts; unwired integration; weak acceptance; and unsupported claims. Do this before general style review.

### Quality Reviewer

After specification compliance, inspect correctness, edge cases, errors, cleanup, security, data handling, concurrency, performance, compatibility, test quality, maintainability, local conventions, regression risk, operability, unnecessary complexity, and diff hygiene.

### Verifier

Run or inspect the narrowest decisive checks, then broaden by blast radius. Record every requirement as `PASS`, `FAIL`, or `NOT_RUN`; fresh output outranks previous summaries.

### Phase Or Milestone Auditor

Trace the original objective and latest user decisions through specification, implementation, integration, reviews, verification, UAT, documentation, installation state, and handoff. Challenge capability-loss and “complete” claims directly.

## Finding Severity

Use exactly:

- `Blocker`: behavior is incorrect, unsafe, outside accepted scope, or lacks evidence required for progression or completion. Stop the gate.
- `Important`: material correctness, maintainability, test, security, compatibility, or requirement risk. Fix and re-review, or defer only with explicit user approval.
- `Nitpick`: non-blocking improvement with clear value. Record without holding the gate.

Do not use Critical/High/Medium/Low for this review protocol. Do not inflate preferences into findings.

## Disposition Versus Severity

Severity describes impact. Closure disposition is separate:

- fixed and re-reviewed;
- explicitly deferred by the user;
- rejected with evidence;
- follow-up outside the accepted objective.

A phase or milestone is not complete with an unresolved Blocker or Important finding unless the user explicitly changes the accepted boundary.

## Report

Use `../report-templates/review-report.md`. Findings lead. State `APPROVED`, `COMPLIANT`, `COMPLETE`, or the corresponding negative recommendation only after checking the actual review point and evidence.
