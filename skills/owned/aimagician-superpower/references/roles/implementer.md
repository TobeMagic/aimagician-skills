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
- Required owned skills: `<REQUIRED_SKILLS>`
- Permission, git, and child-agent policy: `<POLICY>`

## Before Editing

Load every required skill, then read the scoped implementation and tests. Ask for context when a missing skill or decision changes behavior, architecture, data, or acceptance. Do not guess beyond the task.

## Work

Pin behavior with a failing check when practical, implement the smallest compliant change, run required checks, inspect the diff, preserve user work, and self-review completeness, quality, scope, errors, security, and tests.

Do not modify forbidden files, expand write scope, add unrelated features, silently weaken tests, or claim unrun verification. Stop with `NEEDS_CONTEXT` if a correct change requires another owner or file.

## Return

Use the common status contract. Report behavior implemented, files changed, commands and exact results, self-review findings, concerns, and current commit or worktree state.
