TASK_ID: window-pptx-v6-phase45-plan-review
ROLE: plan-reviewer
TASK_TYPE: review
MODALITY: text
OBJECTIVE: Independently challenge whether Phase 45's dual materialization bridge can satisfy V6R-MAT-01 truthfully and safely before implementation.
DELIVERABLE: Findings-first review with APPROVED or NOT_APPROVED.
REVIEW_POINT: Exact current worktree bound by the controller runner.
REVIEW_BINDING: --review-worktree /mnt/d/growth_up_youth/repo/skills

SOURCE_OF_TRUTH:
- .planning/phases/45-window-pptx-v6-selection-to-materialization/45-RESEARCH.md
- .planning/phases/45-window-pptx-v6-selection-to-materialization/45-CONTEXT.md
- .planning/phases/45-window-pptx-v6-selection-to-materialization/45-SPEC.md
- .planning/phases/45-window-pptx-v6-selection-to-materialization/45-01-PLAN.md
- .planning/REQUIREMENTS.md V6R-MAT-01
- skills/owned/window-pptx/scripts/window_pptx/template_intelligence.py
- skills/owned/window-pptx/scripts/window_pptx/generation.py
- skills/owned/window-pptx/scripts/window_pptx/deck_plan.py
- skills/owned/window-pptx/scripts/window_pptx/render_plan.py
- skills/owned/window-pptx/scripts/window_pptx/template_pack.py
- skills/owned/window-pptx/scripts/window_pptx_automation.py

ORIGINAL_REQUESTS:
- Continue autonomously until all phases are complete and visual quality reaches the accepted reference level.
- Reuse highly differentiated templates and prove real reuse rather than metadata-only selection.

ACCEPTED_DECISIONS:
- Registered-native candidates must bind the exact base variant and cannot silently fall back.
- Physical candidates execute only through the whole-deck lossless TemplatePack adapter.
- Mixed materializers, unknown candidates, and incomplete evidence fail closed.
- Auto mode preserves unsupported-scenario compatibility; explicit selection is strict.
- Arbitrary multi-source OOXML relationship merging is deferred.

KNOWN_CONTEXT:
- Selection is currently tests-only and production ignores it.
- SlideBlueprint currently drops candidate.base_variant_id.
- Native and TemplatePack CLI routes are disconnected.
- Phase 44 private bytes and credentials are forbidden review inputs.

REQUIRED_SKILLS:
- cli-agent-delegator: enforce independent frozen review and report contract.
- aimagician-superpower: verify requirement traceability, phase gates, and implementation realism.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.

ALLOWED_SCOPE:
- Read only the named source-of-truth files and directly imported definitions needed to validate an assertion.
- Non-mutating rg/sed/git inspection.
FORBIDDEN_SCOPE:
- Any write, private directory, credential/cookie/source URL, network, package install, git mutation, or unrelated Phase 43/44 dirty changes.
PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: rg, sed, git status/diff/show, read-only Python inspection without writes.
TESTS_AND_EVIDENCE: Map every GOAL-45 item to an executable seam; identify missing fields, fallbacks, ordering, artifact, schema, compatibility, and physical evidence risks.
GIT_POLICY: inspect-only
MODEL_POLICY: DeepSeek reasoning default; Agnes quota fallback only.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill load, source review, execution trace, finding synthesis, recommendation.
STOP_AND_ESCALATE_WHEN: A required source/skill is unavailable or review needs forbidden private data.
SESSION_EXPORT: NONE
OUTPUT_FORMAT: Loaded skills; findings table with severity/path/evidence/remediation; GOAL-45-01..04 coverage table; assumptions; final APPROVED/NOT_APPROVED; provider/model/attempt chain/fallback/session/fingerprint/status.
