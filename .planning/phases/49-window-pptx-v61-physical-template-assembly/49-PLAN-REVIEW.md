# Phase 49 Independent Plan Review

**Review point:** `215e1d3dc2369fc0209980c9dcae7f0fdf1621f7`
**Fingerprint:** `0c6793fea6ef286e213ed63cb0d0aa1b0743e52ea8bd84ec83caaac25fbc02e3`
**Provider:** OpenCode
**Primary/final model:** `sub2api_openai/gpt-5.6-sol`
**Declared chain:** `gpt-5.6-sol` → `gpt-5.6-terra`
**Effective chain:** declared chain → `agnes/agnes-2.0-flash`
**Session:** `ses_01e53443fffeT0icqV0zWLFY7J`
**Run status:** DONE
**Review result:** REVISE / DONE_WITH_CONCERNS

## Findings

| Severity | Finding | Accepted remediation |
|---|---|---|
| Blocker | Spec reused GOAL-49 IDs with meanings different from the roadmap | Rename detailed checks to AC-49-01..10 and map them to six roadmap goals and seven requirements |
| Blocker | The only completion audit was ordered before merge/push/install parity | Add premerge implementation audit, then merge/push/install parity, then a second audit frozen to pushed master |
| Important | Asset-fit and score breakdown were not executable | Make asset fit/residue/direct-use/style compatibility gates; emit exact five-component score evidence |
| Important | OPC owner identity and unsafe target policy lacked precision | Lock owner-aware queue tuple, normalization, missing-target failure, HTTPS hyperlink allowlist, and traversal/security fixtures |
| Important | Recursive QA report fields and assertions were underspecified | Require recursive relationship, unresolved/unsafe, reuse/dedup, size/amplification, lineage, and portability fields |
| Important | Immutable fact binding and capacity enforcement were underplanned | Require source-bound fact/asset refs, per-slot capacity, hashes, residue/outside-shape guards, and failure tests |
| Important | Clean-room/reviewer isolation lacked fingerprints | Add recursive pre/post manifests, symlink rejection, exact run provenance, one canonical packet, identical hashes, isolated session evidence |
| Important | Two focused test commands pointed to future files implicitly | Name both new test files in task write scopes and keep private replay separate |
| Important | Rollback omitted index/install compatibility | Fail closed on old eligibility-less index and restore/roll forward source, install, and regenerated index together |

## Gate Result

- Structural workflow gates at the frozen point: align/spec/plan/execute PASS.
- Substantive review: 2 Blocker, 7 Important, 0 Nitpick.
- This review is not an approval and cannot satisfy Phase 49 premerge or
  completion-audit gates.
- A fresh re-review of the revised committed plan is required; it must return
  APPROVED with zero Blocker/Important before the plan-review gate closes.

## Re-review 02

**Review point:** `841ed7dba2eb83d97ec604cf60937b1426efd425`
**Fingerprint:** `164314544e45c47b338fcb784faf0433c1bb795a138e8f221271a32011535663`
**Provider:** OpenCode
**Primary/final model:** `sub2api_openai/gpt-5.6-sol`
**Session:** `ses_01e45a14fffeAFN4q1ggoRkGoU`
**Run status:** DONE
**Review result:** REVISE / DONE_WITH_CONCERNS

| Severity | Finding | Accepted remediation |
|---|---|---|
| Blocker | `AC-49-*` evidence rows are treated as unknown Requirement IDs by the current trace parser | Keep the detailed checklist and mapping in the locked spec, but use descriptive first cells in validation so machine trace remains scoped to declared `V61-*` requirements and roadmap `GOAL-*` criteria; require zero unknown IDs before freeze |
| Important | Slide-level refs plus string bindings cannot prove each replacement's authority | Lock every binding as `{text, fact_refs, asset_refs}` and verify external fact/asset manifests by path and SHA-256 before per-slot adaptation |
| Important | The 15-distinct-page invariant is stated but not executable | Reject duplicate page IDs, report distinct/duplicate counts, add a duplicate fixture, and require 15 target/lineage/distinct IDs in replay and clean-room gates |

The Blocker is addressed without modifying workflow infrastructure: detailed
criteria remain human- and audit-traceable under their mapped requirements,
while the workflow's stable requirement parser receives only declared IDs.
The two Important findings are now explicit schema/runtime/test tasks. A fresh
committed re-review is still required and must return APPROVED with zero
Blocker/Important.

## Re-review 03

**Review point:** `2e8d42d7292941d73172e3fa7bc82b13e53a70b6`
**Fingerprint:** `4e5cc397a7922afb4ca20587c69fedc4ba49e5ed4fb885ddaa331a5c3c292233`
**Provider:** OpenCode
**Primary/final model:** `sub2api_openai/gpt-5.6-sol`
**Session:** `ses_01e3f76c2ffeUcUMEsHj0R48dr`
**Run status:** DONE
**Review result:** APPROVED

- Blocker: 0
- Important: 0
- Nitpick: 1 (the specification named `manage_window_pptx_library.py` rather
  than the existing `manage_window_pptx_v61_library.py`; corrected after the
  review as a documentation-only change, for which the reviewer explicitly
  stated no re-review was needed)
- All 3 prior Blocker and 9 prior Important findings were accepted as fully
  remediated.
- Workflow align/spec/plan/execute gates passed; trace contained no unknown
  requirement IDs and only the expected pre-execution `NOT_RUN` gaps.

The Phase 49 plan-review gate is closed. This approval is not implementation
or release evidence; the later frozen premerge and pushed-SHA completion audits
remain mandatory.
