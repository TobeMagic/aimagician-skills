TASK_ID: V61-P49-PLAN-REVIEW-01
ROLE: plan-reviewer
TASK_TYPE: review
MODALITY: text
OBJECTIVE: Independently determine whether the locked Phase 49 specification and approved plan are complete, executable, safely ordered, and sufficient to prove USR-V61-01 without hidden scope or weak acceptance.
DELIVERABLE: Findings-first plan review with one requirement row per V61-* item, finding counts, final status, and exact remediation for every Blocker or Important.
REVIEW_POINT: Commit 215e1d3 on integration/window-pptx-v61-final-20260808.
REVIEW_BINDING: --review-ref 215e1d3

SOURCE_OF_TRUTH:
- .planning/REQUESTS.md: USR-V61-01
- .planning/REQUIREMENTS.md: V61-LIB-01, V61-SEL-01, V61-ASM-01, V61-ADAPT-01, V61-QA-01, V61-CLEAN-01, V61-REL-01
- .planning/ROADMAP.md: Milestone v6.1 / Phase 49 / GOAL-49-01 through GOAL-49-06
- .planning/phases/49-window-pptx-v61-physical-template-assembly/49-SPEC.md
- .planning/phases/49-window-pptx-v61-physical-template-assembly/49-CONTEXT.md
- .planning/phases/49-window-pptx-v61-physical-template-assembly/49-RESEARCH.md
- .planning/phases/49-window-pptx-v61-physical-template-assembly/49-DISCUSSION-LOG.md
- .planning/phases/49-window-pptx-v61-physical-template-assembly/49-01-PLAN.md

ORIGINAL_REQUESTS:
- USR-V61-01: a complete requirement folder plus installed Skill must let Codex gpt-5.6-terra medium select and physically reuse certified templates for every slide, with no reference PPTX/private bytes in the client folder and no quality claim before independent acceptance.

ACCEPTED_DECISIONS:
- Phase 49 stabilizes v6.1 first; the later v7 milestone renames to pptx-studio and completely deletes window-pptx.
- 15/15 accepted slides require direct-use-certified physical lineage; generated visual fallback does not count.
- Multiple selected pages may share one source package when complete-work reuse is the best fit.
- The model owns narrative, candidate IDs, and fact/asset binding only; it cannot author raw geometry, styles, OOXML, code, or release scores.
- COM is optional read-only certification and cannot block delivery.
- Output must have zero unresolved internal relationships and the 15-slide replay must be no larger than 1.30x the 25 MiB source.

KNOWN_CONTEXT:
- Audit found: non-first pages read slide1.xml; the compiler drops direct-use disposition; all pages use one style cluster; nested relationship resolution uses the wrong owner; the verifier checks only slide rels; output/source size is 4.02x.
- The certified core has 288 pages from 266 packages: 129 direct-use-capable and 159 reference-only.
- Phase 49 workflow align/spec/plan/execute gates pass at the frozen review point.

REQUIRED_SKILLS:
- cli-agent-delegator: apply the independent review contract, permissions, severity, and status protocol.
- aimagician-superpower: apply specification, planning, verification, and closure gates for High phase work.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.

ALLOWED_SCOPE:
- Read the frozen repository files listed above and directly referenced implementation/tests needed to judge plan realism.
- Run read-only Git inspection, rg/sed/file reads, and the Phase 49 workflow align/spec/plan/execute validators.

FORBIDDEN_SCOPE:
- Any file write, formatting, cache/artifact generation, commit, branch change, push, network call, secret/config access, .private content, private PPTX bytes, cookie/credential reads, or child-agent delegation.
- Reopening accepted product decisions or reviewing implementation correctness as if the plan were already complete.

PERMISSION_MODE: read-and-run
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: git status/log/show/diff/ls-files/rev-parse; rg; sed; wc; node skills/owned/aimagician-superpower/scripts/workflow.mjs validate/status/trace; non-mutating filesystem listing under the repository excluding .private.
TESTS_AND_EVIDENCE: Run Phase 49 align/spec/plan/execute validators; cite concrete source paths and plan tasks for every finding.
GIT_POLICY: inspect-only; no commit, checkout, restore, reset, stash, clean, merge, rebase, or push.
MODEL_POLICY: Primary sub2api_openai/gpt-5.6-sol because this is a high-risk large-context architecture/plan review; fallback sub2api_openai/gpt-5.6-terra; each provider model has its own declared quota scope and the owned runner may append Agnes once as the final unlimited fallback.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: Report skill loading, source review, validator start/end, requirement mapping, synthesis, and final status through normal worker events.
STOP_AND_ESCALATE_WHEN: A required skill/source is unavailable, the frozen review point cannot be resolved, any requested action exceeds allowed commands, or the review fingerprint drifts.
SESSION_EXPORT: NONE
OUTPUT_FORMAT:
1. Loaded skills and review-point provenance.
2. Findings ordered Blocker, Important, Nitpick; each cites requirement/goal, evidence path, impact, and exact plan change.
3. Matrix for all seven V61 requirements: Covered / Partial / Missing and decisive planned evidence.
4. Checks of ordering, OPC algorithm realism, migration/rollback, private-boundary safety, clean-room validity, visual/audit independence, and v7 deferral boundary.
5. Finding counts and final recommendation APPROVED or REVISE.
6. Final status using exactly the STATUS_PROTOCOL values. DONE is valid only with APPROVED and zero Blocker/Important.
