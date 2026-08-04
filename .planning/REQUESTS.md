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
- **REQ-SYNC-004:** Bootstrap synchronization reconciles selected target Skill directories to the active owner set and removes unowned Skill directories, while preserving Codex-managed `.system` skills.
- **REQ-SKILL-010:** Add clean owner Skills for long-form knowledge distillation, evidence-grounded reasoning distillation, and validated Skill evolution without upstream branding or installer behavior.
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

## USR-20260730-001: Direct Agnes vision and goal-locked completion

**Status:** Accepted
**Source:** User discussion and accepted implementation plan
**Supersedes:** The visual-routing portions of REQ-MODEL-003 and REQ-MODEL-005; historical evidence remains valid.

### Accepted Requirements

- **REQ-VISION-001:** Add one provider-neutral `vision-analysis` owned skill whose current backend reads local or HTTPS images through the Agnes OpenAI-compatible API using `AGNES_API_KEY`.
- **REQ-VISION-002:** Every external image request requires explicit upload authorization and emits sanitized provenance without persisting keys, image bytes, base64 payloads, or sensitive URL query data.
- **REQ-VISION-003:** Agnes rate limits retry until success or cancellation; network, timeout, 408, and 5xx failures use three bounded retries; non-retriable 4xx failures stop immediately.
- **REQ-ROUTE-001:** CLI-agent visual work obtains evidence through `vision-analysis`, then sends text evidence to the normal OpenCode reasoning route without claiming OpenCode can attach images to Agnes.
- **REQ-ROUTE-002:** OpenCode reasoning remains DeepSeek-first; explicit DeepSeek usage limits switch to Agnes, and Agnes rate limits remain event-driven rather than fixed-time failures.
- **REQ-ALIGN-001:** AImagician execution validates the active milestone, phase, roadmap goal, specification goal, requirement mapping, and scope before implementation or completion.
- **REQ-ALIGN-002:** Phase completion requires passing evidence and independent audit decisions for every requirement and every roadmap success criterion; passing tests alone is insufficient.
- **REQ-ALIGN-003:** Milestone completion validates all member phases and requirements, while work outside the active phase requires a user-approved, traceable exception with a return checkpoint.
- **REQ-SYNC-003:** Update taxonomy and README, add trigger and runtime regression coverage, perform a real non-sensitive Agnes image-understanding smoke test, sync Codex/OpenCode, and complete a fresh independent OpenCode audit.

### Explicit Non-goals

- Sending images through OpenCode native attachments for Agnes.
- Storing the Agnes key in the repository, skill content, command output, reports, or test fixtures.
- Image generation, audio understanding, native PDF parsing, video understanding, or automatic visual-provider ranking.
- Changing or closing the active Window-PPTX Phase 28 as part of this controlled exception.

## USR-20260730-002: Local-first delivery and shared private planning

**Status:** Accepted
**Source:** User discussion and accepted implementation plan

### Accepted Requirements

- **REQ-LOCAL-001:** Add a local-first delivery capability that maps the complete execution context before implementation and uses a risk-scaled LOCAL, CI/PREMERGE, optional PREVIEW, and POSTMERGE verification ladder.
- **REQ-GATE-001:** Add executable `premerge` and `postmerge` gates; deployable work is only complete after online confirmation and a fresh independent audit, while non-deployable work records an explicit `N/A`.
- **REQ-RECOVERY-001:** A failed postmerge check reopens the checklist, blocks further promotion, and routes to the project's documented rollback or roll-forward instead of performing a generic automatic rollback.
- **REQ-PLANNING-001:** Keep `.planning` as the project-first source of truth and support both Git-tracked and local-private storage without weakening task, phase, milestone, evidence, or handoff traceability.
- **REQ-WORKTREE-001:** Local-private planning uses one Git-common-dir store shared by all worktrees, a local Git exclude, and lock plus revision conflict detection; tracked planning retains branch semantics.
- **REQ-AUDIT-006:** Review and audit workers must use a frozen commit/tree or a fingerprinted working-tree review point and detect review-point drift.
- **REQ-SYNC-004:** Skillbird doctor must detect content drift between managed owned-skill sources and Codex/OpenCode installations, not only missing directories.
- **REQ-CI-001:** Add non-deploying pull-request CI for typecheck, tests, build, and package smoke while preserving the tag-only release workflow.
- **REQ-DOC-002:** Update the owned skills, templates, evals, README, and tests; bootstrap the final owned set to Codex/OpenCode and verify source/install parity.

