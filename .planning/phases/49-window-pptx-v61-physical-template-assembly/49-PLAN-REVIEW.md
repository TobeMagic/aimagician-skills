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
