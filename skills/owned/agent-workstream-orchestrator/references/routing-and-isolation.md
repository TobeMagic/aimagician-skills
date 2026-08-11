# Routing And Isolation

## Partition Test

A candidate lane is independent only when all are explicit:

- its output can be accepted without private reasoning from another active lane;
- its write scope does not overlap another writer;
- its dependencies are available as files, commits, commands, or recorded decisions;
- its failure can be retried or abandoned without corrupting shared state;
- its acceptance can be checked independently before integration.

If one condition fails, narrow the lane or keep it in the controller.

## Coupling Score

Escalate isolation as coupling increases:

| Signal | Consequence |
|---|---|
| Read-only and no shared state | Fresh session only |
| Bounded writes to exclusive paths | Fresh session with exact write scope |
| Git changes that may outlive the session | Branch; add a worktree when controller state is dirty or concurrent |
| Multiple lanes touch one registry, schema, lockfile, or migration | One integration owner edits the shared surface |
| Architecture, security, persisted data, or user-visible contract is unresolved | Controller decides before delegation |

## Agent Choice

- Use OpenCode for broad evidence collection, research, tests, Git checks, reports, and bounded mechanical work.
- Use Codex for difficult implementation, architecture-sensitive refactors, or work requiring sustained local reasoning.
- Use the controller for final tradeoffs and shared high-coupling changes.
- Split exploration from implementation when the explorer's context would otherwise dominate the implementer.

The agent name does not determine trust. Validate outputs by consequence: low-risk facts can be sampled; architecture, security, data, and completion claims require primary evidence.

## Write Safety

Every write lane declares allowed paths and forbidden shared surfaces. A worker may not broaden scope, rewrite unrelated user changes, or clean the parent worktree. If two lanes need the same file, assign that file to the integration owner or run the lanes sequentially.
