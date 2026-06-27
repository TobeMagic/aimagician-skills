---
name: agentic-repo-explorer
description: Delegate large codebase exploration, architecture discovery, dependency mapping, or implementation-context gathering to an external explorer agent, currently OpenCode, then summarize the returned context into a decision-ready report.
category: research
subcategory: repo-analysis
tags:
  - opencode
  - exploration
  - architecture
  - context
  - agent-to-agent
compatibility:
  tools: [bash, opencode]
  requires: A repository path and a concrete exploration objective
---

# Agentic Repo Explorer

Use this skill when the main agent should not spend its own context window scanning a large repository. It turns the user's objective into a precise exploration prompt, delegates the scan to OpenCode, and converts the result into a structured context report for planning, debugging, or implementation.

Current explorer backend: OpenCode only. Future explorer agents can be added behind the same workflow.

## When To Use

Use this skill for:

- exploring a large codebase;
- understanding project architecture;
- finding where a feature is implemented;
- analyzing related code before a risky change;
- mapping dependencies, data flow, control flow, APIs, schemas, routes, services, hooks, or tests;
- cross-module bug investigation;
- preparing context for another agent;
- exporting or preserving an exploration session.

Do not use it for:

- reading one or two known files;
- trivial local checks;
- tasks where the main agent already has enough context;
- direct code edits unless the user explicitly changes the task from exploration to implementation.

## Core Rule

The explorer agent investigates. The main agent orchestrates, summarizes, verifies plausibility, and decides next steps.

Do not ask OpenCode to modify files for this skill. The delegated prompt must say `Do not modify files`.

## Preflight

1. Resolve the project path.
   - If the user provided a path, use it.
   - Otherwise use the current working directory.
   - Verify it exists:

```bash
test -d "<project_path>"
```

2. Check OpenCode.

```bash
command -v opencode
opencode --version
opencode models
```

3. If OpenCode is missing, install only with a user-level package manager or official install script. Do not use `sudo` unless the user explicitly authorizes it.

Preferred install options:

```bash
npm install -g opencode-ai
```

or:

```bash
curl -fsSL https://opencode.ai/install | bash
```

After installing, verify:

```bash
opencode --version
opencode models
```

If the binary exists but is not executable:

```bash
chmod +x "<opencode_binary_path>"
```

If the binary is not on `PATH`, fix the user-level shell path and re-run `command -v opencode`.

4. Check configuration without overwriting user settings.
   - Global config path: `~/.config/opencode/opencode.json`.
   - If the file exists, merge missing keys; do not replace unrelated provider, model, plugin, MCP, instruction, or project settings.
   - If the file does not exist, create it with the minimal exploration config below.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "*": "allow",
    "external_directory": {
      "~/.config/opencode/get-shit-done/*": "allow"
    },
    "read": {
      "~/.config/opencode/get-shit-done/*": "allow"
    }
  },
  "mcp": {
    "linear": {
      "type": "remote",
      "url": "https://mcp.linear.app/mcp",
      "enabled": true
    },
    "notion": {
      "type": "remote",
      "url": "https://mcp.notion.com/mcp",
      "enabled": true
    }
  }
}
```

Record whether config changed. If config changes would overwrite unknown fields, stop and report the needed manual merge.

## Model Selection

Run:

```bash
opencode models
```

Prefer the first available model in this order:

1. `opencode/deepseek-v4-flash-free`
2. `opencode/nemotron-3-ultra-free`
3. `opencode/north-mini-code-free`
4. `opencode/mimo-v2.5-free`
5. `opencode/big-pickle`

If none are available:

- report the available model list;
- choose the strongest clearly free model if one is identifiable;
- otherwise ask for a model decision or stop with a fallback recommendation.

If the selected model fails during run, retry once with the next available model in the priority list. Do not fabricate exploration results after two failures.

## Prompt Construction

Convert the user's objective into a narrow exploration prompt. Include enough detail for OpenCode to search broadly while avoiding irrelevant inventory.

Use this template:

```text
You are a codebase exploration agent.

Your task is to deeply analyze this repository and return a complete, structured exploration report.

Current goal:

<USER_OBJECTIVE>

