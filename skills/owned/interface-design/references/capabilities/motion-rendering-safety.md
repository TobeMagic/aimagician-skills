# Motion Rendering Safety

Use this module when adapting an existing animation system or diagnosing capture artifacts. The final capture must be a pure function of accepted inputs and design time.

## Seek-Safety Checklist

- Drive DOM, SVG, Canvas, WebGL, GSAP, cursors, counters, media, and particles from one deterministic time value. Disable CSS transitions and keyframes during capture because they interpolate from prior browser state.
- Render time zero before every batch. A proxy tween, stale `lastTick`, or first-frame transition must not leave the first captured frame between states.
- Keep warm-up navigation, font loading, and GPU initialization outside the output frame directory. Recreate browser contexts only at documented batch boundaries and seek again before capture.
- Set readiness only after fonts, images, local data, shaders, and measured geometry settle. Never measure text before the final fallback font is known.
- Seed every random source. Keep scene-local colors, transforms, z-order, filters, and visibility from leaking into the next scene.
- For `file://` delivery, inline critical runtime code or serve the project locally. Validate CORS, module loading, fonts, images, audio, and fetch behavior in the actual delivery mode.
- Hide recording controls and debug overlays through explicit capture state. Do not preserve warm-up frames, replay controls, focus rings from automation, or a stale recording flag in the final source.
- Capture first, boundary, middle, reveal, poster, and final frames. Re-seek representative timestamps twice and compare hashes to prove determinism.

## Existing Timeline Libraries

Use `assets/starter/gsap-deterministic-stage.js` only when the project already has a pinned GSAP dependency. Build one paused timeline, avoid infinite repeats, expose the standard time setter, and sleep the ticker during capture. Use `assets/starter/gallery-wall-stage.js` for pure ripple, convergence, and sinusoidal-pan geometry without copying a branded scene.

## Diagnostic Order

1. Reproduce one bad timestamp with a still screenshot.
2. Check readiness, fonts, missing requests, console errors, random input, and deterministic setters.
3. Capture the same timestamp in a fresh context and compare hashes.
4. Inspect scene boundary timestamps one frame before and after the defect.
5. Fix source state; do not conceal the defect with encoding interpolation.
6. Re-render only after the still probe passes, then run media verification.

## Follow-Up Deliveries

- Smaller file: reduce dimensions or frame rate according to distribution, shorten dead holds, and enforce a fail-closed size budget; do not sacrifice text legibility blindly.
- Sharper output: capture at the required source geometry, load final fonts, avoid post-upscale, and inspect a downscaled distribution frame.
- Portrait or square: recompose at the new ratio and safe area; do not crop the landscape stage mechanically.
- Approved watermark or attribution: add it to the editable HTML source with safe-area and contrast rules, then re-render. Do not inject hidden promotion.
- Transparent background: select WebM VP9 or ProRes 4444, omit the page background, and verify alpha over light and dark composites.
- Lossless intermediate: keep the PNG sequence or approved mezzanine format, then derive distribution assets from it.
