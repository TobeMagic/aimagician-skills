# Prototypes And Data Experiences

Use this module for app concepts, workflow demos, dashboards, interactive reports, and data visualization.

## Prototype Contract

Choose fidelity based on the uncertainty:

- **Structure prototype:** validates navigation, hierarchy, and content shape.
- **Interaction prototype:** validates transitions, input, state, and task flow.
- **Visual prototype:** validates art direction, type, color, imagery, and motion.
- **Integrated demo:** proves a realistic end-to-end product story with bounded fake services.

State what is real, simulated, placeholder, and out of scope. A prototype must not masquerade as production. Keep its data deterministic and its main path runnable without undocumented setup.

## App Prototypes

- Match the target platform's navigation, safe areas, input conventions, and density without redrawing decorative device chrome unless the frame is necessary for evaluation.
- Prefer a responsive app canvas over fixed screenshots when interaction matters.
- Build the critical path and recovery path, not a collection of disconnected screens.
- Use real images or representative structured content when they affect layout decisions.
- Record transitions and state ownership in `assets/templates/prototype-plan.md`.

## Dashboards And Reports

Start with the decisions users make, then select metrics and views. Establish:

- metric definition, time window, comparison baseline, units, freshness, and source;
- global versus local filters and visible filter state;
- overview-to-detail path and cross-filter behavior;
- empty, delayed, partial, anomalous, and permission-restricted data;
- table fallback or accessible summary for visual encodings.

Use a quiet work-focused composition for repeated operational use. Prioritize scan order, comparison, and action over decorative cards.

## Data Visualization

- Trend: line or area only when area encoding helps; annotate significant changes.
- Magnitude comparison: bar, dot plot, or table; use a common baseline.
- Distribution: histogram, box plot, density, or sorted strip according to sample size.
- Part-to-whole: stacked bar or limited composition; avoid many-slice pies.
- Relationship: scatter, matrix, or network only when topology is the question.
- Sequence: timeline, flow, funnel, or staged diagram.

Do not use 3D charts, decorative chart junk, misleading axes, unexplained dual scales, or color-only distinctions. Show source, units, period, and uncertainty when relevant. Provide tooltips or detail views without hiding the essential comparison.
