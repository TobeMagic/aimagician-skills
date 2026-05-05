# Phase 6 Validation: window-pptx

## Goal-Backward Check

User goal: add an owned `window-pptx` skill for Windows PowerPoint COM/VBA automation that supports a project folder with `REQUEST.md`, templates/assets/data, optional plugin discovery, and a discuss step before execution.

The implementation must make the following true:

1. The repository contains `skills/owned/window-pptx/SKILL.md`.
2. The skill clearly triggers on Windows PowerPoint COM/VBA automation requests.
3. The skill defines a `REQUEST.md` project-folder contract.
4. The skill documents when and how to discuss before running.
5. The skill handles iSlide/OKPlus as optional add-ins, not hard dependencies.
6. A bundled script can list add-ins and perform a minimal PowerPoint COM smoke workflow on Windows.
7. Bootstrap dry-run includes `window-pptx` in default owned skills.

## Planned Verification

- `python3 -m py_compile skills/owned/window-pptx/scripts/window_pptx_automation.py`
- `npm run build`
- `npm test`
- `node dist/cli/index.js bootstrap --dry-run --json`
- Inspect dry-run JSON for `window-pptx`

## Runtime Gap

PowerPoint COM execution itself cannot be validated from WSL/Linux. Runtime validation requires:

- Windows native shell
- desktop PowerPoint installed
- Python with `pywin32`

The bundled script must fail clearly outside Windows instead of pretending COM is available.
