# Portable Backend Workflow

Use this reference for backend choice, PptxGenJS setup, independent render proof, OOXML failures, optional PowerPoint certification, and `TYPE_E_CANTLOADLIBRARY` diagnosis.

## Authority and process boundaries

The authoritative chain is:

```text
FactStore -> BriefPlan -> NarrativePlan -> DeckPlan -> RenderPlan
```

Only the validated RenderPlan crosses the Python-to-Node boundary. The model never emits JavaScript, OOXML, HTML, CSS, COM, or geometry code. The fixed skill-local worker maps registered objects to PptxGenJS `4.0.1`.

HTML is downstream proof only. It is generated deterministically from RenderPlan and is never parsed to create PPTX. Arbitrary model-authored HTML/CSS and HTML-to-PPTX runtimes are forbidden.

## Install and fingerprint

```bash
cd scripts/node
npm ci --ignore-scripts --no-audit --no-fund
node window_pptx_worker.mjs --doctor
soffice --version
pdfinfo -v
pdftoppm -v
```

The portable fingerprint records:

- Node and npm executable/version
- declared and installed PptxGenJS `4.0.1`
- `package.json` and `package-lock.json` SHA-256
- LibreOffice and Poppler executable/version
- OS, release, machine, locale, and sorted installed fonts
- model provider/model ids and governed asset manifest

PowerPoint evidence is absent in a portable-only fingerprint. If present, it must hash-bind a successful certification result.

## Capability matrix

| Capability | PptxGenJS | PowerPoint COM |
|---|---:|---:|
| Native text, shapes, images | yes | yes |
| Native table and chart | yes | yes |
| Notes and hyperlinks | yes | yes |
| Master/background styling | yes | yes |
| Logical process/timeline/matrix/quadrant/funnel/roadmap | editable child shapes | yes |
| Physical template/source import | no | yes, subject to PowerPoint object-model fidelity |
| `.pptm` / `.potx` / `.potm` | no | yes |
| Native shape grouping | no | yes for object-model-exposed groups |
| Animation | no | yes for object-model-exposed effects; not every internal feature is guaranteed |
| SmartArt | no | object-model dependent; not a governed portable feature |
| Daily headless generation | yes | no |
| PowerPoint rendering/certification | no | yes |

`--backend auto` selects PptxGenJS only. It never falls back to COM. A physical template, macro/template output, animation, or another unsupported required capability raises a stable capability error before candidate or process mutation.

## Portable transaction

1. Validate DeckPlan/RenderPlan and output policy.
2. Negotiate capabilities.
3. Render a new candidate with the fixed Node worker.
4. Normalize core timestamps, ZIP entry order/timestamps/permissions/compression, and embedded chart-workbook timestamps.
5. Inspect the package against RenderPlan.
6. Copy the candidate into a temporary workspace.
7. Run LibreOffice with an isolated `UserInstallation` profile.
8. Validate PDF page count/size; convert pages to PNG with Poppler.
9. Check PNG readability, dimensions, density, edge risk, and adjacent repetition.
10. Run QualityReport v2 and stop on any hard gate.
11. Verify source and candidate hashes.
12. Atomically promote the PPTX, optional PDF, reports, proof directory, and verification manifest as one rollback-capable bundle.

LibreOffice never re-saves the canonical PPTX. A failure removes the candidate and leaves an existing delivery untouched.

## Governed visual floor

Portable rendering owns a deterministic visual floor instead of relying on the caller or model to improvise styling:

