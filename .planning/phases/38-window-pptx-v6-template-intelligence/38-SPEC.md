# Phase 38: Certified Template Intelligence - Specification

**Created:** 2026-07-30
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Depends on:** Phase 37 `SEED_READY`; authenticated commercial sync may continue independently
**Requirements:** 3

## Goal

Turn the existing disconnected layout registries, Catalog v3, ArtDirection
profiles, and single authorized TemplatePack v1 into one certified selection
system that can plan complete reference-grade decks without asking a model to
invent coordinates, styles, OOXML, or repair code.

Phase 38 is successful only when a locked brief can produce a deterministic,
explainable `TemplateSelectionPlan` and per-slide `SlideBlueprint` from a
certified 60–100-candidate pilot library anchored by three legally usable
complete-work visual spines.

## Background

Phase 37 established safe acquisition, quarantine, rights records, Catalog v3,
stable IDs, dependency closure, and certified-only query. It deliberately did
not connect the catalog to generation.

The current runtime still has four disconnected surfaces:

- 110 registered layout variants with no certification or complete-work
  context;
- twelve v1 art-direction profiles that do not encode a complete deck motif,
  page choreography, or reference evidence;
- one authorized 15-slide physical TemplatePack v1 that can adapt fixed
  text/chart slots but cannot participate in semantic retrieval;
- four legacy templates that remain `legacy_unverified` and must never
  auto-select.

The user-accepted `工作总结.pptx` is already packaged in the Skill with explicit
authorization. Its source file and packaged TemplatePack are byte-identical:
SHA-256 `59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839`.
It contains 15 slides, one master, three layouts, 29 media objects, and four
editable charts. It therefore supplies a legal work-report visual spine and a
pixel-level art-direction baseline, not merely an external inspiration image.

## Requirements

### V6-LIB-01: Certified, Queryable Template Intelligence

- **Source requests:** USR-V6-01, USR-V6-05, USR-V6-06
- **Current:** Catalog v3 can safely query packages, but layout variants,
  complete-work spines, TemplatePack v1, design packs, and legacy items are not
  joined by a selection API.
- **Target:** Registry v3 is an additive expand-contract facade over Catalog
  v3, layouts, components, themes, design packs, art directions, composition
  grammars, narrative rules, TemplatePack v1/v2, and legacy metadata. It
  exposes stable page-candidate and spine IDs, certification, capacity,
  semantic fit, deck/style family, dependencies, materialization route, and
  deterministic retrieval.
- **Acceptance:** old loaders and fields keep their behavior; exactly 60–100
  certified pilot page candidates are queryable; uncertified catalog and
  legacy entries never auto-select; dependency, rights, capacity, family, and
  materializer gates fail closed.

### V6-DESIGN-01: Bounded Model-Led Selection

- **Source requests:** USR-V6-01, USR-V6-02, USR-V6-06, USR-V6-07
- **Current:** v1 direction selection and deterministic layouts can create
  structurally valid but visually shallow decks. A model is either too
  constrained to improve art direction or is asked to make unsafe open-ended
  design choices.
- **Target:** GPT-5.5 medium receives a locked brief, fact IDs, asset roles,
  deck anatomy, and a small certified candidate set. It may choose stable
  spine/candidate IDs, bindings, importance, and evidence-bound rationale. A
  deterministic validator owns capacity, family compatibility, dependencies,
  factual grounding, and the final blueprint.
- **Acceptance:** unknown IDs, uncertified items, raw coordinates, shape IDs,
  OOXML paths, HTML, code, font/color overrides, unsupported claims,
  unbound facts, capacity violations, cross-family drift, and undeclared
  fallback fail. Low-confidence or no-fit choices resolve to a registered safe
  default or explicit `NO_FIT`, never an arbitrary layout.

### V6-DECK-01: Complete-Work Art Direction And Rhythm

- **Source requests:** USR-V6-04, USR-V6-06, USR-V6-07
- **Current:** page-level layout selection does not guarantee a directory,
  functional section dividers, motif continuity, varied analytical pages,
  decision cadence, or complete-work polish.
