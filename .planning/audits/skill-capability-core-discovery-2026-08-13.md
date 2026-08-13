TASK_ID: skill-capability-core-discovery-2026-08-13-core
ROLE: plan-reviewer
TASK_TYPE: discovery
MODALITY: text
OBJECTIVE: Produce a minimum-change Darwin upgrade plan and fixed behavioral pressure scenarios for the selected core owned Skills.
DELIVERABLE: A Markdown matrix with one row per Skill: observed capability gap, smallest behavior-changing treatment, happy-path scenario, ambiguity/non-trigger scenario, real-tool or artifact assertion, failure/recovery assertion, likely files, and regression risks.
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
- Baseline static scores: aimagician-superpower 70.4, cli-agent-delegator 57.2, agent-workstream-orchestrator 60.8, webapp-testing 45.6, github-pr-workflow 56.4, composio-tool-router 56.6, vision-analysis 50.6, system-prompt-engineering 54.2, skill-creator 52.8, llm-know-how-wiki 58.8, gcloud-ops-workflow 47.0.
- The dominant weighted gaps are incomplete failure branches/checkpoints and missing executable decision rules; do not recommend filler merely to satisfy the static scanner.

REQUIRED_SKILLS:
- cli-agent-delegator: bounded independent plan review contract.
- skill-optimizer: static-versus-behavioral evaluation protocol.
- skill-creator: runtime purity, trigger, progressive-disclosure, and regression constraints.
- aimagician-superpower: requirement mapping and completion boundaries.
- agent-workstream-orchestrator: evaluate its own tracking/isolation behavior.
- webapp-testing: evaluate browser verification behavior.
- github-pr-workflow: evaluate PR and merge behavior.
- composio-tool-router: evaluate SaaS tool discovery/routing behavior.
- vision-analysis: evaluate authorized visual evidence behavior.
- system-prompt-engineering: evaluate prompt engineering boundaries.
- llm-know-how-wiki: evaluate knowledge and secret-inventory boundaries.
- gcloud-ops-workflow: evaluate safe cloud operation behavior.

ALLOWED_SCOPE:
- skills/owned/{aimagician-superpower,cli-agent-delegator,agent-workstream-orchestrator,webapp-testing,github-pr-workflow,composio-tool-router,vision-analysis,system-prompt-engineering,skill-creator,llm-know-how-wiki,gcloud-ops-workflow}/
- skills/owned/skill-optimizer/
- listed planning records

FORBIDDEN_SCOPE:
- Any write, git mutation, network/SaaS/cloud call, secret inspection, source mirror, docx/pdf/xlsx/window-pptx read or modification, and any unrelated repository scan.

PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: literal read operations only for paths in ALLOWED_SCOPE; do not invoke Bash, list directories, inspect installed copies, inspect quality/, home directories, Git state, or any path outside ALLOWED_SCOPE.
TESTS_AND_EVIDENCE: Cite exact headings/paths; distinguish observed fact, inference, and recommendation. Do not fabricate baseline/treatment outputs.
GIT_POLICY: inspect-only
MODEL_POLICY: Primary opencode/deepseek-v4-flash-free for bounded text analysis; the owned runner may use Agnes only after an accepted quota failure.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill loading, per-Skill scan, matrix synthesis, final result
STOP_AND_ESCALATE_WHEN: Any named Skill or planning source cannot be loaded; a recommendation needs a user product decision; or the next contemplated tool call is outside ALLOWED_SCOPE. In the last case return BLOCKED without making that call.
SESSION_EXPORT: NONE
OUTPUT_FORMAT: # Loaded Skills; # Per-Skill Matrix; # Cross-Skill Patterns; # Minimal Treatment Order; # Risks and Open Questions; # Status.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.
