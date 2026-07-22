# Delegated Prompt Contract

Every CLI-agent invocation uses this contract. More detail in the prompt is cheaper than a worker rediscovering context or exceeding scope.

## Required Envelope

```text
TASK_ID: <stable identifier>
ROLE: <explorer | researcher | visual-inspector | operator | implementer | plan-reviewer | spec-reviewer | quality-reviewer | verifier | auditor>
OBJECTIVE: <one measurable outcome>
DELIVERABLE: <report, evidence table, patch, commit, or decision input>
REVIEW_POINT: <exact commit, diff, worktree state, source snapshot, URLs, or artifact set>

SOURCE_OF_TRUTH:
- <path, document, requirement set, user decision, or primary URL>

ACCEPTED_DECISIONS:
- <decision that must not be reopened>

KNOWN_CONTEXT:
- <facts already established by the controller>

REQUIRED_SKILLS:
- <skill-id>: <why it is required and which part to apply>

ALLOWED_SCOPE:
- <exact repositories, roots, files, URLs, services, commands, or data classes>

FORBIDDEN_SCOPE:
- <paths, systems, secrets, commands, behaviors, and unrelated dirty work>

PERMISSION_MODE: <strict-read-only | read-and-run | bounded-write>
WRITE_SCOPE: <exact paths, or NONE>
ALLOWED_COMMANDS: <command classes and important exact commands>
TESTS_AND_EVIDENCE: <checks to run or evidence to collect>
GIT_POLICY: <inspect-only | no-commit | local-commit-after-review | other explicit policy>
CHILD_AGENT_POLICY: <forbidden | explicitly bounded roles>

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: <events or stage markers expected>
STOP_AND_ESCALATE_WHEN: <missing context, scope conflict, permission need, provider failure, unsafe state>
SESSION_EXPORT: <NONE, or exact allowed output path>
OUTPUT_FORMAT: <required headings, tables, JSON, or patch/commit handoff>
```

Do not omit a field. Use `NONE` when a field does not apply so the absence is deliberate.

## Skill Loading Gate

The prompt must contain this instruction:

```text
Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.
```

Name only skills relevant to the role. Typical routing:

- broad repository or source discovery: `cli-agent-delegator` plus `aimagician-superpower` when engineering context is needed;
- web or evidence research: `cli-agent-delegator` plus the domain research skill;
- tests, git checks, implementation, or engineering review: `cli-agent-delegator` plus `aimagician-superpower`;
- browser verification: add `webapp-testing`;
- HTML visual review: add `interface-design`;
- PR state: add `github-pr-workflow`;
- parallel write lanes: add `parallel-worktree-pr-flow`.

## Permission Semantics

### strict-read-only

- No file, config, git, issue, SaaS, cloud, or system mutation.
- Commands must inspect only.
- Do not export a session unless an exact write path is authorized.

### read-and-run

- Run only named non-destructive checks.
- Capture `git status --short` before and after commands that may create caches, snapshots, coverage, or build artifacts.
- Report new artifacts. Do not delete, reset, restore, or clean them unless explicitly allowed.

### bounded-write

- The controller supplies a clean isolated worktree and exact write scope.
- Read outside the write scope only when it is inside `ALLOWED_SCOPE` and needed for context.
- Never edit outside `WRITE_SCOPE`, even to fix formatting or tests.
- Stop with `NEEDS_CONTEXT` if correct implementation requires a new file or owner outside the scope.
- A local commit requires `GIT_POLICY: local-commit-after-review` and passing review evidence.
- Push, merge, rebase, reset, checkout-overwrite, clean, stash, package publishing, system install, and production mutation remain forbidden unless individually authorized.

## Child-Agent Inheritance

Default `CHILD_AGENT_POLICY` is `forbidden`. If child agents are authorized, each child receives the same:

- source of truth and accepted decisions;
- allowed and forbidden scope;
- permission and write scope;
- required skills;
- command and git policy;
- secret handling, status, severity, evidence, and stop rules.

Give each child a smaller explicit objective. Do not allow recursive scope expansion, unrestricted repository globs, full-repository diffs, or additional writes unless the controller's envelope explicitly permits them. The parent worker remains responsible for reconciling child output.

## Progress And Waiting Contract

Use provider logs and report meaningful stages when supported: preflight, skill loading, source scan, command/test start, command/test end, synthesis, review, and final result. Tool calls, file references, streamed logs, stage changes, provider requests, and session updates are progress events.

Quiet output alone is not failure. While the process is alive and event state advances, keep waiting. A stale classification requires positive evidence that neither the process nor provider session is advancing; record the last event and health check. Do not use a fixed elapsed-time cutoff as proof of staleness.

## Safety And Evidence

- Never print secret, token, key, cookie, credential, or environment values.
- If sensitive material appears to exist, report only its location and type.
- Separate observed facts, inferences, and recommendations.
- Cite concrete paths, symbols, commands, test names, URLs, or artifacts.
- Do not claim `DONE` from prose alone; attach evidence.
- Do not claim a test or file is absent without a scoped search.
- Do not hide skipped or failing checks.

## Final Status Rules

- `DONE`: deliverable complete, scope respected, required checks passed, no Blocker or unresolved Important finding.
- `DONE_WITH_CONCERNS`: deliverable exists, but uncertainty, skipped evidence, or an Important finding needs controller judgment.
- `NEEDS_CONTEXT`: a named source, skill, decision, permission, or scope extension is required.
- `BLOCKED`: a concrete dependency or repeated provider/environment failure prevents responsible progress.
