# Delivery Routing

Use this module before visual work whenever “presentation,” “prototype,” “deck,” “report,” or “editable” could imply different output technologies.

## Ownership Decision

1. Ask what must be opened, edited, or handed off at the end.
2. Record the required file type, runtime, editability, offline behavior, aspect ratio or viewport, and target environment.
3. Route browser-native artifacts and explicit HTML-first derivatives to this skill. Route ordinary native Office artifacts to the matching document skill.

| Requirement | Route |
|---|---|
| Browser URL or local HTML, CSS, and JavaScript | `interface-design` |
| Interactive app, prototype, dashboard, report, visualization, or web presentation | `interface-design` |
| User explicitly requires HTML as presentation source plus PDF | `interface-design`, HTML-first PDF route |
| User explicitly requires HTML as presentation source plus PPTX | `interface-design`, then choose editable or fidelity HTML-first PPTX before building |
| Editable `.pptx`, slide master, PowerPoint template, speaker notes in Office, or corporate deck handoff | `pptx` or `window-pptx` |
| Visual experimentation in HTML plus final native `.pptx` | Design here, then rebuild and verify in the PPT owner |

Do not make HTML implementation obey PowerPoint conversion limitations unless the user explicitly chooses HTML-first editable PPTX. Do not describe fidelity image slides as editable. If an explicit HTML-first PPTX request omits editability, ask once and stop before implementation.

## Hybrid Handoff

When HTML exploration precedes native PowerPoint, complete `assets/templates/ppt-handoff.md` with:

- narrative and slide inventory;
- exact aspect ratio and safe areas;
- semantic colors, fonts, weights, and fallback fonts;
- grid, spacing, image treatment, and motion-to-static translation;
- per-slide hierarchy, content, visual anchor, and notes;
- assets and their source or license status;
- known effects that require native reinterpretation;
- acceptance screenshots and reconstruction tolerances.

The PPT owner decides how to implement native shapes, text, charts, media, masters, and Office compatibility. The HTML owner remains responsible only for the accepted visual direction and handoff evidence.

## Ambiguity Gate

Ask one concise format question only when the answer changes ownership or architecture. Explicit HTML-first PPTX always requires editable versus fidelity selection unless the user already supplied it. A plain native `.pptx` request does not trigger HTML-first production.
