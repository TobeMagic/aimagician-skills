# v6.1 Agent Workflow: Brief to Physical Template Assembly

This reference is the executable contract for a medium/high-capability Agent.
`SKILL.md` stays short; load this file when the user asks for a complete PPTX
from a requirement folder or when certified private templates are available.

For the Phase 49 work-report acceptance, the author is Codex
`gpt-5.6-terra` with medium reasoning. It must select the
`reference-work-summary` certified package and produce the exact physical
sequence `target N -> source slide N` for `N=1..15`. All selections share one
package SHA; all page IDs and query IDs are distinct. The profile forbids
native generated-layout/PptxGenJS fallback, non-adjacent substitution,
screenshots, whole-slide rasterization, blank pages, and duplicate physical
pages.

Codex may decide only the fact-safe narrative, the candidate ID selected from
each locked query result, and bindings to certified ordinary/governed slots.
It does not own art direction, geometry, raw colors/fonts, masters/layouts,
OOXML, executable design code, repair code, scoring, approval, or release.

## Operating state machine

The authoring Agent must move through these states in order. Persist artifacts
under the evidence directory named by the locked client contract; use
`<project>/.window-pptx/audits/` only when no path was specified:

```text
INTAKE
  -> DISCUSSION_REQUIRED (questions only)
  -> LOCKED_BRIEF
  -> ART_DIRECTION_LOCKED
  -> NARRATIVE_LOCKED
  -> TEMPLATE_PLAN_LOCKED
  -> PHYSICAL_ASSEMBLY
  -> RULE_QA
  -> CANDIDATE_READY_FOR_BLIND_REVIEW
```

The authoring Agent stops there. A fresh isolated harness, not the author,
owns `VISUAL_HARNESS -> RELEASED`; it receives a hash-bound render packet and
must not receive the author conversation, self-scores, or prior reviewer
results.

`INTAKE` may inspect `REQUEST.md`, `MODULES.md`, `SLIDE-MAP.md`, data files,
and assets. If any required authority is missing, the Agent emits a bounded
question list and does not create a candidate deck. The user can answer in
chat or update the project folder. A brief becomes `LOCKED` only when audience,
decision, timing, slide budget, anatomy, facts, sources, assets/rights,
brand constraints, output path, overwrite policy, macro/add-in policy, and
acceptance rubric are explicit.

## Discussion contract

Ask in this order, keeping questions grouped so a client can answer them in
one pass:

1. audience, meeting, decision, deadline, and presentation duration;
2. source-of-truth facts, claims that must not change, and missing data;
3. required anatomy and slide budget (cover, directory, section dividers,
   evidence, decision, closing, appendix);
4. brand colors, forbidden colors, fonts, logo, tone, density, and examples;
5. asset roles, crop/orientation requirements, rights, and whether generated
   imagery is allowed;
6. output path, native editability, speaker notes, PDF, macros, add-ins, and
   PowerPoint certification policy;
7. acceptance thresholds and who can approve the final deck.

Never invent a fact, source, customer name, citation, brand token, or asset
right to clear the gate. State `NEEDS_DISCUSSION` when the answer is absent.

## Art direction and macro narrative

After the brief is locked, write `direction-decision.json`. For Phase 49 this
file records the design system extracted from the certified reference package;
Codex does not choose a new theme or override its tokens. Record:

- dominant background, primary text, accent, data-positive, data-negative,
  and neutral colors;
- title/body/label type roles and approved fallback fonts;
- 12-column grid, safe margins, spacing scale, corner radius, stroke and
  shadow policy;
- image crop and icon language; chart palette and label rules;
- density target and maximum consecutive body-family run;
- forbidden treatments (tiny labels, unlicensed imagery, 3D charts,
  decorative collisions, mixed icon languages).

Write a `narrative-plan.json` before selecting physical pages. The plan must
contain one sentence per slide answering “what should the audience remember”
and one evidence or decision action. Use the semantic role mapping below:

