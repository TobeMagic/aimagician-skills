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

## USR-20260729-001: Dynamic OpenCode routing and short-task delegation

**Status:** Accepted
**Source:** User discussion and accepted implementation plan
**Supersedes:** The model-specific portion of REQ-AUDIT-002; all traceability and blocking-finding requirements remain active.

### Accepted Requirements

- **REQ-DELEGATE-001:** Eligible simple, short, execution-oriented work is delegated to OpenCode by default instead of consuming the controller's context.
- **REQ-DELEGATE-002:** Bounded writes require locked requirements, exact write scope, a clean isolated worktree, explicit verification, and no commit by default.
- **REQ-MODEL-001:** Every non-visual OpenCode task defaults to `opencode/deepseek-v4-flash-free`.
- **REQ-MODEL-002:** If DeepSeek is absent from the live free-model inventory, the controller selects another available free model for the task without a maintained quality ranking table.
- **REQ-MODEL-003:** Visual work defaults to Agnes and may use another verified vision-capable model when Agnes is unavailable.
- **REQ-MODEL-004:** Automatic fallback to Agnes occurs only for visual work or an explicit usage, quota, or rate-limit failure; other failures retain their actual classification.
- **REQ-MODEL-005:** Model discovery uses cached `opencode models --verbose` metadata with explicit refresh and a verified capability override for custom-provider metadata gaps.
- **REQ-AUDIT-004:** Completion audits remain fresh, independent, requirement-by-requirement OpenCode reviews but are no longer locked to Agnes; non-visual audits follow the normal DeepSeek-first route.
- **REQ-AUDIT-005:** Existing records using the `Agnes Completion Audit` heading and Agnes model remain valid without rewriting historical evidence.
- **REQ-RUNTIME-001:** OpenCode runs use the current positional prompt syntax, stream progress, wait on process and activity events rather than fixed elapsed limits, and record the complete model attempt chain.
- **REQ-SYNC-002:** Updated owned skills are tested, bootstrapped to Codex and OpenCode, and verified through the agent-facing list/doctor contract.

### Explicit Non-goals

- Maintaining a fixed ranking of non-DeepSeek free models.
- Delegating unresolved product, architecture, security acceptance, migration, or destructive-operation decisions.
- Treating every provider, network, authentication, permission, or syntax failure as an Agnes fallback condition.
- Rewriting completed historical audits solely to change their model terminology.
