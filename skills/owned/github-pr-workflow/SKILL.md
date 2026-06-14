---
name: github-pr-workflow
description: Use when creating, inspecting, reviewing, updating, or closing
  GitHub pull requests, especially when PR readiness depends on CI, reviewer-bot
  output, review comments, Linear links, or LLM wiki activity records.
metadata:
  related_skills:
    - linear-issue-workflow
    - llm-know-how-wiki
compatibility:
  tools:
    - bash
    - git
    - gh
    - python
  requires: GitHub CLI authenticated for the target repo
category: operate
subcategory: github
tags:
  - pull-request
  - review
---

# GitHub PR Workflow

Use this skill for PR creation, review status, CI, reviewer-bot output, and merge readiness. Use `linear-issue-workflow` for Linear state changes.

## First Reads

- For reviewer-bot gates, read [`references/reviewer-bot.md`](./references/reviewer-bot.md).
- For `gh` commands, read [`references/gh-command-recipes.md`](./references/gh-command-recipes.md).

## Core Rules

- Use `gh` for GitHub state. Use local `git` for local branch state.
- Always identify repo and PR number or URL before querying.
- Do not say a PR is ready until checks, reviewer-bot, and required reviews have been inspected.
- Link PRs back to Linear when the work came from a Linear issue.
- For Linear issue work, default PR base is `dev` and PR title is `[<ISSUE-ID>] <Linear issue title>` unless the human explicitly provides a different base or title.
- Record PR creation, review checks, merge readiness, and closure in `LLM-know-how-wiki`.

## PR Lifecycle

1. **Create**
   - Confirm current branch and base branch.
   - Use base `dev` when creating a PR for Linear issue work unless explicitly overridden.
   - Use title `[ISSUE-ID] <Linear issue title>` when a Linear issue exists.
   - Include Linear URL, summary, tests, risks, and screenshots/logs as relevant.
   - Return the PR URL so `linear-issue-workflow` can update Linear status and comment with the link.

2. **Inspect**
   - Run `gh pr view` for title, state, author, base/head refs, body, reviews, review decision, and URL.
   - Run `gh pr checks`.
   - Fetch comments and review threads when there are unresolved concerns.

3. **Reviewer-Bot Gate**
   - Search PR comments and reviews for the configured reviewer-bot identity.
   - Treat failed bot output, blocking comments, or missing required bot output as not ready.
   - Summarize bot result before claiming completion.

4. **Fix Loop**
   - Apply fixes for blocking review comments.
   - Push updates.
   - Re-run or re-check CI and reviewer-bot.
   - Record each significant review cycle in the wiki.

5. **Close**
   - Merge only when checks, reviewer-bot, and required human reviews pass or are explicitly waived.
   - After merge, update Linear through `linear-issue-workflow` when applicable.
   - Write a final wiki activity record.

## Wiki Activity Record

Use the related `llm-know-how-wiki` recorder:

```bash
python <llm-know-how-wiki>/scripts/record_activity.py \
  --wiki-root <wiki-root> \
  --operation GITHUB_PR_WORKFLOW \
  --issue LUC-123 \
  --pr https://github.com/motse-ai/gke-agent-manager/pull/12 \
  --repo motse-ai/gke-agent-manager \
  --summary "Checked PR #12: CI passed, reviewer-bot approved"
```

If the wiki record fails, report that failure instead of silently dropping the audit trail.

## Common Mistakes

- Checking only `gh pr checks` and ignoring reviewer-bot comments.
- Assuming a linked Linear issue is closed by PR creation.
- Merging without reading unresolved review threads.
- Forgetting to record the PR/review state into the wiki.
