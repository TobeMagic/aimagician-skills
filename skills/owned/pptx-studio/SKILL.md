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
presenter, date, language, delivery duration/range (if supplied), deadline, anatomy, authoritative data,
approved assets/rights, brand constraints, prohibitions and acceptance rubric.
If a material field is missing, ask concise questions only. Never invent a
fact, claim, brand rule, asset or decision. A normal business deck has cover →
directory → section dividers → evidence → recommendation/summary → closing;
change this only when the locked brief says so.

Do not turn a client preference or a historical reference length into a fixed
slide count. Normalize the locked discussion into
`work/brief.normalized.json`, then write `work/narrative-plan.json` before any
template query. The plan has beats, not a requested count: every retained beat
must state its audience decision (`page_intent`), one-sentence conclusion
(`key_message`), owned fact IDs, information grammar, density and a
keep/split/merge/delete decision. The harness derives the delivery count only
from valid retained beats. It rejects a body without facts, an over-capacity
beat that was not split, and a section divider not followed within two delivery
pages by evidence for that same section.

After the runtime paths below are available, validate this contract before
retrieval. If it fails, revise the narrative or ask the client about the
specific missing fact; do not retrieve templates to fill a structural hole:

```bash
$PPTX_STUDIO_MANAGER validate-narrative \
  --source-root work/source-root.sentinel --archive-root work/archive-root.sentinel \
  --manifest work/manifest.sentinel \
  --brief-normalized work/brief.normalized.json \
  --narrative-input work/narrative-plan.json \
  --narrative-output work/narrative-validation.json
```

The resulting `slide_count` and ordered `delivery_beat_ids` are evidence, not
a user-facing target to backfill. A section followed by a second title-only
page is a validation failure, not a visual rhythm choice.

Before preflight or assembly, verify that the composition plan still matches
the pinned catalog, visual observations and compiler. A `MIGRATION_REQUIRED`
result means re-plan from the locked brief; never edit its old IDs to force it
through a changed component contract:

```bash
$PPTX_STUDIO_MANAGER verify-replay \
  --source-root work/source-root.sentinel --archive-root work/archive-root.sentinel \
  --manifest work/manifest.sentinel --catalog "$CATALOG" \
  --observation-index "$OBSERVATIONS" --composition-plan work/composition-plan.json \
  --replay-output work/replay-report.json
```

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
  uses `data` or `dashboard` **only** when the brief supplies the complete
  governed time series/category grid required by that native data contract; a
  before/after, plan/actual, year-on-year or category variance uses
  `comparison`; a published numeric grid uses `table`; an ordered future plan
  uses `roadmap` or `timeline`. These are semantic page roles, never aliases
  for `multi-item` merely because a source page has several labels. When the
  certified source has a governed chart/table data contract, use that native
  data surface and provide its complete client data; do not flatten it into
  text cards.
- clinical-department coverage, clinical-operation coordination or a
  multi-department work interface uses `clinical-network`; never call it a
  generic process, comparison or data page. This specialised role can use a
  certified department-network composition only when the locked message is
  genuinely about those relationships.
- people, awards, map, business model, product, quote and partners use their
  specialist categories.

When no dedicated certified closing page can hold the complete approved CTA in
one native title surface, the deterministic closing retrieval may consider a
certified `quote` page only when its independent visual observation explicitly
labels it `quote`. This remains a `closing` role and must pass the closing
statement-capacity, style-cluster, quality, binding and rendered-review gates.
On this narrow fallback only, bind the complete CTA as a `label` when the
preflight publishes its single quote statement surface as `label`; otherwise
use `title`. It does not authorize a generic content page, splitting one fact
over multiple surfaces, or a manually drawn ending.

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

The runtime resolves the private library in this declared order: an explicit
`--private-root`, `PPTX_STUDIO_PRIVATE_ROOT`,
`$PPTX_STUDIO_SKILL_ROOT/.private/`, then a co-installed Skill `.private/`.
Managed Codex installation deliberately excludes the commercial `.private`
tree, so local runs set `PPTX_STUDIO_SKILL_ROOT` to the checked-out Skill root;
this is normal local use, not a client-folder lookup. The operator must provide
`PPTX_STUDIO_SKILL_ROOT` and `PPTX_STUDIO_MANAGER`; the manager must equal
`$PPTX_STUDIO_SKILL_ROOT/scripts/manage_pptx_studio_library.py`; the catalog
is `<skill-root>/.private/intelligence/pptx-studio/catalogs/gaojie-active.v7.json`
and the observation index is
`<skill-root>/.private/intelligence/pptx-studio/vision/gaojie-active-observations.v1.json`;
the hash-bound component authority is
`<skill-root>/.private/intelligence/pptx-studio/components/gaojie-component-core.v2.json`;
the hash-bound visual certification ledger is
`<skill-root>/.private/intelligence/gaojie/certified-core.json`; the physical certified-category root is
`<skill-root>/.private/sources/gaojie`.
At the start of a run, verify those exact paths with `test -f` or stop with
`RUNTIME_UNAVAILABLE`. Do not discover them by scanning the filesystem. Never
write a private path, catalog content, preview or source package into the
client folder or final summary.

