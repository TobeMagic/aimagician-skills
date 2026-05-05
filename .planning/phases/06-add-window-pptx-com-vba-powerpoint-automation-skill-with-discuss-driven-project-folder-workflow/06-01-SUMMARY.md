# Phase 6 Plan 01 Summary: window-pptx skill

**Completed:** 2026-05-05

## What Changed

- Added owned skill `skills/owned/window-pptx`.
- Added a discuss-gated PowerPoint project-folder workflow based on `REQUEST.md`.
- Added Windows-native Python helper script for:
  - Windows/pywin32 runtime checks
  - PowerPoint COM add-in discovery
  - template/source deck auto-detection
  - minimal request-summary slide generation
  - PPTX save and optional PDF export
- Added reference docs for folder contracts and COM/add-in boundaries.
- Updated README, English quick docs, and roadmap inventory.

## Key Decisions

- Native PowerPoint COM is the core execution path.
- iSlide/OKPlus are optional add-ins, not required dependencies.
- Plugin invocation is allowed only when a public COM/VBA/API entrypoint is known.
- Real COM execution must run from native Windows with desktop PowerPoint and pywin32.
- WSL can host the repo, but should not be treated as the PowerPoint COM runtime.

## Verification

- `python3 -m py_compile skills/owned/window-pptx/scripts/window_pptx_automation.py` passed.
- `npm run build` passed.
- `npm test` passed: 7 files, 25 tests.
- `node dist/cli/index.js bootstrap --dry-run --json` resolved:
  - `ownedSkillCount: 12`
  - `resolvedSkillCount: 45`
  - `window-pptx: true`
  - default targets: `codex`, `claude`, `opencode`, `gemini`, `hermes`, `cursor`
- `npm run bootstrap` applied the current environment install.
- `node dist/cli/index.js inspect --target codex --json` confirmed installed `window-pptx`.
- `node dist/cli/index.js doctor --json` returned `healthy` for all default targets.
- Token scan found no real `ghp_` or `ms-...` secrets in committed files.

## Runtime Gap

The helper script has not been run against desktop PowerPoint in this WSL session. A full runtime smoke test requires Windows native PowerShell/CMD, installed PowerPoint, and `pywin32`.
