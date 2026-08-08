# Phase 46 Context

## Objective

Regenerate three real anchor decks that visibly reach the supplied reference's
art-direction level while remaining editable and evidence-bound.

## Inputs

- locked realistic briefs in
  `.planning/evidence/phase39-40-flagships-r2/briefs/`;
- user reference `.planning/references/pptx/工作总结.pptx`;
- certified private core and package index below the ignored Skill-local
  `.private/` boundary;
- Phase 45 selection, blueprint, and materialization contracts.

## Baseline

The Phase 39/40 PPTX files remain the rejected baseline. They are not promotion
candidates.

## Implementation boundary

- New tracked engine, schemas, docs, and tests are allowed.
- Generated private assets, source media extracts, PPTX artifacts, PDFs, PNGs,
  and review packets remain under ignored/private or planning-evidence paths
  according to existing repository policy.
- No credential, source URL, commercial package byte, or distributable media
  enters tracked files.

## Implementation Decisions

- Add an anchor-specific blueprint and renderer.
- Keep the old flagships unchanged as baseline evidence.
- Separate candidate materialization evidence from influence-only evidence.
- Iterate the work-summary before expanding to the other two anchors.

## Existing Patterns To Preserve

- Locked ProjectBriefPack fact authority.
- Phase 45 exact candidate selection/materialization evidence.
- Native editable objects and no whole-slide rasterization.
- Isolated LibreOffice/Poppler proof and hash manifests.

## Allowed Scope

- New tracked schemas, renderer modules, tests, and documentation.
- Local extraction/use of authorized private media with digest provenance.
- Generated PPTX/PDF/PNG/contact-sheet evidence.

## Forbidden Scope

- Credential or source URL disclosure.
- Committing private commercial bytes.
- Reference-only direct materialization.
- Mandatory COM or screenshot decks.

## Integration And Compatibility

The new engine is additive. Existing v5/v6 APIs and the rejected Phase 39/40
generator remain intact. Phase 45 sidecars and error semantics stay canonical
for candidate truth.

## Visual contract

Every anchor must contain:

- cover, directory, section/chapter, body, decision/conclusion, and closing;
- at least one photo-led or hero-visual page;
- at least one native chart and one native diagram/table;
- three or more materially different body compositions;
- explicit sparse/medium/dense rhythm;
- one coherent motif and type system across the whole deck;
- no run of more than two pages with the same composition family.
