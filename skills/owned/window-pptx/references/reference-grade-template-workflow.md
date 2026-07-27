# Reference-Grade Template Workflow

Use this workflow when the user supplies a polished PPTX as the visual target
and authorizes its design assets for reuse. It raises the visual floor without
asking a weak model to recreate hundreds of coordinates, crop settings,
vector decorations, charts, and master relationships.

## 1. Authorization and provenance

A TemplatePack must contain:

- a source PPTX copied into the owned skill only with explicit authorization;
- `ORIGIN.md` recording source path, authorization scope, and SHA-256;
- `template-pack.json` declaring the source hash, slide count, supported
  scenarios, shape slots, chart slots, and capacity;
- a DesignPack manifest that selects the TemplatePack only for compatible
  scenarios.

Never register an internet-downloaded deck, unlicensed font, or third-party
media bundle without a compatible license or explicit user authorization.

## 2. Stable binding boundary

Text slots target `(slide number, cNvPr shape id)`. Chart slots target
`(chart part, cache index)` plus an embedded workbook coordinate.

The model supplies only slot values. It cannot supply:

- an OOXML path;
- a shape id;
- coordinates, font, color, or arbitrary XML;
- a chart-part path or workbook path;
- code, macros, or COM instructions.

Unknown slots, missing required slots, duplicate targets, over-capacity text,
non-finite chart values, source-hash mismatch, and slide-count mismatch fail
before output mutation.

## 3. Rich text and line behavior

Each text shape keeps its existing paragraphs and run properties. A binding
value separated by `\n` maps successive fragments to existing rich-text runs.
It does not create a paragraph. Use this only when the TemplatePack author
intentionally exposes multiple differently styled runs, for example:

```json
{
  "s01.title": "参考级\n交付系统"
}
```

If a shape has one run, provide one compact string and let the existing text
frame perform normal wrapping. Capacity is a hard maximum, not a design
recommendation; use shorter action titles whenever a fallback font expands.

## 4. Editable charts

Chart labels and values are not edited as screenshots. The adapter updates:

1. the chart XML cache used by PowerPoint and preview engines;
2. the corresponding shared string or worksheet cell in the embedded XLSX.

Numeric values must be finite JSON numbers. Text and numeric slots use
different workbook coordinate types. A chart update that cannot update both
representations is rejected.

## 5. Package preservation

Adaptation writes a temporary OOXML package, validates it, and atomically
promotes a new candidate. The source is hash-checked before and after.
Unbound package parts must be byte-identical. A no-op adaptation must produce a
byte-identical copy.

The adapter preserves:

- masters, layouts, themes, and slide sizes;
- images, crop rectangles, transparencies, and gradients;
- vector shapes, groups, connectors, and z-order;
- native tables, charts, chart caches, and embedded workbooks;
- speaker notes, links, and package relationships unless explicitly bound.

## 6. Reference-grade quality gate

Openability and lack of overlap are necessary but insufficient. The structural
profile rejects decks below explicit floors for:

- average visual/editable object count per slide;
- distinct page-composition signatures;
- packaged media count and bytes;
- editable chart count;
- grouped/vector composition;
- gradients, crops, connectors, and other decorative primitives.

The generated candidate is then opened by an isolated LibreOffice process,
exported to PDF, and rasterized page by page with Poppler or Ghostscript.
Page count, geometry, source hash, and candidate hash must remain stable.

PNG inspection detects near-empty pages, unusually dense pages, non-decorative
content touching edges, missing previews, and adjacent near-duplicates.
Structural and PNG gates complement each other: neither is a pixel-perfect
PowerPoint certification.

## 7. Font portability

LibreOffice can substitute Windows or commercial fonts. This can visibly
change line breaks or make calligraphic titles appear oversized even when the
OOXML and original reference render the same way under LibreOffice.

Therefore:

- preserve the authorized source font declarations by default;
- when a declared display font produces proven cross-engine overlap, apply a
  manifest-owned `text_style_rules` clamp to selected slot kinds/slides; never
  let the model choose the fallback font or font size;
- record installed-font fingerprints;
- keep binding copy compact enough for declared capacities;
- treat LibreOffice as a deterministic cross-engine floor;
- use optional native PowerPoint certification for final pixel judgment when
  the customer environment depends on those fonts;
- never claim PowerPoint pixel identity from LibreOffice proof alone.

## 8. Delivery evidence

Keep these files under `.window-pptx/audits/`:

- `template-adaptation-report.json`
- `reference-quality-report.json`
- `template-portable-proof/portable-proof.pdf`
- one PNG per slide
- engine versions, candidate hash before/after, and source-template hash

The final response must link the promoted PPTX and report unresolved font or
cross-engine differences explicitly.

## 9. Visual reviewer routing

Pixel-level judgment must come from a reviewer that demonstrably decoded the
rendered slide images in the current session. Use
`scripts/window_pptx/reviewer_routing.py`:

- prefer `agnes/agnes-2.0-flash` for PNG review;
- first attach a representative readable PNG and record an explicit
  image-input capability probe;
- do not infer vision support from the model family or provider name;
- if Agnes rejects the attachment, reports no image support, or returns an
  ambiguous result, mark visual UAT `NOT_RUN`;
- permit a fallback only when that exact fallback model has a successful
  image-input probe;
- never route pixel judgment to `opencode/deepseek-v4-flash-free`; use
  DeepSeek for code, contract, rule, and schema audits.

A reviewer needs the anonymized PNG evidence and its hash-bound PPTX. JSON
metrics, structural inspection, or a textual description of the slides cannot
substitute for seeing the pixels.
