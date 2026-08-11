# Runtime-Pure Skills And Durable Project Memory

## Control

- User source: `USR-20260811-001`
- Parent milestone: `v6.1`
- Parent phase: `49`
- Task class: controlled off-phase capability upgrade
- Return checkpoint: Phase 49 workflow completion gate and terminal handoff
- Forbidden scope: private assets and active user worktrees. Window-PPTX changes
  are limited to relocating evaluation-only data and repointing those exact
  runtime/test references; no presentation capability or output behavior may
  change.

## Goal

Ship a smaller, runtime-pure owner Skill set whose project policy, evaluation
fixtures, and durable memory live outside installed Skill packages, while core
engineering Skills gain measurable routing, failure, checkpoint, and
multi-session orchestration capability.

## Requirements

- **SKILL-PURE-01:** Installed Skills contain reusable capability instructions,
  required references, scripts, and templates only; no project-specific Linear,
  branch, reviewer, deployment, or repository policy is shipped globally.
- **SKILL-ARCHIVE-01:** `pptx`, `modelscope_imagegen`, `mcp-builder`, and
  `linear-issue-workflow` leave the active owner set, taxonomy, README routing,
  and bootstrap output while remaining recoverable under `skills/archived/`.
- **SKILL-EVAL-01:** No Skill under `skills/` contains an `evals/` directory;
  useful fixtures and behavior contracts live under `quality/skill-evals/` and
  continue to participate in repository tests.
- **SKILL-ORCH-01:** The multi-agent orchestration Skill routes independent
  read-only sessions, bounded execution sessions, isolated write worktrees,
  and integration/PR flows by task coupling and risk, and tracks provider,
  session, scope, status, evidence, and handoff.
- **SKILL-MEM-01:** `aimagician-superpower` defines optional project memory at
  `.planning/memory/memory.md` and daily notes at
  `.planning/memory/YYYY-MM-DD.md`, with bounded reads, evidence promotion,
  redaction, and no-secret rules.
- **SKILL-OPT-01:** Darwin static baselines and controlled behavior scenarios
  cover the core workflow Skills; accepted edits improve observable routing or
  execution and introduce no runtime/source-neutrality regression.

## Darwin Baseline

| Skill | Static score | Dominant gaps |
|---|---:|---|
| aimagician-superpower | 60.8 | failure branches, explicit checkpoints |
| parallel-worktree-pr-flow | 50.4 | trigger, failure handling, checkpoints, worktree overbinding |
| cli-agent-delegator | 52.4 | ordered workflow, failure branches, checkpoints |
| skill-creator | 48.8 | missing eval resource, failure handling, checkpoints |
| composio-tool-router | 51.2 | actionable commands, failure handling, checkpoints |
| github-pr-workflow | 51.0 | actionable commands, failure handling, checkpoints |
| llm-know-how-wiki | 48.5 | trigger precision, workflow clarity, sibling routing, failures |

## Darwin Treatment

| Skill | Baseline | Treatment | Delta |
|---|---:|---:|---:|
| aimagician-superpower | 60.8 | 65.6 | +4.8 |
| cli-agent-delegator | 52.4 | 57.2 | +4.8 |
| parallel-worktree-pr-flow -> agent-workstream-orchestrator | 50.4 | 60.8 | +10.4 |
| skill-creator | 48.8 | 52.8 | +4.0 |
| composio-tool-router | 51.2 | 56.6 | +5.4 |
| github-pr-workflow | 51.0 | 56.4 | +5.4 |
| llm-know-how-wiki | 48.5 | 58.8 | +10.3 |

All referenced resources resolve. Independent behavior review rated Darwin
effectiveness 7/10 and found Scenarios A-E improved, with no Blocker or
Important finding. The completed comparison is stored in
`docs/audits/skill-runtime-purity-memory-2026-08-11.md`.

## Behavior Scenarios

1. A large feature contains one architecture decision, two independent
   repository explorations, one bounded test run, and two disjoint write lanes.
   The workflow must keep macro decisions with the controller, start tracked
   sessions for independent context, and use worktrees only for write lanes.
2. A short one-file documentation correction must not trigger phase planning,
   a worktree, a session registry, or an independent completion audit.
3. A project asks to update Linear after delivery. The runtime workflow must
   discover project preference, route generic SaaS work through Composio, and
   avoid assuming a Linear Skill, MCP, `dev` branch, or reviewer bot.
4. A resumed task with missing chat context must read the main project memory,
   today's note, and relevant planning source without scanning every daily log
   or treating unverified notes as authority.
5. A long-running delegated worker must continue while events show progress,
   stop on repeated no-progress or scope drift, and retry with a corrected
   bounded prompt instead of relying on a fixed elapsed-time cutoff.

## Acceptance Evidence

- No `skills/owned/*/evals` directories.
- Formatter, taxonomy, package-copy, focused Skill tests, typecheck, build, and
  full tests pass.
- Bootstrap/doctor report only the reduced owner set for Codex and OpenCode.
- Darwin static scores improve or every non-improving edit is rejected.
- At least one full model/tool behavior comparison and one independent final
  OpenCode audit complete with no unresolved Blocker or Important finding.

## Final Evidence

- Independent reviewer: `opencode/deepseek-v4-flash-free`, session
  `ses_00fbde4bdffeobq00tJe65wSYt`; final verdict `PASS`, Blocker 0,
  Important 0, Nitpick 3 before cleanup.
- `npm run typecheck`: pass.
- `npm run build`: pass.
- `npm test`: 29 files, 178 tests passed.
- Skillbird formatter: 24 active Skills, no issues.
- Window-PPTX affected suite: 67 passed, 1 skipped. The full suite passed all
  861 dependency-independent tests; the dependency-backed failures were rerun
  with the existing local `pptxgenjs` tree and all 74 previously failing/error
  cases passed.
- `git diff --check`: pass.
- Installation sync and doctor evidence are recorded after the final source
  commit so installed manifests can be compared to that exact revision.
