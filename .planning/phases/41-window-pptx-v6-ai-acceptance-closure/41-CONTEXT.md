# Phase 41 Context

## Implementation Decisions

- Acceptance is AI-only, as explicitly requested by the user.
- Three visual-capable reviewers use fresh, isolated contexts and anonymous,
  hash-bound images.
- The calibration reference controls craft complexity, hierarchy, and finish;
  it does not require palette, industry, density, typography, or motif copying.
- Engineering evidence and visual evidence are separate gates.
- Provider unavailability or an invalid/misattributed review is `NOT_RUN`, not a
  pass or fail score.

## Existing Patterns To Preserve

- Anonymous hash-bound candidate IDs and physically labeled slide evidence.
- Fresh isolated reviewer contexts with immutable raw reports.
- Deterministic score floors and same-slide consensus detection.
- Separate engineering, visual, and independent completion-audit gates.

## Allowed Scope

- Anonymous evidence packets, visual-review protocol, deterministic
  aggregation, final audit/validation documents, state/roadmap updates, and
  release documentation.

## Forbidden Scope

- Manual score overrides, threshold reduction, imputed reviewers, continued
  contexts, generator/model disclosure, or hiding failed rounds.
- Declaring GO while any requirement is FAIL/NOT_RUN or any consensus
  Blocker/Important remains.

## Integration And Compatibility

The final gate consumes immutable PPTX/PNG hashes plus OOXML/editability
evidence. It does not change generation behavior and remains independent of
COM availability.
