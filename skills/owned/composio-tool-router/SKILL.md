---
name: composio-tool-router
description: Use when routing third-party SaaS tool work through Composio CLI for lightweight discovery, service-scoped tool lookup, schema-on-demand, dry-run validation, or MCP-light Slack, Linear, GitHub, Notion, Jira, and similar integrations.
category: operate
subcategory: tool-routing
tags:
  - composio
  - tool-router
  - integrations
  - saas
  - mcp-alternative
compatibility:
  tools: [bash, composio]
  requires: Composio CLI, intended service/toolkit, user intent, and explicit confirmation for external writes
---

# Composio Tool Router

Use this skill as a lightweight third-party SaaS tool registry and router. It helps the agent discover and invoke Slack, Linear, GitHub, Notion, Jira, and similar actions through Composio without loading a full MCP server's schema into every turn.

This skill replaces only the MCP-heavy parts that Composio can cover: tool discovery, service-scoped routing, schema-on-demand, auth-aware execution, and proxy calls. Use `mcp-builder` for custom MCP servers, local resource exposure, prompt/resource protocol design, or MCP-specific schema work.

## Capability Routing

Load only the reference needed for the current task.

| Need | Reference |
|---|---|
| CLI commands for discovery, schema lookup, dry-run, execution, and proxy | `references/cli-workflow.md` |
| Safety classes, confirmation rules, secret handling, and MCP replacement boundaries | `references/safety-and-boundaries.md` |

## When To Use

Use this skill when:

- the user wants to discover actions for a SaaS service such as Slack or Linear;
- the agent needs a compact list of available Composio actions for one toolkit;
- a task can be solved by searching Composio for the right tool instead of preloading MCP schemas;
- only one or a few tool schemas should be loaded on demand;
- the task involves checking whether an external account is connected or what auth step is needed;
- the user wants a unified external SaaS entrypoint that can later extend to GitHub, Notion, Jira, Gmail, and similar services.

Do not use it when:

- the task is building or changing an MCP server;
- the needed capability is a local filesystem resource, local database, project-only API, or custom server not exposed through Composio;
- the user explicitly asked to use a configured MCP tool;
- a direct first-party CLI is already the safest, narrowest path and avoids Composio auth indirection.

## Default Operating Contract

- CLI-first: prefer `composio` commands over SDK/API code unless the user explicitly asks for SDK integration.
- Service-scoped: identify the toolkit slug first, then list or search inside that toolkit.
- Schema-on-demand: inspect a specific tool schema only after selecting a candidate action.
- Dry-run first: validate write-capable calls with `--dry-run` before real execution.
- Confirm external writes: any create, update, archive, delete, send, invite, publish, or proxy mutation needs explicit confirmation of target, payload, and expected effect.
- Secret-safe: never print tokens, API keys, OAuth state, or raw files from `~/.composio/`.
- Output-efficient: summarize candidate tools and only include fields needed for the next decision.

## Workflow

### 1. Classify Intent

- Identify the target service or toolkit, such as `linear`, `slack`, `github`, `notion`, or `jira`.
- Identify the user intent: discover, inspect schema, validate, execute, debug auth, or proxy an API call.
- Determine risk class: read-only, write/update, destructive, public communication, admin action, or unknown.
- If service, target, or write intent is ambiguous, discuss before calling anything beyond discovery.

### 2. Preflight

- Check the CLI: `command -v composio`, `composio --version`, and relevant `--help`.
- If auth state matters, use `composio whoami` or `composio link <toolkit>` only after explaining why.
- Do not inspect or quote local Composio config/cache files that may contain auth state.

### 3. Discover Tools

- For a known service, list compact inventory: `composio tools list <toolkit> --limit 50`.
- For narrowed service search, use `composio tools list <toolkit> --query "<term>" --limit 20`.
- For intent search, use `composio search "<intent>" --toolkits <toolkit> --limit 10`.
- Prefer service-scoped results over global search to reduce noise.

### 4. Select And Inspect

- Choose the smallest tool that matches the user's intent.
- Prefer read-only tools for lookup and validation before mutation.
- Inspect only the selected tool: `composio tools info <tool_slug>` or `composio execute <tool_slug> --get-schema`.
- Capture required inputs, optional inputs, likely IDs to resolve first, and pitfalls from the command output.

### 5. Validate And Execute

- Build the payload from user-approved facts and resolved IDs.
- For write-capable calls, run `composio execute <tool_slug> -d '<json>' --dry-run` first.
- Before real execution, confirm the exact tool slug, target account/service, destination/resource, payload summary, and whether duplicate execution would be harmful.
- Execute once. If the response indicates success, do not retry blindly.
- For failures, summarize the error, connection state, missing scopes or fields, and the safest retry path.

### 6. Return A Compact Tool Report

Include:

- toolkit and user intent;
- commands run;
- candidate tools considered;
- selected tool slug and why;
- schema or required inputs inspected;
- auth/link state if checked;
- dry-run result for write-capable work;
- real execution result if performed;
- risks, assumptions, and next action.

## MCP Replacement Rules

Use Composio instead of MCP when the problem is:

- finding SaaS actions by service or intent;
- executing a supported SaaS action with existing Composio auth;
- reducing context that would otherwise come from large MCP tool schemas;
- using one unified external SaaS entrypoint across multiple apps.

Keep MCP or another direct integration when the problem needs:

- local resources, resource templates, or prompt surfaces;
- a custom tool contract not available in Composio;
- streaming, long-lived local servers, or target-specific MCP client behavior;
- strict self-hosted control over schemas, auth, audit logs, or data residency.

## Output Contract

For Composio routing work, report:

- toolkit/service;
- discovery command and result summary;
- selected action/tool slug;
- whether schema was loaded on demand;
- whether auth/link was needed;
- dry-run and confirmation status for writes;
- execution result or reason execution was not performed;
- residual risk and validation suggestions.
