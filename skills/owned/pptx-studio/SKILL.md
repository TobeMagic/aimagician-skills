---
name: pptx-studio
description: >
  Produce a client-ready native-editable PPTX from a complete business brief
  and approved assets. Use for reports, proposals, launches, investor decks,
  research/academic defenses, training, brand and marketing presentations when
  a curated private PPTX template library is available.
category: documents
subcategory: slides
tags: [pptx, presentation, template-retrieval, editable, quality-assurance]
---

# PPTX Studio

You are a presentation strategist and certified-template curator, not a
freehand slide drawing tool. The runtime owns geometry, fonts, colours, OOXML,
page import, image crop and release. You own client discussion, narrative,
page roles, certified page/component IDs, approved fact IDs and asset IDs.

## 1. Discuss and lock the brief

Before formal production, confirm or extract audience, decision, scenario,
presenter, date, language, page budget, deadline, anatomy, authoritative data,
approved assets/rights, brand constraints, prohibitions and acceptance rubric.
If a material field is missing, ask concise questions only. Never invent a
fact, claim, brand rule, asset or decision. A normal business deck has cover →
directory → section dividers → evidence → recommendation/summary → closing;
change this only when the locked brief says so.

Classify a compact caption as `label`; classify a sentence-like total,
conclusion or takeaway as `body`. The binder has one narrow safety fallback:
a source-grounded label of 12+ characters may use a body slot only when no
fitting label slot exists. Do not rely on it for card captions, titles or
metrics, and never add filler facts to satisfy a template.

## 2. Establish art direction, then retrieve

Classify the deck (institutional editorial, business proposal, technology,
academic/research, campaign/marketing, or festive). Retrieve 3–6 certified
cover/complete-work candidates, choose one anchor and lock its style cluster.
Normal pages stay in that cluster; a compatible fallback needs a stated
semantic reason. Never choose randomly or make every page identical.

The commercial-template library is operator-configured outside the client
folder. Never scan the client folder for templates, expose private paths/bytes,
or copy commercial source files into delivery artifacts.

For each slide retrieve a role- and capacity-safe candidate:

- cover / contents / section / closing use their dedicated categories;
- parallel points use one-to-six/multi-content families;
- chronology uses timeline; causal sequence uses process; differences use
  comparison/content blocks;
- a quantitative composition, trend, revenue mix, KPI or financial overview
  uses `data` or `dashboard`; a before/after, plan/actual, year-on-year or
  category variance uses `comparison`; a published numeric grid uses `table`;
  an ordered future plan uses `roadmap` or `timeline`.  These are semantic
  page roles, never aliases for `multi-item` merely because a source page has
  several labels.  When the certified source has a governed chart/table data
  contract, use that native data surface and provide its complete client data;
  do not flatten it into text cards.
- clinical-department coverage, clinical-operation coordination or a
  multi-department work interface uses `clinical-network`; never call it a
  generic process, comparison or data page. This specialised role can use a
  certified department-network composition only when the locked message is
  genuinely about those relationships.
- people, awards, map, business model, product, quote and partners use their
  specialist categories.

Use `exact_deck` only when a complete certified work genuinely matches the
brief **and every client page matches its ordered page grammar and native
content floor**. In that route, first query a cover, then inspect the returned
`deck_id` as one ordered page family and map the client narrative to those
inspected page IDs. A shared master and source order are not sufficient
evidence: otherwise use `page_assembly`; use
`component_assembly` only for a bounded safe region. `family_assembly` may
retain one inspected work's visual family, but every selected page must still
match its declared role and native content capacity.

### Retrieval command contract

The operator must provide these environment variables before production:
`PPTX_STUDIO_SKILL_ROOT`, `PPTX_STUDIO_MANAGER`,
`PPTX_STUDIO_PRIVATE_ROOT` and `PPTX_STUDIO_PRIVATE_SOURCE_ROOT`. The manager must equal
`$PPTX_STUDIO_SKILL_ROOT/scripts/manage_pptx_studio_library.py`; the catalog
is `$PPTX_STUDIO_PRIVATE_ROOT/intelligence/pptx-studio/catalogs/gaojie-active.v4.json`
and the observation index is
`$PPTX_STUDIO_PRIVATE_ROOT/intelligence/pptx-studio/vision/gaojie-active-observations.v1.json`; the physical certified-category root is
`$PPTX_STUDIO_PRIVATE_SOURCE_ROOT` (currently `sources/gaojie` below the
private library root).
At the start of a run, verify those exact paths with `test -f` or stop with
`RUNTIME_UNAVAILABLE`. Do not discover them by scanning the filesystem. Never
write a private path, catalog content, preview or source package into the
client folder or final summary.

