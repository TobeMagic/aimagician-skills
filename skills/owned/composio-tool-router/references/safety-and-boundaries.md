# Safety And Boundaries

Composio can act in external SaaS systems. Treat it as a real external tool surface, not as local documentation lookup.

## Risk Classes

| Class | Examples | Default handling |
|---|---|---|
| Discovery | `tools list`, `search`, `tools info`, `--get-schema` | Safe to run when scoped to the task |
| Auth transition | `whoami`, `link`, `login` | Explain first; do not expose auth files |
| Read-only action | list teams, get issue, retrieve channel info | Run when requested and scoped |
| Write/update | create issue, send message, update record, add reaction | Dry-run first and confirm exact payload |
| Destructive/admin | archive, delete, invite admin, workspace changes | Confirm target and blast radius; prefer preview/readback first |
| Proxy | direct API calls via `composio proxy` | Use only when no tool fits; mutations need confirmation |

## Confirmation Checklist For Writes

Before real execution, confirm:

- toolkit and connected account if visible;
- exact tool slug;
- target resource or destination ID;
- human-readable payload summary;
- whether the operation is public, reversible, or admin-scoped;
- duplicate execution risk;
- verification or readback step after success.

## Secret Handling

- Never print API keys, OAuth tokens, refresh tokens, cookies, or raw auth files.
- Do not read `~/.composio/user_data.json`, cached credentials, or config files unless the user explicitly asks for a secret-safe inventory.
- If a command reports a secret, redact the value and report only that a credential exists.
- Keep payloads out of shell history when they contain secrets; prefer stdin or a temporary file only when needed and clean it up.

## MCP Boundary

Composio is a good MCP-light replacement when the task is SaaS tool discovery or SaaS action execution. It is not a complete protocol replacement.

Keep MCP for:

- local resource exposure;
- resource templates;
- prompt surfaces;
- custom tools that are not in Composio;
- client-specific MCP behavior;
- strict self-hosted schema/auth/audit requirements.

Use `mcp-builder` when designing those MCP contracts.

## Failure Handling

If discovery fails:

- report the command and error;
- check `composio --version` and command help;
- try a narrower toolkit/query only if the syntax is valid.

If auth fails:

- report the toolkit and missing connection or scope;
- suggest `composio link <toolkit>` when appropriate;
- do not fabricate connected state.

If execution fails:

- separate validation errors, auth/scope errors, API errors, and rate limits;
- do not retry non-idempotent operations unless success was clearly false;
- for writes, use readback only after a successful response or when the API response is ambiguous and readback is safe.
