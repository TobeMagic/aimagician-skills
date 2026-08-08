# Phase 38 Context

## Baseline

- Phase 37 closed at `ed925be`.
- The full Window-PPTX suite passed 843 tests at that boundary.
- Catalog v3 provides stable IDs, content dedupe, aliases, certified-only
  query, and dependency closure.
- Authenticated commercial sync remains `NEEDS_AUTH`.
- Existing runtime assets include 110 layout variants across 25 page families,
  21 components, eight themes, twelve art directions, four design packs, four
  quarantined legacy templates, and one authorized physical TemplatePack v1.

## Visual Evidence

The user-accepted source and packaged physical template share SHA-256
`59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839`.
The exact reference renders as 15 pages with 29 media objects and four charts.
Its visual floor is materially above the rejected v5.1 trials because it uses
a complete motif system, decisive typographic scale, functional structural
pages, and different visual forms for different evidence.

## Objective And Boundary

Phase 38 connects safe catalog metadata to executable design selection. It
does not claim final flagship visual parity; Phases 39–40 must prove that with
real PPTX artifacts and pixel review.

## Implementation Decisions

- The registry policy stores source digests and derivation rules; runtime
  derives candidates instead of duplicating geometry.
- The 84 candidates are 15 physical pages, 60 registered variants, and nine
  specialty aliases with explicit materializers.
- `TemplateSelectionPlan` and `SlideBlueprint` are strict additive contracts;
  the existing DeckPlan and RenderPlan remain canonical downstream surfaces.

## Allowed Scope

- Additive schemas, v2 manifests, Registry v3 policy, v1 adapter, retrieval,
  selection/blueprint validation, Skill documentation, tests, and Phase 38
  evidence.

## Forbidden Scope

- Private credentials or commercial bytes, arbitrary physical slide import,
  raw model geometry/style/code, whole-slide rasterization, mandatory COM, and
  final flagship visual GO.

## Accepted Architecture

1. Keep TemplatePack v1 and all current registries unchanged.
2. Add TemplatePack v2 as a complete-work manifest and v1 adapter.
3. Add Registry v3 as a digest-bound facade over current sources.
4. Derive a balanced certified pilot from existing executable variants.
5. Add three legal visual spines: one authorized physical pack and two
   first-party registered-composition packs.
6. Give GPT-5.5 medium only stable candidate selection and binding decisions.
7. Validate deck anatomy, capacity, family/style, facts, assets, dependencies,
   rhythm, and materializer before rendering.

## Existing Patterns To Preserve

- strict dataclasses and unknown-field rejection;
- deterministic JSON serialization, SHA-256 lineage, and stable ordering;
- public schemas plus stricter runtime validation;
- fail-closed legacy isolation and certified-only automatic query;
- portable native-editable PPTX as canonical output;
- one deterministic repair, one same-family reselection, one visual replan.

## Security And Rights Invariants

- no credential or private byte is read by Template Intelligence;
- certification cannot be inferred from authentication or metadata alone;
- the physical source is immutable and hash-bound;
- first-party composition spines declare repository ownership and their
  executable registry dependencies;
- unsupported active content is preserve-only or blocked, never executed or
  silently rasterized.

## Integration And Compatibility

- old `load_template_pack` behavior and TemplatePack v1 schema remain stable;
- old archetype/layout/theme/design/legacy loaders remain stable;
- v3 adapts their public data rather than rewriting them;
- existing direct DeckPlan and BriefPlan routes remain available until Phase
  39 integrates the new selection plan.

## External Preconditions

None for the first-party pilot. Commercial catalog expansion may resume only
after a rotated short-lived private credential and item-level rights evidence
are available.
