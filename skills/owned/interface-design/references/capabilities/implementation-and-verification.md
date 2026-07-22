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

Score each expert dimension from 1 to 10 with evidence, then run the implementation and accessibility gates separately:

- concept and strength of the central idea;
- consistency between the selected philosophy and every design decision;
- visual hierarchy and message priority;
- craft quality across typography, color, spacing, imagery, alignment, and motion;
- functionality, interaction completeness, responsive behavior, and accessibility;
- originality and absence of generic template or AI-generated visual habits.

Any score below 8 requires a fix or an explicit accepted tradeoff. Review stills directly and motion through representative playback plus the package from `scripts/prepare-motion-review.mjs`. A vision-model review may add findings but never replaces deterministic geometry, browser, frame, codec, size, audio, or accessibility checks. Run the applicable gates in `assets/patterns/quality-checks.json` and record results in `assets/templates/visual-qa.md`.

## Completion Gate

Completion requires the accepted artifact to open in its target environment, primary interactions to work, target viewports to pass, no blocking console or network errors, critical content and assets to render, accessibility checks to pass, and screenshots to show no overlap, overflow, blank canvas, or unintended layout shift. Fixed media must also pass representative-frame, duration, loop, codec, loudness when applicable, and file-budget checks. HTML-first derivatives must match the selected editable or fidelity contract.