Component authorities are operator-maintained. A curator must compile a new
profile from an independently reviewed source/shape declaration with
`curate-components`; it derives source package and slide hashes, complete root
closures, field capacities, relationship IDs and equal-size host anchors from
the local certified PPTX. A v3 profile may also certify a fixed **canvas**
anchor: its target rectangle is derived from an existing source-native
component and the curator must prove that the corresponding target page zone
is empty (except for explicitly declared background underlays). The runtime
can then translate, never scale, that native editable component into the fixed
zone. Never hand-author component/anchor hashes or coordinates, make a profile
from catalog records alone, or use a canvas anchor to cover client evidence.
This curation route is private-library maintenance, never a production-agent
tool or client-folder action.

When a curator promotes an archived source only for component reuse, use the
operator-only `promote-components` route with an exact reviewed package list.
It hash-verifies an archive original and its copied component-shelf instance;
it never moves or restores a whole archived category. The resulting
component-only pages are intentionally excluded from ordinary page query,
deck inspection and style planning. They may enter a production plan only
through a hash-bound component profile and a certified host-anchor placement.
Render, independently review, and rebuild the catalog before compiling that
profile. A visual candidate that fails the intended role/cardinality review
must remain unselected even if its copy and render hashes are valid.

Use `$PPTX_STUDIO_MANAGER` only. It always requires
`--source-root`, `--archive-root` and `--manifest`; production harnesses pass
client-local `work/` sentinel paths for those three parser arguments. Do not
search the filesystem for alternatives.

Before any narrative or retrieval work, run the manager's runtime gate exactly
once and retain its generated JSON. Do **not** write, summarize or simulate
this report yourself: a hand-authored `status:"PASS"` is invalid evidence.
The accepted report has `catalog_page_count`, `observation_count` and
`source_package_count`, all positive, plus `catalog_denied_page_count` and
the catalog, observation and certification digest fields. Its catalog must
carry a `PASS` certification overlay bound to the current ledger. Use:

```bash
$PPTX_STUDIO_MANAGER runtime-check \
  --source-root work/source-root.sentinel --archive-root work/archive-root.sentinel \
  --manifest work/manifest.sentinel --runtime-output work/runtime-health.json
```

If this command fails or its required aggregate fields are absent, stop as
`RUNTIME_UNAVAILABLE`; do not create a substitute JSON file.

The certification overlay is operator-maintained, never agent-authored. A
page whose final certified disposition is `deny` is ineligible at query,
planning, composition, native preflight and physical assembly even when an old
materialization record says `eligible`. If the certification digest changes,
the operator rebuilds the catalog through the manager's `rebuild-catalog`
command with `--certification-evidence`; never edit catalog JSON by hand or
work around a denied page with a copied ID.

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
incompatible material. It also excludes a template-owned keynote speaker,
celebrity, public figure or other identifiable portrait. A client-approved
staff portrait may enter only as an explicit governed asset binding; never
retain a commercial template's person merely because the surrounding page
matches the requested role.
Use `general` only when the locked brief genuinely permits such material. Use
only returned `candidate_id` values in the composition request. The role
vocabulary includes `cover`, `contents`, `section`, `closing`, `one-item`,
`two-item` through `six-item`, `multi-item`, `team`, `timeline`, `process`,
`business-model`, `comparison`, `matrix`, `roadmap`, `risk`, `dashboard`, `data`,
`table`, `clinical-network`, `product`, `quote`, `partners`, `case-study` and
`map`.

Set `suitability` to `academic-defense` for a research or academic-defense
deck. This keeps research, methodology, experiment and scholarly evidence
eligible while excluding sales, campaign, consumer-product, celebrity,
product-showcase and stock-speaker subjects. It is a distinct audience gate,
not an alias for `general` or a relaxation of the institutional-report gate.

Select the role from the client message's information grammar before selecting a page:
data, comparison, table and dashboard have dedicated native surfaces and must
not be relabelled as multi-item.
When the message describes an implementation sequence, pilot order or
cross-functional handoff, select `process` even if its heading uses the word
“architecture”. Reserve `business-model` for a real set of independently
named business-model units with enough meaningful client facts to populate
them; decorative one-character diagram markers are never those units.
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

### Certified component fallback

