TASK_ID: skill-capability-research-discovery-2026-08-13-research
ROLE: plan-reviewer
TASK_TYPE: discovery
MODALITY: text
OBJECTIVE: Produce a minimum-change Darwin upgrade plan and fixed behavioral pressure scenarios for the selected research and knowledge owned Skills.
DELIVERABLE: A Markdown matrix with one row per Skill: observed capability gap, smallest behavior-changing treatment, happy-path scenario, ambiguity/non-trigger scenario, real-tool or artifact assertion, evidence-quality/failure assertion, likely files, and regression risks.
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
- Do not modify docx, pdf, xlsx, or window-pptx.
- Runtime Skills remain source-neutral and do not contain eval corpora.

KNOWN_CONTEXT:
- Baseline static scores: deep-research-system 59.3, opensource-architecture-research 46.7, academic-paper-workflow 47.6, repo-interview-playbook 61.2, knowledge-distillation 74.0, perspective-distillation 73.4.
- Favor evidence quality, correct abstention, progressive disclosure, and reusable decision artifacts over generic research prose.

REQUIRED_SKILLS:
- cli-agent-delegator: bounded independent plan review contract.
- skill-optimizer: static-versus-behavioral evaluation protocol.
- skill-creator: runtime purity, trigger, progressive-disclosure, and regression constraints.
- deep-research-system: research delivery boundary.
- opensource-architecture-research: comparison and architecture boundary.
- academic-paper-workflow: scholarly integrity and submission boundary.
- repo-interview-playbook: repository interview boundary.
- knowledge-distillation: evidence-to-knowledge boundary.
- perspective-distillation: multi-perspective synthesis boundary.

ALLOWED_SCOPE:
- skills/owned/{deep-research-system,opensource-architecture-research,academic-paper-workflow,repo-interview-playbook,knowledge-distillation,perspective-distillation}/
- skills/owned/{skill-optimizer,skill-creator,cli-agent-delegator}/
- listed planning records

FORBIDDEN_SCOPE:
- Any write, git mutation, internet search, secret inspection, source mirror, docx/pdf/xlsx/window-pptx read or modification, and any unrelated repository scan.

PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: read-only file inspection and the read-only audit-skill command only.
TESTS_AND_EVIDENCE: Cite exact headings/paths; distinguish observed fact, inference, and recommendation. Do not fabricate baseline/treatment outputs.
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
