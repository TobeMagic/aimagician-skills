TASK_ID: skill-capability-design-discovery-2026-08-13-design
ROLE: plan-reviewer
TASK_TYPE: discovery
MODALITY: text
OBJECTIVE: Produce a minimum-change Darwin upgrade plan and fixed behavioral pressure scenarios for github-readme-highstar and interface-design.
DELIVERABLE: A Markdown matrix with one row per Skill: observed capability gap, smallest behavior-changing treatment, happy-path scenario, ambiguity/non-trigger scenario, real artifact assertion, visual/implementation failure assertion, likely files, and regression risks.
REVIEW_POINT: master worktree at dispatch; no implementation is approved yet.
REVIEW_BINDING: NONE

SOURCE_OF_TRUTH:
- .planning/REQUESTS.md (USR-20260813-001)
- .planning/tasks/skill-capability-optimization-2026-08-13.md
- skills/owned/skill-optimizer/SKILL.md and references/rubric.md
- skills/owned/skill-creator/SKILL.md

ORIGINAL_REQUESTS:
- USR-20260813-001

ACCEPTED_DECISIONS:
- Total 90+ means static weighted score >=70 plus controlled effectiveness >=9/10; static-only scores are diagnostic.
- Preserve HTML-first visual work and PPTX handoff boundary; do not modify document Skills or window-pptx.
- Runtime Skills remain source-neutral and do not contain eval corpora.

KNOWN_CONTEXT:
- Baseline static scores: github-readme-highstar 66.2 and interface-design 74.0.
- README Skill previously gained a pass-based flow and visual media integration; do not replace it with generic marketing instructions.

REQUIRED_SKILLS:
- cli-agent-delegator: bounded independent plan review contract.
- skill-optimizer: static-versus-behavioral evaluation protocol.
- skill-creator: runtime purity, trigger, progressive-disclosure, and regression constraints.
- github-readme-highstar: repository branding and README visual route.
- interface-design: HTML-first visual design, prototype, motion, verification, and PPTX handoff boundary.
- webapp-testing: browser verification route when applicable.

ALLOWED_SCOPE:
- skills/owned/{github-readme-highstar,interface-design,webapp-testing,skill-optimizer,skill-creator,cli-agent-delegator}/
- listed planning records

FORBIDDEN_SCOPE:
- Any write, git mutation, external image upload, secret inspection, source mirror, docx/pdf/xlsx/window-pptx read or modification, and any unrelated repository scan.

PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: read-only file inspection and the read-only audit-skill command only.
TESTS_AND_EVIDENCE: Cite exact headings/paths; distinguish observed fact, inference, and recommendation. Do not fabricate visual or baseline/treatment outputs.
GIT_POLICY: inspect-only
MODEL_POLICY: Primary opencode/deepseek-v4-flash-free for bounded text analysis; the owned runner may use Agnes only after an accepted quota failure.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill loading, per-Skill scan, matrix synthesis, final result
STOP_AND_ESCALATE_WHEN: Any named Skill or planning source cannot be loaded, or a recommendation needs a user product decision.
SESSION_EXPORT: NONE
OUTPUT_FORMAT: # Loaded Skills; # Per-Skill Matrix; # Cross-Skill Patterns; # Minimal Treatment Order; # Risks and Open Questions; # Status.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.
