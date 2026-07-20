# Debugging And Forensics

Use this module for failures, flaky behavior, regressions, data corruption, state pollution, intermittent integration errors, or unclear root causes.

## Four-Stage Method

### 1. Reproduce And Preserve

- Capture the smallest reliable reproduction, exact command, environment, inputs, expected behavior, actual behavior, and sanitized output.
- Determine whether the failure is deterministic, intermittent, load-related, order-dependent, or environment-specific.
- Preserve logs and state before cleanup destroys evidence.

### 2. Isolate And Trace

- Reduce the failing path without changing the symptom.
- Trace backward from the bad value, side effect, or state transition to its first incorrect origin.
- Inspect control flow, data flow, lifecycle, concurrency, caching, configuration, and external boundaries.
- Compare working and failing cases one variable at a time.
- Use `find-polluter.mjs` when a test or command creates unwanted filesystem state.

### 3. Form And Test Hypotheses

- State one falsifiable root-cause hypothesis.
- Design the smallest probe that distinguishes it from alternatives.
- Change one variable at a time.
- If three targeted attempts fail, stop patching and revisit architecture, assumptions, or missing context.

### 4. Correct And Defend

- Patch the earliest controllable root cause, not only the visible symptom.
- Add validation at meaningful boundaries when bad data could travel farther.
- Add a regression check that fails before and passes after the fix.
- Re-run the original scenario, nearby cases, and broader checks justified by blast radius.

## Condition-Based Waiting

Wait for observable state, event, file, process result, count, or response rather than guessing a sleep duration. A safety timeout is still required for test conditions and must report what condition was not met. Timing tests may use a fixed delay only when the timing itself is the behavior and the reason is documented.

Use `wait-for.mjs` to retry a non-destructive command until it exits successfully. External CLI-agent runs follow their provider's activity-event policy instead of this test helper.

## State-Pollution Safety

Before searching for a polluter:

- assert the watched path or state is initially clean;
- enumerate candidate tests explicitly;
- run candidates sequentially in isolation;
- stop at the first creator and preserve the state;
- never delete the watched path automatically.

## Forensic Report

Record reproduction, timeline, evidence, ruled-out hypotheses, root cause, causal chain, patch, regression check, defense-in-depth changes, residual uncertainty, and commands needed to reproduce or verify.
