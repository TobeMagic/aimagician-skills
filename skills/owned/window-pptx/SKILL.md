---
name: window-pptx
description: >
  Plan, generate, inspect, repair, and deliver professional native-editable
  PPTX from a project folder. The default governed path is cross-platform
  PptxGenJS plus OOXML semantic inspection and LibreOffice/Poppler proof;
  Windows PowerPoint COM is an explicit legacy or certification path.


  Use this skill whenever the user asks to create, edit, batch-update,
  reproduce, or polish PowerPoint decks using COM, VBA, pywin32,
  PowerPoint.Application, PptxGenJS, iSlide/OKPlus add-in discovery, or a
  "folder with requirements + PPT/materials" workflow. Also use it when the user wants
  one-to-one PowerPoint implementation from a template, advanced PPT production,
  master-level watermarks, reusable slide modules, design systems,
  award/team/government/technology style layouts, stock image search, Iconify
  icon search/download, template library retrieval/recommendation,
  animation/notes/add-in-aware operations, or anything beyond pure pptx
  libraries. Also use it when a weaker model must generate a professional,
  fact-safe, native-editable business deck through constrained planning,
  governed art direction, semantic layouts, and automatic quality gates.


  This skill has a discuss gate: before executing real deck edits, confirm or
  read from REQUEST.md the project folder, source/template deck, output policy,
  macro/add-in policy, and acceptance check.
compatibility:
  tools:
    - python
    - node
    - npm
    - libreoffice
    - poppler
    - powershell
    - git
  requires: Python 3.11+, Pillow, Node.js 18+, npm, LibreOffice Impress, Poppler or Ghostscript; Windows PowerPoint and pywin32 are optional
category: documents
subcategory: slides
tags:
  - pptx
  - windows
  - automation
---

# Window PPTX Governed Generation

This skill turns governed content plans into professional, native-editable PPTX. Its default delivery path does not require PowerPoint COM:

```text
FactStore -> BriefPlan -> NarrativePlan -> DeckPlan -> RenderPlan
-> DesignPack -> VisualPlan + AssetPlan
-> PptxGenJS or authorized TemplatePack candidate
-> deterministic OOXML -> semantic + reference-complexity hard gates
-> isolated LibreOffice PDF -> Poppler/Ghostscript PNG -> QualityReport v2
-> atomic PPTX promotion
```

Use explicit Windows PowerPoint COM only for a capability the portable backend declares unsupported, or for optional read-only certification after portable PASS:

- unrestricted physical template/source-deck editing; authorized TemplatePack
  slot adaptation is portable and does not require COM
- `.pptm`, `.potx`, or `.potm` workflows
- native shape groups, animation, or PowerPoint-only object-model operations
- add-in discovery and approved plugin operations
- sampled compatibility certification

Never silently fall back from PptxGenJS to COM, drop a requested feature, or rasterize a governed slide. Capability mismatch is a pre-mutation failure.

## Required Discuss Gate

Do not start real PPT editing until these five items are confirmed in chat or present in `REQUEST.md`:

1. Project folder path
2. Whether this is a fresh portable deck or requires physical template/source-deck import
3. Output path and overwrite policy
4. Macro/add-in policy
5. Acceptance check

If the user says to proceed autonomously and `REQUEST.md` already contains enough information, continue using those written assumptions. If anything is missing, ask only the missing items.

## Project Folder Contract

Default folder shape:

```text
ppt-project/
  REQUEST.md
  MODULES.md
  SLIDE-MAP.md
  template.pptx
  assets/
    downloads/
      pixabay/
      iconify/
  data/
  notes/
  output/
  .window-pptx/
    scripts/
    generated_assets/
    exports/
    audits/
    logs/
    cache/
```

Recognize these inputs:

- `REQUEST.md`: primary user requirements
- `MODULES.md`: deck-level module and design-system plan
- `SLIDE-MAP.md`: slide-level role/action map
- `*.pptx`, `*.pptm`, `*.potx`, `*.potm`: templates or source decks
- `assets/` or `images/`: logos, screenshots, photos, icons, backgrounds
- `assets/downloads/pixabay/`: downloaded stock photo/illustration assets
- `assets/downloads/iconify/`: downloaded Iconify SVG icons organized by icon set prefix
- `templates/template-library/reference/`: built-in category PPTX files for template recommendation
- `templates/template-library/template-library-review.xlsx`: reviewed template index and recommendation log
- `data/`: CSV, JSON, Excel, chart data, tables
- `notes/`: speaker notes, outlines, references
- `output/`: generated decks and exports
- `.window-pptx/`: generated scripts, assets, exports, audits, logs, add-in inventory, API search caches

