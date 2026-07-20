# Phase 22 Validation: Baseline and Safety

**Status:** Complete
**Linux/fake-COM evidence:** Passed
**Real Windows evidence:** Passed twice consecutively

## Recorded Evidence

| Slice | Commits / harness | Fresh recorded result | Review |
|---|---|---|---|
| Pure safety primitives | `35462d1` | 35 focused tests passed | Final compliant after Minor remediation |
| Strict dry-run / result routing | `77c172e`, `97fcc2a` | 55 focused tests passed | No unresolved finding |
| COM lifecycle / terminal inspection / guards | `0a8c4e8`, `4ed65d9` | 72 focused tests passed | No unresolved finding |
| Transactional candidate save | `6f9d749`, `fde2d11` | 96 focused tests passed | No unresolved finding |
| Real COM remediation | `a54aac6`, `04d66db`, `2890ae7`, `cd20cca` | 105 Phase 22 tests passed | Initial P1/P2/P3 findings remediated; final independent review ✅ |
| Native Windows PowerPoint | `tests/window_pptx/windows_phase22_uat.py` | Two runs × 13/13 passed, cleanup passed | See `22-WINDOWS-UAT.md` |

## Real Windows Matrix

- [x] Native Windows Python, pywin32, and `PowerPoint.Application` registration.
- [x] Owned isolated cleanup and attached-session preservation.
- [x] Exact `AutomationSecurity` disable/restore after success and injected failure.
- [x] Strict dry-run with filesystem/network/COM/mutation sentinels.
- [x] Registry-only terminal add-in and plugin inspection without PowerPoint startup.
- [x] Disposable `.pptx` and `.pptm` candidate save, package validation, reopen, promotion, and edit round trip.
- [x] 16:9, 4:3, and portrait export geometry.
- [x] Windows paths containing spaces and Chinese characters.
- [x] Invalid extension, staging conflict, same path, source lock, and injected promotion failure.
- [x] Pre/post SHA-256 source equality.
- [x] PPTX success plus injected PDF promotion failure with existing PDF preservation.
- [x] UTF-8 single-JSON evidence, disposable-root cleanup, and no process residue.

## Exit Criteria

1. Focused tests, Python compilation, CLI routing, and diff checks pass. **Met.**
2. Commands, environment, cases, outputs, hashes, and results are recorded. **Met.**
3. Strict dry-run demonstrates zero side effects. **Met.**
4. Source/output/staging guards reject before COM or write. **Met.**
5. Attached preservation and owned cleanup are observed in real PowerPoint. **Met.**
6. Macro security is forced and restored exactly. **Met.**
7. PPTX/PPTM package, reopen, promotion, suffix, and editability checks pass. **Met.**
8. Sources remain unchanged in success and failure cases. **Met.**
9. No unresolved Critical or Important review finding remains. **Met.**
10. `V5-SAFE-01` through `V5-SAFE-08` have fresh evidence. **Met.**

## Verdict

**Phase 22 is complete.** Phase 23 is unblocked. v5.0 remains active and unshipped until phases 23–29 and all customer-delivery gates pass.
