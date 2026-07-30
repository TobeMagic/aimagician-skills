TASK_ID: window-pptx-phase46-architecture-research-v2-20260730
ROLE: independent implementation researcher
TASK_TYPE: research
MODALITY: text
OBJECTIVE: Recommend the smallest architecture that produces a visible
reference-grade step-change for three editable PPTX anchors.
DELIVERABLE: Findings first, named implementation seams, risks, architecture,
tests, and first execution slice.

REQUIRED_SKILLS:
- cli-agent-delegator
- aimagician-superpower
- window-pptx

PERMISSION_MODE: evidence-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: NONE. Load the required skills, then call no repository,
shell, read, search, web, write, or child-agent tool. Reason only from this
packet.

FROZEN_PACKET:

- Exact requirement V6R-ANCHOR-01: work-report, campus-competition, and
  academic-defense anchors use actual certified candidates and pass anatomy,
  editability, artifact, and reference-grade pixel review.
- The accepted reference work-summary is 15 slides. Its art direction uses
  expressive oversized Chinese typography, diagonal gold bands, lighthouse
  imagery, photographic cover/closing, strong directory/chapter pages, native
  charts, controlled high-density data, illustration, recurring motif, and
  visible sparse/dense rhythm.
- Existing three 32-slide flagships are structurally valid and editable but
  rejected visually. Their generator is one monolithic Node/PptxGenJS file,
  `build_window_pptx_v6_flagships.mjs`, with hardcoded themes and helpers such
  as `newDeck`, `addTitle`, `addMotif`, `cover`, `agenda`, `section`,
  `metricCards`, chart, table, and diagram helpers.
- Existing annual report repeats ivory/green cards and rounded rectangles.
  Existing campus repeats dark navy/teal cards. Existing academic repeats
  light editorial cards/tables. All three have weak imagery, insufficient
  scale contrast, and too little page-form variation.
- Phase 44 has a certified private core with 288 pages: 129 direct-use and 159
  reference-only. Direct-use pages include four covers, eleven directories,
  eight section pages, ten closings, quote pages, people, awards, timelines,
  one map, framework diagrams, KPI-chart components, background motifs, and
  text-navigation components. Reference-only pages may guide art direction but
  cannot materialize.
- Phase 45 production emits a deterministic TemplateSelectionPlan and
  SlideBlueprint sidecars. Registered native candidates bind exact governed
  variants. Physical candidates use a hash-bound whole-pack TemplatePack
  adapter. A candidate materialization report becomes PASS only after observed
  output matches the expected candidate. Arbitrary multi-source OOXML
  relationship merging does not yet exist.
- PPTX must remain natively editable. Whole-slide rasterization is forbidden.
  COM is optional/unreliable. Portable LibreOffice/Poppler rendering is
  available. Local private assets are authorized for this user's local output.
- `template_intelligence.py` owns certified candidate retrieval and
  blueprints. `selection_materialization.py` owns exact native/physical
  evidence. `template_pack.py` owns physical pack adaptation. The existing
  flagship generator currently bypasses that production bridge.
- The critical choice is among:
  A. keep extending the monolithic generator;
  B. build a new anchor-specific blueprint/composition engine that translates
     selected certified pages into editable design primitives;
  C. implement controlled editable-shape import from physical PPTX pages;
  D. combine B for the first slice with a bounded C later.

QUESTIONS:
1. Choose A/B/C/D and justify it against visual impact, editability, evidence,
   and implementation risk.
2. Define exact new modules/files and their responsibilities.
3. Define a page blueprint schema that fixes hero imagery, typography,
   composition, motif, density, and rhythm without asking a weak model for
   coordinates.
4. Define how certified physical/reference pages visibly influence output
   without false materialization claims.
5. Define the fastest work-summary slice that proves a genuine visual
   step-change, and the gates before campus/academic expansion.
6. Define tests/evidence and top failure modes.

Return concise but implementation-specific guidance. Do not claim you inspected
files or pixels beyond this packet.
