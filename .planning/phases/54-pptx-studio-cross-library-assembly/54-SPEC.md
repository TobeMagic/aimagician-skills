# Phase 54: Cross-Library Component Assembly and PowerPoint Compatibility — Specification

**Created:** 2026-08-14
**Milestone:** v7 PPTX Studio Curated Composition
**Roadmap phase:** 54
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Requirements:** 3
**Requirement IDs:** V7-MIX-01, V7-POWERPOINT-01, V7-REPLAY-01

## Goal

Advance from a successful fixed-deck rebinding regression to a

## Background

The roadmap goal continues: genuinely flexible, senior-designer-like assembly
selects coherent whole pages and certified visual components from many curated
private source packages, retains native editability, and proves the exact
output opens in PowerPoint as well as portable renderers.

`pptx-studio` must derive the client deck from narrative beats through bounded
model decisions; the compiler owns geometry, style, physical assembly and
repair.

## Requirements

### V7-MIX-01: Narrative-derived mixed-library reuse

- **Source requests:** USR-V7-02
- **Current:** The fixed work-report replay proves same-source text/data
  rebinding, but not multi-package designer-like assembly. It can preserve a
  reference sequence that has no business purpose in the new brief.
- **Target:** Introduce a narrative beat/page-rationale contract, anchor-style
  selection, bounded page/component retrieval and governed mixed assembly.
- **Acceptance:** Every delivery page has `page_intent`, `key_message`, facts,
  grammar and a merge/split rationale. For a substantive 10+ page result, at least six
  source packages and five categories contribute physical lineage, with no
  source supplying more than four full pages.

### V7-POWERPOINT-01: Real PowerPoint-compatible physical assembly

- **Source requests:** USR-V7-02
- **Current:** LibreOffice displayed a deck whose dangling source tags caused
  blank PowerPoint slides. Same-source v57 recovery proved that source-native
  relationship/master topology renders visibly in PowerPoint.
- **Target:** Make the importer and verifier detect/rewrite every owned
  relationship reference and reject unsafe/cross-package structures before
  delivery.
- **Acceptance:** Tags fixtures are repaired or rejected; page/component
  fixtures and the final exact artifact visibly render and remain editable in
  PowerPoint's main canvas, not merely in a thumbnail or LibreOffice render.

### V7-REPLAY-01: Version-safe selection and assembly replay

- **Source requests:** USR-V7-02
- **Current:** Recompiling an old selection plan can change component bindings
  after catalog/preflight/compiler evolution.
- **Target:** Pin schemas, catalog observations, preflight, component grammar,
  adapter and compiler in every selection/assembly plan.
- **Acceptance:** A matching environment replays byte-stably; any mismatch
  fails with a stable migration report, never a silently altered deck.

## Implementation Tracks

1. **Curated visual index.** For every active package/page, retain an Agnes
   observation bound to a rendered image hash. Store deck-level family,
   palette, industry, density and tone; page-level role/grammar/capacity; and
   component-level semantic intent, member set, capacity, relative placement,
   style signature and allowed adaptations. Retrieval returns a shortlist,
   never raw private paths or hundreds of items.
   Apply the final hash-bound `certified-core` disposition as a deterministic
   catalog overlay: a matching `deny` page is blocked from retrieval through
   physical assembly, and runtime rejects a catalog whose certification digest
   no longer matches the ledger.
2. **Composition contract.** The agent first emits a narrative beat ledger,
   then derives the number of pages. Every resulting page records the audience
   decision it enables, a one-sentence key message, facts it owns, expected
   information density, chosen grammar and merge/split rationale. A section
   divider must be followed within two pages by evidence that belongs to that
   section; otherwise it is merged, replaced or removed. The agent then emits
   a style anchor, role sequence, bounded candidate IDs, selected page IDs,
   selected component IDs and locked fact/asset IDs. A deterministic scorer
   enforces role, capacity, semantic, style, editability and asset
   compatibility. It rejects forced filler, unexplained pages, and—where the
   resulting brief has 10+ pages—a mixed deck that violates the
   6-package/5-category/4-page maximum guard. A narrative merge cannot reduce
   a multi-page business deck from 12 to 11 pages to escape this boundary.
