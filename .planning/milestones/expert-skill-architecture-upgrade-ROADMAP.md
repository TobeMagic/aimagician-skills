# Expert Skill Architecture Upgrade

**Created:** 2026-07-21
**Branch:** `feat/expert-skill-architecture-upgrade`
**Status:** Complete

## Goal

Upgrade the owned engineering and HTML design skills so a weaker model can follow explicit expert decision procedures, while preserving source-neutral runtime content, progressive loading, existing workflow capabilities, and the native PowerPoint boundary.

## Requirements

- **REQ-ENG-01:** Preserve the complete `aimagician-superpower` lifecycle and add concrete senior-engineering exploration, design, delivery, testing, debugging, review, and migration methods.
- **REQ-ENG-02:** Provide reusable engineering artifacts, deterministic task routing, and scenarios for analysis, feature work, bug repair, and refactoring.
- **REQ-DES-01:** Position `interface-design` as the owner of all HTML/CSS/JS-driven visual design, prototype, data, and browser presentation work.
- **REQ-DES-02:** Add information architecture, visual-system, layout, component, interaction, prototype, data, motion, presentation, and browser-QA methods.
- **REQ-DES-03:** Provide executable decision/pattern/quality libraries and scenarios for landing, dashboard, app prototype, and HTML presentation.
- **REQ-PPT-01:** Route native editable PowerPoint delivery to `pptx` or `window-pptx`; support an explicit hybrid handoff without ownership conflict.
- **REQ-SRC-01:** Keep external mirrors ignored and source provenance outside runtime skills.
- **REQ-OPS-01:** Pass focused and full repository checks, perform independent review, sync Codex/OpenCode, and integrate without disturbing unrelated working-tree changes.

## Phases

| Phase | Priority | Scope | Status | Evidence |
|---|---:|---|---|---|
| 1. Baseline and source audit | P0 | Owned skills, three external repositories, PPT boundary, current tests | Complete | Local mirrors, OpenCode reports, direct source inspection |
| 2. Engineering capability integration | P0 | Four modules, templates, route helper, evals, upgraded entry | Complete | `skills/owned/aimagician-superpower/` |
| 3. HTML universal design integration | P0 | Eight modules, pattern libraries, templates, route helper, evals, PPT boundary | Complete | `skills/owned/interface-design/` |
| 4. Documentation and automated acceptance | P0 | Merge audits, README, architecture and scenario tests | Complete | `docs/`, 101 passing tests |
| 5. Independent review and integration | P0 | Full checks, OpenCode review, Codex/OpenCode sync, commit and safe cherry-pick | Complete | Root commit `17ea2c5`; Skillbird and OpenCode acceptance healthy |

## Validation Evidence

- `npm test`: 21 files, 101 tests passed.
- `npm run typecheck`: passed.
- `npm run build`: passed.
- `node dist/cli/index.js format-skills --check --json`: all 23 owned skills `ok`.
- Runtime source-neutral scan: passed.
- `git diff --check`: passed.
- Independent OpenCode review: engineering ACCEPT, frontend ACCEPT, PPT boundary ACCEPT; four low/suggestion findings fixed and follow-up review reported no unresolved finding.
- Root integration: isolated commit `e5cffcf` was cherry-picked without path overlap as `17ea2c5`; unrelated Window-PPTX working-tree changes remained intact.
- Skillbird global reset: Codex and OpenCode each contain exactly 23 managed owned skills; `list` and `doctor` both report `healthy` with zero issues.
- Installed runtime comparison: upgraded Codex/OpenCode skill trees match repository source after excluding ignored audit mirrors; no `_external_repos`, `_analysis`, or `source-routing` directory was installed.
- Fresh OpenCode acceptance: `opencode/deepseek-v4-flash-free`, session `ses_07cb9c685fferbOJlS5z2isko1`, reported PASS for owner-ID parity, engineering modules, design modules/assets/templates, HTML/PPT routing, and forbidden-directory absence.

## Completion Result

All requirements and completion gates for this milestone are satisfied. Engineering and HTML design runtime capabilities are source-neutral, executable routing and acceptance scenarios are present, native PowerPoint ownership is explicit, repository checks pass, and both requested CLI targets are synchronized to the complete owned set.

## Completion Gate

- Every runtime reference resolves and all JSON decision assets validate.
- Engineering routes cover analysis, feature, bug, refactor, performance, and architecture.
- Design routes cover landing, dashboard, app prototype, HTML presentation, native PPTX, and hybrid delivery.
- Runtime skills contain no external source branding or update/install behavior.
- Focused tests, full tests, typecheck, build, formatter, and installation checks pass.
- Independent review has no unresolved blocking or high finding.
- The root worktree's unrelated active changes remain intact.
