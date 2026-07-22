# Creative Coding And Motion Media

Use this module when HTML, CSS, SVG, Canvas, WebGL, or timed DOM composition is the source for an interactive visual, motion hero, product demo, animated poster, GIF, or encoded video.

## Choose The Rendering Primitive

- Use DOM and CSS for typography, product UI, layout, and accessibility.
- Use SVG for diagrams, paths, icons, and resolution-independent geometry.
- Use Canvas for dense particles, procedural fields, pixel work, or high-frequency drawing.
- Use WebGL or Three.js only when depth, lighting, or many animated objects materially carry the concept.
- Combine primitives through explicit layers; do not use Canvas to rasterize text that must stay crisp and inspectable.

## Storyboard Before Animation

For motion work, define a sequence with scene purpose, visible proof, start/end time, transition, narration or silence, and static-poster candidate. One short product loop usually needs:

1. identity and context;
2. user action;
3. system progress or mechanism;
4. verified result;
5. a stable closing frame.

Use `assets/templates/motion-storyboard.md`. Motion must explain state, causality, or narrative. Decorative motion is subordinate and should disappear under reduced motion without losing meaning.

## Deterministic Time Contract

Encoded media must not depend on wall-clock timing. The source page must expose:

```js
window.__VISUAL_READY__ = true;
window.__setDesignTime = (seconds) => {
  // Set every scene, progress value, cursor, canvas, and transition from seconds.
};
```

`__VISUAL_READY__` becomes true only after fonts, images, and required data are ready. Calling `__setDesignTime(t)` repeatedly with the same value must produce the same pixels. Pause CSS animations, requestAnimationFrame loops, media elements, blinking cursors, and random sources during deterministic capture. Seed procedural randomness.

The framework-neutral clock scaffold is `assets/starter/motion-stage.js`. React work may use `assets/starter/react-motion-stage.jsx`. Both support Stage/Sprite intervals, pure seek, easing, interpolation, and seeded state. The fixed-format composition scaffold is `assets/starter/repository-hero.html`.

When an existing project already uses GSAP, adapt it through `assets/starter/gsap-deterministic-stage.js` rather than adding a second animation engine. Gallery or multi-focus compositions may use the pure geometry in `assets/starter/gallery-wall-stage.js`. Load `motion-rendering-safety.md` for seek, warm-up, first-frame, font, file-delivery, and scene-state failure modes.

## Motion Language

- Build anticipation, action, and follow-through rather than linear appearance/disappearance.
- Show the process that produces a result; do not teleport from prompt to polished outcome.
- Use shared-element or directional continuity between scenes. A scene change reflects a conceptual change, not every small step.
- Use focused easing: strong ease-out for reveal, ease-in-out for travel, and a short hold before a critical result.
- Coordinate stagger, depth, focus, and camera movement around one narrative beat. Do not animate every element independently.
- For long motion, use a five-beat arc: establish, build, accelerate, reveal, hold.

## Production Pitfalls

Use relative positioning for layered scenes, load fonts before measurement, and keep render functions pure under seek. Use PID-isolated temporary directories for concurrent export. Hide progress, replay, and browser controls during capture. Set an explicit recording flag to disable loops, cursor blink, warm-up frames, and CSS transitions. Inline critical runtime code for `file://` delivery. Use contextual color tokens across light and dark scenes. Prefer deterministic frame duplication or direct capture at the target rate over interpolation that invents unstable frames.

## Media Rendering

Use `scripts/render-motion-media.mjs` to capture deterministic frames with Playwright and encode Poster, H.264 MP4, palette-optimized GIF, alpha-capable WebM or ProRes 4444 MOV, PNG sequences, or any requested combination. The renderer waits for completed browser paints, rebuilds the capture page in bounded batches to release compositor resources, and writes regular keyframes for reliable seeking. Preserve:

- editable source;
- poster WebP;
- final MP4, GIF, transparent overlay, and/or PNG sequence required by the delivery contract;
- render settings and validation output.

Choose media from the distribution contract:

- short silent README or repository loop: tracked GIF with an explicit size budget;
- longer, high-detail, or audio-bearing delivery: MP4 plus Poster;
- interactive or user-controlled experience: HTML;
- fixed still: WebP, PNG, or SVG according to content.
- compositing overlay: transparent WebM or ProRes 4444 MOV plus an alpha-channel inspection.

Do not add narration, music, sound effects, remote font dependencies, tracking, or watermarks unless the brief explicitly requires and licenses them. When sound is required, load `audio-and-narration.md`.

## Validation

Inspect the source in a browser and validate the encoded artifact:

- no console, network, font, image, SVG, Canvas, or WebGL failure;
- nonblank first, middle, poster, and last frames;
- stable framing, safe crop, readable type, and no overlapping controls;
- no black flashes, duplicated scene jumps, clipping, or unintended layout shifts;
- expected width, height, duration, frame rate, codec, pixel format, and file size;
- static poster communicates the core product without motion;
- reduced-motion mode remains understandable for interactive delivery.

Capture at exact geometry. Also inspect a downscaled frame because a technically correct 1600px video can still be unreadable in a 700px README column.

Run `scripts/verify-motion-media.mjs` for encoded artifacts. Run `scripts/prepare-motion-review.mjs` to create objective freeze/silence evidence, representative frames, and a provider-neutral semantic-review prompt. A vision model may review that package, but it must cite frames and cannot replace deterministic checks.

Choose the render path explicitly:

| Need | Route |
|---|---|
| DOM, SVG, Canvas, ordinary WebGL, GIF, MP4, alpha overlay, or PNG sequence fits local resources | `render-motion-media.mjs` |
| The project already has a specialized renderer, remote farm, advanced shader stack, or scale requirement | `render-with-adapter.mjs` plus a project-owned adapter |
| Backend choice is uncertain | Produce a short representative render in both viable routes and compare fidelity, determinism, cost, security, and operability before full production |

Pin and validate the selected backend in the project. Keep adapters project-local and side-effect free; do not mutate user configuration or hide provider credentials in a manifest. For size, sharpness, new aspect ratios, approved attribution, alpha, and lossless-intermediate follow-ups, use `motion-rendering-safety.md` rather than ad hoc encoding guesses.