- **Target:** each complete-work spine governs theme, grid, typography,
  palette, motif, imagery language, chart/table language, page-role grammar,
  density rhythm, hero cadence, maximum same-family run, section transitions,
  closing behavior, and compatible alternatives. Page selection occurs inside
  the chosen spine/style family unless an explicit certified bridge exists.
- **Acceptance:** the three flagship anatomy contracts can be covered without
  generic filler; every page role has at least two capacity-safe candidates
  except intentionally singular physical reference pages; page sequences pass
  anatomy, rhythm, diversity, motif, and same-family compatibility validation.

## Reference Art-Direction Baseline

The exact rendered reference contact sheet is staged under
`.planning/evidence/phase38-reference-baseline/contact-sheet.png`.

### Reusable Logic

- warm ivory field with one dark green primary and restrained champagne-gold
  accent;
- extreme Chinese display-type contrast on cover and section pages;
- a persistent lighthouse/radial-line/diagonal-beam motif that changes scale
  and crop rather than becoming a repeated card shell;
- explicit cover → directory → section → evidence → section → evidence →
  future plan → closing choreography;
- analytical variety: hero metrics, composition chart, waterfall comparison,
  table, project portfolio, KPI matrix, organization flow, capability map, and
  radial roadmap;
- native charts and tables remain visually integrated with the theme;
- high-density evidence pages alternate with sparse typographic reset pages.

### Logic To Improve, Not Copy

- avoid illegible small labels, 3D chart effects, excessive decorative
  collisions, and one-character title fragmentation when a modern readable
  lockup can preserve the same hierarchy;
- do not copy the reference organization, wording, photographs, illustration
  identity, or hospital-specific content into unrelated scenarios;
- do not mix cartoon, outline, and photorealistic icon languages on one deck;
- decorative richness must remain subordinate to facts and editable objects.

## Versioned Contracts

### TemplatePack v2

TemplatePack v2 is additive. TemplatePack v1 remains byte/hash compatible and
loads through a v2 adapter.

Required v2 concepts:

- stable `pack_id`, `deck_family_id`, `style_cluster_id`, version and digest;
- explicit rights/certification evidence and one of
  `physical_ooxml` or `registered_composition` source modes;
- complete-work `ArtDirectionProfile`;
- ordered deck-anatomy and choreography rules;
- stable page candidates with role, semantic kinds, capacity, density,
  importance, asset needs, materializer, dependencies, and alternatives;
- typed text, number, image, logo, icon, chart, table, and repeat-group slot
  descriptors where the materializer supports them;
- preserve/block capability policy for SmartArt, macros, OLE, ActiveX,
  external relationships, motion, and unsupported font/media dependencies;
- source-integrity, editability, portable-proof, and visual-evidence state.

`physical_ooxml` packs retain TemplatePack v1 adaptation for declared physical
slots. `registered_composition` packs materialize through the governed native
renderer. No route may silently rasterize a page.

### Registry v3

Registry v3 is a runtime facade, not a flag-day rewrite. It validates source
registry digests, adapts existing fields, and exposes:

- all existing archetype/layout/component/theme/design/art-direction data;
- certified complete-work spines;
- the bounded pilot page-candidate set;
- stable candidate lookup and deterministic hybrid scoring;
- page-role, semantic, density, capacity, scenario, asset, language,
  editability, deck-family, and style-cluster filters;
- maximum-marginal-relevance style diversity after hard filtering;
- dependency closure and explainable ranking evidence.

The pilot contains exactly 84 certified executable candidates:

- 15 singular physical-page candidates from the authorized work-report pack;
- 60 governed registered-composition candidates selected deterministically
  from the existing 110 variants (the first two stable variants from every
  registered family plus ten capacity/diversity supplements); and
- nine certified specialty aliases backed by explicit registered
  materializers for map, awards, people profile, partner/logo wall, business
  model, architecture, mockup, quote, and six/multi-content use.

Together they cover every registered page family and the user-requested cover,
directory, section, title, ending, one-to-six and multi-content, people,
awards, map, timeline, process, business model, mockup, quote, partner,
image-text, chart, table, material, text-component, decorative, data, and
launch needs. An alias is a governed semantic/materializer specialization, not
a claim that a generic base variant already has the missing visual grammar.

