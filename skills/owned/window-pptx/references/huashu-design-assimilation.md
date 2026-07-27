# Huashu Design Assimilation Record

## Reproducible source boundary

- Upstream: `https://github.com/alchaincyf/huashu-design`
- Reviewed commit: `32cc58127f6074965e72530a2b593dac43572ec6`
- Git archive SHA-256: `0ce6833f2e1c6426d7dd01de277a8a1fe8bd999ca2e5a52c8fcc71c045da53d5`
- Reviewed subtree SHA-256: `e71d9ad375dac683e80d91e8e1d8425a00ef91f128a2ed641d83eb4f613f4f81`
- LICENSE SHA-256: `6d6a2a9caf2e6d2b76974050427053b2892d8aa4c33fd168ce63a537fcee9d96`
- License: MIT; notice copied to `third_party/huashu-design-LICENSE`.

The upstream is a design-method reference only. No Huashu runtime, prompts, style prose, HTML conversion code, showcases, media, fonts, or generated decks are copied into Window-PPTX.

## Decisions

| Observed principle | Decision | Independent Window-PPTX implementation |
|---|---|---|
| Decide story before layout | Adapt | FactStore → BriefPlan → NarrativePlan → DeckPlan authority chain |
| Offer multiple visual directions | Adapt | Twelve neutral profiles; deterministic safe/editorial/expressive candidates |
| Separate content planning and visual production | Accept/adapt | Strict semantic contract followed by registry compilation |
| Use reusable style systems | Adapt | Native theme/art-direction/layout/component registries |
| Review representative pages before full production | Adapt | Deterministic proof-slide IDs and interactive direction stop |
| Validate output visually | Accept/adapt | OOXML inspection, LibreOffice/Poppler proof, optional PowerPoint certification, QualityReport v2, bounded repair |
| HTML/CSS as the primary slide renderer | Reject | Governed native-editable PPTX objects are mandatory; portable PptxGenJS is the default and COM is capability-specific |
| Prompt-only style catalog | Reject | Typed registry with controlled IDs and deterministic selectors |
| Arbitrary model-written visual code | Reject | Raw design, code, macros, and scripts are forbidden at the model boundary |
| Copy upstream prompts/styles/media | Reject | Clean-room implementation and MIT notice only |

This combination aims for complementary strengths: Huashu-inspired design-process discipline plus Window-PPTX fact governance, deterministic native-object engineering, transaction safety, and automated quality gates.
