# Session Lifecycle

## Prompt Packet

Every worker prompt contains:

1. parent goal and worker objective;
2. source-of-truth paths, relevant excerpts, and current commit;
3. Skills the worker must read and why;
4. allowed reads, exact write scope, and prohibited actions;
5. known commands and interfaces so preflight is not repeated;
6. expected output, acceptance evidence, and stop conditions;
7. uncertainty rule: report material ambiguity instead of inventing a decision.

## States

`planned -> ready -> running -> waiting | blocked | failed | handoff -> integrated -> closed`

- `waiting` means the process is healthy but awaiting an external event.
- `blocked` requires a named external dependency or unresolved material decision.
- `handoff` means worker execution ended; it is not integration or completion.
- `closed` requires parent-level acceptance.

Record `last_activity_at` whenever a log event, command result, file update, or explicit progress message arrives. Continue waiting while meaningful events advance. Use an inactivity investigation, not a fixed task-duration cutoff.

## Resume

On resume, read the registry entry and handoff before opening worker logs. Confirm the session still exists, the base commit has not invalidated its assumptions, and the write scope remains exclusive. Resume from the last accepted checkpoint; do not repeat finished exploration.

## Handoff

Require objective status, changed files, commands and results, decisions, assumptions, unresolved findings by severity, residual risk, session identity, commit or diff reference when applicable, and the next controller action. Reject a handoff that only says the task is done.
