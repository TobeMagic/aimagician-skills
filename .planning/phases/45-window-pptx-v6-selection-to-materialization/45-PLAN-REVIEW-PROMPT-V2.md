TASK_ID: window-pptx-v6-phase45-plan-review-v2
ROLE: plan-reviewer
TASK_TYPE: review
MODALITY: text
OBJECTIVE: Challenge the frozen Phase 45 design packet below without repository exploration.
DELIVERABLE: Findings-first APPROVED or NOT_APPROVED review.
REVIEW_POINT: Exact worktree fingerprint supplied by the runner; evidence packet below is complete for this review.
REVIEW_BINDING: --review-worktree /mnt/d/growth_up_youth/repo/skills

SOURCE_OF_TRUTH:
- Embedded evidence packet in this prompt.

ORIGINAL_REQUESTS:
- Continue autonomously until all phases complete and output reaches reference art-direction level.
- Reuse differentiated templates and prove real reuse, not metadata-only selection.

ACCEPTED_DECISIONS:
- Registered-native candidates must bind exact base_variant_id and cannot fall back.
- Physical candidates execute only through the whole-deck lossless TemplatePack adapter.
- Mixed materializers, unknown candidates, incomplete evidence, and drift fail closed.
- Auto mode preserves unsupported-scenario compatibility; explicit selection is strict.
- Arbitrary multi-source OOXML relationship merging is deferred.

KNOWN_CONTEXT:
- Current selection exists only in tests; production generation ignores it.
- PageCandidate contains base_variant_id and physical_slide.
- SlideBlueprint contains physical_slide but drops base_variant_id.
- prepare_brief_generation does not import template_intelligence.
- compile_deck_plan and compile_render_plan resolve layout independently.
- native render may presently fall back from an enforced composition layout.
- automation exposes disconnected BriefPlan native and --render-template-pack physical routes.
- adapt_template_pack is atomic, source-hash checked, exact-inventory checked, and returns source/output digests and slide count.
- three certified spines exist: institutional physical, campus registered-native, academic registered-native.
- schemas exist for selection plan and blueprint.

REQUIRED_SKILLS:
- cli-agent-delegator: frozen independent review discipline.
- aimagician-superpower: requirement traceability and executable-phase review.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. If any required skill cannot be loaded, return NEEDS_CONTEXT. After loading the two skills, DO NOT invoke Read, Grep, Glob, Bash, Web, child agents, or any other tool. The packet below is the only evidence.

EVIDENCE_PACKET:
- Requirement V6R-MAT-01: Production consumes TemplateSelectionPlan and SlideBlueprint; every selected physical or registered candidate has exact materializer evidence and unknown/unmaterialized choices fail.
- GOAL-45-01: production builds/serializes deterministic selection plan and complete blueprints for supported spines.
- GOAL-45-02: registered candidates force exact registered variant; missing/fallback/mismatch fails.
- GOAL-45-03: physical candidates execute through hash-bound TemplatePack adapter with per-slide evidence.
- GOAL-45-04: unknown/uncertified/unmaterialized/reference-only/mixed/drift/incomplete evidence fail; tests and completion audit pass.
- Planned implementation Task 1: add base_variant_id to blueprint; derive locked content-capacity brief; optional validated explicit choices; serialize selection/blueprints.
- Task 2: pass an exact layout-by-slide map into compiler and render plan; exact materializer fields take precedence; no fallback; compare observed RenderSlide.layout_id one-to-one; pre-render is PLANNED, render is PASS.
- Task 3: wrap existing whole-pack adapter; require one physical spine/materializer; validate physical slide mapping; use declared bindings; emit source pack/digest, output digest, output slide, candidate and status for every selection.
- Task 4: write separate selection, blueprint, and materialization JSON artifacts; focused fail-closed tests and regression.
- Compatibility: auto mode skips scenarios without a certified spine; once a spine or explicit choices exist all rules are strict.
- Out of scope: arbitrary multi-source slide graph merging and direct materialization of Phase 44 reference-only pages.
- Invariant: overall PASS only when evidence cardinality and IDs exactly equal selections and every item PASS.

ALLOWED_SCOPE: Embedded packet only.
FORBIDDEN_SCOPE: All filesystem/repository/private/credential/network inspection and all writes.
PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: NONE
TESTS_AND_EVIDENCE: Reason over the packet; map GOAL-45-01..04 and identify missing executable contracts or unsafe claims.
GIT_POLICY: inspect-only
MODEL_POLICY: DeepSeek reasoning default; Agnes quota fallback only.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill load, packet review, finding synthesis, recommendation.
STOP_AND_ESCALATE_WHEN: Any missing decision prevents responsible review; do not fetch it.
SESSION_EXPORT: NONE
OUTPUT_FORMAT: Loaded skills; findings table with severity/evidence/remediation; GOAL-45-01..04 coverage; required plan amendments; final APPROVED/NOT_APPROVED; provider/model/attempt/fallback/session/fingerprint/status.
