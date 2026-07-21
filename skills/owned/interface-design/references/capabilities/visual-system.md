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
- For CJK content, choose fonts with complete glyph coverage, avoid synthetic italics, use appropriate punctuation and line breaking, and test mixed-script alignment.
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
