---
phase: 02
slug: bootstrap-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 02 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest |
| **Config file** | `vitest.config.ts` |
| **Quick run command** | `npm test -- bootstrap` |
| **Full suite command** | `npm test` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm test -- bootstrap`
- **After every plan wave:** Run `npm test`
- **Before phase verification:** Run `npm run build` and `npm test`
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | INST-05 | unit | `npm test -- bootstrap-command` | no | pending |
| 02-02-01 | 02 | 2 | INST-02 | integration | `npm test -- bootstrap-engine` | no | pending |
| 02-03-01 | 03 | 3 | INST-01 | smoke | `npm test -- bootstrap-smoke` | no | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/cli/` - CLI parser and command UX tests
- [ ] `tests/bootstrap/` - bootstrap engine and manifest tests
- [ ] `src/shared/platform.ts` - cross-platform user path resolution

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fresh-machine bootstrap output feels understandable | INST-01 | Output clarity is partly subjective | Run `aimagician-skills bootstrap --dry-run` and review the report format |

---

## Validation Sign-Off

- [ ] All tasks have automated verification
- [ ] Sampling continuity is maintained across all three plans
- [ ] Wave 0 dependencies exist before engine logic lands
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
