# Phase 54: Cross-Library Component Assembly and PowerPoint Compatibility — Context

## Product Boundary

The input is a client-only requirement folder: locked brief, facts/data and
approved client assets. It contains neither a reference deck nor private
template bytes/previews. The installed `pptx-studio` Skill resolves the
separate user-authorized local library. In a managed Codex install, commercial
asset bytes remain absent by design; `PPTX_STUDIO_SKILL_ROOT` points to the
checked-out local Skill tree (or `PPTX_STUDIO_PRIVATE_ROOT` points directly to
its `.private` root). This declared resolution path is outside the client
folder and is verified by `runtime-check`; no discovery scan is permitted.

The authoring agent follows: discuss missing requirements → lock narrative,
audience and success criterion → select theme/style anchor → retrieve a
bounded deck/page shortlist → retrieve components only when a complete page
cannot express the fact grammar → submit ID-only composition/binding plan →
compiler assembles/adapts → harness checks and repairs only declared-safe
slots → independent review.

## Decisions Already Locked

- `gpt-5.6-terra` medium is the first acceptance author.
- The model may choose narrative, candidate/page/component IDs and fact/asset
  IDs; it may not author geometry, raw colours, fonts, OOXML, code or a
  release result.
- One dominant style family is mandatory. Compatible fallback is catalogued,
  bounded and explainable; random variation is prohibited.
- The agent derives page count from narrative decisions, fact density and
  certified capacity. It must produce a page-rationale ledger and merge
  under-filled or split over-capacity beats. For a substantive acceptance
  brief of 10+ pages, it uses at least 6 packages / 5 categories
  and no package contributes over 4 pages. Both whole pages and components
  must have physical provenance.
- The private catalog consumes the final certified-core visual disposition.
  Hash-matched `deny` pages are blocked through physical assembly, and runtime
  rejects a stale certification overlay rather than trusting old eligibility.
- Acceptance covers two independent client packs: a professional report and
  an academic defense. They share the Skill/runtime, not narrative or page IDs.
- `ppt/tags` is source-authoring metadata. If it is omitted from delivery,
  every corresponding `p:custDataLst/p:tags r:id` owner reference must be
  removed before the package is written.
- LibreOffice is a portable check, not PowerPoint compatibility proof.

## Current Regression Finding

The work-report v55 package retained `p:custDataLst/p:tags` rId references on
slides 2, 3, 4, 9, 10, 12 and 13 after the importer intentionally omitted the
associated tag relationships. LibreOffice rendered these slides but PowerPoint
displayed them blank. The source-native v57 recovery, which retains the source
master/layout/relationship topology while applying governed content bindings,
visibly renders in PowerPoint. It is a regression baseline only, not Phase 54
mixed-library acceptance.

The fixed reference anatomy also exposed a distinct product defect: a section
divider (for example, "精益治理") could be followed by a second title/divider
instead of a page that proves the section claim. That is a mechanical source
sequence replay, not narrative design. From this phase onward, an unowned
divider, an under-filled beat, or a page with no audience decision is a hard
planning defect even if every source page renders.

## 2026-08-16 Planning Discovery

The clean hospital-finance pack validated as a 17-beat, 73-fact narrative and
the current catalog runtime passed. A first mixed selection also met the
11-package/8-category/4-page maximum and dependency-budget gates, but native
binding exposed two planning gaps before any delivery could be released:

- Cardinality alone cannot prove a page has the required mix of title, label,
  metric and body surfaces.
- A matching count cannot prove that a long approved label or date fits one
  native surface.

The planner now accepts optional value-free `content_requirements` and
`minimum_role_capacities` per beat and rejects a candidate before composition
when either fails. Regression tests cover a five-body ledger rejected from a
four-body page and an eight-character label rejected from seven-character
native labels. This is a durable weak-model guardrail, not a client-specific
override.

The remaining professional-pack constraint is genuine: the locked cool
cluster cannot simultaneously supply a long-label solution page, the four-step
process date capacity, the four-body investment ledger plus its conclusion,
and a non-repetitive conclusion page under the current three-card reuse limit
and dependency budget. A no-anchor probe and an 18-beat probe both returned
`STYLE_CLUSTER_FEASIBILITY_NO_MATCH`. The next implementation slice must add
certified component-level composition or a compatible curated page family;
neither a text rewrite nor a fourth repeated card page is an acceptable fix.

## 2026-08-16 Physical Timeline Probe

The hospital pack's final validated narrative currently has 15 delivery beats;
`s14` owns four source-located date/action milestones. The manager's new
disposable `probe-page` route executed the full compose -> native preflight ->
binding -> adaptation -> physical import -> QA transaction for certified
cool-style candidate `page_27dd147759da5f877b0c99ad_001`. It returned
`NO_MATCH`: the selected source has five required timeline groups, and its
second date field cannot fit the source-grounded 14-character label. A second
catalog candidate with four apparent date-bearing shapes was rejected by the
bounded manager revalidation before import. Neither result may be promoted to
the compatible style cluster.