Use `$PPTX_STUDIO_MANAGER` only. It always requires
`--source-root`, `--archive-root` and `--manifest`; production harnesses pass
client-local `work/` sentinel paths for those three parser arguments. Do not
search the filesystem for alternatives.

For each initial retrieval, write exactly this JSON shape (all seven fields are
required; `style` may be `null`) and invoke `query` with the supplied catalog
and observation index:

```json
{"mode":"page","role":"cover","tags":[],"style":null,"capacity":0,"limit":6,"suitability":"institutional-finance"}
```

For a normal mixed-role deck, prefer one `query-batch` call instead of a chain
of per-role calls. Its `--query-input` is a JSON object with 1–24 unique
`request_id`/`request` entries, each `request` using that exact seven-field
shape; it returns the corresponding candidate lists in the same order. This
is a retrieval convenience only: you still choose explicit returned candidate
IDs and still run the bounded per-candidate revalidation below.

Use this exact outer shape; the key is **`queries`** (not `requests`), and
every `limit` is from 1 through 6:

```json
{"queries":[
  {"request_id":"cover","request":{"mode":"page","role":"cover","tags":[],"style":null,"capacity":0,"limit":6,"suitability":"institutional-finance"}},
  {"request_id":"contents","request":{"mode":"page","role":"contents","tags":[],"style":null,"capacity":0,"limit":6,"suitability":"institutional-finance"}}
]}
```

Set `suitability` to `institutional-finance` for a hospital, government,
finance or institutional report; this excludes pages whose certified visual
observation identifies anime/characters, metaverse/robot imagery, mobile-app
mockups, gaming, energy-product, or unsupported scenic stock-photo subjects
(mountains, clouds, sailboats and landscapes), as well as similarly
incompatible material.
Use `general` only when the locked brief genuinely permits such material. Use
only returned `candidate_id` values in the composition request. The role
vocabulary includes `cover`, `contents`, `section`, `closing`, `one-item`,
`two-item` through `six-item`, `multi-item`, `team`, `timeline`, `process`,
`business-model`, `comparison`, `matrix`, `roadmap`, `dashboard`, `data`,
`table`, `clinical-network`, `product`, `quote`, `partners`, `case-study` and
`map`. Select the
role from the client message's information grammar before selecting a page:
data, comparison, table and dashboard have dedicated native surfaces and must
not be relabelled as multi-item.
Use `page_assembly` for a normal mixed-role business deck. Preserve query
results in client-local `work/` evidence; never copy a catalog, preview or
source package there.

For page retrieval, the catalog already excludes a candidate whose independent
native text-region count is below that role's client-fact floor *or whose
native chart/table/workbook content cannot be completely governed by the
physical importer*. Treat a
`NO_MATCH` as a cue to select a lower-cardinality narrative form or split the
message; never relabel a one-textbox page as a five-item or dashboard page.
Certified semantic tags also recognize standard complete-work page anatomy:
`chapter_title`/`section_divider` is a `section`, and agenda/outline is
`contents`. Use those returned candidates rather than rejecting a good
complete-work page solely because its visual observation used a more specific
label.

After broad retrieval has selected a shortlist, revalidate each chosen page
with the same seven fields plus optional `candidate_ids`, for example
`"candidate_ids":["page_<24-lowercase-hex>_001"]`. This bounded audit returns
only that already-known catalog page and applies the same role, suitability and
native-region gates. It is not a filesystem lookup and does not permit an
unregistered page.

For `page_assembly`, every `selected_candidate_id` must be unique across the
deck. The physical importer intentionally rejects a repeated source page;
when a page type recurs (for example section dividers or data cards), select a
different returned candidate for each occurrence. Treat
`PAGE_SOURCE_DUPLICATE` as a composition correction, not an assembly retry.

