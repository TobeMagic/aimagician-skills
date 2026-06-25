# Verification And UAT

Use this module before claiming completion and whenever work changes behavior, installation state, documents, UI, integrations, or data handling.

## Verification Order

1. Run the narrowest check that proves the changed behavior.
2. Add or update regression tests when behavior was previously unpinned.
3. Broaden to typecheck, lint, build, integration, browser, document, or smoke checks based on blast radius.
4. Inspect generated artifacts directly when tests do not cover them.
5. Record skipped checks and why they were skipped.

## Evidence Types

Completion can be proven by:

- passing command output;
- inspected generated files;
- browser screenshots or console/network checks;
- document open/extract validation;
- API response checks;
- manual acceptance scenarios;
- before/after comparison;
- security or secret scan output when data handling is involved.

## UAT Scenarios

For user-facing behavior, define acceptance scenarios:

- scenario name;
- starting state;
- user action;
- expected visible result;
- data or side effect expected;
- pass/fail result;
- evidence path or command.

Keep UAT practical. A few high-signal scenarios are better than a broad checklist nobody runs.

## Regression Review

Before closure, check:

- requirements satisfied;
- non-goals respected;
- no accidental capability loss;
- no stale TODOs or placeholders;
- no broken imports or paths;
- no generated noise committed unintentionally;
- installation or target paths still clean when relevant;
- known limitations documented.

## Failed Verification

If a check fails:

1. Preserve the failure output.
2. Classify it as implementation bug, test bug, environment issue, flaky check, or unrelated pre-existing failure.
3. Fix only the relevant scope.
4. Re-run the narrow check.
5. Broaden again only after the narrow check passes.
