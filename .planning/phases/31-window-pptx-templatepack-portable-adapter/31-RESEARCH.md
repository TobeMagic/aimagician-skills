# Phase 31 Research

## Established facts

- The authorized source contains nested grouped shapes, rotations, flips, four
  charts, and four embedded workbooks.
- Most declared text targets are nested rather than direct slide children, so
  top-level-only geometry inspection is insufficient.
- OOXML group transforms expose parent `off/ext` and child `chOff/chExt`;
  shape transforms may also rotate or flip around their center.
- The current portable chain already renders source/candidate without COM and
  records engine versions and stable hashes.
- The existing undeclared-part invariant is stronger than a visual score for
  package preservation but cannot detect candidate text spilling outside its
  declared rendered region.

## Selected metric

For each RGB channel outside the trusted union mask:

`similarity = 1 - sum(abs(source - candidate)) / (255 * channel_count)`

`changed_pixel_ratio` is the share of unmasked pixels where any channel differs
by more than 8.

Both are required because a high average can hide a small severe drift, while
changed-pixel ratio alone does not express drift magnitude.

## Risks

- Renderer antialiasing must be compared only under the same recorded engine
  fingerprint.
- Very broad masks can make the score meaningless, so coverage is capped.
- Shape rotation and nested groups require composed affine transforms.
- Charts are identified through slide relationships, not only text slot IDs.
- Automatic similarity remains insufficient for aesthetic judgment.
