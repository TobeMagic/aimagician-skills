# Project Memory

Use project memory to recover durable context without rereading the repository history. Memory is a compact index of accepted facts and recent work, not a second specification, a transcript, or a secrets store.

## Storage

For planning-managed projects:

```text
.planning/memory/
├── memory.md
└── YYYY-MM-DD.md
```

- `memory.md` contains durable architecture, invariants, accepted preferences, recurring commands, active risks, and links to authoritative evidence.
- `YYYY-MM-DD.md` contains that day's decisions, verified progress, failed attempts worth avoiding, open questions, and the exact resume point.

For a project without `.planning`, adopt a project-local location only when the user or repository policy requests durable memory. Do not silently introduce planning infrastructure for a quick task.

## Read Policy

At a missing-context, resume, phase, milestone, or High-work start:

1. read `memory.md` when present;
2. read today's note when present;
3. read an older daily note only when the memory index, active task, or handoff links to it;
4. verify any fact that can change implementation against its authoritative source.

Do not scan every daily note. Prefer accepted requirements and current code over memory. Mark stale, disputed, or unverified entries instead of treating them as facts.

## Write Policy

Record only information that reduces future rediscovery:

- accepted decisions and the source that authorized them;
- verified architecture or behavior and its file or command evidence;
- stable project preferences;
- failed approaches with a concrete reason;
- unresolved questions and who must decide;
- current checkpoint and next action.

Never store secrets, tokens, private raw data, full conversations, speculative claims, or copied logs. Use the project's controlled secret inventory for sensitive locators and record only a non-sensitive reference.

## Promotion And Pruning

Write transient progress to today's note. Promote an item to `memory.md` only when it is durable, evidence-backed, and likely useful beyond the current task. Replace superseded items rather than accumulating contradictions. Remove or mark stale entries when code, requirements, or accepted decisions change.

Project-wide architecture and invariants still belong in the canonical project context when one exists. Memory links to that context; it does not duplicate it.

## Checkpoint

Before handoff or closure, ask:

- Did this work create a durable decision or reusable fact?
- Is the entry evidence-backed and free of secrets?
- Does it belong in daily memory, long-term memory, canonical context, or nowhere?
- Is the exact next action recoverable without loading unrelated history?

If no durable information was created, record `NONE` in the handoff rather than manufacturing memory churn.
