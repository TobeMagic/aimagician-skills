# Agent Role Contract

Use this contract for every delegated role.

## Required Brief

- Objective and role.
- Exact requirements and accepted decisions.
- Relevant context supplied by the controller.
- Allowed and forbidden files, systems, and commands.
- Read-only or write permission.
- Expected checks and evidence.
- Output format and escalation conditions.

Do not ask the agent to rediscover context already known to the controller. Do not grant write permission implicitly.

## Required Status

Return exactly one:

- `DONE`
- `DONE_WITH_CONCERNS`
- `NEEDS_CONTEXT`
- `BLOCKED`

Then report files inspected or changed, commands and results, findings, uncertainty, and next action. Never expose secret values.
