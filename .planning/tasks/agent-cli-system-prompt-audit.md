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
- [x] REQ-AUDIT-001/002/003: implement task/phase traceability and Agnes gates.
- [x] REQ-SYNC-001: update README, build, test, sync, list, and doctor Codex/OpenCode.
- [ ] REQ-GIT-001: run fresh Agnes audit, resolve findings, commit, merge, and push.

## Evidence

| Requirement | Evidence | Status |
|---|---|---|
| REQ-PROMPT-001/002 | `tests/skills/system-prompt-engineering.test.ts`; `node scripts/audit-system-prompt-upstreams.mjs` reports 15 capabilities, zero delta | PASS |
| REQ-AGENT-001/002/003/004 | CLI and manager tests; live `--agent capabilities`; bootstrap preview; structured usage error | PASS |
| REQ-AUDIT-001/002/003 | Runtime tests; workflow task/phase validators; fresh Agnes session `ses_057ceb4beffeTKW3y9IQ3ApLva`; controller spot-checks below | PASS |
| REQ-SYNC-001 | `npm run build`; `npm test` 23 files/128 tests; formatter check; Codex/OpenCode bootstrap and doctor 24/24 healthy | PASS |
| REQ-GIT-001 | Pending | NOT_RUN |

## Agnes Completion Audit

- **Provider:** OpenCode
- **Model:** `agnes/agnes-2.0-flash`
- **Session:** `ses_057ceb4beffeTKW3y9IQ3ApLva`
- **Run status:** PASS
- **Review point:** `5cda3935173138701a197a567b97624f3cf60272`
- **Requirement matrix:** REQ-AGENT-001..004 PASS; REQ-PROMPT-001..002 PASS; REQ-AUDIT-001..003 PASS; REQ-SYNC-001 PASS; REQ-GIT-001 expected post-audit sequencing
- **Blocker:** 0
- **Important:** 0
- **Nitpick:** 0
- **Controller spot-check:** Reproduced 23 files/128 tests, build, formatter, capabilities and preview JSON, exit-code behavior, upstream ignore/baseline, workflow gates, and Codex/OpenCode 24/24 doctor health. Corrected three auditor reporting errors: the exact model ID is `agnes/agnes-2.0-flash`, the session is the ID above, and the CLI test path ends in `.ts`, not `.py`.

## Final Decision

**Status:** Audit passed; integration pending
**Reason:** All implementation requirements pass with no Blocker or Important finding. Merge and push remain intentionally open under REQ-GIT-001.
