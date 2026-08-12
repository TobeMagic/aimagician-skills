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
## Window-PPTX v6 Request Chain

**Updated:** 2026-07-29

## USR-V6-01: Reset the rejected visual-quality floor

**Status:** Accepted
**Source:** User request and visual rejection of current trials

### Original Request

The current generated decks and iteration requirements are shallow and do not
reach the accepted reference deck or a senior presentation designer's level.
Do not stop at recommendations; implement, test, compare, and iterate.

### Accepted Decisions

- Preserve v5.1 as an explicit `NO_GO` archive.
- v6.0 optimizes for reference-grade customer delivery before weak-model
  generalization.

### Derived Requirements

- V6-DESIGN-01
- V6-DECK-01
- V6-QA-01
- V6-EVID-01
- V6-REL-01

### Exclusions

- Treating deterministic engineering scores as visual acceptance.

## USR-V6-02: Use a stronger default authoring model

**Status:** Accepted
**Source:** User decision

### Original Request

Use Codex GPT-5.5 medium as the quality-first authoring model so the Skill can
first prove reference-level output.

### Accepted Decisions

- GPT-5.5 medium owns v6.0 narrative and visual selection.
- Weak-model distillation begins only after v6.0 GO.

### Derived Requirements

- V6-DESIGN-01
- V6-UAT-01

### Exclusions

- v6.0 release claims based on DeepSeek-only authoring.

## USR-V6-03: Build realistic scenario requirements

**Status:** Accepted
**Source:** User request and locked planning discussion

### Original Request

Create requirements that look like complete real client requests, including
detailed data, materials, copy, audience, timing, decisions, and acceptance
criteria for campus competition, work reports, academic defenses, and other
common scenarios.

### Accepted Decisions

- Three complete flagships plus twelve locked skeletons.
- Synthetic standardized facts are allowed when explicitly labeled and
  source-bound.
- Formal generation requires discussion lock.

### Derived Requirements

- V6-BRIEF-01
- V6-CORPUS-01

### Exclusions

- Shallow one-fact-per-slide benchmark prompts.

## USR-V6-04: Require complete deck anatomy

**Status:** Accepted
**Source:** User request

### Original Request

Generated decks need cover, directory, chapter pages, title hierarchy,
conclusion, ending, appendix, and scenario-appropriate sections instead of a
sequence of generic text pages.

### Accepted Decisions

- Long decks require directory and section dividers.
- The three flagships use fixed main/appendix slide budgets.

### Derived Requirements

- V6-BRIEF-01
- V6-CORPUS-01
- V6-DECK-01

### Exclusions

- Adding empty structural pages without narrative function.

## USR-V6-05: Build a governed Gaojie-style template library

**Status:** Accepted
**Source:** User request referencing the Gaojie category taxonomy

### Original Request

Discover and manage the full entitled catalog, including cover, directory,
section, title, ending, one-to-six and multi-content, people, awards, maps,
timelines, process, business model, mockup, quote, partners, image-text,
charts, tables, images, practical materials, palettes, topics, data bases,
text components, decorations, excellent works, and launch templates.

### Accepted Decisions

- Originals remain under the Skill's ignored private directory.
- Full discovery is resumable; certification is staged.
- Complete works are visual spines and direct TemplatePack reuse is allowed
  only with rights evidence.

### Derived Requirements

- V6-ASSET-01
- V6-LIB-01
- V6-DECK-01

### Exclusions

- Access-control bypass, unlicensed redistribution, or committing private
  originals.

## USR-V6-06: Reach the accepted reference's art direction

**Status:** Accepted
**Source:** User-supplied `工作总结.pptx` and approved plan

### Original Request

Match the reference's hierarchy, page rhythm, motif continuity, visual
richness, data presentation, and complete-work polish without merely copying
its text or placing content into generic cards.

### Accepted Decisions

- Extract reusable ArtDirectionProfile rules.
- Recombine design logic; do not copy protected identity or distinctive media
  without authorization.

### Derived Requirements

- V6-DESIGN-01
- V6-DECK-01
- V6-UAT-01

### Exclusions

- Page-by-page unauthorized copying.

## USR-V6-07: Simplify repair and improve components

**Status:** Accepted
**Source:** User request

### Original Request

Remove redundant component repair and shallow block decoration. Use better
template selection, motifs, imagery, diagrams, and bounded correction.

### Accepted Decisions

- One deterministic repair, one same-family reselection, and one visual replan
  are the complete loop.

### Derived Requirements

- V6-QA-01
- V6-DECK-01

### Exclusions

- Unlimited heuristic repair passes.

## USR-V6-08: Keep PPTX portable and editable without mandatory COM

