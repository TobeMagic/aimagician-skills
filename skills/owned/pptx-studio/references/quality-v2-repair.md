# Quality Report v2 and Bounded Repair

## Inspection namespaces

QualityReport v2 merges findings from:

1. `input`: schema, facts, citations, brand/assets.
2. `narrative`: required facts, critical beats, story order, action titles.
3. `compile`: capacity, semantic mapping, asset fallback, layout decision.
4. `render`: COM objects, geometry, data fidelity, fonts, links.
5. `preview`: overflow, hierarchy, whitespace, crop, repetition, anti-slop.
6. `package`: OOXML openability, slide size/count, PDF, transaction/source integrity.
7. `editability`: native objects, tags/names, charts/tables/diagrams, raster coverage.

Severity order is hard-gate, critical, important, warning, info. Findings deduplicate by namespace/code/slide/object-or-path; the higher severity wins. Output order is deterministic.

Required checks include overflow, minimum font size, bounds, overlap drift, alignment/margins, density/emptiness, image aspect, chart/table labels, repeated page families, theme/title hierarchy, placeholder content, package openability, editability, and font compatibility. On the production BriefPlan route, the expected per-slide PNG preview set must exist and be readable before save; missing, unreadable, or unavailable preview inspection is a hard gate.

## Two stages only

Pre-render may run once. It may split content, choose a compatible lower-density variant, downgrade a missing image to native composition, or choose the safe art direction. It cannot change facts, numbers, units, citations, user wording, sources, or language.

Post-render may run once for repairable COM/geometry/text issues. The weak-model route limits the existing structural repair engine to one pass.

Before each stage, deep-snapshot state. Accept a repair only if the defect vector strictly improves lexicographically:

```text
(hard-gates, critical, important, warning, weighted-score)
```

Rollback on exceptions, canonical protected-content change, fact-digest change, or non-monotonic output. The protected digest retains facts, numbers, units, citations, user text, and sources while excluding only registered visual fields, so copying an old digest cannot conceal content mutation. A failed candidate is never promoted.

After the candidate is saved, the transaction reopens it with macros disabled and repeats semantic/editability inspection against the RenderPlan before atomic promotion. Text, object tags, native chart/table/diagram data, and editable-object coverage must survive serialization. `reopened-content-validation` is a required package step, and the runner accepts that evidence only when its own validator callback actually ran. Package/source-integrity and reopened-content failures remain hard gates even when visual scores are good.

Expected audit artifacts:

- `narrative-plan.json`
- `direction-decision.json`
- `generation-manifest.json`
- `quality-report.json` and `repair-log.json` (legacy COM-compatible view)
- `quality-report.v2.json` (cross-stage view)
- per-slide quality-v2 PNG previews for every production Brief render
