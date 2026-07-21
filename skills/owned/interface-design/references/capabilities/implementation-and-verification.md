# Implementation And Verification

Use this module while building and before any visual completion claim.

## Implementation Rules

- Follow the repository's framework, routing, component API, tokens, and data patterns.
- Keep semantic structure and behavior independent from decoration.
- Define stable dimensions and responsive constraints for fixed-format surfaces.
- Reserve space for images, charts, validation, and async content to prevent layout shift.
- Use progressive enhancement for optional visual effects and a usable fallback when they fail.
- Load critical fonts and first-viewport media deliberately; do not lazy-load the primary visual that defines the page.
- Keep CSS values tokenized and avoid arbitrary inline exceptions unless the exception is documented and truly local.

## Responsive Verification

For general web work, inspect 320, 375, 414, 768, and a representative desktop width. Add product-specific sizes when the target environment requires them. Check:

- no horizontal overflow or clipped focus ring;
- readable hierarchy and line length;
- tables, charts, navigation, and overlays transform intentionally;
- controls remain reachable and labels fit;
- safe areas, touch targets, pointer and hover capabilities;
- localization expansion and 200% zoom where relevant.

Do not merely shrink a desktop composition. Reorder, stack, summarize, scroll a bounded data region, or disclose progressively according to the task.

## Browser Evidence Loop

1. Start the actual app or a minimal valid local server.
2. Wait for the page-ready condition, fonts, critical images, and data state.
3. Exercise the primary path, keyboard path, and one failure or empty path.
4. Capture screenshots at target widths and inspect them visually.
5. Check console errors, failed network requests, accessibility tree or automated probes, and motion preference.
6. Fix structural defects first, rerun the same evidence, then broaden.

Use `webapp-testing` for browser automation. For canvas, WebGL, or animation-heavy work, verify nonblank pixels, framing, progression, and reduced-motion behavior rather than trusting DOM presence.

## Quality Critique

Score each dimension from 1 to 5 with evidence:

- concept and domain fit;
- information and visual hierarchy;
- typography, color, spacing, and alignment craft;
- workflow completeness and interaction states;
- specificity and truthful content;
- restraint and absence of generic template tells;
- responsive transformation and accessibility;
- implementation stability and performance.

Any score below 4 requires a fix or an explicit accepted tradeoff. Run the applicable gates in `assets/patterns/quality-checks.json` and record results in `assets/templates/visual-qa.md`.

## Completion Gate

Completion requires the accepted artifact to open in its target environment, primary interactions to work, target viewports to pass, no blocking console or network errors, critical content and assets to render, accessibility checks to pass, and screenshots to show no overlap, overflow, blank canvas, or unintended layout shift.
