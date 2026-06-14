---
name: webapp-testing
description: Use when browser automation or local web app verification is needed, including page smoke tests, forms, screenshots, console/network checks, responsive checks, and regression probes.
category: build
subcategory: browser-testing
tags:
  - playwright
  - webapp
  - verification
metadata:
  merged_from:
    - webapp-testing
    - playwright-skill
compatibility:
  tools: [bash, playwright, browser]
  requires: A reachable URL, local dev server, or static HTML entrypoint
---

# Webapp Testing

Use this skill whenever UI behavior must be proven in a browser.

## Source Decisions

- Claude's `webapp-testing` provides the black-box local server pattern and Python Playwright probe style.
- The existing Playwright skill contributes broad browser verification, screenshot, viewport, and console/network checks.
- Project-native tests are preferred when the repo already has them; temporary probes stay under `/tmp`.

## Default Workflow

1. Find how the app runs.
   - Read package scripts and framework config.
   - Reuse an existing dev server if one is already running.
   - Start a dev server when needed and keep the URL in the final report.
   - If using a helper such as `scripts/with_server.py`, run `with_server.py --help` first and treat it as a black-box wrapper around the dev server lifecycle.
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
