TASK_ID: phase38-locked-plan-review
ROLE: plan-reviewer
TASK_TYPE: review
MODALITY: text
OBJECTIVE: Independently determine whether the locked Phase 38 spec and plan are sufficient, internally consistent, compatible, testable, and correctly scoped to support reference-grade Phase 39–40 flagships.
DELIVERABLE: PASS or FAIL with requirement-by-requirement evidence, exact Blocker/Important/Nitpick findings, and minimal required corrections. Do not edit files.
REVIEW_POINT: current uncommitted Phase 38 planning diff after local workflow spec/plan PASS.

SOURCE_OF_TRUTH:
- .planning/REQUESTS.md
- .planning/REQUIREMENTS.md V6-LIB-01, V6-DESIGN-01, V6-DECK-01
- .planning/ROADMAP.md Phases 38–41
- .planning/phases/38-window-pptx-v6-template-intelligence/38-SPEC.md
- .planning/phases/38-window-pptx-v6-template-intelligence/38-CONTEXT.md
- .planning/phases/38-window-pptx-v6-template-intelligence/38-01-PLAN.md
- .planning/phases/38-window-pptx-v6-template-intelligence/38-RESEARCH.md
- .planning/phases/38-window-pptx-v6-template-intelligence/38-DISCUSSION-LOG.md
- Phase 37 public APIs in:
  - skills/owned/window-pptx/scripts/window_pptx/catalog.py
  - skills/owned/window-pptx/scripts/window_pptx/template_pack.py
  - skills/owned/window-pptx/scripts/window_pptx/registry.py
  - skills/owned/window-pptx/scripts/window_pptx/directions.py

ORIGINAL_REQUESTS:
- USR-V6-01, USR-V6-02, USR-V6-04, USR-V6-05, USR-V6-06, USR-V6-07, USR-V6-08
- Continue until all phases complete and visual quality reaches the accepted reference.

ACCEPTED_DECISIONS:
- GPT-5.5 medium is the v6 author/selector; weak-model distillation is v6.1.
- Native editable PPTX is canonical; COM optional; HTML proof-only.
- One authorized physical work-report spine and two first-party executable composition spines form the legal pilot.
- TemplatePack v1/current registries remain compatible.
- Phase 38 does not claim final flagship visual parity.

KNOWN_CONTEXT:
- The OpenCode working directory is `/mnt/d/growth_up_youth/repo/skills`.
  The owned Skill root is the nested path
  `/mnt/d/growth_up_youth/repo/skills/skills/owned/window-pptx`; there is no
  `/mnt/d/growth_up_youth/repo/skills/owned/window-pptx`.
- Workflow spec and plan validation pass locally.
- Existing layout registry has 110 variants across 25 families.
- The accepted reference and packaged physical TemplatePack are SHA-identical.
- Commercial acquisition remains NEEDS_AUTH and must not block the first-party pilot.

REQUIRED_SKILLS:
- cli-agent-delegator: apply independent plan-review and evidence protocol.
- aimagician-superpower: verify original-request traceability and phase gates.
- skill-creator: review the owned Skill architecture, schemas, code, docs, evals, and tests as one capability.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.

ALLOWED_SCOPE:
- Strict read-only inspection inside /mnt/d/growth_up_youth/repo/skills.
- Non-mutating git/rg/find/sed and workflow validate spec/plan.
- Read only the named source-of-truth files and four exact public API files
  above. Do not perform a broad repository scan.

FORBIDDEN_SCOPE:
- Writes, tests that create artifacts, network, .private, secrets, downloads, git mutation, implementation, visual claims from pixels, child delegation.

PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: git status/diff/log; rg/find/sed; workflow validate spec/plan.
TESTS_AND_EVIDENCE: Map every Phase 38 requirement and acceptance criterion to a planned owner/test; challenge the 84-candidate derivation, three-spine legality/executability, v1 compatibility, model boundary, materializer handoff, and Phase 39/40 dependency.
GIT_POLICY: inspect-only
MODEL_POLICY: DeepSeek default; exact-prompt Agnes fallback only after explicit quota/rate limit.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skills; source review; traceability matrix; architecture/compatibility challenge; testability challenge; verdict.
STOP_AND_ESCALATE_WHEN: required source/skill unavailable or scope expansion needed.
SESSION_EXPORT: NONE
OUTPUT_FORMAT: Skills loaded; frozen review point; requirement matrix PASS/FAIL/NOT_RUN; acceptance/test ownership matrix; findings; missing/extra/shallow/narrow behavior; verdict PASS/FAIL; model/attempt/fallback/session/status.

EXECUTION_NOTE: In this OpenCode environment the Read tool requires the exact
`filePath` schema and has failed repeatedly in a prior attempt. Do not retry
that failing tool shape. Use allowed read-only Bash `sed`, `rg`, and `git diff`
commands for every source. Never use `git checkout`, restore, reset, clean,
stash, commit, or any other mutation.
