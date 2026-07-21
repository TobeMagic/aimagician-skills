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

An HTML presentation is a browser-native visual experience, not a PowerPoint file. Define aspect ratio, navigation, overview, full-screen behavior, speaker-note approach, keyboard controls, print or PDF behavior if needed, and offline asset policy.

Build a narrative before slides:

1. audience decision or takeaway;
2. opening context or tension;
3. evidence and mechanism;
4. implications or alternatives;
5. recommendation and action.

Each frame has one dominant idea, one visual anchor, and an intentional density. Vary frame grammar across title, argument, evidence, comparison, process, demo, and close rather than repeating one card layout.

## Architecture

- Use a single-file deck only when small, self-contained, and maintainable.
- Use multiple slide files plus shared tokens for larger decks, parallel work, or independent per-frame review.
- Give every frame stable dimensions and predictable overflow behavior.
- Keep slide labels, notes, and controls outside printable or captured content when possible.
- Verify every frame individually and in sequence.

If native `.pptx` becomes the accepted deliverable, stop browser production at the approved direction, complete `assets/templates/ppt-handoff.md`, and route to the PPT owner. Do not constrain a creative HTML exploration to a lossy conversion path unless the user accepts that tradeoff explicitly.