| Content signal | Preferred page role |
| --- | --- |
| title/identity | `cover` |
| agenda/route | `contents` |
| chapter transition | `section` |
| trend/metric | `data`, `content-blocks`, or `supporting-asset` |
| sequence/implementation | `process` or `timeline` |
| team/person | `people` |
| comparison | `content-blocks` with explicit before/after binding |
| conclusion/action | `roadmap`, `statement`, or `closing` |

Do not select pages randomly. Vary rhythm by role, density, and hero interval;
keep one dominant style cluster for the whole deck.

## Physical template retrieval

Compile the private catalog once per source fingerprint:

```bash
python <skill-root>/scripts/manage_window_pptx_v61_library.py compile-pages \
  --private-root <private-root> \
  --output <private-root>/v61/library-v4.json
```

When a bundled certified complete-work family is a materially closer match
than page-level assembly, compile that family into a separate private index;
do not copy its PPTX into the client project. The Phase 49 annual-work-report
family is prepared with:

```bash
python <skill-root>/scripts/manage_window_pptx_v61_library.py compile-reference \
  --private-root <private-root> \
  --deck <skill-root>/design-packs/institutional-annual-editorial/template.pptx \
  --output v61/reference-work-summary-library-v4.json
```

Keep both indexes. Use whole-family reuse only when its role coverage, content
capacity, asset requirements, and art direction fit the locked brief; otherwise
query the general certified core page by page. Phase 49 has already locked the
whole-family decision: use only
`v61/reference-work-summary-library-v4.json`; the general core cannot fill a
missing page.

Retrieve candidates for each slide, never for the deck as one undifferentiated
query:

```bash
python <skill-root>/scripts/manage_window_pptx_v61_library.py query-pages \
  --private-root <private-root> \
  --library v61/library-v4.json \
  --role content-blocks \
  --capacity-budget 120 \
  --semantic-category 表格图表 \
  --limit 6
```

For production, persist all ordinal-specific requests and redacted results as
one immutable bundle rather than copying terminal output:

```bash
python <skill-root>/scripts/manage_window_pptx_v61_library.py query-bundle \
  --private-root <private-root> \
  --library v61/reference-work-summary-library-v4.json \
  --query-request <project>/evidence/page-template-query-request.v1.json \
  --output <project>/evidence/page-template-query-bundle.v1.json
```

The assembly plan includes that bundle's project-relative path and SHA-256.
Each slide's `selection` records the query ID, candidate rank, exact total
score, reason, and fallback reason. At render time the Skill reruns all fifteen
queries against the hash-locked index and rejects any changed order, score,
eligibility decision, candidate identity, page/package/source-slide digest, or
fallback evidence.

The query score is deterministic: role 0.30, capacity 0.25, semantic fit
0.20, style 0.15, editability 0.10. The Agent may return only the chosen
`page_id`, fact/asset bindings, and a short selection reason. It must not
return geometry, raw colors/fonts, OOXML, HTML/CSS, executable code, a score,
or a release judgment.

The JSON wrapper is nested: eligibility and scoring are at
`candidates[i]`, while page lineage/capacity/slots are under
`candidates[i].page_template`. Production rules are:

- never pass `--include-ineligible`;
- set `--capacity-budget` to the planned visible character count (`0` skips
  the gate and is forbidden after the narrative is locked);
- first query the exact role and locked `--style-cluster` without
  `--allow-fallback`;
- outside Phase 49 only, retry with `--allow-fallback` when no exact-role
  candidate exists;
- accept only `eligibility=true`; every fallback needs a non-empty
  `fallback_reason` and a registered compatible cluster;
- use `--asset-requirement image` only when the locked asset manifest contains
  a usable client image; otherwise require image-free candidates;
- copy the query wrapper's `library_index_sha256` unchanged into the assembly
  plan.

Phase 49 permits no query fallback: every ordinal must return and select its
exact direct-use certified reference page.

