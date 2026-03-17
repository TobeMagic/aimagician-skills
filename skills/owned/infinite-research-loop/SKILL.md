---
name: infinite-research-loop
description: |
  启动一个自主循环实验流程，让 AI 在无人监管的情况下反复尝试、评估、保留或回退实验。
  适用于任何可以迭代 + 量化反馈的任务，例如训练调参、算法优化、功能迭代等。
  当用户说“让 AI 帮我整夜跑实验”“自动调参”“循环测试”“无人守候”时触发。
  使用前必须先和用户 discuss 确认各项参数，再写入 `program.md`。
compatibility:
  tools: [bash, git, python]
  requires: 项目仓库已初始化 git，存在可运行的评估脚本
---

# Infinite Research Loop Skill

Reference: https://github.com/karpathy/autoresearch/tree/master

The core idea comes from Karpathy's autoresearch:
write a `program.md` as the agent's operating specification, then let the agent
iterate autonomously without asking the user whether to continue.

## Before You Start: discuss with the user

Do NOT skip this step and jump straight into the loop.

Before writing `program.md`, confirm the following:

1. Objective metric: what exactly are we optimizing, and where do we read it?
2. Writable scope: which single file may the agent modify, and what is strictly read-only?
3. Time budget: max duration per experiment, and total session length.
4. Eval method: exact eval command to run, exact field to read from output.
5. Exploration focus: what to prioritize this session, and what to explicitly skip.

Once confirmed, write the agreed parameters into `program.md` in the format below.

## `program.md` Format

This file lives in the project root and is the agent's single source of truth.
Humans edit it. The agent executes it strictly.

```md
# program.md — [PROJECT_NAME]

## Objective

METRIC:    [metric_name]
DIRECTION: [lower|higher] is better
SUCCESS_THRESHOLD: [delta vs current best, e.g. improvement > 0.002]

## File Permissions

WRITABLE:  [filename]           # agent may only modify this file
READONLY:  [file1, file2, ...]  # never touch

## Experiment Rules

TIME_LIMIT:    [N] min
EVAL_COMMAND:  [shell command]
RESULT_PATH:   [path/to/file]
RESULT_FIELD:  [json_key]
COMMIT_FORMAT: "exp: {description} | {metric}: {value}"

## Exploration Focus (this session)

- [dimension_1]
- [dimension_2]
- [dimension_3]

## Excluded Directions

- [what NOT to try, to save search space]

## Fallback (when out of ideas)

1. Read referenced papers/libs inside WRITABLE file
2. Re-read project files from a fresh angle
3. Combine near-miss ideas from past experiment history
4. Try more aggressive architectural changes

## Termination

- User interrupts (Ctrl+C)
- Optional: stop after [N] experiments
- Optional: stop when metric reaches [threshold]
```

## Agent Execution Loop

Once `program.md` is written, run the following loop without stopping:

```text
loop:

1. propose one new idea -> modify WRITABLE file only
2. run EVAL_COMMAND with timeout TIME_LIMIT
3. read metric from RESULT_PATH[RESULT_FIELD]
4. decide:
   - error (trivial: typo, syntax) -> fix and re-run
   - error (fundamental)           -> skip, log FAILED, git reset
   - timeout / crash               -> skip, log FAILED, git reset
   - metric improved               -> git commit with COMMIT_FORMAT
   - metric degraded               -> git reset --hard HEAD
5. if out of ideas -> run Fallback sequence from program.md
6. NEVER ask the user whether to continue
```

## Research Loop Model

```text
propose idea, modify main code
    ->
run pre-written experiment or test script
    ->
save output result to file
    ->
evaluate outcome
   /            \\
error           normal
  ->              ->
try fix       result improved? -> git commit ->
  ->              ->
repeat fail    result worse?   -> git reset
  ->              ->
skip          continue loop
```

## Hard Constraints

- Modify ONLY the file listed under `WRITABLE`. One character outside that scope means stop and report.
- `git reset` is a last resort. Use it only when the metric clearly degrades or the idea is fundamentally broken.
- Never pause, prompt, or wait for user input once the loop has started.
- Respect user interrupt immediately.

## Failure Handling Rules

- Timeout rule:
  - expected runtime per experiment is about 5 minutes
  - if one run exceeds 10 minutes, kill it and mark it as FAILED
- Crash rule:
  - trivial mistakes like typos or syntax errors should be fixed and retried
  - fundamentally bad ideas should be skipped quickly
- Autonomy rule:
  - once the loop starts, do not ask the user whether to continue
- Reset rule:
  - be conservative; avoid rollback unless the result clearly got worse

## If There Are No Ideas

Use this fallback sequence:

1. Read papers, libraries, or references mentioned in the writable file.
2. Re-read project code from a fresh angle.
3. Combine previous near-miss ideas.
4. Try more aggressive architectural changes.

## Throughput Estimate

As a rough guide:

- about 5 minutes per experiment
- about 12 experiments per hour
- about 100 experiments over an 8-hour overnight run
