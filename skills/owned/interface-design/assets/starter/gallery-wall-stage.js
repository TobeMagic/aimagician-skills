/** Pure deterministic geometry for gallery-wall and multi-focus motion. */
const GalleryWallStage = (() => {
  const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, value));
  const mix = (from, to, progress) => from + (to - from) * progress;
  const easeOut = (progress) => 1 - Math.pow(1 - clamp(progress), 3);

  function ripple(items, focusIndex, progress, spacing = 48) {
    const eased = easeOut(progress);
    return items.map((item, index) => {
      const distance = Math.abs(index - focusIndex);
      const direction = Math.sign(index - focusIndex);
      return { ...item, x: item.x + direction * distance * spacing * eased, scale: mix(1, index === focusIndex ? 1.08 : 0.92, eased) };
    });
  }

  function cornerConvergence(items, progress, width, height, inset = 48) {
    const targets = [
      { x: inset, y: inset }, { x: width - inset, y: inset },
      { x: width - inset, y: height - inset }, { x: inset, y: height - inset },
    ];
    const eased = easeOut(progress);
    return items.map((item, index) => {
      const target = targets[index % targets.length];
      return { ...item, x: mix(item.x, target.x, eased), y: mix(item.y, target.y, eased) };
    });
  }

  function sinusoidalPan(time, { amplitudeX = 28, amplitudeY = 16, period = 8, phase = 0 } = {}) {
    const angle = (time / period) * Math.PI * 2 + phase;
    return { x: Math.sin(angle) * amplitudeX, y: Math.cos(angle * 0.5) * amplitudeY };
  }

  return { ripple, cornerConvergence, sinusoidalPan };
})();