If a physical template is required, first determine whether it is an
authorized, versioned TemplatePack. TemplatePack slot adaptation is portable
OOXML and preserves the source's masters, layouts, images, vector decoration,
native charts, and embedded workbooks. Arbitrary source-deck editing still
requires explicit `--backend com`; `--backend auto` never ignores or
approximates an unregistered template.

Read [project-folder-contract.md](./references/project-folder-contract.md) when you need the full folder and `REQUEST.md` rules.

Read [editable-deliverable-rebuild.md](./references/editable-deliverable-rebuild.md) when a rendered/image version looks good but the final deliverable must remain editable. Do not use a full-slide screenshot as a completed page unless the user explicitly chooses raster output.

## REQUEST.md Template

Use [templates/REQUEST.md](./templates/REQUEST.md) for new projects.

Minimum acceptable sections:

```markdown
# PowerPoint Request

## Goal

## Inputs

## Output

## Edit Requirements

## Visual Constraints

## Preferred Plugins

## Acceptance Check
```

`Preferred Plugins` is optional. Empty means "use the governed portable backend and no plugin".

## Runtime Setup

Install the pinned portable worker once from the skill directory. Do not use an unpinned global PptxGenJS:

```bash
cd skills/owned/window-pptx/scripts/node
npm ci --ignore-scripts --no-audit --no-fund
node window_pptx_worker.mjs --doctor
```

Install Pillow in the Python runtime used by the automation command so real
PNG previews are inspected rather than merely counted:

```bash
python -m pip install Pillow
```

Required daily-proof tools:

```bash
soffice --version
pdfinfo -v
pdftoppm -v
# Ghostscript is an accepted independent rasterizer fallback when Poppler is absent.
gs --version
```

The pinned runtime is PptxGenJS `4.0.1` plus JSZip `3.10.1`. The Skill fingerprints the actual Node/npm, package files, LibreOffice, Poppler, OS, locale, and fonts. Missing or mismatched runtime evidence fails closed.

For optional Windows COM operations, install pywin32 in native Windows Python:

```powershell
py -m pip install pywin32
py path\to\window_pptx_automation.py --project-dir C:\ppt-project --com-doctor --json
```

## Backend Selection Contract

| Requirement | Backend | Verification |
|---|---|---|
| Fresh editable `.pptx`, motion off, no physical template | `auto` → `pptxgenjs` | `portable` |
| Same, plus same-host PowerPoint certification | `pptxgenjs` | `powerpoint` |
| Authorized registered TemplatePack slot adaptation | portable OOXML | hash + slot + chart/workbook + LibreOffice + complexity gates |
| Unregistered physical template/source-deck editing | explicit `com` | legacy COM gates |
| `.pptm` / `.potx` / `.potm`, animation, native grouping | explicit `com` | legacy COM gates |
| HTML preview/debugging | never a backend | optional proof only |

Portable mode supports native editable text, shapes, images, tables, charts, notes, hyperlinks, masters/backgrounds, and six diagram families. Diagrams are editable child shapes with stable logical-group metadata, not SmartArt or native PowerPoint groups.

Unsupported capabilities fail before candidate creation. `auto` never changes to COM implicitly.

## DesignPack, VisualPlan, and TemplatePack

Weak models choose content semantics and a registered business scenario. They
do not invent style, fonts, coordinates, page composition, or asset policy.
The deterministic compiler selects:

```text
scenario -> DesignPack -> page family candidates -> paced variant
-> components -> AssetPlan -> VisualPlan
```

The four built-in DesignPacks are:

- `institutional-annual-editorial`
- `consulting-executive`
- `product-launch-stage`
- `data-research-editorial`

Together they cover all 15 registered commercial archetypes. Each pack defines
theme tokens, font fallbacks, page-family vocabulary, density rhythm,
same-layout repetition limits, hero cadence, asset priority, required visual
anchors, and a capacity-safe fallback. Use:

- `registries/design-packs.json`
- `schemas/design-pack.v1.schema.json`
- `schemas/visual-plan.v1.schema.json`
- `schemas/asset-plan.v1.schema.json`

When the requested art direction matches an authorized template, select a
TemplatePack instead of rebuilding the design from raw coordinates. A
TemplatePack is valid only when its source SHA-256 matches the manifest and
every change targets a declared stable shape or chart slot. Unbound OOXML parts
must remain byte-identical. Editable chart changes must update both chart
caches and the corresponding embedded XLSX.

Portable TemplatePack example:

```bash
python scripts/window_pptx_automation.py \
  --project-dir /path/to/ppt-project \
  --render-template-pack \
  --template-pack institutional-work-summary-v1 \
  --template-bindings bindings.json \
  --output output/final.pptx \
  --export-pdf \
  --json
```

Template bindings are complete, schema-bounded, and capacity-checked before
mutation. A newline inside a binding separates existing rich-text runs; it
does not invent a paragraph or arbitrary line break. The adapter writes a new
candidate atomically and never changes the authorized source template.

