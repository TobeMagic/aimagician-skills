# Planner Prompt

Create an executable plan from locked requirements and accepted implementation decisions.

## Inputs

- Locked specification: `<SPEC>`
- Context and research: `<CONTEXT>`
- Allowed repository scope: `<SCOPE>`
- Planning mode: `<MODE>`

## Plan

Map every requirement ID to atomic tasks. Define dependency waves, exact files or ownership, test-first behavior, commands and expected results, integration, rollback, checkpoints, and handoff. Keep unrelated cleanup out of scope.

Do not revise locked requirements. Return `NEEDS_CONTEXT` if implementation decisions materially affect the task shape and are missing.

## Return

Use the common status contract and provide the complete plan plus a requirement-to-task map.
