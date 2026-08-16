# HTML-First Presentations

Use this module only when the user explicitly wants HTML to remain the presentation source. Browser HTML is the primary artifact; PDF and PPTX are derivatives generated from that source.

## Contract Selection

Before the first slide, lock one output contract:

| Contract | HTML freedom | PPTX editability | Use when |
|---|---|---|---|
| Browser HTML | Full | Not applicable | The presentation runs in a browser. |
| HTML plus PDF | Full | Not applicable | Visual fidelity, printing, or archival distribution matters. |
| HTML plus editable PPTX | Constrained | Native text, shapes, lists, and images | Recipients must edit content in PowerPoint. |
| HTML plus fidelity PPTX | Full | Slide image only | The user explicitly wants PPTX packaging but visual fidelity matters more than object editing. |

If PPTX mode is unspecified, stop and ask editable versus fidelity. Never infer this tradeoff from the word “PPTX.” Use `scripts/design-router.mjs --pipeline html-first` to surface the decision.

## Deck Architecture

- For five or more slides, build two structurally different showcase slides and obtain direction approval before bulk production.
- Use one self-contained deck with `assets/starter/deck-stage.js` for at most ten slides when shared state or in-deck animation matters. Preserve an existing custom player only when it passes the same runtime and export contract.
- Default to independent slide HTML files plus `assets/starter/deck-index.html` for long decks, isolated CSS, parallel work, and editable conversion.
- Keep shared tokens, fonts, assets, slide manifest, and notes explicit. Each slide must open and verify independently.
- Provide keyboard navigation, overview, full screen, progress, local persistence, speaker notes, and print behavior without placing controls inside captured slide content.
- For long-deck overview performance and visual review, run `scripts/render-deck-thumbnails.mjs`; keep the generated thumbnail manifest aligned with the deck manifest rather than loading dozens of live iframes.

### Standard Single-File Player

A standalone HTML presentation must be usable directly from a browser without a separate application shell:

- Arrow keys, Page Up/Down, Space, Home, and End navigate.
- Wheel and horizontal touch gestures navigate without firing repeatedly from one gesture.
- `Escape` or `O` opens a global overview made of selectable slide cards; either key closes it.
- `F` enters or exits full screen.
- A stable progress indicator, slide count, URL hash, and local persistence expose position.
- Print styles emit one slide per page and remove navigation chrome.
- Controls remain outside captured slide content.

Use `<deck-stage>` with direct child `<section>` elements for the reusable starter. A project-specific `#deck > .slide` implementation with a global `go(index)` function is also a supported fidelity-export contract. Test keyboard behavior, overview selection, wheel/touch navigation, full screen, console errors, and every slide at the exact stage geometry.

## Editable PPTX Mode

Editable mode translates computed DOM geometry into native PowerPoint objects. Build every slide from the first line for this target:

1. Use a declared physical slide size. Default to `960pt x 540pt`, equivalent to `LAYOUT_WIDE`.
2. Put primary text in `p`, `h1`-`h6`, or list elements. A `div` must not contain unwrapped text.
3. Put fill, border, radius, and shadow on a containing shape element, not the text element.
4. Use `img` for images; do not rely on `background-image` for convertible content.
5. Do not use arbitrary CSS gradients, Web Components, filters, or complex SVG for elements that must remain editable.
6. Use `data-pptx-merge="true"` when several paragraphs must become one editable text frame.
7. Use declared placeholders for native charts or other objects added after DOM translation.

Run `scripts/export-html-deck-pptx.mjs --mode editable`. The converter must validate dimensions, overflow, bottom safe area, unsupported CSS, text wrapping, images, and browser errors before writing any output. One failing slide fails the whole deck; partial PPTX files are not deliverables.

## Fidelity PPTX Mode

Fidelity mode permits gradients, filters, complex SVG, Canvas, and other browser-native treatments. Run `scripts/export-html-deck-pptx.mjs --mode fidelity`; each verified slide is rendered at the accepted geometry and placed as one full-slide image. State plainly that slide objects are not editable. Preserve the HTML source as the editable design artifact.

For a single interactive HTML file, run:

```bash
NODE_PATH=<playwright-and-pptxgenjs-node-modules> \
  node scripts/export-html-stage-pptx.mjs \
  --html <deck.html> \
  --out <deck.pptx> \
  --mode fidelity
```

The stage exporter accepts `<deck-stage> > section` or `#deck > .slide`. It navigates each frame in the live player, removes player chrome, captures the accepted geometry, and packages full-slide images. It intentionally rejects editable mode. When native text and shapes are required, use independent slide files and the editable converter from the beginning.

## PDF Mode

- Use `scripts/export-html-deck-pdf.mjs` for independent slide files.
- Use `scripts/export-html-stage-pdf.mjs` for a single deck-stage document.
- Verify page count, physical geometry, searchable text where expected, print backgrounds, font embedding or fallback, and absence of blank trailing pages.

## Verification

Verify the browser deck first, then the derivative. Check every slide at exact geometry, sequence, notes, overflow, fonts, links, and asset readiness. For editable PPTX, inspect OOXML or reopen in PowerPoint-compatible software and prove text and shapes are native objects. For fidelity PPTX, compare representative rendered slides pixel-for-pixel within the accepted tolerance. Native Office automation may be used as a verifier without changing HTML-first ownership.

Ordinary editable PowerPoint work that does not explicitly require HTML remains owned by `pptx-studio`.
