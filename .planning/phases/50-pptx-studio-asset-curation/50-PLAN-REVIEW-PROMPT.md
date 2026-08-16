TASK_ID: phase50-plan-review-20260811
ROLE: plan-reviewer
TASK_TYPE: review
MODALITY: text
OBJECTIVE: Independently assess whether the locked Phase 50 plan can safely
deliver the approved local private-library curation, rendered-page visual
catalog and bounded retrieval tracer without scope drift or irreversible loss.
DELIVERABLE: A concise independent plan-review report with one PASS/FAIL/NOT_RUN
row for each V7-CURATE-01, V7-CATALOG-01, V7-VISION-01, V7-REGION-01 and
V7-QUERY-01; findings only as Blocker, Important or Nitpick; no fixes.
REVIEW_POINT: Uncommitted but frozen controller worktree at
`/mnt/d/growth_up_youth/repo/skills-pptx-studio-v7`, expected HEAD
`a1d2d182b4c453f59fbc0a8dbb40cf783af2b826`. Review binding must hash the
worktree before/after and reject drift.
REVIEW_BINDING: --review-worktree /mnt/d/growth_up_youth/repo/skills-pptx-studio-v7

SOURCE_OF_TRUTH:
- `.planning/STATE.md`
- `.planning/PROJECT.md`
- `.planning/CONTEXT.md`
- `.planning/REQUESTS.md` (USR-V7-01)
- `.planning/REQUIREMENTS.md` (V7-CURATE-01 through V7-QUERY-01)
- `.planning/ROADMAP.md` (Phase 50 and dependent Phase 51–53 boundaries)
- `.planning/phases/50-pptx-studio-asset-curation/50-SPEC.md`
- `.planning/phases/50-pptx-studio-asset-curation/50-CONTEXT.md`
- `.planning/phases/50-pptx-studio-asset-curation/50-RESEARCH.md`
- `.planning/phases/50-pptx-studio-asset-curation/50-DISCUSSION-LOG.md`
- `.planning/phases/50-pptx-studio-asset-curation/50-AI-SPEC.md`
- `.planning/phases/50-pptx-studio-asset-curation/50-01-PLAN.md`

ORIGINAL_REQUESTS:
- USR-V7-01: make a future `pptx-studio` agent use client requirements/assets
  with flexible complete-deck, page and controlled component reuse; retain
  exactly 22 named Gaojie categories; archive the other seven recoverably;
  use Agnes descriptions of rendered retained pages; never delete or publish
  private assets; later remove `window-pptx` with no shim.

ACCEPTED_DECISIONS:
- Phase 50 is curation/catalog/query only. Physical component assembly,
  public rename/removal, full QA and clean-room acceptance are Phase 51–53.
- Existing private root is outside this worktree. No private bytes/paths,
  rendered images, credentials or cookies may be read, printed or uploaded in
  this review.
- User authorization permits future Agnes upload of rendered active-page PNGs;
  the plan must preserve original-PPTX/media/credential exclusions.
- A curation apply is legal only after dry-run/source hashes/recovery path
  pass; private sources are archived, never deleted.
- Models may choose bounded narrative/candidate/fact/asset binding decisions,
  not raw geometry/style/OOXML/code or release results.

KNOWN_CONTEXT:
- Phase 49 completed and pushed on master `a1d2d18`; its public physical-page
  APIs must remain unchanged through Phase 50.
- Local inventory observed 29 Gaojie category directories, 377 packages and
  294 PPTX files inside the user-approved 22 active categories. The inactive
  names are 055-图文排版, 056-表格图表, 058-实用素材, 062-风格配色,
  104-数据基座, 105-文本组件 and 106-装饰形状.
- Existing code has portable rendering and page-template extraction patterns,
  but no deck/page/region catalog or approved-category partition contract.

REQUIRED_SKILLS:
- aimagician-superpower: apply phase-plan, traceability and review criteria.
- cli-agent-delegator: honor the delegated review contract and report format.
- vision-analysis: evaluate whether the planned Agnes boundary is safe; do not
  invoke it or inspect/upload any image in this text plan review.

Before substantive work, load every skill named in REQUIRED_SKILLS and report
the loaded skill IDs. Apply their workflows and boundaries. If any required
skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the
missing item; do not substitute an improvised workflow.

ALLOWED_SCOPE:
- Read only the listed planning files, `skills/owned/window-pptx/SKILL.md`,
  `skills/owned/window-pptx/scripts/window_pptx/private_asset_intelligence.py`,
  `skills/owned/window-pptx/scripts/window_pptx/page_template_library.py`,
  `skills/owned/aimagician-superpower/scripts/workflow.mjs`, and
  `skills/owned/vision-analysis/SKILL.md`.
- Run `git status --short --branch`, `git rev-parse HEAD`,
  `node skills/owned/aimagician-superpower/scripts/workflow.mjs validate --project . --phase 50 --gate align|spec|plan`, and narrowly scoped `sed`, `rg`, or `find` reads inside the listed tracked paths.

FORBIDDEN_SCOPE:
- All private roots/`.private`, credentials, cookies, archive payloads,
  renderer output, customer folders, network, external APIs, installs,
  formatting, writes, commits, pushes, merges, resets, cleanup, test commands
  that create artifacts, child agents, or any command not explicitly allowed.

PERMISSION_MODE: read-and-run
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: exactly the read-only commands described in ALLOWED_SCOPE.
TESTS_AND_EVIDENCE: Run the three listed workflow gates and report their
before/after git status. Validate requirement coverage, plan ordering,
reversible archive semantics, private/vision boundary, schema/testing seams,
and the Phase 50→51/52/53 migration edge.
GIT_POLICY: inspect-only; no commit and no write.
MODEL_POLICY: Primary `sub2api_openai/gpt-5.6-terra` is selected because this
is a high-risk cross-module plan requiring long-context systems reasoning;
fallback `sub2api_openai/gpt-5.6` is equivalent broad reasoning capacity;
then `opencode/nemotron-3-ultra-free` offers an independent high-context
review route. Each provider uses its declared model quota scope; Agnes is the
automatic final fallback only and must not inspect images here.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: report preflight, skill loading, source review, gate runs,
coverage review and final synthesis.
STOP_AND_ESCALATE_WHEN: a required source is missing, scope requires private
byte access, any command would write, the review point drifts, or model
availability prevents a bounded independent review.
SESSION_EXPORT: NONE
OUTPUT_FORMAT:
1. loaded skills and review-point/fingerprint status;
2. requirement matrix (five requirements: PASS/FAIL/NOT_RUN, evidence);
3. findings table with only allowed severities;
4. explicit review of exact active/archived partition, hash/recovery safety,
   visual upload boundary, deterministic query and deferred migration;
5. model policy declared/effective chain, final model/transitions/session;
6. final `APPROVED` only when every requirement is PASS and Blocker/Important
   counts are zero, otherwise `CHANGES_REQUIRED`; then STATUS.