### Accepted Decisions

- Remote `master` is first fast-forwarded to the previously audited `0f8216b` capability baseline.
- Full completion occurs after postmerge online evidence, not merely after merge or deployment.
- PREVIEW is risk-based; `ONLINE_ONLY` items require an explicit exception contract.
- Postmerge evidence is recorded in the corresponding `.planning` artifacts when planning exists. LLM wiki remains a cross-project macro activity record.
- Planning-only closure commits may trigger another deployment; they remain tied to the original implementation merge SHA and do not recursively create a new delivery cycle when the diff is proven metadata-only.
- Existing projects preserve their planning mode. New local-private stores are not automatically backed up and must warn about clone or machine-loss risk.
- Local-private worktrees share one canonical planning root under the Git common directory. Concurrent writes use short locks and revision checks.

### Explicit Non-goals

- Generic automatic production rollback.
- Claiming local environments are perfectly equivalent to production.
- Uploading complete private planning content to LLM wiki.
- Silently copying a local-private planning store when symlink or junction attachment fails.
- Changing or closing the active Window-PPTX Phase 28.

## USR-20260803-001: Controller-selected OpenCode models and canonical project context

**Status:** Accepted
**Source:** User discussion and accepted implementation plan
**Supersedes:** REQ-MODEL-001 and the DeepSeek-first reasoning portion of REQ-ROUTE-002. Historical audit evidence remains valid and immutable.

### Accepted Requirements

- **REQ-MODEL-V2-001:** `opencode-run.mjs` lists all active free text models across configured providers without requiring a task directory or prompt.
- **REQ-MODEL-V2-002:** Every OpenCode worker execution requires a controller-selected primary model and supports an ordered controller-selected fallback chain.
- **REQ-MODEL-V2-003:** OpenCode Zen models share one user-asserted quota pool, non-Zen provider models use model-specific pools, and Agnes is appended at most once as the final unlimited fallback.
- **REQ-MODEL-V2-004:** Fallback transitions preserve exact failure semantics, provider and quota invalidation, event-driven waiting, complete attempt provenance, and a versioned result schema.
- **REQ-MODEL-V2-005:** Visual acquisition remains owned by `vision-analysis`; the downstream OpenCode reasoning model is selected explicitly like any other text worker.
- **REQ-CONTEXT-V1-001:** Planning-managed projects can maintain one canonical `.planning/CONTEXT.md` for stable architecture, cross-phase decisions, invariants, source routing, and unresolved material questions.
- **REQ-CONTEXT-V1-002:** Context loading is risk-scaled: recent relevant sources orient the agent first, authority order resolves conflicts, and phase/milestone/High/resume work blocks on missing adopted context while isolated Quick work remains lightweight.
- **REQ-CONTEXT-V1-003:** Phase and milestone closure records and validates durable context promotion or an explicit no-change decision without rewriting historical phase records.
- **REQ-COMPAT-V2-001:** Existing DeepSeek/Agnes audits and public result fields remain valid while new controller-selected audit chains are accepted prospectively.
- **REQ-SYNC-V2-001:** Update skills, templates, docs, evals, tests, and runtime; then synchronize owned skills to Codex/OpenCode and verify installation health and content parity.

### Accepted Decisions

- Model quality is judged by the controller from task difficulty, task fit, known model behavior, context capacity, tool support, and quota diversity; the runtime does not own a static quality ranking.
- Quota policy is a versioned user assertion, not inferred provider metadata.
- Quota, rate-limit, model-unavailable, and provider authentication failures may advance the declared chain according to their invalidation scope. Permission, syntax, exhausted network retry, and worker-quality failures stop.
- Navigation recency never changes authority: latest explicit user decisions and locked requirements/specifications remain stronger than newer but lower-authority notes.
- Material uncertainty affecting behavior, architecture, interfaces, data, security, scope, acceptance, or irreversible work requires discussion. Local reversible details may proceed with a recorded assumption.

### Explicit Non-goals

- A persistent model quality leaderboard or automatic runtime scoring.
- Paid or unknown-cost model selection.
- Sending images through OpenCode attachments for Agnes.
- Rewriting historical audit sessions or completed task evidence.
- Changing or closing active Window-PPTX Phase 28.
