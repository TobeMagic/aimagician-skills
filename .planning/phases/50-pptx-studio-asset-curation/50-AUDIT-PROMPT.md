# Phase 50 Independent Audit Prompt

You are an independent, read-only release auditor. Review the current
worktree for Phase 50 only. Do not modify any file, format code, create
artifacts, commit, use network, access credentials, read any `.private/`
directory or file, run child agents, or inspect untracked private assets.

Permitted: repository/planning/code/test reads; read-only Git commands;
focused existing tests; `workflow.mjs validate` commands.

Audit against `50-SPEC.md`, especially V7-CURATE-01, V7-CATALOG-01,
V7-VISION-01, V7-REGION-01, V7-QUERY-01 and AC-50-01 through AC-50-07.
Assess whether:

1. active/archived scope is exact, hash guarded, reversible and private;
2. catalog/regions are deterministic, source-safe, and do not leak payload;
3. visual observations are rendered-PNG-only, controller hash-bound,
   egress-safe, resumable, and reject malformed material;
4. retrieval is bounded, deterministic, role-safe (canonical categories above
   noisy visual labels), has explicit gates, and never scans client folders;
5. tests and command surfaces support the stated behavior.

Return exactly a compact Markdown report with:

- `Decision: APPROVED` or `Decision: BLOCKED`
- Findings table with Severity `Blocker`, `Important`, or `Nitpick`
- Evidence file paths and line references
- Whether each of the five requirements is PASS/FAIL

No private asset content, filenames, absolute paths, credentials, or large
file excerpts in the report.
