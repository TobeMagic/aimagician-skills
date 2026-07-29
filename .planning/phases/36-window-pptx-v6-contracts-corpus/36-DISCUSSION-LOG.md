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
