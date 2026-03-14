---
phase: 4
slug: gemini-and-plugins
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-14
---

# Phase 4 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest |
| **Config file** | `tsconfig.json` |
| **Quick run command** | `npm test -- direct-target-sync` |
| **Full suite command** | `npm test` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm test -- direct-target-sync`
- **After every plan wave:** Run `npm test`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | TARG-04 | integration | `npm test -- direct-target-sync` | yes | pending |
| 4-02-01 | 02 | 2 | PLUG-01 | unit | `npm test -- target-mapping` | yes | pending |
| 4-02-02 | 02 | 2 | PLUG-03 | integration | `npm test -- bootstrap` | yes | pending |
| 4-03-01 | 03 | 2 | PLUG-02 | integration | `npm test -- bootstrap` | yes | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [x] `tests/bootstrap/direct-target-sync.test.ts` - existing fake-home target install coverage
- [x] `tests/bootstrap/bootstrap-engine.test.ts` - existing bootstrap integration coverage
- [x] `tests/catalog/target-mapping.test.ts` - existing target normalization coverage

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real CLI discovery of generated Gemini extensions | TARG-04 | automated tests can verify files but not the live Gemini CLI UI on this machine | Run bootstrap against a real user profile, start Gemini CLI, and confirm extension-provided capability is visible |
| Claude plugin consent flow remains explicit | PLUG-03 | the project should not auto-consent on behalf of the user | Run bootstrap with a Claude-targeted plugin asset and confirm the report explains why installation was skipped |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