This establishes a real remaining runtime gap: exact-cardinality dated
milestones need either a quality-eligible source page with the matching number
of certified date/action groups, or a separately certified,
compiler-owned timeline-cardinality adaptation that removes a complete native
milestone unit (including its visual dependencies) and then passes physical
render/QA. Ordinary `process` fallback, blank fifth node, invented date/action
or freehand repair are prohibited.

## 2026-08-16 Professional-Pack Recovery Findings

The current locked hospital-finance brief remains valid at 15 narrative beats,
but a resumed author run exposed two separate failures that must not be
collapsed into a generic model failure:

- The style planner read individual catalog fragment regions for a cover
  lockup and rejected a cover whose real native title surface had already
  passed `probe-cover`. The planner now considers the catalog region capacity
  and its native text-surface capacity together; native preflight remains the
  final binding authority. The focused style-planning suite passes after this
  repair.
- After that repair, the ordinary plan still has no feasible professional
  cluster. The active library has no institutional-finance suitable,
  independently high-quality (`>= 0.80`) closing page with one editable
  surface able to carry the locked 16-character approval CTA. The only
  capacity-safe active quote candidate was visually inspected and is a
  consumer wedding image; a city-network closing candidate was independently
  reviewed by Agnes and rejected as generic/celebratory with insufficient
  readable CTA capacity. These pages are not eligible for a hospital delivery.

The next slice is therefore curated-library completion, not a threshold
exception: identify or add one locally authorized, template-native,
institutional closing page with an atomic long-statement surface; render it;
obtain independent visual certification; then rebuild the private catalog and
certification overlay. In parallel, expand the certified component profile
beyond its current single-source `multi-item`/`dashboard` set so the ordinary
planner can legally fall back for `s04`, `s10` and `s11` without weakening
whole-page quality gates. A short CTA, a generic one-item page, a manually
drawn ending, or a lower visual-quality floor is not an acceptable recovery.

## 2026-08-16 Visual Re-observation and Planner Recovery

The visual index contained a hash-bound but semantically incorrect observation
for `page_0692ee8d14d47efe7336ed05_001`: its blue skyline quote page had been
recorded as a four-node process diagram. The maintenance runtime now supports
an operator-specified exact `--page-id` re-observation scope. It validates that
every ID belongs to the pinned catalog and that the local PNG still matches the
catalog image hash before an Agnes batch may overwrite the stale observation.
The corrected observation identifies a corporate skyline `quote` page.

That page is a quality-eligible, institutionally suitable, 24-character
native-title quote fallback for the locked 16-character hospital approval CTA.
It passes the two-page cover/closing feasibility probe. A blue city cover
candidate was physically bound and passed mechanical QA, but independent Agnes
review rejected it as a client-ready hospital closing because it lacks a formal
signoff and uses generic city imagery; it remains excluded.

The full professional plan now reports only `s10` and `s11` as named
non-structural role gaps, which are eligible for component fallback. However,
the ordinary-page subset remains `STYLE_CLUSTER_FEASIBILITY_NO_MATCH`.
Diagnostic inspection shows a separate semantic-library deficit: `s07` and
`s08` are approved process beats but the prior request mislabeled both as
`three-item`; the one eligible three-item page cannot be placed on adjacent
beats. Correcting both to the truthful three-step `process` grammar exposes
that no quality-eligible process page has the required title plus three paired
label/body steps. This must be addressed by certified process-page/component
curation or a lossless narrative replan, never by relabeling the process as
cards.

## 2026-08-17 Professional r5 Cluster and Component Evidence

The prior diagnosis that `s07` and `s08` were process pages was incorrect.
`s07` is three parallel capability units; `s08` is a two-part scope/result
claim; and the separated `s09` is three governance units. The revised r5
narrative validates 16 delivery beats and 59 locked facts without padding a
requested page count.

Three runtime repairs were required before the retained whole-page subset
could be planned truthfully:

- a certified blue-skyline quote closing is classified as cool only for a
  corporate/minimal skyline observation with no warm colour cue;
- a cool professional art direction may use an anchor plus up to three
  independently certified compatible signature variants, still checked for
  colour family, professional archetype, suitability and quality;
- a component-fallback planning request preserves each retained beat's
  original `sequence_index`, preventing a component omission from turning
  non-adjacent section dividers into a false source-repeat violation.

With those controls, the r5 whole-page subset passed `plan-style-cluster`:
13 selected pages, 9 source packages, 8 categories, at most 4 pages per
source, and 100% cool-professional cluster coverage. The remaining beats are
exactly `s04` (four operational indicators), `s11` (five investment facts)
and `s12` (three KPIs plus acceptance statement).

The existing 16-component private profile is not yet eligible for this deck:
its only dashboard and investment-card hosts are green/soft-beige or
teal/gold, not compatible with the locked cool-blue institutional cluster.
Compilation correctly fails `STYLE_SIGNATURE_NOT_ALLOWED`; the profile must
be expanded from independently certified cool professional four/five-card and
KPI sources before the run can proceed. Treating those hosts as a compatible
page, changing the deck colour family, or relaxing the style gate is
explicitly prohibited.

