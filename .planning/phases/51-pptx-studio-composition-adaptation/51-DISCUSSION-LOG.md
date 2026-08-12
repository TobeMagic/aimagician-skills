# Phase 51: Discussion Log

**Updated:** 2026-08-12

## Decisions

| Topic | Options considered | Decision | Reason |
|---|---|---|---|
| reuse hierarchy | free per-slide selection; fixed whole-deck; governed three modes | exact-deck → page → explicit component | maximizes template fidelity while preserving flexible assembly |
| style control | model color prompt; inferred similarity; anchor plus explicit derived signatures | anchor/style-signature lock | model cannot silently drift visual direction |
| text content | free text in plan; fact IDs only | fact IDs only | makes content provenance and capacity checks mechanical |
| implementation | mutate PPTX now; emit plan only | emit plan only | preserves a testable boundary before physical assembly |

## Assumptions

| Assumption | Status | Evidence or action |
|---|---|---|
| catalog source IDs resolve to a later materializer locator | Locked | Phase 50 catalog contract and v6.1 private physical importer |
| style signatures can be derived from public-safe catalog/observation fields | To validate | focused synthetic and local smoke tests |
| all client facts/assets are locked before plan compilation | Locked | later Skill workflow requires brief lock |

## Rejected Options

- A model-created component geometry layer: violates the user objective to
  turn creative execution into governed reusable capability.
- Automatic fuzzy style fallback: makes visual compatibility non-repeatable.
- Directly extending legacy `window_pptx` selection APIs: creates migration
  debt before `pptx-studio` is ready.

## Deferred Work

- Actual cross-package import and target-slot replacement.
- Final visual/structural repair and clean-room client acceptance.