**Status:** Accepted
**Source:** User discussion about COM, HTML conversion, and alternatives

### Original Request

Do not make the broken PowerPoint COM environment a production dependency.
Preserve editable PowerPoint capabilities through portable OOXML/PptxGenJS and
independent rendering.

### Accepted Decisions

- Native editable PPTX is canonical.
- HTML is proof-only.
- COM is optional read-only diagnostics/certification.

### Derived Requirements

- V6-PORT-01
- V6-PORT-02

### Exclusions

- Whole-slide raster delivery or HTML as canonical PPTX source.

## USR-V6-09: Use fully independent AI-only blind review

**Status:** Accepted
**Source:** Latest explicit user decision

### Original Request

Replace human scoring completely with blind AI reviewers that have fully
independent contexts.

### Accepted Decisions

- Three fresh anonymous visual-capable review contexts.
- No reviewer sees generator traces or other scores.
- Unavailable image input yields `NOT_RUN`; no two-reviewer fallback.

### Derived Requirements

- V6-UAT-01
- V6-AUDIT-01
- V6-REL-01

### Exclusions

- Human scoring, manual score override, or self-review by the generator
  context.

## USR-V6-10: Implement, verify, iterate to GO, then commit and push

**Status:** Accepted
**Source:** Repeated user execution instructions

### Original Request

Implement the plan, generate multiple complete PPTX files, compare against the
reference and previous trials, keep iterating until milestone acceptance, then
organize commits and push.

### Accepted Decisions

- Use `.planning` phases 36–41 and preserve durable evidence.
- Push v6 only after release gates and fresh Agnes completion audit pass.

### Derived Requirements

- V6-EVID-01
- V6-DOC-01
- V6-AUDIT-01
- V6-REL-01

### Exclusions

- Declaring completion from code changes or test summaries alone.

## USR-V6-11: Reopen the rejected v6 result and use the real private catalog

**Status:** Accepted
**Source:** Latest user visual rejection and acquisition authorization

### Original Request

The current trial quality still does not show the supplied reference or
excellent commercial works. Use Playwright to download the complete entitled
catalog for local use, ignore private assets in Git, and implement the actual
result rather than optimizing portability first.

### Accepted Decisions

- Invalidate the previous v6 GO and reopen the milestone.
- Acquire all requested categories through the normal authenticated UI.
- Store credentials, originals, state, and mining artifacts only under the
  ignored Skill-local `.private/` tree.
- Certify a 300–500-page core first while full acquisition remains resumable.
- Actual template selection must be materialized, not written only as manifest
  metadata.
- Three realistic anchors must reach the reference art-direction level before
  fifteen-scenario and ordinary-model expansion.
- Any independent AI visual `Blocker` or `Important` finding blocks promotion.

### Derived Requirements

- V6R-GROUND-01
- V6R-ACQ-01
- V6R-MINE-01
- V6R-MAT-01
- V6R-ANCHOR-01
- V6R-WEAK-01
- V6R-UAT-01
- V6R-REL-01

### Exclusions

- Access-control bypass, credential leakage, redistribution, whole-slide
  raster output, or claiming code variants as downloaded templates.

## USR-V6-12: Select visually diverse templates inside every real category

**Status:** Accepted
**Source:** User direction after authenticated Gaojie access was restored

### Original Request

Continue without stopping unless user intervention is required. Every category
contains many weakly named PPT items, so inspect their images and download a
highly differentiated, reusable subset rather than mechanically taking the
first items or accumulating near-duplicates.

### Accepted Decisions

- The Gaojie template source of truth is the 32 nonzero categories under
  `products.aspx`; other site sections are inventoried separately and cannot
  overwrite template categories with the same numeric `category_id`.
- Inventory every product card and preview image before selecting downloads.
- Use deterministic image features and farthest-first selection to reject
  exact and near-duplicate previews and preserve style, color, density, and
  composition variation.
- Target 12 representatives per sufficiently populated category, producing a
  roughly 300–400-template private core; retain all items only when a category
  contains fewer candidates and report the shortfall.
- Phase 44 must render the downloaded PPTX files and perform a second
  cross-category visual/structural deduplication before certification.
- Authentication expiry, CAPTCHA, entitlement rejection, or site blocking are
  the only expected reasons to request user intervention during acquisition.

### Derived Requirements

- V6R-ACQ-01
- V6R-MINE-01

### Exclusions

- First-N selection, title-only classification, downloading all near-duplicate
  items, uploading credentials to a reviewer, or claiming thumbnail diversity
  as final rendered-slide quality.

## USR-V61-01: Physical certified-page assembly before the v7 studio migration

**Status:** Accepted
**Source:** User instructions to implement the discussed Skill-first generation
chain, use `gpt-5.6-terra` medium, physically reuse downloaded templates, and
continue until milestone acceptance.

