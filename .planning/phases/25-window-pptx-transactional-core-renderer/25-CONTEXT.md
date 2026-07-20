# Phase 25 Context: Transactional Editable Core Renderer

Phases 23 and 24 now provide validated semantic slides, governed themes, and deterministic layout slots. Phase 25 must connect those pure decisions to PowerPoint without reopening design freedom for the model.

The renderer accepts a compiled DeckPlan plus explicit runtime context. It resolves theme and layout choices before any COM mutation, creates only registered editable core objects, records every intended operation, and saves only through the existing candidate/reopen/atomic-promotion transaction. Geometry is expressed in page-relative inches and converted to PowerPoint points at the final boundary.

This phase covers text boxes, basic native shapes, governed images, slide/master backgrounds, footer elements, grouping, and z-order. Native charts, tables, complex diagrams, notes, hyperlinks, motion, and final export fidelity belong to Phase 26. Visual inspection and repair scoring belong to Phase 27, but Phase 25 establishes typed inspect/repair hook stages so the runner has one stable lifecycle.

No live PowerPoint mutation is required for Linux acceptance. A recording fake-COM object model must prove call ordering, arguments, editability intent, cleanup, and transaction integration. Real Windows acceptance remains mandatory before the milestone closes.
