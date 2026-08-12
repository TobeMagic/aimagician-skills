# OpenCode Independent Completion Audit

TASK_ID: readme-darwin-runtime-cleanup-2026-08-12
ROLE: auditor
TASK_TYPE: audit
MODALITY: text
OBJECTIVE: Independently verify that the current implementation satisfies the approved README visual, Darwin Skill optimization, runtime cleanup, and synchronization requirements without changing files.
DELIVERABLE: A concise but evidence-based completion audit with a requirement matrix, findings, residual risks, and a final PASS or NEEDS_WORK decision.
REVIEW_POINT: current worktree before implementation commit
REVIEW_BINDING: --review-worktree /mnt/d/growth_up_youth/repo/skills-master-sync
SOURCE_OF_TRUTH: `.planning/REQUESTS.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/CONTEXT.md`, `.planning/ROADMAP.md`, `.planning/tasks/readme-darwin-runtime-cleanup-2026-08-12.md`, `README.md`, `docs/README.en.md`, `catalog/taxonomy.yaml`, current files under `skills/owned`, and the commands/results listed below.
ORIGINAL_REQUESTS: USR-20260812-001
ACCEPTED_DECISIONS: Work directly on the latest master; use Darwin as a measured optimization protocol; generate one static README hero and one reproducible deterministic HTML motion preview with static poster/GIF fallback; keep archive and planning evidence; remove only runtime noise; do not alter Window-PPTX behavior; push master after independent audit; synchronize only the owned set to Codex and OpenCode.
KNOWN_CONTEXT: The current project milestone is v6.1, phase 49. This is explicitly approved controlled off-phase maintenance. `window-pptx` behavior is out of scope. Old `pptx`, `modelscope_imagegen`, and `mcp-builder` entries are archived; active `window-pptx` is the retained editable PowerPoint capability. The current owned set is 24 populated, tracked, installable Skill directories across six categories. Empty untracked placeholders named `cangjie`, `nuwa`, and `darwin` are not Skills and must not be counted or committed.
REQUIRED_SKILLS:
  - aimagician-superpower: authoritative risk-scaled workflow, source-of-truth alignment, checkpoints, verification, audit, and closure
  - github-readme-highstar: README evidence, structure, visual route, integration, accessibility, and media fallback
  - interface-design: HTML visual composition, deterministic media rendering, browser/ffmpeg visual QA, and presentation boundary
  - skill-optimizer: Darwin scoring and controlled Skill treatment rules
  - cli-agent-delegator: audit prompt contract, model policy, read-only OpenCode execution, findings protocol, and evidence limits
  - vision-analysis: interpret the supplied sanitized visual evidence without pretending the worker has image attachments
BEFORE_SUBSTANTIVE_WORK: Load every skill named in REQUIRED_SKILLS and report the loaded IDs. Read the source-of-truth files before forming findings. If a required source cannot be loaded, return NEEDS_CONTEXT instead of inventing a replacement.
ALLOWED_SCOPE: Read-only inspection of the review worktree, its Git metadata, owned Skill instructions, README/docs/planning records, catalog, generated README assets, and local verification metadata.
FORBIDDEN_SCOPE: Do not edit, create, delete, rename, install, commit, push, reset, checkout, clean, or mutate any file. Do not access the controller's dirty worktree. Do not inspect or print secrets, environment values, API keys, raw image bytes, or private external source mirrors.
PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: `git status`, `git diff`, `git diff --check`, `git log`, `rg`, `find`, `sed`, `awk`, `wc`, `node` read-only checks, `npm pack --dry-run`, `ffmpeg` decode/metadata checks if available, and existing repository validation commands that do not write files.
TESTS_AND_EVIDENCE: Prior controller evidence includes `format-skills --check` PASS for 24 formatted Skill records; `npm run typecheck` PASS; focused expert Skill tests PASS 14/14; full `npm test` PASS 29 files and 178 tests; `npm run build` PASS; `git diff --check` PASS before final documentation/media-only adjustments; browser rendering PASS at 1600x900 and 960x540 with no console/page errors; deterministic render PASS for poster and GIF (8 seconds, 1600x900 poster, 960x540 GIF, 8 fps); ffmpeg decode PASS, while the repository verifier could not run because `ffprobe` is unavailable. Re-check current evidence and mark unavailable checks as NOT_RUN rather than PASS.
CATALOG_EXPECTATION: Verify the README count is 24 and matches the current populated, tracked, installable `skills/owned` directories. Verify the six category labels and current CLI identity. Treat catalog entries without an owned directory as disabled/legacy references, not active installed Skills.
MODEL_POLICY: The controller selected `opencode/deepseek-v4-flash-free` as the primary free reasoning model because the task is a medium-complexity audit. A stronger available free OpenCode model may be selected only with a stated reason. Agnes is a fallback for quota exhaustion, not a reason to skip source inspection.
CHILD_AGENT_POLICY: Do not spawn child agents or delegate further.
GIT_POLICY: Inspect-only. Do not mutate Git state. Report the review worktree status and distinguish pre-existing commits from uncommitted changes.
STATUS_PROTOCOL: Start with PREFLIGHT, then emit short progress updates for source loading and verification, then final report. Do not claim completion from test status alone.
FINDING_SEVERITY: Blocker prevents truthful delivery or violates scope/safety; Important leaves a required capability, requirement, or acceptance path incomplete; Nitpick is non-blocking polish or documentation drift.
STOP_AND_ESCALATE: Stop with NEEDS_WORK if any Blocker or Important is found, if the implementation changes Window-PPTX behavior, if README claims cannot be reconciled with the current owned set, or if the review point cannot be bound to this worktree.
SESSION_EXPORT: Not required. Report the OpenCode session ID if the runner returns one; do not fabricate an export.

