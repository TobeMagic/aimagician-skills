# Debugging And Forensics

Use this module for failures, flaky behavior, regressions, data corruption, state pollution, intermittent integration errors, or unclear root causes.

## Six-Stage Method

### 1. Build A Feedback Loop

- Find the fastest observable loop that reliably distinguishes failing from working behavior. Prefer a focused automated test, then a deterministic script or API call, then a bounded runtime probe.
- Confirm the loop goes red before changing implementation. If it is too slow or noisy to guide one hypothesis at a time, tighten it first.

### 2. Reproduce, Preserve, And Minimize

- Capture the exact command, environment, inputs, expected behavior, actual behavior, and sanitized output.
- Determine whether the failure is deterministic, intermittent, load-related, order-dependent, or environment-specific.
- Preserve logs and state before cleanup destroys evidence.
- Remove unrelated inputs, setup, and modules one at a time while preserving the same failure signature.

### 3. Isolate And Trace

- Reduce the failing path without changing the symptom.
- Trace backward from the bad value, side effect, or state transition to its first incorrect origin.
- Inspect control flow, data flow, lifecycle, concurrency, caching, configuration, and external boundaries.
- Compare working and failing cases one variable at a time.
- Use `find-polluter.mjs` when a test or command creates unwanted filesystem state.

### 4. Rank And Test Hypotheses

- State three to five plausible hypotheses when the cause is not already proven. Rank them by evidence, likelihood, and cost to disprove.
- For the highest-ranked hypothesis, design the smallest probe that distinguishes it from at least one alternative.
- Change one variable at a time.
- If three targeted attempts fail, stop patching and revisit architecture, assumptions, or missing context.

### 5. Instrument Deliberately

- Add diagnostics only where they distinguish the active hypotheses.
- Include correlation, state transition, timing, and boundary values as applicable; redact sensitive data.
- Tag temporary instrumentation so it can be found, and remove it after the regression check passes unless it has durable operational value.

### 6. Correct, Defend, And Learn

- Patch the earliest controllable root cause, not only the visible symptom.
- Add validation at meaningful boundaries when bad data could travel farther.
- Add a regression check that fails before and passes after the fix.
- Re-run the original scenario, nearby cases, and broader checks justified by blast radius.
- Record the causal chain, why existing defenses missed it, and the smallest prevention improvement. Avoid a broad post-mortem for a local low-risk defect.

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
