TASK_ID: window-pptx-v6-phase45-spec-quality-review
ROLE: spec-reviewer
TASK_TYPE: review
MODALITY: text
OBJECTIVE: Independently verify Phase 45 implementation against V6R-MAT-01 and identify correctness or integration defects before phase closure.
DELIVERABLE: Findings-first specification and quality review with COMPLIANT or NOT_COMPLIANT.
REVIEW_POINT: Exact current worktree bound by the runner.
REVIEW_BINDING: --review-worktree /mnt/d/growth_up_youth/repo/skills

SOURCE_OF_TRUTH:
- .planning/phases/45-window-pptx-v6-selection-to-materialization/45-SPEC.md
- .planning/phases/45-window-pptx-v6-selection-to-materialization/45-01-PLAN.md
- skills/owned/window-pptx/scripts/window_pptx/template_intelligence.py
- skills/owned/window-pptx/scripts/window_pptx/selection_materialization.py
- skills/owned/window-pptx/scripts/window_pptx/generation.py
- skills/owned/window-pptx/scripts/window_pptx/deck_plan.py
- skills/owned/window-pptx/scripts/window_pptx/render_plan.py
- skills/owned/window-pptx/scripts/window_pptx/cli.py
- skills/owned/window-pptx/scripts/window_pptx_automation.py
- skills/owned/window-pptx/schemas/slide-blueprint.v1.schema.json
- skills/owned/window-pptx/schemas/candidate-materialization-report.v1.schema.json
- tests/window_pptx/test_template_intelligence.py
- tests/window_pptx/test_template_pack.py
- tests/window_pptx/test_weak_model_generation_pipeline.py

ORIGINAL_REQUESTS:
- Continue autonomously through all phases and prove real differentiated-template reuse.
- Decks require directory and section pages; metadata-only template labels are unacceptable.

ACCEPTED_DECISIONS:
- Registered candidates bind exact base_variant_id; fallback/mismatch fails.
- Physical candidates use the lossless whole-pack adapter with selection sidecars.
- One materializer per plan; unknown, drift, tamper, mixed, and incomplete evidence fail.
- Auto mode preserves unsupported scenarios; explicit required mode is strict.
- Arbitrary multi-source OOXML merging is deferred.

KNOWN_CONTEXT:
- Production tracer passed with 9/9 expected variants equal observed layouts.
- Tracer PPTX SHA-256 c12dcb1f9f9d6d8225104b637dd10c64cabe5059f3dbe3cadb7551142d68b483.
- Materialization report SHA-256 5ed121658f49a0f7863db3e415806d604e161b0deead1ffd6f9f551f4bb5694c.
- Focused tests: template intelligence 18 passed; weak-model generation 76 passed; template pack plus template intelligence 28 passed; deck/template/portable regressions 86 passed.
- Visual art-direction acceptance is Phase 46; this review concerns truthful selection/materialization and anatomy integration.

REQUIRED_SKILLS:
- cli-agent-delegator: frozen independent review protocol.
- aimagician-superpower: requirement traceability and phase correctness.
- window-pptx: domain contracts for editable PPTX, templates, and portable production.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. If any required skill or named source cannot be loaded, return NEEDS_CONTEXT. Use only Read on the exact SOURCE_OF_TRUTH files. Do not use Bash, Grep, Glob, Web, child agents, or read any other file.

ALLOWED_SCOPE: Exact SOURCE_OF_TRUTH files with Read only.
FORBIDDEN_SCOPE: .private, credentials, cookies, URLs, downloads, Phase 43/44 unrelated files, all writes, all commands, broad searches, network, git mutation.
PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: NONE
TESTS_AND_EVIDENCE: Inspect tests and code; map GOAL-45-01..04; challenge parser tampering, materializer uniformity, native fallback, physical pack matching, artifact timing, anatomy compatibility, schema truth, and regression claims.
GIT_POLICY: inspect-only
MODEL_POLICY: DeepSeek reasoning default; Agnes quota fallback only.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill load, exact-file reads, requirement trace, quality challenge, recommendation.
STOP_AND_ESCALATE_WHEN: Any required evidence needs a forbidden file or tool.
SESSION_EXPORT: NONE
OUTPUT_FORMAT: Loaded skills; findings table with severity/path/symbol/evidence/remediation; GOAL-45-01..04 PASS/FAIL/NOT_RUN; test-evidence assessment; assumptions; final COMPLIANT/NOT_COMPLIANT; provider/model/attempt/fallback/session/fingerprint/status.
