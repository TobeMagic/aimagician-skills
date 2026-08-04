# Owner Skill Sync And Distillation

## Goal

Keep Codex and OpenCode synchronized with the active `skills/owned` set, remove unowned runtime Skill directories during bootstrap reconciliation, preserve Codex system-managed Skill storage, and add three clean reusable distillation/quality Skills.

## Checklist

- [x] Add a clean long-form knowledge-to-Skill distillation owner Skill.
- [x] Add a clean evidence-grounded reasoning and decision-advisor distillation owner Skill.
- [x] Add a clean baseline, independent comparison, regression, and reversible Skill optimization owner Skill.
- [x] Add taxonomy and formatter coverage for all three Skills.
- [x] Remove author, promotion, installer, and upstream identity material from the owner Skill bodies.
- [x] Prune unowned direct Skill directories during `bootstrap` reconciliation.
- [x] Preserve Codex `.system` built-in Skill storage, including during `--clean`.
- [x] Keep additive `install` behavior unchanged.
- [x] Sync Codex and OpenCode and verify both target doctors are healthy.
- [x] Run typecheck, build, formatter, focused tests, and full test suite.

## Evidence

- `npm run typecheck` passed.
- `npm run build` passed.
- `node dist/cli/index.js format-skills --check --json` passed for 28 owner Skills.
- `npm test` passed: 27 files, 164 tests.
- Real bootstrap synchronized 28 owner Skills to Codex and OpenCode.
- Real doctor reported both targets healthy with 28 managed and 28 detected owner Skills and no issues.
- Codex `.system` remained present and was excluded from owner cleanup.
- Direct `bootstrap --clean` regression coverage confirms non-owner Codex Skills are removed while `.system` and owned Skills remain.

## Boundary

The Codex `.system` directory is controlled by Codex and is not part of the owner set. It is intentionally preserved because deleting it removes or destabilizes Codex built-in capabilities. All other direct Skill directories under selected target Skill roots are reconciled to the active owner/explicitly enabled asset set.
