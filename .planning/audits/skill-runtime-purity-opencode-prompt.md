# Independent Skill Runtime-Purity And Behavior Audit

## Role

You are a fresh independent reviewer. Do not modify files, install dependencies, commit, push, or change configuration. Read the required Skills before judging:

- `skills/owned/skill-optimizer/SKILL.md`
- `skills/owned/aimagician-superpower/SKILL.md`
- `skills/owned/agent-workstream-orchestrator/SKILL.md`
- `skills/owned/cli-agent-delegator/SKILL.md`

Use the Darwin/skill-optimizer controlled-comparison method. The baseline is exact Git ref `origin/master` (`a1d2d182b4c453f59fbc0a8dbb40cf783af2b826`). The treatment is the current frozen review worktree. Compare baseline files using `git show origin/master:<path>`; do not switch branches or mutate the worktree.

## Accepted Requirement

Audit `USR-20260811-001` and `.planning/tasks/skill-runtime-purity-memory.md` one item at a time:

1. Archive active `pptx`, `modelscope_imagegen`, `mcp-builder`, and `linear-issue-workflow`; remove them from active taxonomy, README routing, and installation output while preserving recoverable archives.
2. Remove every Skill-local `evals/` directory. Preserve useful quality evidence under repository-level `quality/skill-evals/`. Runtime capability must not depend on that quality tree. Any data genuinely required at runtime must have a capability-oriented `assets/` path.
3. Replace `parallel-worktree-pr-flow` with clean, provider-neutral `agent-workstream-orchestrator`. It must support independent read-only sessions, short bounded test/Git/report/research tasks, difficult Codex work, OpenCode work, isolated writes, optional worktrees, integration/PR modes, event-based waiting, durable session state, and controller validation. Worktree/PR must be optional, not universal.
4. Move Linear policy out of a general Skill into `.planning/preferences/linear.md`. It remains Composio CLI only, optional to core delivery, and must not assume MCP, branch names, reviewer bots, IDs, or merge policy.
5. Add `aimagician-superpower` project memory using `.planning/memory/memory.md` and `.planning/memory/YYYY-MM-DD.md`, bounded reads, authority ordering, evidence promotion, stale-entry handling, and no-secret rules.
6. Actually apply Darwin to optimize core Skills, including `aimagician-superpower`, without source branding, project policy, dead references, or capability regression.
7. Preserve the original dirty user worktree; this implementation must be isolated from latest `origin/master`.

## Locked Behavioral Scenarios

For each scenario, compare what the baseline Skill system instructs an ordinary model to do with what the treatment instructs. Judge observable routing and execution, not prose volume.

### Scenario A: Mixed large feature

One architecture decision, two independent repository explorations, one bounded test run, and two disjoint write lanes. Expected treatment: controller keeps macro decisions; explorations and tests use tracked fresh sessions; write lanes use isolation; worktrees only for concurrent writes; one parent-level integration and acceptance check.

### Scenario B: Short coupled edit

One known function and adjacent test depend on one unresolved behavior choice. Expected treatment: resolve the choice, keep work in controller, no forced phase, registry, worktree, PR, or independent audit.

### Scenario C: Linear closure

After verified delivery, update Linear. Expected treatment: read project preference, route through Composio CLI, no Linear MCP or active Linear Skill, no assumed `dev`/reviewer bot, and do not reopen core delivery unless new evidence reveals a requirement gap.

### Scenario D: Missing-context resume

Expected treatment: read canonical planning authority, long-term memory, today's note, and only explicitly relevant older memory; do not scan all notes or let memory override requirements/code/runtime evidence.

### Scenario E: Long worker run

The worker is slow but emits logs/tool/file progress. Expected treatment: keep waiting by events; do not stop at a fixed elapsed duration; intervene only on explicit failure, scope drift, or repeated no-progress.

## Evidence Already Produced

- `npm run typecheck`: PASS.
- `npm run build`: PASS.
- `npm test`: 29 files, 178 tests PASS.
- focused Skill and acceptance suite: 8 files, 55 tests PASS.
- affected PowerPoint path suite: 67 PASS, 1 skipped.
- full PowerPoint suite first run: 861 PASS, 4 skipped; 24 failures and 23 errors all reported missing `skills/owned/window-pptx/scripts/node/node_modules/pptxgenjs` in the clean worktree.
- after linking the unchanged, previously installed skill-local dependency tree, the complete failed/error file set reran as 74 PASS.
- `skillbird format-skills --check`: 24 Skills, no issues.
- `git diff --check`: PASS.

Verify representative commands and files yourself. Distinguish environmental dependency evidence from treatment regressions.

## Required Output

Return:

1. model and session identity;
2. one matrix row per requirement: `PASS`, `FAIL`, or `NOT_RUN`, with concrete paths/commands;
3. baseline versus treatment matrix for Scenarios A-E, with whether behavior measurably improved, stayed equal, or regressed;
4. runtime-purity check, including any Skill-local `evals/`, dead progressive-disclosure references, active archived IDs, or runtime dependency on `quality/`;
5. findings using exactly `Blocker`, `Important`, or `Nitpick` with file evidence;
6. Darwin effectiveness score from 0-10 for the treatment and rationale;
7. final verdict `PASS` only if no Blocker or Important remains and every requirement is evidenced.

Do not accept green tests as a substitute for requirement coverage. Do not report historical `.planning` references as active routing defects unless current runtime/catalog code uses them.
