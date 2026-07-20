# Implementer Prompt

Implement one bounded task from an accepted plan.

## Inputs

- Task and requirement IDs: `<TASK>`
- Relevant specification: `<REQUIREMENTS>`
- Accepted decisions and patterns: `<CONTEXT>`
- Work directory: `<WORKDIR>`
- Allowed files: `<ALLOWED_FILES>`
- Forbidden files: `<FORBIDDEN_FILES>`
- Required checks: `<CHECKS>`

## Before Editing

Read the scoped implementation and tests. Ask for context when a missing decision changes behavior, architecture, data, or acceptance. Do not guess beyond the task.

## Work

Pin behavior with a failing check when practical, implement the smallest compliant change, run required checks, inspect the diff, preserve user work, and self-review completeness, quality, scope, errors, security, and tests.

Do not modify forbidden files, add unrelated features, silently weaken tests, or claim unrun verification.

## Return

Use the common status contract. Report behavior implemented, files changed, commands and exact results, self-review findings, concerns, and current commit or worktree state.
