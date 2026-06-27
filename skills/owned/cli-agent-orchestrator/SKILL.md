---
name: cli-agent-orchestrator
description: Orchestrate external CLI agents for bounded multi-agent work such as exploration, review, planning, verification, or context gathering. Use when the main agent should delegate a large or specialized task to another CLI agent, currently OpenCode for read-only exploration, then validate and summarize the result.
category: operate
subcategory: agent-orchestration
tags:
  - cli-agent
  - multi-agent
  - orchestration
  - opencode
  - exploration
compatibility:
  tools: [bash, opencode]
  requires: A task objective, allowed scope, forbidden scope, and target CLI agent
---

# CLI Agent Orchestrator

Use this skill to coordinate external CLI agents. The main agent owns task framing, safety boundaries, prompt quality, result review, and final handoff. The delegated CLI agent performs the heavy scan or specialized work.

Current provider: OpenCode. Current task type: read-only exploration. Future providers and task types can be added under `references/` without changing the orchestration contract.

## Capability Routing

Load only the files needed for the current task.

| Need | Reference |
|---|---|
| OpenCode preflight, config, model selection, run command, session export | `references/providers/opencode.md` |
| Read-only exploration task contract and prompt template | `references/task-types/exploration.md` |
| Exploration report shape | `references/report-templates/exploration-report.md` |

## When To Use

Use this skill when:

- the task is large enough that the main agent should not spend its own context window scanning everything;
- another CLI agent can cheaply inspect a repository, document corpus, issue set, logs, configs, APIs, or other allowed sources;
- the user needs a structured context report before planning, implementation, debugging, review, or audit;
- exploration may need multiple targeted passes;
- the result will be handed to the main agent or another agent for follow-up work.

Do not use it when:

- one or two known files are enough;
- the target source is small and already in context;
- the user asked for immediate implementation and the needed context is already known;
- the external agent would need write access but the task has not been explicitly re-scoped beyond read-only exploration.

## Discuss-First Boundary Gate

Before invoking any external CLI agent, confirm or infer these points. If any missing answer materially changes safety, scope, or output, discuss it with the user first.

1. Task type: exploration, review, planning, verification, audit, summarization, comparison, or another role.
2. Objective: the exact question the external agent must answer.
3. Allowed scope: repositories, paths, documents, issues, tickets, logs, cloud resources, or other sources it may inspect.
4. Forbidden scope: paths, secrets, env files, user files, external systems, commands, or data classes it must not touch.
5. Execution permissions: strict read-only by default; explicitly name any non-destructive commands that are allowed.
6. Output use: main-agent decision, implementation plan, bug triage, another-agent context pack, or archival report.
7. Iteration policy: whether a weak first answer can trigger a second targeted exploration pass.

If the user gives a broad request, narrow it into a bounded task before delegation.

## Default Safety Contract

The default mode is read-only by task contract.

- The delegated prompt must say not to modify files.
- The delegated prompt must say not to delete files.
- The delegated prompt must say not to write config.
- The delegated prompt must say not to run destructive commands.
- The delegated prompt must say not to reveal secret values.
- Do not pass auto-approval flags for write-capable tasks unless the user explicitly changes the task type and accepts the risk.

If the user asks for external-agent writes, stop and re-discuss the task as an execution workflow. Do not silently expand this skill beyond orchestration and context gathering.

## Orchestration Loop

1. Classify the task.
   - Pick a task type.
   - Current implemented task type: exploration.
2. Select the provider.
   - Current implemented provider: OpenCode.
   - Read `references/providers/opencode.md` before running OpenCode.
3. Lock boundaries.
   - Confirm allowed and forbidden scope.
   - Confirm read-only or any permitted command class.
4. Build the prompt.
   - Use the task-type template.
   - Include objective, scope, forbidden scope, output format, and safety contract.
5. Run preflight.
   - Verify CLI exists.
   - Verify project/source path when relevant.
   - Verify model availability and provider config.
6. Execute the external CLI agent.
   - Prefer non-interactive mode.
   - Capture stdout/stderr and exit status.
   - Retry once with a fallback model/provider only when the failure is provider/model related.
7. Review the result.
   - Do not blindly trust it.
   - Check whether it answered the objective.
   - Mark unsupported claims.
   - Spot-check critical file paths or assertions only when necessary.
8. Iterate if needed.
   - If gaps are bounded and the user allowed iteration, run a second targeted prompt.
   - If gaps change scope or safety, discuss first.
9. Produce the handoff.
   - Use the report template for the task type.
   - Include preflight, provider, model, boundaries, findings, risks, recommendations, validation, and open questions.

## Provider Registry

Current provider:

- `opencode`: best current explorer backend for read-only exploration across code, docs, issues, logs, configs, APIs, and other allowed sources.

Future provider slots:

- documentation/search agent;
- infra/cloud inspection agent;
- issue or planning-system agent;
- database/schema inspection agent;
- review-only code agent;
- verification agent.

Provider-specific commands, config, and failure handling belong in `references/providers/<provider>.md`, not in the main skill.

## Task Type Registry

Current task type:

- `exploration`: read-only context discovery across code, docs, issues, logs, APIs, architecture, data flow, dependencies, risks, and recommendations.

Future task types:

- `review`: delegate a bounded review and reconcile findings;
- `planning`: ask another agent for implementation options or plan critique;
- `verification`: ask another agent to inspect validation evidence;
- `audit`: ask another agent to check requirement coverage, security, or migration risk;
- `summarization`: turn large source material into a context pack;
- `comparison`: compare architectures, libraries, providers, or implementation approaches.

Task-specific prompts and report templates belong in `references/task-types/` and `references/report-templates/`.

## Quality Gates

Before accepting external-agent output, check:

- Does it answer the user's objective?
- Does it respect allowed and forbidden scope?
- Does it include concrete references where possible?
- Does it separate facts from assumptions?
- Does it avoid secret values?
- Does it identify risks and edge cases?
- Does it provide validation suggestions?
- Are recommendations actionable?
- Are open questions explicit?

If the report fails these checks, either run a targeted follow-up or return the gaps clearly.

## Output Contract

Final output must include:

- task objective;
- provider and model used;
- preflight status;
- allowed and forbidden scope;
- whether config changed;
- whether session export succeeded;
- structured findings;
- risks and unknowns;
- recommended next step;
- validation suggestions;
- any reliability caveats about the external-agent result.
