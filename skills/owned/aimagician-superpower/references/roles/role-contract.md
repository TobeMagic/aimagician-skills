# Agent Role Contract

Use this contract for every delegated role.

## Required Brief

- Task ID, objective, role, deliverable, and frozen review point.
- Source of truth, exact requirements, accepted decisions, and known context.
- Required owned skills with reasons; load them before substantive work.
- Allowed and forbidden files, systems, sources, and commands.
- Permission mode, exact write scope, git policy, and child-agent policy.
- Expected checks, evidence, progress events, finding severity, output format, and escalation conditions.

Do not ask the agent to rediscover context already known to the controller. Do not grant write permission implicitly. If a named skill, source, decision, or permission is missing, return `NEEDS_CONTEXT` instead of improvising. Use the full `cli-agent-delegator/references/prompt-contract.md` envelope for OpenCode.

## Required Status

Return exactly one:

- `DONE`
- `DONE_WITH_CONCERNS`
- `NEEDS_CONTEXT`
- `BLOCKED`

Then report files inspected or changed, commands and results, findings, uncertainty, and next action. Never expose secret values.

Review findings use exactly `Blocker`, `Important`, or `Nitpick`. Child agents are forbidden unless explicitly allowed; when allowed, they inherit the complete scope, permission, skill, evidence, and stop contract.
