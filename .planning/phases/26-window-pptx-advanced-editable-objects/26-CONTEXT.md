# Phase 26 Context: Advanced Editable Objects

Phase 25 provides a closed, exact-governed renderer boundary for editable core objects. Phase 26 may enrich that boundary, but model input must remain semantic: it cannot supply COM calls, coordinates, chart XML, animation IDs, arbitrary object names, or free-form style values.

This phase replaces advanced native fallbacks with typed commands derived from validated content blocks. Charts and tables keep editable data. Processes, timelines, matrices, quadrants, funnels, and roadmaps are composed from governed native shapes and grouped deterministically. Speaker notes and hyperlinks are explicit semantic fields. Motion is off by default and can only select a small governed preset. PNG/PDF exports use actual presentation geometry and remain downstream of successful rendering.

Real PowerPoint behavior will still require Phase 29 Windows acceptance. Linux acceptance uses an expanded recording fake-COM boundary, exact render-plan validation, data-fidelity assertions, and transaction/export ordering tests.
