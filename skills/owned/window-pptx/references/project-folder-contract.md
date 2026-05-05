# window-pptx Project Folder Contract

This contract lets an agent turn a local folder into a reproducible PowerPoint automation job.

## Folder Layout

```text
ppt-project/
  REQUEST.md
  template.pptx
  source.pptx
  assets/
    logo.png
    screenshot-01.png
  data/
    metrics.csv
    chart.json
  notes/
    outline.md
  output/
  .window-pptx/
```

## Required File

`REQUEST.md` is the source of truth. If chat and `REQUEST.md` conflict, ask before editing.

## Recognized Inputs

| Path | Meaning |
|---|---|
| `REQUEST.md` | User requirements and run policy |
| `template.pptx` / `template.pptm` / `template.potx` / `template.potm` | Preferred visual template |
| `source.pptx` / other decks | Existing material to copy or edit |
| `assets/` | Images, icons, logos, screenshots, backgrounds |
| `data/` | Tables, chart data, JSON, CSV, Excel |
| `notes/` | Speaker notes, copy, references, outlines |
| `output/` | Generated deck and exports |
| `.window-pptx/` | Generated scripts, inventory, logs |

## REQUEST.md Sections

### Goal

Describe the desired final deck and audience.

### Inputs

List the template/source deck and important assets.

### Output

Specify output file name, export requirements, and overwrite policy.

### Edit Requirements

List exact slide operations:

- create new deck
- edit existing deck
- add/remove/reorder slides
- rewrite copy
- add charts/tables/images
- add speaker notes
- add animations/transitions

### Visual Constraints

Describe style:

- follow template exactly
- use brand colors
- preserve master/theme
- use a specific aspect ratio
- avoid certain colors/fonts

### Preferred Plugins

Optional. Examples:

- iSlide allowed only if detected and callable
- OKPlus allowed only if detected and callable
- native PowerPoint COM only

### Macro Policy

Recommended explicit values:

- `macros: disabled`
- `macros: allowed only for named macros`
- `macros: allowed for this trusted template`

### Acceptance Check

Define how to know the run is successful:

- expected slide count
- required slide titles
- PDF export required
- visual review required
- compare against reference deck

## Defaults

If `REQUEST.md` omits a detail:

| Missing item | Default |
|---|---|
| output path | `output/final.pptx` |
| overwrite policy | do not overwrite source decks |
| template | auto-detect `template.*`; ask if ambiguous |
| macros | disabled |
| plugins | native COM only |
| PDF export | disabled |

## Generated Artifacts

Use `.window-pptx/` for generated implementation files:

```text
.window-pptx/
  addins.json
  run.log
  automate_deck.py
```

Keep `output/` for user-facing results only.
