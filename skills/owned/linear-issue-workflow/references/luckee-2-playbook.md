# Luckee 2.0 Linear Playbook

Use this reference when a Linear issue belongs to Luckee 2.0 or uses `LUC-*`.

## Evidence Priority

1. Linear MCP live issue data for current issue state.
2. GitHub PR/check/review data for implementation state.
3. `LLM-know-how-wiki/wiki/project/luckee_2_0_status.md` for compiled project context.
4. Feishu and PRD snapshots for product or historical context.

If Linear and Feishu disagree, do not silently merge them. Call out the conflict.

## Issue Intake Checklist

- Issue ID and URL, for example `LUC-123`.
- Title and current state.
- Team and project.
- Assignee and priority.
- Acceptance criteria or expected behavior.
- Target repo and likely service page in the wiki.
- Existing linked branch or PR.
- Risk area: agent runtime, frontend, GKE/OpenClaw, Feishu IM, ads, data-provider, or product shell.

## Branch Rule

Default base is the latest remote `dev`:

```bash
git fetch origin dev --prune
git switch -c LUC-123-short-slug origin/dev
```

If the repo has no `origin/dev`, stop and confirm whether to use `develop`, `main`, or another branch. Do not guess.

## Status Rule

- Backlog/Todo: planning only.
- In Progress: implementation has started on a branch.
- In Review: PR is open and ready for review.
- Done: PR is merged or human explicitly says to close.

Do not move to Done while CI, reviewer-bot, or required reviews are unresolved.

## Wiki Records To Write

Record these as `LINEAR_WORKFLOW`:

- issue intake completed;
- branch created from latest `origin/dev`;
- scope changed or blocker discovered;
- PR created and linked;
- reviewer-bot checked;
- PR merged or Linear closed.