Whole certified pages are the default. Use a component only after the
style-cluster planner or bounded role revalidation returns a truthful
`NO_MATCH` for that **non-structural** beat; it is not a way to decorate an
otherwise suitable page. Cover, contents, section and closing never use this
fallback. Query the private authority with:

```bash
$PPTX_STUDIO_MANAGER query-components \
  --source-root work/source-root.sentinel --archive-root work/archive-root.sentinel \
  --manifest work/manifest.sentinel --catalog "$CATALOG" \
  --observation-index "$OBSERVATIONS" \
  --component-profile "$COMPONENT_PROFILE" \
  --query-input work/component-query.json \
  --query-output work/component-query-result.json
```

The request is exactly
`{"role":"dashboard","style":null,"suitability":"institutional-finance","limit":6}`.
The response contains only opaque IDs, semantic roles and capacities, never a
private path, shape ID, source copy, geometry, colour or XML. V4 is the
production component contract: select one to six returned components only when
each one has a different returned `host_anchor_id` on the same returned
`host_page_id`. A component may occur once and an anchor may occur once. Do
not infer a coordinate, transform, colour, scale or extra component. The
private compiler owns the exact native insertion, ID repair and any
hash-certified cleanup of unused host cards. A returned anchor can be a
replacement reservation or a curator-certified fixed canvas zone; the agent
does not choose between geometry variants or receive enough data to redraw it.

Use the component fallback only after the ordinary style-cluster pass reports
the non-structural beat as `NO_MATCH`. Keep all ordinary page-eligible beats in
the planner result. Re-run the planner for those retained ordinary beats to
lock their candidates and art direction, then query components only for the
named missing beats. This is a controlled mixed plan, not a handwritten list
of unrelated pages. When a retained planner request omits a beat that will be
filled by a certified component, preserve each retained beat's original
zero-based `sequence_index`; the solver uses this only to prevent false
adjacent-repeat decisions across the component beat. It never exposes
geometry, source order or template data. Map a factual KPI grid to `dashboard` and an independently
named investment-card set to `multi-item` only when the component query returns
that semantic role; otherwise revise the narrative or ask for the missing
facts. Cover, contents, section and closing never use this fallback.

This fallback requires a schema-`4.0` composition request. It keeps the normal
v2 item shape for ordinary pages, and uses this ID-only item for a multi-card
component page:

```json
{"slide_id":"s08","beat_id":"evidence","role":"dashboard","host_candidate_ids":["page_<24-lowercase-hex>_001"],"selected_host_candidate_id":"page_<24-lowercase-hex>_001","component_placements":[{"host_anchor_id":"anchor_<24-lowercase-hex>","component_id":"component_<24-lowercase-hex>"},{"host_anchor_id":"anchor_<24-lowercase-hex>","component_id":"component_<24-lowercase-hex>"}],"minimum_capacity":2}
```

The root request also carries the exact profile authority:
`"component_profile":{"profile_id":"...","profile_sha256":"..."}`.
Pass `--component-profile "$COMPONENT_PROFILE"` unchanged to `compose`,
`verify-replay`, `preflight`, `adapt` and `assemble`. Missing or changed
profile authority is a migration failure: re-plan; do not replay stale IDs or
reconstruct the component with freeform shapes.

After broad retrieval has selected a shortlist, revalidate each chosen page
with the same seven fields plus optional `candidate_ids`, for example
`"candidate_ids":["page_<24-lowercase-hex>_001"]`. This bounded audit returns
only that already-known catalog page and applies the same role, suitability and
native-region gates. It is not a filesystem lookup and does not permit an
unregistered page.

For `page_assembly`, prefer a unique `selected_candidate_id` for every page.
The deterministic planner may use bounded reuse only when the certified
high-quality cluster cannot supply enough distinct pages:
in a 10–19 page deck, at most one extra instance; one source page at most
twice; the two beats must have the same one-to-six/multi/comparison/case-study
role and may not be adjacent. A sparse certified `section` page is the sole
structural exception: the planner may reuse it non-adjacently up to four times
when each occurrence binds a different approved section title and the page has
no more than two writable text surfaces. Cover, contents, closing, timeline
and roadmap pages are never repeatable; the planner may reuse one
`process` page once under the same non-adjacent, same-role content-repeat
budget when the two beats each fully populate its published step grammar. Do
not request repetition by hand; copy only the planner's exact result. Any other
`PAGE_SOURCE_DUPLICATE` is a composition correction, not an assembly retry.

