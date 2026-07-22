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

- Match the target platform's navigation, safe areas, input conventions, and density. When platform context matters, use the source-neutral iOS, Android, macOS, or browser starter frame rather than inventing device chrome.
- Prefer a responsive app canvas over fixed screenshots when interaction matters.
- Build the critical path and recovery path, not a collection of disconnected screens.
- Use real, licensed images or representative structured content when they affect layout decisions. Record provenance and do not leave a generic placeholder when a truthful public-domain or project asset is available.
- Keep application state outside the decorative frame so every screen uses one deterministic navigation and data model.
- Run a real Playwright click path through the primary flow, one back path, and one failure or reset path before delivery.
- Record transitions and state ownership in `assets/templates/prototype-plan.md`.

## Variants And Live Tweaks

Use `assets/starter/design-comparison.jsx` for two or three static directions. Use a live tweak panel when changes are continuous or combinatorial. Expose no more than six meaningful decisions, such as density, type role, palette mode, navigation model, motion intensity, or content emphasis. The default state must already be a finished design. Persist selections locally, provide reset, and make the selected configuration exportable or visible in the review record.

Use `assets/starter/tweak-panel.jsx` for the persisted React hook and accessible control surface. Select a domain baseline from `assets/patterns/taste-anchor-patterns.json`, then expose only decisions that remain genuinely open; never turn implementation tokens into an unbounded style editor.

Do not expose arbitrary CSS values or hundreds of controls. Variants support a decision; they are not an excuse to avoid one.

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

## Infographics

Use an infographic when a bounded data story, process, system, or comparison must work as one fixed visual rather than an operational dashboard. Start with one sourced thesis, then select only the statistics, diagram, chart, annotations, legend, and source notes needed to prove it. Use `evidence-infographic`, `stat-block`, and `annotated-diagram`; preserve units, denominators, dates, uncertainty, and attribution beside the marks they qualify.

Design each required aspect ratio deliberately. Do not shrink a desktop composition into a vertical poster, encode magnitude with decorative area, or turn unrelated facts into a card grid. Verify reading order, label collisions, color-independent meaning, source legibility, and a text fallback at the final distribution size.
