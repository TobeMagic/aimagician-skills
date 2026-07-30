# Phase 45 Discussion Log

**Status:** Accepted for implementation

## Decisions

| Decision | Resolution |
|---|---|
| What counts as materialized? | Exact observed native layout or exact physical source slide in a verified adapted package; planning metadata alone does not count. |
| Can native rendering silently fall back? | No. A selected registered variant must render exactly or fail. |
| Can physical and native candidates mix? | No. The current engines cannot preserve that claim safely. |
| Can private reference-only pages auto-select? | No. They require content replacement and remain outside direct materialization. |
| Must unsupported scenarios break existing callers? | No. Auto mode selects only certified spines; explicit choices or a selected spine are strict. Phase 47 expands scenario coverage. |
| How is pre-render compilation represented? | `planned`, never `pass`; only rendered/adapted output can produce PASS evidence. |

## Assumptions

- The three current certified spines are the Phase 45 production scope.
- Existing unsupported scenarios remain compatible in auto mode.

## Rejected Options

- Claim selection IDs as materialization evidence.
- Permit renderer fallback after an exact registered choice.
- Copy arbitrary private slides without relationship-graph validation.

## Deferred Work

- Registering the Phase 44 direct-use private core as executable packs.
- Safe arbitrary multi-source OOXML slide merging.
