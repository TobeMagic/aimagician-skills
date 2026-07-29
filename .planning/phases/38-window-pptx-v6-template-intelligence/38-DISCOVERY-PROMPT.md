TASK_ID: phase38-template-intelligence-discovery
ROLE: explorer
TASK_TYPE: discovery
MODALITY: text
OBJECTIVE: Map the smallest complete Phase 38 implementation that turns the existing Catalog v3, TemplatePack v1, registries, and art-direction code into certified TemplatePack v2/Registry v3/template-selection intelligence capable of supporting reference-grade flagship generation in Phases 39–40.
DELIVERABLE: An evidence-backed architecture gap report with current flows, exact change locations, compatibility risks, test plan, and a proposed locked acceptance checklist. Do not edit files.
REVIEW_POINT: branch feat/window-pptx-v6 at commit ed925be, clean worktree before discovery.

SOURCE_OF_TRUTH:
- .planning/REQUESTS.md
- .planning/STATE.md
- .planning/ROADMAP.md
- .planning/REQUIREMENTS.md
- .planning/phases/38-window-pptx-v6-template-intelligence/38-SPEC.md
- .planning/phases/37-window-pptx-v6-acquisition-catalog/37-SUMMARY.md
- skills/owned/window-pptx/SKILL.md
- skills/owned/window-pptx/scripts/window_pptx/catalog.py
- skills/owned/window-pptx/scripts/window_pptx/template_pack.py
- skills/owned/window-pptx/scripts/window_pptx/registry.py
- skills/owned/window-pptx/scripts/window_pptx/directions.py
- skills/owned/window-pptx/scripts/window_pptx/generation.py
- skills/owned/window-pptx/scripts/window_pptx/portable_renderer.py
- skills/owned/window-pptx/design-packs/
- skills/owned/window-pptx/registries/
- skills/owned/window-pptx/tests/window_pptx/

ORIGINAL_REQUESTS:
- USR-V6-01
- USR-V6-02
- USR-V6-04
- USR-V6-05
- USR-V6-06
- USR-V6-07
- USR-V6-08
- User requires continuation through all phases until visual quality reaches the accepted reference.

ACCEPTED_DECISIONS:
- v6.0 is quality-first and uses GPT-5.5 medium for authoring; weak-model distillation is v6.1.
- Native editable PPTX is canonical; HTML is proof-only; COM is optional diagnostics.
- Certified complete works are visual spines; do not copy unauthorized identity/media.
- Private commercial bytes and credentials stay ignored under .private and cannot be read for this task.
- Phase 37 SEED_READY is sufficient to begin Phase 38; authenticated commercial sync remains NEEDS_AUTH.
- Engineering scores cannot substitute for visual acceptance.

KNOWN_CONTEXT:
- Phase 37 added secure acquisition, quarantine, rights certification, Catalog v3, stable IDs, aliases, dependency closure, and certified-only query.
- One authorized in-repository institutional annual editorial TemplatePack v1 exists.
- The accepted reference deck is .planning/references/pptx/工作总结.pptx, but this text-only task should inspect package metadata/code paths only, not claim visual findings.
- Phase 38 currently has an underspecified four-bullet locked spec.

REQUIRED_SKILLS:
- cli-agent-delegator: apply bounded discovery and evidence protocol.
- aimagician-superpower: preserve request traceability, phase gates, and completion boundaries.
- skill-creator: evaluate owned Skill contract, references, scripts, schemas, evals, and tests as one governed capability.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.

ALLOWED_SCOPE:
- Read-only inspection inside /mnt/d/growth_up_youth/repo/skills.
- Non-mutating git, rg, find, sed, Python one-liners that only print analysis, and existing test collection inspection.
- Inspect the ZIP directory/OOXML metadata of the reference PPTX without extracting or modifying it.

FORBIDDEN_SCOPE:
- Any write, format, test that creates artifacts, package install, network access, browser access, secret access, .private access, commercial-template download, git mutation, process termination, or child delegation.
- Do not evaluate pixels or claim visual parity from text/OOXML metadata.

PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: git status/log/show/diff; rg; find; sed; ls; wc; unzip -l; python read-only inspection.
TESTS_AND_EVIDENCE: Cite exact paths, symbols, callers, schemas, tests, compatibility boundaries, and at least one end-to-end selection/materialization data flow.
GIT_POLICY: inspect-only
MODEL_POLICY: DeepSeek default, Agnes only after an explicit usage/quota/rate-limit event using the exact same prompt.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill loading; source scan; current-flow trace; gap matrix; acceptance/test proposal; final report.
STOP_AND_ESCALATE_WHEN: A required skill/source is unavailable, scope requires writes or secrets, or the provider fails outside the allowed quota fallback.
SESSION_EXPORT: NONE
OUTPUT_FORMAT: Required skills loaded; current architecture table; end-to-end current flow; Phase 38 gap matrix mapped to V6-LIB-01/V6-DESIGN-01/V6-DECK-01; exact file/symbol change map; compatibility/security risks; proposed acceptance checklist; proposed focused/related/full tests; findings with severity; status, model, attempt chain, fallback reason, session ID.
