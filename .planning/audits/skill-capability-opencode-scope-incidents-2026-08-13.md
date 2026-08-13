# OpenCode Scope Incidents: 2026-08-13

## Context

Two independent, read-only Skill audits were dispatched through
`cli-agent-delegator/scripts/opencode-run.mjs` with explicit allowed paths and
forbidden actions. Both used `opencode/deepseek-v4-flash-free` with
`agnes/agnes-2.0-flash` declared only as quota fallback.

## Observed Incidents

| Session | Contract | First invalid action | Result |
|---|---|---|---|
| `ses_006af113cffeOakV7dXcHubDuI` | 19-Skill frozen audit | Read the oversized request ledger then failed to produce a final report | Invalid: no completion output |
| `ses_006ac3720ffeUEp7lqkc7XNGIH` | two-Skill design audit | Ran `skills/owned/**/SKILL.md` glob plus directory and Git scans outside listed paths | Stopped by controller; invalid for evidence |

No writes, commits, pushes, installs, secret reads, or external calls were
observed. The controller terminated both processes after scope drift or missing
final output.

## Implication

The current delegate contract can require a scope manifest, detect a visible
violation, invalidate the handoff, and re-route work. It is not an OpenCode
tool-level sandbox while the user's global `"*": "allow"` permission remains
active. No completion, behavioral-effectiveness, or independent-audit claim
may rely on either session.

## Required Follow-up

Implement a runner-level isolated OpenCode configuration or permission adapter
before treating unattended OpenCode audits as controlled behavioral evidence.
