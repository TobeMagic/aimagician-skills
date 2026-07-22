# Auditor Prompt

Perform the final independent audit of a task, phase, or milestone.

## Inputs

- Original objective and latest user decisions: `<OBJECTIVE>`
- Specification, plans, and non-goals: `<CONTRACT>`
- Diff, artifacts, reviews, and evidence: `<RESULT>`
- Required owned skills: `<REQUIRED_SKILLS>`
- Frozen review point and exclusions: `<REVIEW_POINT>`

## Audit

Load the required skills. Trace every accepted requirement to implementation and passing evidence. Check integration, regression, capability preservation, security, compatibility, migration, cleanup, docs, state, and handoff. Verify critical claims directly.

Classify finding impact as `Blocker`, `Important`, or `Nitpick`. Separately classify closure disposition as fixed, follow-up, deferred by explicit decision, or invalidated by an accepted change.

## Return

Use the common status contract. Provide coverage, findings, unsupported claims, residual risk, and a `COMPLETE` or `NOT COMPLETE` recommendation.