Every returned candidate also has `page_id`, `deck_id`,
`theme_family_page_count`, `theme_family_visual_quality`, `page_visual_quality` and a certified
`style_signature`. Prefer a cover
from a complete certified work with enough eligible sibling pages for the
deck, rather than selecting the visually loudest single-page cover. A complete
family whose certified minimum portable visual-quality signal is below `0.80`
is not eligible as the deck anchor; this is only a prefilter and never replaces
the required independent rendered review. Choose
the cover candidate's `page_id` as
`art_direction.anchor_page_id`; copy its exact `style_signature` into
`allowed_style_signatures`. A complete anchor deck's sibling pages are allowed
even when their page-level signatures differ. Add at most **three** more
signatures, and only when the query result proves each necessary compatible
cross-deck fallback: it must preserve the anchor's
colour-family. For a cool professional institutional system, light-cyan,
balanced-blue and dark-blue pages may be deliberately combined for
evidence/chapter/data/process rhythm; red/ceremonial, green, warm,
light-neutral or unrelated editorial fallbacks are not compatible. Do not
substitute a deck ID, style label or
natural-language direction. The exact
`art_direction` contract is:

```json
{"anchor_page_id":"page_<24-lowercase-hex>_001","allowed_style_signatures":["style_<24-lowercase-hex>"],"suitability":"institutional-finance"}
```

A cross-package fallback must also have a certified portable
`page_visual_quality` of at least `0.80` in its query result. A matching style
signature alone never permits a visibly weak page to enter a reference-grade
deck. If no such fallback exists, reframe the message with a compatible
anchor-family page or split the narrative; do not use a low-quality template
to satisfy capacity.
The style planner applies the same `0.80` floor to ordinary selected pages,
including siblings from the anchor deck. The only lower structural floor is
`0.78` for a genuinely sparse `section` divider; this does not authorize a
weak contents, closing or body page.

Before locking an anchor family, perform the physical **`probe-cover`** route
for each shortlisted cover. It is a non-delivery transaction that composes,
preflights, binds the actual client cover facts, imports one physical page and
runs the same overlap/overflow/editability QA as a delivery. A capacity-only
`compose` + `preflight` result is insufficient: a source may have five safe
slots in isolation but still collide once a real title, department or date is
placed in them. The probe artifact is deleted after QA and never counts as a
client delivery.

Write one value-bearing input per returned candidate, retaining only real
client cover facts that this page is intended to display. A sparse title cover
must receive only the title; do not force presenter/date metadata into a
decorative composition without a certified metadata surface. The unbound
metadata remains in the fact ledger and must be placed once on an appropriate
opening or evidence page before final binding. For example:

```json
{"schema_version":"pptx-studio-cover-probe.v1","candidate_id":"page_<24-lowercase-hex>_001","suitability":"institutional-finance","facts":[{"fact_id":"cover-title","value":"项目立项汇报","semantic_role":"title"}]}
```

```bash
$PPTX_STUDIO_MANAGER probe-cover \
  --source-root work/source-root.sentinel --archive-root work/archive-root.sentinel \
  --manifest work/manifest.sentinel --catalog "$CATALOG" \
  --observation-index "$OBSERVATIONS" --private-source-root "$PPTX_STUDIO_PRIVATE_SOURCE_ROOT" \
  --cover-probe-input work/cover-probe-input.json \
  --cover-probe-output work/cover-probe-result.json \
  --assembly-workspace work/cover-probes
```

Only a literal `status:"PASS"` result may contribute its
`locked_anchor_page_id` to the later style-cluster request. `NO_MATCH`,
including `COVER_PROBE_PHYSICAL_QA_FAILED`, excludes that candidate rather
than asking the model to alter geometry, reduce typography or add freehand
text. This is a hard eligibility gate before inspecting sibling pages.

When the ordinary style-cluster pass reports a genuine `NO_MATCH` for a
**non-structural** beat and bounded candidate revalidation returns one
compatible cross-family page, prove that candidate with the disposable
physical **`probe-page`** route before adding its exact style signature to the
locked cluster. It is never a delivery, never accepts cover/contents/section/
closing, and it does not relax the component-fallback rule. The request carries
the role's semantic `minimum_capacity` rather than raw fact count: a four-step
timeline has capacity `5` (one title + four milestones), even though it binds
nine title/label/body surfaces.

```json
{"schema_version":"pptx-studio-page-probe.v1","candidate_id":"page_<24-lowercase-hex>_001","role":"timeline","suitability":"institutional-finance","minimum_capacity":5,"facts":[{"fact_id":"timeline-title","value":"项目里程碑","semantic_role":"title"},{"fact_id":"milestone-date-01","value":"2026 年 1 月","semantic_role":"label"},{"fact_id":"milestone-action-01","value":"完成项目立项。","semantic_role":"body"}]}
```

