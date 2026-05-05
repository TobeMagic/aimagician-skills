# PowerPoint COM Capabilities and Boundaries

## Core Principle

Windows desktop PowerPoint exposes a COM automation object model that closely matches VBA. Python can access it through `pywin32` and `win32com.client`.

Typical entrypoint:

```python
import win32com.client

app = win32com.client.DispatchEx("PowerPoint.Application")
presentation = app.Presentations.Open(r"C:\deck\template.pptx", -1, -1, 0)
```

## Useful Object Model Areas

| Area | Example API | Use |
|---|---|---|
| Application | `PowerPoint.Application` | Start or attach to PowerPoint |
| Presentations | `Presentations.Open`, `Presentations.Add` | Open or create decks |
| Slides | `Slides.Add`, `Slides(i).Delete` | Add, delete, reorder slides |
| Shapes | `Shapes.AddTextbox`, `Shapes.AddPicture`, `Shapes.AddTable` | Add content |
| Text | `Shape.TextFrame.TextRange.Text` | Read/write text |
| Notes | `NotesPage.Shapes` | Add speaker notes |
| Animation | `Slide.TimeLine.MainSequence.AddEffect` | Add animation effects |
| Add-ins | `Application.COMAddIns`, `Application.AddIns` | Inspect available add-ins |
| Output | `Presentation.SaveAs`, `ExportAsFixedFormat` | Save deck or export PDF |

## Add-in Types

### COM Add-ins

PowerPoint exposes loaded COM add-ins through `Application.COMAddIns`. The collection can provide:

- count
- item access
- description
- ProgID
- GUID
- connected state

Some add-ins can be toggled through `Connect`, depending on implementation and policy.

### PowerPoint Add-ins

PowerPoint-specific add-ins usually use `.ppa` or `.ppam`. They are exposed through `Application.AddIns`.

### Office JavaScript Web Add-ins

COM can open decks that contain Office JS add-ins, but COM does not fully manage the JavaScript add-in lifecycle. Treat them as document-hosted UI/runtime components.

## iSlide / OKPlus Guidance

Use this decision tree:

1. List add-ins.
2. Check whether iSlide/OKPlus appears in `COMAddIns` or `AddIns`.
3. If detected, look for a known ProgID, macro, or documented automation API.
4. If a callable entrypoint exists, use it carefully and log the exact call.
5. If only Ribbon/UI behavior exists, do not depend on it; reproduce the result with native COM or ask for a manual export/material from the plugin.

## Known Runtime Constraints

- Windows only.
- Requires installed desktop PowerPoint.
- Native Windows Python is preferred.
- WSL cannot directly host PowerPoint COM execution.
- Trust Center, macro policy, and enterprise security policies can block macro/add-in behavior.
- UI-only add-ins may require user interaction and are not reliable for unattended runs.

## Official References

- PowerPoint `Presentations.Open`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentations.open
- PowerPoint `Application.COMAddIns`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.comaddins
- Office `COMAddIns`: https://learn.microsoft.com/en-us/office/vba/api/office.comaddins
- PowerPoint `Application.AddIns`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.addins
- PowerPoint `Sequence.AddEffect`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.sequence.addeffect
- PowerPoint `Sequence`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.sequence
