# v6.1 Agent Workflow: Brief to Physical Template Assembly

This reference is the executable contract for a medium/high-capability Agent.
`SKILL.md` stays short; load this file when the user asks for a complete PPTX
from a requirement folder or when certified private templates are available.

## Operating state machine

The Agent must move through these states in order and persist one JSON artifact
per state under `<project>/.window-pptx/audits/`:

```text
INTAKE
  -> DISCUSSION_REQUIRED (questions only)
  -> LOCKED_BRIEF
  -> ART_DIRECTION_LOCKED
  -> NARRATIVE_LOCKED
  -> TEMPLATE_PLAN_LOCKED
  -> PHYSICAL_ASSEMBLY
  -> RULE_QA
  -> VISUAL_HARNESS
  -> RELEASED
```

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

After the brief is locked, select a registered theme and write
`direction-decision.json` containing:

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
python scripts/manage_window_pptx_v61_library.py compile-pages \
  --private-root <private-root> \
  --output <private-root>/v61/library-v4.json
```

Retrieve candidates for each slide, never for the deck as one undifferentiated
query:

```bash
python scripts/manage_window_pptx_v61_library.py query-pages \
  --library <private-root>/v61/library-v4.json \
  --role content-blocks \
  --capacity-budget 1200 \
  --semantic-category 表格图表 \
  --limit 6
```

The query score is deterministic: role 0.30, capacity 0.25, semantic fit
0.20, style 0.15, editability 0.10. The Agent may return only the chosen
`page_id`, facts/assets bindings, confidence, and a short reason. It must not
return geometry, raw colors/fonts, OOXML, HTML/CSS, or executable code.

Each selected template record must preserve:

- `page_id`, `package_sha256`, `source_sha256`, source path, slide number;
- role, category, style cluster, deck family, palette, capacity, editability;
- `slot_graph.text_slot_ids` and the binding chosen for each slot.

For the supplied work-summary reference family, source ordinal is not target
ordinal. Slides 3, 4, 10 and 13 are chapter/divider pages; slides 5, 6, 8 and
9 is a KPI dashboard; slide 7 is a table; slide 8 is a case-study/project
page; slide 11 is people; slide 12 is content-blocks; slide 14 is process;
slide 15 is closing. A target evidence
slide must never select page 4 merely because it is the fourth source page.
It is valid to reuse a certified page non-adjacently when the target narrative
has more roles than the source family, but record the reason and keep the
dominant style cluster locked.

The Agent must bind title/headline/body copy to the selected page's actual slot
IDs. It must not assume `shape_9` or any other shape number across packages.
For the locked Phase 49 acceptance scenario, all 15 `page_id` values must be
distinct; there is no duplicate-page exception. A later scenario may declare
a different reuse policy only in its own locked brief and acceptance schema.
Bindings are complete, not sparse: the JSON object must contain exactly every
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

The assembly plan references an external locked fact store and asset manifest
using project-relative paths and SHA-256 values. Those files, not Agent-authored
plan text, define the allowed IDs and renderings. Empty refs are valid only for
copy listed in the locked connective-copy allowlist. Use empty `text` with an
authorized connective entry to intentionally clear a decorative/source slot.
A page with no editable text slots is not eligible for a content slide. The
query response exposes `slot_graph.slots` and deterministic residue/eligibility
evidence; reject or replace candidates with named brands, product claims, or
unrelated source copy rather than hoping a later visual review will catch it.

## Asset manifest

Every asset is a record, not an untracked file:

```json
{
  "id": "asset-07-kpi-dashboard",
  "role": "quarterly-kpi-dashboard",
  "locator": "data/kpi-dashboard.csv",
  "source_id": "client-source",
  "rights": "client-provided",
  "sha256": "...",
  "used_on": [8],
  "crop_policy": "contain",
  "editable": true
}
```

Private commercial originals remain under `.private/`, ignored by Git, and
are addressed by digest/page ID only. The clean client folder contains no
private bytes, previews, cookies, or historical output. A missing asset uses a
declared safe fallback (theme hero, neutral vector, or empty slot), never a
random web image or a placeholder string.

## Assembly and QA

Create an `assembly-plan.v1` with one `target_slides` item per narrative slide,
plus locked `fact_store` and `asset_manifest` path/digest authorities. The
production assembler resolves those paths only inside the clean project root,
rejects symlinks and path escape, verifies their hashes, and fails on unknown,
unused, or unbound references before any PPTX mutation.
Then run:

```bash
python scripts/render_window_pptx_assembly.py \
  --private-root <private-root> \
  --library <private-root>/v61/library-v4.json \
  --assembly-plan <project>/.window-pptx/audits/assembly-plan.json \
  --output <project>/output/final.pptx \
  --report <project>/.window-pptx/audits/physical-assembly-report.json
```

The physical report must show: every slide has a source page ID and source
hash, every relationship resolves, content types cover every media extension,
`python-pptx` opens the deck, native text/shapes remain editable, the dominant
style cluster is respected, and the output hash is recorded.

Rule QA runs before any visual score is considered:

```bash
python scripts/qa_window_pptx_physical.py \
  --pptx <project>/output/final.pptx \
  --assembly-plan <project>/.window-pptx/audits/assembly-plan.json \
  --library <private-root>/v61/library-v4.json \
  --report <project>/.window-pptx/audits/rule-qa.json
```

The command is a release gate. It fails on placeholder or named-brand/source
residue, out-of-bounds shapes, unreadable text below 8 pt, malformed output,
or a slide-count mismatch. Warnings (for example a surviving decorative source
label or text below 11 pt) are retained for the independent visual reviewer.
The rule engine is intentionally not a visual-quality substitute.

- slide count, required roles, and title presence;
- text overflow/underflow, tiny text, overlap, out-of-bounds geometry;
- safe margins, alignment, image aspect ratio, chart-label readability;
- repeated-family run, density floor/ceiling, color/font consistency;
- unresolved relationships, missing fonts, unsupported OLE/macro/file links;
- no full-slide bitmap substitution.

Visual harness then renders every slide through an isolated LibreOffice/Poppler
proof path and sends the resulting contact sheets to fresh blind reviewers.
The authoring Agent cannot score or release its own deck. A failed rule gets a
bounded repair (slot text reflow, page replacement, or declared safe fallback);
repeated non-improving repairs stop with `NEEDS_REPLAN`.

## Release contract

Release only when all required rows are `PASS`: locked brief, art direction,
narrative, physical lineage, OPC/editability, deterministic QA, visual harness,
and output policy. COM is optional read-only certification after portable PASS;
it is never a prerequisite for ordinary `.pptx` generation.