- cover, agenda/section, content, and closing pages use distinct role-aware layout-master motifs;
- short cover, section, and focal-statement titles use the registered display scale only when exact slot-capacity calculation proves that 44 pt fits; longer titles retain the governed title scale;
- titles are bold and theme-primary, footers are muted, cards/KPIs use governed elevation and alpha, and KPI type scales only to the largest registered size that still fits its exact slot;
- title sizing follows the measured 44/32/22/18 pt ladder, while inline emphasis is emitted as native editable rich-text runs;
- exact numeric extraction binds each value to its authored unit, preserves mixed-unit changes, and displays large integers with thousands separators;
- conservative explicit parallel lists map to card compositions without treating numeric grouping commas as delimiters;
- exactly three short authored labels use a compact three-tile composition capped at 2.1 inches instead of inheriting detailed-card height;
- a plain focal claim uses normal editable statement typography and a governed accent; only an explicit `quote` fact may receive quotation styling;
- a single timeline or roadmap node becomes a compact left-aligned milestone band, while multi-node sequences retain the registered diagram geometry;
- a closing objective is classified into a fact-safe `Decision required`/`Next action` title, and an action without a real hyperlink is rendered as a high-contrast rectangular band rather than a fake button;
- categorical measures sharing one unit may become a native editable bar chart under an analytical direction; trend prose without explicit ordered series data remains a statement;
- charts whose plotted values all carry the same exact percent unit preserve source category order and use a native 0-100 value axis, 20-point major ticks, and literal `0"%"` axis/data-label formatting;
- numeric evidence embedded in a trusted metric sentence may retain `metrics` emphasis without parsing or inventing a value; non-numeric metric labels fall back to statement treatment;
- if a seeded composition cannot fit unchanged evidence, the compiler searches every serviceable variant in the same semantic family and prefers the highest safe type scale before falling back to generic body text;
- assetless covers and one-item KPI pages rotate between registered compositions rather than repeating one centered page;
- five- and six-item agendas have exact card variants, while longer agendas rebalance continuations so a one-item orphan is not emitted;
- unbound empty decorations are forbidden during automatic layout selection because a blank frame is indistinguishable from a missing-image placeholder;
- charts use a theme-derived series palette, restrained grid/axis styling, and bounded direct value labels; tables use a contrast-safe primary header, themed zebra rows, and numeric alignment.

These are native editable PowerPoint objects. The OOXML inspector checks the selected role layout, geometry, colors, alpha, title/card weight, decoration visibility, shadows, and the existing semantic/data contracts. Visual proof still requires contact-sheet review; deterministic styling is a quality floor, not evidence of senior-designer equivalence.

Font choice is resolved against the installed inventory using the governed Arial, Liberation Sans, Carlito, and DejaVu Sans fallback chain. A portable run records the chosen face and inventory digest instead of silently requesting an unavailable font.

## OOXML hard gates

The semantic inspector checks:

- ZIP safety, required parts, content types, and all relationship targets/ids
- slide order, count, dimensions, role-layout/master chain, governed master geometry/style, and background
- stable `objectName` plus structured `altText` identity
- native object kind, geometry, z-order, text, and editability sentinel
- governed fill, line, alpha, shadow, font face, font size/weight/style, and text color for native text/shape objects
- image relationship, payload, and required crop metadata
- native table text/data
- chart caches, embedded XLSX relationship/package/data
- notes text and slide backlink
- external and internal slide hyperlinks

Representative stable failures include `CONTENT_TYPE_MISSING`, `RELATIONSHIP_TARGET_MISSING`, `RELATIONSHIP_ID_INVALID`, `OBJECT_IDENTITY_MISSING`, `OBJECT_TEXT_MISMATCH`, `OBJECT_GEOMETRY_MISMATCH`, `CHART_WORKBOOK_RELATIONSHIP_MISSING`, `CHART_PERCENT_AXIS_MISMATCH`, `CHART_PERCENT_FORMAT_MISMATCH`, `IMAGE_PAYLOAD_UNREADABLE`, `NOTES_MISSING`, `HYPERLINK_TARGET_MISMATCH`, and `SLIDE_SIZE_MISMATCH`.

## Optional PowerPoint certification

Same-host certification:

```bash
python scripts/window_pptx_automation.py \
  --project-dir /path/to/project \
  --render-deck-plan --deck-plan deck-plan.json \
  --backend pptxgenjs --verification powerpoint
```

Cross-host/WSL bridge certification requires both the candidate and its hash-bound report:

```powershell
python scripts\window_pptx_automation.py `
  --project-dir C:\project `
  --certify-pptx output\final.pptx `
  --portable-verification-report .pptx-studio\audits\portable-verification.json `
  --json
```

Certification:

- rejects a mismatched or failed portable report
- fails closed if any `POWERPNT.EXE` already exists
- creates PowerPoint through late-bound `IID_IDispatch`
- binds `Application.HWND` to the one newly created process id
- disables macros and opens read-only with no window
- opens an exact-hash temporary copy rather than the canonical delivery
- exports PDF/PNG without saving the presentation
- verifies the PPTX hash before/after
- closes/quits only the HWND/PID-bound owned session
- never edits the registry or terminates an unowned process

