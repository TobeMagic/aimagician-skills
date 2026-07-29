# Phase 37: Secure Acquisition and Catalog - Discussion Log

**Updated:** 2026-07-29

## Decisions

| Topic | Options | Decision | Reason |
|---|---|---|---|
| Command surface | Extend generation CLI; separate manager | Separate manager | Isolate acquisition/security from rendering |
| Default mutation | Apply; dry-run | Dry-run | Avoid accidental download or state mutation |
| Credential transport | argv/env/file | ignored file only | Avoid process-list and log leakage |
| Redirects | automatic; manual | manual one-hop policy | Strip authorization cross-host |
| Archive handling | extract; passive inspect | passive inspect | Never execute active content |
| Catalog storage | SQLite; JSON v3 | deterministic JSON v3 | Portable and sufficient for tracer |
| Legacy migration | rewrite; adapter | adapter | Preserve consumers and quarantine |
| Auth blocker | stop; continue offline | continue offline | Core contracts need no cookie |

## Assumptions

| Assumption | Status | Action |
|---|---|---|
| Fresh credential arrives only through `.private/` | Pending | Keep live sync `NEEDS_AUTH` |
| Rights metadata can precede legal-use decision | Accepted | Use explicit unknown/restricted/allowed |
| JSON suffices until scale is measured | Accepted | Preserve storage adapter seam |

## Rejected Options

- Extending the large generation CLI with acquisition flags.
- Passing a raw credential by argv or environment variable.
- Automatic redirect following with authorization retained.
- Extracting untrusted packages before inspection.
- Rewriting existing registries or auto-certifying legacy items.
- Blocking all offline engineering on commercial authentication.

## Deferred Work

- Site-specific authenticated adapter and full commercial inventory.
- Real-package geometry/pHash enrichment at library scale.
- TemplatePack v2 and ArtDirectionProfile, owned by Phase 38.

## Review Checkpoint

- DeepSeek plan review was rate-limited and the failed process was stopped
  after it ceased producing review activity.
- Agnes fallback session `ses_051e9410cffeyPY2lbey0hhc3T` found no Blocker
  and one Important: schemas lacked field-level contracts. The Spec and plan
  now define fields, enums, conditions, pHash state, stable IDs, dedupe, and
  certification thresholds.
- The reported naming Nitpick referenced text that is not present in the plan
  and is rejected after controller inspection.
- Fresh Agnes re-review session `ses_051e2df22ffeEp5xAgbtqzOYhR` returned
  PASS with Blocker 0, Important 0, and Nitpick 0 after checking both
  requirements, the four field-level contracts, stable IDs, dedupe, pHash
  state, certification thresholds, security policy, and test mapping.
- The re-review worker exceeded its strict-read-only scope by appending a
  conclusion to this log. The controller removed that unauthorized edit and
  recorded the verified result here through the repository editing workflow.
