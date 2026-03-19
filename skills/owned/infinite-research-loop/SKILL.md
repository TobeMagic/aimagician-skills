---
name: infinite-research-loop
description: |
  Run a self-directed experiment loop for any task that can improve through repeated edits plus measured feedback.
  Use when the user wants "overnight experiments", "auto tuning", "autonomous iteration", "loop testing",
  or an unattended research workflow. In GSD-managed repos, use this skill as the inner experiment executor
  inside an existing phase or quick task instead of creating a parallel planning flow. Before the loop starts,
  discuss and lock the objective metric, writable scope, eval command, time budget, and stop conditions into
  `program.md`.
compatibility:
  tools: [bash, git, python]
  requires: Git-initialized project with a runnable eval or test command
---

# Infinite Research Loop

Reference: https://github.com/karpathy/autoresearch/tree/master

The core idea comes from Karpathy's autoresearch:
write a `program.md` as the agent's operating contract, then let the agent run
many small experiments without asking the user whether to continue.

This skill is the inner experiment engine.
If the repo already uses GSD, then GSD remains the outer control plane:

- GSD decides the broader task, phase, and verification path.
- This skill executes the narrow repeated search loop inside that boundary.

## Operating Modes

Choose the smallest mode that fits the repo:

- `GSD mode`
  Use this when `.planning/STATE.md`, `.planning/phases/`, or `.planning/quick/`
  exists. Reuse the active phase or quick-task objective instead of inventing a
  separate roadmap.
- `Standalone mode`
  Use this when the repo is not managed by GSD. `program.md` becomes the only
  execution contract.

## GSD Integration

When GSD artifacts exist, treat them as upstream source of truth.

Read only the minimum context needed:

1. `.planning/STATE.md`
2. The active phase or quick-task plan
3. The latest `UAT.md` or `VERIFICATION.md` if the loop is trying to close a known gap

Then apply these rules:

- Reuse the active goal, constraints, and success criteria from GSD.
- Narrow the loop to one writable file or one tightly scoped module.
- Do not create a second roadmap, milestone, or independent planning track.
- Keep commits atomic so they remain compatible with GSD's normal verification flow.
- When the loop finishes, hand back a concise summary that can feed directly into
  `$gsd-verify-work`, `$gsd-plan-phase`, or `$gsd-quick --full`.

If the repo is GSD-managed but the active scope is still ambiguous, resolve the
missing details during the initial discussion before writing `program.md`.

## Before You Start: Discuss With The User

Do not start the loop before these parameters are explicit.

Confirm:

1. Objective metric
   What exactly are we optimizing? Where do we read the number?
2. Baseline
   What is the current best result or current stable commit?
3. Writable scope
   Which single file may the agent modify? What is strictly read-only?
4. Eval method
   What exact command runs one experiment? Which file and field hold the result?
5. Time budget
   What is the per-run timeout, and what is the total session budget?
6. Exploration focus
   What dimensions should this session prioritize, and what should be skipped?
7. GSD handoff
   If this is a GSD repo, which phase or quick task does this loop belong to,
   and what command should the user run after the loop finishes?

Once agreed, write the parameters into `program.md`.

## `program.md` Format

`program.md` lives in the project root and becomes the loop's only execution contract.
Humans revise it. The agent follows it strictly.

```md
# program.md — [PROJECT_NAME]

## Objective

METRIC:    [metric_name]
DIRECTION: [lower|higher] is better
BASELINE:  [current best value or commit]
SUCCESS_THRESHOLD: [minimum meaningful improvement]

## GSD Context

MODE:            [phase|quick|standalone]
SOURCE_OF_TRUTH: [path to active PLAN.md, quick task, or "manual"]
HANDOFF_HINT:    [$gsd-verify-work 3 | $gsd-quick --full ... | none]

## File Permissions

WRITABLE:  [single file path]
READONLY:  [file1, file2, ...]

## Experiment Rules

TIME_LIMIT:      [N] min
SESSION_LIMIT:   [optional total time or experiment count]
EVAL_COMMAND:    [shell command]
RESULT_PATH:     [path/to/result/file]
RESULT_FIELD:    [json key, jq path, or parser note]
REVERT_STRATEGY: [prefer restoring only WRITABLE]
COMMIT_FORMAT:   "exp: {description} | {metric}: {value}"

## Exploration Focus

- [dimension_1]
- [dimension_2]
- [dimension_3]

## Excluded Directions

- [what not to try]

## Fallback

1. Re-read the WRITABLE file and referenced libraries
2. Re-read nearby project files from a fresh angle
3. Combine near-miss ideas from previous runs
4. Try a more aggressive but still scoped change

## Termination

- User interrupts
- Session limit reached
- Metric reaches target
- No credible ideas remain
```

## Execution Loop

Once `program.md` exists, run this loop without stopping for permission:

```text
loop:

1. propose one reversible idea
2. modify WRITABLE only
3. run EVAL_COMMAND with TIME_LIMIT
4. read RESULT_PATH and parse RESULT_FIELD
5. decide:
   - trivial failure        -> fix once and re-run
   - fundamental failure    -> log FAILED and revert WRITABLE scope
   - timeout / crash        -> log FAILED and revert WRITABLE scope
   - metric improved        -> git commit atomically with COMMIT_FORMAT
   - metric degraded        -> revert WRITABLE scope
6. if out of ideas -> execute Fallback from program.md
7. never ask the user whether to continue
```

## Loop Discipline

Follow these rules throughout execution:

- Change only `WRITABLE`.
- Prefer one idea per experiment so results stay interpretable.
- Save or print enough output to explain why an experiment passed or failed.
- Be conservative with rollback.
- Preserve good commits; do not squash multiple experiments into one commit.
- Respect user interrupt immediately.

## Revert Policy

Prefer the smallest rollback that restores the pre-experiment state:

- First choice:
  restore only `WRITABLE`
- Second choice:
  revert only the files explicitly allowed by `program.md`
- Last resort:
  broader git reset, but only if the experiment scope is isolated and
  `program.md` explicitly allows it

This keeps the loop compatible with GSD's atomic-commit and state-tracking style.

## Failure Handling

- Expected runtime per experiment is about 5 minutes.
- If one run exceeds 10 minutes, kill it and mark it as `FAILED`.
- Trivial failures like typos, imports, or syntax mistakes can be fixed once and re-run.
- Fundamentally bad ideas should be abandoned quickly.
- Once the loop starts, do not pause for approval.

## If There Are No Ideas

Use this fallback order:

1. Read papers, libraries, or references mentioned in `WRITABLE`.
2. Re-read nearby code with a different hypothesis.
3. Combine previous near-miss ideas.
4. Try a more aggressive but still single-scope architectural change.

## Handoff Back To GSD

When the loop stops in a GSD-managed repo, return a concise research handoff:

- best metric versus baseline
- commits kept
- failed directions worth avoiding
- remaining uncertainty
- recommended next GSD step

Use these handoff defaults:

- Stable improvement ready for user-facing validation -> `$gsd-verify-work`
- Improvement found but plan needs to change -> `$gsd-plan-phase`
- Narrow follow-up task without milestone changes -> `$gsd-quick --full`

## Throughput Estimate

Rough guide:

- about 5 minutes per experiment
- about 12 experiments per hour
- about 100 experiments over an 8-hour overnight run
