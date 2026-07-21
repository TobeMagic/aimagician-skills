(function initializeDeterministicStage() {
  const root = document.documentElement;
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

  window.__VISUAL_READY__ = false;
  window.__setDesignTime = (seconds) => {
    const time = Math.max(0, Number(seconds) || 0);
    const duration = Math.max(0.001, Number(root.dataset.duration) || 8);
    const progress = clamp(time / duration, 0, 1);
    root.style.setProperty("--design-time", String(time));
    root.style.setProperty("--design-progress", String(progress));
    root.dataset.scene = String(Math.min(4, Math.floor(progress * 5)));
    window.dispatchEvent(new CustomEvent("design-time", { detail: { time, progress } }));
  };

  const imagesReady = Promise.all(
    [...document.images].map((image) => image.complete
      ? Promise.resolve()
      : new Promise((resolve) => {
          image.addEventListener("load", resolve, { once: true });
          image.addEventListener("error", resolve, { once: true });
        }))
  );

  Promise.all([document.fonts?.ready ?? Promise.resolve(), imagesReady]).then(() => {
    window.__setDesignTime(0);
    window.__VISUAL_READY__ = true;
  });
}());
