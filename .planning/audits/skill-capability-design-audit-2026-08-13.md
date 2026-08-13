TASK_ID: skill-capability-design-audit-2026-08-13
ROLE: independent-skill-auditor
TASK_TYPE: audit
OBJECTIVE: Review exactly two owned Skills for concrete capability improvements and routing regressions.

REQUIREMENTS:
- `github-readme-highstar` and `interface-design` must retain their existing repository-truth, HTML-first, visual-evidence, responsive-QA, and PPTX boundary behavior.
- The treatment must add recoverable visual validation and source-integrity guardrails, not only descriptive prose.
- Runtime packages must not include or depend on evaluation corpora.
- A static score is not proof of 90+ behavior; state that controlled effectiveness remains NOT_RUN.

ALLOWED_SCOPE:
- skills/owned/github-readme-highstar/
- skills/owned/interface-design/
- skills/owned/skill-optimizer/references/rubric.md

FORBIDDEN_ACTIONS: writes, commits, network calls, home/configuration reads, secret inspection, package installs, and any non-listed Skill read.
PERMISSION_MODE: strict-read-only

REVIEW METHOD:
1. Read each candidate SKILL.md and only directly routed references needed to verify a cited behavior.
2. For each Skill, cite one concrete new decision, checkpoint, guardrail, or runnable validation route.
3. Check that the non-trigger route still sends native editable PowerPoint delivery to its PPTX owner.
4. Report only `Blocker`, `Important`, or `Nitpick`; no finding is valid without path evidence.

OUTPUT FORMAT:
# Requirement Matrix
# github-readme-highstar
# interface-design
# Findings
# Effectiveness Evidence Status
# Status

Do not use a static score as a behavioral score. Do not implement changes.
