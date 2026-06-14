---
name: mcp-builder
description: Use when creating, reviewing, or refactoring MCP servers, tool schemas, resource templates, or external API integrations for agent use.
category: build
subcategory: integrations
tags:
  - mcp
  - server
  - tools
metadata:
  merged_from:
    - anthropic-mcp-builder
    - awesome-claude-skills-mcp-builder
compatibility:
  tools: [bash, node, python]
  requires: Target API or local capability, intended agent workflow, and authentication constraints
---

# MCP Builder

Use this skill when building MCP servers or improving tool contracts for agents.

## Source Decisions

- Claude's MCP builder guidance provides protocol-first design, tool annotation discipline, and evals.
- Existing local code patterns decide the runtime, packaging, and test framework.
- Current MCP protocol docs are authoritative when local memory or examples conflict.

## Design Principles

1. Tools should map to user intents, not raw API endpoints.
2. Schemas must be strict, typed, and explicit about required fields.
3. Tool outputs should be compact, structured, and stable; prefer `structuredContent` when clients need machine-readable results.
4. Risky operations need dry-run, preview, or confirmation paths.
5. Authentication, rate limits, and data boundaries must be documented.
6. Tool `annotations` must honestly describe behavior, including `readOnlyHint` and `destructiveHint` where supported.

## Workflow

1. Define the agent workflow.
   - What can the agent safely do?
   - What state does it need to read?
   - Which operations mutate external systems?
   - Which responses must be human-readable, machine-readable, or both?
2. Design tools/resources.
   - Prefer a few coherent tools over many thin wrappers.
   - Use resources for stable context such as schemas, docs, and configuration.
   - Use resource templates for parameterized read-only context.
   - Name tools by action and domain so agents can discover them without knowing implementation details.
3. Implement.
   - Follow the repo's existing MCP framework and runtime.
   - Validate inputs at the boundary.
   - Return structured JSON with predictable error shapes.
   - Provide actionable errors: what failed, whether retry is safe, and what input or auth state to change.
4. Test.
   - Unit test schema validation and core handlers.
   - Add integration tests with mocked external services when possible.
   - Manually inspect tool metadata for names, descriptions, and parameter clarity.
   - Run MCP Inspector or the repo's equivalent tool-client smoke when available.

## Protocol Checklist

Before implementation, check the current MCP docs or local SDK docs for:

- server bootstrap and transport expectations;
- tool input schema syntax and supported output schema;
- `structuredContent` and text content behavior;
- resource and resource template shape;
- prompt support if the server exposes reusable prompts;
- tool `annotations`, including `readOnlyHint`, `destructiveHint`, idempotence, and open-world behavior;
- client limitations for authentication, files, images, pagination, and long-running work.

## Eval Set

Create a small eval set before calling the server complete:

- 10 read-only questions that should be answerable without mutation.
- 3 mutation previews that should not modify external state.
- 3 invalid-input cases that should produce actionable errors.
- 2 auth or permission failures.
- 1 large-result case that proves pagination, summarization, or resource linking works.

## Guardrails

- Do not expose destructive API calls without a preview or explicit confirmation pattern.
- Do not return entire large documents when a summary or pointer is enough.
- Do not hide auth requirements in code only.
- Do not design tools around implementation details that users would not understand.
- Do not mark mutating tools as read-only in annotations.
- Do not skip MCP Inspector or equivalent client smoke when a server can be launched locally.

## Output Contract

For MCP work, report:

- tools/resources added or changed;
- `structuredContent` / output schema behavior;
- annotations and safety hints;
- auth and safety behavior;
- tests run;
- known API limitations or follow-up work.