### ArtDirectionProfile v2

The v2 profile binds observable design evidence to implementation tokens:

- theme, palette roles, type scale, grid, safe margins, spacing, radius,
  stroke, shadow, image crop, icon, chart, table, background, and decoration;
- motif primitives plus placement, repetition, variation, and forbidden-use
  rules;
- page-family preferences and exclusions;
- density sequence, hero interval, maximum repeated family, section reset, and
  closing cadence;
- asset minimums, quality fallback, editability risk, and portable
  compatibility;
- reference/source digest and certification state.

### TemplateSelectionPlan And SlideBlueprint

The plan includes a chosen spine, one stable candidate per slide, fact and
asset references, capacity evidence, family/style compatibility, confidence,
fallback state, and deterministic rationale. A blueprint resolves only
registered slots and tokens. Neither contract permits raw geometry, raw
OOXML/HTML, executable code, arbitrary style values, or model-written repair.

## Retrieval And Selection Rules

1. Require a discussion-complete locked ProjectBriefPack.
2. Select one certified complete-work spine from scenario, audience, tone,
   language, brand, asset availability, and page-budget evidence.
3. Expand mandatory anatomy before body-page selection.
4. Hard-filter page candidates by certification, rights, source mode,
   materializer capability, aspect ratio, page role, semantic kind, capacity,
   asset needs, language, deck family, style cluster, and dependency closure.
5. Score the remaining candidates by semantic fit, role fit, capacity headroom,
   art-direction fit, scenario fit, asset fit, neighboring-page rhythm, and
   editability. Stable ID is the final tie-breaker.
6. Return 3–6 candidates for a model-led decision; MMR prevents near-identical
   choices from occupying the list.
7. Validate the model choice and bindings. Any unsupported field or claim
   fails closed.
8. Enforce deck-level rhythm: no more than two consecutive ordinary body
   pages from one family, a visual reset at each section, and deliberate
   sparse/dense alternation.
9. On capacity failure, use one same-family alternative. On continued failure,
   return `NO_FIT`; later phases may perform one visual replan.

## Three Legal Visual Spines

1. `institutional-work-summary`: physical OOXML, user-authorized,
   SHA-bound to the accepted 15-slide reference.
2. `campus-innovation-pitch`: first-party registered composition, owned by
   this repository, optimized for map/problem/product/prototype/pilot/business/
   team/ask choreography.
3. `academic-defense-editorial`: first-party registered composition, owned by
   this repository, optimized for question/method/experiment/result/limitation/
   contribution/defense appendix choreography.

The two first-party spines must be complete executable grammars in Phase 38.
Their final customer artifacts are generated and visually accepted in Phase
40. A spine is not certified from prose alone: its candidate coverage,
materializer route, rights, registry dependencies, and deterministic preview
sequence must validate.

## Engineering Contract

- **Owners:** `template_pack_v2.py` owns v2 manifests and v1 adaptation;
  `template_intelligence.py` owns Registry v3, candidates, retrieval,
  selection plans, and blueprints; existing modules keep their v1 ownership.
- **Invariants:** certified-only automatic selection; one primary spine per
  deck; no raw design/code fields from a model; immutable fact references;
  deterministic ranking; explicit materializer; source packages never mutate.
- **Compatibility:** existing `load_template_pack`, `load_archetypes`,
  layouts, themes, DesignPack, DeckPlan, RenderPlan, and CLI behavior remain
  unchanged. New v2/v3 entrypoints are additive.
- **Failure semantics:** invalid pack/registry/profile returns structured
  validation failure; no candidate returns `NO_FIT`; unsupported physical
  capability is preserve-only or blocked; uncertified fallback is forbidden.
- **Rollback:** remove additive v2/v3 schemas, manifests, modules, references,
  and tests; TemplatePack v1 and all current registries continue to work.

## Constraints

- Formal selection requires a discussion-complete locked ProjectBriefPack.
- Private credentials and unlicensed bytes remain outside this phase.
- Source PPTX packages are immutable and hash-bound.
- Automatic selection is certified-only and dependency-closed.
- A model cannot emit raw geometry, style values, code, OOXML, HTML, or repair
  instructions.
