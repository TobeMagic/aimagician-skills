# Motion And HTML Presentations

Use this module for purposeful interface motion and browser-native slide narratives.

## Motion Grammar

Motion must explain cause, continuity, hierarchy, progress, or spatial relationship. Define:

- trigger and user control;
- start and end state;
- duration and easing by motion type;
- interruption, reversal, cancellation, and reduced-motion behavior;
- performance budget and fallback.

Use short direct transitions for controls, coordinated movement for layout continuity, and staged emphasis only for narrative moments. Prefer transform and opacity when they preserve layout and performance. Avoid `transition: all`, universal fade-up on scroll, bounce as a default, cursor followers, unpausable auto-rotation, and motion that obscures task completion.

Show processes rather than teleporting from input to polished result when the intermediate state builds trust. Keep focus and interaction available during non-blocking animation.

## HTML Presentation Contract

An HTML presentation is a browser-native visual source. Define aspect ratio, navigation, overview, full-screen behavior, speaker-note approach, keyboard controls, print or export behavior, and offline asset policy. It can remain browser-only or produce explicit HTML-first PDF/PPTX derivatives through `html-first-presentations.md`.

Build a narrative before slides:

1. audience decision or takeaway;
2. opening context or tension;
3. evidence and mechanism;
4. implications or alternatives;
5. recommendation and action.

Each frame has one dominant idea, one visual anchor, and an intentional density. Vary frame grammar across title, argument, evidence, comparison, process, demo, and close rather than repeating one card layout.

For an editorial or durable reading deck, start from `assets/starter/publication-slide.html`: masthead, kicker, assertion, lede, evidence protagonist, source, folio, and decision footer form a publication grammar without turning every frame into a card. Rotate the visual protagonist across number, quote, chart, diagram, product view, comparison, timeline, full-bleed evidence, and all-text frames.

For timed work, select and adapt one of `assets/patterns/motion-scene-recipes.json`. Recipes provide a starting beat budget, not a fixed story; actual narration duration, product causality, and accepted distribution always win.

## Architecture

- Use a single-file deck only when it has at most ten slides and shared interaction or animation justifies it.
- Default to multiple slide files plus shared tokens for larger decks, parallel work, independent per-frame review, or editable PPTX conversion.
- For five or more slides, approve two structurally different showcase slides before producing the full sequence.
- Give every frame stable dimensions and predictable overflow behavior.
- Keep slide labels, notes, and controls outside printable or captured content when possible.
- Verify every frame individually and in sequence.

If ordinary native `.pptx` becomes the accepted deliverable, stop browser production at the approved direction, complete `assets/templates/ppt-handoff.md`, and route to the PPT owner. If the user explicitly requires HTML-first PPTX, load `html-first-presentations.md` and keep HTML as the source of truth.
