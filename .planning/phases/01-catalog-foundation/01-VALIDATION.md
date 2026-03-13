---
phase: 01
slug: catalog-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 01 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest |
| **Config file** | `vitest.config.ts` (to be created in Wave 0 if missing) |
| **Quick run command** | `npm test -- --runInBand schema` |
| **Full suite command** | `npm test` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm test -- --runInBand schema`
- **After every plan wave:** Run `npm test`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 0 | REPO-01 | unit | `npm test -- --runInBand schema` | no | pending |
| 01-02-01 | 02 | 1 | SRC-01 | unit | `npm test -- --runInBand schema` | no | pending |
| 01-03-01 | 03 | 1 | SRC-04 | integration | `npm test` | no | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `package.json` - baseline scripts for `test`, `build`, and `lint` if missing
- [ ] `vitest.config.ts` - Vitest baseline configuration
- [ ] `tests/catalog/` - schema and fixture tests for catalog parsing
- [ ] `tests/fixtures/` - owned-skill and catalog directory fixtures

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Directory conventions are readable to the maintainer | REPO-01 | Human judgment on repository ergonomics | Review generated repository structure and confirm it matches the locked decisions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
