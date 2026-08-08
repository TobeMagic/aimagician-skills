# Phase 34 Specification: Visual Regression, Repair, and Four-Scenario UAT

**Status:** Locked
**Depends on:** Phase 33

## Requirements

- P34-REG-01: Freeze accepted and rejected contact sheets and derive
  deterministic density, repetition, hierarchy, anchor, crop, and whitespace
  checks without pretending pixel similarity equals design quality.
- P34-REPAIR-01: Repair text fit, split/merge, layout variant, asset fallback,
  crop, alignment, and density in at most two monotonic passes while preserving
  facts and rolling back non-improvements.
- P34-UAT-01: Generate business report, project proposal, product launch, and
  data analysis artifacts through four DesignPacks. Every artifact must pass
  engineering, Quality v3, direct visual review, editability, and portable
  proof gates.
- P34-FAIL-01: The historical sparse r12/R2 class must fail the new profile
  with stable, actionable codes.
- P34-EVIDENCE-01: Preserve prompts, plans, manifests, hashes, model route,
  retries, repairs, outputs, and reviews for exact replay.

## Exit

All four representative scenarios pass with no unresolved Blocker or
Important finding. Passing one reference TemplatePack deck does not substitute
for passing the generated DesignPack lane.
