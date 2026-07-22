# Audio And Narration

Use this module for narrated explanations, launch films, motion demos, tutorials, music, or sound effects. Audio is a designed information layer, not a default decoration.

## Sound Contract

Before producing sound, define:

- whether the delivery is silent, effects-only, music-led, narrated, or mixed;
- audience, locale, transcript, accessibility, duration, and distribution loudness;
- source, ownership, license, and allowed use for every clip;
- voice character and pronunciation without binding the project to a provider;
- whether browser playback must begin muted or only after explicit user action.

Never autoplay sound in a browser. Never bundle unlicensed music, effects, voices, credentials, or provider-specific identity into the skill.

## Narration-Driven Workflow

1. Write and approve the narration as short semantic segments using `assets/templates/narration-script.md`, `## scene-id` headings, and optional `[[cue:id]]` markers.
2. Run `scripts/compile-narration-timeline.mjs` once to generate the provider-neutral TTS manifest.
3. Use `scripts/render-narration-tts.mjs` with a project-selected adapter. The adapter owns provider authentication through environment variables and exports `synthesize()`.
4. Run `scripts/compile-narration-timeline.mjs` again with the generated audio directory to measure actual clip durations, concatenate an optional voiceover track, and write the `NarrationStage` timeline. Optional `<scene>.words.json` sidecars provide exact word and cue timing; proportional fallback cues must remain marked as estimates and be reviewed.
5. Build one continuous visual timeline from measured voice timing using `assets/starter/narration-stage.jsx`.
6. Create `assets/templates/audio-cues.json` for voice, music, and effects with start, duration, gain, fade, source, and license.
7. Mix with `scripts/mix-motion-audio.mjs`, using music ducking under voice and restrained effects at meaningful causal events.
8. Verify sync, intelligibility, clipping, true peak, integrated loudness, silence, transcript, and final container playback.

## Motion Relationship

Long-form narrated work is one continuous motion narrative, not a sequence of PowerPoint-like cuts. Let voice meaning drive focus, reveal, camera, and hold time. Use scene changes only when the conceptual state changes. Preserve continuity with shared elements, directional movement, or audio bridges.

Effects should confirm cause, success, transition, or material character. Music controls pace and emotional continuity but must not mask speech. Keep a visual-only intermediate and the final mixed output so defects can be isolated.

## Provider-Neutral TTS Adapter

An adapter is a local ESM module:

```js
export async function synthesize({ id, text, voice, locale, outputPath }) {
  // Read provider credentials from environment variables and write outputPath.
}
```

The skill never stores tokens. If no authorized adapter exists, stop with the narration manifest and report the missing provider rather than fabricating audio. An adapter may return `words[]` entries containing `text`, clip-relative `start`, `end`, and optional `char_start`; the TTS runner writes the portable `<scene>.words.json` sidecar without embedding a provider contract.

## Acceptance

Deliver the approved script, narration manifest, generated clip inventory, measured timeline, cue sheet, provenance, visual-only media, mixed media, transcript or captions, and validation report. Report any provider, pronunciation, licensing, or loudness uncertainty explicitly.
