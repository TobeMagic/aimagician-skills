# Request Ledger

## USR-20260728-001: Agent-first Skillbird and completion audit

**Status:** Accepted
**Source:** User discussion and approved implementation plan

### Accepted Requirements

- **REQ-AGENT-001:** Add a stable, non-interactive `--agent` CLI contract without replacing the human CLI or TUI.
- **REQ-AGENT-002:** Agent write commands preview by default and apply only with explicit `--yes`.
- **REQ-AGENT-003:** Agent output uses one versioned JSON envelope, deterministic ordering, no ANSI, and documented exit codes.
- **REQ-AGENT-004:** Add a discoverable `capabilities` command and make `skillbird --agent` return it instead of opening the TUI.
- **REQ-PROMPT-001:** Add one source-neutral `system-prompt-engineering` owned skill that progressively discloses the combined capabilities of the two accepted upstream sources.
- **REQ-PROMPT-002:** Keep upstream mirrors ignored and commit only distilled capabilities, reusable assets, evals, and an auditable source mapping.
- **REQ-AUDIT-001:** Record original requests and trace them through accepted requirements, implementation evidence, and completion audit.
- **REQ-AUDIT-002:** Every completion claim must use a fresh OpenCode Agnes audit; unresolved Blocker, Important, FAIL, or NOT_RUN prevents completion.
- **REQ-AUDIT-003:** The main Agent must validate completion-critical reviewer claims against primary evidence.
- **REQ-SYNC-001:** Update README, run regression checks, sync owned skills to Codex and OpenCode with Skillbird, and verify installation health.
- **REQ-GIT-001:** Integrate only clean audited work, exclude the dirty PPT worktree, merge to `master`, and push after final audit.

### Explicit Non-goals

- Desktop application or cross-platform GUI.
- Repository split or adoption of another skill manager.
- TUI redesign beyond regression fixes.
- Automatic upstream mutation of owned skills.

