# Phase 36 Context

## Baseline

- v5.1 archive commit: `e4ed78c7b31beebdb94f0f37c6c412012dfec085`
- Original v5 branch: `70d1b6762acdbe0732a502e8d1e151f3957323eb`
- Python baseline: `792` collected, `789` passed, `3` failed
- Vitest baseline: `108/108`
- Build, typecheck, formatter, and diff checks: PASS

The archived failures are:

1. unfilled governed CTA slots in the asset-materialized generation path;
2. `BASELINE` versus `START` trend-label expectation drift;
3. one of two training/e-commerce calibration packets failing Quality v3.

## Accepted Architecture

The v6 authoring flow is:

`Raw intake -> ProjectBriefPack -> Brief lock -> NarrativePlan -> candidate
retrieval -> GPT-5.5 TemplateSelectionPlan/SlideBlueprint -> native
materializer -> deterministic QA -> independent AI review`.

Models may select registered semantics, slots, components, and normalized grid
relationships. They may not invent facts or emit raw OOXML, HTML, executable
code, arbitrary coordinates, fonts, or colors.

## Implementation Decisions

- ProjectBriefPack v1 is an additive, versioned boundary with three explicit
  states: `Draft`, `NeedsDiscussion`, and `Locked`.
- Only a complete `Locked` pack may enter formal narrative or rendering work.
  Other states return structured discussion questions and create no PPTX.
- The lock digest covers normalized authoritative facts, sources, assets,
  audience, goals, timing, brand constraints, anatomy, decisions,
  prohibitions, and rubric.
- The tracked corpus contains reproducible synthetic metadata and public
  citations only. Commercial originals and credentials remain under the
  ignored `.private/` root.
- The first implementation model is Codex GPT-5.5 medium. Weak-model
  distillation is a separate v6.1 concern and must not weaken v6.0 evidence.

## Existing Patterns To Preserve

- Preserve the existing BriefPlan, DeckPlan, CompositionPlan, RenderPlan,
  portable renderer, and Quality v3 contracts during additive migration.
- Preserve native-editable shapes, text, tables, and charts as the canonical
  output; images may be used only where the asset role requires raster media.
- Preserve deterministic validation, structured findings, immutable benchmark
  facts, bounded repair, and evidence-bundle conventions.
- Preserve the existing Python package and CLI naming conventions and the
  current Node-based skill formatting, typecheck, build, and Vitest gates.

## Allowed Scope

- Phase 36 planning and evidence artifacts.
- The ignored private-root policy and staged secret/binary checker.
- ProjectBriefPack v1 schema, normalization, state transition, digest, corpus,
  CLI, and focused tests.
- Minimal fixes for the three archived deterministic regression failures.
- Skill documentation required to expose the Phase 36 contract.

## Forbidden Scope

- Authenticated Gaojie access or any committed commercial template byte.
- Credentials, cookies, tokens, private keys, or secret-bearing logs.
- TemplatePack v2, Registry v3, final flagship rendering, or release scoring.
- Deletion of legacy plan/render APIs or weakening of Quality v3 assertions.
- COM as a required runtime, HTML-to-slide as the canonical pipeline, or
  unsupported claims added to synthetic or academic scenarios.

## Integration And Compatibility

ProjectBriefPack v1 feeds the future narrative planner without replacing the
legacy public exports in this phase. Corpus manifests are deterministic inputs
for template retrieval and benchmark generation. The private-asset checker
operates at the git-index boundary and will later be reused by acquisition and
release preflight. Consumers that have not adopted v1 continue to use existing
contracts until a separately evidenced contract phase removes them.

## Flagship Order

1. Annual/work report
2. Campus competition defense
3. Academic thesis defense

Each flagship must include cover, directory, section dividers, main evidence,
decision or conclusion, closing, and appendix. The tracked corpus is synthetic
but structurally equivalent to a real client brief; public academic metadata
receives real citations.

## External Preconditions

Authenticated acquisition remains `NEEDS_AUTH` until the user confirms the
previous chat-only session was revoked and supplies a new short-lived cookie
through the ignored private path. No credential value is recorded.