## 2026-08-17 Component Curation Checkpoint

An independent Agnes review rejected five visually plausible blue candidates:
the five-block grid contains template-owned office portraits and alternating
photo/text frames, the three-card page is consumer-marketing styled, the
four-column page is a portrait roster, the selected three-section source has
an HR photograph, and the research page carries publication-specific imagery.
They are not admissible for an institutional hospital report even though some
match the colour signature or cardinality.

The runtime now includes an operator-only `curate-components` compiler. It
accepts an explicit private curation declaration but derives all source
package/slide hashes, complete shape closures, relationship IDs, field
capacities and equal-size host checks directly from the certified source
PPTX. This prevents manual hash fabrication when a future independently
reviewed cool-professional source is added. It does not make an unsuitable
page suitable, and no profile was expanded from the rejected candidates.

## 2026-08-17 Selective Component-Promotion Evidence

The library now has an operator-only selective-promotion transaction for
archived packages. It copies only an explicit reviewed package list to a
component-only source category, verifies the source and destination SHA-256
values, and leaves the archive originals intact. Ordinary query, deck
inspection and style planning exclude this category; only a compiled
component-profile may use one of its pages as a host. This prevents a future
author from mistaking a useful visual fragment for a universally suitable
complete page.

Three initially promising cold-blue data-base pages were promoted, rendered,
and independently reviewed. The resulting runtime health report passed with
509 catalog pages, 509 observations and 298 source packages. Review evidence
accepted the four-card KPI composition as an editable operational-KPI source,
but corrected two earlier assumptions: the apparent investment composition
has only four low-capacity segments, and the three-outcome strip has no
independent acceptance-statement surface. They cannot satisfy the locked
investment or acceptance beat merely through changed labels.

A hash-bound exploratory profile with four operational KPI cards and one
three-outcome strip plus heading compiled and queried successfully. It is not
release authority: the KPI source is a cool infographic rather than the locked
professional cluster, while the outcome source has a mixed rather than cool
colour family. The compiler must continue to reject either source under the
current art direction. The remaining work is to curate components whose
native host grammar, field capacity, visual semantics and style profile all
match `s04`, `s11` and `s12`; changing the report to fit a weak source is not
an acceptable recovery.

## 2026-08-17 Fixed Canvas Insertion Capability

The previous component contract only replaced an equally sized host closure.
That is insufficient for a professionally designed KPI canvas that has native
KPI cards but no heading or conclusion surface. The runtime now supports a
private profile v3 `canvas` anchor. An operator supplies a reviewed title or
statement source closure and a target host page; the compiler derives the
target rectangle from the source closure, verifies equal dimensions, and
rejects the declaration unless the target zone is empty apart from explicitly
declared underlays. At runtime the agent still submits only opaque component
and anchor IDs. The physical assembler re-verifies component, canvas and host
slide hashes, translates the native editable closure without scaling, repairs
shape IDs and preserves relationship closure.

This closes the *mechanical* gap for `s04` (heading plus four KPIs), `s11`
(heading/statement plus investment cards) and `s12` (heading, outcome cards
and acceptance statement). It does not certify any current source as a
cool-professional hospital asset. The next operator step is a visual curation
pass to identify source-native title/statement closures and compatible KPI
hosts that satisfy the locked cool-blue art direction.

## 2026-08-17 Cold-Blue Source Screening

The current runtime gate remains healthy: 509 catalog pages, 509 visual
observations, 298 source packages and 80 final-deny pages. A focused,
authorized Agnes review rejected six superficially blue high-quality pages:
two had template business people or service-marketing imagery, one had an
aircraft/runway sales motif, one used stock photography, one was tax-service
marketing art, and one was an academic conference divider. A second review of
four no-media candidates rejected a glossy hierarchy page as whole-page-only,
a neon platform architecture page as technology marketing, and a wave-card
marketing page as consumer promotion. It accepted only
`page_3c59f24f9cd8c5995bd7f8ff_001` as a potential source for a three-card
cool-blue grammar; its native page has one heading and three modular phase
cards, but no standalone acceptance-statement region and no four/five-card
KPI or investment grammar. It is not promoted for the professional r5 run.

The component-source style gate now evaluates every selected component source
against the same locked art direction as its host. This prevents the older
green/teal or warm component profiles from entering through a visually
compatible host page. The curation search therefore remains open for genuine
cool-professional title/statement and four/five-card sources rather than
lowering the gate or relabelling an unsuitable page.

## Non-goals

- No private asset bytes, visual thumbnails or commercial credentials enter
  Git, logs or the clean client folder.
- No rasterized slide or PptxGenJS/HTML/freeform fallback counts toward the
  mixed-library acceptance.
- Do not claim release until PowerPoint and independent blind visual gates
  have exact-artifact evidence.
