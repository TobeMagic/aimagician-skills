# Memory, Context, And Continuity

## Memory Layers

Define each layer independently:

| Layer | Typical content | Lifetime |
|---|---|---|
| Turn | Current request and tool result | One response |
| Session | Decisions, unresolved work, temporary preferences | Current session |
| Project | Durable conventions, architecture, accepted requirements | Project lifetime |
| User | Explicit reusable preferences | Until corrected or deleted |

For every layer specify owner, write trigger, read trigger, retention, correction, deletion, sensitivity, and provenance.

Use `../assets/templates/memory-policy.md`.

## Write Discipline

Store decisions and durable facts, not unrestricted transcripts or hidden reasoning. Do not infer sensitive traits. Require explicit user intent for personal preference memory where appropriate.

Resolve conflicts using recency, authority, specificity, and evidence. A newer explicit correction supersedes an older inferred preference.

## Context Loading

- Load stable high-authority context first.
- Discover specialized context lazily.
- Use representative slices before broad retrieval.
- Track what was omitted and why.
- Mark facts, inference, and unknowns.
- Preserve citations or source paths through summarization.

## Compression And Resume

A continuity summary retains:

- current objective and accepted boundary;
- decisions and their reasons;
- source-of-truth locations;
- completed work and evidence;
- unresolved requirements, risks, and blockers;
- current state and exact next action.

Never claim completion from a summary alone. Reload decisive sources and current runtime state after resume.

