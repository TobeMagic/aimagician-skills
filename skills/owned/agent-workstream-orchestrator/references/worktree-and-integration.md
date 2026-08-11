# Worktree And Integration

Use a worktree only when a write lane needs isolation from another active writer, must preserve a long-running branch, or will be integrated independently. Read-only sessions and short exclusive writes do not need one.

## Setup

1. Freeze the base commit and inspect existing worktrees and dirty files.
2. Assign a unique branch, worktree path, and write scope.
3. Reserve shared surfaces for one integration owner.
4. Validate registry overlap before creating worktrees.
5. Never move, reset, or clean another worktree to make setup convenient.

## Integration Order

Integrate dependency providers before consumers, then shared registries/configuration, then user-facing wiring and documentation. Inspect each diff before merge. Rebase or merge according to repository policy; do not assume a base branch name or merge method.

Run lane checks before integration and parent-level checks after all shared wiring is present. A lane commit proves only its bounded output.

## Pull Requests

Use PRs when required by repository policy, user instruction, protected branches, or independent review. Direct local integration is acceptable when the repository workflow permits it. Never create a PR merely because a worktree exists.

## Cleanup

Remove branches and worktrees only after accepted integration and only when ownership is clear. Cleanup is a separate explicit action; helper scripts in this Skill do not delete worktrees automatically.
