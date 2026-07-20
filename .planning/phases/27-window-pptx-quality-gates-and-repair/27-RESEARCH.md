# Phase 27 Research: Measurable Candidate Quality

## Failure Classes

| Layer | Deterministic checks |
|---|---|
| Package | candidate promotion state, OOXML validation, macro-disabled reopen, PDF evidence, source-hash equality |
| COM | slide/object counts, expected native chart/table/diagram coverage, names/tags, editable coverage, page setup |
| Geometry | bounds, governed coordinates, overlap policy, minimum font, estimated text capacity, image aspect |
| Visual | occupied-area balance, label readability, blank-series handling, full-slide raster detection, preview ratio |
| Deck | title hierarchy, theme/font consistency, repeated families/layouts, pacing, findings by slide |

## Stable Scoring

- `critical`: 100 points and a customer-delivery hard gate.
- `error`: 25 points; hard only for registered safety/editability codes.
- `warning`: 5 points.
- `info`: 0 points.

A candidate passes only when every registered hard gate passes. A repair pass is accepted only when the weighted defect score decreases and the hard-gate failure set does not grow. At most two repair passes are allowed.

## Safe Repair Boundary

Allowed: restore page size, expected object bounds, governed font attributes, object names/tags, and editable flags where the native object already exists.

Forbidden: rewrite user content, remove slides, replace native charts/tables with images, add unknown assets, invent data, suppress a finding without changing evidence, mutate a source/final file, or accept a lower score with a new hard-gate regression.

## Reports

`quality-report.v1` contains layer snapshots, stable findings, weighted score, hard-gate state, and transaction evidence. `repair-log.v1` contains every proposed/applied/rejected action, before/after scores, hard-gate deltas, pass limit, and rollback result.
