# Phase 49 V61 Scoped Premerge Implementation Audit

```text
TASK_ID: V61-P49-PREMERGE-AUDIT-02
ROLE: auditor
TASK_TYPE: audit
MODALITY: text
DELIVERABLE: A hash-bound scoped premerge audit with requirement/goal/criterion
matrix, finding counts, scope statement, and exactly APPROVED or REVISE.
REVIEW_POINT: The exact committed Phase-49 evidence-promotion state supplied by
the controller. This is a premerge implementation review, not completion.
REVIEW_BINDING: supplied by the controller as --review-ref; review that exact
commit only.

ORIGINAL_REQUESTS:
- USR-V61-01.

ACCEPTED_DECISIONS:
- Codex gpt-5.6-terra at medium performs the clean 15-slide acceptance run.
- 15/15 accepted pages physically reuse certified direct-use pages; native
  blank-deck fallback is not acceptance evidence.
- Three fresh independent AI blind reviews require median >= 8, parity true,
  and no Blocker/Important.
- COM is optional read-only certification and cannot block portable delivery.
- Do not begin Phase 50/v7, rename, archive, delete, or prune private assets.

KNOWN_CONTEXT:
- Frozen run10 candidate SHA-256 is 1d862e0f9ac49fc42b6e3b3918abc29aea94776ebdf5f830bf4b34d6688ec28a.
- Run10 physical, clean, and blind evidence are already captured externally
  and summarized in 49-VALIDATION.md; no private or visual bytes are required.
- First overall evidence audit ses_0110ed0b7ffeIusalNWvViu2e5 found 0 Important
  and confirmed all functional gates, but correctly returned REVISE because
  phase records were stale and postmerge work had not happened.

REQUIRED_SKILLS:
- cli-agent-delegator: independent read-and-run audit contract.
- aimagician-superpower: Phase-49 requirements/evidence reconciliation.
- skill-creator: installed-Skill workflow and documentation scope.
- vision-analysis: validate documented Agnes provenance only; no image access.

Before substantive work, load every skill named in REQUIRED_SKILLS and report
the loaded skill IDs. If a required skill or source cannot be loaded, return
NEEDS_CONTEXT; do not substitute an improvised workflow.
```

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

**GIT_POLICY:** inspect-only; no commit, merge, push, reset, checkout, clean,
stash, or branch change.  
**MODEL_POLICY:** primary `sub2api_openai/gpt-5.6-terra` at medium reasoning:
the user locked it for this production-quality acceptance and it supports the
large evidence/repository reconciliation. Ordered fallback
`sub2api_openai/gpt-5.6-sol`; Agnes runtime fallback may be appended only by
the runner and is not a visual-review route here.  
**CHILD_AGENT_POLICY:** forbidden.  
**SESSION_EXPORT:** NONE.  
**STATUS_PROTOCOL:** DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED.  
**FINDING_SEVERITY:** Blocker | Important | Nitpick.  
**STOP_AND_ESCALATE_WHEN:** a required source/skill is missing, a command would
exceed scope, the review binding drifts, or evidence conflicts materially.

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
