# Linear MCP Chain

Use the configured Linear MCP connector as the live source for issue status.

## Read Chain

1. Resolve issue by identifier or URL.
2. Fetch issue fields: identifier, title, URL, team, project, state, assignee, priority, labels, estimate, branch name, description, comments, and attachments metadata.
3. Fetch parent issue and child/sub-issues, including each child assignee, state, title, URL, blockers, and linked PRs.
4. Fetch linked PRs or branch metadata if the connector exposes them.
5. Summarize the current state before changing files.

Do not store signed attachment URLs or private upload tokens in the wiki.

## Write Chain

Use Linear MCP updates for:

- state changes, such as In Progress or In Review;
- comments with branch, PR, test, blocker, and closure summaries;
- linking PRs when native GitHub integration did not do it automatically.
- creating child issues when a large issue is intentionally split;
- assigning new child issues to the current Linear user by default unless another owner is specified;
- linking child issues back to their parent.

Before updating Linear, state the exact update you will make.

## Failure Handling

- If MCP is unavailable, do not fake issue status from memory.
- If issue details are incomplete, ask for the missing issue URL or acceptance criteria.
- If a Linear update fails, record the failure in the wiki activity log and continue with local/GitHub work only when safe.
