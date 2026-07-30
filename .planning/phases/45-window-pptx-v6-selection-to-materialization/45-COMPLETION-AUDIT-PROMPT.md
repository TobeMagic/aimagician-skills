TASK_ID: window-pptx-phase45-completion-audit-20260730
ROLE: independent completion auditor
TASK_TYPE: audit
MODALITY: text
OBJECTIVE: Decide whether Phase 45 satisfies V6R-MAT-01 and GOAL-45-01
through GOAL-45-04 from the frozen evidence packet below.
DELIVERABLE: Findings first, exact requirement matrix, APPROVED or
NOT_APPROVED, and DONE or DONE_WITH_CONCERNS.

SOURCE_OF_TRUTH:
- The self-contained FROZEN_EVIDENCE_PACKET below.

REQUIRED_SKILLS:
- cli-agent-delegator
- aimagician-superpower
- window-pptx

PERMISSION_MODE: evidence-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: NONE. Load the required skills, then call no tool.
CHILD_AGENT_POLICY: forbidden
MODEL_POLICY: DeepSeek reasoning default; Agnes only after explicit DeepSeek
usage/quota/rate-limit evidence.
FINDING_SEVERITY: Blocker | Important | Nitpick

EXACT_REQUIREMENT:
- V6R-MAT-01: Production consumes TemplateSelectionPlan and SlideBlueprint;
  every selected physical or registered candidate has exact materializer
  evidence and unknown/unmaterialized choices fail.

EXACT_GOALS:
- GOAL-45-01: Brief generation builds and serializes a deterministic selection
  plan and complete blueprints for supported certified spines.
- GOAL-45-02: Registered-native selections force the exact registered variant;
  missing variants, fallback, or observed mismatch fail closed.
- GOAL-45-03: Physical selections execute only through the hash-bound
  TemplatePack adapter and emit per-slide source/output evidence.
- GOAL-45-04: Unknown, uncertified, unmaterialized, reference-only, mixed
  materializer, drift, and incomplete evidence paths fail; focused and
  regression tests plus fresh independent completion audit pass.

FROZEN_EVIDENCE_PACKET:

- Production brief generation now emits `template-selection-plan.json`,
  `slide-blueprints.json`, and `candidate-materialization-report.json`.
- Every blueprint binds slide ID, spine, candidate, family, materializer,
  governed facts/assets/tokens, and exactly one physical slide or registered
  base variant as appropriate.
- Retrieval hard-matches candidate source mode and materializer to the
  certified spine. Strict sidecar parsers reject schema, field, enum,
  confidence, and physical/base-type drift.
- `registered_layout_bindings` binds the exact `base_variant_id` before deck
  and render compilation. Post-render verification compares every observed
  `RenderSlide.source_id` and layout ID with the expected selection. Missing
  or substituted variants raise stable `MATERIALIZER_*` errors; there is no
  fallback after exact binding.
- `materialize_physical_selection` executes only a uniform
  `template_pack_v1_adapter` plan. It validates pack ID, source SHA-256,
  slide count, physical slide bounds, source integrity, and output creation.
  Every selection emits expected/observed source slide and source/output
  SHA-256 evidence.
- `_uniform_context` rejects incomplete cardinality/order, mixed spines,
  mixed materializers, uncertified or tampered candidates, materializer/source
  mismatch, family/token/fact/asset drift, and reference-only misuse.
- A report begins as `planned`; only the post-render or post-adaptation
  consistency checkpoint may promote it to `pass`.
- A real automation run generated a 9-slide PPTX with SHA-256
  `c12dcb1f9f9d6d8225104b637dd10c64cabe5059f3dbe3cadb7551142d68b483`.
  The materialization report SHA-256 is
  `5ed121658f49a0f7863db3e415806d604e161b0deead1ffd6f9f551f4bb5694c`.
  It reports `pass`, `registered_native_renderer`, and 9/9 exact evidence rows.
  LibreOffice opened/rendered the file and portable OOXML checks passed.
- The tracer's separate quality report flags `TEXT_ONLY_DECK_MONOCULTURE`.
  This is an explicit Phase 46 visual-quality handoff, not concealed evidence:
  Phase 45's locked goal is materialization truth, not reference-grade art
  direction.
- Latest tests after all changes:
  - selection/materialization + template-pack + weak-model generation:
    104 passed;
  - deck-plan and portable regressions: 77 passed;
  - Python compilation: PASS;
  - scoped diff check: PASS.
- A fresh frozen-worktree specification/quality review using Agnes after
  explicit DeepSeek usage limiting returned COMPLIANT with no Blocker or
  Important. Its stable frozen fingerprint is
  `18e17ed9af7a8fcbee53931fdd6167288397ed6bbb79d6bde664f9227fe7e7e1`.

OUTPUT_FORMAT:
1. Loaded skill IDs and provider/model/session/attempt chain.
2. Findings first, with Blocker/Important/Nitpick.
3. Exactly one PASS|FAIL|NOT_RUN row for V6R-MAT-01 and GOAL-45-01..04.
4. APPROVED or NOT_APPROVED.
5. DONE or DONE_WITH_CONCERNS.

Reason only from this packet after loading the required skills.
