# Phase 49: Physical Template Assembly and Work-Report Acceptance - Discussion Log

**Updated:** 2026-08-08

## Decisions

| Topic | Options considered | Decision | Reason |
|---|---|---|---|
| Acceptance tracer | broad scenario suite / one complete tracer | one realistic 15-slide hospital-finance report first | Proves the full chain before expanding breadth |
| Authoring model | weak free model / stronger constrained model | Codex `gpt-5.6-terra` medium | Establish template-level quality before distillation |
| Model authority | arbitrary design code / governed decisions | narrative, candidate IDs, and fact/asset bindings only | Geometry and style remain certified-template authority |
| Template reuse | generated layout fallback / physical reuse | 15/15 physical direct-use lineage | Makes reuse measurable and prevents text-on-cards fallback |
| Source grouping | force 15 packages / allow complete-work reuse | distinct page IDs; shared package allowed when best fit | Preserves coherent style and avoids artificial package duplication |
| COM | mandatory / optional | optional read-only certification | Portable OOXML must deliver independently |
| Rename | compatibility shell / full removal | later flag-day `pptx-studio`; delete `window-pptx` completely | Latest explicit user boundary |

## Assumptions

| Assumption | Status | Evidence or action |
|---|---|---|
| The private library remains locally accessible through configured Skill state during clean-room generation. | Confirmed | USR-V61-01 and existing private-root resolver |
| The 25 MiB work-summary source is the locked size baseline for the replay. | Confirmed | SHA-bound reference inventory and Phase 49 audit |

## Rejected Options

- Treating PptxGenJS/native generated visuals as physical template reuse.
- Searching the clean client folder for private templates.
- Accepting a slide-only relationship check as package integrity.
- Keeping a permanent `window-pptx` compatibility shell after v7 migration.

## Deferred Work

- `pptx-studio` flag-day migration and complete old-name deletion.
- Gaojie Active/Archive/Reject pruning to the approved 97-PPTX target.
- Agnes Deck→Page→Region descriptions and deck/page/component retrieval.