The bridge manifest and per-file SHA-256 inventory provide strong accidental-integrity and mismatch detection, not cryptographic attestation against an attacker who can rewrite every local file. Run certification on a trusted host if adversarial provenance matters.

## Why COM is optional, not comprehensive

PowerPoint COM is a desktop automation object model, not a complete public interface to every byte or internal feature in a PPTX. It is stateful, Windows-only, sensitive to desktop/registration state, and some features are version-, add-in-, or UI-dependent. It is therefore valuable for a narrow capability lane and for sampled PowerPoint fidelity certification, but it is not required for fresh editable decks and should not be described as universal coverage.

The portable lane combines PptxGenJS for native editable objects, direct OOXML validation for semantic and package fidelity, and LibreOffice/Poppler for an independent visual proof. Direct OOXML libraries can complement this for inspection or narrowly governed patching, but low-level XML editing alone is too fragile as the main weak-model interface.

HTML-to-PPTX is intentionally proof-only here. Browser layout is useful for deterministic review, but converting arbitrary HTML/CSS commonly flattens content, loses native chart/table semantics, creates font and pagination drift, and expands the untrusted-code surface. If a future converter is evaluated, it must still emit the same typed RenderPlan objects and pass the same editability, OOXML, cross-engine, and transaction gates; HTML must not become the model-authored source of truth.

### Alternative engine decision record

| Engine | Best role in this Skill | Why it is not the current default |
|---|---|---|
| PptxGenJS | governed native-object generation | selected: broad editable object coverage, masters, charts/tables, and a small fixed Node worker |
| python-pptx | inspection, narrow patching, or a future Python-native adapter | strong industrial-grade core but incomplete PowerPoint feature coverage; a second renderer would double parity and QA work |
| Open XML SDK / direct PresentationML | validation, normalization, and narrowly governed package repair | precise but very low-level; unsafe as a free-form weak-model authoring surface and provides no renderer |
| LibreOffice UNO | independent rendering/proof and possible controlled conversions | broad API but different layout engine; it must not resave the canonical PPTX or be treated as PowerPoint-pixel-equivalent |
| Aspose.Slides | future licensed high-coverage backend/rendering evaluation | broad cross-platform feature claims, including rendering and animation, but commercial licensing, binary/runtime footprint, fidelity, and deterministic-contract work require a separate decision |
| arbitrary HTML/CSS conversion | proof-only | browser composition is not a reliable authority for native PowerPoint editability, semantic charts/tables, masters, or cross-engine typography |

Adding another renderer is valuable only when it closes a measured capability gap. Every adapter must consume the same validated RenderPlan, declare exact capabilities, emit native editable objects, and pass the existing semantic, visual, fingerprint, and rollback contracts.

## Why `TYPE_E_CANTLOADLIBRARY (0x80029C4A)` occurs

Early-bound pywin32/makepy resolves the PowerPoint `_Application` interface IID through the Windows `Interface\{IID}\TypeLib` registration. A stale WPS installation can redirect that interface to the WPS presentation TypeLib while the registered `wppapi.dll` no longer exists. Loading the generated `_Application` metadata then fails with `TYPE_E_CANTLOADLIBRARY` even when:

- `POWERPNT.EXE` exists and starts
- Microsoft `MSPPT.OLB` exists and loads
- the Microsoft PowerPoint TypeLib is registered
- late-bound `IDispatch` activation works

Run:

```powershell
python scripts\window_pptx_automation.py --project-dir C:\project --com-doctor --json
```

The doctor is read-only. It reports interface TypeLib mismatch, known WPS contamination, missing registered files, Microsoft TypeLib evidence, executable/bitness, and the safe ownership policy. Do not automatically delete registry keys. Back up the reported key, then use Microsoft Office Quick/Online Repair or an administrator-approved registry repair.

## Delivery artifacts

A portable PASS normally includes:

- final editable `.pptx`
- optional final `.pdf`
- `ooxml-report.json`
- `quality-report.v2.json`
- `portable-verification.json`
- `portable-proof/portable-proof.pdf`
- one PNG per slide
- optional `render-proof.html`
- generation/narrative/direction/repair artifacts for BriefPlan mode
- per-file SHA-256 evidence in the pipeline result or calibration manifest

Do not claim PowerPoint compatibility when certification is `NOT_RUN`. Do not claim senior-designer equivalence until the formal weak-model benchmark and blind review pass.