The reference-grade structural gate rejects sparse but technically valid
decks. For the institutional work-summary profile it checks average visual
objects per slide, layout-signature variation, media count/bytes, editable
charts, grouped/vector composition, and decorative primitives. This gate is in
addition to rendered PNG checks; it cannot be replaced by open-file success.
The generated route uses a separate media-agnostic floor for average editable
objects, distinct page compositions, and rich-slide coverage. Its compiler
adds a deterministic editable editorial layer to the authoritative RenderPlan,
so old 3–4-object text/card decks fail instead of receiving a false pass.

Read [reference-grade-template-workflow.md](./references/reference-grade-template-workflow.md)
for authorization, binding, chart editability, font portability, and quality
evidence rules.

## Optional WSL to Windows Certification Bridge

Generate and verify the daily candidate inside WSL/Linux first. WSL may then launch native Windows Python for optional certification of that exact hash-bound candidate.

Valid bridge pattern from WSL:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
  "python 'D:\Growth_up_youth\repo\skills\skills\owned\window-pptx\scripts\window_pptx_automation.py' --project-dir 'D:\ppt-project' --certify-pptx 'output\final.pptx' --portable-verification-report '.window-pptx\audits\portable-verification.json' --json"
```

What this means:

- WSL may perform the full portable generation and daily QA.
- Windows `powershell.exe` runs the command.
- Windows `python.exe` imports `win32com.client`.
- PowerPoint certification runs inside the logged-in Windows desktop session.
- Paths passed to the script must be Windows paths such as `D:\...`, not `/mnt/d/...`.

Before optional certification, verify the Windows runtime:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
  "python -c \"import sys, win32com.client; print(sys.executable); print('pywin32 ok')\""
```

Known bridge caveats:

- PowerShell stdout redirection may produce UTF-16 files; prefer scripts that write UTF-8 JSON directly.
- Chinese paths may display mojibake in terminal output even when file access is correct.
- `py` launcher may be absent; use `python` if Windows Python is on PATH.
- PowerPoint must be installed and available in the current interactive Windows desktop session.
- Portable generation is suitable for headless WSL/Linux; PowerPoint certification is not.
- WSL and Windows have different Python packages, PATH, environment variables, and current directories.
- File locks can occur if PowerPoint keeps a deck open; close presentations in `finally` blocks.

## Bundled Helper Script

Prefer the bundled helper script for governed compile/render/check operations. The default render backend and verification level are `auto` and `portable`.

```bash
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py \
  --project-dir /path/to/ppt-project \
  --deck-plan deck-plan.json \
  --render-deck-plan \
  --output output/final.pptx \
  --export-pdf \
  --json
```

Initialize a new project workspace with stable review folders and planning files:

```powershell
py ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --init-project `
  --no-save
```

This creates:

- `REQUEST.md`
- `SLIDE-MAP.md`
- `.window-pptx/media/`
- `.window-pptx/scripts/`
- `.window-pptx/generated_assets/`
- `.window-pptx/exports/`
- `.window-pptx/audits/`
- `.window-pptx/temp/`
- `.window-pptx/logs/`

Inspect iSlide / OKPlus registration safely without starting PowerPoint or loading add-in code:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --probe-plugin-apis `
  --plugin-progid iSlideTools.Public `
  --plugin-progid Slibe.OKPlus `
  --no-save `
  --json
```

If optional PowerPoint COM starts failing, diagnose registration before clearing generated wrappers:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --com-doctor `
  --json
```

`--com-doctor` is read-only and never edits the registry. The old request-summary, watermark, template-intake, animation, and add-in routes remain explicit COM operations.

For a real one-to-one physical-template edit, generate a project-specific Python COM script under `.window-pptx/`, select `--backend com`, and use the helper as the base for ownership, macro security, open/save/export, and cleanup.

## Governed BriefPlan Mode (Default for New Weak-Model Decks)

For a new deck, default to the strict authority chain:

```text
trusted materials -> FactStore -> BriefPlan -> NarrativePlan -> DeckPlan
-> DirectionDecision -> RenderPlan -> QualityReport v2 -> PPTX candidate
```

The weak model writes only BriefPlan fact references and registered semantic hints. It does not restate trusted facts or choose titles, coordinates, fonts, colors, layout IDs, templates, code, macros, or COM calls. Use:

- `schemas/fact-store.v1.schema.json`
- `schemas/brief-plan.v1.schema.json`
- `schemas/narrative-plan.v1.schema.json`
- `schemas/brand-spec.v1.schema.json`
- `schemas/direction-decision.v1.schema.json`
- `schemas/quality-report.v2.schema.json`
- `schemas/design-pack.v1.schema.json`
- `schemas/visual-plan.v1.schema.json`
- `schemas/asset-plan.v1.schema.json`

