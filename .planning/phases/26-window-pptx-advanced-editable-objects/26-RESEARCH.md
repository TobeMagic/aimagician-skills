# Phase 26 Research: Native Advanced Object Boundary

## Weak-Model Failure Modes to Remove

| Failure | Deterministic replacement |
|---|---|
| Chooses a chart by visual guess | Semantic chart intent plus governed chart-type mapping |
| Converts data to a screenshot | Typed categories/series written into a native chart workbook |
| Draws a table as unrelated text boxes | Native PowerPoint table with bounded rows/columns and governed cells |
| Emits arbitrary diagram geometry | Registered diagram recipes allocate native nodes/connectors inside one governed slot |
| Drops notes or links | Versioned semantic fields compiled into explicit interaction commands |
| Adds distracting animation | Motion is `off` unless an allowed preset is requested |
| Exports at fixed pixels | Long-edge export dimensions derive from PageSetup ratio |
| Partially saves after advanced-object failure | Existing candidate-only transaction remains the only delivery route |

## Architecture

1. Extend DeckPlan with bounded semantic notes, hyperlinks, and motion preference; keep raw design fields forbidden.
2. Add immutable chart, table, diagram, interaction, and export specifications to the render plan.
3. Re-derive every advanced specification from the compiled semantic block during public-plan validation.
4. Render charts/tables through native PowerPoint collections and diagrams through named, tagged, grouped native shapes.
5. Expand recording fake COM for chart data, tables, notes, links, effects, and export calls with deterministic failure injection.
6. Preserve the Phase 25 runner and transaction ordering; advanced objects cannot write final outputs directly.

## Safe Defaults

- Unsupported or malformed advanced data becomes an explicit native fallback finding, never a silent screenshot.
- Chart series/categories, table rows/columns, and diagram nodes have strict capacity limits and stable truncation/splitting behavior.
- Hyperlinks accept only governed external HTTP(S), mailto, or internal slide targets.
- Motion presets are limited to `off`, `subtle-fade`, and `step-reveal`; `off` is the default.
- Export commands use the rendered presentation size and verify output existence/signature without changing source decks.
