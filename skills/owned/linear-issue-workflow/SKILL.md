---
name: linear-issue-workflow
description: Use when starting, implementing, tracking, or closing a Linear issue, especially Luckee 2.0 work that needs Linear MCP context, a fresh dev-based branch, GitHub PR linkage, reviewer-bot gates, or LLM wiki activity records.
metadata:
  related_skills:
    - github-pr-workflow
    - llm-know-how-wiki
compatibility:
  tools: [bash, git, linear-mcp, python]
  requires: Configured Linear MCP connector; write access to the target repo for branch work
---

# Linear Issue Workflow

Use this skill for one issue from intake to closure. Linear is the work-state source. GitHub is the PR/review source. `LLM-know-how-wiki` is the durable audit trail.

## First Reads

- For Luckee 2.0 specifics, read [`references/luckee-2-playbook.md`](./references/luckee-2-playbook.md).
- For Linear MCP usage, read [`references/linear-mcp-chain.md`](./references/linear-mcp-chain.md).
- For branch, PR, status, and reviewer gates, read [`references/branch-pr-status-rules.md`](./references/branch-pr-status-rules.md).

## Core Rules

- Start from a Linear issue ID or URL. Do not infer scope from chat alone.
- Read the issue through Linear MCP before touching code.
- Confirm target repo, target base branch, owner, acceptance criteria, and current status.
- Default base branch is latest `origin/dev`.
- Branch name format: `<ISSUE-ID>-<short-slug>`, for example `LUC-123-fix-feishu-qr-pending`.
- One Linear issue maps to one working branch and one primary PR unless the human explicitly approves a multi-repo split.
- After implementation and verification, create a GitHub PR targeting `dev` before claiming the development handoff is complete, unless the human explicitly says not to open a PR.
- PR title must be based on the Linear issue: `[<ISSUE-ID>] <Linear issue title>`.
- Immediately after PR creation, update Linear to In Review or the repo/team's review-equivalent state and add a Linear comment with PR URL, branch, test result, and remaining risk.
- Every meaningful remote code update must add a Linear comment: pushed commits, PR updates, review fixes, changed test results, merges, and deployment verification results.
- When a branch push or merge triggers automatic deployment, resolve branch-to-environment mapping from the project `LLM-know-how-wiki` first. Then check repo CI/CD config, then live cloud config. Use defaults such as `dev` -> staging and `main`/`master` -> prod only as fallback.
- Do not mark the issue complete until PR checks, reviewer-bot, and required human review are resolved.
- After every meaningful workflow transition, record activity in the project wiki.

## Workflow

1. **Intake**
   - Resolve the Linear issue through MCP.
   - Capture identifier, title, URL, team, project, state, assignee, priority, labels, description, comments, and linked PRs.
   - Read the project wiki for context: `wiki/index.md`, relevant service pages, and Luckee 2.0 project pages.

2. **Plan**
   - State the repo, base branch, working branch, acceptance criteria, and test plan.
   - If any of these are missing, ask a narrow question before branching.
   - Move Linear to In Progress only when actual implementation starts.

3. **Branch**
   - Run `git fetch origin dev --prune`.
   - Create the branch from `origin/dev`: `git switch -c LUC-123-short-slug origin/dev`.
   - If `origin/dev` does not exist, stop and confirm the correct base branch.
   - Record the branch event in `LLM-know-how-wiki`.

4. **Implement**
   - Make scoped changes for the issue.
   - Run focused tests and relevant lint/typecheck/build commands.
   - Comment on Linear when scope changes, a blocker appears, or implementation reaches PR readiness.
   - After each push or PR update, add a Linear comment with branch, commit SHA, summary, tests, PR URL if available, and risk/follow-up.
   - Do not stop at local implementation when the work is PR-ready; continue into the PR step.

5. **PR**
   - Use `github-pr-workflow` for PR creation, checks, reviews, reviewer-bot, and merge readiness.
   - Push the issue branch and create a PR against `dev`.
   - PR title should be `[<ISSUE-ID>] <Linear issue title>`, for example `[LUC-123] Fix Feishu QR pending state`.
   - PR body should include Linear URL, summary, tests, risks, and screenshots/logs when relevant.
   - Link the PR back to Linear by native integration or a Linear comment.
   - Move Linear to In Review or the team's review-equivalent state after the PR exists.
   - Add a Linear comment containing the PR URL, branch name, summary, test result, and known follow-up/risk.
   - Record PR creation and Linear update in `LLM-know-how-wiki`.

6. **Review Gate**
   - Read CI, human reviews, and reviewer-bot output before claiming completion.
   - Fix blocking comments and re-check.
   - Comment on Linear after pushed review fixes or changed check/test results.
   - Record reviewer-bot and final review state in the wiki.

7. **Deployment Verification**
   - If merge or push triggers automatic deployment, use `gcloud-ops-workflow` to verify build/deploy provenance.
   - Determine environment from configured branch mapping in this order: project wiki deployment metadata/runbooks, repo CI/CD config, live cloud config, fallback defaults.
   - If wiki expectations conflict with CI/CD or live cloud state, report the conflict and do not silently choose one.
   - Compare expected commit, Cloud Build source revision, artifact/image digest, Cloud Run/GKE deployed revision, service URL, and deployment status.
   - Add a Linear comment with environment, expected commit, build ID/status, deployed revision/image, URL, and verdict: MATCH, MISMATCH, or UNKNOWN.
   - Record deployment verification in `LLM-know-how-wiki`.

8. **Close**
   - Only move Linear to Done or equivalent after merge or explicit human instruction.
   - Final Linear comment should summarize PR, tests, review result, and any follow-up.
   - Record final activity in the wiki.

## Wiki Activity Record

Use the related `llm-know-how-wiki` script after transitions:

```bash
python <llm-know-how-wiki>/scripts/record_activity.py \
  --wiki-root <wiki-root> \
  --operation LINEAR_WORKFLOW \
  --issue LUC-123 \
  --repo motse-ai/gke-agent-manager \
  --branch LUC-123-fix-feishu-qr-pending \
  --summary "Started LUC-123 from latest origin/dev" \
  --source https://linear.app/luckee20/issue/LUC-123
```

If the wiki is unavailable, say that the workflow audit trail could not be written and continue only if the human agrees.

## Common Mistakes

- Starting from a stale local branch instead of `origin/dev`.
- Closing Linear when code is pushed but reviewer-bot has not been read.
- Pushing commits or review fixes without adding a Linear update comment.
- Assuming deployment mapping from branch names without checking `LLM-know-how-wiki` first.
- Ignoring conflicts between wiki deployment metadata, repo CI/CD config, and live cloud triggers.
- Treating Feishu project tables as newer than Linear without evidence.
- Forgetting to write a wiki activity record after branch creation, PR creation, review checks, or closure.
