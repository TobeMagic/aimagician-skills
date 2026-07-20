# Phase 22 Research: Existing Capability and Safety Audit

**Researched:** 2026-07-19
**Status:** Evidence recorded; Windows runtime verification pending

## Evidence Sources

This assessment separates observed evidence from architectural inference.

- **Repository evidence:** the pre-v5 `SKILL.md`, references, templates, legacy helper, tests, and approved v5 plan were read locally.
- **OpenCode evidence:** a strict read-only exploration completed successfully with OpenCode 1.17.6 using `opencode/deepseek-v4-flash-free`.
- **Implementation evidence:** focused task reports and independent reviews cover the Phase 22 safety slices.
- **Inference:** predictions about ordinary-model failure are reasoned from decision openness and missing deterministic constraints; they are not benchmark results.

## OpenCode Audit Record

| Field | Evidence |
|---|---|
| Objective | Read-only exploration of the current `window-pptx` Skill, helper, workflow, risks, and test seams before modification |
| Version | OpenCode 1.17.6 |
| Model | `opencode/deepseek-v4-flash-free` |
| Session | `ses_0851c3613ffex5lbFoDiWEU5oz` |
| Preflight | Successful |
| Run | Successful, with continuous activity and no retry |
| Export | Sanitized session export succeeded at `/tmp/window-pptx-v5-phase22-opencode.json` |
| Configuration | No OpenCode configuration changes |
| Independent disposition | P0 findings and test seams were checked locally; the suggested unsafe `--legacy-v4` bypass was rejected |

The `/tmp` export is transient run evidence, not a committed repository artifact. Claims in this phase are grounded in committed code/reports rather than assuming the audit is authoritative.

## Initial Capability Assessment

### Observed strengths before v5

- The Skill already documented a discuss gate, project-folder contract, template/source discovery, Windows/WSL boundaries, native COM execution, add-in discovery, asset workflows, script management, and broad advanced-production guidance.
- The helper could initialize projects, inspect add-ins/plugin surfaces, open or create presentations, add basic content, save decks, export PDF/PNG, and emit JSON.
- The reference library already covered COM capabilities, folder and module management, template recommendation, assets, scripts, and production lessons.
- PowerPoint COM was correctly treated as the core path and iSlide/OKPlus as optional rather than required engines.

### Observed gaps and P0 risks

The repository/OpenCode audit identified safety and determinism gaps in the legacy helper: dry-run routing was not a strict zero-side-effect contract; output/source/staging policy was not centralized; COM ownership depended on inference; macro-security restoration was not a shared invariant; inspection and presentation routes were coupled; saves were not candidate-first transactions; export sizing used fixed assumptions; and `SKILL.md` linked a missing editable-deliverable reference.

The Phase 22 implementation now addresses these code paths, but real Windows behavior is still unproven.

## Capability Boundary Against the Requested Production System

| Capability | Initial state | v5 requirement |
|---|---|---|
| Content intake | Discuss gate and REQUEST template | Versioned DeckPlan and 15 narrative archetypes |
| Content planning | Guidance-heavy | Deterministic semantic mapping, capacity, splitting, rhythm |
| Visual design | Handbook/examples | Eight governed themes and tokens |
| Layout selection | Model/template judgment | 24 families, 72+ variants, ranked candidates |
| Assets | Discovery/download guidance | Provenance, crop, icon, fallback, and manifest rules |
| Charts/tables/diagrams | COM guidance and ad hoc scripting | Native editable object renderers with coverage gates |
| PPTX implementation | Legacy general-purpose facade | Transactional compiler and core renderer |
| QA | Manual guidance and limited checks | Five-layer snapshots, schemas, hard gates, bounded repair |
| Weak-model support | Mostly prompt/process guidance | Safe defaults, constrained choices, decision traces, benchmark |

## Ordinary-Model Failure Inferences

These are design hypotheses to test in Phase 28, not measured results:

1. A weak model is likely to copy text into repeated boxes because page-type choice and information hierarchy are open-ended.
2. It is likely to exceed visual capacity because splitting/merging rules and density limits are not executable.
3. It may choose inconsistent typography, color, spacing, and decoration when design guidance is prose rather than tokens.
4. It may flatten editable content or use screenshots when native-object requirements are not hard gates.
5. It may stop after first generation because overflow, overlap, repetition, compatibility, and reopen checks are not an enforced loop.
6. It may produce unstable results across reruns because layout selection lacks deterministic scoring, confidence, and fallback traces.

## Research Conclusion

The initial Skill was a capable expert handbook and automation scaffold, not yet a deterministic production compiler. Phase 22 must close safety risks first. Phases 23–29 then convert expert judgment into schemas, rules, registries, native renderers, QA, benchmark evidence, and Windows acceptance.
