---
name: window-pptx
description: |
  Automate Windows desktop PowerPoint through COM/VBA-compatible object models from a project folder containing REQUEST.md, templates, assets, data, and output requirements.

  Use this skill whenever the user asks to create, edit, batch-update, reproduce, or polish PowerPoint decks on Windows using COM, VBA, pywin32, PowerPoint.Application, iSlide/OKPlus add-in discovery, or a "folder with requirements + PPT/materials" workflow. Also use it when the user wants one-to-one PowerPoint implementation from a template or needs animation/notes/add-in-aware operations beyond pure pptx libraries.

  This skill has a discuss gate: before executing real deck edits, confirm or read from REQUEST.md the project folder, source/template deck, output policy, macro/add-in policy, and acceptance check.
compatibility:
  tools: [powershell, python, git]
  requires: Windows desktop PowerPoint, native Windows Python, pywin32
---

# Window PowerPoint COM Automation

This skill drives the installed Windows desktop PowerPoint app through the same object model exposed to VBA.

Use it for high-fidelity PowerPoint work where pure `.pptx` libraries are too limited:

- open or create `.pptx` / `.pptm` decks
- reuse a visual template
- edit slides, text boxes, images, tables, charts, notes, and layout objects
- inspect or add basic animations through `TimeLine.MainSequence`
- export to PDF when the local PowerPoint install supports it
- discover installed PowerPoint add-ins such as iSlide / OKPlus

Do not use this as a cross-platform PPT library. Real automation must run from native Windows, not WSL.

## Required Discuss Gate

Do not start real PPT editing until these five items are confirmed in chat or present in `REQUEST.md`:

1. Project folder path
2. Source/template deck choice
3. Output path and overwrite policy
4. Macro/add-in policy
5. Acceptance check

If the user says to proceed autonomously and `REQUEST.md` already contains enough information, continue using those written assumptions. If anything is missing, ask only the missing items.

## Project Folder Contract

Default folder shape:

```text
ppt-project/
  REQUEST.md
  template.pptx
  assets/
  data/
  notes/
  output/
  .window-pptx/
```

Recognize these inputs:

- `REQUEST.md`: primary user requirements
- `*.pptx`, `*.pptm`, `*.potx`, `*.potm`: templates or source decks
- `assets/` or `images/`: logos, screenshots, photos, icons, backgrounds
- `data/`: CSV, JSON, Excel, chart data, tables
- `notes/`: speaker notes, outlines, references
- `output/`: generated decks and exports
- `.window-pptx/`: generated scripts, run logs, add-in inventory

If no template is specified, prefer files named `template.pptx`, `template.pptm`, `template.potx`, or `template.potm`. Otherwise ask which deck to use if multiple candidate decks exist.

Read [project-folder-contract.md](./references/project-folder-contract.md) when you need the full folder and `REQUEST.md` rules.

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

`Preferred Plugins` is optional. Empty means "use native PowerPoint COM only".

## Runtime Setup

Run from a Windows-native shell:

```powershell
py -m pip install pywin32
py path\to\window_pptx_automation.py --project-dir C:\path\to\ppt-project --list-addins
```

If `py` is not installed, use Windows `python`:

```powershell
python path\to\window_pptx_automation.py --project-dir C:\path\to\ppt-project --list-addins
```

If the repository is inside WSL under `/mnt/d/...`, call the script using a Windows path from PowerShell, for example:

```powershell
py D:\Growth_up_youth\repo\skills\skills\owned\window-pptx\scripts\window_pptx_automation.py --project-dir D:\ppt-project --list-addins
```

## WSL to Windows Bridge Mode

WSL can launch Windows executables through interop, but PowerPoint COM automation is still executed by Windows processes.

Valid bridge pattern from WSL:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
  "python 'D:\Growth_up_youth\repo\skills\skills\owned\window-pptx\scripts\window_pptx_automation.py' --project-dir 'D:\ppt-project' --list-addins"
```

What this means:

- WSL is only the caller/orchestrator.
- Windows `powershell.exe` runs the command.
- Windows `python.exe` imports `win32com.client`.
- PowerPoint COM runs inside the logged-in Windows desktop session.
- Paths passed to the script must be Windows paths such as `D:\...`, not `/mnt/d/...`.

Before running real work from WSL, verify the Windows runtime:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
  "python -c \"import sys, win32com.client; print(sys.executable); print('pywin32 ok')\""
```

Known bridge caveats:

- PowerShell stdout redirection may produce UTF-16 files; prefer scripts that write UTF-8 JSON directly.
- Chinese paths may display mojibake in terminal output even when file access is correct.
- `py` launcher may be absent; use `python` if Windows Python is on PATH.
- PowerPoint must be installed and available in the current interactive Windows desktop session.
- This is not suitable for pure headless WSL, Linux cron, or SSH-only Windows sessions.
- WSL and Windows have different Python packages, PATH, environment variables, and current directories.
- File locks can occur if PowerPoint keeps a deck open; close presentations in `finally` blocks.

