TASK_ID: skill-capability-implementation-audit-2026-08-13
ROLE: independent-skill-auditor
TASK_TYPE: audit
MODALITY: text
OBJECTIVE: Audit whether the selected 19 owned Skills received real capability improvements without source-purity, routing, or boundary regressions.
DELIVERABLE: A requirement matrix for USR-20260813-001, per-Skill findings, and a ranked list of any minimum corrective changes.
REVIEW_POINT: Frozen worktree supplied by the controller.

SOURCE_OF_TRUTH:
- .planning/REQUESTS.md (USR-20260813-001)
- .planning/tasks/skill-capability-optimization-2026-08-13.md
- skills/owned/skill-optimizer/SKILL.md and references/experiment-protocol.md
- skills/owned/skill-creator/SKILL.md
- the selected SKILL.md files and only references they explicitly route to

SELECTED_SKILLS:
- aimagician-superpower, cli-agent-delegator, agent-workstream-orchestrator, webapp-testing, github-pr-workflow, composio-tool-router, vision-analysis, system-prompt-engineering, skill-creator, llm-know-how-wiki, gcloud-ops-workflow
- deep-research-system, opensource-architecture-research, academic-paper-workflow, repo-interview-playbook, knowledge-distillation, perspective-distillation
- github-readme-highstar, interface-design

EXCLUDED_SKILLS:
- window-pptx, docx, pdf, xlsx

ACCEPTED_DECISIONS:
- A static score is diagnostic only. A 90+ total claim additionally needs controlled baseline/treatment effectiveness >=9/10.
- Runtime packages stay pure: no skill-local eval corpus, source mirrors, provider keys, author identities, or unrelated project policy.
- The observed OpenCode scope-drift incident must be judged as a real constraint: prompt contracts can detect and invalidate drift, but must not claim to sandbox tools.

PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_SCOPE: This frozen repository worktree, excluding secret values and user home/configuration. Read only files needed for the audit; do not inspect non-selected Skill packages beyond excluded-path diff verification.
FORBIDDEN_ACTIONS: Writes, commits, pushes, merges, installs, network/SaaS/cloud calls, secret/config inspection, process control, and changing the review point.

EVALUATION QUESTIONS:
1. For each selected Skill, identify one concrete new behavior or recovery decision rather than a wording-only change.
2. Verify trigger and non-trigger boundaries remain coherent with sibling Skills.
3. Verify referenced paths resolve and no runtime Skill relies on quality evidence.
4. Identify where the task cannot honestly claim controlled 90+ effectiveness yet.
5. Report Blocker, Important, and Nitpick only. Every finding must cite a path and specific evidence.

OUTPUT_FORMAT:
# Review Point
# Requirement Matrix
# Per-Skill Capability Evidence
# Findings
# Effectiveness-Evidence Status
# Required Corrections
# Status

STATUS_PROTOCOL: PASS | FAIL | NOT_RUN | NEEDS_CONTEXT
FINDING_SEVERITY: Blocker | Important | Nitpick

Do not implement corrections. Do not infer real-model effectiveness from static wording. Treat missing controlled baseline/treatment outputs as NOT_RUN, not PASS.
