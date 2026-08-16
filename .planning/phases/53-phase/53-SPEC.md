# Phase 53: Clean-Room Work-Report Acceptance and Release — Specification

**Created:** 2026-08-12
**Milestone:** v7 PPTX Studio Curated Composition
**Roadmap phase:** 53
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Requirements:** 2
**Requirement IDs:** V7-ACCEPT-01, V7-RELEASE-01

## Goal

Prove the migrated Skill with a fresh capable-model agent in a clean

## Requirements

### V7-ACCEPT-01: Clean client-folder, real-agent work report

- **Source requests:** USR-V7-01
- **Current:** fixture-only physical assembly and no fresh capable-agent
  evidence from a clean client requirement folder.
- **Target:** one `gpt-5.6-terra` medium Codex run creates the required
  hospital-finance report using only its client pack plus installed Skill;
  count is derived from the approved narrative rather than prescribed.
- **Acceptance:** clean inventory, agent transcript, narrative/page-rationale
  ledger, editable PPTX, and complete per-slide physical lineage all match the
  locked client brief. The historical 15-page source is replay-only regression
  evidence.
- A clean folder contains only client brief, facts, acceptance criteria and
  client-provided assets; no reference PPTX, private templates, previews or
  historic production outputs.
- Codex runs with `gpt-5.6-terra` at medium reasoning and the installed
  `pptx-studio` Skill.
- The agent produces the narrative-derived editable page set through catalog
  retrieval, governed composition/adaptation and physical assembly only.
- Evidence must show directory/section/body/closing anatomy and a complete
  catalog-page/package/slide/slot lineage for every page.
- When a complete certified work is the semantic and visual match, the agent
  must be able to inspect its ordered, value-free page inventory after cover
  retrieval and select the complete family without misclassifying each page
  through a generic component-category role. Its actual native text surface
  remains explicit and governs binding/visual release.
- A page with native chart, table, or embedded-workbook values is eligible for
  a client deck only when the locked client pack supplies the corresponding
  complete structured dataset. A text-only outline must select a compatible
  zero-data-surface page instead; clearing a chart or retaining sample values
  is not an acceptable delivery shortcut.

### V7-RELEASE-01: Independent release proof

- **Source requests:** USR-V7-01
- **Current:** Phase 52 has local fixture QA and temporary source/install
  parity only; no release output has independent visual/audit evidence.
- **Target:** bind every release check to the exact delivered file fingerprint
  and obtain three context-isolated visual reviews plus a frozen audit.
- **Acceptance:** every report is PASS; review median and audit have no
  unresolved Blocker/Important finding.
- Portable physical assembly, rules QA and plan-aware QA must be PASS on the
  exact delivered output fingerprint.
- Three fresh, anonymous visual reviews must be created by contexts that did
  not author or select the deck. Their evaluation inputs contain rendered pages
  and a rubric, not source templates or the author session.
- A frozen-worktree independent audit finds no unresolved Blocker or Important
  issue. The source/install digest parity is rechecked at release point.

## Constraints

- Private library is external to the clean client folder and resolves only by
  hash under the local private root. Its content never enters output or prompt.
- No PptxGenJS/native generated visual fallback counts for this acceptance.
- No manual score override, self-review, COM dependency or rasterized slide.
- If model/provider access fails, record NOT_RUN and do not claim acceptance.

## Background

Phase 52 moved the public identity to `pptx-studio` and proved fixture-level
physical assembly. This phase is deliberately a real client-like test: its
author sees no reference deck/template pages, while runtime retrieval resolves
the already governed local private library outside the client folder.

## Boundaries

### In Scope

- One complete hospital-finance work report and its release evidence.
- Replanning/reassembly required to make the narrative-derived output pass.

### Out Of Scope

- Additional business scenarios, public distribution of private assets,
  changes to commercial source material or release with a human-score override.

## Acceptance Criteria

- [ ] AC-53-01: clean-room inventory proves no private/reference contamination.
- [ ] AC-53-02: Codex real run produces one 15-page editable physical assembly.
- [ ] AC-53-03: exact-output QA and lineage are PASS.
- [ ] AC-53-04: three independent visual reviewers and frozen audit are PASS.

## Decision Log

| Round | Question | Decision |
|---:|---|---|
| 1 | Can a model bypass catalog assembly if output looks attractive? | No; every page must have physical catalog lineage. |
| 2 | Can one multimodal reviewer approve release? | No; three fresh anonymous contexts are required. |
| 3 | Does moving private assets into the new ignored root contaminate the client pack? | No; the clean folder has no private subtree and inventory proves it. |
| 4 | May a chart-heavy reference page be used when the brief only supplies headline metrics? | No. Query/preflight expose a value-free structured-data requirement and selection must choose a compatible no-data-surface page until a complete dataset is locked. |
| 5 | Does a full-bleed certified background image make a physical template page a rasterized slide? | No, provided the imported page retains a material native shape system or editable text surface. QA still rejects a screenshot-like page only when both non-picture native coverage and editable-text coverage are sparse. |
| 6 | May a clean-room agent inspect the selected anchor family before it composes a 15-page page assembly? | Yes. `inspect-deck` is an explicit bounded family-anatomy step, followed by candidate-ID revalidation. It preserves the style lock and eliminates the false conflict between coherent family reuse and per-page proof. |
| 7 | Must an inspected complete-work page pass a generic role taxonomy before flexible recomposition? | No. `family_assembly` is a restricted complete-work adaptation route: every page remains unique, editable, data-safe, capacity-checked and from the exact anchor deck, but generic role labels do not override the certified work's own editorial anatomy. |

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.96
- **Boundary clarity:** 0.95
- **Constraint clarity:** 0.97
- **Acceptance clarity:** 0.95
- **Ambiguity:** 0.04
