# Audit And Closure

Use this module at phase end, milestone end, review closeout, or before handing work back to the user.

## Audit Checklist

Check the result against:

- original objective;
- locked scope and non-goals;
- requirements and acceptance IDs;
- research assumptions;
- plan tasks;
- validation evidence;
- user-visible behavior;
- regression risk;
- unresolved TODOs;
- generated or installed artifacts;
- documentation and handoff needs.

## Gap Handling

Classify each gap:

- blocker: must be fixed before completion;
- follow-up: should be tracked, but current objective is usable;
- deferred: explicitly out of scope or postponed by user decision;
- invalid: no longer relevant because the plan changed.

Do not hide gaps in a cheerful summary. State what remains and what proof exists.

## Closure Summary

A useful closeout includes:

- what changed;
- why it satisfies the objective;
- files changed;
- verification run and result;
- manual checks performed;
- checks not run;
- residual risk;
- next recommended action.

## Learning Extraction

When work reveals reusable context, preserve it:

- update project docs or wiki;
- record command patterns;
- record integration gotchas;
- add regression tests;
- update planning state;
- capture follow-up tasks.

## Cleanup

Before final response:

- check git status;
- remove temporary files you created unless they are useful artifacts;
- ensure generated outputs are intended;
- ensure local-only reference material is ignored or filtered;
- confirm installed targets contain only active managed skills when installation was part of the task.
