# Phase 35 Specification: Weak-Model Benchmark and Milestone Closure

**Status:** Locked
**Depends on:** Phase 34

## Requirements

- P35-BENCH-01: Refreeze the benchmark dataset, prompts, seeds, model routes,
  environment inventory, and scoring rubric before formal trials.
- P35-BENCH-02: Run DeepSeek V4 Flash Free as the ordinary planning model on
  the four representative scenarios. Run a second ordinary model on the same
  frozen set when available; capability failure is recorded, never replaced
  by an untracked model.
- P35-VISUAL-01: Use direct Agnes only after a fresh image-input probe; use
  OpenCode agents only for contracts/code/evidence when their image attachment
  probe fails.
- P35-BLIND-01: Anonymized independent human review must average at least
  4.2/5 with no relevant dimension below 4.0. AI review cannot satisfy this
  requirement.
- P35-XENGINE-01: LibreOffice proof is mandatory. Native PowerPoint sampling
  is optional certification and COM failure is recorded as an environment
  limitation, not a portable-delivery failure.
- P35-AUDIT-01: A final read-only milestone audit maps every v5.1 requirement
  to fresh reproducible evidence and returns `GO` with no unresolved Blocker
  or Important issue.

## Release rule

Default-branch merge and release are authorized only after engineering,
visual, blind-review, benchmark, and final-audit gates all return PASS/GO.
