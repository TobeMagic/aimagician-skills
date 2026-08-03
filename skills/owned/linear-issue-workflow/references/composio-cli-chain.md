# Linear Through Composio CLI

Load `composio-tool-router` first. Keep schemas on demand and use the exact CLI syntax exposed by the installed version.

## Read Chain

1. Discover the Linear toolkit: `composio tools list linear --limit 50`.
2. Narrow by intent when needed: `composio tools list linear --query "get issue" --limit 20`.
3. Inspect only the selected action: `composio tools info <tool-slug>`.
4. Execute the smallest read action with the known issue ID.
5. Reconcile material ticket facts with current user decisions before planning.

## Post-Delivery Write Chain

1. Resolve the current issue and required children.
2. Select the smallest status, comment, or link action and inspect its schema.
3. Build a payload from verified PR URL, merge SHA, tests, and residual risk.
4. Run the action with `--dry-run`.
5. Execute only under direct confirmation or task-scoped delegated-closure authorization.
6. Read the issue back and report the resulting state/comment/link.

No Linear MCP command, schema, or background server is part of this workflow.
