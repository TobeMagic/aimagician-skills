# Quick Task Recipes

Use these recipes only after the controller has locked the objective, scope, permissions, and evidence. Fill every field from `../prompt-contract.md`; these blocks define task-specific content rather than replacing the full envelope.

## Git And Test Report

```text
ROLE: operator
TASK_TYPE: quick
MODALITY: text
PERMISSION_MODE: read-and-run
OBJECTIVE: Inspect <review point>, run <exact checks>, and report readiness.
ALLOWED_COMMANDS: git status/diff/log plus <exact test, lint, typecheck, build, or smoke commands>
TESTS_AND_EVIDENCE: before/after git status, exit codes, failing names, first actionable error, generated pollution, checks not run
WRITE_SCOPE: NONE
GIT_POLICY: inspect-only
```

## Localized Fix

```text
ROLE: implementer
TASK_TYPE: quick
MODALITY: text
PERMISSION_MODE: bounded-write
OBJECTIVE: Implement the already accepted behavior without redesigning it.
WRITE_SCOPE: <exact paths in a clean isolated worktree>
ALLOWED_COMMANDS: scoped reads, edits inside WRITE_SCOPE, <exact verification commands>
TESTS_AND_EVIDENCE: changed paths, diff summary, exact check output, before/after git status
GIT_POLICY: no-commit
STOP_AND_ESCALATE_WHEN: correctness requires new behavior, scope expansion, migration, secret access, destructive action, or production mutation
```

## Scoped Web Research

```text
ROLE: researcher
TASK_TYPE: research
MODALITY: text
PERMISSION_MODE: strict-read-only
OBJECTIVE: Resolve <specific question> from current primary sources.
ALLOWED_SCOPE: <domains, repositories, APIs, date range>
TESTS_AND_EVIDENCE: direct citations, publication/update dates, observed facts, inference, uncertainty, recommendation
WRITE_SCOPE: NONE
GIT_POLICY: inspect-only
```

## Visual Inspection

```text
ROLE: visual-inspector
TASK_TYPE: discovery
MODALITY: vision
MODEL_POLICY: vision-analysis evidence then DeepSeek reasoning
PERMISSION_MODE: strict-read-only
OBJECTIVE: Inspect the authorized assets against <observable criteria>.
REQUIRED_SKILLS: cli-agent-delegator, vision-analysis, <domain skill when needed>
ALLOWED_SCOPE: exact image, screenshot, PDF page, or rendered artifact paths
TESTS_AND_EVIDENCE: upload authorization, visual acquisition provenance, visible defects, location, severity, comparison evidence, uncertainty, controller spot-check
STOP_AND_ESCALATE_WHEN: upload is not authorized, an image cannot be loaded, AGNES_API_KEY is absent, or the direct vision backend fails
```

## Pre-Commit Or Completion Review

```text
ROLE: auditor
TASK_TYPE: audit
MODALITY: text
PERMISSION_MODE: read-and-run
OBJECTIVE: Compare the frozen review point with every accepted request and completion condition.
TESTS_AND_EVIDENCE: one PASS/FAIL/NOT_RUN row per requirement, Blocker/Important/Nitpick findings, decisive checks, missing and extra scope
GIT_POLICY: inspect-only
STOP_AND_ESCALATE_WHEN: review point moves, required source is missing, or a check needs new permission
```

The controller records the selected provider and model outside the task body. For non-visual work, DeepSeek is the default. If it is absent, the controller chooses from live free candidates and records why; the recipe never encodes a fallback ranking.
