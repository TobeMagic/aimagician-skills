# Expert Skill Architecture Upgrade

**Created:** 2026-07-21
**Branch:** `feat/skill-capability-audit`
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
| 4. Documentation and automated acceptance | P0 | Merge audits, README, architecture and scenario tests | Complete | `docs/`, 108 passing tests |
| 5. Independent review and integration | P0 | Full checks, OpenCode review, Codex/OpenCode sync, commit and safe cherry-pick | Complete | Root commit `17ea2c5`; Skillbird and OpenCode acceptance healthy |
| 6. HTML-native production parity | P0 | Complete source audit, GIF, devices/tweaks, deck/PDF, explicit HTML-first PPTX, narration/audio, runtime neutrality | Complete | Capability/parity audits, 108 tests, Agnes review, three-target bootstrap, YapCLI GIF acceptance |

## 2026-07-22 Extension Requirements

- **REQ-DES-04:** Preserve the complete reusable HTML-native production method from the audited design source through progressive owned modules, templates, starters, scripts, routes and tests.
- **REQ-DES-05:** Support deterministic poster, MP4 and tracked autoplay GIF delivery with loop, frame, codec, duration and size evidence.
- **REQ-DES-06:** Support variants/tweaks, comparison canvases, device/browser frames, Stage/Sprite motion, narration, provider-neutral TTS, licensed audio cues, ducking and loudness validation.
- **REQ-PPT-02:** Keep ordinary PowerPoint under the native PPT owners while supporting explicit HTML-first PDF and PPTX delivery through mandatory editable/fidelity contracts.
- **REQ-SRC-02:** Keep the complete source snapshot ignored and uninstallable; document capability parity outside the Skill runtime and prove no source identity or operational noise is installed.
- **REQ-OPS-02:** Use `agnes/agnes-2.0-flash` for the independent OpenCode audit, sync Codex/OpenCode/Claude, and validate a tracked GIF README hero in YapCLI.

## Validation Evidence

- `npm test`: 21 files, 108 tests passed.
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
- Final HTML-native capability audit: `agnes/agnes-2.0-flash`, session `ses_075ab8bb1ffeA6lh3tCV6i4G5H`, reported PASS with no blocker or high finding; direct spot checks corrected its three count/search errors.
- Phase 6 implementation: commit `ef95cbc` on `feat/skill-capability-audit`, pushed to `origin/feat/skill-capability-audit`.
- Three-target bootstrap: Codex, OpenCode, and Claude each report 23 managed owned skills, healthy `list`/`doctor` results, and zero issues; Codex's separate `.system` directory remains intact as a built-in runtime owner.
- YapCLI media acceptance: OpenCode session `ses_0758576f2ffe28Keo3o3Ecizew` used `agnes/agnes-2.0-flash`, committed and pushed `547860f` to `main`, and left a clean worktree with local HEAD equal to `origin/main`.
- Tracked YapCLI README hero: 800x450 GIF, 8 seconds, 12 fps, 96 frames, 261,335 bytes, silent, optimized palette, infinite loop, and three distinct nonblank representative frames.

## Completion Result

All requirements and completion gates for this milestone are satisfied. Engineering and HTML design runtime capabilities are source-neutral, executable routing and acceptance scenarios are present, native PowerPoint ownership is explicit, repository checks pass, all three CLI targets are synchronized to the complete owned set, and the tracked YapCLI GIF workflow is verified end to end.

## Completion Gate

- Every runtime reference resolves and all JSON decision assets validate.
- Engineering routes cover analysis, feature, bug, refactor, performance, and architecture.
- Design routes cover landing, dashboard, app prototype, HTML presentation, native PPTX, and hybrid delivery.
- Runtime skills contain no external source branding or update/install behavior.
- Focused tests, full tests, typecheck, build, formatter, and installation checks pass.
- Independent review has no unresolved blocking or high finding.
- The root worktree's unrelated active changes remain intact.
