# Phase 22 Validation: Baseline and Safety

**Status:** Active / Incomplete
**Linux/fake-COM evidence:** Available
**Real Windows evidence:** Pending

## Recorded Focused Evidence

| Slice | Commits | Fresh recorded result | Independent review |
|---|---|---|---|
| Pure safety primitives | `35462d1` | 35 focused tests passed | Spec compliant; one Minor test issue later resolved |
| Strict dry-run / result routing | `77c172e`, `97fcc2a` | 55 focused tests passed | Final: no Critical/Important/Minor |
| COM lifecycle / terminal inspection / guards | `0a8c4e8`, `4ed65d9` | 72 focused tests passed | Final: no Critical/Important/Minor |
| Transactional candidate save | `6f9d749`, `fde2d11` | 96 Phase 22 tests passed | Final remediation review: no Critical/Important/Minor |

These results prove focused Python behavior with temporary files and recording fakes. They do not substitute for PowerPoint runtime acceptance.

## Pending Real Windows Cases

- [ ] Verify native Windows Python, pywin32, and `PowerPoint.Application` registration.
- [ ] Exercise an owned isolated session and prove tool cleanup closes its presentations and application.
- [ ] Attach to an existing user PowerPoint session and prove cleanup preserves the application and unrelated presentations.
- [ ] Capture a non-default `AutomationSecurity`, force disable for every programmatic open/reopen, and prove exact restoration after success and injected failure.
- [ ] Run strict dry-run with write/network/COM sentinels and prove zero side effects.
- [ ] Run terminal `--list-addins` and plugin probe routes, including the known iSlide/OKPlus environment when present, without opening a presentation or writing inventory.
- [ ] Save and reopen disposable `.pptx` and `.pptm` candidates; verify suffix preservation, required OOXML parts, and edit sentinel persistence.
- [ ] Exercise 16:9, 4:3, and custom/portrait geometry and verify exported image dimensions preserve ratio.
- [ ] Exercise Windows paths containing spaces and Chinese characters.
- [ ] Exercise source lock, invalid output, staging conflict, and promotion failure paths without source mutation.
- [ ] Record source SHA-256 before and after each case and verify equality.
- [ ] Verify PDF partial-success reporting if PPTX promotion has succeeded and PDF export/promotion fails.

## Phase 22 Exit Criteria

Phase 22 may be marked complete only when all are true:

1. All Phase 22 focused tests, Python compilation, CLI help, JSON routing, and diff checks pass from a clean tree.
2. The real Windows cases above have commands, environment details, inputs, outputs, hashes, and results recorded.
3. Strict dry-run has demonstrated zero writes, network calls, and COM dispatch.
4. Source/output/staging guards reject logical same paths before any write or presentation open.
5. Attached-session preservation and owned-session cleanup are both observed in real PowerPoint.
6. Macro automation security is disabled during every open/reopen and restored exactly after success and failure.
7. PPTX/PPTM candidates pass package validation, macro-disabled read-only reopen, atomic promotion, and edit-sentinel checks.
8. Source hashes remain unchanged before and after successful and failed transactions.
9. No unresolved Critical or Important review finding remains.
10. `V5-SAFE-01` through `V5-SAFE-08` each link to fresh evidence.

## Current Verdict

**Not ready to close.** Transactional save code and Linux/fake-COM tests are present, but the real Windows cases are pending. Phase 22 and v5.0 remain active/incomplete.
