# Phase 49: Window-PPTX v6.1 — Physical Template Assembly

**Created:** 2026-08-01
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Requirements:** 7
**Original requests:** USR-V61-01

## Goal

Given only a complete 15-slide hospital-finance requirement pack and the installed Skill, let Codex `gpt-5.6-terra` medium select direct-use certified pages, adapt client facts, and emit one native-editable PPTX whose complete OPC graph, physical lineage, package size, portability, and visual quality all pass independent acceptance.

## Background

Every one of the 15 slides must have a distinct certified page ID, be
physically copied from its source `.pptx`, adapted with the client facts, and
assembled into one target deck. Multiple selected pages may share a source
package when complete-work reuse is the best match. No PptxGenJS or native
visual fallback may count as acceptance.

The first v6.1 checkpoint proved that physical slide copying and native text
adaptation are possible, but a frozen audit found six release blockers: wrong
metadata for non-first pages, lost direct-use eligibility, one hard-coded style
cluster, owner-relative OPC traversal errors, a slide-only verifier, and 4.02x
package amplification. Phase 49 is a stabilization and clean-room acceptance
phase, not a completion claim for that checkpoint.

## Requirements

### V61-LIB-01: Correct and eligibility-preserving page intelligence

**Source requests:** USR-V61-01

- **Current:** Multi-page records use slide 1 metadata and the compiled index
  drops direct-use disposition while assigning one style to every page.
- **Target:** Compile the requested slide and preserve source eligibility,
  structural evidence, capacity, palette, and meaningful style features.
- **Acceptance:** GOAL-49-01 and the focused page-library tests pass.

### V61-SEL-01: Deterministic safe selection

**Source requests:** USR-V61-01

- **Current:** Reference-only pages can enter runtime candidates and style
  filtering cannot distinguish designs.
- **Target:** Rank only eligible candidates under the locked weighted score and
  one dominant compatible style family.
- **Acceptance:** GOAL-49-02 and deterministic query tests pass.

### V61-ASM-01: Complete physical OPC import

**Source requests:** USR-V61-01

- **Current:** Nested dependencies are resolved against the wrong owner and
  static parts are copied per target slide.
- **Target:** Import complete owner-relative dependency closure, preserve
  content types, safely share/deduplicate immutable parts, and reject unsafe
  relationships.
- **Acceptance:** GOAL-49-03 passes on synthetic recursive fixtures and the
  private 15-slide replay.

### V61-ADAPT-01: Governed native slot adaptation

**Source requests:** USR-V61-01

- **Current:** Text adaptation exists but is not guarded by complete OPC
  closure and preserved direct-use eligibility.
- **Target:** Adapt declared source shape IDs only after dependency closure,
  enforce capacity and immutable facts, and retain editable objects/styles.
- **Acceptance:** Adaptation, capacity-failure, python-pptx, and LibreOffice
  tests pass.

### V61-QA-01: Recursive integrity and bounded output

**Source requests:** USR-V61-01

- **Current:** The verifier checks slide relationships only and accepts an
  output with eight missing nested targets and 4.02x size amplification.
- **Target:** Verify every internal relationship, lineage, native editability,
  dependency reuse, determinism, and package-size metrics.
- **Acceptance:** GOAL-49-04 passes with zero unresolved targets and output no
  larger than 33,941,179 bytes for the locked replay.

### V61-CLEAN-01: External clean-room generation

**Source requests:** USR-V61-01

- **Current:** Development trials can see local references and historical
  outputs.
- **Target:** Codex receives only the public requirement pack, business assets,
  and installed Skill; private lookup is resolved through configured Skill
  state outside the client folder.
- **Acceptance:** GOAL-49-05 and the clean-folder manifest pass.

### V61-REL-01: Independent release closure

**Source requests:** USR-V61-01

- **Current:** No accepted v6.1 external generation, visual review set,
  completion audit, merge, or installed digest exists.
- **Target:** Close only through engineering, visual, audit, delivery, and
  installation gates.
- **Acceptance:** GOAL-49-06 and every unchecked acceptance criterion pass.

## Boundaries

### In Scope

- Correct page metadata and direct-use-safe deterministic retrieval.
- Cross-package native OPC import, slot adaptation, recursive verification,
  conservative deduplication, and size reporting.
- One 15-slide clean-room work-report generation and its acceptance evidence.

### Out Of Scope

- The approved `pptx-studio` flag-day rename, complete deletion of
  `window-pptx`, private-library pruning, and Agnes Deck→Page→Region indexing;
  the next milestone owns those changes after this baseline is stable.
- Mandatory PowerPoint COM, whole-slide raster output, arbitrary model-written
  geometry/style/code, or redistribution of private commercial assets.

## Constraints

