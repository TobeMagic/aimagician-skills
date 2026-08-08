TASK_ID: window-pptx-phase45-architecture-discovery-20260730
ROLE: explorer
TASK_TYPE: discovery
MODALITY: text
OBJECTIVE: Map the exact current production path from TemplateSelectionPlan and
SlideBlueprint through PPTX generation, identify why selected physical/native
candidates are not proven to be materialized, and propose the smallest
fail-closed Phase 45 implementation boundary for V6R-MAT-01.
DELIVERABLE: Evidence-first architecture map with exact files/symbols/callers,
current behavior, missing wiring, two viable designs, recommended design,
tests, risks, and a concrete write-scope proposal.
REVIEW_POINT: current worktree after Phase 44 completion
REVIEW_BINDING: NONE

SOURCE_OF_TRUTH:
- .planning/REQUESTS.md
- .planning/REQUIREMENTS.md
- .planning/ROADMAP.md
- .planning/STATE.md
- skills/owned/window-pptx/SKILL.md
- skills/owned/window-pptx/references/quality-first-v6-workflow.md
- skills/owned/window-pptx/scripts/window_pptx/template_intelligence.py
- skills/owned/window-pptx/scripts/window_pptx/generation.py
- skills/owned/window-pptx/scripts/window_pptx/template_pack_v2.py
- skills/owned/window-pptx/scripts/window_pptx/portable_ooxml.py
- skills/owned/window-pptx/scripts/window_pptx/composer.py
- relevant ownership-aligned tests discovered from imports/callers

ORIGINAL_REQUESTS:
- V6R-MAT-01: production consumes TemplateSelectionPlan and SlideBlueprint;
  every selected physical or registered candidate has exact materializer
  evidence and unknown/unmaterialized choices fail.
- Latest user decision: continue autonomously until all phases complete; stop
  only for genuine user intervention.

ACCEPTED_DECISIONS:
- Phase 44 is complete and supplies a private certified core with 129
  direct-use pages and 159 reference-only pages.
- Reference-only pages have auto_materialize=false and cannot enter automatic
  production.
- The implementation must prove actual physical/native candidate use, not
  merely emit candidate IDs in a manifest.
- Unknown, uncertified, reference-only, or unmaterialized selections fail
  closed.
- No PowerPoint COM dependency is required for Phase 45.

KNOWN_CONTEXT:
- Current selection/blueprint schemas and deterministic planners exist.
- Existing materializers include template_pack_v1_adapter and
  registered_native_renderer.
- Phase 45 must bridge tracked selection contracts to real private candidate
  bytes while keeping private paths/bytes out of tracked artifacts.

REQUIRED_SKILLS:
- cli-agent-delegator: enforce bounded independent discovery and evidence.
- aimagician-superpower: map the active phase goal to implementation and tests.
- window-pptx: apply the owned PPTX production/materialization contract.

ALLOWED_SCOPE:
- Read tracked repository files under .planning and
  skills/owned/window-pptx, plus ownership-aligned tests.
- Use rg, sed, git status/diff, and Python/Node read-only inspection commands.

FORBIDDEN_SCOPE:
- Do not read skills/owned/window-pptx/.private or any credential, Cookie,
  private PPTX, rendered image, or source URL.
- No writes, tests, builds, network, browser, COM, package installation,
  commit, push, reset, clean, stash, or destructive command.
- Do not reopen completed Phase 44 visual decisions.

PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: read-only rg, sed, git status/diff, file listing, and
language-level source parsing without output files.
TESTS_AND_EVIDENCE: Cite exact symbols, callers, schema fields, and existing
test seams. Distinguish fact, inference, and recommendation.
GIT_POLICY: inspect-only
MODEL_POLICY: DeepSeek reasoning default; Agnes only after explicit DeepSeek
usage/quota/rate-limit evidence.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill load, source map, caller trace, design alternatives,
test seam, final report.
STOP_AND_ESCALATE_WHEN: a required skill/source is unavailable, private
inspection is required, or the correct design needs a user decision beyond the
accepted boundary.
SESSION_EXPORT: NONE
OUTPUT_FORMAT:
1. Loaded skills and provider/model/session/attempt chain.
2. Current end-to-end control/data flow with exact symbols.
3. Missing or misleading materialization evidence.
4. Two viable designs and tradeoffs.
5. Recommended contract, invariants, failure semantics, and write scope.
6. Requirement-to-test matrix.
7. Findings and DONE status.

Before substantive work, load every skill named in REQUIRED_SKILLS and report
the loaded skill IDs. Apply their workflows and boundaries. If any required
skill or source cannot be loaded, return NEEDS_CONTEXT; do not improvise.
