# Phase 11: Previewed Managed Sync Engine - Research

**Researched:** 2026-06-04
**Domain:** TypeScript/Node.js filesystem sync engine, manifest-scoped managed installs, bootstrap preview/apply workflow
**Confidence:** HIGH for repository-local architecture and test strategy; MEDIUM for missing Phase 11 context details because `11-CONTEXT.md` was absent in the isolated research worktree

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Phase goal: Convert resolved desired state into preview-confirmed filesystem sync that only affects selected CLI targets and Skillbee-managed items.
- Phase requirement IDs: SYNC-01, SYNC-02, SYNC-03, SYNC-04, SYNC-05, SYNC-06, SYNC-07.
- User already asked to start from the failing `planManagedInstallSync` test and an initial `planManagedInstallSync` pure function has been implemented in `src/bootstrap/direct-target-sync.ts`.
- Research must account for current state and identify what remains for a robust phase plan, including `runBootstrap` integration and verification needs.

### Claude's Discretion
- Research repository-local implementation options and recommend a prescriptive plan for separating preview planning from filesystem application.
- Identify robust verification coverage for target scoping, managed-only deletion, manifest preservation, dry-run behavior, and report integration.

### Deferred Ideas (OUT OF SCOPE)
- Do not broaden this phase into a marketplace, hosted sync service, multi-user policy system, or full external package manager.
- Do not hand-roll support for target capabilities that the project already treats as unsupported/skipped.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SYNC-01 | Produce a deterministic preview/plan of managed install filesystem changes before applying them. | Use a pure `planManagedInstallSync` function returning ordered create/overwrite/remove/skip operations from desired installs + previous manifest. |
| SYNC-02 | Apply sync only after preview/confirmation semantics are satisfied. | Integrate plan generation into `runBootstrap`; preview returns planned operations without writes, apply executes the exact plan. |
| SYNC-03 | Limit writes/removals to selected targets only. | Preserve current retained unselected manifest behavior and have planner filter desired/previous installs by `selectedTargets`. |
| SYNC-04 | Remove only Skillbee-managed stale installs. | Base removals exclusively on previous manifest records and allowed target roots; never scan-delete unmanaged directories. |
| SYNC-05 | Enforce allowed-root safety before destructive operations. | Centralize path containment checks and report stale managed entries outside target homes as skip operations. |
| SYNC-06 | Update manifest/report output from applied sync results. | Convert applied write operations into `BootstrapManifestManagedInstall[]`; expose preview/apply operations to callers for reporting. |
| SYNC-07 | Verify idempotency and partial target behavior. | Add unit/integration tests around reruns, unselected target preservation, no-write preview, and manifest equality. |
</phase_requirements>

## Summary

Phase 11 should not introduce a new external stack. The existing implementation already has the right raw ingredients: `resolveManagedSkillInstalls` builds desired target-specific install records, `manifest.ts` stores previous managed installs, `runBootstrap` preserves unselected target manifest records, and `syncManagedInstalls` now exposes an initial pure `planManagedInstallSync` function. The phase should finish turning this into a first-class managed sync engine: deterministic pure planning first, then a small effectful executor that applies the accepted plan.

The key architectural gap is run-level preview/report integration. `direct-target-sync.ts` can now preview create/overwrite/remove/skip operations and existing `syncManagedInstalls` reuses that plan, but callers still need a stable way to surface those operations for pre-write confirmation and final reporting. A robust plan should preserve current bootstrap compatibility while exposing sync operations where Phase 12 can render them.

**Primary recommendation:** Use `resolve desired state -> pure deterministic plan -> preview/report -> apply exact plan -> manifest from applied records`, with all removals gated by both previous manifest ownership and allowed-root containment.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Node.js `fs/promises` | Current stable API | Filesystem mkdir/rm/cp/write operations | Already used in `direct-target-sync.ts`; no new dependency needed. |
| TypeScript | 5.9.2 | Strongly typed sync plans, manifest records, target discriminants | Existing repo standard; catches operation shape drift. |
| Vitest | 4.1.0 | Unit and integration verification | Existing repo standard via `npm test`. |

### Supporting
| Library | Purpose | When to Use |
|---------|---------|-------------|
| Node.js `path` | `normalize`, `dirname`, separator-aware containment | All destination/root comparisons and operation paths. |
| Existing `manifest.ts` | Managed ownership source of truth | Previous manifest records decide stale managed removals. |
| Existing `source-resolution.ts` | Desired install state | Keep desired state generation separate from sync planning. |
| Existing `run-bootstrap.ts` | Orchestration, reporting, manifest write | Integrate preview/apply plan without bypassing bootstrap reports. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Node `fs/promises.cp/rm` | `fs-extra` | Not needed; Node APIs are stable and repo has no `fs-extra` dependency. |
| Pure planner + executor | Keep only monolithic `syncManagedInstalls` | Faster short-term, but preview-confirmed behavior is harder to prove. |
| Manifest-only ownership | Scan target directories for marker files | Scanning risks touching unmanaged user content. |
| Sequential executor | Parallel filesystem operations | Sequential execution is safer and deterministic for overlapping target homes. |

## Architecture Patterns

### Recommended Project Structure