## Bundled Helper Script

Prefer the bundled helper script for deterministic checks:

```powershell
py ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py --project-dir C:\ppt-project --list-addins --json
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
- `.window-pptx/exports/`
- `.window-pptx/temp/`
- `.window-pptx/logs/`

Probe iSlide / OKPlus or other add-in automation surfaces without invoking their business methods:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --probe-plugin-apis `
  --plugin-progid iSlideTools.Public `
  --plugin-progid Slibe.OKPlus `
  --no-save `
  --json
```

If PowerPoint COM starts failing after `EnsureDispatch` / makepy errors, clear the generated COM wrapper cache before retrying:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --clear-com-cache `
  --list-addins `
  --no-save
```

Create or open a deck and add a request-summary slide:

```powershell
py ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py --project-dir C:\ppt-project --output output\final.pptx
```

Export PDF too:

```powershell
py ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py --project-dir C:\ppt-project --output output\final.pptx --export-pdf
```

The helper is intentionally conservative. For a real one-to-one deck, generate a project-specific Python COM script under `.window-pptx/`, using the helper as the base for environment setup, add-in discovery, open/save/export, and safe cleanup.

## Execution Workflow

1. Read `REQUEST.md`.
2. Inventory project files.
3. Confirm missing discuss-gate items.
4. Run add-in discovery if the request mentions plugins or if the user asks whether iSlide/OKPlus can be used.
5. If plugin use is desired, run `--probe-plugin-apis` and inspect:
   - Office add-in registry values
   - direct `Dispatch(progID)` result
   - `Application.COMAddIns.Item(progID).Object`
   - exposed type library / dispatch members
6. Choose native COM implementation first unless a documented plugin method is actually discoverable.
7. Generate a concrete Windows Python script in `.window-pptx/`.
8. Execute the script from Windows PowerShell or CMD.
9. Save outputs under `output/`.
10. Export PNG previews for target slides when visual work is involved.
11. Verify acceptance criteria with COM object checks and rendered previews.
12. Report generated files, unresolved ambiguities, and any plugin limitations.

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

## Native COM Capabilities

Use PowerPoint COM for:

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

- list installed COM add-ins
- list PowerPoint-specific `.ppa` / `.ppam` add-ins
- read description, ProgID, GUID, and connected/loaded status
- probe COM registration and type information
- inspect `COMAddIns.Item(progID).Object` without calling unknown methods
- enable/disable only when explicitly requested and safe
- call a plugin only when a documented COM/VBA/API entrypoint is known

Not allowed by default:

- assume Ribbon buttons are callable
- call lifecycle methods such as `OnConnection` / `OnDisconnection` manually
- depend on iSlide/OKPlus for core deck generation
- use UI automation as the first approach
- manage Office JavaScript web add-in internals through COM

If a user asks "can I use iSlide/OKPlus?", answer:

- yes for discovery and possibly public automation interfaces
- no guarantee for UI-only features
- native PowerPoint COM remains the default fallback

Observed local probe pattern:

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
- PDF export exists if requested

For animation homework or animation-sensitive decks, do not validate by animation count alone. Export a structured effect table for each required slide:

- animation sequence index
- target shape name
- effect type
- trigger type
- duration
- delay
- transition effect when slide transitions are required

Then compare the effect table against the user-visible requirement. Example: "fade in + left-to-right motion path + disappear" must appear as distinct effects on the light shape, while the title text must have a wipe effect triggered with the light.

For visual fidelity, export PDF or images and ask the user to inspect them. Do not claim pixel-perfect verification from COM object checks alone.

## Failure Handling

If running outside Windows:

- stop and explain that desktop PowerPoint COM requires native Windows

If PowerPoint is not installed:

- stop and ask the user to install or use a Windows machine with desktop PowerPoint

If `pywin32` is missing:

```powershell
py -m pip install pywin32
```

If PowerPoint COM starts failing with type library or makepy errors:

- remove the current user's temp `gen_py` cache or run the helper with `--clear-com-cache`
- prefer late-bound `win32com.client.dynamic.Dispatch("PowerPoint.Application")` in project scripts
- avoid `EnsureDispatch` unless early-bound constants are necessary

If a plugin is not found:

- continue with native COM if possible
- list detected add-ins and clearly say the requested plugin was not available

If a plugin is found but not callable:

- do not fake plugin use
- reproduce the requested effect with native COM or report the unsupported plugin-only part

## Security and Safety

- Never execute macros unless `REQUEST.md` or the user explicitly allows macros.
- Never overwrite source decks by default.
- Save generated scripts and logs under `.window-pptx/`.
- Keep credentials out of decks, scripts, logs, and commits.
- Be careful with `Application.Quit()` if attaching to an existing PowerPoint session.
