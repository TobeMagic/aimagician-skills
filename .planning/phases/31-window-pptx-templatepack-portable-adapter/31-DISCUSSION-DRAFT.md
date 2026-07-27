# Phase 31 Discussion Draft: From Reference-Grade Tracer to Repeatable Quality

**Status:** Draft for discussion
**Milestone:** v5.1 Window-PPTX Reference-Grade Visual Engine
**Date:** 2026-07-27

## Current evidence

The reference-driven tracer slice is materially successful:

- the authorized 15-slide TemplatePack preserves the supplied visual language;
- governed text and chart/workbook slots remain editable;
- no-op output is byte-identical and full adaptation changes only declared
  parts;
- r10 passes structural and cross-engine portable proof without COM;
- the generated DesignPack route now rejects the historical sparse floor.

The milestone is not ready to close:

- generated DesignPack-only decks remain below the supplied reference;
- the `0.98` non-slot similarity requirement is not yet defined as a
  reproducible metric;
- visual UAT has no currently verified image-capable OpenCode reviewer;
- the full two-model benchmark and blind review remain `NOT_RUN`.

## Recommended product strategy

Keep two explicit delivery lanes instead of forcing one renderer to solve every
project:

1. **TemplatePack lane — quality-first.** Use authorized high-quality PPTX
   packs for customer delivery when a compatible scenario exists.
2. **DesignPack lane — coverage-first.** Compile semantic content into governed
   component compositions when no TemplatePack matches.

For the next iteration, invest approximately 70% in extracting reusable
composition knowledge from the successful reference and 30% in TemplatePack
hardening. More TemplatePack slots alone improve reuse but do not teach the
generated lane how to design.

## Proposed optimization chain

### Wave A — close the TemplatePack contract

1. Define non-slot preservation as an OOXML-part invariant plus a rendered
   masked-region metric; do not use a whole-slide pixel score that penalizes
   intended text/data changes.
2. Add a reproducible golden-r10 command that regenerates the deck from a
   versioned binding fixture and emits a small manifest instead of committing
   every intermediate render.
3. Add font substitution fingerprints, chart/workbook round-trip checks, and
   PowerPoint read-only sampling as optional certification.
4. Produce a TemplatePack authoring command that inventories shapes, proposes
   safe slots, estimates capacity, and generates a reviewable manifest.

**Exit:** the TemplatePack lane is reproducible from a clean clone, declared
parts are the only mutations, and the masked non-slot metric is frozen.

### Wave B — turn the reference into composition grammar

1. Extract reusable primitives: editorial title rail, section number, KPI
   cluster, media frame, chart frame, callout, evidence strip, footer, and
   closing motif.
2. Define composition recipes as constraints and relationships, not copied
   coordinates: anchors, spans, alignment groups, hierarchy, density bands,
   media ratios, and z-order.
3. Add capacity contracts for every recipe and deterministic split/merge
   behavior before rendering.
4. Rank variants from semantic form, content volume, previous-page rhythm,
   asset availability, and emphasis level.
5. Add negative rules for repeated geometry, weak focal hierarchy, decorative
   noise, tiny labels, and unsupported asset stretching.

**Exit:** the generated route can reproduce the reference's hierarchy,
coverage, rhythm, and editorial richness without copying its physical slide
XML.

### Wave C — complete four scenario DesignPacks

Ship four packs with distinct but compatible visual languages:

- institutional annual/editorial;
- consulting executive;
- product launch/stage;
- data and research editorial.

Each pack must provide:

- scenario/archetype coverage;
- at least three governed variants for its dominant page families;
- theme and typography tokens;
- component recipes and capacity limits;
- asset intents, provenance rules, and high-quality fallbacks;
- rhythm rules for adjacent pages;
- a small golden fixture set.

**Exit:** all fifteen commercial scenarios resolve to a pack and no scenario
falls back to a text-only or single-layout deck.

### Wave D — visual regression and bounded repair

1. Separate structural, rendered, semantic, and human/vision-model verdicts.
2. Add local deterministic metrics for coverage, alignment, repetition,
   density, crop distortion, whitespace balance, contrast, and readable text.
3. Add reference-relative metrics only where a reference or golden fixture
   exists.
4. Route pixel review through capability probes; prefer Agnes when the active
   connector proves image input, otherwise use another verified vision model
   or a human reviewer.
5. Implement bounded repair in this order: variant reselection, split/merge,
   text fit, geometry alignment, asset fallback/crop, then decoration removal.
6. Re-render after each repair and roll back any non-monotonic change.

**Exit:** four representative scenarios pass deterministic gates and an actual
pixel reviewer; automatic metrics never masquerade as visual acceptance.

### Wave E — weak-model reliability and closure

Use a staged benchmark:

1. four-scenario diagnostic with DeepSeek V4 Flash Free;
2. one second ordinary model after provider availability is frozen;
3. only then execute the full formal matrix;
4. anonymized blind review over hash-bound PPTX and readable PNGs;
5. optional read-only PowerPoint sampling for the frozen high-risk subset.

**Exit:** average blind score is at least 4.2/5, no dimension is below 4,
cross-engine evidence is fresh, and every accepted requirement is traceable.

## Decisions to discuss before locking Phase 31

1. **Priority split:** accept the recommended 70% composition-grammar / 30%
   TemplatePack-hardening investment, or prioritize building more TemplatePacks?
2. **Similarity definition:** accept masked non-slot rendered similarity plus
   exact OOXML preservation, rather than an undifferentiated whole-slide 0.98?
3. **Visual reviewer:** provide/configure a verified vision-capable provider,
   use a human blind reviewer, or support both?
4. **Evidence storage:** keep large PPTX/PDF/PNG runs local or in release/object
   storage while committing only manifests and selected golden previews?
5. **First generated-lane acceptance scenario:** institutional work summary,
   consulting proposal, product launch, or data-analysis report?

This draft is intentionally not a locked execution plan. The answers above
change sequencing, acceptance evidence, and cost.
