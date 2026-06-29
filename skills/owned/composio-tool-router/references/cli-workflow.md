# Composio CLI Workflow

Use these commands as the default CLI-first path. Verify `composio --help` before relying on remembered syntax because Composio evolves quickly.

## Preflight

```bash
command -v composio
composio --version
composio --help
composio tools --help
composio tools list --help
```

Use `composio whoami` only when account identity or auth state matters for the task.

## Toolkit Discovery

List tools for one toolkit:

```bash
composio tools list linear --limit 50
composio tools list slack --limit 50
```

Filter inside one toolkit:

```bash
composio tools list linear --query "issue" --limit 20
composio tools list slack --query "message" --limit 20
composio tools list slack --tags important --limit 20
```

Use semantic search for an intent:

```bash
composio search "create a Linear issue" --toolkits linear --limit 10
composio search "send a Slack message" --toolkits slack --limit 10
```

Prefer toolkit-scoped search over broad global search unless the service is unknown.

## Tool Inspection

Inspect a selected tool:

```bash
composio tools info LINEAR_CREATE_LINEAR_ISSUE
composio execute LINEAR_CREATE_LINEAR_ISSUE --get-schema
```

Only inspect schemas for selected candidate tools. Avoid loading many schemas into context.

## Authentication

If the selected toolkit is not connected, explain the auth step:

```bash
composio link linear
composio link slack
```

Do not run login/link flows silently when they would open a browser, change local auth state, or require user interaction.

## Dry-Run And Execute

Validate write-capable payloads first:

```bash
composio execute LINEAR_CREATE_LINEAR_ISSUE \
  -d '{"team_id":"...","title":"...","description":"..."}' \
  --dry-run
```

Execute only after confirmation:

```bash
composio execute LINEAR_CREATE_LINEAR_ISSUE \
  -d '{"team_id":"...","title":"...","description":"..."}'
```

For public communications, such as Slack posts, confirm the exact destination, message body, thread behavior, and duplicate-send risk before real execution.

## Proxy

Use proxy only when no suitable Composio tool exists and the API endpoint is known:

```bash
composio proxy "https://slack.com/api/conversations.info?channel=..." --toolkit slack
```

Mutating proxy calls require the same confirmation as mutating tools.

## Result Handling

- Treat HTTP/process success as transport success, not business success.
- Inspect response fields such as `successful`, `ok`, `error`, returned IDs, and timestamps.
- Store IDs needed for follow-up actions.
- Do not retry non-idempotent sends or creates after any confirmed success.
- Summarize large responses instead of pasting full payloads.
