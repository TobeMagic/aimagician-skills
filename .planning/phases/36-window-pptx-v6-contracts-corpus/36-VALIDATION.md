# Phase 36 Validation

**Status:** PASS for Phase 36 engineering scope; v6.0 milestone remains open
**Validated:** 2026-07-29
**Branch:** `feat/window-pptx-v6`
**Implementation commits:** `072e8a7`, `8c579cf`, `9b3dbc2`

Phase 36 establishes the intake, corpus, safety, and executable documentation
boundary. It does not claim that TemplatePack v2, private acquisition,
reference-grade flagship PPTX files, or three-context visual acceptance already
exist.

## Requirement Evidence

| Requirement | Result | Fresh evidence |
|---|---|---|
| V6-BRIEF-01 | PASS | `project-brief-pack.v1.schema.json`, `project_brief.py`, and the management CLI implement Draft → NeedsDiscussion → Locked, structured questions, complete authority/rights checks, immutable facts, and a stable lock digest. Focused contract tests pass. |
| V6-CORPUS-01 | PASS | The deterministic corpus contains exactly 15 valid locked packs: three complete flagships and twelve realistic skeletons. Tests enforce scenario coverage, at least eight quantitative facts, at least three material roles, required anatomy, decisions, slide budgets, prohibitions, sources, and accepted flagship facts. |
| V6-DOC-01 | PASS | `SKILL.md`, the v6 workflow reference, and behavior evals make the locked brief gate, GPT-5.5-medium quality-first route, private boundary, complete-deck anatomy, bounded repair, and three-context AI-only acceptance executable. Contract tests and Skillbird formatting pass; the stale v5 default and old human blind-review release wording are absent. |

## Safety Boundary

- `.private/` is ignored and is the only permitted local home for commercial
  originals, acquisition state, and credentials.
- The staged-index guard rejects private paths, credential signatures, private
  keys, and unapproved binaries without echoing matched values.
- The guard fails closed when staged-index inspection itself fails.
- No authenticated commercial acquisition was attempted. It remains
  `NEEDS_AUTH` until the old exposed session is revoked and a new short-lived
  credential is supplied through the ignored private path.

## Fresh Verification

| Check | Result |
|---|---|
| Complete Window-PPTX code regression before the final Skill-contract test file, three deterministic shards | 813/813 PASS: 491 + 146 + 134, including the 42-case weak-model benchmark |
| Current Python collection after adding the three documentation-contract tests | 816 collected = 813 previously executed code tests + 3 focused Skill-contract tests |
| v6 contract/safety/brief/corpus focused rerun | 22/22 PASS: 6 private guard + 7 brief + 6 corpus + 3 Skill contract |
| Archived regression owning modules | 80/80 PASS |
| Complete portable calibration module | 11/11 PASS |
| Root Vitest | 22 files, 108/108 PASS |
| TypeScript typecheck | PASS |
| Production build | PASS |
| `node dist/cli/index.js format-skills --check` | 23 checked, no changes, no issues |
| `evals/evals.json` JSON parsing | PASS |
| Phase 36 workflow spec/plan/execute gates | PASS / PASS / PASS |
| `git diff --check` | PASS |

The three archived baseline defects are closed without weakening Quality v3:
generated raster bookends use governed poster layouts, single-action CTA
content no longer creates invented decision cards, and prose-only direction
labels remain editable and use `BASELINE`.

## Deliberate Non-Claims

- V6-ASSET-01 and V6-LIB-01 are Phase 37 work.
- V6-DESIGN-01 and V6-DECK-01 are Phase 38 work.
- No v6 flagship PPTX has been generated or visually accepted.
- The final three visual-capable blind-review packets are `NOT_RUN`; they are a
  Phase 41 release gate and cannot be replaced by this code/document audit.
- COM remains optional diagnostics. Phase 36 requires no PowerPoint COM run.

## Phase Completion Rule

Phase 36 may close only after fresh independent specification, implementation
quality, verification-truth, and Agnes completion reviews return PASS with no
Blocker or Important finding. Any unresolved finding changes this document
back to FAIL or PENDING.