- Private assets and credentials remain ignored and never enter commits or
  reviewer packets.
- COM is optional read-only certification only.
- The clean client folder is never searched for templates.
- Reference-only, quarantined, rejected, unsafe, or capacity-incompatible
  candidates fail closed.
- Any unresolved internal relationship, missing lineage, failed open/render,
  package-size breach, Blocker, Important, `FAIL`, or `NOT_RUN` keeps Phase 49
  open.

## Acceptance criteria

- [ ] **GOAL-49-01:** `compile-page-templates` ingests the 288 certified core
  pages from 266 distinct packages and emits a deterministic
  `page-template-library-v4.json` plus per-package OPC manifests, each with
  source SHA-256, slide count, masters, layouts, themes, and slot graph.
- [ ] **GOAL-49-02:** `query-page-templates` accepts role + style-cluster
  filters and returns ranked candidates with deterministic scoring weights
  (role 0.30, capacity 0.25, semantic 0.20, style 0.15, editability 0.10).
- [ ] **GOAL-49-03:** `assemble-physical-deck` takes an assembly plan (≥15
  slides), opens each source `.pptx`, extracts slide 1 plus its required OPC
  dependencies, rewrites relationship and content-type IDs with stable
  `v61_<source-hash>_<ordinal>` names, and emits a single target `.pptx`
  whose `/ppt/slides/slideN.xml` bytes verify equal to the source bytes for
  the chosen page (modulo text replacement).
- [ ] **GOAL-49-04:** `adapt-slot-text` rewrites the chosen text-bearing
  shapes using the existing per-shape OOXML patcher, runs the existing
  `TemplatePack` text-style rules, and produces a per-slide adaptation
  evidence report.
- [ ] **GOAL-49-05:** `verify-physical-assembly` validates OPC integrity
  (zip-open, `[Content_Types].xml` parse, every slide resolves through
  `slideN.xml.rels` to a registered target), editability (native editable,
  not flattened), and per-slide lineage (slide N ⇒ package_sha256, slide
  ordinal, source SHA-256). Failures block release.
- [ ] **GOAL-49-06:** Build a clean external requirement pack
  `annual-work-report.requirement-pack.v1.json` containing only public data
  (no reference PPTX, no template previews, no private bytes, no historical
  outputs). The pack contains the locked 15-slide role sequence and the
  hospital-finance synthetic facts.
- [ ] **GOAL-49-07:** Run a Codex worker
  (`codex exec --dangerously-bypass-approvals-and-sandbox -c
  'model_provider="OpenAI"' -c 'model_reasoning_effort="medium"' -m
  gpt-5.6-terra --cd <clean-dir>`) against the requirement pack and Skill
  only, and produce a single PPTX. The PPTX must satisfy 15/15 lineage,
  open in `python-pptx`, and pass the verifier.
- [ ] **GOAL-49-08:** Three fresh independent anonymous visual reviews, each
  with no prior context and no shared images, must each return median ≥8/10
  on the same acceptance rubric (composition, narrative, brand harmony,
  editability, native fidelity). Any review returning <8/10 or any Blocker
  /Important fails the milestone.
- [ ] **GOAL-49-09:** A fresh independent OpenCode completion audit returns
  DONE with zero Blocker/Important and an unchanged frozen fingerprint.
- [ ] **GOAL-49-10:** The integration branch is fast-forwarded/pushed to
  `master` and the installed Skill is re-synced with content-digest parity.

## Architectural additions

### New schemas

- `schemas/page-template.v1.schema.json` — single certified page manifest.
- `schemas/template-library-index.v4.schema.json` — full library output of
  `compile-page-templates`.
- `schemas/assembly-plan.v1.schema.json` — Codex-authored plan linking each
  target slide to a chosen `page_id`.
- `schemas/physical-assembly-report.v1.schema.json` — verifier output.

### New modules

- `scripts/window_pptx/page_template_library.py` — `compile_page_templates`,
  `query_page_templates`, deterministic scoring.
- `scripts/window_pptx/physical_assembly.py` — `assemble_physical_deck`,
  `adapt_slot_text`, `verify_physical_assembly`.

### New CLI

- `scripts/manage_window_pptx_library.py compile-pages`
- `scripts/manage_window_pptx_library.py query-pages`
- `scripts/window_pptx_automation.py --render-assembly-plan` accepts an
  assembly plan and produces the target PPTX.

### Private-root precedence

1. `--private-root`
2. `WINDOW_PPTX_PRIVATE_ROOT` env var
3. `~/.config/window-pptx/library.json`

The clean client folder MUST NOT be searched for private templates.

### Cross-package OPC importer (single algorithm)

1. Preallocate every target slide path
   (`/ppt/slides/slideNNN.xml`,
    `/ppt/slides/_rels/slideNNN.xml.rels`).
