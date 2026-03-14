---
phase: 03
slug: direct-skill-targets
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 03 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest |
| **Config file** | `vitest.config.ts` |
| **Quick run command** | `npm test -- direct-target` |
| **Full suite command** | `npm test` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm test -- direct-target`
- **After every plan wave:** Run `npm test`
- **Before phase verification:** Run `npm run build` and `npm test`
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | TARG-01 | unit/integration | `npm test -- direct-target-sync` | no | pending |
| 03-02-01 | 02 | 2 | TARG-02 | integration | `npm test -- direct-target-sync` | no | pending |
| 03-02-02 | 02 | 2 | TARG-03 | integration | `npm test -- direct-target-sync` | no | pending |
| 03-03-01 | 03 | 3 | INST-04 | integration | `npm test -- bootstrap-engine` | no | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/bootstrap/direct-target-sync.test.ts` - fake-home integration coverage for copy and prune behavior
- [ ] `src/bootstrap/target-homes.ts` - centralized target-home resolution
- [ ] `src/bootstrap/direct-target-sync.ts` - apply logic for managed directory sync

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Installed skills appear in the real CLI's list command | INST-04 | Automated tests should not mutate the real user home during validation | Run bootstrap against the real user home, then use each CLI's skill listing command to confirm visibility |

---

## Validation Sign-Off

- [ ] All tasks have automated verification
- [ ] Sampling continuity is maintained across all three plans
- [ ] Wave 0 dependencies exist before direct apply logic lands
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
