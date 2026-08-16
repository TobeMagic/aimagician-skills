TASK_ID: phase50-plan-review-retry-20260811
ROLE: plan-reviewer
TASK_TYPE: review
MODALITY: text
OBJECTIVE: Review the locked Phase 50 plan for only five risks: approved-source
partition correctness, reversible archive safety, private/Agnes boundary,
deck/page/region catalog contracts, and Phase 50 scope leakage into later
migration/assembly. Return an approval decision; do not edit.
DELIVERABLE: A short plan-review report with PASS/FAIL/NOT_RUN for
V7-CURATE-01, V7-CATALOG-01, V7-VISION-01, V7-REGION-01 and V7-QUERY-01 plus
findings only as Blocker, Important or Nitpick.
REVIEW_POINT: Frozen worktree `/mnt/d/growth_up_youth/repo/skills-pptx-studio-v7`
at HEAD `a1d2d182b4c453f59fbc0a8dbb40cf783af2b826` with controller planning
changes. Reject if its fingerprint changes.
REVIEW_BINDING: --review-worktree /mnt/d/growth_up_youth/repo/skills-pptx-studio-v7
SOURCE_OF_TRUTH:
- `.planning/REQUESTS.md` section `USR-V7-01`
- `.planning/REQUIREMENTS.md` v7 table
- `.planning/ROADMAP.md` Phase 50–53
- `.planning/phases/50-pptx-studio-asset-curation/50-SPEC.md`
- `.planning/phases/50-pptx-studio-asset-curation/50-CONTEXT.md`
- `.planning/phases/50-pptx-studio-asset-curation/50-RESEARCH.md`
- `.planning/phases/50-pptx-studio-asset-curation/50-01-PLAN.md`
- `.planning/phases/50-pptx-studio-asset-curation/50-AI-SPEC.md`
ORIGINAL_REQUESTS:
- USR-V7-01: retain exactly 22 named active Gaojie categories, archive the
  other seven without deletion, index retained rendered pages with Agnes, and
  build future flexible deck/page/component reuse under `pptx-studio`.
ACCEPTED_DECISIONS:
- Phase 50 does not assemble components, rename public code or generate client
  decks. It produces only safe curation/catalog/query contracts.
- Private source bytes/paths/credentials must not be read, printed, uploaded,
  committed or used by this review. Future Agnes analysis is only of rendered
  active-page PNGs and is user-authorized.
- Archive must be hash-bound, dry-run-first and recoverable; no deletion.
KNOWN_CONTEXT:
- Actual inventory: 29 category dirs, 377 packages; exact active allowlist is
  22 categories and inactive set is seven named dirs. Phase 49 is complete at
  master `a1d2d18`; legacy APIs remain unchanged in Phase 50.
REQUIRED_SKILLS:
- aimagician-superpower: phase-plan and review criteria.
- cli-agent-delegator: delegation scope/output contract.
- vision-analysis: assess visual-upload safety only; do not invoke it.
Before substantive work, load every skill named in REQUIRED_SKILLS and report
the loaded skill IDs. If a named skill/source is unavailable, return
NEEDS_CONTEXT; do not improvise.
ALLOWED_SCOPE:
- Read only the source-of-truth planning files plus
  `skills/owned/window-pptx/scripts/window_pptx/private_asset_intelligence.py`,
  `skills/owned/window-pptx/scripts/window_pptx/page_template_library.py`, and
  `skills/owned/vision-analysis/SKILL.md`.
- May run only `git status --short --branch`, `git rev-parse HEAD`, and
  `node skills/owned/aimagician-superpower/scripts/workflow.mjs validate --project . --phase 50 --gate align|spec|plan`.
FORBIDDEN_SCOPE:
- Writes, commits, network, APIs, private roots, `.private`, tests, formatter,
  package tools, child agents, source deletion/moves and every other command.
PERMISSION_MODE: read-and-run
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: exactly the three command forms in ALLOWED_SCOPE.
TESTS_AND_EVIDENCE: run the three allowed workflow gates; state before/after
git status and cite planning paths for every finding.
GIT_POLICY: inspect-only
MODEL_POLICY: Primary `sub2api_openai/gpt-5.6` is chosen for independent
long-context architecture review after the prior `gpt-5.6-terra` session
returned zero tokens and was rejected. Fallback is
`opencode/nemotron-3-ultra-free`; declared quota scopes are model-specific then
shared OpenCode. Agnes is automatic final fallback but must not inspect images.
CHILD_AGENT_POLICY: forbidden
STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill loading, allowed gate runs, five-risk analysis, final.
STOP_AND_ESCALATE_WHEN: required source/skill is missing, a needed action
requires private access/write/network, review point drifts, or provider fails.
SESSION_EXPORT: NONE
OUTPUT_FORMAT:
- Loaded skills; review point and gate results.
- Five-row requirement matrix.
- Findings table, count of Blocker/Important/Nitpick.
- `APPROVED` only if all five PASS and zero Blocker/Important, otherwise
  `CHANGES_REQUIRED`; final STATUS.