3. **Physical component importer.** Import a page or integrity-preserving
   component closure recursively. Preserve native text/shapes/charts/media;
   rewrite all targets; deduplicate only byte-identical safe dependencies;
   reject macro/OLE/script/file targets. Do not decompose a certified visual
   group into arbitrary shapes.
4. **Compatibility sanitization.** When source authoring `tags` metadata is
   discarded, remove its relationship and all `p:custDataLst/p:tags` rId
   references. The recursive verifier treats any remaining rId as a hard
   defect. Add equivalent explicit handling for any future discarded metadata
   type rather than silently filtering it.
5. **Replay/version contract.** Persist catalog, observation, preflight,
   component grammar, adapter and compiler digests in the plan. Replaying a
   stale plan either uses the pinned compatible compiler or emits a stable
   migration report; it must not reinterpret component keys.
6. **Acceptance harness.** Run ZIP/OPC closure/editability/overflow/overlap/
   density/style/lineage checks, then real PowerPoint open/render on the exact
   SHA when available, plus three independent anonymized visual reviews.

## Acceptance Scenarios

Create a fresh `某市中心医院 2026 年财务运营数智化升级项目立项汇报` requirement pack with no requested slide count. The agent must propose
the count from the brief and show its beat ledger. The needed grammar is likely
to include cover, directory, section dividers, executive view, KPI/data story,
roadmap, process, business model, product/mockup, team, risks, quote and
closing, but pages are added, combined or removed only when the facts and
decision flow justify it. If the resulting deck has 10+ pages, it must use
distinct certified assets from at least six packages and five categories,
with an anchor style family covering at least 70% of weighted visual surfaces.

Then create a separate clean academic-defense pack with a complete research
question, methods, governed evidence, findings, limitations and defense
decision, again with no reference PPTX and no requested slide count. It must
use the same narrative, certified retrieval, native binding, replay and QA
contracts while selecting an academic-appropriate style cluster. Reusing the
professional-report output or merely changing its text is not acceptance.

## Exit Gates

- all source/part/component lineage is complete and physical;
- no package violates contribution limit, and no non-certified component is
  selected;
- no dangling internal rIds or stripped-metadata references exist;
- target opens visibly in PowerPoint and LibreOffice, with editable native
  elements; and
- both professional-report and academic-defense cases pass the harness;
- three fresh blind reviewers per final exact artifact plus an independent
  audit return GO with no Blocker/Important.

## Boundaries

### In Scope

- Narrative-derived page count, page-rationale validation, staged template and
  component retrieval, cross-package physical assembly, safe slot adaptation,
  version-pinned replay and the exact-artifact PowerPoint gate.
- A new clean client-only hospital-finance digital-upgrade proposal whose
  number of pages is intentionally unspecified.
- A separate clean academic-defense brief with complete source-grounded
  research content and an independently derived narrative/page count.
- Private local catalog/observation/index changes and tests, while keeping all
  commercial bytes/previews outside Git and outside the client folder.

### Out Of Scope

- Treating the historical whole-deck replay as a production-design acceptance,
  public redistribution of Gaojie source packages, or client-folder access to
  private templates.
- Freeform model-authored geometry/style/OOXML/code, raster/HTML visual
  fallback, self-scored release, mandatory COM for daily production, or manual
  post-assembly visual patching.

## Constraints

- `gpt-5.6-terra` at medium reasoning is the first acceptance author. It may
  select bounded IDs and bind supplied facts/assets, but cannot author layout
  primitives or release decisions.
- One dominant anchor style family is mandatory. A compatible fallback must be
  catalogued and justified; random visual mixing is prohibited.
