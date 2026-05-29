# Sub-Issue Planning

Use this reference when a Linear issue has child issues, needs to be split, or is being considered for final closure.

## Current Linear User

Resolve the current Linear user through the MCP connector when possible. Use that user as "me".

If the connector cannot identify the current user and assignee matters, ask for the intended assignee before creating or assigning child issues.

## Read Requirements

Before planning or closing an issue, fetch:

- parent issue, if any;
- child/sub-issues;
- current assignee for each child;
- state for each child;
- linked PRs and branch metadata;
- latest comments and blockers;
- acceptance criteria in parent and children.

## Completion Gate

Do not close a parent issue until:

- all required child issues are in terminal states;
- child issues assigned to the current Linear user are complete or explicitly marked not required;
- non-Done terminal states such as canceled, duplicate, or won't-do have an explicit rationale;
- parent acceptance criteria and recent comments have been rechecked for remaining requirements;
- PR, review, deployment, and wiki-record gates are satisfied when applicable.

If any required child issue remains open, add a parent comment listing:

- child issue ID and title;
- assignee;
- current state;
- blocker or next action.

## Splitting Large Issues

Split or propose splitting when an issue is:

- too large for one focused PR;
- multi-service or multi-repo;
- owned by multiple people;
- naturally sequential;
- unclear enough that acceptance criteria need separate tracks;
- likely to remain open across multiple development sessions.

Do not split small, single-scope issues just to create process overhead.

## Child Issue Plan

Before creating child issues, present a compact plan:

```text
Sub-issue plan:
- Parent: LUC-123 <title>
- Child 1: <title>
  - owner: <current Linear user by default>
  - scope:
  - acceptance:
  - dependency:
- Child 2: ...
```

Default assignee for new child issues is the current Linear user unless the human specifies another owner or the split is explicitly collaborative.

Each child issue should include:

- parent link;
- clear scope;
- acceptance criteria;
- owner;
- dependency order if relevant;
- implementation notes or related service/repo;
- expected verification.

## Execution Order

When child issues assigned to the current Linear user exist:

1. Work the highest-priority unblocked child issue.
2. Update Linear with branch, commit, PR, tests, and blockers.
3. Move the child issue through the normal workflow.
4. After each child reaches a terminal state, update the parent comment.
5. Re-check the parent for remaining requirements before closure.