In v6.1, `--semantic-category` is certified category matching, not Agnes
natural-language or visual-semantic retrieval. Agnes Deck→Page→Region indexing
belongs to the next milestone and must not be implied here.

The private assembler-side library record must preserve:

- `page_id`, `package_sha256`, `source_sha256`, source path, slide number;
- role, category, style cluster, deck family, palette, capacity, editability;
- `slot_graph.text_slot_ids` and the binding chosen for each slot.

The Agent-facing query result deliberately replaces the private source path
with a `private://<package-sha>/slide-NNN` locator and blanks literal source
copy. The Agent persists only the public query evidence; the assembler resolves
the actual private locator from the locked library index.

Phase 49 uses this exact N-to-N sequence. `source slide` must equal `target`,
and every row must come from the same certified package SHA:

| Target | Source slide | Template role | Narrative role |
| ---: | ---: | --- | --- |
| 1 | 1 | `cover` | `cover` |
| 2 | 2 | `contents` | `contents` |
| 3 | 3 | `section` | `section-governance` |
| 4 | 4 | `section` | `policy-evidence` |
| 5 | 5 | `data` | `revenue-composition` |
| 6 | 6 | `data` | `medical-revenue-comparison` |
| 7 | 7 | `table` | `expenditure-table` |
| 8 | 8 | `case-study` | `projects-debt` |
| 9 | 9 | `kpi` | `kpi-dashboard` |
| 10 | 10 | `section` | `section-innovation` |
| 11 | 11 | `people` | `team` |
| 12 | 12 | `content-blocks` | `efficiency-comparison` |
| 13 | 13 | `section` | `section-roadmap` |
| 14 | 14 | `process` | `roadmap` |
| 15 | 15 | `closing` | `closing` |

The assembler validates all four columns. A semantically similar page from the
general core is still a Phase 49 failure. Non-adjacent certified selection is
available only to a different v6.1 profile whose locked brief and acceptance
schema explicitly allow it.

The Agent must bind title/headline/body copy to the selected page's actual slot
IDs. It must not assume `shape_9` or any other shape number across packages.
For the locked Phase 49 acceptance scenario, all 15 `page_id` and query ID
values must be distinct; there is no duplicate-page or source-ordinal
exception. A later scenario may declare a different reuse policy only in its
own locked brief and acceptance schema.
Query results deliberately redact the private source path and literal source
copy. Bindings are complete, not sparse: the JSON object must contain exactly every
ID in `slot_graph.text_slot_ids`. Every value is an object containing `text`,
`fact_refs`, and `asset_refs`, for example:

```json
{
  "shape_17": {
    "text": "门诊收入同比增长 8.4%",
    "fact_refs": ["fact-finance-017"],
    "asset_refs": []
  }
}
```

When `slot_graph.fragment_groups` is non-empty, fill a group as one governed
phrase rather than validating its characters independently. Membership comes
from the locked group's `slot_ids`; order comes from the corresponding locked
slots' contiguous `group_order` values. Every non-empty one-character member
uses the same sole FactStore record, and their ordered concatenation must be an
exact or whitespace-normalized complete registered rendering of that fact.
Empty remainder members require `connective-clear`. Arbitrary substrings,
reordered/repeated characters, report-authored group metadata, and `character`
mode outside a locked group fail before mutation and again during independent
validation of the final PPTX.

### Governed embedded content

`slot_graph` covers ordinary `p:sp` text only. Before a page can be
direct-use eligible, the compiler must also finish
`governed_content_inventory` for every customer-visible surface in its OPC
closure:

- native `table-cell` content on the slide;
- chart cache `chart-value` and `chart-text` nodes;
- effective `workbook-cell` values in embedded XLSX parts;
- notes, comments, and diagram text;
- tag-part metadata, cached layout/master fields, and retained media hashes.

