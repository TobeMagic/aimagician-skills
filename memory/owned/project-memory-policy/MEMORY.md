---
name: project-memory-policy
description: Read and write policy for user and project memory stores
---

# Memory Policy

Memory is a compact index of accepted facts and recent work. It is not a second specification, a transcript, or a secrets store.

## Stores

User store:

```text
~/.skillbird/memory/
├── memory.md
└── YYYY-MM-DD.md
```

Project store, for planning-managed repositories:

```text
.planning/memory/
├── memory.md
└── YYYY-MM-DD.md
```

- `memory.md` holds durable architecture, invariants, accepted preferences, recurring commands, active risks, and links to evidence.
- `YYYY-MM-DD.md` holds that day's decisions, verified progress, failed attempts worth avoiding, open questions, and the exact resume point.

Do not silently create `.planning` for a Quick task. Adopt a project-local store only when the user or repository policy wants durable memory. Bootstrap may write templates into a missing store; it must not overwrite existing live files.

## Read Policy

At a missing-context, resume, phase, milestone, or High-work start:

1. read `~/.skillbird/memory/memory.md` when present;
2. read `.planning/memory/memory.md` when present;
3. read today's note in each store when present;
4. read an older daily note only when the memory index, active task, or handoff links to it;
5. verify any fact that can change implementation against its authoritative source.

Do not scan every daily note. Prefer accepted requirements and current code over memory. Mark stale, disputed, or unverified entries instead of treating them as facts.

## Write Policy

Record only information that reduces future rediscovery:

- accepted decisions and the source that authorized them;
- verified architecture or behavior and its file or command evidence;
- stable preferences (user store for cross-project habits, project store for this repository);
- failed approaches with a concrete reason;
- unresolved questions and who must decide;
- current checkpoint and next action.

Never store secrets, tokens, cookies, private raw data, full conversations, speculative claims, or copied logs.

## Promotion And Pruning

Write transient progress to today's note. Promote an item to `memory.md` only when it is durable, evidence-backed, and likely useful beyond the current task. Replace superseded items rather than accumulating contradictions. Remove or mark stale entries when code, requirements, or accepted decisions change.

## Templates

- [`templates/user-memory.md`](templates/user-memory.md)
- [`templates/project-memory.md`](templates/project-memory.md)
- [`templates/daily-memory.md`](templates/daily-memory.md)
