# Phase 6: window-pptx COM/VBA PowerPoint Automation Skill - Research

**Researched:** 2026-05-05
**Domain:** Windows desktop PowerPoint automation, COM/VBA object model, pywin32-assisted project-folder workflow
**Confidence:** HIGH for native PowerPoint COM capabilities, MEDIUM for third-party add-in invocation

<research_summary>
## Summary

The reliable first version should be a skill, not a generic PPT generation engine. PowerPoint's Windows desktop COM/VBA object model is broad enough to open presentations, create slides, edit shapes/text/media, work with notes, save/export, inspect animation sequences, and enumerate add-ins. The practical boundary is that COM automation requires native Windows plus installed desktop PowerPoint, and third-party add-ins such as iSlide/OKPlus are only safely callable when they expose a documented automation surface.

The user workflow should be folder-based: a project directory contains `REQUEST.md`, optional templates/source decks, assets/data/notes, and an `output/` folder. The agent reads `REQUEST.md`, confirms ambiguous execution parameters before running, then creates or adapts a Windows-native Python COM script to implement the requested deck edits.

**Primary recommendation:** create `skills/owned/window-pptx` with a required discuss gate, a strict project-folder contract, add-in discovery guidance, and a bundled helper script for environment checks, add-in inventory, and a minimal request-summary deck/edit smoke run.
</research_summary>

<standard_stack>
## Standard Stack

| Component | Purpose | Why it fits |
|---|---|---|
| Windows desktop PowerPoint | Automation host | Required for `PowerPoint.Application` COM automation |
| Python + pywin32 | COM bridge | Directly drives the VBA-compatible object model from scripts |
| `REQUEST.md` | User-facing instruction file | Keeps deck requirements, templates, assets, plugin preferences, and acceptance checks in one folder |
| PowerPoint `.pptx` / `.pptm` / `.potx` / `.potm` | Templates and source decks | Reuses existing visual systems instead of rebuilding theme/master logic first |
| `output/` | Generated deck/export destination | Avoids overwriting user source files |

### Alternatives Considered

| Alternative | Tradeoff |
|---|---|
| Pure `.pptx` libraries such as python-pptx | Cross-platform, but cannot cover the full desktop/VBA animation/add-in surface |
| Browser/UI automation for PowerPoint | Can press Ribbon buttons, but brittle and hard to verify |
| Depending on iSlide/OKPlus | Useful when callable, but unsafe as the core path because many add-ins expose UI rather than stable COM APIs |
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Discuss-Gated Execution

Do not start real PPT editing until the skill has enough local truth:

- project folder path
- source/template PPT choice
- output path and overwrite policy
- macro/add-in policy
- acceptance check

If `REQUEST.md` already contains those fields, it counts as prior discussion and the agent can proceed.

### Pattern 2: Native COM Core, Plugin Optional

The first version should always be able to produce output with native PowerPoint COM. Add-ins are discoverable through `Application.COMAddIns` and `Application.AddIns`, but invocation requires a known ProgID/macro/API from the plugin vendor or user.

### Pattern 3: Script-as-Working-Artifact

For each PPT job, the agent should produce a concrete Windows Python script in the project folder, not rely on hidden manual operations. This keeps the run reproducible, debuggable, and easy to rerun.

### Anti-Patterns to Avoid

- Treating Cursor/Claude/Codex skills paths as PowerPoint runtime paths
- Executing COM automation from WSL and assuming it can access desktop PowerPoint
- Overwriting source `.pptx`/`.pptm` files by default
- Claiming iSlide/OKPlus actions can be called without a discovered public automation entrypoint
- Managing Office JavaScript add-in lifecycle through COM
</architecture_patterns>

## Validation Architecture

Phase 6 can be verified without a Windows PowerPoint instance by checking repository integration:

- `window-pptx` is discovered as an owned skill
- README and docs list the new skill
- the bundled script compiles with Python syntax checks
- TypeScript build and test suite remain green
- `bootstrap --dry-run --json` includes `window-pptx` for default targets

Full runtime verification requires Windows native Python, installed PowerPoint, and `pywin32`.

<sources>
## Sources

### Primary

- Microsoft Learn: PowerPoint `Presentations.Open` opens a presentation and exposes `ReadOnly`, `Untitled`, and `WithWindow` controls: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentations.open
- Microsoft Learn: PowerPoint `Application.COMAddIns` returns the COM add-ins currently loaded in PowerPoint: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.comaddins
- Microsoft Learn: Office `COMAddIns` collection exposes registered COM add-in information and update/item access: https://learn.microsoft.com/en-us/office/vba/api/office.comaddins
- Microsoft Learn: PowerPoint `Application.AddIns` lists PowerPoint-specific add-ins such as `.ppa` and `.ppam`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.addins
- Microsoft Learn: PowerPoint `Sequence.AddEffect` adds animation effects to shapes via a slide's timeline sequence: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.sequence.addeffect
- Microsoft Learn: PowerPoint `Sequence` is the animation effect collection accessed through `TimeLine.MainSequence`: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.sequence
- Local context: `.planning/phases/06-add-window-pptx-com-vba-powerpoint-automation-skill-with-discuss-driven-project-folder-workflow/06-CONTEXT.md`

</sources>

---
*Phase: 06-add-window-pptx-com-vba-powerpoint-automation-skill-with-discuss-driven-project-folder-workflow*
*Research completed: 2026-05-05*
*Ready for planning: yes*
