# Reviewer-Bot Gate

Load this reference only when the repository actually configures a reviewer bot or branch protection requires one. Reviewer-bot output is otherwise advisory, not a universal completion gate.

## What To Check

- PR reviews with bot authors.
- PR issue comments that mention review findings.
- Review threads or unresolved conversations.
- CI/check run annotations if the bot reports through checks.

## Passing State

Treat reviewer-bot as passing only when:

- the latest relevant bot review/comment is positive or non-blocking;
- no newer commit invalidates that review;
- no unresolved bot-authored blocking thread remains;
- required human reviews are also satisfied.

## Blocking State

Treat as blocking when:

- the bot reports critical, important, failing, or requested changes;
- the bot output is missing but required by project convention;
- a bot thread is unresolved;
- CI/checks tied to the bot are failed, pending, or cancelled.

Record the result in a wiki only when the project or user asks for that audit trail.
