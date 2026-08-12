# Phase 53: Clean-Room Work-Report Acceptance and Release — Research

**Updated:** 2026-08-12

## Objective

Establish whether the installed `pptx-studio` Skill lets a fresh capable Codex
agent turn a client-only requirement pack into a 15-page, native-editable,
physically lineage-bound work report.

## Local Evidence

| Source | Fact | Relevance |
|---|---|---|
| `53-SPEC.md` | Acceptance requires a fresh `gpt-5.6-terra` medium Codex run, 15 slides, complete physical lineage and independent release proof. | Defines the non-negotiable release gates. |
| `skills/owned/pptx-studio/SKILL.md` | Agent authority is limited to brief discussion, narrative, retrieval IDs and fact/asset IDs; runtime owns visual implementation. | Prevents a passing deck from being a free-form fallback. |
| `skills/owned/pptx-studio/scripts/manage_pptx_studio_library.py` | The `assemble` path binds catalog/composition/adaptation plans to physical editable PPTX import. | Production assembly entry point. |
| `/tmp/pptx-studio-phase53-client.KV9xoK` | The client pack has exactly `CLIENT_BRIEF.md`, `FACTS.md` and `ACCEPTANCE.md`; it has no template or reference files. | Clean-room test input. |
| `/tmp/pptx-studio-install-phase53.json` | Skillbird installed `pptx-studio` into Codex with source digest `sha256:9f8ac6f0294ae775b3e4b22d440e0f82b55c88977b5155414e7cdbe682159ff9`. | The model can load the intended public Skill. |
| `/tmp/pptx-studio-doctor-phase53.json` | Codex managed Skill installation is healthy; private library does not inflate the installed directory. | Installation precondition. |
| Failed clean-room transcripts | Explicit `model_provider="OpenAI"` is unavailable in this environment, while the selected `gpt-5.6-terra` model runs when that invalid override is omitted. A second/third run also proved catalog text capacity can exceed an actual source-slot capacity. | The harness must omit that provider override and must preflight selected native slots before adaptation. |
| `physical_adapter.preflight_native_slots` | Selected catalog pages are resolved by hash and their actual native slot capacities are emitted without source text or private paths. | Removes trial-and-error binding decisions from the agent. |

## External Evidence

| Source | Fact | Relevance |
|---|---|---|
| Codex runtime | Must be exercised at the user-selected `gpt-5.6-terra` medium configuration. | This is the only valid proof of actual agent behavior. |
| Rendered delivery pages | Three fresh reviewer contexts can evaluate visual quality without author-session or source-template access. | Required independent visual release evidence. |

## Options

| Option | Benefits | Costs and risks | Verification |
|---|---|---|---|
| Treat fixture tests as release evidence | Fast. | Does not prove a fresh model can retrieve, bind and compose a real brief. | Rejected by V7-ACCEPT-01. |
| Give Codex the reference/template files in the client folder | Easier imitation. | Violates clean-room and masks retrieval behavior. | Rejected by V7-ACCEPT-01. |
| Run the locked clean-room production prompt with external hash-bound private root | Tests the intended user workflow while private data stays outside the client folder. | Requires model quota and independent follow-up reviews. | Chosen. |

## Recommendation

Freeze source/install parity, then execute one fresh Codex production run. The
agent must perform native-capacity preflight after composition and before it
records client facts/bindings. Accept
only the exact output fingerprint after physical lineage, opening/editability,
rule QA, independent render reviews and a frozen audit all pass.

## Assumptions To Confirm

- Codex access is currently authenticated; the actual run will verify model availability.
- No client-owned bitmap assets are needed for this first work report; certified
  template visuals remain physical slide dependencies and are not placed in the
  client pack.