## Visual Evidence From Controller

The controller inspected the generated static hero and regenerated deterministic demo poster locally. The visual-analysis skill then supplied sanitized evidence from those two images using Agnes `agnes-2.0-flash`, one successful attempt, with no rate-limit event. The controller must treat this as evidence, not as a substitute for inspecting the HTML/README source:

- The generated hero is an abstract local-first catalog-to-agent flow with a warm paper background, dark panels, cyan/amber/coral routes, generous negative space, and no readable fake product copy.
- The deterministic poster visibly presents “One catalog. Every agent.”, the six categories, the `global / project` scope, the CLI install command, and Codex/OpenCode/Claude target panels. The poster was regenerated after correcting the active count to 24 and narrowing the terminal panel to avoid overlapping the third target.
- The local controller spot-check found no browser console/page errors. `ffmpeg` decoded the media; the official motion verifier remains NOT_RUN because `ffprobe` is not installed.
- Do not turn the visual analysis's generic caution about recognizable target names into a finding by itself: those names represent actual supported install targets in this repository. Raise a finding only if the source or README falsely claims unsupported integrations or if the rendered layout obscures content.

## Required Audit Questions

1. Does the root README embed a truthful static hero, a repository-relative dynamic preview, and a reproducible source/static fallback?
2. Does the English README match the root README on current count, categories, archive boundary, CLI identity, and PPTX/HTML design boundary?
3. Do `aimagician-superpower` and `github-readme-highstar` show measurable, observable Darwin improvements without losing their prior capabilities or adding repository-specific workflow pollution?
4. Are old external or archived entries kept out of the active owner install path while the required archive/planning/history remains recoverable?
5. Are generated caches and `skills/*/evals` absent from the runtime source/package, with no unrelated deletion?
6. Do the listed local checks support the changed surfaces, and are unavailable checks honestly marked?
7. Is the implementation ready for a master commit and owner-only Codex/OpenCode synchronization, or is a correction required first?

## Required Output

Return exactly this high-level structure:

# OpenCode Audit Report
## 1. Preflight Result
- OpenCode status, version/model, project path, review binding, loaded required Skills, write policy
## 2. Requirement Matrix
| Requirement | Evidence inspected | Verdict | Notes |
| --- | --- | --- | --- |
Include `README-01`, `README-02`, `SKILL-OPT-02`, `CLEAN-01`, and `VERIFY-01`.
## 3. Findings
List every Blocker, Important, and Nitpick with file paths and concrete evidence. State `None` explicitly for empty severities.
## 4. Capability And Scope Audit
Cover README routing, Darwin changes, archive/runtime boundary, active owner count, and Window-PPTX exclusion.
## 5. Verification Review
Separate PASS, FAIL, and NOT_RUN. Do not promote `ffprobe` or any unobserved check to PASS.
## 6. Final Decision
Return `PASS` only when no Blocker/Important remains and all required scope is covered. Otherwise return `NEEDS_WORK` with the smallest next correction.
