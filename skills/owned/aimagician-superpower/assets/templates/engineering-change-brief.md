# Engineering Change Brief: {{OBJECTIVE}}

**Task type:** feature | bug | refactor | performance | architecture | prototype
**Risk:** low | medium | high
**Requirements:** TBD
**Delivery class:** Deployable | Non-deployable

## Target And Guardrails

- Observable outcome: TBD
- Invariants to preserve: TBD
- Allowed files or owners: TBD
- Forbidden files or owners: TBD
- Compatibility and rollback: TBD

## Vertical Slices

### Slice 1: Tracer

- Behavior proved: TBD
- Entry to result path: TBD
- Failing check or baseline: TBD
- Minimal implementation: TBD
- Expected evidence: TBD
- Checkpoint and rollback: TBD

### Slice 2: Boundaries And Failure

- Behavior proved: TBD
- Cases: TBD
- Expected evidence: TBD

### Slice 3: Migration And Cleanup

- Consumers migrated: TBD
- Compatibility removal condition: TBD
- Expected evidence: TBD

## Integration Points

| Boundary | Change | Owner | Verification |
|---|---|---|---|
| TBD | TBD | TBD | TBD |

## Delivery Ladder

| Stage | Required | Checks | Evidence target | Failure response |
|---|---|---|---|---|
| LOCAL | YES | TBD | TBD | Fix locally before remote execution |
| CI / PREMERGE | TBD | TBD | Frozen revision and required CI | Keep merge blocked |
| PREVIEW | TBD | TBD | Preview revision, URL, logs, or probes | Fix or use documented recovery |
| POSTMERGE | TBD | TBD | Merge SHA, artifact provenance, online checks | Reopen checklist and recover |

## Online-Only Exceptions

| Check | Why local is insufficient | Target | Expected evidence | Failure response | Owner |
|---|---|---|---|---|---|
| None | N/A | N/A | N/A | N/A | N/A |

## Artifact Provenance

- Implementation revision: TBD
- Build or release identity: TBD
- Provenance verification method: TBD
- Closure-only planning update expected: YES | NO

## Review And Completion

- Specification reviewer: TBD
- Quality reviewer: TBD
- Broad checks: TBD
- Frozen premerge review point: TBD
- Required postmerge checks: TBD
- Residual risk: TBD
