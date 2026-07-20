# Planning Modes

Use this module only after target, boundaries, evidence, locked requirements, and implementation assumptions are stable.

## Plan Contract

A substantial plan names:

- objective, locked requirement IDs, and non-goals;
- exact files or ownership areas allowed and forbidden;
- atomic tasks and dependency waves;
- state, schema, API, migration, or compatibility effects;
- test-first steps where behavior can be pinned down;
- exact verification commands and expected outcomes;
- observable UAT where behavior is user-facing;
- rollback, recovery, checkpoints, and handoff expectations.

Every accepted requirement must map to at least one task. Every task must map to a requirement, explicit enabling work, or accepted maintenance need.

## Plan Modes

- **Quick:** one or two low-risk edits with one direct check.
- **Phase:** a resumable sequence with durable artifacts and gates.
- **Research:** evidence and recommendation are the deliverable; implementation is a later phase.
- **MVP:** smallest end-to-end slice first, then bounded extensions.
- **TDD:** failing behavior check, minimal implementation, pass, refactor, broader regression.
- **Repair:** reproduce, isolate, trace root cause, patch, regression check, nearby audit.
- **Review:** findings first, then accepted fixes or follow-up tasks.
- **Gap closure:** convert failed validation or audit findings into the smallest correcting tasks.
- **Ultra plan:** cross-system work with explicit workstreams, ownership, dependency graph, integration gates, and independent reviewers.

## Task Shape

Each task states:

1. requirement IDs and objective;
2. inputs and prerequisite decisions;
3. allowed and forbidden files;
4. exact implementation behavior;
5. test or probe to write or run;
6. acceptance and expected evidence;
7. checkpoint and next dependency.

Avoid instructions such as "handle errors" or "add tests" without naming the required cases.

## Independent Plan Review

For substantial work, dispatch a fresh plan reviewer with the specification, research conclusion, context, and complete plan. The reviewer checks:

- missing or extra scope;
- requirement coverage and falsifiability;
- wrong ordering or hidden dependency;
- unrealistic file scope;
- migration, security, concurrency, or compatibility omissions;
- weak verification or rollback;
- tasks too large for one focused implementation context.

Revise and re-review until no blocking or important finding remains. Do not let the plan author self-approval replace independent review.

Run `workflow.mjs validate --gate plan` while reviewing the plan, then mark accepted plans accordingly and run `validate --gate execute` before implementation. Use `trace` as evidence accumulates.
