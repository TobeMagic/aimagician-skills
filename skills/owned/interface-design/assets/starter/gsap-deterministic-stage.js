/**
 * Optional adapter for a project that already uses GSAP. It does not load or
 * provide GSAP. The project passes its pinned gsap instance and a pure timeline
 * builder, then deterministic capture uses the standard design-time protocol.
 */
const GsapDeterministicStage = (() => {
  const easing = Object.freeze({
    reveal: 'power3.out',
    travel: 'power2.inOut',
    settle: 'power2.out',
    precise: 'none',
    elasticMaterial: 'back.out(1.4)',
  });

  function create({ gsap, duration, buildTimeline, onReady = () => {} }) {
    if (!gsap?.timeline || typeof buildTimeline !== 'function') throw new Error('Pass a pinned GSAP instance and buildTimeline(timeline)');
    if (!Number.isFinite(duration) || duration <= 0) throw new Error('duration must be positive');
    const timeline = gsap.timeline({ paused: true, defaults: { overwrite: 'auto' } });
    buildTimeline(timeline, easing);
    timeline.pause(0, false);
    const priorReady = window.__VISUAL_READY__;
    const priorSetter = window.__setDesignTime;
    window.__VISUAL_READY__ = false;
    window.__totalDuration = duration;
    window.__setDesignTime = (seconds) => {
      const time = Math.max(0, Math.min(duration, Number(seconds) || 0));
      timeline.pause(time, false);
      gsap.ticker?.sleep();
    };
    Promise.resolve(document.fonts?.ready).then(() => {
      window.__setDesignTime(0);
      window.__VISUAL_READY__ = true;
      onReady({ timeline, duration });
    });
    return {
      timeline,
      easing,
      destroy() {
        timeline.kill();
        delete window.__totalDuration;
        if (priorSetter) window.__setDesignTime = priorSetter;
        else delete window.__setDesignTime;
        window.__VISUAL_READY__ = priorReady ?? false;
        gsap.ticker?.wake();
      },
    };
  }

  return { create, easing };
})();
