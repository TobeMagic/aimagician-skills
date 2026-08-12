# Weak-Model Generation Workflow

Use this workflow for new decks when the planning model may be ordinary or unreliable. The model never owns facts, page geometry, fonts, colors, template IDs, code, or COM calls.

## Authority chain

```text
trusted material
  -> FactStore v1 (immutable text, values, units, citations)
  -> BriefPlan v1 (fact IDs + registered hints only)
  -> NarrativePlan v1 (deterministic story and coverage)
  -> DeckPlan v1 (canonical semantic contract)
  -> DirectionDecision v1 (three governed candidates)
  -> RenderPlan v1 (exact native-editable commands)
  -> QualityReport v2 + bounded repair
  -> transactional PPTX candidate
```

FactStore is trusted input. Build it from the user's supplied documents/data; do not ask a weak model to restate facts. `text`, `value`, `unit`, `source_id`, `locator`, language, and status are immutable after validation.

BriefPlan is the only normal model-authored object. It may contain:

- one registered `scenario_id`;
- groups with `id`, `fact_refs`, optional registered `beat_hint`, optional registered `semantic_hint`, and `importance`;
- controlled preferences.

Unknown keys fail closed. Raw `title`, layout IDs, coordinates, fonts, colors, templates, code, scripts, macros, or free-form styling are forbidden.

## Bounded model loop

1. Give the model the FactStore fact IDs, registered scenario, permitted beats, permitted semantic kinds, and the BriefPlan schema.
2. Normalize once. This may remove a JSON fence, normalize `v1` to `1.0`, resolve a scenario alias, and slug controlled IDs. It may not rewrite facts or invent content.
3. Validate.
4. On failure, return the structured error and the same immutable fact IDs. Allow at most two model retries.
5. After two failures, use the safe default: one group per required fact, archetype-derived beat assignment, normal/high importance, professional tone, balanced density, motion off.
6. Compile once. Never ask the model to patch RenderPlan or COM output.

## CLI

Compile without PowerPoint:

```powershell
python window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --fact-store facts.json `
  --brief-plan brief.json `
  --compile-brief-plan `
  --no-output-deck `
  --json
```

Inspect three directions without rendering:

```powershell
python window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --fact-store facts.json `
  --brief-plan brief.json `
  --render-brief-plan `
  --direction-mode interactive `
  --no-output-deck `
  --json
```

Rerun with the approved registered direction:

```powershell
python window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --fact-store facts.json `
  --brief-plan brief.json `
  --render-brief-plan `
  --direction-mode locked `
  --direction-id quiet-assertion-evidence `
  --output output\final.pptx `
  --export-qa `
  --json
```

Use `--brand-spec brand.json` only for trusted brand information. A mandatory missing logo/product asset is a hard gate when `require_brand_fidelity` is true.

## Safe defaults

- Unknown or low-confidence direction: quiet safe candidate.
- No usable image: choose a native-editable statement/diagram composition before layout resolution; never promote a placeholder.
- Font selection: choose the first installed face from the governed Arial, Liberation Sans, Carlito, and DejaVu Sans fallback chain; never claim an unavailable font.
- Dense content: compiler split; do not shrink below component minimums.
- Sparse content: focal statement or text-media; do not manufacture empty cards.
- Ambiguous relationship: structured-content family.
- Motion: off.

Direct DeckPlan remains supported for expert callers and replay, but it is marked fact-ungoverned unless an external FactStore audit accompanies it.

## Deterministic fact-to-form rules

- Keep every extracted number attached to its authored unit, including mixed-unit changes such as hours to minutes. Preserve source wording for word-form measures, source-present relative labels such as `Above Q1`, and large integer display values with thousands separators; never emit generic `Measure N` when the sentence contains an exact qualifier.
- Treat an explicit `supports/includes/offers/integrates with X, Y, and Z` construction as a parallel list only when the whole list is unambiguous; then render the items as cards. Never split a thousands separator as a list delimiter.
- Under an analytical direction, two or more categorical measures sharing one unit may become a native editable bar chart with source labels. A single scalar remains a KPI or statement.
- When every plotted measure has the same exact percent unit, keep the authored category order and use the governed 0-100 percentage-axis contract; mixed or missing units must not inherit that format.
- A trend claim without explicit ordered categories and values remains a fact-backed statement. Never infer or fabricate a chart series.
- Three short label-only items use the registered compact-card variant; items with descriptions retain detailed-card capacity. Do not invent icons, product logos, numbering, or placeholder copy.
- A single dated event uses the compact milestone treatment. Do not manufacture preceding/following stages merely to fill a timeline.
- Plain claims are statements, not quotations. Use quote styling only when the immutable fact is explicitly a quote.
- Closing titles are selected from governed action semantics. A real decision objective may use `Decision required`; other explicit actions use `Next action`; the objective itself remains unchanged.
- A layout-capacity miss triggers a same-family deterministic search before any generic fallback. The model never resolves that miss by shrinking below minimum type or rewriting evidence.
- Use the 44/32/22/18 pt title ladder only when the exact title slot fits; fall back down the ladder instead of clipping or shrinking body text below its minimum.
- Preserve governed inline emphasis as native editable rich-text runs rather than flattening the text to an image.

## Benchmark evidence

A formal ordinary-model run requires the strict `fingerprint-bundle.v1` object, not a bare or opaque hash. Its component manifests bind the Python/dependency set, OpenCode version and exact model IDs, Windows environment, non-empty installed-font inventory, PowerPoint build, and asset bindings to their canonical SHA-256 fields. The source tree must be clean and match the engine, registry, schema, Skill/reference, corpus, protocol, prompt, and threshold hashes. Manifest-only planning does not count as a formal run.

Formal execution is fail-closed under `benchmark-run-contract.v1`: it uses the default benchmark root, all 180 frozen trials, live-provider responses, the fixed 90-second per-call timeout, and `manifest_only=false`. The runner writes an immutable `run-contract.json` bound to the frozen manifest and fingerprint bundle. Response-file replay and manifest-only mode are diagnostic-only; formal resume is accepted only when the existing manifest, fingerprint, contract, and per-trial metadata match that exact contract digest.

Blind scores are valid only after each evaluated entry has one hash-verified readable OOXML PPTX and one or more byte-verified PNG previews. The builder stages them under anonymized `B-*` review paths; a packet without these staged delivery artifacts is marked not ready and the score-sheet loader fails closed.
