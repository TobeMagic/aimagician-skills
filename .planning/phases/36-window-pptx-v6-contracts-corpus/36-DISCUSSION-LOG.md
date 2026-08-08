# Phase 36: v6 Contracts and Realistic Corpus - Discussion Log

**Updated:** 2026-07-29

## Decisions

| Topic | Options considered | Decision | Reason |
|---|---|---|---|
| v6 author | Ordinary model first; Agnes first; GPT-5.5 first | GPT-5.5 medium first | Prove the Skill can reach the reference before distillation |
| Corpus | Reuse shallow v5; private customer data; realistic synthetic packs | Three complete synthetic flagships plus twelve skeletons | Reproducible, detailed, safe, and comparable |
| Brief gate | Advisory completeness; strict state machine | Draft → NeedsDiscussion → Locked | Prevent design from starting on unresolved content |
| Template use | Pure rules; direct copy only; hybrid | Complete-work spine plus certified components/rules | Combines art direction with semantic adaptability |
| Acquisition | Commit originals; external cache; Skill-local private library | Skill-local `.private` library | Single-user operation without repository leakage |
| COM | Mandatory certification; optional; remove entirely | Optional diagnostics only | Portable delivery already covers the canonical path |
| Review | Human; one AI; three independent AIs | Three independent AI-only contexts | Latest explicit user instruction |
| Repair | Extend heuristics; bounded correction/reselection/replan | Bounded three-stage loop | Prevent redundant accumulated fixes |

## Assumptions

| Assumption | Status | Evidence or action |
|---|---|---|
| The accepted work-summary reference is authorized for local analysis and adaptation | Accepted | Existing Phase 30–31 provenance and user direction |
| Commercial template access does not imply redistribution rights | Confirmed | Rights evidence remains a per-artifact release gate |
| A new short-lived cookie will be supplied privately only when Phase 37 reaches auth | Pending external precondition | Non-auth work continues as planned |

## Rejected Options

- Model-authored HTML as the canonical PPTX source.
- Mandatory PowerPoint COM for daily generation.
- Unlimited auto-repair.
- Treating DeepSeek code/contract review as visual inspection.
- Releasing with fewer than three preflighted blind reviewers.

## Deferred Work

- Weak-model distillation and trace-specific training infrastructure move to
  v6.1 after v6.0 GO.

## Implementation Checkpoints

### 2026-07-29 — Brief lock and corpus tracer

- Commit `072e8a7` established the v6 planning contract, ignored private root,
  staged secret/binary guard, ProjectBriefPack v1 schema/state/digest boundary,
  and atomic management CLI.
- The corpus implementation now builds exactly fifteen locked packs: three
  full flagships and twelve realistic scenario skeletons. Every pack has at
  least eight quantitative facts, three material roles, a decision, timing,
  slide budget, mandatory cover/directory/section/closing/appendix anatomy,
  prohibitions, rubric, and stable lock.
- Academic dataset metadata cites the public DCRNN paper; every MDGFormer
  comparison, variance, ablation, robustness, and efficiency value is labeled
  as standardized synthetic experiment evidence.
- Focused evidence: ProjectBriefPack, corpus, and safety tests pass `17/17`;
  all fifteen packs also pass the Draft 2020-12 JSON Schema and formal-lock
  validation.

### 2026-07-29 — Archived regression repair

- Required generated proposal bookend imagery now selects registered
  `cover.poster-editorial` / `cta.poster-editorial` layouts instead of being
  materialized and then reported as unused.
- `cta.decision-three` parses one proof line plus exactly three decision chips
  without losing source text. A single grounded action falls back to
  `cta.top-band` or an image-led single CTA; it never fabricates empty cards.
- Prose-only directional motifs use `BASELINE` consistently and still remain
  native editable without invented chart series.
- All three archived failures pass. Their owning composition,
  asset-materialization, and core-renderer modules pass `80/80`; the complete
  portable calibration module passes `11/11`.

### 2026-07-29 — Phase verification checkpoint

- The complete Window-PPTX Python regression passes `813/813` in three
  deterministic shards: `491 + 146 + 134`, including the `42/42` weak-model
  benchmark.
- The final v6 contract/safety/brief/corpus slice passes `22/22`.
- Root Vitest passes `108/108`; typecheck, build, Skillbird formatting,
  behavior-eval JSON parsing, workflow spec/plan/execute gates, and diff checks
  pass.
- This is Phase 36 engineering evidence only. Private acquisition,
  TemplatePack v2, flagship PPTX generation, and three-context visual UAT
  remain later-phase work and are not inferred as complete.