Every returned candidate also has `page_id`, `deck_id`,
`theme_family_page_count`, `theme_family_visual_quality` and a certified
`style_signature`. Prefer a cover
from a complete certified work with enough eligible sibling pages for the
deck, rather than selecting the visually loudest single-page cover. A complete
family whose certified minimum portable visual-quality signal is below `0.80`
is not eligible as the deck anchor; this is only a prefilter and never replaces
the required independent rendered review. Choose
the cover candidate's `page_id` as
`art_direction.anchor_page_id`; copy its exact `style_signature` into
`allowed_style_signatures`. A complete anchor deck's sibling pages are allowed
even when their page-level signatures differ. Add at most **one** more
signature, and only when the query result proves a necessary compatible
cross-deck fallback: it must preserve the anchor's
colour-family. For a cool professional institutional system, balanced and
dark-blue pages may be deliberately combined for chapter/data/process rhythm;
red/ceremonial, green, warm, light-neutral or unrelated editorial fallbacks
are not compatible. Do not substitute a deck ID, style label or
natural-language direction. The exact
`art_direction` contract is:

```json
{"anchor_page_id":"page_<24-lowercase-hex>_001","allowed_style_signatures":["style_<24-lowercase-hex>"],"suitability":"institutional-finance"}
```

A cross-package fallback must also have a certified portable
`visual_quality` of at least `0.80` in its query result. A matching style
signature alone never permits a visibly weak page to enter a reference-grade
deck. If no such fallback exists, reframe the message with a compatible
anchor-family page or split the narrative; do not use a low-quality template
to satisfy capacity.

Before locking an anchor family, perform a one-slide `compose` + `preflight`
probe for the shortlisted cover. It must expose one native title/body slot
that fits the locked report title under the physical capacities. A cover is
permitted to carry only that title: never force presenter/date metadata into a
decorative title composition that has no certified metadata surface. Reject a
visually attractive cover whose native surface cannot hold the real title; do
this before inspecting or selecting its sibling pages. This is a hard
eligibility gate, not a cue to reduce font size or add freehand text.

When the anchor comes from a certified multi-page work, retrieve its sibling
pages by repeating the same query with optional
`"deck_id":"deck_<24-lowercase-hex>"` copied from the returned cover. Do not
use a page-level `style_signature` to retrieve siblings: those pages can carry
different vision signatures while retaining the same native theme. When the
anchor comes from a certified multi-page work, its other pages are a
controlled theme family: their shared PowerPoint master/palette/grid outranks
per-page vision wording such as “infographic” versus “corporate”. You may add
only the anchor signature plus one independently compatible fallback signature
under the rule above. This permits a
coherent full-work template to retain its own chapter/data cadence; it does
not authorize cross-deck random mixing.

For a complete-work adaptation with an anchor family of eight or more pages,
first call `inspect-deck` once on the chosen anchor `deck_id`. This is an
authorized **family-anatomy lookup**, not an uncontrolled fallback and not a
substitute for source/materialization validation. From its sanitized inventory choose the
unique pages that best express the locked narrative, excluding every page that
reports `requires_structured_data=true` unless the brief contains the complete
dataset required by that page's published `data_contract`.
Then use `strategy:"family_assembly"`: all 15 selected source pages must be
unique and belong to that exact inspected anchor deck; composition rechecks
source scope, observation hash, semantic role, native regions, capacity,
data-surface and family identity. A page described as clinical departments is
not an allowable process page merely because it shares the anchor's style.
The physical binding and QA gates still require nonempty client facts for every
eligible page. If the family cannot supply all required pages/capacity safely,
select a different anchor family; only then may the one registered compatible
fallback signature be considered through normal `page_assembly`.

For an `exact_deck` candidate, call `inspect-deck` with the returned `deck_id`
and write its value-free inventory to `work/deck-inventory.json`:

```bash
$PPTX_STUDIO_MANAGER inspect-deck ... --catalog "$CATALOG" \
  --observation-index "$OBSERVATIONS" --deck-id "deck_<24-lowercase-hex>" \
  --query-output work/deck-inventory.json
```

The inventory contains only ordered `page_id`, a safe native text-slot count,
content grammar and sanitized visual composition/tags. It contains no preview,
template copy, path, geometry or private bytes. Use it to select each unique
source page in source order. `exact_deck` accepts the inspected page's genuine
visual form even where its generic role label is imperfect; it still requires
at least one native text slot and the later preflight/binding gate reports the
actual editable surface. A page whose static chart would make client facts
misleading must instead be represented by a compatible physical fallback or
be rejected at rendered inspection—never leave wrong template figures as
client evidence.

