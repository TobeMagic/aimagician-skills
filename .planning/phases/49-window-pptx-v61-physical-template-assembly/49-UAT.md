# Phase 49: Physical Template Assembly and Work-Report Acceptance - UAT

**Updated:** 2026-08-08

## Scenarios

### UAT-01: Clean-room 15-slide hospital-finance report

- **Starting state:** New external folder containing only the locked public
  requirement pack and business assets; installed Skill has configured private
  library access.
- **Action:** Run Codex `gpt-5.6-terra` medium with the production prompt.
- **Expected visible result:** One coherent, reference-grade 15-slide editable
  work-report PPTX with cover, contents, sections, evidence pages, roadmap, and
  closing.
- **Expected side effect:** Evidence proves 15/15 direct-use physical lineage,
  zero unresolved OPC targets, and no generated visual fallback.
- **Result:** NOT_RUN
- **Evidence:** TBD

### UAT-02: Ineligible or capacity-incompatible candidates

- **Starting state:** Query includes reference-only and undersized candidates.
- **Action:** Compile/query and attempt an invalid assembly plan.
- **Expected visible result:** Eligible alternatives are returned; the invalid
  plan fails with a specific eligibility/capacity error.
- **Expected side effect:** No PPTX is promoted and no private source changes.
- **Result:** NOT_RUN
- **Evidence:** TBD

### UAT-03: Unsafe or unresolved OPC relationship

- **Starting state:** Synthetic source contains file/OLE/script or missing
  internal targets.
- **Action:** Assemble and verify.
- **Expected visible result:** Release fails closed with relationship evidence.
- **Expected side effect:** No incomplete output is promoted.
- **Result:** NOT_RUN
- **Evidence:** TBD

### UAT-04: Deterministic rebuild after correction

- **Starting state:** A failed invalid plan is corrected without changing
  source packages.
- **Action:** Re-run assembly twice with identical inputs.
- **Expected visible result:** Both outputs open/render and are visually
  equivalent.
- **Expected side effect:** Stable lineage and dependency metrics; no stale
  temporary output or source mutation.
- **Result:** NOT_RUN
- **Evidence:** TBD

## UAT Decision

**Status:** NOT_RUN
**Residual risk:** Phase remains open until all four scenarios and independent
visual/audit gates pass.
