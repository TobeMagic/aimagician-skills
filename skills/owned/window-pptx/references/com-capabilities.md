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

## Animation Verification

For animation tasks, inspect `Slide.TimeLine.MainSequence` after saving the deck. Record at least:

- `Effect.Shape.Name`
- `Effect.EffectType`
- `Effect.Timing.TriggerType`
- `Effect.Timing.Duration`
- `Effect.Timing.TriggerDelayTime`

This matters because static PNG/PDF exports cannot prove animation behavior. A valid verification report should show the ordered effect list, not only the number of animations.

Example interpretation:

- Fade effect on a light shape
- Motion-path-right effect on the same light shape
- Wipe effect on the title text triggered with previous
- Disappear effect on the light shape
- Slide transition effect set when the requirement asks for transitions

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

1. Run the registry-only inventory; do not start PowerPoint for routine discovery.
2. Check both HKLM 32/64-bit views and the shared HKCU Office add-in key.
3. Inspect Office add-in registration, `HKCR\<ProgID>\CLSID`, load behavior, and manifest metadata.
4. Look for a vendor-documented ProgID, macro, or automation API.
5. Treat direct `Dispatch`, `Application.COMAddIns.Item().Object`, and `ITypeInfo` as outside the default safe probe. Investigate them only in a separately approved interactive run.
6. If a documented callable entrypoint exists, use it carefully and log the exact call.
7. If only Ribbon/UI behavior or registration exists, do not depend on it; reproduce the result with native COM or ask for a manual export/material from the plugin.

## Observed iSlide / OKPlus Probe Results

These are historical examples from one interactive Windows PowerPoint investigation and are not emitted by the current registry-only command. They should not be treated as universal guarantees.

### iSlide

Observed:

- `COMAddIns` entry: `iSlideTools.Public`
- CLSID: `{2B92539D-351A-44C2-858A-BF50963536A8}`
- Inproc server: `D:\software\iSlide Tools\iSlideTools.Loader64.dll`
- Office add-in registry `LoadBehavior=3`
- `COMAddIn.Object` exists
- direct `Dispatch("iSlideTools.Public")` succeeds
- exposed dispatch interface: `_IDTExtensibility2`

Visible methods:

- `OnConnection`
- `OnDisconnection`
- `OnAddInsUpdate`
- `OnStartupComplete`
- `OnBeginShutdown`

Interpretation: this exposes the add-in lifecycle interface, not a stable public design API. Do not call lifecycle methods to trigger features.

### OKPlus / OneKeyTools Plus

Observed:

- `COMAddIns` entry: `Slibe.OKPlus`
- Friendly name: `OneKeyTools_Plus`
- Office add-in registry contains a VSTO manifest path such as `...\OneKeyToolsPlus.vsto|vstolocal`
- `COMAddIn.Object` is `None`
- direct `Dispatch("Slibe.OKPlus")` fails with invalid class string

Interpretation: treat it as a connected VSTO UI add-in unless a separate automation object or documented macro/API is provided.

## Known Runtime Constraints

- Windows only.
- Requires installed desktop PowerPoint.
- Native Windows Python is preferred.
- WSL cannot directly host PowerPoint COM execution, but it can launch Windows `powershell.exe` or `cmd.exe`; the actual COM automation must then run inside Windows Python against the logged-in desktop PowerPoint session.
- Trust Center, macro policy, and enterprise security policies can block macro/add-in behavior.
- UI-only add-ins may require user interaction and are not reliable for unattended runs.
- Broken `gen_py` / makepy caches can break COM wrapping. Clear the user's temp `gen_py` cache or use late-bound `win32com.client.dynamic.Dispatch`.

## WSL Bridge Checklist

Use this when the repo lives in WSL but PowerPoint is installed on Windows:

1. Convert paths from `/mnt/d/...` to `D:\...`.
2. Invoke `powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "python ..."` from WSL.
3. Verify `python -c "import sys, win32com.client; print(sys.executable)"` reports a Windows Python path.
4. Run scripts that write UTF-8 files themselves instead of relying on PowerShell `>` redirection.
5. Keep PowerPoint visible for debugging if UI/add-ins are involved.
6. Do not assume WSL packages, virtualenvs, or environment variables exist in Windows Python.

## Official References

- PowerPoint `Presentations.Open`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentations.open
- PowerPoint `Application.COMAddIns`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.comaddins
- Office `COMAddIns`: https://learn.microsoft.com/en-us/office/vba/api/office.comaddins
- PowerPoint `Application.AddIns`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.addins
- PowerPoint `Sequence.AddEffect`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.sequence.addeffect
- PowerPoint `Sequence`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.sequence
