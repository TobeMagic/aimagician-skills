# Script Management Workflow

Use this workflow when creating or maintaining project-specific PowerPoint automation scripts.

## Principle

Keep reusable capabilities in the skill helper, and keep project-specific design decisions in the project script.

This avoids both extremes:

- rewriting a huge one-off script every time
- forcing every project into a rigid global template

## Recommended Layout

```text
ppt-project/
  .window-pptx/
    scripts/
      run_project.py
    generated_assets/
    exports/
    audits/
    logs/
```

## Script Layers

### Skill Helper

The installed `window_pptx_automation.py` should handle:

- project initialization
- add-in discovery
- media extraction
- Pixabay search/download
- master watermark helper
- export QA helper
- deck audit helper
- safe open/save/close patterns

### Project Script

The project script should handle:

- reading the specific `REQUEST.md`
- reading `MODULES.md` and `SLIDE-MAP.md`
- opening the chosen source/template deck
- creating project-specific layouts
- inserting downloaded/generated assets
- writing project run logs
- calling export and audit steps

## Deterministic Script Rules

- Define paths at the top.
- Never overwrite the source deck.
- Save output under `output/`.
- Write all logs under `.window-pptx/logs/`.
- Write generated assets under `.window-pptx/generated_assets/`.
- Export review images under `.window-pptx/exports/`.
- Close presentations in `finally`.
- Quit only the isolated PowerPoint instance created by the script.

## Windows Runtime Rule

Real COM work must run under Windows Python:

```powershell
python C:\ppt-project\.window-pptx\scripts\run_project.py
```

From WSL, call Windows PowerShell:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
  "python 'C:\ppt-project\.window-pptx\scripts\run_project.py'"
```

WSL is useful for repo search and orchestration, but it does not host PowerPoint COM.

## Recommended Project Script Sections

1. constants and paths
2. COM startup and cleanup
3. helper functions
4. design tokens
5. module builders
6. asset preparation
7. deck assembly
8. export and audit
9. main

## Logs to Produce

`run_log.json`:

- started_at
- source deck
- output deck
- generated slides
- module IDs
- assets used
- warnings

`deck_audit.json`:

- slide count
- font list
- shape counts
- image counts
- animation effects

`asset_manifest.json`:

- local asset paths
- source URLs
- provider
- usage notes

## When to Copy Code

For a small task, call the helper directly.

For a serious deck, create a project script and reuse only stable helper patterns. Do not paste giant unrelated scripts into every project.