- Portable native-editable PPTX remains canonical; COM is optional
  diagnostics and HTML remains proof-only.
- The pilot must be reproducible without authenticated commercial access.

## Boundaries

### In Scope

- v2/v3 schemas, strict loaders, compatibility adapters, pilot registry,
  three spine manifests, semantic retrieval, selection/blueprint validation;
- reference art-direction evidence and Skill workflow documentation;
- deterministic registered-composition materialization handoff;
- focused and affected regression tests.

### Out Of Scope

- authenticated commercial download or certification without fresh rights;
- final 32-slide work-report artifact, owned by Phase 39;
- final campus/academic artifacts, owned by Phase 40;
- cross-source physical OOXML slide import, SmartArt editing, macro output,
  OLE/ActiveX activation, or whole-slide rasterization;
- weak-model distillation, owned by v6.1.

## Test Seams And Critical Cases

| Behavior | Observable seam | Failing case | Evidence |
|---|---|---|---|
| v1 compatibility | v2 adapter and old loader | v1 hash/fields/selection change | existing TemplatePack suite plus adapter tests |
| Registry v3 facade | loader and digest validation | missing/changed source registry silently accepted | focused registry tests |
| Pilot certification | candidate inventory | count outside 60–100 or family/taxonomy gap | inventory coverage tests |
| Safe retrieval | query API | legacy/unverified/wrong-family candidate auto-selects | negative retrieval tests |
| Capacity and assets | selection validator | over-capacity or missing required asset accepted | parameterized plan tests |
| Model boundary | plan/blueprint schema | coordinate, shape ID, OOXML, HTML, code, font, or color accepted | forbidden-field tests |
| Deck rhythm | sequence validator | missing directory/section/closing or repeated shell run accepted | flagship anatomy tests |
| Materialization | explicit route handoff | selected candidate lacks an executable materializer | tracer tests |
| Reference evidence | physical spine digest | packaged template drifts from accepted reference | SHA and OOXML inventory tests |

## Acceptance Criteria

- [ ] V6-LIB-01, V6-DESIGN-01, and V6-DECK-01 have concrete passing evidence.
- [ ] TemplatePack v1 behavior and all existing registry loaders remain
      compatible.
- [ ] Registry v3 exposes exactly 84 certified pilot page candidates covering
      every registered family and required user taxonomy.
- [ ] Three legal complete-work spines validate; the physical work-report
      spine remains SHA-bound to the accepted reference.
- [ ] A locked flagship brief produces a deterministic selection plan and
      slide blueprints; unsafe/unknown/over-capacity input fails closed.
- [ ] Focused, affected, and full Window-PPTX tests pass.
- [ ] Workflow, formatter, private guard, and diff gates pass.
- [ ] Fresh independent specification, quality, verification, visual, and
      completion reviews have no unresolved Blocker or Important finding.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.98
- **Boundary clarity:** 0.97
- **Constraint clarity:** 0.97
- **Acceptance clarity:** 0.97
- **Ambiguity:** 0.028

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | Visual truth | Is the reference only inspirational? | No; the packaged authorized TemplatePack is byte-identical and supplies a legal physical spine |
| 2 | Compatibility | Replace v1 loaders and registries? | No; use additive v2/v3 adapters and preserve old behavior |
| 3 | Library size | Index all 110 variants immediately? | No; certify a balanced 84-candidate pilot covering every family and required taxonomy |
| 4 | Model role | Let GPT-5.5 draw layouts? | No; it selects certified IDs and bindings while rules own design implementation |
| 5 | Spine strategy | Wait for commercial downloads? | No; use one authorized physical spine and two first-party executable composition spines |
| 6 | Physical scope | Implement arbitrary cross-deck OOXML import now? | No; keep physical v1 adaptation and registered-composition materialization; cross-source import is deferred |
| 7 | Visual defects | Copy every visible reference behavior? | No; preserve hierarchy/rhythm/motif/variety while rejecting tiny labels, 3D effects, and decorative collisions |
