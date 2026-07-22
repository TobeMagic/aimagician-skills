# Narration Script

Write one approved semantic scene under each `## scene-id` heading. IDs use lowercase letters, numbers, dots, underscores, or hyphens and remain stable across the TTS manifest, timeline, React scenes, tests, and revisions.

Place `[[cue:id]]` immediately before the spoken phrase or visual event it should trigger. Cue IDs are globally unique. The compiler removes markers from speech, measures generated clips, and maps each cue from provider word timestamps when available; otherwise it emits a labeled proportional estimate that requires review.

## opening

Replace this paragraph with the approved opening narration. [[cue:product-proof]]Now reveal the verified product proof.

## mechanism

Explain the mechanism in short spoken sentences. [[cue:result]]End on the measured result and its limitation.

## close

Resolve the argument in language that works with or without sound. [[cue:final-hold]]Hold the final proof long enough to read and use it as a poster candidate.

## Review

- Read the complete script aloud before synthesis.
- Confirm pronunciation, locale, names, numbers, abbreviations, and text normalization.
- Keep each scene semantically coherent; split long paragraphs rather than estimating duration from character count.
- Preserve the script as transcript and caption source.