Every governed content record has a stable slot ID, source part, deterministic
locator, source-text SHA-256, value type, and optional `peer_group_id`. The
public query copy blanks literal `source_text`; it exposes only the metadata
needed to bind safely, such as semantic role, series/point index, worksheet
ordinal/cell reference, and value type. The private library remains the sole
source of the original locator and bytes.

A chart/workbook peer is structural, never guessed by matching displayed
values. The compiler accepts only a supported one-dimensional A1 reference in
the chart's `c:f`, maps `c:pt/@idx` to the exact worksheet cell, and emits a
peer only when one chart value and one workbook cell form an unambiguous pair.
Bind that `peer_group_id` once; the assembler applies one fact-authorized value
to both chart cache and XLSX cell and rejects disagreement. An unpaired
workbook cell and every table cell use their own governed slot ID.

An embedded XLSX is itself an untrusted nested OPC package. Before it may be
copied, the assembler requires the certified passive workbook subset and
rejects macros or `.xlsm`, OLE/ActiveX or other active content, external or
unresolved relationships, formulas, and unsupported parts. It strips workbook
metadata, calculation chains, and table definitions, then deterministically
rebuilds shared strings from still-referenced authorized cells. Replaced,
ungoverned, whitespace-only, or otherwise unauthorized source strings must not
remain in the sanitized package.

Governed bindings use the same locked object as ordinary text:

```json
{
  "peer_0123456789abcdef01234567": {
    "text": "45063.1",
    "fact_refs": ["fact-medical-revenue-2025"],
    "asset_refs": []
  },
  "table_cell_0123456789abcdef01234567": {
    "text": "预算执行率 97.2%",
    "fact_refs": ["fact-budget-execution"],
    "asset_refs": []
  }
}
```

Every inventoried value must produce passing binding evidence. It may be
explicitly bound as above or deterministically retained only when exactly one
locked FactStore rendering or connective-copy entry authorizes the source
value. Unknown, ambiguous, drifted, partially covered, or conflicting peers
fail before output promotion. Layout/master field caches are validated against
their inventory and cleared; source tag parts and tag relationships are
removed rather than copied.

After mutation, the renderer writes one final governed-mutation record per
target, including slide ordinal, page/slot identity, kind, target part,
deterministic locator, peer group when present, and the digest of the final
value. Chart/workbook records also bind the final slide part, frame shape ID,
slide chart rId, chart part, chart package rId, XLSX part, and target-part
SHA-256. These fields are derived by following the final relationship graph;
they are never copied from the plan or import map. The report binds the
ordered records with a mutation-manifest SHA-256;
the independent verifier recomputes that manifest and rereads final table,
chart, and XLSX values rather than trusting author-stage counters.

The assembly plan references an external locked FactStore, asset manifest, and
connective-copy authority using project-relative paths and SHA-256 values. It
also references the public query bundle by project-relative path and SHA-256.
Those files, not Agent-authored plan text, define the allowed candidates, IDs,
and renderings. A FactStore record may carry trusted `allowed_renderings`; an
unregistered substring is never inferred as valid. Empty refs are valid only
for exact text in the locked connective-copy authority. To clear a source
slot, use empty `text` only when that authority explicitly contains one unique
entry whose `text` is `""`. Retaining unchanged source text is governed by the
same rule and is rejected unless that exact text is registered connective copy.
A page with no editable text slots is not eligible for a content slide. The
query response exposes `slot_graph.slots` and deterministic residue/eligibility
evidence; reject or replace candidates with named brands, product claims, or
unrelated source copy rather than hoping a later visual review will catch it.

## Asset manifest

Every asset is a record, not an untracked file:

```json
{
  "schema_version": "1.0",
  "bindings": {
    "asset-07-dashboard": {
      "path": "assets/dashboard.png",
      "sha256": "<lowercase-sha256>",
      "record": {
        "id": "asset-07-dashboard",
        "kind": "image",
        "quality": 1.0,
        "source": "client",
        "license": "client-provided",
        "retrieved_at": "2026-08-08",
        "width_px": 1920,
        "height_px": 1080
      }
    }
  }
}
```

