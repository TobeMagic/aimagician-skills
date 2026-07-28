# Code Agent Engineering

## Operating Loop

1. Reconcile the request with repository state and project sources.
2. Explore enough context to identify owners, contracts, and blast radius.
3. Lock behavior and test seams before broad edits.
4. Implement the smallest end-to-end slice.
5. Run narrow then broad verification.
6. Review specification compliance before general quality.
7. Audit original requirements before completion.

## Repository Safety

- Read before editing and preserve unrelated user changes.
- Avoid destructive Git commands without explicit authorization.
- Use isolated worktrees for delegated writes or risky integration.
- Stage and commit only intended files.
- Do not bypass hooks or tests merely to produce a commit.
- Never expose secrets from configuration, history, logs, or environment.

## Code Quality Contract

Require local conventions, coherent ownership, explicit failure behavior, maintainability, security, performance proportional to risk, and observable tests. Avoid speculative abstraction, redundant comments, placeholder behavior, broad unrelated refactors, and tests that only replay mocks.

## Tool And Agent Use

Delegate broad exploration or mechanical checks when appropriate, but keep requirement reconciliation and architecture decisions with the controller. Worker prompts must include repository path, review point, write scope, required skills, tests, Git policy, and forbidden actions.

## Completion

Tests passing is evidence, not requirement coverage. Trace each accepted requirement to implementation, integration, verification, user-facing acceptance when relevant, independent review, and handoff.

