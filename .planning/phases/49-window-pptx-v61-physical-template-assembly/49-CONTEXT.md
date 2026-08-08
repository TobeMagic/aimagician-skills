# Phase 49: Physical Template Assembly and Work-Report Acceptance - Context

**Updated:** 2026-08-08
**Specification:** `49-SPEC.md`

## Locked Requirements

- V61-LIB-01, V61-SEL-01, V61-ASM-01, V61-ADAPT-01, V61-QA-01,
  V61-CLEAN-01, V61-REL-01. `49-SPEC.md` is normative.

## Project Context Intake

| Source ID | Path | Policy | Read result | Conflict or assumption |
|---|---|---|---|---|
| SRC-STATE | `.planning/STATE.md` | MUST_READ | v6.1 / Phase 49 active | NONE |
| SRC-PROJECT | `.planning/PROJECT.md` | MUST_READ | physical assembly is the active milestone | NONE |
| SRC-CONTEXT | `.planning/CONTEXT.md` | MUST_READ | direct-use and owner-relative OPC invariants adopted | NONE |
| SRC-ROADMAP | `.planning/ROADMAP.md` | MUST_READ | GOAL-49-01 through GOAL-49-06 | NONE |
| SRC-REQUIREMENTS | `.planning/REQUIREMENTS.md` | MUST_READ | seven v6.1 requirements mapped to Phase 49 | NONE |
| SRC-PHASE | `49-SPEC.md` | MUST_READ | locked contract and blockers | NONE |

- Read the most recent relevant checkpoint first for orientation.
- Resolve conflicts by authority, not filesystem time or document recency.
- Stop and discuss material uncertainty before implementation.

## Implementation Decisions

- Keep the v6.1 public APIs stable while correcting their behavior.
- Add one assembly-wide import context and one cached context per source
  package; relationship resolution is always relative to the current owner.
- Share same-source static dependencies and only cross-deduplicate explicitly
  safe immutable binary or relationship-free parts.
- Preserve source eligibility in the page record; query defaults exclude
  non-direct-use candidates.
- Keep clean-room generation outside the repository and private library bytes
  outside the client folder.

## Existing Patterns To Preserve

- Content-addressed private source identity and ignored `.private/` boundary.
- Native OOXML editability, source immutability, atomic output, and fail-closed
  security checks.
- Existing CLI and schema compatibility for the checkpoint while Phase 49 is
  stabilized.

## Allowed Scope

- Phase 49 planning/evidence.
- v6.1 page-library, physical-assembly, rule-QA, CLI/schema, and focused tests.
- External clean requirement pack and ignored acceptance artifacts.

## Forbidden Scope

- Credentials, cookies, private PPTX bytes, or generated reviewer images in
  Git.
- v7 rename/removal, destructive asset pruning, unrelated Skillbird changes,
  arbitrary native-renderer fallback, or mandatory COM.

## Integration And Compatibility

- `compile_page_templates`, `query_page_templates`,
  `assemble_physical_deck`, and `verify_physical_assembly` remain stable entry
  points.
- Existing v5/v6 historical artifacts remain readable; new evidence is
  prospective and does not rewrite closed audits.
- Delivery class is non-deployable source/install synchronization; postmerge
  online deployment is `N/A`, but merge/push and installed digest parity are
  required.

## Expected Project Context Promotion

- `PROMOTE CTX-PPTX-001` and `CTX-PPTX-002` after final implementation and
  evidence confirm the direct-use and owner-relative OPC contracts.
