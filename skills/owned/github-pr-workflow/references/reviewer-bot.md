# Reviewer-Bot Gate

Reviewer-bot output is a completion gate for PR work.

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

Record the result in `LLM-know-how-wiki` as `GITHUB_PR_WORKFLOW`.

