# Phase 22 Real Windows PowerPoint UAT

**Verdict:** Passed twice consecutively
**Date:** 2026-07-20
**Harness:** `tests/window_pptx/windows_phase22_uat.py`

## Environment

| Item | Observed value |
|---|---|
| OS | Windows 11 `10.0.26200` |
| Native Python | Anaconda Python 3.13.11, 64-bit |
| PowerPoint | 16.0, build 20131 |
| pywin32 | Available |
| Pillow | 12.2.0 |
| Registry records | 7 across `shared`, `32`, and `64` views |
| Unique registered PowerPoint COM add-in ProgIDs | 4 |
| `iSlideTools.Public` | Office add-in key present; ProgID/CLSID available |
| `Slibe.OKPlus` | Office add-in/VSTO manifest key present; callable ProgID/CLSID unavailable |

Add-in inventory and plugin probing use registry-only inspection. The route does not start PowerPoint, access `COMAddIns.Object`, update add-ins, open presentations, or write inventory files. Loaded `.ppa`/`.ppam` state is intentionally unavailable in this safety mode.

## Reproducible Command

Run from the repository root under WSL with native Windows Python:

```bash
'/mnt/d/miniconda3/python.exe' \
  'D:\Growth_up_youth\repo\skills\tests\window_pptx\windows_phase22_uat.py'
```

The harness sets `sys.dont_write_bytecode = True`, creates only `%TEMP%\窗口 PPTX 验证 <uuid>`, emits progress to stderr, emits exactly one UTF-8 JSON document to stdout, scrubs the disposable root as `%WINDOW_PPTX_UAT_TEMP%`, and removes the directory at the end. No repository PPTX/PPTM fixture is opened or mutated.

## Consecutive Results

| Run | Run ID | Duration | Passed | Failed | Blocked | Cleanup |
|---|---|---:|---:|---:|---:|---|
| 1 | `97e445b8ab624101a7333b90c222caff` | 265,884 ms | 13 | 0 | 0 | Passed |
| 2 | `de2844b6712b40bc97a5be27ec5747fa` | 283,679 ms | 13 | 0 | 0 | Passed |

Every UAT-owned application must become COM-inaccessible within 30 seconds after `Quit()` or its case fails. The harness also captures the baseline `POWERPNT.EXE` process IDs before testing and fails the complete run unless every process created after that baseline exits within 30 seconds. Both accepted JSON summaries record `process_cleanup: passed` and an empty `new_powerpoint_process_residue` list. Each baseline contained zero PowerPoint processes, and an independent operating-system query after each harness exit also found none.

## Case Matrix

| Case | Run 1 | Run 2 | Evidence |
|---|---|---|---|
| `preflight` | Passed | Passed | PowerPoint registration and real automation observed |
| `dry_run_zero_side_effects` | Passed | Passed | Filesystem snapshot unchanged; network, COM, and mutating helpers not called |
| `owned_isolated_cleanup` | Passed | Passed | One `DispatchEx`; owned application closed |
| `attached_preservation` | Passed | Passed | Attached application and two unrelated presentations preserved |
| `macro_security_success_failure` | Passed | Passed | Value forced from 1 to 3 and restored to 1 after success and injected failure |
| `terminal_addins_probe` | Passed | Passed | Registry-only result; presentation and filesystem state unchanged |
| `pptx_transaction` | Passed | Passed | Candidate package/reopen/promotion/edit round trip passed |
| `pptm_transaction` | Passed | Passed | Macro-enabled suffix and editable round trip preserved |
| `ratio_exports` | Passed | Passed | 16:9 `1600×900`, 4:3 `1600×1200`, portrait `900×1600` |
| `guard_failures` | Passed | Passed | Invalid extension, staging collision, and same path rejected before COM/write |
| `promotion_failure` | Passed | Passed | Existing output unchanged; candidate removed |
| `source_lock` | Passed | Passed | Locked output and source unchanged |
| `pdf_partial_failure` | Passed | Passed | PPTX promoted; existing PDF preserved; partial result surfaced |

Both PPTX and PPTM success cases recorded the same ordered validation trace:

1. `save-copy`
2. `ooxml-package`
3. `macro-disabled-reopen`
4. `validation-copy-closed`
5. `atomic-promote`
6. `source-integrity-postcheck`

## Source-Integrity Evidence

All disposable sources were hashed before and after their case and remained unchanged.

| Run | Case | SHA-256 before and after |
|---|---|---|
| 1 | PPTX transaction | `6c89684a608b92c60be0aafba87c104775d685c212e67843b83a06fc96b6b5b5` |
| 1 | PPTM transaction | `5105af1b65e5b0923edf8fbdc9998f69a46e1069a04bbb58bab12b02c9a3ed8d` |
| 1 | Guard source | `4ccd24d68caf79bdfbe4ec800928036880bcaafeeeaa746c93fc64d3c6bf8710` |
| 2 | PPTX transaction | `5382df445eb685d4b90290c70e852825145d888693baaca8e9da82d8f5a376d3` |
| 2 | PPTM transaction | `a39a5d91ff66749117787384d784dee3d1f610999ca9536b0e2bfde520ccfca6` |
| 2 | Guard source | `afa177f98d6955800c076a61735507a76771d258f88d6a7aa7ceb66faf02457b` |

Promotion-failure, source-lock, and PDF-partial cases also asserted source equality internally in both runs.

## Runtime Defects Found and Fixed

The real matrix found behavior that recording fakes could not expose:

- PowerPoint add-in enumeration could load third-party code and hang Office. Inspection is now registry-only and never starts PowerPoint.
- Late-bound PowerPoint exposed `AutomationSecurity` as a callable getter. The macro-security context now normalizes that form before exact restoration.
- Unsafe output requests were rejected only after `DispatchEx`. Output, same-path, and staging checks now run before COM or other writes.
- Reopen/edit checks needed explicit keeper and COM-reference cleanup to avoid Office lock prompts in unattended UAT.
- A non-accepted evidence run exposed a transient PPTX-to-PPTM RPC handoff while the prior Office server was still exiting. The harness now confirms COM application shutdown and releases references before the next case. Two focused format-sequence runs and the two accepted full runs then passed consecutively.
- Review found that COM inaccessibility alone did not prove operating-system process cleanup. The final harness now treats post-baseline `POWERPNT.EXE` residue as a hard failure; only the two runs above were accepted after that gate was added.

## Gate Decision

Every Phase 22 real-Windows case and cleanup gate passed twice. Together with the focused Python suite, compilation, review, and source-integrity evidence, this unblocks Phase 23. It does not ship v5.0; phases 23 through 29 remain required.
