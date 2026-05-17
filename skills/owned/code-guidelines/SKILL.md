---
name: code-guidelines
description: Use for every non-trivial coding task, including feature work, bug fixes, refactors, review fixes, test failures, and debugging. Also use when the user asks to think before coding, wants minimal diffs, wants to avoid overengineering, or wants testable/verifiable goals.
metadata:
  related_skills:
    - test-driven-development
    - linear-issue-workflow
    - github-pr-workflow
    - llm-know-how-wiki
compatibility:
  tools: [bash, git]
  requires: A codebase, a concrete task, and preferably a runnable verification command
---

# Code Guidelines

Use this skill to keep coding work disciplined: think first, keep changes small, edit only what matters, and verify the result.

## Default Use

Use this skill for every non-trivial coding task:

- feature implementation;
- bug fixes;
- refactors;
- review fixes;
- test failures;
- production/debug fixes.

Apply it as the default coding discipline.

## The 4 Principles

1. Think Before Coding
   - State assumptions, ambiguities, constraints, and tradeoffs before editing.
   - Ask a narrow question when a missing answer would change the implementation.
   - Push back when the requested path is riskier or more complex than needed.

2. Simplicity First
   - Write the smallest implementation that solves the current problem.
   - Do not add speculative abstractions, configurability, adapters, or future-proofing.
   - Prefer existing project patterns over new framework or architecture choices.

3. Surgical Changes
   - Touch only the files and lines required for the task.
   - Do not perform drive-by cleanup, style churn, or unrelated refactors.
   - If unrelated problems are found, mention them separately instead of changing them.

4. Goal-Driven Execution
   - Convert "do X" into a verifiable goal.
   - For bugs, reproduce the failure when practical, then make it pass.
   - For features, define acceptance checks and run the narrowest useful verification.

## Execution Loop

1. Define the target
   - What changes, what stays out of scope, and what will prove completion.
2. Gather evidence
   - Read existing code and docs before editing.
3. Make the minimal change
   - Follow local patterns and avoid unrelated churn.
4. Verify
   - Run tests, lint, typecheck, build, or a targeted manual check.
5. Report
   - Summarize the change, verification, and any residual risk.

## Related Workflows

- Use `test-driven-development` when a bug or feature can be pinned down with a test.
- Use `linear-issue-workflow` when the task starts from a Linear issue.
- Use `github-pr-workflow` when PR checks, reviews, or reviewer-bot results matter.
- Use `llm-know-how-wiki` when a decision, runbook, workflow activity, or durable finding should be recorded.

## Output Contract

For non-trivial coding work, final output should include:

- target and scope;
- key changes;
- verification command and result;
- unresolved risks or follow-up only when relevant.

## Anti-Patterns

- Coding before reading the relevant code.
- Adding abstractions for a single caller.
- Reformatting files unrelated to the task.
- Treating "looks right" as verification.
- Hiding uncertainty instead of stating it.

## Companion Notes

Use [`references/principles-checklist.md`](./references/principles-checklist.md) for a compact checklist.
