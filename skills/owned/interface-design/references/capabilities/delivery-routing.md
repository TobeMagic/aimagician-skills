# Delivery Routing

Use this module before visual work whenever “presentation,” “prototype,” “deck,” “report,” or “editable” could imply different output technologies.

## Ownership Decision

1. Ask what must be opened, edited, or handed off at the end.
2. Record the required file type, runtime, editability, offline behavior, aspect ratio or viewport, and target environment.
3. Route browser-native artifacts to this skill and native Office artifacts to the matching document skill.

| Requirement | Route |
|---|---|
| Browser URL or local HTML, CSS, and JavaScript | `interface-design` |
| Interactive app, prototype, dashboard, report, visualization, or web presentation | `interface-design` |
| Editable `.pptx`, slide master, PowerPoint template, speaker notes in Office, or corporate deck handoff | `pptx` or `window-pptx` |
| Visual experimentation in HTML plus final native `.pptx` | Design here, then rebuild and verify in the PPT owner |

Do not make HTML implementation obey PowerPoint conversion limitations unless the user explicitly chooses a conversion-oriented experiment. Do not describe a screenshot-based or lossy conversion as an editable native deck.

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

Ask one concise format question only when the answer changes ownership or architecture. If the user already specifies HTML, browser, URL, `.pptx`, PowerPoint, Office editability, or a named PPT workflow, do not ask again.
