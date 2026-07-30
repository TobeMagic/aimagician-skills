TASK_ID: window-pptx-phase46-architecture-research-20260730
ROLE: independent implementation researcher
TASK_TYPE: research
MODALITY: text
OBJECTIVE: Produce a concrete architecture and execution recommendation for
rebuilding three editable PPTX anchors at reference-grade art direction.
DELIVERABLE: Findings first, implementation seams, risks, recommended
architecture, test strategy, and a bounded first execution slice.

REQUIRED_SKILLS:
- cli-agent-delegator
- aimagician-superpower
- window-pptx

WRITE_SCOPE: NONE
CHILD_AGENT_POLICY: forbidden

SOURCE_OF_TRUTH:
- `.planning/REQUESTS.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/45-window-pptx-v6-selection-to-materialization/45-SUMMARY.md`
- `.planning/phases/45-window-pptx-v6-selection-to-materialization/45-VALIDATION.md`
- `.planning/phases/39-window-pptx-v6-work-report-tracer/39-SUMMARY.md`
- `.planning/phases/40-window-pptx-v6-campus-academic-tracers/40-SUMMARY.md`
- `skills/owned/window-pptx/scripts/build_window_pptx_v6_flagships.mjs`
- `skills/owned/window-pptx/scripts/window_pptx/template_intelligence.py`
- `skills/owned/window-pptx/scripts/window_pptx/selection_materialization.py`
- `skills/owned/window-pptx/scripts/window_pptx/template_pack.py`
- `skills/owned/window-pptx/scripts/window_pptx/private_asset_intelligence.py`
- `tests/window_pptx/test_v6_flagship_generator.py`
- `tests/window_pptx/test_template_intelligence.py`

KNOWN_VISUAL_EVIDENCE:
- The accepted work-summary reference is a 15-slide complete work with
  expressive oversized Chinese typography, diagonal gold bands, lighthouse
  imagery, photographic cover/closing, strong chapter pages, native charts,
  dense-but-controlled data, illustration, motif continuity, and visible
  sparse/dense rhythm.
- The old annual work-report output is clean but generic: repeated ivory
  cards, rounded rectangles, thin radial motif, weak imagery, limited scale
  contrast, and appendix-heavy repetition. It does not resemble the reference
  or excellent commercial works.
- The old campus output is a dark-blue/teal component system repeated over
  almost every page, with few real photos/mockups and little narrative
  spectacle.
- The old academic output is a light editorial grid but again relies on
  repeated rounded cards and tables, with insufficient scientific diagrams,
  figure-led layouts, and visual hierarchy variation.
- Phase 44 has a 288-page private core: 129 direct-use pages and 159
  reference-only pages. Direct-use includes covers, directory pages, sections,
  closings, quote pages, people, awards, timelines, maps, diagrams, motifs, and
  text-navigation components. Reference-only pages may guide art direction but
  cannot materialize automatically.
- Phase 45 proves exact native bindings and hash-bound whole-pack physical
  adaptation. It intentionally does not implement arbitrary multi-source
  OOXML relationship merging.
- The user prioritizes actual visual effect on this local machine and allows
  locally authorized assets. PPTX must remain editable; whole-slide raster
  output is forbidden. COM is optional and currently unreliable.

QUESTIONS:
1. Should Phase 46 extend the existing monolithic flagship generator, build a
   new anchor-specific authoring engine, or add a controlled editable-shape
   import/translation layer from selected physical pages?
2. What is the smallest safe architecture that can visibly use certified
   private candidates without pretending metadata is reuse?
3. How should page blueprints encode hero imagery, typographic composition,
   chart/diagram direction, motif continuity, density, and rhythm so ordinary
   models do not own geometry?
4. Which tests and evidence prove actual candidate use, editable output,
   portable rendering, and no prohibited rasterization?
5. What first slice most quickly demonstrates a visual step-change on the
   work-summary anchor before scaling to campus and academic?

Return concrete recommendations tied to named files and symbols. Do not modify
the repository.
