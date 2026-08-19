---
name: github-pr-workflow
description: Use when creating, inspecting, reviewing, updating, merging, or closing a GitHub pull request. Resolve repository-specific branch and merge protections first. Do not use for ordinary local commits. Linear through Composio is optional post-delivery tracking only.
metadata:
  related_skills:
    - composio-tool-router
compatibility:
  tools: [bash, git, gh]
  requires: GitHub CLI authenticated for the target repository
category: operate
subcategory: github
tags:
  - pull-request
  - review
  - merge
  - delivery
---

# GitHub PR Workflow

Use this skill to get verified code into the repository through the shortest path that matches its real protections. PR work follows core delivery; optional tracker, wiki, and reporting work follows the merge.

## Resolve Project Policy Once

Before the first PR in a project, establish the target branch and protections from project evidence:

1. read contribution and release documentation plus local automation configuration;
2. inspect the remote default branch and recent merged PR base branches with `gh`;
3. inspect the PR's required checks/reviews and branch protection where access permits;
4. if the evidence is absent or conflicts, ask the user which integration branch to use.

Never assume `dev`, `develop`, `main`, `master`, a reviewer-bot, or an LLM wiki. Reuse the confirmed project convention in later tasks until repository evidence or the user changes it.

## Risk-Scaled PR Path

| Work tier | Minimum PR path |
|---|---|
| Quick | Focused verification, surgical diff review, PR/merge when the project uses it, and only actual merge protections. |
| Standard | Focused tests plus a concise PR body; inspect the checks and required reviews actually configured for the target branch. |
| High | Full review/verification evidence, independent audit where required by `aimagician-superpower`, and all actual branch protections. |

CI, reviewer bots, full regression suites, wiki records, screenshots, and deployment checks are required only when repository protection, risk, user acceptance, or project policy makes them material. Tool unavailability must not block otherwise safe core delivery unless it is an enforced protection.

## Lifecycle

### 1. Prepare

- Confirm the repository, current branch, intended base, dirty state, and whether the change belongs in a PR or an already-approved target branch.
- Keep user changes separate. Do not rewrite history, reset, or clean unrelated files.
- Do not run `gh auth status` as routine PR evidence. Use a target-scoped read-only `gh` query first; inspect authentication only to diagnose an actual auth failure, and never include account names, host-file paths, token metadata, or scopes in the report.
- Inspect branch protection with the documented REST endpoint once. A 404 establishes that traditional branch protection is absent; optionally inspect repository rulesets with the documented REST endpoint once. Do not guess GraphQL schema types or repeat equivalent protection probes after a definitive response.
- Use a Linear issue ID in the title/body only when one is actually associated with the work. The title may use `[ISSUE-ID] <title>` when the ticket's canonical title is relevant.

### 2. Create Or Update

- Push only when authorized by the repository workflow or user.
- Create a PR against the resolved project base with a compact summary, verification commands/results, known risk, and relevant visual evidence.
- Link a Linear issue after the PR is created only if the task needs tracking. Read the project's Linear preference when present, then route the action through `composio-tool-router` and Composio CLI; never require Linear for merge readiness unless the repository policy does.

### 3. Inspect Merge Readiness

- Use `gh pr view`, `gh pr checks`, and review-thread inspection to identify the actual state.
- Distinguish required checks/reviews from advisory results. A configured reviewer-bot is a required gate only when branch protection or the project explicitly requires it.
- Fix confirmed blocking review or check failures. Do not treat a missing optional bot, optional wiki, or unavailable tracker integration as a reason to delay a verified PR.

### 4. Merge And Close

- Merge only when the repository's required protections pass or an authorized maintainer waives them.
- Record the merge commit and any required postmerge evidence.
- After core merge work, delegate optional Linear status/comment/closure and wiki/report administration through the appropriate skill. These actions must not reopen code delivery unless they reveal a real acceptance gap.

## Failure Handling And Checkpoint

| Trigger | First response | Fallback |
|---|---|---|
| Base branch or protection policy is unknown | Inspect repository docs, remote defaults, and current PR state once | Ask the maintainer instead of assuming a branch or bot requirement |
| `gh` cannot authenticate or required checks are unavailable | Record the exact command and limitation; keep local evidence separate | Hand off a ready-to-review branch or wait only for an enforced external protection |
| Branch-protection endpoint returns 404 or ruleset query is unavailable | Record the exact resolved protection state without speculating | Treat only local workflow configuration and observed PR checks as advisory evidence |
| Reviewed head, base, or check result changes | Invalidate affected evidence and re-inspect the actual merge gate | Stop merge and request a new review when a protected update or conflict requires it |

- Unknown base branch or merge policy: inspect repository evidence once, then ask rather than guessing.
- `gh` unavailable or unauthenticated: report the exact limitation; keep verified local delivery ready and do not fabricate PR state.
- Required check fails: diagnose the failing protection; advisory or missing optional automation does not block.
- Branch changed after review: invalidate stale diff evidence and rerun the affected check.
- Merge conflict or protected update: stop before destructive history changes and follow repository policy.

Before merge, confirm the reviewed head SHA, resolved base, actual required protections, decisive local evidence, and unresolved finding count. After merge, capture the merge SHA; optional tracker or wiki work is a separate closure step.

**CHECKPOINT:** Before creating or updating a PR, confirm repository, base, head, authorization to push, local verification, and which reported checks are actually required.

**CHECKPOINT:** Before merge, confirm current head SHA, base, required reviews/checks, unresolved thread status, merge strategy, and postmerge evidence owner.

**CHECKPOINT:** If any merge prerequisite changed after review, stop merge, refresh only the affected evidence, and route a new reviewer decision when the changed surface is material.

## Output Contract

Report repository and resolved base branch, PR URL/state, required versus advisory checks, reviews read, verification evidence, merge result, remaining blockers, and deferred post-delivery administration. Do not claim a merge protection has passed without inspecting its current state.

Read [GitHub CLI recipes](references/gh-command-recipes.md) for concrete inspection commands. Read [reviewer-bot guidance](references/reviewer-bot.md) only when a repository actually configures such a bot.

```bash
gh pr view <number-or-url> --json baseRefName,headRefName,mergeable,reviewDecision
```

```bash
gh pr checks <number-or-url> --watch=false
```

```bash
gh pr merge <number-or-url> --merge --delete-branch=false
```
