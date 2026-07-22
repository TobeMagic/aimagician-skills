(function initializeDeterministicStage() {
  const root = document.documentElement;
  const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
  const interpolate = (value, inputStart, inputEnd, outputStart, outputEnd) => {
    if (inputStart === inputEnd) return outputEnd;
    const progress = clamp((value - inputStart) / (inputEnd - inputStart));
    return outputStart + (outputEnd - outputStart) * progress;
  };
  const easings = {
    linear: (value) => value,
    inOutCubic: (value) => value < 0.5 ? 4 * value ** 3 : 1 - ((-2 * value + 2) ** 3) / 2,
    outExpo: (value) => value === 1 ? 1 : 1 - 2 ** (-10 * value),
    outBack: (value) => {
      const c1 = 1.70158;
      const c3 = c1 + 1;
      return 1 + c3 * (value - 1) ** 3 + c1 * (value - 1) ** 2;
    }
  };

  function seededRandom(seed = 1) {
    let state = Number(seed) >>> 0 || 1;
    return () => {
      state ^= state << 13;
      state ^= state >>> 17;
      state ^= state << 5;
      return (state >>> 0) / 4294967296;
    };
  }

  function createStage({ duration = 8, scenes = [] } = {}) {
    const state = { duration: Math.max(0.001, Number(duration) || 8), time: 0, scenes: [] };

    const addScene = ({ id, start, end, render }) => {
      if (!id || typeof render !== "function") throw new Error("A scene requires id and render()");
      const normalized = { id, start: Number(start), end: Number(end), render };
      if (!Number.isFinite(normalized.start) || !Number.isFinite(normalized.end) || normalized.end <= normalized.start) {
        throw new Error(`Invalid interval for scene ${id}`);
      }
      state.scenes.push(normalized);
      state.scenes.sort((left, right) => left.start - right.start || left.id.localeCompare(right.id));
      return api;
    };

    const seek = (seconds) => {
      const time = clamp(Number(seconds) || 0, 0, state.duration);
      state.time = time;
      const progress = clamp(time / state.duration);
      const activeScenes = [];
      for (const scene of state.scenes) {
        const sceneProgress = clamp((time - scene.start) / (scene.end - scene.start));
        const active = time >= scene.start && time <= scene.end;
        scene.render({ time, progress, sceneProgress, active, easing: easings, interpolate, clamp });
        if (active) activeScenes.push(scene.id);
      }
      root.style.setProperty("--design-time", String(time));
      root.style.setProperty("--design-progress", String(progress));
      root.dataset.scene = activeScenes.at(-1) ?? String(Math.min(4, Math.floor(progress * 5)));
      window.dispatchEvent(new CustomEvent("design-time", { detail: { time, progress, activeScenes } }));
      return { time, progress, activeScenes };
    };

    const api = {
      addScene,
      seek,
      get duration() { return state.duration; },
      get time() { return state.time; },
      get scenes() { return [...state.scenes]; }
    };
    for (const scene of scenes) addScene(scene);
    return api;
  }

  const defaultStage = createStage({ duration: Number(root.dataset.duration) || 8 });
  window.DesignStage = { clamp, interpolate, easings, seededRandom, createStage, defaultStage };
  window.__VISUAL_READY__ = false;
  window.__setDesignTime = (seconds) => defaultStage.seek(seconds);

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
