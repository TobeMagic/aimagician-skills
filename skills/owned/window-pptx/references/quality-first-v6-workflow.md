# Window-PPTX v6 quality-first workflow

## Purpose

v6.0 resets the rejected v5.1 visual floor. It first proves that the Skill can
support a capable authoring model at senior presentation-designer level. It
does not yet claim that an ordinary model can reach the same result. Weak-model
distillation starts only after v6.0 passes reference-parity acceptance.

The canonical route is:

```text
raw request and materials
-> ProjectBriefPack Draft
-> structured discussion
-> NeedsDiscussion
-> complete Locked pack
-> constrained NarrativePlan
-> certified candidate retrieval
-> TemplateSelectionPlan + SlideBlueprint
-> native editable materialization
-> deterministic QA and bounded repair
-> three-context AI-only blind review
-> release or NOT_RUN/FAIL
```

## ProjectBriefPack v1

The pack owns:

- RawIntakeManifest and original request;
- immutable FactStore and source locators;
- material roles, locators, rights, and required flags;
- primary audience, knowledge level, and decision authority;
- purpose, target decision, and observable success outcomes;
- presentation and Q&A time;
- brand tone, light/dark mode, required colors, and prohibited styles;
- main, minimum, maximum, appendix, and backup slide budgets;
- required cover, directory, section, evidence, decision, closing, and
  appendix anatomy;
- decisions, prohibited claims, weighted acceptance rubric, unresolved
  questions, state, and lock SHA-256.

State rules:

| State | Allowed output |
|---|---|
| `Draft` | validation findings and structured questions |
| `NeedsDiscussion` | validation findings and structured questions |
| `Locked` | formal planning only when the digest matches and no question remains |

Do not create a placeholder PPTX to make an incomplete request look finished.
Do not infer rights, decisions, sources, results, customer facts, or academic
claims.

Commands:

```bash
python scripts/manage_window_pptx_project_brief.py validate \
  --input project-brief.json
python scripts/manage_window_pptx_project_brief.py lock \
  --input project-brief.json \
  --output project-brief.locked.json
python scripts/manage_window_pptx_project_brief.py formal-check \
  --input project-brief.locked.json
```

## Realistic corpus

`scripts/window_pptx/project_brief_corpus.py` deterministically builds fifteen
locked scenarios:

- annual work report;
- campus competition defense;
- academic thesis defense;
- business/operations review;
- project proposal;
- product launch;
- market analysis;
- sales proposal;
- investor pitch;
- strategy planning;
- data analysis report;
- training course;
- brand/company introduction;
- project kickoff;
- ecommerce marketing plan.

The three flagships retain all accepted metrics and limitations. The twelve
skeletons each contain at least eight quantitative facts, three required
material roles, real audience and decision context, timing, slide budget,
anatomy, prohibitions, and rubric.

Export:

```bash
python scripts/export_window_pptx_brief_corpus.py \
  --output-dir /tmp/window-pptx-v6-briefs
```

Business and campus facts are standardized synthetic evaluation inputs.
Academic public dataset metadata points to the DCRNN source. All MDGFormer
comparison, variance, ablation, robustness, parameter, and inference values
point to `synthetic://mdgformer/experiment-log-v1`; never present them as
published results.

## Authoring-model authority

Codex GPT-5.5 medium is the v6.0 default author, or the controller may choose
an explicitly equivalent capable model. The model receives:

- the exact locked pack and allowed fact/source IDs;
- project archetype and required deck anatomy;
- certified template candidates with thumbnails and semantic metadata;
- registered page roles, components, capacity, design tokens, and normalized
  grid relationships;
- explicit prohibited claims and the acceptance rubric.

The model returns only constrained narrative grouping, registered candidate
selection, component bindings, and normalized relationships. Reject:

- unknown registry or template IDs;
- arbitrary coordinates, fonts, colors, or effects;
- OOXML, HTML, CSS, JavaScript, Python, VBA, macros, or COM calls;
- unsupported facts, citations, comparisons, causal claims, or rights;
- slide counts or anatomy that contradict the lock;
- model-authored QA scores or release decisions.

The authoring model must not be one of the final blind reviewers.

