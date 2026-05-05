# Phase 6 Context: window-pptx COM/VBA PowerPoint Automation Skill

## User Intent

Create an owned skill named `window-pptx` for Windows-only PowerPoint automation through COM / VBA-compatible object models.

The user wants a project-folder workflow:

- The user opens or prepares a folder.
- The folder contains a `REQUEST.md` describing the desired PPT result.
- The folder may contain a template `.pptx` / `.pptm`, source PPTs, images, charts, data files, notes, and other assets.
- The skill should help produce a PowerPoint output that follows the request as closely as possible.

## Initial Discuss Decisions

- First version scope: `PPT编辑(MVP)`
- Folder contract: `REQUEST.md`
- Runtime: `Windows本机`

## Research Notes

Primary reference set:

- PowerPoint `Presentations.Open`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentations.open
- PowerPoint `TimeLine`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.timeline
- PowerPoint `Sequence.AddEffect`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.sequence.addeffect
- PowerPoint `Application.COMAddIns`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.comaddins
- Office `COMAddIn`: https://learn.microsoft.com/en-us/office/vba/api/office.comaddin

Key findings:

- `Presentations.Open` opens a presentation and returns a `Presentation` object. Its `WithWindow` parameter can hide or show the opened file, which matters for unattended batch runs.
- `TimeLine` stores animation information for a slide, slide range, or master. `TimeLine.MainSequence` exposes the main animation sequence.
- `Sequence.AddEffect` can add animation effects to a target shape and returns an `Effect` object.
- `Application.COMAddIns` exposes the currently loaded COM add-ins for PowerPoint.
- Office `COMAddIn` exposes identifiers such as `ProgID` / `Guid`, and the `Connect` property can report or change whether an add-in is connected.

## MVP Skill Shape

The first skill should focus on reliable editing rather than trying to expose the entire PowerPoint object model.

Minimum useful behavior:

- Confirm Windows + desktop PowerPoint + Python + pywin32 availability.
- Read `REQUEST.md` as the primary instruction.
- Discover local project inputs:
  - template files: `*.pptx`, `*.pptm`, `*.potx`, `*.potm`
  - source assets: `assets/`, `images/`, `data/`, `charts/`, `notes/`
  - optional existing output: `output/`
- Generate or run a Windows-native Python COM automation script.
- Open template/source presentation through `PowerPoint.Application`.
- Apply requested slide edits, layout changes, text, shapes, notes, images, and exports.
- Save generated files under `output/`.

Suggested project folder:

```text
ppt-project/
  REQUEST.md
  template.pptx
  assets/
  data/
  notes/
  output/
```

## Capability Boundaries

First version should support:

- open / create / save / export presentations
- add / delete / reorder slides
- add and edit shapes, text boxes, images, tables, and notes
- use a template presentation as visual source
- optionally export to PDF / images if PowerPoint supports it locally

Defer to later iterations:

- advanced animation timelines
- transition choreography
- master/theme surgery beyond template reuse
- COM add-in enable/disable flows beyond read-only discovery
- direct invocation of vendor-specific add-in APIs
- Office JavaScript web add-in lifecycle management

## Plugin Strategy: iSlide / OKPlus / Other PowerPoint Add-ins

The user wants to know whether existing PowerPoint plugins such as iSlide and OKPlus can be used.

Working answer:

- Yes, if the plugin is installed in the same Windows PowerPoint environment.
- The skill can discover installed COM add-ins through `PowerPoint.Application.COMAddIns`.
- The skill can inspect fields such as description, ProgID, GUID, and connection state.
- Some COM add-ins can be enabled or disabled through the `Connect` property.
- Stable feature invocation is only possible if the plugin exposes a documented COM automation interface, VBA macro entrypoint, ProgID, or otherwise callable public object model.
- If a plugin only exposes Ribbon/UI buttons and no automation API, the first version should not depend on it. UI automation can be treated as a later, less reliable fallback.
- Office JavaScript web add-ins are a separate category. COM can open and edit presentations that contain them, but cannot fully control the add-in's internal JS lifecycle.

MVP policy:

- Core PPT generation must work without iSlide / OKPlus.
- `REQUEST.md` can include an optional section such as `## Preferred Plugins`.
- The skill should first run a local discovery script that lists available PowerPoint add-ins.
- If iSlide / OKPlus are detected, the agent may use them only when there is a known callable interface or an explicit user-provided workflow.
- If no callable interface is available, use native PowerPoint COM operations to reproduce the desired result.

Suggested discovery output:

```text
PowerPoint COM Add-ins:
- Description
- ProgID
- GUID
- Connect

PowerPoint AddIns:
- Name
- FullName
- Loaded
```

## Important Constraints

- Windows-only.
- Requires installed desktop PowerPoint.
- Requires `pywin32` or equivalent COM bridge.
- Native Windows Python is preferred for the MVP.
- WSL can host the repository, but COM execution should happen from Windows.
- Macro execution and COM add-in control may trigger Trust Center / policy restrictions.

## Open Questions For Planning

- Should `REQUEST.md` require a strict section template, or should free-form natural language be accepted?
- Should output default to `output/final.pptx`, or include timestamped output names?
- Should the skill generate automation scripts only, or execute them automatically when the environment is valid?
- Should `.pptm` macro reuse be allowed by default, or gated behind explicit user confirmation?
- What is the acceptance check: visual inspection, slide count/text assertions, exported PDF comparison, or screenshots?
