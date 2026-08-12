# README, Darwin, And Runtime Cleanup Audit

**Status:** Complete  
**Task:** `readme-darwin-runtime-cleanup-2026-08-12`  
**Source request:** `USR-20260812-001`  
**Reviewed implementation point:** pushed master implementation commit `2169c88` (the exact frozen worktree content reviewed before commit)
**Parent context:** v6.1 Phase 49; Window-PPTX behavior was explicitly out of scope.

## Outcome

The repository now presents Skillbird with a generated static hero, a deterministic HTML demo, a repository-relative GIF, and a static poster fallback. The active owner set is truthfully 24 populated, tracked, installable Skills across six categories. Archived Skills, planning evidence, and the external evaluation corpus remain recoverable outside the runtime install path.

The first independent audit rejected a temporary count of 27 because `cangjie`, `darwin`, and `nuwa` were empty untracked directories rather than Skills. Those placeholders were removed, all count-bearing media was regenerated at 24, and the second audit passed.

## Requirement Matrix

| Requirement | Status | Evidence |
|---|---|---|
| README-01 | PASS | Root and English README embed the static hero and GIF; HTML source and poster fallback are repository-relative and present. |
| README-02 | PASS | Both READMEs state 24 active owned Skills, six categories, `skillbird`, archive boundary, and the HTML/`window-pptx` delivery boundary. |
| SKILL-OPT-02 | PASS | `aimagician-superpower` gained three completion checkpoints; `github-readme-highstar` gained evidence/structure/visual/integration passes, trigger boundaries, and failure handling. |
| CLEAN-01 | PASS | Seven tracked Python cache files removed; cache patterns expanded in `.gitignore`; no `skills/*/evals`, `__pycache__`, or empty owned placeholders remain. |
| VERIFY-01 | PASS | Typecheck, tests, build, format check, package dry-run, browser assertions, media render/decode, catalog count, and independent audit completed. |

## Darwin Treatment

The controlled static rubric used `skills/owned/skill-optimizer/scripts/audit-skill.mjs`. Only Skills with a meaningful observed gap were changed.

| Skill | Baseline | Treatment | Delta | Result |
|---|---:|---:|---:|---|
| `aimagician-superpower` | 65.6 | 70.4 | +4.8 | Requirement-to-verification checkpoints retained |
| `github-readme-highstar` | 41.3 | 66.2 | +24.9 | Pass-based workflow, trigger boundary, and failure handling retained |
| `interface-design` | 74.0 | 74.0 | 0.0 | No treatment; sibling boundary preserved |
| `cli-agent-delegator` | 57.2 | 57.2 | 0.0 | No treatment; delegation contract preserved |
| `agent-workstream-orchestrator` | 60.8 | 60.8 | 0.0 | No treatment; session/worktree routing preserved |

These scores are static quality evidence only; behavioral tests, source inspection, and independent review remain required.

## Visual Evidence

`vision-analysis` inspected the generated hero and regenerated poster through Agnes `agnes-2.0-flash` with explicit external-upload authorization. The run succeeded in one attempt with no rate-limit event.

- The hero communicates a central local-first catalog distributing capabilities to multiple agent destinations without fake logos or readable pseudo-copy.
- The poster communicates the six categories, `GLOBAL / PROJECT`, the install command, the source-of-truth panel, and real supported Codex/OpenCode/Claude targets.
- Browser checks at 1600x900 and 960x540 found `__VISUAL_READY__`, six categories, three targets, one active state at a deterministic timestamp, no console/page errors, and zero target/terminal overlap.
- The motion verifier that requires `ffprobe` was not run because `ffprobe` is unavailable. `ffmpeg` rendered and decoded the poster/GIF successfully; the missing verifier is recorded as `NOT_RUN`, not `PASS`.

## Verification

| Check | Result |
|---|---|
| `npm run typecheck` | PASS |
| `npm test` | PASS, 29 files and 178 tests |
| `npm run build` | PASS |
| `node dist/cli/index.js format-skills --check` | PASS, 24 Skills, no issues |
| `git diff --check` | PASS |
| `npm pack --dry-run --json` | PASS, 843 files; no `.planning`, `quality`, tests, evals, pyc, or cache paths |
| `skills/owned` count | PASS, 24 tracked/populated Skills; six taxonomy groups |
| `find skills -type d -name evals` | PASS, none |
| `find . -name __pycache__` | PASS, none outside ignored dependencies |
| Browser and media checks | PASS |
| `ffprobe` motion verifier | NOT_RUN, executable unavailable |

## Independent OpenCode Audit

**Provider:** OpenCode  
**Primary model:** `opencode/deepseek-v4-flash-free`  
**Final model:** `agnes/agnes-2.0-flash`  
**Attempt chain:** `opencode/deepseek-v4-flash-free` -> `agnes/agnes-2.0-flash`  
**Fallback reason:** DeepSeek rate-limit response during the second audit; the runner selected the configured Agnes fallback.  
**Session:** `ses_0099b3604ffeFzWHlpGCI2n1Go`  
**Run status:** PASS  
**Review point:** strict read-only `--review-worktree` against the implementation worktree at `047627257cbfb617a324f0e9e704789c9533edd0`, committed without content changes as `2169c88`
**Controller spot-check:** Local image inspection, Agnes visual evidence, browser assertions, ffmpeg decode, package exclusion check, and source/README count parity.  
**Requirement matrix:** PASS  
**Blocker:** None  
**Important:** None  
**Nitpick:** README asset paths intentionally differ by document location: root uses `./docs/assets`, English README uses `./assets`; both resolve correctly.

The audit loaded `aimagician-superpower`, `github-readme-highstar`, `interface-design`, `skill-optimizer`, `cli-agent-delegator`, and `vision-analysis` before substantive review. It confirmed no Window-PPTX diff, and the controller subsequently completed the approved commit/push and owner-only target synchronization.

## Delivery

`2169c88` was pushed to `origin/master`. The post-commit owner-only synchronization and target health checks are recorded by the controller after this audit; no non-owned Skill is part of the source set.

## Scope Closure

No user worktree, private asset, Window-PPTX behavior, historical phase record, archive entry, or external installer was changed. Runtime packages continue to exclude planning records and evaluation corpora while preserving the archive directory for explicit recovery.
