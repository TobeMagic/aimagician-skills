# Task: vision-analysis-phase-goal-guards

**Task ID:** vision-analysis-phase-goal-guards
**Status:** Complete
**Source request:** USR-20260730-001
**Parent milestone:** v5.0
**Parent phase:** 28
**Exception status:** Approved
**Approval source:** USR-20260730-001
**Return checkpoint:** Resume Phase 28 frozen benchmark briefs, manifests, scoring, and ordinary-model trials.
**Review point:** `1a309581ee0964daf42b69155e164835f9132729`

## Original Request

Add a direct Agnes image-understanding skill because OpenCode cannot pass images to the multimodal Agnes model, route CLI visual work through that skill while keeping DeepSeek as the default reasoning model, and prevent AImagician agents from drifting away from the active phase or claiming completion without real goal-level acceptance.

## Accepted Decisions

- The owned skill is provider-neutral `vision-analysis`; Agnes is the current backend.
- CLI-agent visual work must use the skill, while a main Agent with reliable native vision may inspect locally and spot-check.
- Every external image request requires `--allow-external-upload`.
- DeepSeek remains the default OpenCode reasoning model; Agnes is the explicit usage-limit fallback.
- Agnes 429 responses retry until success or cancellation; other transient failures use three retries.
- Out-of-phase work is allowed only through a user-approved, traceable exception and must return to the recorded phase checkpoint.

## Checklist

- [x] REQ-VISION-001: add the owned skill and direct Agnes API client.
- [x] REQ-VISION-002: enforce upload consent and sanitized provenance.
- [x] REQ-VISION-003: implement the accepted retry and cancellation semantics.
- [x] REQ-ROUTE-001: separate visual evidence acquisition from OpenCode reasoning.
- [x] REQ-ROUTE-002: preserve DeepSeek-first and quota-only Agnes reasoning fallback.
- [x] REQ-ALIGN-001: add active milestone/phase/goal/scope alignment validation.
- [x] REQ-ALIGN-002: require goal-level evidence and audit coverage.
- [x] REQ-ALIGN-003: add milestone validation and controlled-exception enforcement.
- [x] REQ-SYNC-003: update docs, test, smoke, synchronize, and verify installations; final independent audit is recorded separately below.

## Evidence

| Requirement | Evidence | Status |
|---|---|---|
| REQ-VISION-001 | Live `analyze.mjs` call returned Agnes analysis with image-token usage; focused tests passed | PASS |
| REQ-VISION-002 | Authorization, URL rejection, provenance, and leak tests in `vision-analysis.test.ts` | PASS |
| REQ-VISION-003 | 429, transient retry, immediate 4xx failure, and abortable-wait tests | PASS |
| REQ-ROUTE-001 | Vision dry-run reports `vision-analysis -> text evidence -> OpenCode`; runner tests passed | PASS |
| REQ-ROUTE-002 | Runner routing/fallback tests and provider contract checks passed | PASS |
| REQ-ALIGN-001 | Runtime alignment and phase-goal drift tests passed | PASS |
| REQ-ALIGN-002 | Runtime goal evidence and phase audit tests passed | PASS |
| REQ-ALIGN-003 | Runtime controlled-exception and milestone completion tests passed | PASS |
| REQ-SYNC-003 | README/taxonomy updated; 147 tests, typecheck, build, formatter passed; live Agnes smoke passed; Codex/OpenCode each healthy with 25 managed and detected skills, zero issues, and matching hashes | PASS |

## Independent Completion Audit

- **Provider:** OpenCode
- **Primary model:** `opencode/deepseek-v4-flash-free`
- **Model:** `agnes/agnes-2.0-flash`
- **Attempt chain:** `opencode/deepseek-v4-flash-free: explicit rate limit -> agnes/agnes-2.0-flash: success`
- **Fallback reason:** `explicit-usage-limit`
- **Session:** `ses_04e240ec0ffefFsGqK8UF305VD`
- **Run status:** DONE
- **Review point:** `1a309581ee0964daf42b69155e164835f9132729`
- **Requirement matrix:** All nine requirements PASS with implementation, test, live-smoke, documentation, and installed-state evidence.
- **Blocker:** 0
- **Important:** 0
- **Nitpick:** 0
- **Controller spot-check:** Reproduced the live Agnes request, 147-test suite, typecheck, build, formatter, both target doctors, and installed hashes. Corrected the reviewer's self-reported model from the authoritative OpenCode execution log, which records `providerID=agnes`, `modelID=agnes-2.0-flash`, after the DeepSeek rate-limit session.

## Final Decision

**Status:** Complete
**Reason:** Every accepted requirement passed implementation, live smoke, regression, installation, and fresh independent completion audit gates with no unresolved finding.