```bash
$PPTX_STUDIO_MANAGER probe-page \
  --source-root work/source-root.sentinel --archive-root work/archive-root.sentinel \
  --manifest work/manifest.sentinel --catalog "$CATALOG" \
  --observation-index "$OBSERVATIONS" --private-source-root "$PPTX_STUDIO_PRIVATE_SOURCE_ROOT" \
  --page-probe-input work/page-probe-input.json \
  --page-probe-output work/page-probe-result.json \
  --assembly-workspace work/page-probes
```

Only a literal `status:"PASS"` can establish that this candidate safely binds
the actual client facts. The temporary imported PPTX is removed after QA; its
`candidate_id`, `role`, probe hash and compact QA evidence are the only
permitted retained probe output.

When the anchor comes from a certified multi-page work, retrieve its sibling
pages by repeating the same query with optional
`"deck_id":"deck_<24-lowercase-hex>"` copied from the returned cover. Do not
use a page-level `style_signature` to retrieve siblings: those pages can carry
different vision signatures while retaining the same native theme. When the
anchor comes from a certified multi-page work, its other pages are a
controlled theme family: their shared PowerPoint master/palette/grid outranks
per-page vision wording such as “infographic” versus “corporate”. You may add
only the anchor signature plus at most three independently certified compatible
companion signatures under the rule above. This permits a
coherent full-work template to retain its own chapter/data cadence; it does
not authorize cross-deck random mixing.

For a complete-work adaptation with an anchor family of eight or more pages,
first call `inspect-deck` once on the chosen anchor `deck_id`. This is an
authorized **family-anatomy lookup**, not an uncontrolled fallback and not a
substitute for source/materialization validation. From its sanitized inventory choose the
unique pages that best express the locked narrative, excluding every page that
reports `requires_structured_data=true` unless the brief contains the complete
dataset required by that page's published `data_contract`.
Then use `strategy:"family_assembly"`: all selected source pages must be
unique and belong to that exact inspected anchor deck; composition rechecks
source scope, observation hash, semantic role, native regions, capacity,
data-surface and family identity. A page described as clinical departments is
not an allowable process page merely because it shares the anchor's style.
The physical binding and QA gates still require nonempty client facts for every
eligible page. If the family cannot supply all required pages/capacity safely,
select a different anchor family; only then may up to two registered compatible
companion signatures be considered through normal `page_assembly`.

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

For production without component fallback, the full composition request uses
schema `2.0`; a plan with a certified component fallback uses schema `4.0` and
the matching component-profile authority. Both embed the
**verbatim** PASS object from `work/narrative-validation.json`, and binds one
`beat_id` to every selected page in the same order. Schema `1.0` is legacy
fixture compatibility only and cannot be used for a new client delivery. For a
substantive 10+ page production plan, compilation additionally requires at least six
source packages across five approved categories, with no package supplying more
than four pages. This proves genuine page/component assembly without turning
provenance into a target for random variety: lock the visual anchor first, then
select compatible certified pages whose native bindability and media budget are
also safe.
At least 70% of a 10+ page plan must remain in the locked anchor **cluster**:
the anchor signature and up to two registered compatible companion signatures
are one cluster only when the compiler proves each signature's colour-family, tone and
professional archetype compatible. A raw signature is only a page-level
visual-description fingerprint; do not mistake corporate/minimal variants of
the same cool professional system for a collage. Warm, green, ceremonial,
neutral-light or otherwise incompatible pages remain outside the cluster and
are rejected.

### Required style-cluster feasibility pass for substantive delivery

For a normal 10+ page page-assembly deck, do not solve cross-library selection
by hand from a batch of unrelated candidates. After narrative validation, map
each retained beat to its semantic role and capacity floor, then call the
runtime planner once:

```bash
$PPTX_STUDIO_MANAGER plan-style-cluster \
  --source-root work/source-root.sentinel --archive-root work/archive-root.sentinel \
  --manifest work/manifest.sentinel --catalog "$CATALOG" \
  --observation-index "$OBSERVATIONS" --private-source-root "$PPTX_STUDIO_PRIVATE_SOURCE_ROOT" \
  --style-cluster-input work/style-cluster-request.json \
  --style-cluster-output work/style-cluster-plan.json
```

The input has `schema_version`, `suitability`, `slides` and an optional
`locked_anchor_page_id`; its schema version is the literal
**`pptx-studio-style-cluster-request.v1`** (never `"1.0"`). Each slide has
`{beat_id, role, minimum_capacity}` and may add two fact-derived, value-free
guards: `content_requirements` (`title`/`label`/`metric`/`body` → required
native-surface count) and `minimum_role_capacities` (the longest approved text
length for each semantic role). These guards are counts and character lengths,
never client copy, paths or geometry. Use them whenever the beat has paired
cards, a mandatory heading, or a long label/date; otherwise omit them. The
smallest valid start is:

