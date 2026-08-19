---
name: review-before-edit
description: Show a reviewable plan before mutating the repo
alwaysApply: true
---

# Review Before Edit

For bugfix, behavior change, or refactor, stop before Write, StrReplace, Delete, commit, or opening a merge request.

Show in one pass:

1. files to change (full paths)
2. before/after or equivalent diff for each file
3. blast radius: callers, runtime behavior, what to test

Wait for an explicit go-ahead such as 改吧, 执行, or 按这个改. Until then: discuss only; do not implement, commit, or push.

Questions like 如何修复 / 怎么改 / 应该怎么修 get a reviewable plan only.

Direct-work exceptions: read-only investigation, logs, existing tests, or the user already said 直接改 / 改吧 in this turn with the same scope.
