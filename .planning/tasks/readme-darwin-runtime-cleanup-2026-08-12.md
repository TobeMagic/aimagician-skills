# README, Darwin, And Runtime Cleanup

**Status:** Complete  
**Source request:** `USR-20260812-001`

## Control

- User source: `USR-20260812-001`
- **Parent milestone:** `v6.1`
- **Parent phase:** `49`
- **Exception status:** Approved
- **Approval source:** `USR-20260812-001`
- Task class: controlled off-phase repository maintenance
- **Return checkpoint:** preserve Phase 49 Window-PPTX scope and return to its workflow completion gate after this task
- Allowed scope: README visuals, README integration, Skill trigger/workflow instructions, planning truth records, generated caches, and package/owner-set verification
- Forbidden scope: Window-PPTX behavior, private assets, active user worktrees, third-party source reintroduction, and deletion of historical phase evidence

## Goal

Improve README product communication and repository hygiene while using the measured Darwin protocol to strengthen only observable Skill routing and workflow gaps.

## Requirements

- **README-01:** The root README has a truthful static Skillbird hero and a repository-relative dynamic preview with a reproducible source and static fallback.
- **README-02:** Root and English README content describes the current 24 active owned Skills, archive boundary, six categories, and current CLI identity without stale active Skill names.
- **SKILL-OPT-02:** Darwin treatment improves README routing and explicit engineering checkpoints without weakening existing capability or sibling boundaries.
- **CLEAN-01:** Generated caches and obvious runtime noise are ignored or removed; planning evidence, archives, and required runtime assets remain recoverable.
- **VERIFY-01:** Typecheck, build, tests, package dry-run, visual media checks, catalog parity, target sync checks, and an independent audit provide evidence for the changed surfaces.

## Darwin Evidence

The controlled baseline/treatment run used `skills/owned/skill-optimizer/scripts/audit-skill.mjs` with the same static rubric and current worktree treatment. Only the two Skills with meaningful gaps were changed; the remaining routing Skills were checked for regression.

| Skill | Baseline | Treatment | Delta | Decision |
|---|---:|---:|---:|---|
| `aimagician-superpower` | 65.6 | 70.4 | +4.8 | Keep three requirement-to-verification checkpoints |
| `github-readme-highstar` | 41.3 | 66.2 | +24.9 | Keep pass-based workflow, trigger boundary, and failure handling |
| `interface-design` | 74.0 | 74.0 | 0.0 | No treatment needed; preserve sibling boundary |
| `cli-agent-delegator` | 57.2 | 57.2 | 0.0 | No treatment needed; preserve delegation contract |
| `agent-workstream-orchestrator` | 60.8 | 60.8 | 0.0 | No treatment needed; preserve session/worktree routing |

The score changes are static quality evidence, not a substitute for behavioral tests or visual inspection. The independent OpenCode audit remains the final completion gate.

## Original Request

Fast-forward to the latest master baseline, work directly on master, inspect remaining optimization opportunities and Darwin results, improve the Skillbird README presentation with image generation, and simplify unused runtime files or folders without weakening owned Skill capability or deleting valuable history.

## Accepted Decisions

- Use the clean master-sync worktree and preserve the user's dirty Window-PPTX worktree.
- Use a generated static hero plus a deterministic HTML/GIF preview with a static poster fallback.
- Treat `skill-optimizer` as the Darwin protocol; do not add a duplicate runtime Skill.
- Keep archives, planning evidence, quality evidence, and required runtime assets recoverable.

## Checklist

- [x] Generate and inspect README hero.
- [x] Render and verify demo poster/GIF from deterministic HTML.
- [x] Update README, English README, and active routing references.
- [x] Re-run Darwin static audits and record accepted deltas.
- [x] Remove only current generated caches and confirm no `skills/*/evals` remains.
- [x] Run local verification and independent OpenCode audit against the frozen implementation revision.
- [x] Commit and push `master`; synchronize Codex/OpenCode and verify owner-only installation.

## Evidence

| Requirement | Evidence | Status |
|---|---|---|
| README-01 | Root and English README embed the static hero and GIF; deterministic HTML source and poster fallback exist under `docs/assets`. | PASS |
| README-02 | Both READMEs state 24 active owned Skills, six categories, `skillbird`, archive boundary, and current presentation boundary. | PASS |
| SKILL-OPT-02 | Darwin table records `aimagician-superpower` +4.8 and `github-readme-highstar` +24.9 with unchanged sibling scores. | PASS |
| CLEAN-01 | Seven tracked pycache files removed, cache patterns ignored, no `skills/*/evals`, pycache, or empty owned placeholders remain. | PASS |
| VERIFY-01 | Typecheck, 29-file/178-test suite, build, format check, package dry-run, browser/media checks, and OpenCode audit passed. | PASS |

## Final Decision

Implementation and delivery requirements are complete. Commit `2169c88` is pushed to `origin/master`, and the managed Codex/OpenCode targets both report a healthy owner-only set of 24 active Skills. The independent audit reviewed the frozen implementation revision; the remaining closure records are metadata-only.

## Independent Completion Audit

**Provider:** OpenCode  
**Model:** `agnes/agnes-2.0-flash`  
**Primary model:** `opencode/deepseek-v4-flash-free`  
**Attempt chain:** `opencode/deepseek-v4-flash-free` -> `agnes/agnes-2.0-flash`  
**Fallback reason:** DeepSeek rate limit during the second audit; `opencode-run.mjs` selected the configured Agnes fallback.  
**Session:** `ses_0099b3604ffeFzWHlpGCI2n1Go`  
**Run status:** PASS  
**Review point:** Strict read-only `--review-worktree` at implementation HEAD `047627257cbfb617a324f0e9e704789c9533edd0`; task/audit records after review are metadata-only closure evidence.  
**Controller spot-check:** Inspected both generated images, ran Agnes visual analysis, browser assertions with no console/page errors, verified zero target/terminal overlap, decoded media with ffmpeg, checked package exclusions, and reconciled 24 populated owned Skills with README/taxonomy.  
**Result schema:** v2  
**Model selection rationale:** DeepSeek was the preferred free model for the medium-complexity audit; Agnes is the configured final fallback for rate limits.  
**Declared model chain:** `opencode/deepseek-v4-flash-free` -> `opencode/nemotron-3-ultra-free` -> `agnes/agnes-2.0-flash`  
**Effective model chain:** `opencode/deepseek-v4-flash-free` (rate limited) -> `agnes/agnes-2.0-flash`  
**Model transitions:** Primary DeepSeek exhausted its provider quota during title/audit startup; the runner continued with Agnes and completed the audit.  
**Requirement matrix:** PASS  
**Blocker:** None  
**Important:** None  
**Nitpick:** README asset path syntax differs by document location but both paths resolve correctly.

## Current Checkpoint

Implementation, independent audit, commit/push, and owner-only Codex/OpenCode synchronization are complete. The first audit rejected a temporary 27-count claim; the empty untracked placeholders were removed, count-bearing assets were regenerated at 24, and the second audit passed. Commit `2169c88` is pushed to `origin/master`; both managed targets report 24 detected and 24 managed active Skills with no issues.