```json
{"schema_version":"pptx-studio-style-cluster-request.v1","suitability":"institutional-finance","slides":[{"beat_id":"cover","role":"cover","minimum_capacity":1}]}
```

For a `timeline`, `roadmap`, or `process` with `content_requirements`, the
sequence contract is executable: declare exactly one `title`, equal nonzero
`label` and `body` counts, and set `minimum_capacity` to `1 + label count`.
Each label/body pair is one complete source-grounded step. Four dated
milestones therefore require `{"title":1,"label":4,"body":4}` and
`minimum_capacity:5`; a false four-capacity request is rejected before
retrieval rather than searching for a three-step template.

The planner receives the declared private source root so it can recognize a
curator-certified cardinality adaptation as an opaque page/role/capacity
eligibility key. It never receives removed shape IDs, geometry or hashes and
cannot request a deletion. A selected adapted timeline remains provisional
until normal native preflight and `probe-page` verify the exact client
date/action facts; this never authorizes a fifth milestone, a process downgrade
or an unregistered page adjustment.

After the required schema-1 cover probe has passed, retain that returned
`page_id` as `locked_anchor_page_id` on every later style-cluster replan for
the same brief. This prevents a closing/body recovery from replacing a cover
whose native title and metadata binding has already been proven. A locked
anchor that is no longer a safe candidate returns
`STYLE_CLUSTER_LOCKED_ANCHOR_NO_MATCH`; do not silently substitute another
cover.

### Deterministic text-backed role ladder

For a v1 text/fact-backed brief, select roles with this ladder before the
first planner call; do not improvise a chart or inflate card count. It is the
weak-model default and applies when the brief has no complete governed
structured-data contract:

| Locked message grammar | Exact text-backed role |
| --- | --- |
| structural cover / directory / divider / close | `cover` / `contents` / `section` / `closing` |
| one conclusion or one hero number | `one-item` |
| two named metrics, a trend headline plus its stated operational consequence, or a simple before/after | `two-item` (use `comparison` only when both sides are complete and genuinely contrasted) |
| three named investment, return, risk or parallel units | `three-item` |
| four/six named parallel units | matching `four-item` … `six-item` |
| more than six named parallel units | `multi-item` |
| causal handoff, operating sequence or rollout steps | `process` |
| dated milestones | `timeline` or `roadmap`, with the exact source-grounded milestone count |

Thus a brief that merely says “volume +18% and month-end close is delayed” is
`two-item`, not a native trend chart; “platform / interfaces / pilot” is
`three-item`, not a four-card page. The `minimum_capacity` is the number of
meaningful client units in that selected role, except a cover where it is the
short visual-title character count. A section uses its approved title fact's
character count, not an invented cardinality. Before calling the planner,
derive the optional surface guards from the locked fact ledger: a page with a
title, four labels and five bodies must request
`"content_requirements":{"title":1,"label":4,"body":5}`; if its longest
label has eight characters, also request
`"minimum_role_capacities":{"label":8}`. A planner `PASS` then proves the
selected page has the required editable slots before physical preflight.

If the first planner result is `STYLE_CLUSTER_FEASIBILITY_NO_MATCH`, preserve
every locked fact and key message. First correct a cover-capacity mismatch with
the shortest meaningful contiguous phrase already present in the approved
title, recording that exact source fragment as a separate cover-title fact.
Then re-run once with the next lower **truthful** role rung
(`six→five→…→one`, `multi-item→six`, or `comparison→two-item`) only when the
surviving named facts still fit that form.

If the complete slide sequence still has no feasible cluster, one
second-order narrative replan is allowed before stopping. It may merge only
adjacent body beats from the same section when all of their facts and key
messages remain explicit in one truthful grammar and the combined capacity is
valid. It may not delete or defer an approved fact, remove a required
structural page, merge across sections, or relabel a process/data relationship
as cards. Rewrite and revalidate `brief.normalized.json`,
`narrative-plan.json`, `fact-store.v1.json` and every `recommended_beat` before
calling the planner again; the new validated count is the delivery count.
This is narrative compression for the audience decision, not changing content
to fit an attractive template. If no lossless merge or truthful lower rung
exists, stop and request the missing client data. Never hand-select IDs after
a `NO_MATCH`.

