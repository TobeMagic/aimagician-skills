---
name: git-safety
description: Safe git and commit defaults across coding CLIs
alwaysApply: true
---

# Git Safety

Commit only when the user asks. Do not update git config. Do not skip hooks. Do not force-push main or master. Do not amend a commit you did not create, or one already pushed, unless the user asks.

Never commit secrets (.env, credentials, keys). Warn if asked to.

If the user asks for a commit: inspect status, diff, and recent log; stage only the agreed files; write a short why-focused message.

PR/MR details stay in github-pr-workflow when GitHub is actually in use.
