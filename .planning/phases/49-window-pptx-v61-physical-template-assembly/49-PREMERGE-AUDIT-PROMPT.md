# Phase 49 V61 Scoped Premerge Implementation Audit

**Task ID:** V61-P49-PREMERGE-AUDIT-02  
**Role:** independent implementation auditor  
**Task type/modality:** audit / text  
**Review binding:** supplied by the controller as `--review-ref`; review that
exact commit only.

## Objective

Independently decide whether the implementation and all **premerge** evidence
for Phase 49 are approved. This is deliberately not the pushed-master
completion audit: V61-REL-01's merge, install-parity, and second-audit steps
remain pending and must not be mislabeled a defect of this premerge review.

Return `APPROVED` only when V61-LIB-01 through V61-CLEAN-01, GOAL-49-01
through GOAL-49-05, and AC-49-01 through AC-49-08 are evidenced PASS; no
Blocker/Important concerns exist; and the Phase records accurately preserve
V61-REL-01/GOAL-49-06/AC-49-09/AC-49-10 as pending post-premerge delivery.
Otherwise return `REVISE` with concrete findings.

## Authoritative Sources

- `.planning/REQUESTS.md` (`USR-V61-01`), `.planning/REQUIREMENTS.md`,
  `.planning/ROADMAP.md`.
- Phase 49 `SPEC`, `CONTEXT`, `01-PLAN`, `VALIDATION`, `UAT`, `AUDIT`,
  `SUMMARY`, and `49-FINAL-AUDIT-PROMPT.md`.
- Run10 evidence paths and hashes cited in `49-VALIDATION.md`. Do not read
  private folders, PPTX, PNG, preview, or source-package bytes.

## Required Checks

1. Load `cli-agent-delegator`, `aimagician-superpower`, `skill-creator`, and
   `vision-analysis`; use vision only to verify documented review provenance,
   without upload or image inspection.
2. Confirm clean frozen worktree, exact review binding, and no Phase-50/v7
   work. Use only the permitted commands below.
3. Read the authoritative requirements and Phase evidence. Verify that records
   distinguish PASS premerge evidence from still-pending postmerge closure.
4. Re-run the five focused test files and the named physical report validator;
   do not read PPTX/private bytes.
5. Check clean-controller, runtime, report, and blind-report JSON/text only;
   verify hashes and review threshold/independence claims without opening any
   images.
6. Return a concise matrix, finding counts, scope statement, and exactly one
   `APPROVED` or `REVISE` recommendation.

## Scope and Permission Contract

Read-and-run only. Allowed: source/planning/evidence-text reads; `git status`,
`git rev-parse`, `git branch --contains`, `git log`, `git show`, `git diff`,
`git ls-files`; `rg` or built-in read-only `grep`; `sed`; fixed-literal
`printf`; the two workflow validators; exact focused pytest command below;
the physical report validator; `node -e` only with `fs.readFileSync`,
`JSON.parse`, and `console.log` for named non-private JSON/text evidence.

Forbidden: writes, formatting, commits, branch changes, network, secrets,
private-root access, PPTX/PNG/preview/image byte reads, external uploads,
child agents, broad/full test suites, and commands outside this list. A scope
violation invalidates the audit.

## Exact Commands

```bash
git status --short
git rev-parse HEAD
git branch --contains HEAD
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_page_template_library.py \
  tests/test_physical_assembly.py \
  tests/test_v61_physical_assembly.py \
  tests/test_v61_blind_review_runner.py \
  tests/test_v61_blind_acceptance.py
PYTHONDONTWRITEBYTECODE=1 python \
  skills/owned/window-pptx/scripts/validate_window_pptx_v61_physical_report.py \
  --project-root /mnt/d/growth_up_youth/pptx-v61-acceptance-20260811-run10 \
  --report /mnt/d/growth_up_youth/pptx-v61-acceptance-20260811-run10/evidence/physical-assembly-report.v1.json
node skills/owned/aimagician-superpower/scripts/workflow.mjs validate --project . --phase 49 --gate align
node skills/owned/aimagician-superpower/scripts/workflow.mjs validate --project . --phase 49 --gate spec
```

Do not require `trace`, `premerge`, `postmerge`, or `complete` to pass at this
point: the latter three become applicable only after your approval and the
subsequent delivery sequence.
