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

1. Reload the active workflow skill instructions when they are not already in context.
2. Read state before acting.
3. Read workflow and planning source-of-truth files: `.planning/STATE.md`, `.planning/ROADMAP.md`, current phase context, discussion logs, research, plan, validation notes, audit notes, and latest summary.
4. Read project docs that define behavior: `README*`, `docs/`, ADRs, contributor docs, architecture docs, API docs, and repo-specific workflow docs.
5. Read the project knowledge base when present: `llm-know-how-wiki`, `.llm-know-how-wiki`, `llm-wiki`, `.llm-wiki`, `wiki/`, or the documented wiki location.
6. Check git status and identify user edits.
7. Identify the last completed checkpoint and the next safe action.
8. State what is known, what remains uncertain, what source was unavailable, and what you will do next.
9. If planning, docs, wiki, or current user instructions conflict in a way that affects implementation, confirm before planning or editing.
10. Continue from the saved state instead of rediscovering solved context or skipping prior decisions.

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
