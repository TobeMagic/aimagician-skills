---
name: memory-pointer
description: Where to read and write user and project memory
alwaysApply: true
---

# Memory Pointer

Two stores, both optional:

- User: ~/.skillbird/memory/memory.md and ~/.skillbird/memory/YYYY-MM-DD.md
- Project: .planning/memory/memory.md and .planning/memory/YYYY-MM-DD.md

On resume, missing context, or High work: read user memory.md, then project memory.md, then today's notes if present. Do not scan all daily notes.

Authority order: accepted requirements, current code, runtime evidence, then memory. Memory never overrides those.

Write only durable facts that prevent rediscovery: accepted decisions, stable preferences, failed approaches with a reason, the exact resume point. Promote daily notes into memory.md only when they will matter after today.

Never store secrets, tokens, cookies, private raw data, or full transcripts.

If a store is missing, continue without creating planning infrastructure for a Quick task. Create the path only when the user wants durable memory.
