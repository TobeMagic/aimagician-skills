# Creative Coding And Motion Media

Use this module when HTML, CSS, SVG, Canvas, WebGL, or timed DOM composition is the source for an interactive visual, motion hero, product demo, animated poster, or encoded video.

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

The reusable clock scaffold is `assets/starter/motion-stage.js`. The fixed-format composition scaffold is `assets/starter/repository-hero.html`.

## Media Rendering

Use `scripts/render-motion-media.mjs` to capture deterministic frames with Playwright and encode a silent H.264 MP4 with ffmpeg. The renderer waits for completed browser paints, rebuilds the capture page in bounded batches to release compositor resources, and writes regular keyframes for reliable seeking. Preserve:

- editable source;
- poster WebP;
- final MP4;
- render settings and validation output.

Do not add narration, music, sound effects, remote font dependencies, tracking, or watermarks unless the brief explicitly requires and licenses them. A silent product loop is preferable to unverified media.

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
