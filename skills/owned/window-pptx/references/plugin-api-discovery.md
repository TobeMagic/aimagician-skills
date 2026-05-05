# PowerPoint Plugin API Discovery

Use this reference when the user asks whether PowerPoint plugins such as iSlide or OKPlus can be automated.

## Principle

PowerPoint add-ins can be installed and connected without exposing a useful public automation API. Discovery must separate three states:

1. Installed and connected
2. Has a COM/VBA/object-model entrypoint
3. Has a safe, documented method that matches the user's requested operation

Only state 3 is enough to call plugin features automatically.

## Safe Probe Command

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --probe-plugin-apis `
  --plugin-progid iSlideTools.Public `
  --plugin-progid Slibe.OKPlus `
  --no-save `
  --json
```

This writes:

```text
ppt-project/.window-pptx/plugin_api_probe.json
```

The probe is read-only:

- reads Office add-in registry keys
- reads ProgID / CLSID registration
- checks direct COM dispatch
- checks `Application.COMAddIns.Item(progID).Object`
- enumerates dispatch members through `ITypeInfo`

It does not call discovered business methods.

## How To Interpret Results

### Good Sign

The probe shows methods/properties that are clearly feature-level and documented, for example:

- `ExportTheme`
- `ApplyLayout`
- `ReplaceImages`
- `BatchAlign`

Then read the vendor/user docs and call only the required method with explicit logging.

### Weak Sign

The probe only shows Office lifecycle methods:

- `OnConnection`
- `OnDisconnection`
- `OnAddInsUpdate`
- `OnStartupComplete`
- `OnBeginShutdown`

This means the add-in is visible to Office, but does not expose the feature API you need.

### No Automation Object

If `COMAddIn.Object` is `None`, direct `Dispatch(progID)` fails, or only a VSTO manifest is present, treat the plugin as UI-only for automation purposes.

## Observed Local Findings

On one tested Windows PowerPoint machine:

- iSlide appeared as `iSlideTools.Public`, direct dispatch succeeded, and `COMAddIn.Object` existed. Its visible type info exposed `_IDTExtensibility2` lifecycle methods only.
- OKPlus appeared as connected `Slibe.OKPlus`, but direct dispatch failed and `COMAddIn.Object` was `None`. Registry showed a VSTO manifest path.

Practical result: native PowerPoint COM remained the correct execution path for deck generation, animation, transition, text, shape, image, and export operations.

## Safety Rules

- Do not invoke lifecycle methods manually.
- Do not press Ribbon buttons through UI automation unless explicitly requested as a last resort.
- Do not enable/disable add-ins unless the user asks and the run plan records it.
- Do not depend on plugin behavior for the core output when native COM can produce the result.
