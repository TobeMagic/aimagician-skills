# Phase 49: Window-PPTX v6.1 — Physical Template Assembly

**Created:** 2026-08-01
**Status:** active
**Risk:** high
**Requirements:** V61-LIB-01, V61-SEL-01, V61-ASM-01, V61-ADAPT-01, V61-QA-01, V61-CLEAN-01, V61-REL-01

## Goal

Implement the v6.1 physical template assembly pipeline so that a Codex worker,
given only a complete client requirement document plus installed `window-pptx`
Skill, produces a complete editable PPTX where every slide physically reuses a
distinct certified template page from the Gaojie private core.

The locked acceptance scenario is the 15-slide hospital finance annual work
report. Every one of the 15 slides must come from a different certified Gaojie
package (page_id), be physically copied from its source `.pptx`, adapted with
the client text, and assembled into a single target deck. No PptxGenJS or
native visual fallback may count as acceptance.

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
