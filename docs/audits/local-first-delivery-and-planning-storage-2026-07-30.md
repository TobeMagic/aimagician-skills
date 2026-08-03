# Local-First Delivery And Planning Storage Audit

**Date:** 2026-07-30  
**Request:** `USR-20260730-002`

## Objective

Reduce remote CI and deployment rework without weakening online acceptance. Engineering work must collect the complete applicable chain locally, prove locally observable behavior before remote execution, and keep deployable work open until the merged artifact passes online verification.

## Implemented Capability

| Requirement | Implementation | Evidence |
|---|---|---|
| Full-chain context before implementation | `engineering-context-map.md` covers entry, orchestration, domain, state, external boundaries, delivery, observability, and user result | Runtime/template tests and Skill content checks |
| Local-first verification ladder | `local-first-delivery.md` defines LOCAL, CI/PREMERGE, risk-based PREVIEW, and POSTMERGE | `workflow.mjs` premerge/postmerge gates |
| Online-only exception discipline | Change and validation templates require reason, target, evidence, failure response, and owner | Delivery contract validation |
| Postmerge completion | Deployable records require merge SHA, artifact match, online PASS, recovery status, and `ONLINE_CONFIRMED` | Runtime deployable task fixture |
| Failure recovery | Failed online checks keep the checklist open and route to repository-specific rollback or roll-forward | Capability module and postmerge finding codes |
| Tracked and local-private planning | `workflow.mjs planning` initializes, attaches, reports, locks, and advances revisions | Multi-worktree runtime test |
| Shared planning across worktrees | Local-private `.planning` points to Git common dir; parallel bootstrap automatically attaches new worktrees | Parallel bootstrap integration test |
| Frozen independent review | OpenCode runner requires `--review-ref` or `--review-worktree` for review/audit and verifies fingerprints | Frozen review runner test |
| Install drift detection | Manifest v4 records source path/digest; doctor compares source and installed content | Bootstrap and CLI doctor drift tests |
| PR validation | Pull requests run typecheck, tests, build, and pack smoke | `.github/workflows/ci.yml` |

## Storage Decision

Tracked planning remains the portable default when history should be reviewed and cloned. Local-private planning is an explicit alternative:

- one store under the repository Git common directory;
- one `.planning` attachment in every worktree;
- `/.planning` in the common local exclude file;
- short writer lease plus expected revision;
- no automatic backup.

Deleting the clone or Git common directory deletes local-private planning. The runtime does not silently migrate between modes.

## Delivery Decision

`Deployable` and `Non-deployable` are explicit classes. For deployable work:

1. all practical local checks run first;
2. CI and a frozen premerge audit establish `MERGE_READY`;
3. preview is required by risk or repository policy;
4. the implementation merge SHA and deployed artifact identity are recorded;
5. online checks and a fresh completion audit establish `ONLINE_CONFIRMED`;
6. a later planning-only closure commit is identified as metadata, not the deployed implementation.

## Compatibility

Existing task and phase records without a `Delivery contract` retain their historical completion behavior. New templates use contract `v1`. Manifest v3 loads as v4-compatible data; old installs remain presence-checked until the next managed sync records source digests.

## Residual Risks

- Local-private planning has no built-in backup by design.
- Source digesting adds bootstrap work; digests are computed once per unique source and cached within the sync.
- Postmerge evidence quality still depends on repository-specific probes and artifact provenance being available.
- A worktree review detects mutation but does not undo it; exact commit review uses a disposable detached worktree and is preferred for closure.
