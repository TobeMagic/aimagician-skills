# Task: Agent-first Skillbird, System Prompt Skill, and Completion Audit

**Task ID:** agent-cli-system-prompt-audit
**Status:** In progress
**Source request:** USR-20260728-001
**Review point:** `feat/agent-cli-system-prompt-audit`

## Accepted Decisions

- `--agent` is a global compatibility layer; existing `--json` and human/TUI behavior remain supported.
- Agent writes preview by default and require `--yes` to apply.
- Idempotent skips return success; required-target partial failures return non-zero.
- Completion audits use `agnes/agnes-2.0-flash` as the primary model.
- Upstream source repositories are local ignored evidence, not runtime Skill content.

## Checklist

- [x] REQ-PROMPT-001/002: implement and test `system-prompt-engineering`.
- [x] REQ-AGENT-001/002/003/004: implement and test the Agent CLI contract.
- [ ] REQ-AUDIT-001/002/003: implement task/phase traceability and Agnes gates.
- [x] REQ-SYNC-001: update README, build, test, sync, list, and doctor Codex/OpenCode.
- [ ] REQ-GIT-001: run fresh Agnes audit, resolve findings, commit, merge, and push.

## Evidence

| Requirement | Evidence | Status |
|---|---|---|
| REQ-PROMPT-001/002 | `tests/skills/system-prompt-engineering.test.ts`; `node scripts/audit-system-prompt-upstreams.mjs` reports 15 capabilities, zero delta | PASS |
| REQ-AGENT-001/002/003/004 | CLI and manager tests; live `--agent capabilities`; bootstrap preview; structured usage error | PASS |
| REQ-AUDIT-001/002/003 | Pending | NOT_RUN |
| REQ-SYNC-001 | `npm run build`; `npm test` 23 files/128 tests; formatter check; Codex/OpenCode bootstrap and doctor 24/24 healthy | PASS |
| REQ-GIT-001 | Pending | NOT_RUN |

## Agnes Completion Audit

- **Provider:** OpenCode
- **Model:** `agnes/agnes-2.0-flash`
- **Session:** NOT_RUN
- **Run status:** NOT_RUN
- **Review point:** NOT_RUN
- **Requirement matrix:** NOT_RUN
- **Blocker:** NOT_RUN
- **Important:** NOT_RUN
- **Nitpick:** NOT_RUN
- **Controller spot-check:** NOT_RUN

## Final Decision

**Status:** In progress
**Reason:** Implementation and independent audit are pending.