- Private source locators, bytes, commercial credentials and rendered previews
  never enter tracked output, external prompts or the clean client pack.
- A final file must pass recursive OPC safety/closure, native editability and
  real PowerPoint main-canvas evidence. LibreOffice is supporting evidence.

## Engineering Contract

- **Inputs:** `brief.normalized.json`, `narrative-plan.json`, bounded catalog
  query results, `selection-plan.json` and approved client assets.
- **Owners:** the agent owns facts, narrative beats, candidates and bindings;
  the compiler owns scoring, geometry, style tokens, physical import, repairs
  and reports; the harness owns validation and release eligibility.
- **Versioning:** every plan records schema, catalog, observation, preflight,
  component-grammar, adapter and compiler digests. An unmatched digest fails
  with a migration report, not a reinterpretation.
- **Failure semantics:** an unexplained page, orphan divider, capacity breach,
  unapproved source, unsafe/dangling relationship or absent PowerPoint evidence
  is a named blocking failure and no delivery is emitted as accepted.

## Acceptance Criteria

- [ ] AC-54-01 (V7-MIX-01): A no-count clean client brief produces a valid,
  deterministic page-rationale ledger. Every page has intent/key message/facts/
  grammar, and an orphan section or empty beat fails validation.
- [ ] AC-54-02 (V7-MIX-01): The selection plan locks an anchor style family,
  returns only bounded candidate IDs, and for a substantive 10+ page delivery proves six
  packages, five categories, four-page maximum/source and complete lineage.
- [ ] AC-54-03 (V7-POWERPOINT-01): Recursive relationship checks repair or
  reject `custDataLst/tags` and equivalent discarded metadata; fixtures cover
  charts, workbooks, styles, masters/layouts and unsafe targets.
- [ ] AC-54-04 (V7-POWERPOINT-01): The final exact-SHA PPTX visibly renders on
  PowerPoint's main canvas and remains editable; LibreOffice-only evidence is
  rejected.
- [ ] AC-54-05 (V7-REPLAY-01): Matching versions replay byte-stably;
  mismatched plan/catalog/preflight/adapter/compiler versions emit a stable
  migration report and cannot assemble silently.
- [ ] AC-54-06 (V7-MIX-01, V7-POWERPOINT-01, V7-REPLAY-01): Three independent
  anonymous visual reviews and a fresh audit see the exact delivered artifact,
  return no Blocker/Important, and their evidence binds to the final SHA.
- [ ] AC-54-07 (V7-MIX-01): One clean professional-report brief and one
  independent clean academic-defense brief both complete the same governed
  Skill workflow and achieve template-standard visual acceptance; neither may
  use a client-supplied reference PPTX or inherit the other case's plan.

## Blocking Questions

- None.

The user has explicitly approved a private local curated library, the
`pptx-studio` production identity, bounded model decision authority,
PowerPoint as a release gate, and narrative-derived page count.

## Ambiguity Report

- **Goal clarity:** 0.95
- **Boundary clarity:** 0.93
- **Constraint clarity:** 0.94
- **Acceptance clarity:** 0.93
- **Ambiguity:** 0.07

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | Product | Is a 15-page reference a production page-count constraint? | No. It is regression-only; final count derives from validated narrative beats. |
| 2 | Story | May a divider be followed by another title-only page? | No. It needs owned evidence within two pages or is merged/replaced/removed. |
| 3 | Design | Can the agent freely draw slides when a template does not fit? | No. It selects bounded certified page/component IDs; compiler-owned safe adaptation is the only change surface. |
| 4 | Compatibility | Does LibreOffice rendering prove delivery compatibility? | No. Real PowerPoint main-canvas rendering of the exact SHA is mandatory. |
| 5 | Replay | May a new compiler reinterpret historical component keys? | No. It must use matching digests or produce a migration report and fail closed. |
| 6 | Coverage | Is one successful professional report enough for the active goal? | No. Academic defense is a separate clean acceptance case using the same governed Skill. |
