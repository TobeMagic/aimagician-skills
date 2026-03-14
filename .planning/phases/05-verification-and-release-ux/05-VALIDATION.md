---
phase: 5
slug: verification-and-release-ux
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-14
---

# Phase 5 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest |
| **Config file** | `tsconfig.json` |
| **Quick run command** | `npm test -- cli` |
| **Full suite command** | `npm test` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm test -- cli`
- **After every plan wave:** Run `npm test`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 5-01-01 | 01 | 1 | VER-01 | integration | `npm test -- cli` | yes | pending |
| 5-01-02 | 01 | 1 | VER-03 | integration | `npm test -- cli` | yes | pending |
| 5-02-01 | 02 | 2 | VER-02 | integration | `npm test -- bootstrap` | yes | pending |
| 5-02-02 | 02 | 2 | VER-01 | smoke | `npm test -- bootstrap-smoke` | yes | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [x] `tests/cli/bootstrap-command.test.ts` - existing CLI command and help coverage
- [x] `tests/bootstrap/bootstrap-smoke.test.ts` - existing compiled CLI smoke coverage
- [x] `tests/bootstrap/direct-target-sync.test.ts` - existing fake-home install coverage

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real-world operator confirmation that listed assets align with what each target CLI loads | VER-01 | automated tests verify filesystem state, not every live target UI | Run `aimagician-skills list`, compare output with the target CLI's visible loaded assets, and confirm the mapping makes sense |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
