# Visual System

Use this module after information architecture and before component-level polish.

## Token Contract

Define semantic tokens before building repeated surfaces:

- canvas, surface, elevated surface, border, divider;
- primary, secondary, muted, inverse, and disabled text;
- accent, accent contrast, selection, focus, success, warning, danger, and info;
- spacing, content width, grid gap, radius, border weight, shadow, and layer;
- display, body, mono, type scale, line height, weight, and measure;
- motion duration, easing, distance, and reduced-motion behavior.

Use variables rather than improvising values inside components. Keep a small coherent scale, but preserve existing project tokens when they already work.

## Layout And Space

- Choose a grid that reflects content relationships, not merely equal columns.
- Use asymmetry to create focus while retaining alignment anchors.
- Let dense operational surfaces use tighter spacing than editorial or marketing surfaces.
- Use stable dimensions and responsive constraints for controls, charts, boards, tables, slide frames, and media.
- Avoid identical section padding and repeated card bands that flatten the page rhythm.
- Cards frame independent repeated items; they are not the default container for every section.

## Typography

- Use at most two primary type families plus mono when code or tabular data requires it.
- Assign clear roles: display, heading, body, label, caption, numeric, code.
- Match display size to copy length and container; never scale type directly with viewport width.
- Keep body measure readable and line height proportional to line length.
- Use `font-variant-numeric: tabular-nums` where values compare vertically.
- For CJK content, choose an open or project-approved family with complete target-language glyph coverage. Order fallbacks by intended CJK language before generic `sans-serif`; a Latin-first fallback can produce mismatched punctuation and numerals.
- Test CJK and Latin x-height, cap height, baseline, weight, and perceived size together. When they differ, use separate semantic spans or a compatible pair rather than arbitrary vertical offsets.
- Avoid synthetic italics for scripts without an approved italic face. Use weight, color, rules, quotation marks, or emphasis dots according to language conventions.
- Chinese body text normally needs more line height than Latin text. Test full-width punctuation, brackets, consecutive punctuation compression, hanging punctuation, forbidden line starts and ends, mixed numerals, acronyms, and tabular values in the actual renderer.
- Keep ordinary CJK letter spacing at `0`; apply tracking only to tested display text. Do not add spaces between CJK characters to imitate tracking.
- For large web font files, subset only from known shipped content and declare `unicode-range` slices with a complete fallback. Dynamic or user-entered text requires the full approved font path.
- Letter spacing is `0` unless the accepted brand system has an explicit, tested reason.

## Color

- Derive palette roles from brand, content, environment, and accessibility needs.
- Prefer perceptual color spaces such as OKLCH when supported; define compatible fallbacks when required.
- Keep neutral surfaces distinguishable without turning the whole interface into one hue family.
- Limit accent footprint so actions and state remain meaningful.
- Never rely on color alone for state, and test contrast on the actual surface beneath text or controls.
- Gradients are allowed only when they communicate depth, light, data, or brand intent; they are not a default background or headline treatment.

## Imagery And Icons

Use actual product states, objects, places, people, diagrams, charts, or generated bitmap assets when the user needs to inspect something real. Define aspect ratio, crop behavior, focal point, loading, alt text, and fallback. Use one consistent icon family and familiar symbols for actions; do not use generic emoji as interface icons.

Record the final token system and rationale in `assets/templates/design-system.md`.

## Direction Vocabulary

When brand context does not determine a direction, load `assets/patterns/visual-direction-patterns.json`. It provides twenty browser-oriented and twenty presentation-oriented direction families across bold, balanced, and quiet intensity, with implementation difficulty and font-profile guidance. Treat these as decision vocabulary, not templates or identities to copy. Select from content, audience, density, media, accessibility, and implementation constraints, then adapt the system to the actual product.

Before accepting a system, query `assets/patterns/anti-template-rules.json`. A detected trap requires the named structural recovery or an explicit evidence-backed reason to retain it.
