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

The command is terminal and emits one result to stdout; it does not write an inventory file. The probe is registry-only:

- reads 32-bit and 64-bit Office add-in registry views
- reads ProgID / CLSID registration in both views
- reports load behavior and VSTO manifest metadata when present
- explicitly skips direct COM dispatch, `Application.COMAddIns.Item(progID).Object`, and `ITypeInfo`

It does not start PowerPoint, load third-party add-in code, open a presentation, call business methods, or write files.

## How To Interpret Results

### Registered Automation Class

The registry result contains a ProgID and CLSID in the Office-compatible view. This proves registration only. It does not prove that feature-level methods are public or safe.

If vendor documentation separately shows methods such as:

- `ExportTheme`
- `ApplyLayout`
- `ReplaceImages`
- `BatchAlign`

then a separate, explicitly approved investigation may call only the required documented method with logging. Do not infer those methods from registration.

### VSTO Manifest Only

The Office add-in key contains a manifest or load behavior but no usable ProgID/CLSID in the compatible view. Treat it as installed but without a proven callable feature API.

### No Automation Object

If registration is absent, incomplete, or undocumented, treat the plugin as UI-only for automation purposes.

## Observed Local Findings

On an earlier interactive test machine (historical evidence, not produced by the current safe command):

- iSlide appeared as `iSlideTools.Public`, direct dispatch succeeded, and `COMAddIn.Object` existed. Its visible type info exposed `_IDTExtensibility2` lifecycle methods only.
- OKPlus appeared as connected `Slibe.OKPlus`, but direct dispatch failed and `COMAddIn.Object` was `None`. Registry showed a VSTO manifest path.

Practical result: native PowerPoint COM remained the correct execution path for deck generation, animation, transition, text, shape, image, and export operations.

## Safety Rules

- Do not invoke lifecycle methods manually.
- Do not start PowerPoint or dispatch add-in classes for routine inventory.
- Do not press Ribbon buttons through UI automation unless explicitly requested as a last resort.
- Do not enable/disable add-ins unless the user asks and the run plan records it.
- Do not depend on plugin behavior for the core output when native COM can produce the result.