For a cover, section or closing specifically, `minimum_capacity` is the
character count of the one source-grounded visual title, approved section
heading or complete approval request, not a fact count. The planner compares
it with one certified native **title** surface only. A complete closing request
is atomic: never split it over a title and decorative label merely to force a
narrow ending page. When the formal project name
is too long, create a separate visual-title fact only from a contiguous,
meaningful phrase already present in that approved title (record its precise
source fragment locator), and bind the complete formal title to an ordinary
certified body/label surface on the same cover. This is a traceable editorial
short form, not invented copy. If neither title/body surfaces fit, choose
another certified cover or ask the client; never silently abbreviate or force
the formal title into a decorative title lockup.
On `PASS`, copy the planner's `art_direction` and exact
`recommended_slides` IDs into the schema-2.0 composition request. Those IDs
already satisfy unique-page, anchor/fallback compatibility, cross-package
page-quality, 6-package/5-category, four-pages-per-source and conservative
private dependency-media-budget constraints. The budget is calculated inside
the private catalog and reported only as an aggregate; do not inspect source
PPTX files or manually substitute a heavier candidate. The final physical ZIP
size gate is still authoritative.
The evidence reports `reused_page_instance_count` and
`maximum_reuse_per_page`; zero is preferred. A nonzero count is valid only
under the bounded rule above and still counts toward package/category
diversity. They are a safe physical selection, not a visual score or a release decision.
This v1 planner is for a normal fact/text-backed beat and deliberately excludes
native chart/table/workbook pages: such a page may enter only through a future
explicit complete structured-data contract, never from a few headline metrics.
Accordingly v1 rejects `data`, `dashboard` and `table` roles. If the brief has
only a few approved metrics, reframe them honestly as `two-item` through
`six-item` or `multi-item` KPI/evidence cards; if it has an actual complete
time series, category grid or workbook-equivalent dataset, use the separate
structured-data route before any such role is selected.
On `STYLE_CLUSTER_FEASIBILITY_NO_MATCH` or `STYLE_CLUSTER_ROLE_NO_MATCH`, revise
the narrative grammar/capacity or ask for facts; never bypass it with random
cross-template choices. Do not replace this planning result with a handwritten
candidate list for a substantive mixed deck.

For example, the full composition request begins as follows (replace all
placeholder values only with query-result values and the narrative object with
the exact validator output):

```json
{"schema_version":"2.0","strategy":"page_assembly","art_direction":{"anchor_page_id":"page_0123456789abcdef01234567_001","allowed_style_signatures":["style_0123456789abcdef01234567"],"suitability":"institutional-finance"},"narrative_validation":{"schema_version":"pptx-studio-narrative-validation.v1","status":"PASS","brief_id":"locked-brief","brief_sha256":"<64-lowercase-hex>","narrative_sha256":"<64-lowercase-hex>","slide_count":2,"delivery_beat_ids":["cover","closing"],"section_evidence":[]},"slides":[{"slide_id":"s01","beat_id":"cover","role":"cover","candidate_ids":["page_0123456789abcdef01234567_001"],"selected_candidate_id":"page_0123456789abcdef01234567_001","minimum_capacity":12},{"slide_id":"s02","beat_id":"closing","role":"closing","candidate_ids":["page_0123456789abcdef01234567_002"],"selected_candidate_id":"page_0123456789abcdef01234567_002","minimum_capacity":12}]}
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
`recommended_beat` (`s01`…`sNN`, where `NN` comes from the narrative
validation). Then write a small
`content-outline.v1.json`: it has only `schema_version` and `slides`; each
slide has `slide_id` and an ordered `facts` list; in a locked production run
every standalone fact is normally
`{"fact_id":"locked-client-fact-id","semantic_role":"title|label|metric|body"}`.
The binder selects the smallest fitting unused native surface deterministically.
Use an optional `component_key` only when the narrative deliberately needs a
specific published surface (for example a hero metric), never as routine slot
guesswork.
For a certified linked unit whose published group includes `component_fields`, use
`{"fact_id":"locked-client-fact-id","semantic_role":"label|metric|body","component_group":"project-card.01","component_field":"project_name"}`;
the binder resolves the named compatible native member. This is the safe
default for any multi-text card: it prevents a same-role descriptor, amount or
unit from being swapped merely because both fit. For an older group without
published fields, supply facts in the returned visual member order. Never put
both target fields on one fact.

The fact store is strict. Do not invent a shortened variant: this is the
minimum valid shape (extend it with more facts only):

```json
{"schema_version":"1.0","project":{"title":"客户已确认项目名","language":"zh-CN"},"sources":[{"id":"facts-md","kind":"client-data","locator":"FACTS.md"}],"facts":[{"id":"s01-title","text":"客户已确认标题","status":"active","source_id":"facts-md","locator":"FACTS.md#报告信息","recommended_beat":"s01"}]}
```

An input paragraph may contain several explicitly stated client facts. Split
it into atomic ledger records when—and only when—the source itself names the
separate values/categories/actions. Keep the same `source_id` and use a
precise fragment locator such as `brief.normalized.json#facts[f07]:平台建设`.
For example, “平台 980 万、接口 420 万、培训与试运行 400 万” is three approved
investment facts; “周期缩短 30%、识别率 85%、月中预警” is three approved KPI
facts; and three named risks with their owners are three approved risk units.
This is traceable normalization, not invention. Conversely, do not split an
undifferentiated conclusion merely to fill cards. Perform this atomicization
before changing a three-/four-item beat into a weaker one-item page.
For a `timeline` or `roadmap`, every milestone is one complete linked unit:
create one source-located `date` fact and one source-located `action` fact for
each milestone, preserve chronological order from the authoritative source,
and bind both through the same published `timeline-step.NN` group using
`component_field:"date"` and `component_field:"action"`. Never bind all dates
first and all actions second, and never treat a date marker as a page title.
If the source does not provide both fields for every required step, select a
simpler page or ask the client; do not retain a blank milestone or infer copy.
The selected native page must publish exactly the same number of milestone
groups as the approved source. Never invent a fifth milestone to fill a
five-node timeline. When no quality-eligible timeline/roadmap has the exact
count, stop with an actionable `NO_MATCH` or use a separately certified
compiler-owned timeline-cardinality adaptation. Never relabel dated milestones
as `process`, even when the chronological order is retained.
A complete client brief also supplies the editorial title fact for every
non-sparse structural page it requests—especially contents/agenda, table,
dashboard and named section variants. Do not assume a template's existing
“目录” copy may survive: add the client-approved agenda title to the fact
ledger and bind it to the certified title surface. If it is absent, ask the
client during requirement lock rather than reaching `bind-outline` with an
empty mandatory title.
Numbered agenda ornaments such as `01`–`04` are compiler-owned navigation
structure, not client facts. Preserve them in their native shapes, exclude
them from the visual-surface coverage denominator, and never create duplicate
facts merely to bind them.
A single CJK glyph is not a meaningful reusable client fact (for example,
never split `建设` into `建` and `设` to satisfy paired fields); retain the
meaningful source phrase or select a grammar that needs fewer facts. Numeric
measurements and genuine non-CJK tokens remain valid.