Compile without PowerPoint:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --fact-store facts.json `
  --brief-plan brief.json `
  --compile-brief-plan `
  --no-output-deck `
  --json
```

For a direction review, use `--render-brief-plan --direction-mode interactive`; this returns safe/editorial/expressive candidates and stops before rendering or file writes. Rerun with `--direction-mode locked --direction-id <registered-id>` or allow the deterministic `auto` safe-default policy.

Render through the native-object transaction:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --fact-store facts.json `
  --brief-plan brief.json `
  --render-brief-plan `
  --backend auto `
  --verification portable `
  --output output\final.pptx `
  --export-qa `
  --json
```

This route writes a candidate only, normalizes ZIP/core timestamps, validates OOXML relationships/content types/page geometry/object identity/text/style/native chart-table-diagram data/notes/links/masters, and renders a copy through isolated LibreOffice plus Poppler. Missing proof, truncated/duplicate/placeholder text, deterministic capacity overflow, near-empty pages, or adjacent near-duplicate pages stops the transaction. Only then are the PPTX, optional PDF, reports, verification manifest, and proof directory promoted as one rollback-capable bundle. `generation-manifest.json` binds the normalized BrandSpec content/source/hash, installed-font inventory/digest, and normalized asset-manifest content/source/hash. `portable-verification.json`, `ooxml-report.json`, PDF/PNGs, QualityReport v2, and SHA-256 evidence remain under `.window-pptx/audits/`. Use `--brand-spec` only with this BriefPlan render route; the direct DeckPlan route rejects it instead of silently ignoring brand requirements.

The portable visual floor is also deterministic: role-aware cover/agenda/content/closing layouts, a capacity-checked 44/32/22/18 pt title ladder, muted footers, capacity-sized KPI typography, exact five/six-card agendas, rebalanced agenda continuations, theme-derived chart/table styling, and automatic rejection of unbound empty decoration frames. Plain focal claims use an editable editorial statement plus a narrow governed rail instead of fake quotation styling or a blank image-like color block; three short authored labels use compact cards; a single dated event uses a compact native milestone band; and a closing action without a real hyperlink uses a high-contrast rectangular action band rather than a fake button. Exact numeric extraction keeps each value bound to its authored unit, preserves thousands separators for large integers and source-present relative labels such as `Above Q1`, routes conservative explicit parallel lists to cards, and may route categorical same-unit measures to a native editable bar chart. Shared percentage charts preserve source order and enforce a native 0-100 axis, 20-point major ticks, and literal percent labels. Unstructured trend prose without an explicit series remains a statement instead of becoming an invented chart. When a seeded composition cannot fit the governed text, the compiler first searches the same semantic family for a capacity-safe higher-type-scale variant and only then permits a generic fallback. Installed-font selection uses the governed Arial/Liberation Sans/Carlito/DejaVu Sans fallback chain, and inline emphasis is emitted as native editable rich-text runs. The OOXML gate verifies role-layout geometry/style plus object alpha, weight, shadow, chart axis/label format, data, and editability; it is not merely an open-file check.

HTML is an optional deterministic RenderPlan proof only. `--no-html-proof` disables it; proof failure is reported but cannot change PPTX bytes or bypass the portable hard gates. Model-authored arbitrary HTML/CSS and HTML-to-PPTX are forbidden.

Read [weak-model-generation-workflow.md](./references/weak-model-generation-workflow.md) for bounded normalization, two-retry handling, fact invariants, and safe defaults. Read [narrative-layout-system.md](./references/narrative-layout-system.md) for the 15 commercial narratives, semantic mappings, capacity, split/merge, and rhythm rules. Read [art-direction-brand-system.md](./references/art-direction-brand-system.md) for the 12 directions, theme tokens, BrandSpec, fonts, and asset gates. Read [quality-v2-repair.md](./references/quality-v2-repair.md) for cross-stage inspection, one pre-render plus one post-render repair, and rollback.

## Governed DeckPlan Mode (Expert Compatibility)

Use direct DeckPlan mode only for expert callers, legacy replay, or trusted upstream planners that already provide a validated semantic deck. It moves page selection, capacity, typography, theme, geometry, editable-object construction, and transaction safety into the skill instead of asking the caller to design with raw coordinates.

The model may provide only semantic intent. The schema rejects raw `x/y/width/height`, layout ids, template ids, fonts, colors, COM calls, code, macros, and scripts. Use `schemas/deck-plan.v1.schema.json` as the contract.

Stable semantic mappings include:

- `trend` with explicit ordered series → editable line chart; trend prose without a series → statement
- `composition` → editable doughnut or governed stacked chart
- `comparison` → comparison layout; categorical same-unit measures may become an editable bar chart under an analytical direction
- `table` → editable native table
- `sequence` / `process` → process diagram
- one dated event → compact editable milestone band; two or more dated events → timeline diagram
- `roadmap` → roadmap diagram
- `matrix` → matrix diagram
- `quadrant` → quadrant diagram
- `funnel` → funnel diagram
- `metrics` → governed KPI layout
- conservative explicit parallel lists → cards; other `bullets` → cards or structured content according to capacity

Each slide should have one dominant semantic block. Put numeric chart data in controlled items such as `category`, `series`, and `value`; put table rows in repeated controlled data items. Use `speaker_notes` on the slide and `hyperlink` on a content block. Hyperlinks are limited to `http`, `https`, `mailto`, and `slide:<id>`. Motion is `off` by default. `subtle-fade` and `step-reveal` are governed COM-only presets; portable mode rejects them before writing.

Compile without PowerPoint to inspect decisions:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --deck-plan deck-plan.json `
  --compile-deck-plan `
  --no-output-deck `
  --json
