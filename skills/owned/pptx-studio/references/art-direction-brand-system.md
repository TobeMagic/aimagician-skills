# Art Direction, Theme, and Brand System

## Direction decision

`registries/art-directions.json` contains exactly twelve independently authored native-PPTX profiles:

- Quiet: assertion/evidence, institutional grid, editorial longform, research dense.
- Neutral: consulting dual type, diagram driven, diagrammatic minimal, narrative sparkline.
- Bold: mono brand poster, stage keynote, asymmetric bento, typographic manifesto.

For each brief the selector returns exactly three candidates: safe, editorial, expressive. Scores use registered scenario/audience fit, density/rhythm, brand availability, asset requirements, locale, editability risk, and requested tone. Stable ID ordering breaks ties.

Auto mode selects the highest-confidence candidate, except that missing brand context, missing required assets, a score below 0.65, or a top-two gap below 0.05 forces the safe candidate. Interactive mode stops before COM and returns candidates plus proof-slide IDs. Locked mode accepts one registered direction and records the operator lock.

## Design tokens

The theme registry governs:

- 12-column grid, horizontal/vertical safe margins, and gutters;
- spacing scale: 0, 8, 16, 24, 32, 48, 64 pt;
- display/title/subtitle/body/label/footnote hierarchy;
- light/dark industry themes and semantic positive/warning/negative colors;
- script-aware font stacks for Latin, Simplified/Traditional Chinese, Japanese, and Korean;
- one-point borders, small/medium/large radii, restrained shadow, and decoration limits;
- image cover-crop with no stretching;
- one icon family per deck;
- native chart/table styling and an 11 pt absolute readability floor.

Themes include executive light/dark, technology, finance/investor, marketing vibrant, ecommerce editorial, education/training, and public enterprise. Direction chooses a compatible theme; a trusted explicit theme may override it.

## BrandSpec

BrandSpec is trusted input, never a weak-model output. It may specify sourced palette roles, sourced heading/body fonts, mandatory asset kinds, prohibited patterns, and whether exact fidelity is required.

Rules:

- Unknown roles and fields fail closed.
- Brand colors override all registered `primary`, `accent`, `positive`, `warning`, `negative`, and `background` roles; contrast-breaking requests produce explicit fallback evidence.
- Fonts are resolved against the real Windows inventory with script-aware fallbacks.
- Mandatory unavailable assets, declared-but-missing fonts, prohibited selected patterns, and fidelity-breaking theme fallbacks are hard gates when exact fidelity is required.
- Optional asset gaps select native editable fallback compositions.
- PNG/JPEG files require byte-verified dimensions and governed provenance. SVG is accepted only for `icon`, `vector`, or `logo`, with matching aspect evidence and no scripts, event handlers, external references, embedded images/data, entities, or doctypes.
- A full-slide raster is never accepted as an editable deliverable.

Record `direction-decision.json`, installed-font digest, BrandSpec source, asset manifest, final resolved theme, and every font/color resolution event in delivery evidence. `generation-manifest.json` stores normalized BrandSpec content plus source/path/canonical hash, the sorted installed-font list plus digest, and normalized asset bindings plus source/path/canonical hash even when the render-plan body is omitted. `--brand-spec` is valid only on the governed BriefPlan render route; legacy direct DeckPlan rendering never silently ignores it.
