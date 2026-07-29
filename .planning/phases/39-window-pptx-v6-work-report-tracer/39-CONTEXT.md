# Phase 39 Context

## Implementation Decisions

- The annual work-report tracer consumes only the locked
  `annual-work-report.project-brief-pack.v1.json`.
- `institutional-work-summary` is the certified visual spine; the native
  renderer uses its warm editorial palette, radial motif, section rhythm, and
  evidence-first composition without copying ungoverned coordinates.
- The flagship is exactly 28 main slides plus 4 appendix slides.
- All geometry, typography, colors, charts, tables, and notes are owned by the
  registered renderer. Model-authored OOXML, HTML, coordinates, and fonts stay
  forbidden.
- LibreOffice/Poppler is the required portable proof. PowerPoint COM is not a
  release dependency.

## Existing Patterns To Preserve

- Locked ProjectBriefPack fact IDs and speaker-note lineage.
- Certified complete-work spine selection and native composition ownership.
- Isolated LibreOffice profiles, Poppler page proof, and hash-bound manifests.
- Additive compatibility with legacy DeckPlan and RenderPlan entry points.

## Allowed Scope

- The v6 flagship generator, its focused tests, Phase 39 planning/evidence,
  certified-template manifests, and linked Skill documentation.
- Native editable shapes, charts, tables, diagrams, notes, and factual labels
  derived from locked facts.

## Forbidden Scope

- Unsupported metrics, customer claims, financial claims, or invented assets.
- Whole-slide rasterization, HTML-to-PPTX as the canonical path, mandatory COM,
  arbitrary repair, or mutation of the reference PPTX.
- Private commercial template bytes or credentials.

## Integration And Compatibility

The tracer adds a registered native-composition bridge to the existing
ProjectBriefPack, TemplatePack v2, Registry v3, and portable evidence
contracts. Legacy DeckPlan/RenderPlan entry points remain available and are not
weakened.
