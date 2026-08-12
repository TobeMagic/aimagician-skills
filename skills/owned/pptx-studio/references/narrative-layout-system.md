# Narrative and Layout System

## Registered commercial narratives

The archetype registry covers business report, project proposal, product launch, market analysis, sales proposal, investor pitch, annual review, strategic plan, data analysis, research report, training, brand introduction, project kickoff, operations review, and ecommerce/marketing.

Each archetype has an ordered outline and at least one critical beat in `registries/narrative-rules.json`. A critical beat without evidence is a hard error. Required facts omitted by the model are assigned deterministically to a compatible beat; they are never discarded.

Every generated deck receives a cover and closing page. An agenda is added only when the deck length and archetype justify it. Five and six sections use exact card compositions; longer agenda continuations are rebalanced to avoid a one-item orphan. Action titles remain literal fact-backed statements or a registered narrative-role label when the complete evidence belongs in the body/KPI slot; open-ended copywriting is not delegated to the weak model.

## Semantic-to-form authority

Apply these relationships before considering visual variation:

| Content relationship | Preferred governed form |
|---|---|
| One decisive claim | editable editorial statement or assertion/evidence; quote styling only for an explicit quote fact |
| Key scalar numbers | big number or KPI dashboard; a trusted metric sentence containing numeric evidence may retain KPI emphasis without extracting or rewriting the value |
| Change over ordered time | line chart only when explicit ordered categories and values exist; otherwise retain a fact-backed statement |
| Category comparison | comparison; categorical measures with one shared unit may use a native editable column/bar chart under an analytical direction |
| Part-to-whole | doughnut for one series; stacked native chart for multiple series |
| Distribution | column/bar; dot intent uses an editable column fallback without paired XY data |
| Relationship between two measures | scatter |
| Ordered stages | process |
| One dated event | compact milestone band |
| Two or more dated events | timeline |
| Multi-horizon plan | roadmap |
| Two-sided differences | comparison/before-after |
| Three short explicit labels | compact three-tile cards capped at the registered short-label height |
| Explicit parallel points with detail | cards or modular grid when conservative whole-list parsing succeeds; numeric grouping commas are never list separators |
| Two-dimensional classification | matrix or quadrant |
| Risk plus action | risk/recommendation |
| Structured records | native table |
| Verified visual evidence | image story or product showcase |

The selected semantic form controls native chart type. Art direction may add a small preference weight only among already compatible families; it cannot turn a process into an unrelated image page.

## Capacity and page rhythm

- One dominant semantic block per page.
- Use component capacities and density presets; split overflow instead of shrinking text below minimums.
- Avoid card layouts for a single point.
- Penalize the same family after one consecutive use and more strongly after two.
- Cover/section/focal pages are sparse; short titles use the display scale only when exact slot capacity permits, evidence pages may be balanced/dense, and closing returns to sparse.
- Titles use the registered 44/32/22/18 pt ladder and fall back by measured slot capacity. Inline emphasis remains native editable rich-text runs.
- A direction-specific deterministic seed rotates compatible geometry variants. There is no random layout selection.
- Each of 25 layout families has at least three geometry signatures. Geometry remains inside a 12-column governed grid and safe margins.

## Page families

The registry covers cover/focal statements, executive summaries, big numbers, text-media, image stories, cards, product showcases, charts, tables, process, timeline, roadmap, comparison, matrix, quadrant, funnel, risk/recommendation, team, case-like evidence, summary, CTA, and closing use cases through 25 semantic families and at least 75 governed variants.

When an asset is missing or rejected, downgrade before layout selection to a native text/shape/diagram family. Do not leave an empty image frame, fake screenshot, decorative placeholder, or stretched image.
