# Task: cli-agent-dynamic-routing

**Task ID:** cli-agent-dynamic-routing
**Status:** Complete
**Source request:** USR-20260729-001
**Review point:** HEAD d1eb7acf0bd5a70bf51d8dc40a2c869e135acb27 plus the current working tree after Codex/OpenCode synchronization

## Original Request

Make OpenCode the default worker for eligible small, simple, short tasks; keep DeepSeek as the default for every non-visual task; use Agnes for visual work or explicit usage-limit fallback; dynamically inspect available free models without maintaining a quality ranking; and remove the Agnes-only completion-audit restriction without weakening independent requirement coverage.

## Accepted Decisions

- The controller retains requirements, architecture, risk acceptance, integration, validation, and final completion responsibility.
- Eligible bounded writes use a clean isolated worktree and default to no commit.
- DeepSeek absence lets the controller choose another available free model.
- Visual work prefers Agnes; verified vision-capable alternatives are allowed when Agnes is unavailable.
- Only explicit usage, quota, or rate-limit failures automatically switch to Agnes.
- Legacy Agnes audit records remain valid.
- Active workers are observed by events and process state, not a fixed wall-clock timeout.

## Checklist

- [x] REQ-DELEGATE-001: strengthen the trigger and eligibility rules for default short-task delegation.
- [x] REQ-DELEGATE-002: add reusable bounded task recipes and preserve isolated-write safety.
- [x] REQ-MODEL-001: enforce DeepSeek-first routing for non-visual work.
- [x] REQ-MODEL-002: expose free candidates for controller choice when DeepSeek is absent.
- [x] REQ-MODEL-003: route visual work through Agnes or a verified vision model.
- [x] REQ-MODEL-004: classify failures and limit automatic Agnes fallback to quota events.
- [x] REQ-MODEL-005: add cached verbose model discovery and capability overrides.
- [x] REQ-AUDIT-004: make completion audit validation model-neutral without weakening evidence gates.
- [x] REQ-AUDIT-005: retain compatibility with historical Agnes audit records.
- [x] REQ-RUNTIME-001: provide current OpenCode syntax, progress streaming, event-based waiting, and attempt provenance.
- [x] REQ-SYNC-002: run tests, independent audit, bootstrap, list, and doctor verification.

## Evidence

| Requirement | Evidence | Status |
|---|---|---|
| REQ-DELEGATE-001 | `cli-agent-delegator/SKILL.md` Default Short-Task Gate; trigger and eval regression tests | PASS |
| REQ-DELEGATE-002 | `quick-task-recipes.md`; isolated-worktree and no-commit contracts; focused skill tests | PASS |
| REQ-MODEL-001 | `opencode-run.mjs` text default; dry-run selected DeepSeek; runner tests | PASS |
| REQ-MODEL-002 | `selection-required` route and live free candidates; runner tests | PASS |
| REQ-MODEL-003 | Agnes vision default, image-capability filtering, and verified override; dry-run and tests | PASS |
| REQ-MODEL-004 | Failure classifier and quota-only fallback; real DeepSeek rate-limit to Agnes run; runner tests | PASS |
| REQ-MODEL-005 | 24-hour verbose inventory cache, refresh flag, and capability-source evidence; dry-run and tests | PASS |
| REQ-AUDIT-004 | Model-neutral workflow validator, templates, docs, and new-record tests | PASS |
| REQ-AUDIT-005 | Legacy `Agnes Completion Audit` compatibility path and regression tests | PASS |
| REQ-RUNTIME-001 | Positional prompt command, attached streaming, process-close waiting, and structured attempt chain | PASS |
| REQ-SYNC-002 | 135/135 full tests; 24-skill bootstrap to Codex/OpenCode; OpenCode and controller list/doctor checks healthy | PASS |

## Independent Completion Audit

- **Provider:** OpenCode
- **Primary model:** `opencode/deepseek-v4-flash-free`
- **Model:** `agnes/agnes-2.0-flash`
- **Attempt chain:** `opencode/deepseek-v4-flash-free: usage-limit (ses_0517e4913ffed8EmBh8rl5flLg) -> agnes/agnes-2.0-flash: success (ses_0517e25f7ffedu0ygnIAJx3HPt)`
- **Fallback reason:** `explicit-usage-limit`
- **Session:** `ses_0517e25f7ffedu0ygnIAJx3HPt`
- **Run status:** DONE
- **Review point:** HEAD d1eb7acf0bd5a70bf51d8dc40a2c869e135acb27 plus the complete working tree after synchronization
- **Requirement matrix:** PASS
- **Blocker:** 0
- **Important:** 0
- **Nitpick:** 0
- **Controller spot-check:** Re-ran Agent list/doctor; both targets healthy with 24 managed/detected and 0 issues; matched repository and installed hashes for both changed skills; inspected default routes, fallback classifier, legacy audit path, and event-driven child-process logic.

## Final Decision

**Status:** Complete
**Reason:** All 11 accepted requirements have passing implementation and runtime evidence; Codex/OpenCode synchronization is healthy; the fresh independent audit found no Blocker, Important, FAIL, or NOT_RUN.