2. For each chosen source page:
   - open the source `.pptx` (zipfile.ZipFile read-only),
   - recursively traverse relationships starting from the chosen slide
     entry,
   - copy required parts (layouts, slideLayouts, masters, slideMasters,
     themes, media, charts, chart styles/colors, embedded workbooks,
     diagrams, notes, notes masters, comments),
   - deduplicate byte-identical parts,
   - otherwise assign `v61_<source-hash>_<ordinal>` to keep the OPC graph
     acyclic,
   - rewrite target slide and relationship IDs,
   - register the slide, slideLayout, slideMaster, theme, and notes
     content types,
   - preserve any safe HTTPS link targets,
   - reject file/script/OLE/macro/unresolved targets before commit.
3. Adapt slot text on the slide after dependency closure, then commit.

### Style cluster

The dominant style cluster is `ivory-green-gold-editorial` (carried from
the locked reference `template-pack-v2.json`). Compatible clusters may be
used as fallback ONLY if they are explicitly registered and the dominant
cluster has no certified page for the requested role. Cross-cluster mixes
on a single deck are not allowed.

## Gate

Any of the following keeps the milestone open: a single slide without
physical lineage evidence, an unparsable PPTX, a slide that does not open
through `python-pptx`, a visual review below 8/10, any Blocker/Important,
fingerprint drift, or push failure.

## Test Seams And Critical Cases

| Behavior | Observable seam | Critical failure | Evidence |
|---|---|---|---|
| V61-LIB-01 / V61-SEL-01 | compiler/query focused tests | slide 2 reads slide 1; reference-only result; one style cluster | `49-VALIDATION.md` |
| V61-ASM-01 / V61-ADAPT-01 | synthetic OPC fixtures and 15-slide replay | missing chart dependency; unsafe target; broken native object | `49-VALIDATION.md` |
| V61-QA-01 | recursive verifier and package metrics | unresolved target, duplicate static graph, >1.30x source | `49-VALIDATION.md` |
| V61-CLEAN-01 / V61-REL-01 | external Codex run and fresh reviews | reference/private leakage, fallback slide, visual or audit finding | `49-UAT.md`, `49-AUDIT.md` |

## Blocking Questions

- None.

The user approved the stabilization-first order, `gpt-5.6-terra` medium,
complete physical reuse, clean-room boundary, and later flag-day
rename/removal.

## Ambiguity Report

- **Goal clarity:** 0.97
- **Boundary clarity:** 0.95
- **Constraint clarity:** 0.96
- **Acceptance clarity:** 0.97
- **Ambiguity:** 0.04

## Decision Log

| Round | Perspective | Decision |
|---:|---|---|
| 1 | Product | Prove one realistic 15-slide work-report tracer before broad scenario expansion. |
| 2 | Model | Use Codex `gpt-5.6-terra` medium and constrain it to narrative, candidate, and binding choices. |
| 3 | Reuse | Every slide needs physical certified lineage; whole-deck or page-level reuse is selected by fit. |
| 4 | Engineering | Resolve full OPC closure without mandatory COM; reject unsafe or unresolved targets. |
| 5 | Migration | Stabilize and merge v6.1 first; then create v7 `pptx-studio` and delete `window-pptx` completely. |

## Stabilization blockers discovered 2026-08-08

This phase remains **active** and must not be described as released or
complete. A post-implementation audit found the following release blockers:

1. The compiler reads `ppt/slides/slide1.xml` for every selected page. The 23
   certified records whose `slide_number` is greater than 1 therefore have
   incorrect structure, slot, capacity, and palette metadata.
2. The v4 index drops the source `pool`, `decision`, and `direct_use`
   disposition. It can consequently return any of the 159 reference-only
   pages as if it were eligible for physical reuse; only 129 pages are in a
   direct-use-capable pool.
3. All 288 pages are currently assigned the same
   `ivory-green-gold-editorial` style cluster. Style filtering and dominant
   style selection are therefore not meaningful.
4. OPC dependency traversal resolves nested relationship targets relative to
   the originating slide instead of the current relationship owner. The
   audited output contains eight unresolved chart-style/chart-color targets.
5. The verifier checks only slide relationships, so it can report success
   while nested internal relationships remain unresolved.
6. The importer copies shared masters, layouts, themes, and media once per
   target slide. The 25.0 MiB reference deck expanded to roughly 100.2 MiB
   (4.02x), including repeated copies of identical images.

Release is blocked until the compiler preserves direct-use eligibility and
reads the requested slide; the importer performs owner-relative recursive OPC
closure with safe dependency deduplication; the verifier checks every internal
relationship; and the 15-slide reference replay is no larger than 1.30x the
source while retaining native editability and complete lineage.