`project`, nonempty `sources`, every source `id`, every fact `status:"active"`,
and a source ID matching every fact's `source_id` are mandatory. The outline
must contain only `{fact_id,semantic_role}`, `{fact_id,semantic_role,component_key}` or
`{fact_id,semantic_role,component_group}` references; never add `value`,
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
private paths. The rule engine auto-allocates ordinary standalone facts by
semantic role and exact capacity. Use a key only to make an intentional
surface choice; for a linked card use its published group and let the binder
resolve the exact native member.

Treat them as a component sequence, never as one interchangeable text pool:
write a page heading as a `title` fact (or target `title.01` only if it must
occupy that exact heading); keep each project/data card's name and
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
Its `component_intent` is a value-free cue such as `metric-label-card` or
`paired-label-unit`; use it to decide whether the client facts form one card,
one labelled content unit or a linked pair.
This is enforced: if the outline selects one member, `bind-outline` rejects
the page until every member is explicitly populated. Select a simpler page
when the agreed brief has no truthful fact for the full component; do not
invent filler or leave a stale template value behind.
The library may also mark a group `required:true`: this is a curated visual
component (for example a project card whose heading, description, amount and
unit are separate source shapes). It is not optional whitespace; every such
group must be completed from separately traceable client facts or the selected
page is rejected. Never attempt to bypass that gate with a repeated fact or
invented filler—split the source data into atomic, source-located facts during
the requirements freeze, or choose a more suitable page.

For any card, relationship or roadmap page with published groups, the binder
also requires visual-group coverage: a page with one to three groups must
complete all of them; a larger grid must complete at least half. A two-card
outline cannot be released into a seven-card KPI grid, nor may a clinical
network leave most relationship nodes empty. Either ground enough cards in
approved facts or choose a lower-cardinality certified page.

This is the central weak-model guardrail: the agent decides only which
approved client fact belongs to which published semantic field; the runtime
owns the template geometry and all PowerPoint mechanics. A field name is a
safe content contract, not a shape ID, coordinate or template text.

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

The binder also rejects any selected text-backed page when approved facts fill
less than the published visual-surface floor, including sparse section and
closing pages whose sample copy would otherwise be cleared from visible cards
or frames. `OUTLINE_VISUAL_SURFACE_COVERAGE_INSUFFICIENT` means re-plan the
beat, losslessly merge adjacent same-section evidence, or select a lower-density
certified page. It never authorizes filler, preservation of sample copy,
freehand drawing or manual post-assembly repair.

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
`pptx-studio` installation or an unapproved renderer.

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