## Complete-deck anatomy and rhythm

Every formal deck includes:

1. cover;
2. directory;
3. required section dividers;
4. evidence body;
5. decision or conclusion;
6. closing;
7. appendix.

The selected complete-work visual spine owns theme, motif, grid, typography,
imagery language, chart/table language, section rhythm, and bookends. Certified
supplemental pages may fill missing semantic roles only when style-cluster and
dependency-closure checks pass.

Do not repeat one layout mechanically. Do not vary layouts randomly. Use
purposeful cadence:

- peak: cover, decisive section openers, major conclusions;
- flow: ordinary evidence and explanatory pages;
- pause: directory, transitions, quotes, limitations;
- peak: decision and closing.

Continuous pages vary family, scale, dominant region, and visual density while
keeping tokens and motif coherent.

## Private library and rights

Local commercial originals, quarantine content, credentials, and acquisition
state live under `.private/`. This tree is ignored.

Before authenticated acquisition:

1. confirm the old exposed session has been revoked;
2. receive a new short-lived credential only through the private path;
3. never place credential values in chat, command arguments, stdout/stderr,
   manifests, screenshots, or commits;
4. record entitlement and allowed use per artifact;
5. quarantine macros, OLE, ActiveX, external relationships, path traversal,
   and unsupported archives;
6. never redistribute or commit originals by default.

Run the staged guard before every commit:

```bash
python scripts/check_window_pptx_private_assets.py --staged --repo-root .
```

The Phase 37 manager is dry-run-first:

```bash
python scripts/manage_window_pptx_library.py query \
  --private-root .private \
  --scenario annual-work-report
```

`discover|sync|ingest|certify|query` return versioned JSON manifests.
Credential input is a path below `.private/`, never a raw value. Cross-host
redirects strip authorization before following; non-allowlisted hosts are
rejected. Passive ingest never extracts or executes a package. Catalog v3
deduplicates by SHA-256, closes certified dependencies, preserves legacy
quarantine, and fails closed on missing rights or unsafe content.
Certification requires an `ACCEPT` quarantine report plus a matching allowed
RightsRecord, with both recorded as evidence digests. The public metadata seed
stays `unverified`; explicit inventory may include it, but automatic generation
selection may not.

## Native output and backend boundary

Portable native-editable PPTX is canonical. Text, shapes, charts, tables,
diagrams, notes, links, and declared image replacements remain editable.

COM is optional:

- explicit physical-template operations that the portable adapter cannot do;
- macro/template formats;
- native grouping or animation;
- documented add-in calls;
- read-only sampled compatibility certification.

HTML is proof-only. Neither model-authored HTML nor HTML-to-slide conversion is
the canonical source.

## QA and repair budget

Generation never ends at first save. Inspect overflow, minimum font size,
page bounds, overlap, alignment, margins, density, image crop/aspect ratio,
chart-label readability, page repetition, style continuity, heading hierarchy,
orphan/widow text, placeholder content, package readability, editability,
font compatibility, source integrity, and rendered PNGs.

The v6 repair budget is:

1. one deterministic local correction;
2. one same-family certified layout reselection;
3. one constrained authoring-model replan.

Each pass must be monotonic, fact-safe, art-direction-safe, hash-recorded, and
capped. Repeated, non-improving, content-changing, or still-broken candidates
fail; they are not endlessly decorated with extra components.

## AI-only blind acceptance

Three fresh visual-capable contexts receive anonymous hash-bound packets with
the reference, generated PPTX, full-resolution PNGs, contact sheet, rubric, and
no generator trace or other score.

Preflight requires each reviewer to demonstrate image loading. Unavailable or
image-incapable reviewers make the round `NOT_RUN`; there is no two-reviewer
fallback. Release requires:

- at least two of three reference-parity passes;
- overall mean at least `4.3`;
- every dimension aggregate at least `4.1`;
- every flagship at least `4.2`;
- zero same-slide same-issue Blocker/Important consensus from two reviewers.

No human score or override is part of v6. A code-only DeepSeek review is useful
for schemas, rules, and implementation but never substitutes for pixel review.
Until the v6 validator and three fresh packets exist, report `NOT_RUN`, not GO.
