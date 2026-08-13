---
name: webapp-testing
description: Use when browser automation or local web app verification is needed, including page smoke tests, forms, screenshots, console/network checks, responsive checks, and regression probes.
category: build
subcategory: browser-testing
tags:
  - playwright
  - webapp
  - verification
compatibility:
  tools: [bash, playwright, browser]
  requires: A reachable URL, local dev server, or static HTML entrypoint
---

# Webapp Testing

Use this skill whenever UI behavior must be proven in a browser.

## Default Workflow

1. Find how the app runs.
   - Read package scripts and framework config.
   - Reuse an existing dev server if one is already running.
   - Start a dev server when needed and keep the URL in the final report.
   - If the repository provides a `with_server.py`-style lifecycle helper, run `with_server.py --help` (or its documented equivalent) first and treat it as a black-box wrapper around the dev server lifecycle.
2. Create a focused Playwright probe.
   - Put temporary scripts under `/tmp` unless the repo already has a test convention.
   - Prefer small Python or TypeScript Playwright scripts that can be re-run from the shell.
   - Check console errors, failed network requests, visible text, form behavior, and screenshots.
3. Exercise realistic user paths.
   - Prefer role/text selectors over brittle DOM paths.
   - Test both success and important failure states.
   - For dynamic apps, wait for `networkidle` or a stable visible state before asserting content.
4. Verify responsive layout.
   - At minimum use one desktop and one mobile viewport for UI changes.
5. Report evidence.
   - Include command, URL, and result.
   - Mention screenshots or traces when captured.

## Reconnaissance-Then-Action

Use this order when the page behavior is unknown:

1. Open the page and capture title, URL, key visible text, console errors, and failed network requests.
2. Inspect accessible roles or stable labels before choosing selectors.
3. Perform the smallest user path that proves the requested behavior.
4. Add screenshots only where visual layout, canvas/media rendering, or responsive behavior matters.
5. Convert the probe into a committed test only when it belongs in the repo's test suite.

## Common Checks

- page renders nonblank content;
- primary workflow can be completed;
- navigation state is correct;
- buttons and inputs are reachable by keyboard;
- no severe console errors;
- text does not overlap or overflow;
- canvas/WebGL/media content is visible when relevant.

## Execution Contract

### 1. Establish A Stable Test Surface

Record the URL, startup command or existing server, target user path, and deterministic readiness signal before probing. Use a loopback server for modules or assets that cannot run from `file://`.

### 2. Prove Behavior Before Pixels

Exercise the target path with accessible selectors, then assert the relevant user-visible state, console errors, failed requests, and keyboard path. Capture screenshots only for visual claims that cannot be asserted semantically.

### 3. Compare The Required Geometry

Run the same route at a desktop and mobile viewport, inspect overflow or overlap, and retain the smallest useful artifact path for review.

**CHECKPOINT:** Do not report a browser result until the URL is reachable, a target state is stable, and console/network findings are classified as expected, fixed, or unresolved.

**CHECKPOINT:** Confirm the browser, viewport, selector, user path, and assertion before creating a screenshot or trace; a capture without a bound behavior is diagnostic only.

**CHECKPOINT:** If local tooling cannot reproduce the requested state, stop at the highest verified layer and report the blocked derivative rather than changing the acceptance claim.

```text
URL -> stable readiness -> user action -> observable state -> console/network -> responsive evidence
```

## Failure Handling

| Trigger | First response | Fallback |
|---|---|---|
| Server cannot start or target URL is unreachable | Inspect the documented startup command and the first actionable error | Test a static entrypoint or report `NOT_RUN` with the blocking command; do not guess browser behavior |
| Selector or readiness signal is unstable | Inspect accessible roles and app-specific loaded state | Replace brittle waits with a semantic locator or record the unstable state as a product defect |
| Console, network, visual, or responsive check fails | Preserve the smallest reproducible route and capture focused evidence | Return a failure report with screenshot/trace path; do not hide it behind a passing HTTP response |

## Guardrails

- Do not rely on a screenshot alone when behavior matters.
- Do not leave background dev server sessions running unless the user needs them.
- Do not commit temporary `/tmp` probes.
- Do not use fixed sleeps when a Playwright locator, load state, `networkidle`, or app-specific ready signal is available.
- Do not treat a passing HTTP status as proof that the UI rendered correctly.

## Output Contract

For each run, provide:

- URL tested;
- command or script used;
- pass/fail result;
- important console/network findings;
- screenshot path only when it is useful.

Read `references/browser-evidence-contract.md` when the test needs a durable browser-evidence record or a handoff to another agent.
