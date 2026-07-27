# Phase 31 Context

## Behavior contract

Given a registered TemplatePack, source-hash-bound bindings, and a portable
renderer, the system produces an editable candidate and proves that all
rendered changes stay inside the pack's declared editable regions. Any
undeclared visual drift, untrusted mask, transform ambiguity, or renderer
mismatch stops promotion.

## Context map

```text
template.pptx + template-pack.json
        |
        +--> template_pack.py --------> adapted candidate.pptx
        |
        +--> template_geometry.py ----> trusted visual masks
                                         |
source/candidate portable PNGs --------> visual_similarity.py
                                         |
                                         +--> similarity report + hard gate

eval bindings + all gates ------------> golden_template_replay.py
                                         |
                                         +--> compact evidence manifest
```

Owners:

- `template_pack.py`: source/hash/slot mutation boundary.
- `template_geometry.py`: source-only OOXML geometry and relationship
  inventory.
- `visual_similarity.py`: rendered comparison; no package mutation.
- `golden_template_replay.py`: orchestration and compact evidence only.
- TemplatePack manifest/schema: trusted policy and masks.

## Design alternatives

### A. Restore declared OOXML parts and compare

Rejected. It proves package restoration, not candidate rendering. Text overflow
or a renderer defect outside the intended shape would disappear when parts are
restored.

### B. Build masks from observed pixel differences

Rejected. It is self-referential: any regression becomes masked because it is
different.

### C. Derive masks from hash-bound source geometry

Selected. It is independent of candidate pixels, reviewable, deterministic,
and detects overflow beyond declared shapes. Nested group transforms and chart
relationships are the main implementation risk and receive direct tests.

## Compatibility and rollback

- Existing packs without visual masks continue to load for adaptation, but
  cannot claim `P31-SIM-01`; the scorer fails with a missing-mask error.
- The manifest extension is additive and versioned.
- The existing reference-quality and portable proof paths remain unchanged.
- Rollback is removal of the new scoring/replay route; adaptation behavior is
  not migrated or rewritten.

## Test seams

- Pure OOXML geometry extraction from synthetic nested-group fixtures.
- Pure Pillow similarity scoring from small generated PNGs.
- TemplatePack schema/loader validation.
- Golden replay orchestration with real institutional pack and LibreOffice.
- Tamper tests for source hash, renderer identity, page shape, and masks.
