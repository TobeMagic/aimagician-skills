# Domain Gates

Use this module to apply specialized quality gates without leaving the main workflow.

## Code Quality

- Read before editing.
- Prefer simple local patterns.
- Add focused tests for changed behavior.
- Keep changes close to the requested surface.
- Verify imports, types, build, and runtime behavior as appropriate.
- Review for security, data handling, error paths, and compatibility.

## Debugging

1. Reproduce the failure.
2. Isolate the smallest failing behavior.
3. Trace the cause with evidence.
4. Patch the cause, not only the symptom.
5. Add a regression check.
6. Re-run the failing scenario and nearby checks.

## UI And Frontend

- Match the product domain and existing design system.
- Check accessibility, keyboard flow, focus states, contrast, and text overflow.
- Verify desktop and mobile layouts.
- Use screenshots or browser probes for meaningful visual changes.
- Use the dedicated interface workflow when brand, motion, metadata, or polish is central.

## Documents And Generated Assets

- Validate generated files by opening, extracting, or inspecting them with an appropriate tool.
- Preserve templates and styles when editing existing documents.
- Avoid committing binary churn unless the deliverable requires it.
- Record the exact generated output paths.

## Secrets And Environment

- Never hardcode credentials into source, docs, screenshots, or logs.
- Inventory environment variables and secret names separately from secret values.
- Scan likely caches and generated artifacts when handling credentials.
- Prefer controlled local vault or env files that are ignored by git.

## Git, PR, And Review

- Check dirty state before edits.
- Do not revert user work.
- Keep commits scoped when the user asks for a commit.
- For review tasks, lead with findings and file/line references.
- For PR tasks, verify CI, reviewer feedback, and linked work items when available.

## Operations

- Treat cloud, production, data, and install paths as higher risk.
- Prefer read-only inspection before mutation.
- Confirm target scope and rollback path before changing shared resources.
- Record commands, outputs, and affected resources.
