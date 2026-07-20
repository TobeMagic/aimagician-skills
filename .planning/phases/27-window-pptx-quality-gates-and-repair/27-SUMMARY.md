# Phase 27 Summary: Quality Gates and Repair

**Status:** Complete
**Completed:** 2026-07-20

## Delivered

- A deterministic five-layer inspection model for package, COM/editability, geometry, visual quality, and deck consistency.
- Stable versioned `quality-report.v1` and `repair-log.v1` schemas with severity weights, hard-gate codes, layer metrics, repair passes, and failure codes.
- Fail-closed checks for package/reopen evidence, source integrity, slide/object coverage, native chart/table/diagram data, editability tags, text content and overflow, bounds, overlap, placeholder content, full-slide rasterization, density, and repeated layouts.
- Candidate-only structural repairs for page size, geometry, fonts, names, and tags, capped at two passes and accepted only for monotonic weighted improvement without new hard gates.
- Whole-candidate in-memory snapshots, deterministic compound-action ordering, exception-safe rollback, and delivery blocking when a repair remains unresolved.
- Transaction-aware hard gates both before save and after package validation, with atomic audit artifacts attached to `QualityGateError`.
- A useful native visual-summary fallback in place of the former low-quality “Visual asset unavailable” placeholder.

## Evidence

The Phase 27 quality pipeline suite passes 19/19 and the complete window-pptx suite passes 404/404. Python compilation, JSON syntax checks, and diff checks pass. Implementation commit: `954d8ad`.

Fault-injection coverage proves missing native objects stop before save, invalid transaction evidence stops after save, chart value/category drift fails closed, table dimensions and diagram labels are checked, compound name/tag/geometry repair remains target-safe, and COM write failures roll back.

OpenCode read-only review was attempted across multiple ordinary free models. The sessions read the relevant implementation but the provider repeatedly ended after tool steps without returning a textual audit verdict. This is recorded as infrastructure evidence rather than converted into a false PASS; the final independent audit remains mandatory in Phase 29.

## Boundary

Phase 28 now owns the frozen fifteen-scenario, three-arm, two-ordinary-model benchmark and before/after evidence. Real Windows PowerPoint quality behavior, canonical artifacts, ten-run reliability, and the final OpenCode verdict remain Phase 29 gates.
