# Phase 25 Research: Renderer Boundary and Failure Controls

## Weak-Model Failure Modes to Remove

| Failure | Deterministic replacement |
|---|---|
| Emits ad-hoc COM calls or coordinates | Typed render commands compiled from governed layouts |
| Uses pixels or assumes 16:9 | Inches until the COM edge, then one points conversion |
| Rasterizes editable content | Native text boxes and shapes by component policy |
| Stretches images | Asset policy plus crop-frame commands |
| Changes z-order accidentally | Stable layer enum and explicit reorder pass |
| Leaves anonymous shapes | Stable deck/slide/component-derived names and tags |
| Partially mutates the final output | Candidate-only rendering and existing transactional promotion |
| Cleanup differs between real and test paths | One runner lifecycle exercised by recording fake COM |
| Renderer silently skips unsupported content | Stable unsupported-component finding or safe native fallback |

## Architecture

1. `build_render_plan` validates or compiles semantic input and joins every slide to a resolved theme/layout.
2. The pure render plan contains slide size, stable object names, typed component commands, layer/group metadata, and source references; it contains no live COM objects.
3. `PowerPointRenderer` applies commands to a presentation using a narrow object-model adapter and records an execution report.
4. A project runner owns validate → compile → plan → render → inspect-hook → repair-hook → transactional-save sequencing.
5. `RecordingPowerPoint` implements the same narrow boundary in memory and exposes a deterministic call log for end-to-end tests.

## Safety Rules

- Reject non-finite or non-positive geometry before COM.
- Convert inches to points exactly once; never feed pixels into PowerPoint.
- Never select an unregistered theme, family, variant, component, or asset.
- Do not save directly to the final output path.
- Make slide and object ordering stable under repeated runs.
- Do not catch and hide COM mutation errors; attach slide/object context and abort candidate delivery.
- Keep advanced-object placeholders native and explicit; do not fake completed charts or tables with screenshots.
