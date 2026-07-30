# Task: local-first-delivery-planning-storage

**Task ID:** local-first-delivery-planning-storage
**Status:** Complete
**Source request:** USR-20260730-002
**Parent milestone:** v5.0
**Parent phase:** 28
**Exception status:** Approved
**Approval source:** USR-20260730-002
**Return checkpoint:** Resume Phase 28 frozen benchmark briefs, manifests, scoring, and ordinary-model trials.
**Review point:** `3fa59c4bc91b2e40d694983c2ae3b5afbd7449ae`

## Original Request

Implement the accepted local-first delivery plan: map complete local context, add LOCAL/CI/PREVIEW/POSTMERGE gates, preserve `.planning` as the first project source of truth, support one local-private planning store shared across worktrees, freeze OpenCode review points, detect managed-install content drift, add PR CI, synchronize Codex/OpenCode, and complete an independent requirement audit.

## Accepted Decisions

- Fast-forward `master` to audited baseline `0f8216b`, then implement in an isolated branch.
- A deployable phase or task is complete only after postmerge online evidence and a fresh independent audit.
- Postmerge failure reopens work and uses project-owned recovery policy; no generic automatic rollback.
- `.planning` supports tracked and local-private modes. Only local-private mode shares one Git-common-dir store across worktrees.
- Local-private mode uses `.git/info/exclude`, short locks, revisions, and no automatic backup.
- Planning evidence remains project-first; LLM wiki receives only macro activity records.
- PR CI is non-deploying. Existing tag-only publishing remains intact.

## Checklist

- [x] REQ-LOCAL-001: Add full-chain context mapping and the four-stage delivery capability.
- [x] REQ-GATE-001: Add executable premerge/postmerge gates and completion semantics.
- [x] REQ-RECOVERY-001: Reopen failed postmerge work and require controlled recovery.
- [x] REQ-PLANNING-001: Support tracked and local-private planning modes.
- [x] REQ-WORKTREE-001: Share local-private planning safely across worktrees.
- [x] REQ-AUDIT-006: Freeze and verify OpenCode review points.
- [x] REQ-SYNC-004: Detect managed source/install content drift.
- [x] REQ-CI-001: Add PR CI without changing tag-only release behavior.
- [x] REQ-DOC-002: Update docs/evals/tests and synchronize Codex/OpenCode.

## Evidence

| Requirement | Evidence | Status |
|---|---|---|
| REQ-LOCAL-001 | Capability module, context/change/validation templates, README, and eval scenarios | PASS |
| REQ-GATE-001 | `workflow.mjs` premerge/postmerge validation plus 17 focused runtime tests | PASS |
| REQ-RECOVERY-001 | Delivery contract recovery findings and `local-first-delivery.md` failure protocol | PASS |
| REQ-PLANNING-001 | `workflow.mjs planning` tracked/local-private init, status, attach, lock, and unlock | PASS |
| REQ-WORKTREE-001 | Shared Git-common-dir test and automatic parallel-worktree attach test | PASS |
| REQ-AUDIT-006 | `opencode-run.mjs` frozen ref/worktree binding and drift test | PASS |
| REQ-SYNC-004 | Manifest v4 source digest plus bootstrap and CLI doctor drift tests | PASS |
| REQ-CI-001 | `.github/workflows/ci.yml`; tag-only `.github/workflows/release.yml` unchanged | PASS |
| REQ-DOC-002 | README/audit docs/evals; 153 tests, typecheck, build, pack; Codex/OpenCode bootstrap and healthy doctor | PASS |

## Delivery Contract

- **Delivery contract:** v1
- **Delivery class:** Non-deployable
- **Context coverage:** PASS
- **Local verification:** PASS
- **CI verification:** PASS
- **Preview verification:** N/A
- **Online-only exceptions:** N/A
- **Artifact provenance:** N/A
- **Premerge decision:** MERGE_READY
- **Implementation merge SHA:** N/A
- **Postmerge verification:** N/A
- **Deployed artifact match:** N/A
- **Provenance exception:** NONE
- **Recovery status:** NOT_REQUIRED
- **Postmerge decision:** N/A

This task changes repository source and local managed installations. Publishing an npm release or deploying a production service is outside the accepted scope, so the delivery is non-deployable; pull-request CI remains required before merge.

## Independent Completion Audit

- **Provider:** OpenCode
- **Primary model:** `opencode/deepseek-v4-flash-free`
- **Model:** `agnes/agnes-2.0-flash`
- **Attempt chain:** DeepSeek `ses_04d04651cffea4rS1vx2s3txmi` (`usage-limit`); Agnes `ses_04d043a5dffeITA4xQWE7PeSBz` (`usage-limit`); Agnes `ses_04d00a44affeG9dUWElWmMYmZm` (`usage-limit`); Agnes `ses_04cfd5ba6ffekK7lrnJu0Jn6oe` (`success`)
- **Fallback reason:** `explicit-usage-limit`
- **Session:** `ses_04cfd5ba6ffekK7lrnJu0Jn6oe`
- **Run status:** DONE
- **Review point:** commit `3fa59c4bc91b2e40d694983c2ae3b5afbd7449ae`; stable fingerprint `0283e44fd30aa3763f8a58078bd653dea86713dad7dcd371b0a33be8199272c0`
- **Requirement matrix:** 9/9 PASS (`REQ-LOCAL-001`, `REQ-GATE-001`, `REQ-RECOVERY-001`, `REQ-PLANNING-001`, `REQ-WORKTREE-001`, `REQ-AUDIT-006`, `REQ-SYNC-004`, `REQ-CI-001`, `REQ-DOC-002`)
- **Blocker:** 0
- **Important:** 0
- **Nitpick:** 0
- **Controller spot-check:** PASS. Verified `validateDeliveryStage`, `validateTaskDelivery`, and `validatePhaseDelivery` in `workflow.mjs`; `prepareFrozenReview` and `worktreeFingerprint` in `opencode-run.mjs`; manifest v4 `sourcePath`/`sourceDigest` and doctor drift detection in `src/bootstrap` and `src/inspection`; focused tests for delivery gates, shared planning, frozen review, and content drift; exact-head PR CI; and tag-only release triggers. Rejected an earlier audit that violated `WRITE_SCOPE: NONE` by writing `/tmp/audit_report.md`; the accepted fresh audit was strictly read-only and the unauthorized artifact was removed.

## Final Decision

**Status:** Complete
**Reason:** All nine requirements have concrete PASS evidence; 153 local tests, typecheck, build, and pack smoke passed; exact-head PR CI passed; Codex/OpenCode synchronization and doctor checks passed; and a fresh frozen OpenCode audit returned 9/9 PASS with zero findings under a stable review fingerprint.
