# Task: vision-analysis-phase-goal-guards

**Task ID:** vision-analysis-phase-goal-guards
**Status:** Ready for independent audit
**Source request:** USR-20260730-001
**Parent milestone:** v5.0
**Parent phase:** 28
**Exception status:** Approved
**Approval source:** USR-20260730-001
**Return checkpoint:** Resume Phase 28 frozen benchmark briefs, manifests, scoring, and ordinary-model trials.
**Review point:** NOT_RUN

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
- [ ] REQ-SYNC-003: update docs, test, smoke, synchronize, audit, and verify installations.

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
| REQ-SYNC-003 | README/taxonomy updated; 147 tests, typecheck, build, formatter passed; Codex/OpenCode each healthy with 25 managed skills and matching hashes; independent audit pending | NOT_RUN |

## Independent Completion Audit

- **Provider:** OpenCode
- **Primary model:** NOT_RUN
- **Model:** NOT_RUN
- **Attempt chain:** NOT_RUN
- **Fallback reason:** NOT_RUN
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
**Reason:** Implementation, live visual smoke testing, full verification, and synchronization passed. A fresh independent completion audit remains required.
