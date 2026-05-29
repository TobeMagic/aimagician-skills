# Branch, PR, and Status Rules

## Branch Naming

Use:

```text
<ISSUE-ID>-<short-slug>
```

Examples:

- `LUC-123-fix-feishu-qr-pending`
- `LUC-87-add-skill-versioning-api`

Slug rules:

- lowercase words when practical;
- hyphen-separated;
- no secrets, usernames, or temporary URLs;
- keep it short enough for GitHub UI readability.

## PR Naming

Use:

```text
[<ISSUE-ID>] <Linear issue title>
```

The title should come from the Linear issue title. Keep the issue meaning intact; only shorten if the original title is too long for a usable GitHub title.

## PR Base

Default PR base is `dev`.

Before creating the PR:

- fetch latest `origin/dev`;
- confirm the working branch is based on `origin/dev`;
- push the issue branch;
- create the PR with base `dev`.

If the repository has no `dev` branch, stop and ask for the correct base branch instead of guessing.

PR body should include:

- Linear issue URL;
- summary;
- test commands and results;
- risks or rollback notes;
- screenshots/log excerpts when user-facing or operational behavior changed.

## Post-PR Linear Update

Immediately after PR creation:

- link the PR to Linear through native integration or a Linear comment;
- move Linear to In Review or the team's review-equivalent state;
- comment with PR URL, branch name, summary, tests run, and remaining risk/follow-up;
- write a `LINEAR_WORKFLOW` activity record in `LLM-know-how-wiki`.

## Code Update Linear Comments

Comment on Linear after each meaningful remote code update:

- pushed commit(s) to the issue branch;
- PR body/title update that changes scope or risk;
- review fix pushed;
- test/check result changed;
- merge to an integration or release branch;
- automatic deployment verification completed or failed.

Use a compact format:

```text
Code update:
- branch:
- commit:
- summary:
- tests/checks:
- PR:
- risk/follow-up:
```

Do not comment for every local file edit. Comment when the update is visible remotely or changes workflow state.

## Branch-To-Environment Deployment Mapping

Automatic deployment verification must use the repository's configured mapping.

Resolve expected environment in this order:

1. Project `LLM-know-how-wiki` deployment metadata/runbooks.
2. Repository CI/CD config such as Cloud Build triggers, GitHub Actions, deploy scripts, or Terraform.
3. Live cloud config such as Cloud Build trigger branch filters and service annotations.
4. Fallback defaults.

Fallback defaults:

- `dev` -> staging;
- `main` -> prod;
- `master` -> prod.

If sources conflict, report the conflict in the Linear comment and wiki activity record. Do not silently pick the default.

After a push or merge to a deploy-triggering branch:

- use `gcloud-ops-workflow` to check Cloud Build and deployment provenance;
- compare expected commit with build source revision and deployed artifact/revision;
- comment on Linear with environment, build ID/status, deployed revision/image, URL, and MATCH/MISMATCH/UNKNOWN verdict;
- write a wiki activity record.

## Completion Gate

The issue is not complete until:

- all required child/sub-issues are terminal, or explicitly marked not required with rationale;
- child/sub-issues assigned to the current Linear user are complete;
- parent acceptance criteria and latest comments have been rechecked for unfinished requirements;
- PR exists and is linked to Linear;
- CI/checks are green or explicitly waived by a human;
- reviewer-bot output has been read;
- required human review is approved or explicitly waived;
- blocking review comments are resolved;
- final wiki activity record is written.

Use `github-pr-workflow` for the PR side of this gate.
