# Linear MCP Chain

Use the configured Linear MCP connector as the live source for issue status.

## Read Chain

1. Resolve issue by identifier or URL.
2. Fetch issue fields: identifier, title, URL, team, project, state, assignee, priority, labels, estimate, branch name, description, comments, and attachments metadata.
3. Fetch linked PRs or branch metadata if the connector exposes them.
4. Summarize the current state before changing files.

Do not store signed attachment URLs or private upload tokens in the wiki.

## Write Chain

Use Linear MCP updates for:

- state changes, such as In Progress or In Review;
- comments with branch, PR, test, blocker, and closure summaries;
- linking PRs when native GitHub integration did not do it automatically.

Before updating Linear, state the exact update you will make.

## Failure Handling

- If MCP is unavailable, do not fake issue status from memory.
- If issue details are incomplete, ask for the missing issue URL or acceptance criteria.
- If a Linear update fails, record the failure in the wiki activity log and continue with local/GitHub work only when safe.

