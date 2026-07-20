# Verification And UAT

Use this module before any completion claim and whenever work changes behavior, installation state, documents, UI, integrations, data, or operational state.

## Evidence Order

1. Run the narrowest behavior check for the changed unit.
2. Run related regression tests and integration checks.
3. Broaden to typecheck, lint, build, browser, document, security, package, or smoke verification according to blast radius.
4. Inspect generated or installed artifacts directly when tests cannot prove their real shape.
5. Exercise UAT for user-facing outcomes.
6. Trace every accepted requirement to passing evidence.

Fresh command output and inspected artifacts outrank an agent's summary or a previous run. Record the timestamp or commit when stale evidence could be misleading.

## Evidence Record

For every requirement ID, record:

- status: `PASS`, `FAIL`, or `NOT_RUN`;
- command, scenario, inspection, or artifact path;
- expected and observed result;
- environment or target;
- gap, limitation, or residual risk.

`NOT_RUN` is not a pass. A skipped check needs a reason and an explicit closure decision.

## UAT Contract

For user-visible work, define scenario, starting state, action, expected visible result, expected side effect, result, and evidence. Include normal, empty or boundary, failure, and recovery cases when they are relevant.

Use `interface-design` and `webapp-testing` for visual, responsive, accessibility, console, and network acceptance. Generated documents must be opened, extracted, rendered, or structurally inspected with the appropriate document workflow.

## Traceability Gate

Run `workflow.mjs trace` to detect:

- an accepted requirement absent from all plans;
- a planned requirement with no validation evidence;
- failed or not-run evidence;
- evidence that names an unknown requirement.

Before execution, `validate --gate plan` must pass. Before closure, `validate --gate complete` must pass unless the user explicitly accepts and records an exception.

## Failed Verification

Preserve output, classify implementation/test/environment/flaky/pre-existing failure, repair only relevant scope, rerun the narrow check, and broaden only after it passes. Do not hide a failed broad check because a narrow test passed.
