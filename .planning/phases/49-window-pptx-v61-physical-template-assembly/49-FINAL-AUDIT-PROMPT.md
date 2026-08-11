TASK_ID: V61-P49-FINAL-AUDIT-01
ROLE: auditor
TASK_TYPE: audit
MODALITY: text
OBJECTIVE: Independently determine whether commit 09974c8 completes USR-V61-01 and Phase 49, using the frozen final implementation plus externally captured clean-room, physical-lineage, rule-QA, and blind-review evidence.
DELIVERABLE: A completion-audit report with one PASS | FAIL | NOT_RUN row for each V61 requirement, finding counts, exact evidence, and final recommendation APPROVED or REVISE.
REVIEW_POINT: Commit 09974c8 on integration/window-pptx-v61-final-20260808, before merge or push.
REVIEW_BINDING: --review-ref 09974c8

SOURCE_OF_TRUTH:
- .planning/REQUESTS.md: USR-V61-01.
- .planning/REQUIREMENTS.md: V61-LIB-01, V61-SEL-01, V61-ASM-01, V61-ADAPT-01, V61-QA-01, V61-CLEAN-01, V61-REL-01.
- .planning/ROADMAP.md: Milestone v6.1 / Phase 49 / GOAL-49-01 through GOAL-49-06.
- .planning/phases/49-window-pptx-v61-physical-template-assembly/49-SPEC.md, 49-CONTEXT.md, 49-01-PLAN.md, 49-VALIDATION.md, 49-UAT.md, and 49-AUDIT.md.
- Frozen final source at commit 09974c8, especially skills/owned/window-pptx/scripts/window_pptx/physical_assembly.py, page_template_library.py, v61_blind_reviews.py, scripts/run_window_pptx_v61_codex_acceptance.py, scripts/validate_window_pptx_v61_physical_report.py, scripts/validate_window_pptx_v61_clean_pack.py, schemas/, references/v61-blind-review-rubric.md, registries/v61-binding-profiles/phase49-work-report-15.binding-profile.v1.json, and the named tests.
- External non-private acceptance evidence:
  - /mnt/d/growth_up_youth/pptx-v61-acceptance-20260811-run10/
  - /mnt/d/growth_up_youth/pptx-v61-harness-20260811-run10/physical-assembly-run-fingerprint.v1.json
  - /mnt/d/growth_up_youth/pptx-v61-acceptance-controller-20260811-run10.log
  - /mnt/d/growth_up_youth/pptx-v61-runtime-identity-20260811-run10.json
  - /mnt/d/growth_up_youth/pptx-v61-blind-packet-20260811-run10/packet.json
  - /mnt/d/growth_up_youth/pptx-v61-blind-reviews-20260811-run10/run-report.json and reviewers/*/review.json

ORIGINAL_REQUESTS:
- USR-V61-01: Given only a complete client requirement folder, business data/assets, and installed Skill, Codex gpt-5.6-terra medium must select and physically reuse certified template pages for every slide, adapt client facts, and emit one editable, client-deliverable PPTX. Acceptance requires an isolated clean room with no reference PPTX/private bytes, deterministic machine QA/repair, and three fresh independent AI blind reviews.

ACCEPTED_DECISIONS:
- Phase 49 is the v6.1 acceptance only. The later v7 rename to pptx-studio and full deletion of window-pptx is explicitly out of scope.
- The accepted work-report test uses 15 direct-use-certified physical pages; every one must have native editable lineage. Generated visual fallback does not count.
- One dominant style cluster is locked. The model may select narrative, candidates, and fact/asset bindings only; it may not author geometry, raw styles, OOXML, code, or release scores.
- COM is optional read-only certification and cannot block delivery.
- Private commercial files are user-local and ignored. The clean client root must not contain reference PPTX, template previews, private bytes, historical outputs, symlinks, or network assets.
- The visual acceptance protocol is reference-relative for art direction only: reference wording/data are not the candidate's copy authority. Candidate-specific visible regressions still block; mere wording differences or uncertain OCR do not.

KNOWN_CONTEXT:
- Final production run: hospital-finance-annual-2025-v61-run10. The controller log reports PASS, child exit 0, no controller issues, frozen installed-skill digest 12ad0503dbef130f1bfecbef53b8702c4c50abb11d5d4d8212dab4740236339a, runtime manifest SHA 136c47da70695da8007e51bbeb595b89eefca805d8686985fac06505be3d6c2a, candidate SHA 1d862e0f9ac49fc42b6e3b3918abc29aea94776ebdf5f830bf4b34d6688ec28a.
- Independent physical-report validation passed: 15 slides, 15 distinct page IDs, 100% native editable coverage, 0 unresolved/unsafe relationships, output 25,393,957 bytes.
- Fresh clean-run validation passed after restoring the frozen installed tree. Focused tests passed: 115 passed, 4 skipped.
- The final visual packet SHA is 8bac20a33475f28d8b6d65d76c629f5fcda2280cf698e872817036e85fc746ce. ART, NARRATIVE, and PRODUCTION reviews are all PASS, all parity=true, medians 9.1, 9.0, and 8.8; all findings are Nitpick only. Each reviewer used two new Agnes observations and a unique isolated Codex synthesis context.
- An earlier clean-run validation briefly failed only because a subsequent local Python inspection created ignored __pycache__ files in the installed skill. It was corrected by re-installing the exact committed Skill source; the final clean-run validation then passed against the original frozen run fingerprint. Do not treat the superseded transient cache drift as an output defect, but verify that the final evidence explicitly binds the final production run and that no acceptance claim relies on it.

REQUIRED_SKILLS:
- cli-agent-delegator: completion-audit contract, review binding, permission, severity, and provenance protocol.
- aimagician-superpower: Phase 49 requirements/traceability/closure-gate audit.
- skill-creator: inspect installed-Skill source, installation-state evidence, and Skill deliverable quality.
- vision-analysis: audit the provenance and independence of the authorized Agnes visual-evidence route; do not upload or analyze new images.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.

ALLOWED_SCOPE:
- Read the frozen review worktree, the source-of-truth planning files, and the external non-private evidence paths named above.
- Run read-only Git commands; rg/sed/find/sha256sum/stat; JSON inspection; and only these non-mutating checks from the frozen review worktree: the named focused pytest files, Phase 49 workflow validate/status/trace commands, and the physical-report validator against the named run10 report/project.
- You may inspect anonymous visual-review JSON and packet metadata. You may not open, upload, or inspect reference/candidate PPTX or PNG bytes.

FORBIDDEN_SCOPE:
- Any file write, format, cache/artifact generation, commit, branch change, push, merge, checkout, reset, restore, stash, clean, network call, secret/config access, cookie/credential read, .private directory read, private PPTX/template bytes, client-output PPTX/image byte inspection, new vision upload, or child-agent delegation.
- Do not re-run Codex generation, edit acceptance evidence, change an acceptance criterion, reopen accepted product decisions, or start Phase 50/v7 work.

PERMISSION_MODE: read-and-run
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: git status/log/show/diff/ls-files/rev-parse; rg; sed; find/stat/sha256sum; JSON read; node skills/owned/aimagician-superpower/scripts/workflow.mjs validate/status/trace; PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider for the named tests only; PYTHONDONTWRITEBYTECODE=1 python scripts/validate_window_pptx_v61_physical_report.py with the named report/project only.
TESTS_AND_EVIDENCE:
- Verify exact review-point provenance and frozen worktree integrity before/after.
- Run/inspect Phase 49 workflow align, spec, trace, and premerge gates as permitted; report any gate unavailable or failing.
- Independently re-run the physical-report validator for run10.
- Run only these focused tests: tests/test_page_template_library.py, tests/test_physical_assembly.py, tests/test_v61_physical_assembly.py, tests/test_v61_blind_review_runner.py, tests/test_v61_blind_acceptance.py.
- Spot-check the final controller, fingerprint, runtime manifest, clean validator pass record, packet metadata, and all three review decisions without reading private assets or slide/image bytes.
- For every V61 requirement, produce PASS, FAIL, or NOT_RUN with decisive path/command evidence. Do not replace requirement coverage with a test-only summary.
GIT_POLICY: inspect-only; no commit, checkout, restore, reset, stash, clean, merge, rebase, or push.
MODEL_POLICY: Primary sub2api_openai/gpt-5.6-terra at medium reasoning, selected because the user locked gpt-5.6-terra medium for this Skill acceptance and the audit needs long-context code/evidence reasoning. Fallback sub2api_openai/gpt-5.6-sol only if the primary is unavailable; each provider model has its own declared quota scope and the owned runner may append Agnes once as final fallback. No visual upload is authorized for this text audit.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: Report skill loading, provenance/fingerprint check, source/evidence scan, validator/test start/end, requirement mapping, synthesis, and final status through normal worker events.
STOP_AND_ESCALATE_WHEN: A required skill/source is unavailable; frozen review fingerprint drifts; a command would exceed the exact allowlist; external evidence binds an inconsistent run; a required validator/test cannot run; or a private/client artifact would be needed.
SESSION_EXPORT: NONE
OUTPUT_FORMAT:
1. Loaded skills, audit provenance, model-selection rationale, declared/effective chain, primary/final model, transitions, attempt chain, fallback reason, session ID, resolved commit, and initial/final fingerprint.
2. Controller spot-check table, marking observed fact versus inference.
3. One PASS | FAIL | NOT_RUN row each for V61-LIB-01, V61-SEL-01, V61-ASM-01, V61-ADAPT-01, V61-QA-01, V61-CLEAN-01, and V61-REL-01, with decisive evidence.
4. Goal/acceptance coverage for GOAL-49-01 through GOAL-49-06 and AC-49-01 through AC-49-10.
5. Findings ordered Blocker, Important, Nitpick; each includes evidence, impact, and required remediation. Explicitly state zero findings where applicable.
6. Checks of physical lineage/editability, clean-room provenance, blind-review independence, final-Skill identity, scope compliance, and Phase-50 deferral.
7. Final recommendation APPROVED or REVISE and final STATUS_PROTOCOL value. DONE is valid only for APPROVED, zero Blocker/Important, and no V61 FAIL/NOT_RUN.
