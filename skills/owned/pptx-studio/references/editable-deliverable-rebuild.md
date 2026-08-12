# Editable Deliverable Rebuild Contract

Use this contract when a rendered image, screenshot, PDF, or visual mockup looks correct but the final customer deliverable must remain editable in PowerPoint.

## Native Editability

Rebuild semantic content as native PowerPoint objects whenever the object model supports it:

- text as text boxes/placeholders with editable runs and paragraphs;
- images as picture shapes with crop settings, not stretched bitmaps;
- charts as native PowerPoint charts with editable embedded data;
- tables as native PowerPoint tables;
- processes, timelines, matrices, quadrants, funnels, and roadmaps as editable shapes/connectors/groups;
- notes, hyperlinks, masters, footers, and approved motion as their corresponding PowerPoint features.

Do not use a full-slide screenshot, rendered canvas, or single background image as the completed page. Raster references may guide reconstruction and may remain as explicitly approved photographic/background assets, but they cannot replace editable slide content unless the user explicitly requests a raster deliverable.

## Coverage Gates

For every generated deck, define expected semantic objects before rendering and compare them with the delivered package/COM snapshot.

- Expected editable text coverage must be at least **99%**. Coverage is the normalized expected text represented in editable PowerPoint text objects, excluding explicitly approved text inside source photographs or logos.
- Expected native chart coverage must be **100%**.
- Expected native table coverage must be **100%**.
- Full-slide rasterization count must be **zero** unless the request explicitly opts into raster output.
- Any approved raster exception must name the slide, source asset, reason, and customer acceptance.

## Rebuild Procedure

1. Inventory the reference page: text, hierarchy, images, icons, data, charts, tables, diagrams, notes, links, and decorations.
2. Map each item to a native component and record any justified raster exception.
3. Resolve the governed theme, page family, layout variant, grid, and safe margins.
4. Recreate text and data first, then images/diagrams, then decorations; preserve meaningful reading and z-order.
5. Group only related objects and keep individual business content editable.
6. Save to a candidate with the same requested PowerPoint suffix.
7. Inspect the OOXML package and required parts, then open the candidate through macro-disabled read-only PowerPoint COM.
8. Reopen a writable disposable copy, edit sentinel text/data, save, reopen again, and prove the edit persists.
9. Promote only after every customer-delivery gate below passes.

## Package and Reopen Requirements

The candidate must:

- be a readable ZIP/OOXML package for `.pptx`/`.pptm`;
- contain the required content type, presentation, relationship, and slide parts;
- preserve the requested macro-enabled suffix and VBA parts when applicable;
- open through PowerPoint with macros forced disabled;
- close, reopen, save a disposable edit, and reopen again without repair prompts or corruption;
- retain editable text, charts, tables, notes, links, and grouping after roundtrip.

## Source Protection

Never rebuild in place by default.

- Resolve source, output, and staging paths before any write or COM open.
- Reject logical same-path source/output requests even when path spellings differ.
- Record the source SHA-256 before staging.
- Save and validate candidate siblings, then atomically promote to the explicit output.
- Recompute the distinct source SHA-256 after all promotions.
- Any unreadable or changed source hash is a hard failure, including partial-delivery cases where an output was already promoted.

## Compatibility and Font Reporting

Record in the validation report:

- PowerPoint/Windows version used for acceptance;
- slide size and output suffix;
- requested fonts, detected fonts, substitutions, and fallback reasons;
- unresolved glyph or language coverage risks;
- linked/embedded media and compatibility warnings;
- macro/add-in dependencies and whether the deck works without optional add-ins;
- package, open, save, reopen, and edit-sentinel results.

Missing fonts must use the governed fallback chain and be reported. Silent font substitution is not customer-delivery evidence.

## Customer-Delivery Hard Gates

Do not label or promote a deck as customer-delivery-ready unless all gates pass:

1. zero blockers and zero errors in the active quality profile;
2. successful package validation and PowerPoint open/save/reopen;
3. unchanged source SHA-256 before and after all requested outputs;
4. expected editable text coverage of at least 99%;
5. 100% expected native chart and native table coverage;
6. zero unapproved full-slide rasterization;
7. no text overflow, off-canvas content, disallowed overlap, image deformation, unreadable chart labels, or missing required content;
8. fonts and compatibility fallbacks are resolved or explicitly accepted;
9. the output opens normally and the edit sentinel persists after roundtrip;
10. candidate validation evidence and final output hashes are recorded.

If a hard gate fails, keep the candidate isolated, report the exact defect, and continue reconstruction or request explicit acceptance of a documented exception. Do not hide the problem behind a rasterized slide.
