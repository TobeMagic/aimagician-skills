# window-pptx Project Folder Contract

This contract lets an agent turn a local folder into a reproducible PowerPoint automation job.

## Folder Layout

```text
ppt-project/
  REQUEST.md
  MODULES.md
  SLIDE-MAP.md
  template.pptx
  source.pptx
  assets/
    logo.png
    screenshot-01.png
    downloads/
      pixabay/
  data/
    metrics.csv
    chart.json
  notes/
    outline.md
  output/
  .window-pptx/
    media/
    scripts/
      run_project.py
    generated_assets/
    exports/
    audits/
    temp/
    logs/
    cache/
    addins.json
    asset_manifest.json
    automate_deck.py
    plugin_api_probe.json
```

## Required File

`REQUEST.md` is the source of truth. If chat and `REQUEST.md` conflict, ask before editing.

## Recommended Planning File

`MODULES.md` is the deck-level production plan. Use it to manage reusable modules before implementing the script:

- cover
- directory
- section divider
- body
- comparison
- timeline/process
- data/chart
- awards/honor
- team
- closing

`SLIDE-MAP.md` is the operator-facing planning sheet for project-style slide work.

Use it to map:

- slide number
- current role
- target role
- action: keep / reference / rebuild / append / overwrite
- assets needed
- notes

Recommended role vocabulary:

- `instruction`
- `material`
- `reference-result`
- `output`
- `cover`
- `directory`
- `section`
- `body`
- `ending`

## Recognized Inputs

| Path | Meaning |
|---|---|
| `REQUEST.md` | User requirements and run policy |
| `MODULES.md` | Deck-level module plan and design system |
| `SLIDE-MAP.md` | Working slide-role map and output plan |
| `template.pptx` / `template.pptm` / `template.potx` / `template.potm` | Preferred visual template |
| `source.pptx` / other decks | Existing material to copy or edit |
| `assets/` | Images, icons, logos, screenshots, backgrounds |
| `assets/downloads/pixabay/` | Locally downloaded stock images from Pixabay |
| `data/` | Tables, chart data, JSON, CSV, Excel |
| `notes/` | Speaker notes, copy, references, outlines |
| `output/` | Generated deck and exports |
| `.window-pptx/media/` | Raw media extracted from `ppt/media/*` |
| `.window-pptx/scripts/` | Project-specific automation entrypoints |
| `.window-pptx/generated_assets/` | Generated image masks, laurel/wheat components, rasterized text, clipped photos |
| `.window-pptx/exports/` | PNG slide exports for review |
| `.window-pptx/audits/` | Font, animation, visual QA, and deck audit JSON files |
| `.window-pptx/temp/` | ASCII temp deck copies for stable COM reruns |
| `.window-pptx/logs/` | Run logs and scratch outputs |
| `.window-pptx/cache/` | API search caches and non-final scratch data |
| `.window-pptx/asset_manifest.json` | Traceable asset source ledger |
| `.window-pptx/` | Generated scripts, inventory, logs, probes |

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
- define the style direction: government/party, technology, business, education, awards, or custom
- define whether watermark belongs on Slide Master or specific Custom Layouts

### Module Plan

Summarize the modules to create. Keep detailed implementation rows in `MODULES.md`.

Examples:

- cover
- directory
- section
- body
- awards
- team
- closing

### Asset Search

State whether stock assets are allowed.

If using Pixabay:

- keep the key in `PIXABAY_API_KEY`
- search with safe search enabled by default
- download selected assets locally
- record source metadata in `.window-pptx/asset_manifest.json`

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
| API keys | environment variables only |
| stock image hotlinking | disabled; download local copies |
| watermark | master/layout-level, not repeated per slide |

## Generated Artifacts

Use `.window-pptx/` for generated implementation files:

```text
.window-pptx/
  media/
  scripts/
    run_project.py
  generated_assets/
  exports/
  audits/
  temp/
  logs/
  cache/
  addins.json
  asset_manifest.json
  run.log
  automate_deck.py
  plugin_api_probe.json
```

Keep `output/` for user-facing results only.
