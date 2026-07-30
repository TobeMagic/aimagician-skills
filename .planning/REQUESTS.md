# Request Ledger: AImagician Skills

**Updated:** 2026-07-29

## USR-V6-01: Reset the rejected visual-quality floor

**Status:** Accepted
**Source:** User request and visual rejection of current trials

### Original Request

The current generated decks and iteration requirements are shallow and do not
reach the accepted reference deck or a senior presentation designer's level.
Do not stop at recommendations; implement, test, compare, and iterate.

### Accepted Decisions

- Preserve v5.1 as an explicit `NO_GO` archive.
- v6.0 optimizes for reference-grade customer delivery before weak-model
  generalization.

### Derived Requirements

- V6-DESIGN-01
- V6-DECK-01
- V6-QA-01
- V6-EVID-01
- V6-REL-01

### Exclusions

- Treating deterministic engineering scores as visual acceptance.

## USR-V6-02: Use a stronger default authoring model

**Status:** Accepted
**Source:** User decision

### Original Request

Use Codex GPT-5.5 medium as the quality-first authoring model so the Skill can
first prove reference-level output.

### Accepted Decisions

- GPT-5.5 medium owns v6.0 narrative and visual selection.
- Weak-model distillation begins only after v6.0 GO.

### Derived Requirements

- V6-DESIGN-01
- V6-UAT-01

### Exclusions

- v6.0 release claims based on DeepSeek-only authoring.

## USR-V6-03: Build realistic scenario requirements

**Status:** Accepted
**Source:** User request and locked planning discussion

### Original Request

Create requirements that look like complete real client requests, including
detailed data, materials, copy, audience, timing, decisions, and acceptance
criteria for campus competition, work reports, academic defenses, and other
common scenarios.

### Accepted Decisions

- Three complete flagships plus twelve locked skeletons.
- Synthetic standardized facts are allowed when explicitly labeled and
  source-bound.
- Formal generation requires discussion lock.

### Derived Requirements

- V6-BRIEF-01
- V6-CORPUS-01

### Exclusions

- Shallow one-fact-per-slide benchmark prompts.

## USR-V6-04: Require complete deck anatomy

**Status:** Accepted
**Source:** User request

### Original Request

Generated decks need cover, directory, chapter pages, title hierarchy,
conclusion, ending, appendix, and scenario-appropriate sections instead of a
sequence of generic text pages.

### Accepted Decisions

- Long decks require directory and section dividers.
- The three flagships use fixed main/appendix slide budgets.

### Derived Requirements

- V6-BRIEF-01
- V6-CORPUS-01
- V6-DECK-01

### Exclusions

- Adding empty structural pages without narrative function.

## USR-V6-05: Build a governed Gaojie-style template library

**Status:** Accepted
**Source:** User request referencing the Gaojie category taxonomy

### Original Request

Discover and manage the full entitled catalog, including cover, directory,
section, title, ending, one-to-six and multi-content, people, awards, maps,
timelines, process, business model, mockup, quote, partners, image-text,
charts, tables, images, practical materials, palettes, topics, data bases,
text components, decorations, excellent works, and launch templates.

### Accepted Decisions

- Originals remain under the Skill's ignored private directory.
- Full discovery is resumable; certification is staged.
- Complete works are visual spines and direct TemplatePack reuse is allowed
  only with rights evidence.

### Derived Requirements

- V6-ASSET-01
- V6-LIB-01
- V6-DECK-01

### Exclusions

- Access-control bypass, unlicensed redistribution, or committing private
  originals.

## USR-V6-06: Reach the accepted reference's art direction

**Status:** Accepted
**Source:** User-supplied `工作总结.pptx` and approved plan

### Original Request

Match the reference's hierarchy, page rhythm, motif continuity, visual
richness, data presentation, and complete-work polish without merely copying
its text or placing content into generic cards.

### Accepted Decisions

