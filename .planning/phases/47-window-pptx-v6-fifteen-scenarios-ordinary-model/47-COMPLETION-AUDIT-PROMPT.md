# Independent Phase 47 completion audit

You are a fresh independent completion auditor. Perform a read-only audit of
the exact frozen worktree supplied by the controller. Do not trust summaries
or prior PASS labels without inspecting implementation and reproducible
evidence.

## Bounded fast path

Finish within the audit runtime. Do not `cat` the whole ROADMAP, recursively
scan the whole repository, or search the repository-root `.private` directory.
Use bash (`sed`, `python`, `find`) if the Read tool schema fails.

Repository:
`/mnt/d/Growth_up_youth/repo/skills`

The private evidence root is exactly:
`/mnt/d/Growth_up_youth/repo/skills/skills/owned/window-pptx/.private/phase47`

Run the final suite verifier exactly as documented in `47-VALIDATION.md`; it
independently opens every PPTX and plan and finishes in about ten seconds.
Then inspect the verifier implementation, both ordinary-model reports, several
raw accepted review files including a retry, the visual runner's
one-subprocess-per-deck implementation, and the focused tests. Prefer these
bounded checks over broad discovery.

REQUIRED_SKILLS:

- cli-agent-delegator
- aimagician-superpower

Load both skills before substantive inspection. If either cannot be loaded,
return `NEEDS_CONTEXT`.

## Original objective

Make the Window PPTX skill produce a complete fifteen-scenario business suite
at reference-grade craft while an ordinary model has only bounded semantic
fact-grouping/order authority. The system, not the model, must own content
mapping, themes, compositions, native PPTX implementation, QA, repair, and
release. Visual acceptance must be AI-only, blind, and isolated.

## Audit scope

Inspect at least:

- `.planning/REQUESTS.md`;
- Phase 47 context, spec, plan, validation, and summary;
- `skills/owned/window-pptx/SKILL.md`;
- `references/quality-first-v6-workflow.md`;
- ordinary-model planner/runner and tests;
- reference-anchor generator and scenario-suite verifier;
- final private R7 manifests, ordinary-model reports, suite verification
  report, portable proof inventory, and raw accepted visual-review JSON.

Reproduce completion-critical claims where practical:

- 15 locked scenarios and exact plan coverage;
- requested DeepSeek unavailability is explicit, fallback model ID is explicit;
- 15 PPTX/manifests, 292 proof pages, expected page budgets;
- twelve distinct scenario signatures and four actual semantic families;
- native editable OOXML, complete notes, no external relationships or
  whole-slide rasterization;
- strict visual gate is 15/15 with mean >=4.2 individually,
  reference-grade true, and zero Blocker/Important;
- no customer-visible internal evaluation strings;
- focused regression result is credible.

Check for gaming: shared review context, cherry-picked partial pages, reused
scores from a different output revision, accepting malformed/inconsistent
JSON, fabricated ordinary-model provenance, synthetic-only coverage, or a
verifier that merely trusts manifests.

Do not modify any file. Report:

1. requirement coverage table for GOAL-47-01 through GOAL-47-04;
2. exact commands/checks run and observed evidence;
3. findings grouped as Blocker, Important, Nitpick;
4. worktree fingerprint before and after;
5. final verdict.

Return `DONE` only if every goal is evidenced, the fingerprint is unchanged,
and there are zero Blocker or Important. Otherwise return `NEEDS_WORK` with
specific reproducible findings.