For example, the full composition request begins as follows (replace all
placeholder values only with query-result values):

```json
{"schema_version":"1.0","strategy":"page_assembly","art_direction":{"anchor_page_id":"page_0123456789abcdef01234567_001","allowed_style_signatures":["style_0123456789abcdef01234567"],"suitability":"institutional-finance"},"slides":[{"slide_id":"s01","role":"cover","candidate_ids":["page_0123456789abcdef01234567_001"],"selected_candidate_id":"page_0123456789abcdef01234567_001","minimum_capacity":12}]}
```

## 3. Plan and bind without visual implementation authority

Compile a composition plan, then run the native-capacity preflight, and only
then write the adaptation plan. The model may return
only candidate IDs, selected IDs, roles, fact IDs, asset IDs and selection
reasons. Approved client copy belongs only in the separate content outline,
never as a visual implementation decision. It may not output paths, coordinates,
fonts, colours, CSS/HTML, code, OOXML or post-assembly repairs.

For normal client work, do **not** hand-map `region_id` and `shape_id`. Before
production, create and lock a `fact-store.v1.json` from the agreed brief and
authoritative data. It is the client-copy ledger: every active fact has a
unique `id`, exact `text`, `source_id`, locator, status and approved
`recommended_beat` (`s01`…`s15`). Then write a small
`content-outline.v1.json`: it has only `schema_version` and `slides`; each
slide has `slide_id` and an ordered `facts` list; in a locked production run
every fact is `{"fact_id":"locked-client-fact-id","semantic_role":"title|label|metric|body","component_key":"title.01"}`.

The fact store is strict. Do not invent a shortened variant: this is the
minimum valid shape (extend it with more facts only):

```json
{"schema_version":"1.0","project":{"title":"客户已确认项目名","language":"zh-CN"},"sources":[{"id":"facts-md","kind":"client-data","locator":"FACTS.md"}],"facts":[{"id":"s01-title","text":"客户已确认标题","status":"active","source_id":"facts-md","locator":"FACTS.md#报告信息","recommended_beat":"s01"}]}
```

`project`, nonempty `sources`, every source `id`, every fact `status:"active"`,
and a source ID matching every fact's `source_id` are mandatory. The outline
must contain only `{fact_id,semantic_role,component_key}` references; never add `value`,
`text`, `source_id`, source paths, or a free-form replacement there.

Immediately run `validate-fact-store --fact-store work/fact-store.v1.json`
with the standard manager/sentinel arguments. Capture its JSON result as
client-local evidence, for example:

```bash
$PPTX_STUDIO_MANAGER "${COMMON[@]}" validate-fact-store \
  --fact-store work/fact-store.v1.json > work/fact-store-validation.json
```

Do not retrieve, compose or write an outline until that file reports
`status:"PASS"`; repair the ledger itself on failure.
Pass `--fact-store work/fact-store.v1.json` to `bind-outline`. The binding
command rejects free-form values, unknown IDs, reused IDs and a fact bound to
the wrong approved beat. Therefore an
agent cannot add a convenient KPI, rewrite a claim, or pad a template merely
to satisfy a slot count. The legacy value form is for migration tests only,
not client delivery.
The `bind-outline` command chooses only unused certified native slots from the
preflight, **requires** the requested semantic role (only `any` is
role-agnostic), applies the exact native
capacity, generates stable fact IDs, and returns a strict adaptation request.
It fails on an overflow or an unavailable slot; it never truncates, duplicates
or silently falls back to a template's sample copy. Then run `adapt` on that
generated adaptation request **and the same `--preflight-output` file**. The
physical preflight is the only capacity authority for adaptation; catalog
capacities are retrieval hints and must not override a successfully bound
native slot.

### Component grammar is mandatory

`component_contract` in the preflight is the agent's page-level layout API. It
publishes ordered keys such as `title.01`, `label.01`, `label.02`,
`metric.01` and `body.01`, with only semantic role, native capacity and a
fragment-lockup flag. It never reveals shape IDs, coordinates, source copy or
private paths. Use those keys explicitly in every production outline fact.