Private commercial originals remain under `.private/`, ignored by Git, and
are addressed by digest/page ID only. The clean client folder contains no
private bytes, previews, cookies, or historical output. Every asset `path` is
a POSIX path relative to the project root; absolute paths, `..`, and symlink
components are rejected. Outside Phase 49 a profile may declare a certified
asset fallback. Phase 49 has no native or generated fallback: if the exact
N-to-N page requires a customer replacement that the locked manifest cannot
supply, stop with `NEEDS_REPLAN`. If the locked brief has no client imagery, use
`{"schema_version":"1.0","bindings":{}}`, keep every `asset_refs` array empty,
and require all fifteen exact pages to be eligible without a customer-image
replacement. Retained certified decorative media is allowed only at the
inventoried source hash. Phase 49 does not expose picture slot IDs through page
queries, so production picture replacement is deliberately out of scope until
the next catalog version adds certified picture-slot records.

For any later profile that permits a replacement asset, evidence is slot-exact:
the selected slide, shape, certified slot, relationship ID, resolved image
target part, and final bytes hash must all match the locked asset manifest. A
correct image elsewhere in the package does not satisfy that binding.

## Assembly and QA

Create an `assembly-plan.v1` with one `target_slides` item per narrative slide,
plus a locked query-bundle path/digest and locked `fact_store`,
`asset_manifest`, and `connective_copy` path/digest authorities. Every target
slide carries its locked selection evidence. The production assembler resolves
those paths only inside the clean project root, rejects symlinks and path
escape, verifies their hashes, recomputes query results, and fails on unknown,
unused, unbound, or drifted references before any PPTX mutation.
Then run:

```bash
python <skill-root>/scripts/render_window_pptx_assembly.py \
  --project-root <project> \
  --private-root <private-root> \
  --library v61/reference-work-summary-library-v4.json \
  --assembly-plan evidence/assembly-plan.v1.json \
  --fact-store fact-store.v1.json \
  --fact-store-sha256 <locked-sha256> \
  --asset-manifest asset-manifest.v1.json \
  --asset-manifest-sha256 <locked-sha256> \
  --connective-copy connective-copy.v1.json \
  --connective-copy-sha256 <locked-sha256> \
  --output output/final.pptx \
  --report evidence/physical-assembly-report.v1.json \
  --rule-qa-report evidence/rule-qa.v1.json \
  --acceptance-profile phase49-work-report-15 \
  --max-output-size-bytes 33941179
```

All paths above except `--private-root` and an absolute explicit library are
project-relative. A relative library is resolved under the private root and
is rejected if it resolves inside the clean client folder. The standalone
renderer is the canonical v6.1 production path.

The physical report must show: exactly fifteen ordinal-aligned lineage records,
fifteen distinct page/query IDs from one package, locked query and content
authority PASS, every relationship resolves, content types cover every media
extension, `python-pptx` opens the deck, native text/shapes/charts/tables remain
editable, the reference style cluster is respected, LibreOffice opens/renders,
the size cap passes, and the output hash is recorded.

The independent validator must derive these claims again from the query bundle
and final PPTX. Report-authored counts, paths, locators, and target hashes are
evidence to compare, not authority. Its implemented independent boundary is:

- schema- and semantics-validate the hash-locked query bundle, anchor each
  selected candidate by lineage ordinal and `page_id`, and require exact
  ordinary-text and governed-slot evidence coverage;
- compare the selected page's shape/native-object/image/chart/table structure
  and certified media authority with the final package;
- reject duplicate or ambiguous evidence, mutation, locator, and archive keys;
- audit the ZIP entry namespace before OOXML parsing: no duplicate,
  noncanonical, case-colliding, directory, encrypted, or symlink entries;
