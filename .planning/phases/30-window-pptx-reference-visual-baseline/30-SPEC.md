# Phase 30 Specification: Reference Visual Baseline and Contracts

**Status:** Locked
**Risk:** high
**User-facing:** yes
**Requirements:** V51-REF-01, V51-TPL-01, V51-TPL-02, V51-TPL-03, V51-DESIGN-01, V51-DESIGN-02, V51-DESIGN-03, V51-DESIGN-04, V51-QA-01, V51-QA-02, V51-QA-03, V51-BENCH-01, V51-UAT-01

## Goal

Replace the sparse v5.0 visual floor with a reference-grade, portable-first architecture that lets ordinary models either adapt an authorized high-quality PPTX through governed slots or compose an independent deck from governed DesignPacks.

## Current

The portable PptxGenJS/OOXML/LibreOffice chain is structurally reliable and editable, but current layouts average only 3–6 objects per slide and visually fail the user's supplied reference bar. The authorized reference has 15 slides, one master, three layouts, 29 media assets, four charts, four embedded workbooks, gradients, cropped images, connectors, and deeply grouped editable shapes.

## Target

1. `TemplatePack` preserves physical PPTX design and replaces only validated editable slots.
2. `DesignPack` owns theme, composition recipes, capacities, assets, rhythm, and safe fallbacks.
3. `AssetPlan` and `VisualPlan` are deterministic compiler artifacts.
4. Reference-grade QA measures visual coverage, entropy, repetition, density, editability, and non-slot similarity.
5. COM is optional certification only.

## Boundaries

### In scope

- User-authorized distribution of `工作总结.pptx` inside the Skill.
- Portable OOXML slot replacement and package preservation.
- Editable text/data/core shapes.
- Four DesignPack contracts covering all fifteen scenarios.
- LibreOffice/Poppler render proof and visual regression.

### Out of scope

- Whole-slide screenshots as PPTX pages.
- Model-authored HTML/CSS/OOXML/JavaScript.
- Mandatory COM for generation.
- Automatic registry repair for PowerPoint/WPS TypeLib issues.
- Claiming v5.0 diagnostic scores as v5.1 visual acceptance.

## Acceptance

- [x] Authorized reference manifest and slot map validate against the source hash.
- [x] A no-op adaptation preserves every package part byte-for-byte.
- [x] A content adaptation changes only declared slide XML parts and emits an atomic report.
- [x] Adapted PPTX opens and renders to 15 PNG pages without COM.
- [x] Semantic text remains editable and extractable.
- [ ] Non-slot visual similarity is at least 0.98.
- [x] Historical sparse r12 fails the reference-grade visual profile.
- [ ] Four representative DeepSeek trials and blind review remain explicit later gates.

## Ambiguity Report

Goal clarity: 0.99
Boundary clarity: 0.98
Constraint clarity: 0.98
Acceptance clarity: 0.97
Ambiguity: 0.02

## Decisions

- The user authorized the reference template, master, media, and vector objects to be packaged and distributed with this Skill.
- First acceptance reuses the reference visual language but replaces its content with a new work-summary narrative.
- `TemplatePack` and `DesignPack` are separate governed paths; neither silently degrades into the other.
- HTML remains proof-only. COM remains optional certification for animation, macros, plugins, or final Microsoft PowerPoint sampling.