Focus on:

1. Relevant modules, files, directories, and entry points
2. Current architecture and organization
3. Key functions, classes, components, APIs, configs, types, schemas, routes, services, hooks, tests, and dependencies
4. Related data flow and control flow
5. Existing implementation patterns that should be followed
6. Risks, edge cases, implicit coupling, migration issues, and hidden assumptions
7. Files likely to change if this requirement is implemented
8. Missing information or assumptions that need confirmation
9. Recommended implementation or debugging plan
10. Follow-up commands or tests to run

Requirements:

- Provide complete context, but avoid unrelated information.
- Do not modify files.
- Do not run destructive commands.
- Do not reveal secrets, tokens, keys, or environment values. If you find sensitive material, only state that sensitive material appears to exist and where it should be reviewed.
- Prefer concrete file paths and code symbols.
- Mark uncertainty explicitly.

Output structure:

# Exploration Summary
# Relevant Files and Directories
# Architecture and Current Behavior
# Key Code Paths
# Data Flow / Control Flow
# Dependencies and Integrations
# Risks and Edge Cases
# Recommended Plan
# Validation / Test Suggestions
# Open Questions
```

## Execution

Use non-interactive mode. First inspect the installed CLI syntax:

```bash
opencode run --help
```

Preferred current syntax:

```bash
opencode run --dir "<project_path>" -m "<model>" --format json "<prompt>"
```

If the installed OpenCode version supports the older or local `--prompt` form, this is also acceptable:

```bash
opencode run "<project_path>" -m "<model>" --prompt "<prompt>"
```

Rules:

- Do not use the TUI by default.
- Use debug/log flags only while diagnosing a failed run.
- Do not pass flags that auto-approve dangerous edits unless the user explicitly changes the task to implementation.
- Keep stdout/stderr for the final preflight summary.
- If JSON output is available, preserve the raw JSON path and summarize from it. If only text output is available, summarize from text.

## Session Export

After a successful run, try to export the session:

```bash
opencode session list --format json --max-count 5
opencode export "<sessionID>" --sanitize > ".planning/explorations/opencode-<timestamp>.json"
```

If `session list` is unavailable, try:

```bash
opencode session
opencode export "<sessionID>" --sanitize > ".planning/explorations/opencode-<timestamp>.json"
```

If export fails, mark session export as unavailable and continue with the report.

## Summarization Rules

Do not blindly trust the explorer output.

- Prefer file paths and symbols from the explorer report.
- If the report makes a high-impact claim without evidence, mark it as unverified.
- Do a small local spot check only when needed to validate a critical claim; do not redo the large exploration.
- Redact secrets and token values from the final report.
- Keep the summary decision-ready: what matters, where to look, what to change, what to test, what remains unknown.

## Failure Handling

If OpenCode is unavailable:

- report the failing command;
- report whether installation was attempted;
- include the error output;
- propose fallback options.

If no free model is available:

- list available models;
- explain why no priority model was selected;
- ask for a model decision or suggest a safe fallback.

If the run fails:

- retry once with the next available priority model;
- if it still fails, return the failure report and do not invent findings.

If the project path is invalid:

- stop before running OpenCode;
- ask for a valid path or use the current directory if appropriate.

## Final Report Format

Return this format to the main agent:

```md
# OpenCode Explorer Report

## 1. Preflight Result

- OpenCode status:
- Version:
- Model used:
- Project path:
- Permission/config changes:
- Session export:

## 2. Exploration Goal

<user goal>

## 3. High-Level Summary

<summary>

## 4. Relevant Files

| File / Directory | Why It Matters |
|---|---|

## 5. Architecture Understanding

<architecture>

## 6. Key Code Paths

<key flows>

## 7. Risks and Edge Cases

<risks>

## 8. Recommended Plan

<steps>

## 9. Validation Suggestions

<checks>

## 10. Open Questions

<unknowns>
```

## Reference Commands

```bash
command -v opencode
opencode --version
opencode models
opencode run --help
opencode run --dir "<project_path>" -m "<model>" --format json "<prompt>"
opencode session list --format json --max-count 5
opencode export "<sessionID>" --sanitize
```

