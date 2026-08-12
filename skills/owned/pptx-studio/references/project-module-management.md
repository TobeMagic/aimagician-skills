# Project Module Management

Use this reference when a PowerPoint task is large enough to need module planning instead of ad-hoc slide edits.

## Why Modules

A deck is easier to automate when each page belongs to a module with a known purpose and layout pattern.

Modules reduce repeated decisions:

- what visual role the slide plays
- what assets are required
- what function builds it
- what QA checks apply

## Required Files

```text
ppt-project/
  REQUEST.md
  MODULES.md
  SLIDE-MAP.md
  .window-pptx/
    scripts/
      run_project.py
    generated_assets/
    exports/
    audits/
    logs/
```

## REQUEST.md vs MODULES.md vs SLIDE-MAP.md

`REQUEST.md` answers: what does the user want?

`MODULES.md` answers: what reusable deck sections/components will satisfy it?

`SLIDE-MAP.md` answers: what happens to each existing or generated slide?

Do not put every implementation detail into `REQUEST.md`. Keep it stable and user-facing.

## Module Table Columns

- `Module ID`: stable ID such as `M01`
- `Type`: cover, directory, section, body, awards, team, data-chart
- `Target Slides`: generated or affected slide numbers
- `Purpose`: what this module must communicate
- `Inputs`: source deck pages, images, data, text, notes
- `Visual Strategy`: layout, style, hierarchy, components
- `Script Function`: builder function name in `.window-pptx/scripts/run_project.py`
- `QA Notes`: specific checks for this module

## Common Module Patterns

### Cover

- large title
- subtitle or event metadata
- background image/gradient
- logo or identity mark
- optional master watermark disabled if it hurts clarity

### Directory

- section list
- progress indicator
- concise labels
- visual connection to section divider pages

### Section Divider

- section number
- short title
- one sentence promise or question
- stronger background than body pages

### Body

- action title
- one core point
- supporting text or visual evidence
- avoid too many columns

### Awards

- ceremonial visual frame
- laurel/wheat/trophy/badge component
- award name as the highest hierarchy
- recipient, issuer, date, achievement

### Team

- consistent headshot/person treatment
- preserve aspect ratio
- name, role, contribution
- avoid background clutter behind faces

### Data Chart

- title states the insight
- chart supports the title
- direct labels for important numbers
- chart source note if needed

## Script Function Naming

Use predictable functions:

- `build_cover`
- `build_directory`
- `build_section`
- `build_body`
- `build_awards`
- `build_team`
- `build_data_chart`
- `apply_master`
- `export_reviews`
- `write_audits`

## Completion Rule

Do not report completion until each module has:

- generated slide(s)
- used assets recorded
- preview export
- module-specific QA result
- unresolved limitations recorded
