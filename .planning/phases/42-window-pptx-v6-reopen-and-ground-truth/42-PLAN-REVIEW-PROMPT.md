TASK_ID: window-pptx-v6-reopen-plan-review-20260730
ROLE: plan-reviewer
TASK_TYPE: review
MODALITY: text
OBJECTIVE: Determine whether the reopened Phase 42–48 plan is complete, safe, testable, and capable of correcting the false v6 completion and reaching the user's reference-grade visual target.
DELIVERABLE: Independent review report with findings first, a requirement coverage table, and APPROVED or NOT APPROVED.
REVIEW_POINT: Worktree state on branch feat/window-pptx-v6 including uncommitted Phase 42 planning files.

SOURCE_OF_TRUTH:
- .planning/REQUESTS.md
- .planning/phases/42-window-pptx-v6-reopen-and-ground-truth/42-CONTEXT.md
- .planning/phases/42-window-pptx-v6-reopen-and-ground-truth/42-SPEC.md
- .planning/phases/42-window-pptx-v6-reopen-and-ground-truth/42-01-PLAN.md
- skills/owned/window-pptx/SKILL.md
- User decisions summarized in Phase 42 context

ORIGINAL_REQUESTS:
- USR-V6-01 through USR-V6-10
- Latest user rejection of current visual quality
- Latest user authorization to use Playwright for the entitled catalog, store originals locally under ignored private storage, and prioritize actual result quality

ACCEPTED_DECISIONS:
- v6 is reopened; previous release GO is invalid
- acquire the full entitled 32-category taxonomy, certify a 300–500 page core first
- runtime credential comes only from .private/auth/gaojie.cookie and must never be printed
- native editable PPTX is canonical; COM optional; HTML proof-only
- three anchors first, then fifteen scenarios and ordinary-model mode
- any independent visual Blocker or Important finding blocks promotion

KNOWN_CONTEXT:
- 84 candidates currently mean 15 physical pages, 60 code compositions, and nine aliases
- current flagship generator starts blank and does not consume physical templates
- current sync returns SITE_ADAPTER_NOT_CONFIGURED
- only one 15-slide physical reference pack and four one-slide legacy files are present
- unauthenticated Gaojie product URLs redirect to HTTP login.aspx

REQUIRED_SKILLS:
- cli-agent-delegator: apply the independent review contract and evidence discipline
- aimagician-superpower: review original-request traceability, phase gates, verification, and closure rules
- skill-creator: review changes to the owned Skill workflow and capability contract
- webapp-testing: review Playwright authentication, browser fixture, and external-site test seams
- window-pptx: review native PPTX, template, editability, QA, and visual-acceptance boundaries

ALLOWED_SCOPE:
- Read-only inspection of /mnt/d/Growth_up_youth/repo/skills
- The Phase 42 source-of-truth files and relevant existing Window-PPTX implementation/tests

FORBIDDEN_SCOPE:
- All writes
- Reading or printing credential values, .private contents, environment secrets, or browser profiles
- Network access, authenticated browsing, downloads, commits, push, merge, reset, clean, or stash

PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: read-only file inspection, rg, find, git status/log/diff, and test listing; do not run tests that create artifacts
TESTS_AND_EVIDENCE: Trace every accepted decision to a phase, implementation seam, decisive test, evidence artifact, and closure gate. Spot-check the acquisition and generator claims in actual code.
GIT_POLICY: inspect-only
MODEL_POLICY: DeepSeek default
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: Report skill loading, source inspection, acquisition seam check, materializer seam check, acceptance check, and synthesis.
STOP_AND_ESCALATE_WHEN: A required skill or source is unavailable, inspection would expose credentials, or review needs write/network authority.
SESSION_EXPORT: NONE
OUTPUT_FORMAT: Use the Independent Review Report template. Findings first. Include one PASS, FAIL, or NOT_RUN row for each accepted decision and recommend the smallest concrete corrections.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.