```

Render through the governed native-object and candidate-save pipeline:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --deck-plan deck-plan.json `
  --render-deck-plan `
  --backend auto `
  --verification portable `
  --output output\final.pptx `
  --export-qa `
  --export-pdf `
  --json
```

For expert direct-DeckPlan callers, use this constrained sequence:

1. Select one registered business scenario; do not invent an outline when an archetype exists.
2. Write one action title and one dominant semantic block per slide.
3. Select a registered content kind; do not select a layout, coordinates, font, or color.
4. Keep each item atomic and within the schema capacity. Let the compiler split overflow into continuation slides.
5. Use `generic` only when no stronger semantic relationship exists.
6. Leave motion off unless the presentation context explicitly benefits from it.
7. Compile first and inspect `decision_trace`, continuation pages, findings, and chosen page families.
8. Render only after the semantic plan validates; export previews and run QA before delivery.

Direct DeckPlan does not prove factual governance by itself. Prefer BriefPlan mode for ordinary models or customer-delivery work. The portable renderer produces named, identity-tagged, editable native text, shapes, images, charts, tables, and logical diagrams. It validates layout, theme, semantic advanced-object data, links, assets, slide geometry, and backend capability before candidate creation. A missing or unsuitable asset falls back to a native editable composition rather than a placeholder screenshot.

Search and download stock images through Pixabay without committing API keys:

```powershell
# Set PIXABAY_API_KEY in the process environment before running.
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --search-images "technology background" `
  --image-type photo `
  --image-orientation horizontal `
  --download-top-image `
  --no-save `
  --json
```

Search and download editable SVG icons through Iconify without an API key:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --search-icons "flowchart" `
  --icon-prefix mdi `
  --icon-color "#FF5722" `
  --icon-height 64 `
  --download-top-icon `
  --no-save `
  --json
```

Use `--download-icon bi:tag-fill` when the exact icon id is known. The helper caches search results under `.window-pptx/cache/iconify/`, downloads SVGs under `assets/downloads/iconify/<prefix>/`, and records color/size/flip/rotate parameters in `.window-pptx/asset_manifest.json`.

Add a master-level watermark instead of repeated per-slide text:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --template template.pptx `
  --add-master-watermark "Confidential" `
  --output output\watermarked.pptx
```

Export review previews and deck audit metadata:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --template output\final.pptx `
  --export-qa `
  --audit-deck `
  --no-save `
  --json
