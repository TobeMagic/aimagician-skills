---
name: linear-issue-workflow
description: "Use when a Linear issue must be read, created, updated, split, linked to a pull request, or closed through Composio CLI. Keep Linear auxiliary to delivery: use it only when ticket context is needed or after core code work is verified, merged, or otherwise ready to hand off."
metadata:
  related_skills:
    - composio-tool-router
    - github-pr-workflow
    - cli-agent-delegator
compatibility:
  tools: [bash, composio, git, gh, opencode]
  requires: Composio CLI with a Linear connection for live Linear work
category: operate
subcategory: linear
tags:
  - linear
  - issue-tracking
  - composio
  - post-delivery
---

# Linear Issue Workflow

Use Linear as an optional work-tracking surface, not as a prerequisite for writing or verifying code. Use Composio CLI for every Linear lookup or mutation. Do not discover or call Linear MCP.

## Route By Need

| Situation | Action |
|---|---|
| Ticket details determine the acceptance criteria or scope | Read the issue through Composio before implementation. |
| User supplied sufficient requirements and only mentioned a ticket incidentally | Deliver and verify code first; update the ticket after the PR or merge. |
| No issue identifier and no request to create one | Do not create or search Linear. |
| Normal task closure after merge | Delegate the bounded Composio read/update/readback to OpenCode when authorization exists. |
| Ticket split changes scope or ownership | Discuss the split with the user before creating child issues. |

## Core Rules

- Load `composio-tool-router` before live Linear work. Discover service-scoped actions on demand with `composio tools list linear --limit 50`; inspect only the selected schema.
- Treat Linear status, comments, and linked records as auxiliary work. They do not block implementation, focused verification, PR creation, or merge unless the ticket itself contains material acceptance information or project policy says otherwise.
- Keep core delivery first: understand -> discuss material tradeoffs -> implement -> necessary verification -> PR -> merge to the project-resolved integration branch. Run Linear closure afterwards.
- Resolve the PR base per project. On the first task, read repository contribution/branch conventions and GitHub default/protection data. If still unclear, ask the user; do not assume `dev`, `develop`, `main`, or `master`. Reuse the confirmed project decision for later tasks.
- One issue normally maps to one branch and primary PR, but split only when it reduces delivery risk. Parent closure requires required child work to be terminal.
- Write actions require the normal Composio dry run and confirmation. A task-scoped user authorization may allow OpenCode to perform only named post-merge state/comment/closure actions; see `composio-tool-router` for the authorization boundary.
- If Composio, auth, or a Linear action is unavailable, report it and continue core code delivery when safe. Never fabricate ticket state.

## Workflow

### 1. Read Only When It Changes Delivery

When a ticket is a source of truth, use Composio discovery, select a read action, and retrieve only the issue fields needed for implementation: identifier, title, description, acceptance criteria, current state, dependencies, parent/children, and linked PRs. Summarize contradictions with the user's latest decision instead of silently preferring either source.

### 2. Deliver Core Work

Use `aimagician-superpower` for risk triage and `github-pr-workflow` for the repository's branch, PR, check, and merge policy. Do not insert Linear comments between ordinary local edits, test runs, or review fixes. Record only meaningful post-delivery facts: PR URL, merge commit, tests, residual risk, and accepted follow-up.

### 3. Delegate Post-Delivery Closure

After the PR is merged or delivery is otherwise accepted, a `cli-agent-delegator` worker may run a `read-and-run` Composio closure contract. Its prompt must include the issue ID, exact authorized actions, PR/commit/test facts, allowed tool slugs, dry-run requirement, readback requirement, and a prohibition on unrelated writes.

The worker may:

- read the current issue and child status;
- move the issue to the project's review or done-equivalent state when authorized;
- add one compact delivery summary comment;
- link the known PR if the selected action supports it;
- return the readback result and any failure.

It must stop with `NEEDS_CONTEXT` if child status, acceptance criteria, state names, payload, or scope is ambiguous.

### 4. Close Carefully

Before closing a parent, re-read its required children and stated acceptance criteria. Do not close while required children are unfinished. A successful merge alone is not proof that a ticket is ready to close; use the verified delivery evidence and ticket criteria. Wiki records and reviewer bots are optional unless the repository or user explicitly requires them.

## Output Contract

Report the issue ID, whether Linear influenced delivery, Composio tools selected, dry-run and readback result for writes, PR/commit/test facts recorded, unresolved child or acceptance gaps, and whether closure was completed, deferred, or blocked. Do not expose credentials or raw auth data.