- Extract reusable ArtDirectionProfile rules.
- Recombine design logic; do not copy protected identity or distinctive media
  without authorization.

### Derived Requirements

- V6-DESIGN-01
- V6-DECK-01
- V6-UAT-01

### Exclusions

- Page-by-page unauthorized copying.

## USR-V6-07: Simplify repair and improve components

**Status:** Accepted
**Source:** User request

### Original Request

Remove redundant component repair and shallow block decoration. Use better
template selection, motifs, imagery, diagrams, and bounded correction.

### Accepted Decisions

- One deterministic repair, one same-family reselection, and one visual replan
  are the complete loop.

### Derived Requirements

- V6-QA-01
- V6-DECK-01

### Exclusions

- Unlimited heuristic repair passes.

## USR-V6-08: Keep PPTX portable and editable without mandatory COM

**Status:** Accepted
**Source:** User discussion about COM, HTML conversion, and alternatives

### Original Request

Do not make the broken PowerPoint COM environment a production dependency.
Preserve editable PowerPoint capabilities through portable OOXML/PptxGenJS and
independent rendering.

### Accepted Decisions

- Native editable PPTX is canonical.
- HTML is proof-only.
- COM is optional read-only diagnostics/certification.

### Derived Requirements

- V6-PORT-01
- V6-PORT-02

### Exclusions

- Whole-slide raster delivery or HTML as canonical PPTX source.

## USR-V6-09: Use fully independent AI-only blind review

**Status:** Accepted
**Source:** Latest explicit user decision

### Original Request

Replace human scoring completely with blind AI reviewers that have fully
independent contexts.

### Accepted Decisions

- Three fresh anonymous visual-capable review contexts.
- No reviewer sees generator traces or other scores.
- Unavailable image input yields `NOT_RUN`; no two-reviewer fallback.

### Derived Requirements

- V6-UAT-01
- V6-AUDIT-01
- V6-REL-01

### Exclusions

- Human scoring, manual score override, or self-review by the generator
  context.

## USR-V6-10: Implement, verify, iterate to GO, then commit and push

**Status:** Accepted
**Source:** Repeated user execution instructions

### Original Request

Implement the plan, generate multiple complete PPTX files, compare against the
reference and previous trials, keep iterating until milestone acceptance, then
organize commits and push.

### Accepted Decisions

- Use `.planning` phases 36–41 and preserve durable evidence.
- Push v6 only after release gates and fresh Agnes completion audit pass.

### Derived Requirements

- V6-EVID-01
- V6-DOC-01
- V6-AUDIT-01
- V6-REL-01

### Exclusions

- Declaring completion from code changes or test summaries alone.

## USR-V6-11: Reopen the rejected v6 result and use the real private catalog

**Status:** Accepted
**Source:** Latest user visual rejection and acquisition authorization

### Original Request

The current trial quality still does not show the supplied reference or
excellent commercial works. Use Playwright to download the complete entitled
catalog for local use, ignore private assets in Git, and implement the actual
result rather than optimizing portability first.

### Accepted Decisions

- Invalidate the previous v6 GO and reopen the milestone.
- Acquire all requested categories through the normal authenticated UI.
- Store credentials, originals, state, and mining artifacts only under the
  ignored Skill-local `.private/` tree.
- Certify a 300–500-page core first while full acquisition remains resumable.
- Actual template selection must be materialized, not written only as manifest
  metadata.
- Three realistic anchors must reach the reference art-direction level before
  fifteen-scenario and ordinary-model expansion.
- Any independent AI visual `Blocker` or `Important` finding blocks promotion.

### Derived Requirements

- V6R-GROUND-01
- V6R-ACQ-01
- V6R-MINE-01
- V6R-MAT-01
- V6R-ANCHOR-01
- V6R-WEAK-01
- V6R-UAT-01
- V6R-REL-01

### Exclusions

- Access-control bypass, credential leakage, redistribution, whole-slide
  raster output, or claiming code variants as downloaded templates.
