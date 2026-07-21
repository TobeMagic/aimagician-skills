# Engineering Delivery Playbooks

Use this module to turn an accepted design into reversible, testable slices. Start with the common loop, then apply the task-specific playbook.

## Common Delivery Loop

1. Pin the behavior with a failing check or preserved baseline.
2. Implement the smallest end-to-end tracer slice through the real integration path.
3. Run the narrow check and inspect the diff.
4. Refactor only while behavior remains green.
5. Add boundary and failure cases in risk order.
6. Run broader regression checks according to blast radius.
7. Perform specification review, then engineering quality review.
8. Record evidence, residual risk, and the next reversible checkpoint.

Do not build all storage, then all services, then all UI without an integrated slice. Horizontal groundwork is justified only when no observable slice can exist without it; keep it bounded and immediately consumed.

## Feature Development

- Start from a concrete user or caller scenario and acceptance example.
- Identify the narrowest vertical slice that proves routing, domain behavior, persistence, and presentation as applicable.
- Preserve compatibility by default; make changed defaults explicit.
- Cover normal, boundary, failure, and recovery behavior.
- Include integration wiring and remove no legacy path until replacement evidence passes.

## Bug Repair

- Build a fast feedback loop that reliably goes red.
- Minimize the reproduction without changing the symptom.
- Write three to five ranked hypotheses with distinguishing probes.
- Instrument only what separates hypotheses; tag temporary diagnostics and remove them.
- Fix the earliest controllable cause, add a regression check, rerun the original scenario, then record a short causal chain and prevention note.

Read `debugging-and-forensics.md` for intermittent, stateful, polluted, or production-only failures.

## Refactoring

- Establish a behavior characterization baseline before structure changes.
- Map callers, contracts, dependency direction, and migration order.
- Use expand-contract for wide changes: introduce the new path, migrate consumers in bounded batches, verify dual behavior, then remove the old path.
- Keep compatibility shims temporary, observable, and owned by a removal task.
- Separate mechanical moves from semantic changes when possible so each diff is reviewable.

## Performance Optimization

- Define workload, environment, metric, baseline, target budget, and acceptable tradeoffs.
- Prove the bottleneck before optimizing.
- Change one causal factor at a time and compare equivalent runs.
- Guard correctness under load, not only speed.
- Add a repeatable benchmark or operational signal that catches regression without creating flaky gates.

## Architecture Change

- Record the domain model, dependency direction, current constraint, and why local repair is insufficient.
- Design two structurally different options and include a no-change option.
- Prefer strangler or expand-contract migration with explicit checkpoints over flag-day replacement.
- Define data compatibility, rollout, observability, rollback, and old-path removal before implementation.

## Prototype Or Spike

- State the single uncertainty and a time or evidence stop condition.
- Choose logic prototype for algorithm or integration uncertainty; choose UI prototype for interaction or visual uncertainty.
- Make it runnable with one documented command and avoid production persistence or hidden coupling.
- Treat the result as disposable unless it passes normal design, test, review, and migration gates.
- Capture verdict, evidence, limitations, and recommended next step before deleting or promoting it.

## Merge Conflict Resolution

- Reconstruct the intent of base, current branch, and incoming branch.
- Preserve both valid behaviors rather than choosing text mechanically.
- Resolve the smallest coherent region, inspect the resulting diff, and run tests for both intents.
- Never discard unfamiliar changes merely to make the conflict marker disappear.

Use `scripts/engineering-route.mjs` to obtain the minimum artifact and review route for a task type, and `assets/templates/engineering-change-brief.md` to make slices executable by another agent.