```

## Template Library Recommendation and Intake

Use this when the user asks to find, choose, rank, compare, recommend, or ingest reusable slide templates from the built-in template library.

Core library assets:

- Built-in category PPTX files live under `templates/template-library/reference/`.
- Preview PNGs are generated under `templates/template-library/previews/`.
- Review and recommendation metadata lives in `templates/template-library/template-library-review.xlsx`.
- One category PPTX may contain 3-5 single-page templates.
- The recommendation unit is one slide, not one deck.

For V2 intake automation, run the helper from native Windows PowerShell/CMD with desktop PowerPoint installed:

```powershell
py D:\Growth_up_youth\repo\skills\skills\owned\window-pptx\scripts\window_pptx_automation.py --project-dir D:\Growth_up_youth\repo\skills\skills\owned\window-pptx --intake-template-library --no-save --json
```

The intake command scans skill-local category PPTX files, exports slide previews, extracts objective slide metadata, and merges AI-initial recommendation fields into the workbook `Library` sheet. It does not create or modify user project decks, does not use macros or workbook buttons, and does not assemble final PPT pages.

For recommendation, consult `template-library-review.xlsx` before designing from scratch. Rows with `ReviewStatus = 已通过` are production-ready recommendations; rows with `AutoRecommendStatus = AutoRecommendable` are AI-initial candidates that may still need human review depending on the request.

Read [template-library-recommendation-workflow.md](./references/template-library-recommendation-workflow.md) for the full workflow, category rules, V2 intake fields, preservation rules, and validation prompts.

## Execution Workflow

1. Read `REQUEST.md`.
2. Confirm missing discuss-gate items.
3. Inventory and hash trusted source material; build FactStore for new generated decks.
4. Read or create `MODULES.md` and `SLIDE-MAP.md` when manual/template editing is required. For governed generation, NarrativePlan and compiled DeckPlan are the machine-readable equivalents.
5. For template recommendation requests, consult `templates/template-library/template-library-review.xlsx` before designing from scratch.
6. Use BriefPlan mode for ordinary models; use direct DeckPlan only for an expert/replay compatibility route.
7. Select DesignPack and art direction, compile VisualPlan + AssetPlan, and
   validate BrandSpec/assets before layout resolution.
8. Search/download required local assets first, including Iconify icons when the design calls for semantic labels, process nodes, flow arrows, UI symbols, or pictograms.
9. Compile and inspect narrative coverage, direction decision, semantic forms, splits, findings, and required backend capabilities.
10. Select registered TemplatePack for authorized reference-grade adaptation;
    select `auto`/PptxGenJS for compatible fresh `.pptx` work. Select `com`
    explicitly only when the request requires a declared COM-only capability;
    never silently switch.
11. Run add-in discovery only if the request mentions plugins or asks whether iSlide/OKPlus can be used.
12. If plugin use is desired, run `--probe-plugin-apis` and inspect:
   - 32-bit and 64-bit Office add-in registry values
   - ProgID / CLSID registration
   - load behavior and VSTO manifest metadata when registered
13. Treat live dispatch and `COMAddIn.Object` as unavailable in the default safe route. Use a plugin only from vendor documentation or a separately approved interactive investigation.
14. Generate only to an ASCII-safe candidate path; normalize the package deterministically.
15. Run OOXML semantic checks before any external proof renderer.
16. Render a candidate copy through an isolated LibreOffice profile, convert
    the PDF through Poppler or the explicit Ghostscript fallback, and run
    QualityReport v2 on those real PNGs.
17. Apply bounded deterministic pre-render/post-render repair where registered; roll back non-monotonic or content-changing repair.
18. Promote the PPTX/PDF/reports/proofs as one rollback-capable bundle only after all portable hard gates pass. Write reports, proofs, and hashes under `.window-pptx/audits/`.
19. Run optional PowerPoint certification only after portable PASS and only when `Application.HWND` binds to the one newly created process. Certify an exact-hash temporary copy, never save the deck, and never terminate a pre-existing process.
20. For benchmark blind review, stage hash-verified OOXML PPTX plus readable PNGs under anonymized `B-*` paths; never accept a score sheet from JSON-only evidence.
21. Route pixel-level visual UAT through `reviewer_routing.py`. Prefer
    `agnes/agnes-2.0-flash`, but select it only after an attachment probe proves
    image input works in the current provider session. If the probe is missing,
    unknown, or rejected, keep the visual verdict `NOT_RUN`. Never use
    `opencode/deepseek-v4-flash-free` as a pixel-review fallback; reserve it for
    code, rule, schema, and contract audits.
22. Report generated files, evidence gaps, unresolved ambiguities, unsupported capabilities, and certification status (`PASS`, `FAIL`, or `NOT_RUN`).

## Advanced Production References

Read [portable-backend-workflow.md](./references/portable-backend-workflow.md) for backend negotiation, pinned setup, OOXML/LibreOffice gates, HTML boundaries, certification, fingerprints, and `TYPE_E_CANTLOADLIBRARY` diagnosis.

Read [advanced-ppt-production-handbook.md](./references/advanced-ppt-production-handbook.md) for serious visual work: slide masters, layouts, design systems, action titles, awards pages, team pages, government/party style, technology style, charts, motion, and QA.

Read [project-module-management.md](./references/project-module-management.md) when the deck needs module planning with `MODULES.md`.

Read [script-management-workflow.md](./references/script-management-workflow.md) when creating `.window-pptx/scripts/run_project.py` or splitting reusable helper code from project-specific code.

Read [asset-library-workflow.md](./references/asset-library-workflow.md) when the project needs stock images, Iconify icons, or downloaded design assets.

Read [huashu-design-assimilation.md](./references/huashu-design-assimilation.md) for the pinned external reference, MIT boundary, and accept/adapt/reject decisions. Huashu is a design-method reference only; do not copy or run its HTML renderer, prompts, style prose, showcases, media, or fonts.

Read [template-library-recommendation-workflow.md](./references/template-library-recommendation-workflow.md) when selecting reusable slide templates from the skill template library. Use `PIXABAY_API_KEY` from the environment only. Iconify does not require an API key. Never commit API keys or hotlink remote asset URLs in the final deck.

## Design-Task Guardrails

When the request is "complete slides from provided materials" rather than simple text edits:

1. Separate slides by role before editing:
   - `instruction slides`: describe homework, rules, acceptance check, timing
   - `material slides`: list logo, colors, fonts, screenshots, raw photos, copy blocks
   - `reference result slides`: already-designed examples that show target polish or layout
   - `output slides`: the slides that should actually be created, overwritten, or appended
   - `cover slides`: title / opening summary slides
   - `directory slides`: agenda / table-of-contents slides
   - `section slides`: chapter divider / section opener slides
   - `body slides`: normal content/detail slides
   - `ending slides`: closing / thanks / summary-ending slides
2. Do not treat a polished reference result slide as a reusable source asset unless the user explicitly asks for reproduction.
3. Prefer extracting raw assets from `ppt/media/*` and rebuilding layouts from those assets.
4. If the user manually fixes one page as the "correct format", export that page to PNG first and use it as the structural target before editing other pages.
5. For visual work, always run at least one export-and-review cycle after generation.

Read [windows-pptx-lessons.md](./references/windows-pptx-lessons.md) when the task involves:

- Chinese paths or filenames
- locked `.pptx` files
- COM instability across multiple reruns
- extracting assets from an input deck
- judging whether a slide is a material page or an already-designed reference page

Read [ppt-homework-execution-playbook.md](./references/ppt-homework-execution-playbook.md) when the task is a full homework / training deck workflow with instruction slides, material slides, reference result slides, fonts, GIF/video animation references, or multiple assignments to complete.

Useful helper actions from the bundled script:

- `--extract-media` to dump `ppt/media/*` into a folder
- `--export-slides 4,6,8-10` to render selected slides to PNG
- `--make-ascii-temp-copy` before repeated COM reruns on Chinese filenames
- `--search-images` / `--download-image` for local traceable stock assets
- `--search-icons` / `--download-icon` for local traceable Iconify SVG assets with `--icon-color`, `--icon-width`, `--icon-height`, `--icon-flip`, and `--icon-rotate`
- `--add-master-watermark` for removable master-level watermarking
- `--export-qa` to render all slides for visual review
- `--audit-deck` to write shape/font/animation metadata

## Explicit Legacy COM Capabilities

Use PowerPoint COM only after capability negotiation selects the explicit `com` lane, or when optional certification is requested. Typical COM-only operations include:

- `PowerPoint.Application`
- `Presentations.Open(...)`
- `Presentations.Add(...)`
- `Slides.Add(...)`
- `Shapes.AddTextbox(...)`
- `Shapes.AddPicture(...)`
- `Shapes.AddTable(...)`
- `NotesPage.Shapes`
- `Slide.TimeLine.MainSequence.AddEffect(...)`
- `Presentation.SaveAs(...)`
- `Presentation.ExportAsFixedFormat(...)`
- `Application.COMAddIns`
- `Application.AddIns`

Read [com-capabilities.md](./references/com-capabilities.md) when you need boundaries, examples, and official references.
Read [plugin-api-discovery.md](./references/plugin-api-discovery.md) when the user wants to test whether iSlide, OKPlus, or another PowerPoint add-in exposes automation APIs.

## iSlide / OKPlus / Add-in Policy

Treat add-ins as optional accelerators.

Allowed:

- list registered PowerPoint COM add-ins from both Windows registry views
- read description, ProgID, CLSID, load behavior, and manifest metadata
- report that live connection, `.ppa` / `.ppam`, dispatch, object, and type information is unavailable in registry-only mode
- enable/disable only when explicitly requested and safe
- call a plugin only when a documented COM/VBA/API entrypoint is known and a separate run is explicitly approved

Not allowed by default:

- assume Ribbon buttons are callable
- call lifecycle methods such as `OnConnection` / `OnDisconnection` manually
- depend on iSlide/OKPlus for core deck generation
- start PowerPoint merely to enumerate or probe add-ins
- call direct `Dispatch(progID)` or inspect `COMAddIn.Object` in the default safe probe
- use UI automation as the first approach
- manage Office JavaScript web add-in internals through COM

If a user asks "can I use iSlide/OKPlus?", answer:

- yes for safe registration discovery; automation requires separate vendor documentation or explicit investigation
- no guarantee for UI-only features
- core generation remains on the portable backend; explicit COM is a capability-specific fallback, never an automatic one

Historical interactive probe pattern (not reproduced by the default safe command):

- iSlide may expose `iSlideTools.Public` as a COM class and a `COMAddIn.Object`, but the visible type info can be only Office's standard `_IDTExtensibility2` lifecycle interface: `OnConnection`, `OnDisconnection`, `OnAddInsUpdate`, `OnStartupComplete`, `OnBeginShutdown`.
- OKPlus / OneKeyTools Plus may appear as a connected VSTO add-in with manifest registration while `COMAddIn.Object` is `None` and direct `Dispatch("Slibe.OKPlus")` fails.
- In both cases, do not treat the add-in as having callable design APIs unless a richer interface is discovered in that exact environment or vendor docs/user-provided docs identify a safe entrypoint.

## Acceptance Checks

Use checks that match the request:

- output file exists under `output/`
- slide count matches expected count
- required titles/text appear
- required images/charts are present
- template visual style is preserved
- notes are present when requested
- OOXML semantic inspection passes for every governed object, relationship, slide/master/layout chain, notes page, hyperlink, chart cache, and embedded workbook
- the output remains native-editable; governed text, shapes, images, tables, charts, notes, and links are not replaced by slide screenshots
- LibreOffice opens the candidate through an isolated profile and exports a PDF whose page count and page geometry match the plan
- Poppler renders every PDF page to a PNG and Quality-v2 reports no blocking overflow, overlap, density, margin, or structural defect
- source and candidate hashes remain unchanged across verification; the verification manifest binds every proof and report to the promoted PPTX
- required runtime and font fingerprints are recorded; optional PowerPoint certification is accepted only when it binds the same candidate hash
- reference-grade outputs pass the structural visual floor; sparse text-only
  pages cannot pass merely because they contain no overlap

For animation homework or animation-sensitive decks, do not validate by animation count alone. Export a structured effect table for each required slide:

- animation sequence index
- target shape name
- effect type
- trigger type
- duration
- delay
- transition effect when slide transitions are required

Then compare the effect table against the user-visible requirement. Example: "fade in + left-to-right motion path + disappear" must appear as distinct effects on the light shape, while the title text must have a wipe effect triggered with the light.

For visual fidelity, inspect the exported PDF and PNG proofs. LibreOffice proof establishes a deterministic cross-engine floor, not PowerPoint pixel identity. Do not claim pixel-perfect verification from OOXML or COM object checks alone.

## Failure Handling

If running outside Windows:

- continue with the portable PptxGenJS + OOXML + LibreOffice/Poppler lane
- stop only when the request explicitly requires a COM-only capability or PowerPoint certification, and explain that those optional stages require native Windows desktop PowerPoint

If Node.js, npm, PptxGenJS `4.0.1`, or LibreOffice is missing or version-drifted,
or neither Poppler nor Ghostscript is available:

- fail before promoting any candidate
- run `python -m window_pptx.cli --doctor` and restore the pinned runtime from `scripts/node/package-lock.json`
- never substitute a different package version, skip the proof stage, or silently switch to COM

If PowerPoint is not installed:

- keep portable generation available
- skip optional certification, or ask the user to install desktop PowerPoint on a native Windows host only when certification or a COM-only feature is required

If `pywin32` is missing:

```powershell
py -m pip install pywin32
```

If PowerPoint COM starts failing with type library or makepy errors:

- run the read-only `--com-doctor` first
- distinguish PowerPoint's registered server and `MSPPT.OLB` from the `_Application` interface TypeLib registration
- classify `TYPE_E_CANTLOADLIBRARY (0x80029C4A)` as a stale/missing TypeLib path when `_Application` resolves to an absent WPS `wppapi.dll`; clearing `gen_py` cannot repair that registry root cause
- prefer late-bound `IDispatch` for the optional certification bridge because it avoids makepy's broken early-bound TypeLib load
- do not edit registry keys automatically; report the exact key/path and require an administrator or application repair workflow for registry correction
- do not treat COM as universal PPTX coverage; it is a Windows desktop object model with version-, add-in-, and UI-dependent gaps, not a complete public interface to every OOXML or internal PowerPoint feature
- keep daily fresh editable PPTX generation on the portable backend; reserve COM for declared physical-template, macro/template-format, native-grouping, animation, plugin-bound, or certification requirements

If a plugin is not found:

- continue with the portable backend, or with explicit native COM when a separately requested COM-only operation still needs it
- list detected add-ins and clearly say the requested plugin was not available

If a plugin is found but not callable:

- do not fake plugin use
- reproduce the requested effect with governed portable primitives when possible; otherwise use explicit native COM or report the unsupported plugin-only part

## Security and Safety

- Never execute macros unless `REQUEST.md` or the user explicitly allows macros.
- Never overwrite source decks by default.
- Save generated scripts and logs under `.window-pptx/`.
- Keep credentials out of decks, scripts, logs, and commits.
- Treat arbitrary HTML as untrusted input: HTML is proof-only and is never the canonical PPTX-generation source.
- Never edit Office/WPS registry entries from the doctor or certification commands.
- Never terminate a PowerPoint process that the current operation cannot prove it created; refuse certification when a pre-existing `POWERPNT.EXE` is present.
- Do not save from the certification bridge. Open an exact-hash temporary copy read-only, export proof, close, quit only the HWND/PID-bound process, and verify the canonical candidate hash is unchanged.
- Promote a candidate only after all required portable checks pass; remove failed candidates without deleting prior successful proofs.
