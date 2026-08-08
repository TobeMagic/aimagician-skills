TASK_ID: window-pptx-phase43-playwright-quality-review-20260730
ROLE: quality-reviewer
TASK_TYPE: review
MODALITY: text
OBJECTIVE: Find correctness, security, resumability, browser, and test defects in the new Gaojie Playwright adapter before it is allowed to touch the real authenticated site.
DELIVERABLE: Independent review report with Blocker/Important/Nitpick findings and a PASS/FAIL matrix for V6R-ACQ-01 subrequirements.
REVIEW_POINT: Uncommitted worktree diff on feat/window-pptx-v6 after Phase 43 adapter implementation.

SOURCE_OF_TRUTH:
- .planning/phases/42-window-pptx-v6-reopen-and-ground-truth/42-CONTEXT.md
- .planning/phases/43-window-pptx-v6-real-playwright-acquisition/43-SPEC.md
- .planning/phases/43-window-pptx-v6-real-playwright-acquisition/43-01-PLAN.md
- skills/owned/window-pptx/scripts/window_pptx/gaojie_playwright.py
- skills/owned/window-pptx/scripts/window_pptx/acquisition.py
- skills/owned/window-pptx/scripts/manage_window_pptx_library.py
- tests/window_pptx/test_acquisition_catalog.py

ORIGINAL_REQUESTS:
- USR-V6-05
- USR-V6-10
- USR-V6-11

ACCEPTED_DECISIONS:
- Normal authenticated Playwright UI only; no access-control bypass
- Credential only from .private/auth/gaojie.cookie and never printed
- HTTP is an explicit exact-host exception for this observed site
- full 32-category discovery, resumable local acquisition, SHA-256 dedupe, 40 GiB disk floor
- external exercise is NEEDS_AUTH until the private credential exists

KNOWN_CONTEXT:
- Focused new browser tests pass 3/3
- Missing local credential exercise returns NEEDS_AUTH without a secret
- Skill-local .gitignore ignores .private/

REQUIRED_SKILLS:
- cli-agent-delegator: independent review and evidence discipline
- aimagician-superpower: specification, security, verification, and phase-gate review
- skill-creator: owned Skill workflow compatibility
- webapp-testing: Playwright/browser fixture correctness and site-drift behavior
- window-pptx: private template acquisition and package boundary

ALLOWED_SCOPE:
- Read-only inspection of the repository and named Phase 43 files
- Run the named focused tests and py_compile if needed

FORBIDDEN_SCOPE:
- All writes
- Reading .private contents or any credential/environment secret
- Network access, real-site browsing, downloads, commit, push, merge, reset, clean, or stash

PERMISSION_MODE: read-and-run
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: rg, sed, git status/diff, python -m py_compile on named files, pytest -q tests/window_pptx/test_acquisition_catalog.py -k gaojie_
TESTS_AND_EVIDENCE: Check exact-origin enforcement, cookie redaction, auth expiry, taxonomy floor, pagination loops, link classification, HTML/error rejection, atomic promotion, collision behavior, resume semantics, disk guard, browser cleanup, CLI status mapping, and test realism.
GIT_POLICY: inspect-only
MODEL_POLICY: DeepSeek default
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill loading, diff inspection, browser-flow trace, security trace, test execution, synthesis
STOP_AND_ESCALATE_WHEN: secret access would be required, source is missing, or a command would exceed allowed scope
SESSION_EXPORT: NONE
OUTPUT_FORMAT: Independent Review Report template; findings first; one row per V6R-ACQ-01 subrequirement; APPROVED or NOT APPROVED.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.
