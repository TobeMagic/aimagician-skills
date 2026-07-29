# Certified Template Intelligence

Use this route only after a discussion-complete `Locked` ProjectBriefPack.
It converts a content decision into a bounded visual choice without giving the
authoring model control of geometry or implementation.

## Runtime

```python
from window_pptx.template_intelligence import (
    build_selection_plan,
    compile_slide_blueprints,
    load_registry_v3,
)

registry = load_registry_v3()
plan = build_selection_plan(locked_brief, registry=registry)
blueprints = compile_slide_blueprints(plan, registry)
```

Registry v3 is digest-bound to the governed layout, component, theme,
design-pack, and art-direction registries. It derives exactly 84 candidates:

- 15 authorized physical pages from the accepted work-summary reference;
- 60 registered variants: two from all 25 families plus ten stable diversity
  supplements;
- nine specialty aliases with explicit native materializers.

The three legal visual spines are:

- `institutional-work-summary`: authorized physical OOXML, ivory/green/gold
  editorial direction;
- `campus-innovation-pitch`: first-party native composition, technical stage
  direction;
- `academic-defense-editorial`: first-party native composition, research
  evidence direction.

## Model boundary

The model may choose only a returned `spine_id`/`candidate_id`, bound fact and
asset references, importance, confidence, fallback state, and registered
reason codes. It may not emit coordinates, dimensions, shape IDs, fonts,
colors, OOXML, HTML/CSS, executable code, or repair instructions.

Hard filters run before scoring: certification and rights, source/materializer
compatibility, deck/style family, role, capacity, assets, and dependency
closure. Semantic and role fit, capacity headroom, specialty fit, and stable
ID ordering then determine a deterministic shortlist. A section resets page
rhythm; more than two consecutive ordinary pages from one family is rejected.

## Materialization

`physical_ooxml` blueprints route to the TemplatePack v1 adapter and preserve
the source package. `registered_composition` blueprints route to the native
editable renderer. Neither route may rasterize a whole slide. COM remains
optional diagnostics and HTML remains proof-only.

On no fit, stop with `NO_FIT`. The bounded recovery budget is one same-family
capacity-safe alternative, one deterministic local repair, and one visual
replan in later flagship phases. Do not fall back to legacy/unverified
templates or freeform drawing.