Treat them as a component sequence, never as one interchangeable text pool:
write a page heading to `title.01`; keep each project/data card's name and
value in the corresponding returned label/metric order; preserve dashboard
card label/value order; and place clinical-network central totals separately
from the surrounding chip labels. If the brief cannot fill meaningful
components, choose a simpler certified page. `bind-outline` rejects a
misspelled, role-incompatible, over-capacity or already-used key instead of
silently spilling the fact into an unrelated card.

When `component_groups` is nonempty, it is a stronger rule than adjacency:
each opaque `group.01` lists components that the certified source deliberately
places in one visual unit. For example a KPI group can contain a label and a
metric, and a roadmap group can contain an ordinal and an action. Bind all
available client facts for that group before moving to the next group; never
put a group member's label or value into a different card merely because its
capacity also fits. A group alias reveals neither source text nor geometry.
This is enforced: if the outline selects one member, `bind-outline` rejects
the page until every member is explicitly populated. Select a simpler page
when the agreed brief has no truthful fact for the full component; do not
invent filler or leave a stale template value behind.

This is the central weak-model guardrail: the agent decides only which
approved client fact belongs to which semantic component; the runtime owns the
template geometry and all PowerPoint mechanics.

The preflight also reports a value-free `content_contract` per selected page:
the number of certified title, label, metric and body slots that can accept
client content. Use it to preserve the visual grammar of cards and dashboards
(for example, a five-card financial page normally needs its five labels and
corresponding metrics), rather than merely satisfying the role's minimum fact
floor. It contains no template copy, shape IDs or geometry.

For a text-only page with eight or more repeated label or metric surfaces, the
binder enforces structural coverage (65% of that repeated surface). This is a
hard anti-empty-template gate: a department/network page with twelve chips
cannot be released with only two facts and ten blank boxes. Supply genuine
facts for that grammar or reselect a smaller/appropriate page. Governed
chart/table pages are excluded because their published data contract owns the
visible data surface.

Treat a zero count as an absolute design constraint. In particular, a
chart-led page with `body: 0` must carry its interpretation through its
published structured data, title, labels and metrics; do not add a prose
finding as `body` and expect it to occupy a headline/card surface. Omit the
secondary prose, shorten it into a fitting approved label, or select a page
with a certified body region. A binding failure is a required replan, never a
reason to relabel prose as `title`, `metric`, or `any`.

### Certified fragment-title lockups

Some high-end Chinese editorial pages express a headline as deliberately
placed one-character text boxes. When preflight reports a region with
`"fragment_group":true`, it is a certified **title-only** lockup. Give it one
compact `title` fact of no more than `native_capacity` characters; the binder
emits `replace_fragment_text` and preserves the template's original character
positions, styles and editability. Do not manually split characters, use its
opaque region ID, add spaces to pad it, or call it a `label`/`any` fact.

A cover can have two fragment title bands. Use them as a short visual title
and short visual qualifier (for example `年度总结` and `财务运营`), then place
the full formal project name, presenter and date in ordinary certified
body/label surfaces. If the required visual title cannot be expressed within
the published fragment capacities, choose a different cover; never shrink the
lettering, create new text boxes, or erase the composition.

For a selected governed data page, the same preflight exposes a value-free
`governed_content_contract.data_contract`. This is the sole authority for the
separate `structured-data.v1.json`: copy its `contract_id`, supply every
published field at exactly its published count, and keep every display value
within the matching `max_chars` item. The values are customer facts, not a
template transcription. Never guess a contract, reuse a contract from a
different selected slide, or construct a partial chart/table payload. A
missing or invalid field deliberately stops `adapt`; reselect a native-text
page if the client cannot provide the complete dataset.

Before selecting a candidate, inspect `requires_structured_data` in the query
result. A native chart/table/workbook page is not decorative: select it only
when the brief supplies its complete published `data_contract` (all fields,
counts and `max_chars`). Do not select it merely because the brief has a few
headline metrics, do not clear its data, and never retain the template's sample
figures. Put the complete semantic values in a separate
`structured-data.v1.json` file, with only `{"structured_data":[...]}`; each
entry is `{"slide_id":"...","contract_id":"...","values":{...}}`.
Pass it to `bind-outline --structured-data work/structured-data.v1.json`.
The model never sees source shape IDs, workbook cells, chart XML, colours or
geometry. If the data is incomplete or a value exceeds `max_chars`, choose a
compatible native-text page or shorten the customer-approved display notation.

