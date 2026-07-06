# Exploration Task Type

Use this task type when an external CLI agent should inspect a broad source area and return context for decision-making.

Exploration is not limited to repositories. It can cover code, docs, issues, tickets, logs, APIs, schemas, configs, cloud resources, dependency trees, architecture, or other allowed sources.

Broad exploration should be delegated instead of consuming the main agent's context window when the scope spans many files, modules, documents, logs, or systems. For tiny lookups across one or two known files, inspect directly.

## Boundary Inputs

Before delegation, define:

- exploration goal;
- allowed sources;
- forbidden sources;
- allowed command classes;
- output audience;
- expected report shape;
- whether a second targeted pass is allowed.

Default command class: read-only inspection only.

## Prompt Template

```text
You are an exploration agent working under a strict read-only task contract.

Your task is to deeply inspect the allowed sources and return a complete, structured exploration report.

Current goal:

<USER_OBJECTIVE>

Allowed scope:

<ALLOWED_SCOPE>

Forbidden scope:

<FORBIDDEN_SCOPE>

Execution rules:

- Do not modify files.
- Do not delete files.
- Do not write configuration.
- Do not run destructive commands.
- Do not reveal secret values, tokens, keys, or environment values. If sensitive material appears to exist, only state that it appears to exist and where it should be reviewed.
- Prefer concrete file paths, symbols, commands, URLs, issue IDs, or source identifiers where available.
- Mark uncertainty explicitly.

Focus on:

1. Relevant sources, files, directories, documents, issues, logs, APIs, or entry points
2. Current architecture, organization, or source structure
3. Key functions, classes, components, APIs, configs, types, schemas, routes, services, hooks, tests, dependencies, or documents
4. Related data flow, control flow, decision flow, or operational flow
5. Existing patterns that should be followed
6. Risks, edge cases, implicit coupling, migration issues, and hidden assumptions
7. Likely files, documents, systems, or decisions affected by follow-up work
8. Missing information or assumptions that need confirmation
9. Recommended implementation, debugging, review, or planning approach
10. Follow-up commands, checks, or tests to run

Output structure:

# Exploration Summary
# Relevant Sources
# Architecture / Current Behavior
# Key Paths Or Flows
# Data / Control / Decision Flow
# Dependencies And Integrations
# Risks And Edge Cases
# Recommended Plan
# Validation / Test Suggestions
# Open Questions
```

## Review Checklist

After the external agent returns:

- Did it stay inside allowed scope?
- Did it avoid forbidden sources and secret values?
- Did it answer the goal?
- Did it give concrete source references?
- Did it separate facts from assumptions?
- Did it identify risks and edge cases?
- Did it include validation suggestions?
- Are open questions useful?

If the report is too broad, run a second prompt with a narrower target. If the report is too shallow, ask for specific missing dimensions.