```text
src/bootstrap/
├── direct-target-sync.ts      # pure managed sync planning + effectful execution
├── run-bootstrap.ts           # orchestrates desired state, preview/apply, report, manifest
├── manifest.ts                # previous/applied managed ownership model
├── source-resolution.ts       # desired skill installs by target
└── target-homes.ts            # target allowed roots and destination directories

tests/bootstrap/
└── direct-target-sync.test.ts # current integration and planner coverage
```

### Pattern 1: Pure Plan, Effectful Apply
Compute all filesystem operations from inputs without touching disk; execute only the returned operations in a separate path. The current `planManagedInstallSync` function should remain pure and deterministic.

### Pattern 2: Manifest-Scoped Removal
A removal is eligible only when it comes from `previousManifest.managedInstalls`, belongs to a selected target, is no longer desired, and is contained under that target’s allowed roots.

### Pattern 3: Selected Target Isolation
Planning iterates only `selectedTargets`; unselected manifest records are retained by `runBootstrap` and never become remove operations.

### Pattern 4: Deterministic Sort Order
Sort target plans, desired installs, previous installs, and operations using stable comparators so previews, tests, and reports are repeatable.

### Anti-Patterns to Avoid
- Deleting by scanning target home.
- Path string prefix without normalization/root boundary.
- Applying during preview/dry-run.
- Parallel remove/copy under the same root.
- Manifest from desired state instead of applied write operations.

## Common Pitfalls

### Pitfall 1: Preview Diverges from Apply
Avoid duplicate diff logic. Generate the same operation plan in preview and apply paths.

### Pitfall 2: Removing Unmanaged User Content
Remove only previous manifest records that are stale and inside allowed roots.

### Pitfall 3: Cross-Target Overreach
Running only `claude` must not prune or overwrite Codex, OpenCode, Gemini, etc.

### Pitfall 4: Unsafe Path Containment
Normalize root and destination, reject destination equal to root, and require `destination.startsWith(root + sep)`.

### Pitfall 5: Partial Copy Leaves Corrupt Destination
At minimum, failed apply must not claim manifest success for failed copies. Stronger transactional replacement can be future hardening if scope allows.

### Pitfall 6: Plugin/Extension Areas Treated Like Skill Directories
Keep `installType` and `installArea` in every operation and manifest record.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 |
| Config file | `vitest.config.ts` |
| Quick run command | `npx vitest run tests/bootstrap/direct-target-sync.test.ts` |
| Full suite command | `npm test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| SYNC-01 | Deterministic preview contains create/overwrite/remove/skip operations without touching disk | unit/integration | `npm test -- tests/bootstrap/direct-target-sync.test.ts -t "previews create overwrite remove"` | ✅ |
| SYNC-02 | Preview does not mutate target homes; apply executes accepted plan | integration | `npm test -- tests/bootstrap/direct-target-sync.test.ts` | ✅ partial; needs run-level preview/report surface |
| SYNC-03 | Selected target run does not remove or update unselected targets | integration | `npm test -- tests/bootstrap/direct-target-sync.test.ts -t "updates only the selected direct targets"` | ✅ |
| SYNC-04 | Stale removal only uses previous managed manifest records, preserving manual dirs | integration | `npm test -- tests/bootstrap/direct-target-sync.test.ts -t "prunes stale managed installs"` | ✅ |
| SYNC-05 | Unsafe previous manifest destinations outside allowed roots are skipped/reported | unit/integration | `npm test -- tests/bootstrap/direct-target-sync.test.ts -t "previews create overwrite remove"` | ✅ |
| SYNC-06 | Applied sync result updates manifest and operation reports consistently | integration | `npm test -- tests/bootstrap/direct-target-sync.test.ts` | ✅ partial; report exposure may need extension |
| SYNC-07 | Re-run idempotency and partial-target manifest retention remain stable | integration | `npm test -- tests/bootstrap/direct-target-sync.test.ts` | ✅ partial |

### Sampling Rate
- Per task: `npm test -- tests/bootstrap/direct-target-sync.test.ts`
- Phase gate: `npm run typecheck && npm test`

### Wave 0 Gaps
- [ ] Confirm run-level preview/report data is exposed for Phase 12 consumption.
- [ ] Confirm manifest writes remain based on applied operations, not skipped removes or desired-only state.
- [ ] Confirm full project tests after integrating operation exposure.

## Sources

### Primary (HIGH confidence)
- Repository source: `src/bootstrap/direct-target-sync.ts` — current pure planner and sync execution implementation.
- Repository source: `src/bootstrap/run-bootstrap.ts` — dry-run/apply orchestration, manifest retention, report writing.
- Repository source: `src/bootstrap/manifest.ts` — manifest v3 managed install model and backward compatibility.
- Repository source: `src/bootstrap/source-resolution.ts` — desired managed skill install generation.
- Repository tests: `tests/bootstrap/direct-target-sync.test.ts` — existing managed sync integration coverage.

### Secondary (MEDIUM confidence)
- Node.js official docs: `https://nodejs.org/api/fs.html` — `fs.promises.cp`, `rm`, `mkdir` behavior.
- Vitest official docs: `https://vitest.dev/guide/` — test conventions and `vitest run`.

## Metadata

**Research date:** 2026-06-04
**Valid until:** 2026-07-04 for repository-local architecture; re-check immediately if newer sync code lands.
