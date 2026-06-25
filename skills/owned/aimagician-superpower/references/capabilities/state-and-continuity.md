# State And Continuity

Use this module when work spans multiple turns, multiple phases, parallel workers, or risky edits.

## State Model

Prefer a durable planning folder when the work is more than a single small change:

- `.planning/STATE.md` for current phase, status, next action, active assumptions, and resume notes.
- `.planning/ROADMAP.md` for phase order, dependencies, and status.
- `.planning/REQUIREMENTS.md` for stable requirements and acceptance IDs.
- `.planning/phases/<phase>/` for phase-local context, research, plan, validation, audit, and summary.

If a repo already has a planning convention, follow it instead of creating a competing one.

## Resume Protocol

1. Read state before acting.
2. Check git status and identify user edits.
3. Read the current phase context, plan, validation notes, and latest summary.
4. Identify the last completed checkpoint and the next safe action.
5. State what is known, what remains uncertain, and what you will do next.
6. Continue from the saved state instead of rediscovering solved context.

## Checkpoints

Checkpoint after any meaningful unit:

- phase context locked;
- research complete;
- plan approved or accepted;
- tests added;
- implementation slice complete;
- verification run;
- audit complete;
- handoff summary written.

Each checkpoint should include the file scope, commands run, result, known gaps, and next action.

## Pause And Recovery

- If blocked by a user decision, record the exact decision needed and the default recommendation.
- If blocked by a failing external service, record the command, error, retry status, and fallback.
- If a plan becomes stale, stop and re-plan the affected part only.
- If user edits appear in touched files, read them and work with them; do not overwrite or revert them.

## Progress Reporting

Keep progress factual:

- current phase;
- completed checkpoints;
- active blocker or risk;
- next command or edit;
- remaining verification.