- prove the package root office-document relationship, the single ordered
  presentation slide list, unique numeric slide IDs/rIds, canonical targets,
  exact `slide1..N` parts, and absence of extra slide relationships or parts;
- reopen through `python-pptx`, fail closed if shape access is malformed, and
  independently recompute per-slide text, native-object, picture,
  full-slide-raster, and raster-dominance evidence;
- allow an external relationship only when both its relationship type is the
  registered hyperlink type and its target is a valid credential-free HTTPS
  URL; reject file, script, OLE, macro, and every other external type;
- traverse the final root relationship graph and apply the passive-workbook
  security audit to every reachable `.xlsx`, including undeclared or decoy
  workbooks.

For `phase49-work-report-15`, governed mutation lineage is also locked by the
immutable tuple
`(ordinal, page_id, slot_id, kind, source_part, locator, peer_group_id)`.
There are exactly 101 registered identities, distributed 22/52/27 across
slides 5/6/7, with SHA-256
`12ce0f96e70c84c07d3b70ec9f4a4385949ffc05981ef983ed09648c282353c2`.
Every mutation record therefore includes its certified `source_part`; the
independent validator recomputes the identity digest rather than accepting a
report assertion. A different acceptance profile with governed mutations is
rejected until its immutable inventory is explicitly registered. Do not
weaken this gate to make an unregistered profile pass.

Source-residue and reachability are hard gates, not advisory counters:

- governed expected, bound, and independently verified counts are equal;
- chart/workbook peer groups resolve to identical authoritative values, the
  final governed-mutation records match independently reread table, chart, and
  XLSX values plus the actual slide-to-chart-to-package relationship chain,
  and their ordered manifest has a valid SHA-256;
- inventoried source tag parts/relationships are stripped and zero remain;
- inventoried layout/master fields are sanitized and zero cached values remain;
- every retained certified-media relationship reaches bytes with the certified
  size/hash, and every permitted replacement matches its exact
  slide/shape/slot/rId/target-part binding and locked manifest hash;
- root reachability is recomputed after overrides and relationship-based
  pruning, leaving zero unreachable dependencies and zero orphan media;
- unresolved/unsafe relationships, unauthorized source content, media hash
  mismatches, and static duplicate bytes are all zero.

The canonical renderer runs the implemented rule QA and writes the requested
report. Current hard checks cover ZIP/open validity, exact sequence and slide
count, locked selection/authority evidence, governed-content verification,
placeholder and named-brand/source residue, severe geometry bounds, text below
8 pt, adjacent style lineage, recursive unsafe/unresolved relationships,
reachability/media integrity, per-slide native-object coverage, and full-slide
bitmap substitution. Softer geometry and text below 11 pt remain warnings.
Alignment quality, nuanced overlap and overflow, safe-margin rhythm, image
aesthetics, chart-label legibility, font/color harmony, and overall art
direction are external visual-harness responsibilities in v6.1; do not claim
the rule engine implements them.

After author-stage PASS, an external visual harness renders every slide once
through an isolated LibreOffice/Poppler proof path and sends the hash-bound
contact sheets to fresh blind reviewers. The authoring Agent cannot score or
release its own deck. A failed rule gets a
bounded repair of bindings on the same certified page. Page replacement,
native redraw, or a declared asset/layout fallback breaks the Phase 49 N-to-N
profile and must stop with `NEEDS_REPLAN`.

## Release contract

The author may claim only `CANDIDATE_READY_FOR_BLIND_REVIEW` when locked brief,
art direction, narrative, physical lineage, OPC/editability, deterministic QA,
and output policy pass. Release additionally requires the external visual
harness and independent release decision. COM is optional read-only
certification after portable PASS; it is never a prerequisite for ordinary
`.pptx` generation.

These implemented engineering contracts do not by themselves mean that the
Phase 49 clean-room Codex run, blind visual review, or release acceptance has
passed. Record those results only after their separate hash-bound harnesses
have actually run.
