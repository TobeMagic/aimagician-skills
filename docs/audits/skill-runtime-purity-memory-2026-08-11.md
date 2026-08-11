# Skill Runtime Purity And Memory Audit

Date: 2026-08-11

## Scope

This audit covers `USR-20260811-001`: archive obsolete active Skills, move
evaluation corpora out of runtime packages, replace the worktree-specific flow
with provider-neutral workstream orchestration, add bounded project memory,
and optimize core Skills with the Darwin protocol.

## Independent Review

- Reviewer: `opencode/deepseek-v4-flash-free`
- Session: `ses_00fbde4bdffeobq00tJe65wSYt`
- Frozen source: worktree based on
  `a1d2d182b4c453f59fbc0a8dbb40cf783af2b826`
- Decision: `PASS`
- Findings before final nitpick cleanup: Blocker 0, Important 0, Nitpick 3

The reviewer mapped every requirement to source and tests, reproduced the
Darwin baseline scores, compared five routing scenarios, and independently
reran the repository verification. The completed behavior review rated Darwin
effectiveness 7/10: all static scores improved and all five scenarios improved;
the cap reflects that behavior was assessed from routing contracts and scenario
tests rather than a repeated multi-model experiment.

## Requirement Results

| Requirement | Result | Main evidence |
|---|---|---|
| Archive obsolete active Skills | PASS | archived trees, taxonomy, README, acceptance tests |
| Remove Skill-local eval directories | PASS | zero `evals/` directories under `skills`; quality corpora retained |
| Provider-neutral workstream orchestration | PASS | routing, lifecycle, registry, isolation, and integration contracts |
| Project-local Linear policy | PASS | `.planning/preferences/linear.md`; Composio-only routing |
| Bounded project memory | PASS | memory capability, templates, project and daily memory |
| Darwin optimization without regression | PASS | all seven scores improved; references resolve; behavior scenarios improved |
| Preserve user work | PASS | isolated worktree from latest `origin/master` |

## Darwin Comparison

| Skill | Baseline | Treatment |
|---|---:|---:|
| aimagician-superpower | 60.8 | 65.6 |
| cli-agent-delegator | 52.4 | 57.2 |
| parallel-worktree-pr-flow -> agent-workstream-orchestrator | 50.4 | 60.8 |
| skill-creator | 48.8 | 52.8 |
| composio-tool-router | 51.2 | 56.6 |
| github-pr-workflow | 51.0 | 56.4 |
| llm-know-how-wiki | 48.5 | 58.8 |

Behavior scenarios improved for mixed large features, short coupled edits,
Linear closure, missing-context resume, and long-running delegated workers.

## Verification

- `npm run typecheck`: pass
- `npm run build`: pass
- `npm test`: 29 files, 178 tests passed
- focused acceptance suite: 41 tests passed
- runtime-purity focused suite: 24 tests passed
- `skillbird format-skills --check`: 24 Skills, no issues
- affected Window-PPTX tests: 67 passed, 1 skipped
- full Window-PPTX dependency-independent coverage: 861 passed, 4 skipped
- all 74 dependency-backed failures/errors passed when rerun with the existing
  local `pptxgenjs` dependency tree
- `git diff --check`: pass

## Residual Risk

The Window-PPTX full suite requires its skill-local Node dependencies, which
are intentionally not committed. Clean environments must install that package
before running dependency-backed deck generation tests. This predates and is
independent of the evaluation-data relocation.
