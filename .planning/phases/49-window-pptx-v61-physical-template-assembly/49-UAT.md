# Phase 49: Physical Template Assembly and Work-Report Acceptance - UAT

**Updated:** 2026-08-11

## Scenarios

### UAT-01: Clean-room 15-slide hospital-finance report

- **Starting state:** New external folder with only the locked public requirement
  pack and business assets; private library access resolves through configured
  installed-Skill state only.
- **Action:** Native Codex `gpt-5.6-terra` with `model_reasoning_effort="medium"`
  runs the one-command profile-job harness.
- **Expected result:** One coherent 15-slide, editable work-report PPTX with
  cover, contents, sections, evidence pages, roadmap, and closing.
- **Result:** PASS.
- **Evidence:** Run10 controller
  `/mnt/d/growth_up_youth/pptx-v61-acceptance-controller-20260811-run10.log`
  reports child exit `0`, no issues, clean validation PASS, and exactly one
  candidate with SHA-256
  `1d862e0f9ac49fc42b6e3b3918abc29aea94776ebdf5f830bf4b34d6688ec28a`.
  The physical validator reports 15/15 distinct direct-use lineage and native
  editability; clean-run validator rerun PASS.

### UAT-02: Ineligible or capacity-incompatible candidates

- **Action:** Exercise direct-use/capacity rejection through focused page-library
  and physical-assembly fixtures.
- **Expected result:** Reference-only, residue-risk, missing-asset,
  incompatible-style, and over-capacity candidates fail before promotion.
- **Result:** PASS.
- **Evidence:** `test_page_template_library.py`, `test_physical_assembly.py`,
  and `test_v61_physical_assembly.py` are included in the 115-pass focused
  suite.

### UAT-03: Unsafe or unresolved OPC relationship

- **Action:** Assemble synthetic unsafe/missing relationship fixtures and run
  the recursive output verifier.
- **Expected result:** Release fails closed; no incomplete PPTX is promoted.
- **Result:** PASS.
- **Evidence:** Focused assembly fixtures plus run10 physical report: 119
  internal relationships, zero unresolved, unsafe, or unreachable parts.

### UAT-04: Deterministic rebuild after correction

- **Action:** Run profile-owned binding/assembly fixtures with stable source,
  facts, and candidate inputs.
- **Expected result:** Stable lineage and native editable output without source
  mutation or stale promotion.
- **Result:** PASS.
- **Evidence:** Focused physical-assembly tests pass; run10 emits one
  hash-bound candidate/report/fingerprint set.

## Visual UAT

Run10 uses a canonical anonymous PNG pair packet with SHA-256
`8bac20a33475f28d8b6d65d76c629f5fcda2280cf698e872817036e85fc746ce`.
Three fresh isolated sessions each used two Agnes observations and a unique
Codex synthesis context. ART scored 9.1, NARRATIVE 9.0, and PRODUCTION 8.8;
all declared reference parity true with zero Blocker/Important. Optional
nitpicks are retained in the blind report and do not block the locked bar.

## UAT Decision

**Status:** PASS for functional clean-room and visual UAT.

**Residual risk:** The release delivery sequence is deliberately still open:
fresh scoped premerge approval, merge/push, pushed-SHA source/install parity,
and a fresh completion audit are tracked as V61-REL-01, not treated as UAT
failures.