### Original Request

Given only a realistic complete requirement folder and the installed Skill,
Codex must independently plan a complete high-quality PPTX, find the most
suitable certified template for every page, physically reuse and adapt it,
and deliver a result no worse than the source templates. The clean client
folder must not contain the reference deck or private template bytes.

### Accepted Decisions

- The locked tracer is a 15-slide hospital-finance annual work report.
- Every accepted slide has physical template lineage; generated visual
  fallback does not count.
- `gpt-5.6-terra` medium chooses narrative, candidate IDs, and fact/asset
  bindings, but cannot author geometry, raw style tokens, OOXML, or release
  scores.
- One dominant style family governs the deck; controlled compatible fallback
  is explicit, never random.
- COM is optional read-only certification and cannot block delivery.
- Recursive OPC integrity, native editability, bounded package size, clean-room
  generation, three independent visual reviews, and a fresh completion audit
  are hard release gates.
- The approved subsequent milestone renames the product to `pptx-studio` and
  completely removes `window-pptx`; no permanent compatibility shell remains.

### Derived Requirements

- V61-LIB-01
- V61-SEL-01
- V61-ASM-01
- V61-ADAPT-01
- V61-QA-01
- V61-CLEAN-01
- V61-REL-01

### Exclusions

- Shipping reference-only pages as direct-use templates.
- Rasterized whole-slide delivery, mandatory COM, hidden native-layout
  fallback, arbitrary model-written geometry/code, or release by self-score.
- Performing the v7 rename and destructive private-asset pruning inside Phase
  49; those changes begin only after the stabilized v6.1 baseline is merged.

## USR-20260811-001: Runtime-pure Skills, project memory, and session orchestration

**Status:** Accepted
**Source:** User direction on 2026-08-11

### Original Request

Archive redundant runtime Skills, remove Skill-local eval directories, use the
Darwin Skill optimization workflow on core Skills, evolve parallel worktree
handling into tracked multi-session task orchestration, move Linear behavior
into project preferences, and add durable project and daily memory to the main
engineering workflow.

### Accepted Decisions

- Implement from the latest `origin/master` without mutating the user's active
  Window-PPTX worktree.
- Archive `pptx`, `modelscope_imagegen`, `mcp-builder`, and
  `linear-issue-workflow` from the active owner set.
- Move evaluation fixtures out of installed Skill packages into a repository
  quality surface; preserve useful regression evidence instead of deleting it.
- Replace `parallel-worktree-pr-flow` with a provider-neutral workstream
  orchestrator where sessions, worktrees, branches, PRs, Codex, and OpenCode
  are selected by task coupling and risk.
- Keep project preferences and durable memory under `.planning`; runtime Skills
  define only the generic discovery, read, write, promotion, and safety rules.
- Use `skill-optimizer` static and behavioral evidence to accept core Skill
  changes; prose growth without measurable workflow improvement is rejected.

### Derived Requirements

- SKILL-PURE-01
- SKILL-ARCHIVE-01
- SKILL-EVAL-01
- SKILL-ORCH-01
- SKILL-MEM-01
- SKILL-OPT-01

### Exclusions

- Window-PPTX or PPTX-Studio implementation changes.
- Deleting user worktrees, untracked acceptance artifacts, source mirrors, or
  historical planning evidence.
- Recording secrets, raw transcripts, or unverified claims in project memory.

## USR-20260812-001: Master README visual upgrade, Darwin refinement, and repository cleanup

**Status:** Accepted
**Source:** User instruction on 2026-08-12 after plan discussion

### Original Request

Fast-forward the repository to the latest master baseline, continue work on the
master branch, inspect remaining optimization opportunities and Darwin results,
use image generation to improve the Skill README presentation, and simplify
unused files or folders without weakening owned Skill capability or deleting
valuable history.

### Accepted Decisions

- Use a fast-forward master strategy and work only in the clean master-sync
  worktree; preserve the user's dirty Window-PPTX worktree.
- Use a static generated hero plus a deterministic dynamic preview with a
  repository-relative source and static fallback.
- Optimize runtime noise and stale current documentation, but keep archived
  Skills, planning records, quality evidence, and required runtime assets
  recoverable.
- Use the repository's `skill-optimizer` Darwin protocol rather than adding a
  duplicate Darwin Skill.

### Derived Requirements

- README-01
- README-02
- SKILL-OPT-02
- CLEAN-01
- VERIFY-01

### Exclusions

- Window-PPTX behavior or private asset changes.
- Reintroducing third-party installers or Skill-local evaluation corpora.
- Deleting historical phase, audit, archive, or user-owned worktree data.