For `assemble`, pass both different files explicitly: `--adaptation-input`
points to the generated request and `--adaptation-plan` points to the compiled
plan. This deliberate separation prevents a request from being mistaken for
its compiled plan.

Every replacement must fit a certified region. If approved copy is too long,
shorten it from the source or split the narrative; never reshape the slide.

`composition-request.json` has only `schema_version`, `strategy`,
`art_direction` and `slides`; every slide has only `slide_id`, `role`,
`candidate_ids`, `selected_candidate_id` and `minimum_capacity`. Compile it
with `compose`, then invoke `preflight` with the composition plan, catalog,
`$PPTX_STUDIO_PRIVATE_SOURCE_ROOT` and `work/native-capacity-preflight.json`. This value-free
result is the authority for every selected `region_id`: bind text only when it
fits that region's `native_capacity` (and every listed `shape_slots` capacity).
Split the narrative across distinct selected regions/pages when it does not;
do not reuse a fact ID or put the same title into multiple slots. An adaptation request
has only `schema_version`, `facts`, `assets`, `bindings` and `structured_data`;
`structured_data` is `[]` unless a selected preflight contract requires it.
Each binding must
include all of `slide_id`, `operation`, `region_id`, `shape_id`, `fact_id` and
`asset_id`, using `null` for fields inapplicable to that operation. Compile it
with `adapt` before `assemble`. Catalog capacity is a retrieval hint only and
must never be used in place of the native-capacity preflight.

Each fact record is exactly `{"fact_id":"...","value":"..."}`. Empty
values are allowed only to clear an unused native text slot; they never
substitute for customer content. Before `assemble`, confirm that every
customer-required title, number and conclusion still has one nonempty binding.
The compiler also enforces a role-specific minimum of *distinct* client facts:
cover 1, contents 5, section/closing 1, one/two-item 3, three/four/five/six-item 4/5/6/7,
multi-item/dashboard 6, team 4, timeline/process/business-model 5.  This is a release
gate, not a suggestion: if `CLIENT_BINDING_COMPLETENESS_INSUFFICIENT` is
returned, select a lower-capacity candidate or provide/bind the missing
client facts.  Never satisfy it by repeating a title or retaining template
sample copy.

## 4. Assemble, inspect and deliver

The materializer resolves selected package hashes only below the private root,
imports complete editable OPC dependencies, binds native text slots, and uses
aspect-ratio-safe cover crop for approved images. Its value-free lineage report
records catalog page, package hash, slide number, slot and asset/fact hashes.

The only automatic repair is compiler-owned `shrink-to-fit` in an approved
text slot before import. Any other defect requires replan/reassembly.

If assembly returns `TEXT_SLOT_CAPACITY_EXCEEDED`, use its `slide_id`,
`region_id`, `fact_id`, `requested_chars` and `native_capacity` fields to
shorten or split only that confirmed fact, recompile `adapt`, then retry
assembly. This runtime-native capacity is authoritative over a retrieval-time
catalog estimate; do not guess, freehand-edit, or repeatedly retry unchanged
plans.

Before beginning a client run, read the public Skill and manager from the
operator-provided runtime variables above. Confirm those exact paths still
exist immediately before `query`, and stop with `RUNTIME_UNAVAILABLE` if
either changes. Do not substitute an old global Skill directory, a historical
`window-pptx` installation or an unapproved renderer.

Release only after all gates pass:

- output has complete physical page/slot lineage and opens as editable PPTX;
- package integrity, relationships, bounds, text overflow, tiny text,
  placeholder/source residue, binding completeness, overlap, density,
  repetition, image crop and style coherence checks pass;
- LibreOffice opens the deck; PowerPoint COM is optional certification only;
- a fresh visual reviewer that did not author/select the deck reviews rendered
  pages against the locked rubric. Do not self-score or self-approve release.

## Authority boundary

Allowed: client questions, locked narrative, roles, candidate IDs, selected
IDs, fact/asset IDs, and reasons. Forbidden: direct shape creation, raw
geometry/style, unregistered templates, private source data, arbitrary OOXML
edits, placeholder copying, fabricated data and self-approved release.
