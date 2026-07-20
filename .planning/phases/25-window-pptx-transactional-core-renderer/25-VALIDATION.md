# Phase 25 Validation: Transactional Core Renderer

**Status:** Active / Incomplete

## Required Evidence

- [ ] A pure typed render plan joins validated compiled slides to exact governed themes, layouts, components, and stable object names.
- [ ] Core text, shapes, and images are emitted as editable native PowerPoint objects.
- [ ] 16:9, 4:3, portrait, and custom sizes preserve margins, gutters, relative placement, and minimum typography.
- [ ] Slide/master background, footer, grouping, and z-order operations are deterministic.
- [ ] Recording fake COM proves end-to-end command ordering, arguments, names, layers, groups, and failure context.
- [ ] The project runner follows validate → compile → plan → render → inspect → repair → transactional save and preserves strict dry-run behavior.
- [ ] Renderer failures cannot promote a candidate or mutate a distinct source.
- [ ] Public API and CLI expose the governed pipeline without accepting uncontrolled raw design instructions.
- [ ] Focused and complete suites pass with no unresolved Critical or Important finding.

## Verdict

Not ready to close; implementation has not started.
