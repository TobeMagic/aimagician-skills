# Phase 37: Secure Acquisition and Catalog - Specification

**Created:** 2026-07-29
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Depends on:** Phase 36
**Requirements:** 2

## Goal

Build a resumable, entitlement-aware private template acquisition and catalog
pipeline without exposing credentials, executing active content, or committing
original assets.

## Background

Phase 36 established a locked realistic brief boundary and a git-index private
asset guard. The existing Skill still has no runtime acquisition policy,
passive quarantine layer, resumable source inventory, content-addressed
catalog, dependency closure, or certified retrieval surface. The only legacy
template registry is explicitly unverified, while TemplatePack v1 is loaded
through a filesystem scan.

## Requirements

### V6-ASSET-01: Entitlement-Aware Private Acquisition

- **Source requests:** USR-V6-05, USR-V6-08, USR-V6-10
- **Current:** The ignored `.private/` boundary and staged-index guard exist,
  but there is no host-scoped acquisition policy, quarantine classifier,
  rights record, or resumable state machine.
- **Target:** A separate library-management boundary provides
  `discover|sync|ingest|certify|query`, defaults to dry-run, reads credentials
  only from an ignored file, strips authorization on cross-host redirects,
  quarantines unsafe packages without extraction, and persists resumable
  state only under `.private/` when explicitly applied.
- **Acceptance:** Auth, redirect, traversal, macro/OLE/ActiveX, external
  relationship, rights, dry-run, resume, and no-secret-output tests pass; no
  credential or private byte enters git, argv, stdout, stderr, or tracked
  evidence.

### V6-LIB-01: Queryable Compatibility-Safe Catalog

- **Source requests:** USR-V6-01, USR-V6-05, USR-V6-06, USR-V6-10
- **Current:** Four legacy entries remain deliberately unverified and one
  TemplatePack v1 is loaded by filesystem scan. There is no content-addressed
  catalog, dependency closure, certification state, or safe retrieval API.
- **Target:** Catalog v3 stores stable source/item/version/hash IDs, geometry,
  perceptual hashes, capacity, style, rights, dependency, editability, and
  certification metadata. Queries are deterministic and certified-only by
  default; old registries remain compatible and uncertified legacy entries
  never enter automatic selection.
- **Acceptance:** Schema, stable-ID, dedupe, dependency-closure, rights,
  certification, compatibility, and deterministic-query tests pass. A public
  metadata-only seed proves the complete discover-to-query tracer without
  private bytes or authentication.

## Behavior Contract

- `discover|sync|ingest|certify|query` are read-only by default and emit
  machine-readable manifests.
- Authentication is host-allowlisted, stripped on cross-host redirects, and
  becomes `NEEDS_AUTH` without automatic credential retry.
- Archives, macros, OLE, ActiveX, external relationships, and traversal paths
  are quarantined.
- Stable source, slide, version, hash, geometry, pHash, capacity, style,
  rights, dependency, and editability metadata are queryable.
- Full entitled inventory is resumable; unauthorized/unavailable entries are
  explicit and never imputed.
- Formal generation still requires a locked ProjectBriefPack. Private bytes
  and credentials remain below ignored `.private/` and never enter argv.
- Complete works are visual spines. Supplemental templates later require
  family/style and dependency-closure certification.
- COM remains optional diagnostics. Portable native-editable PPTX owns v6.

## Engineering Contract

- **Owners:** `acquisition.py` owns remote policy and resumable intents;
  `quarantine.py` owns passive package inspection; `catalog.py` owns IDs,
  compatibility, dependency closure, certification, and retrieval; the
  dedicated library CLI owns command dispatch and JSON serialization.
- **Invariants:** no extraction or active-content execution; credential paths
  resolve under `.private/`; authorization is host-bound; redirects are
  evaluated one hop at a time; writes require `--apply` and stay in
  `.private/`; automatic query returns certified items only.
- **Interfaces:** all new schemas and modules are additive. Existing
  `registry.py`, legacy JSON registries, TemplatePack v1, generation CLI, and
  render paths remain available and unchanged.
- **Failure semantics:** missing credentials return `NEEDS_AUTH`; missing
  rights return `NEEDS_RIGHTS`; unsafe packages return `QUARANTINED`; unknown
  or broken dependencies fail closed; partial inventory is explicit.
- **Rollback:** remove the additive Phase 37 files. Existing registries need
  no migration.

## Versioned Contract Shapes

All four contracts use JSON Schema Draft 2020-12, reject unknown fields, and
carry `schema_version`, `status`, and deterministic identifiers. No contract
permits a credential value, authorization header, cookie, or private byte.

| Contract | Required fields | Required enums and conditional rules |
|---|---|---|
| AcquisitionManifest v1 | command, mode, source ID, origin, allowlisted hosts, requested/completed/unavailable item IDs, resume cursor, state digest, findings | command = discover/sync/ingest/certify/query; mode = dry_run/apply; status = PASS/NEEDS_AUTH/NEEDS_RIGHTS/QUARANTINED/PARTIAL/FAIL; apply requires a private state path but never a credential path/value in output |
| QuarantineReport v1 | package hash/size, entry counts, compressed/uncompressed totals, findings, disposition | disposition = ACCEPT/QUARANTINED/REJECTED; any traversal, encrypted entry, macro, OLE, ActiveX, external relationship, malformed ZIP, entry-count, size, or compression-ratio limit makes ACCEPT invalid |
| RightsRecord v1 | source ID, item ID, access basis, use scope, redistribution state, evidence references, reviewed time, decision | decision = allowed/restricted/unknown; only allowed can certify; unknown or missing evidence produces NEEDS_RIGHTS |
| Catalog v3 | catalog/source/item/version/hash IDs, media type, geometry, pHash state/value, capacity, scenarios, style tags, rights decision, dependency IDs, editability, certification, provenance | certification = certified/quarantined/unverified/revoked; certified requires ACCEPT quarantine, allowed rights, complete dependency closure, nonempty geometry/capacity/style/editability/provenance; pHash state = present/not_applicable/pending, where pending cannot be used for visual-similarity ranking |

Stable IDs are derived from normalized public source identity plus content
SHA-256, never from a local/private path. Hash duplicates have one canonical
catalog item plus explicit source/version aliases. Dependency closure rejects
missing nodes, cycles, quarantined/revoked nodes, and uncertified nodes for
automatic selection.

## Certification Threshold

`certified` is permitted only when the package quarantine disposition is
`ACCEPT`, rights decision is `allowed`, the source and content hashes are
present, dependencies close, geometry/capacity/style metadata is complete, and
editability is not `unknown`. Supplemental items additionally record a future
TemplatePack v2 dependency without claiming that Phase 38 certification has
already occurred.

## Boundaries

### In Scope

- versioned acquisition, quarantine, rights, and Catalog v3 contracts;
- host/redirect policy and redacted private credential-file loading;
- passive OOXML/ZIP inspection without extraction;
- dry-run intents and explicit private-root resumable state;
- content-addressed IDs, dedupe, dependency closure, compatibility, and query;
- a public metadata seed and dedicated machine-readable manager CLI.

### Out Of Scope

- authenticated commercial sync before a rotated short-lived credential;
- committing or redistributing commercial/private bytes;
- site-specific browser automation, bypasses, or undocumented scraping;
- TemplatePack v2, art-direction certification, generation, and flagships;
- COM- or HTML-based acquisition and weak-model distillation.

## Constraints

- Credentials and private bytes never enter argv, logs, exceptions, tracked
  manifests, tests, commits, or session exports.
- Authentication proves access, not redistribution rights; unknown rights
  fail closed.
- Default execution is read-only; explicit writes are atomic and private-root
  confined.
- Existing registries, TemplatePack v1, generation CLI, and render behavior
  remain compatible.
- Synthetic fixtures must not contain production credentials or commercial
  template content.

## Test Seams And Critical Cases

| Behavior | Observable seam | Failing case | Evidence |
|---|---|---|---|
| Dry-run acquisition | library CLI JSON | default command writes state or bytes | CLI/unit tests |
| Host-bound auth | redirect policy | authorization survives a cross-host hop | policy tests |
| Passive quarantine | package classifier | traversal, macro, OLE, ActiveX, or external target is accepted | synthetic ZIP fixtures |
| Resumability | acquisition state reducer | completed items repeat or unavailable items are imputed | state tests |
| Stable catalog | Catalog v3 loader | IDs change with path/order or duplicate hashes create two canonical items | catalog tests |
| Safe retrieval | certified-only query | unverified legacy entry is automatically selected | compatibility/query tests |
| Dependency closure | catalog resolver | missing, cyclic, or uncertified dependency is accepted | closure tests |

## Acceptance Criteria

- [ ] V6-ASSET-01 has concrete passing evidence.
- [ ] V6-LIB-01 has concrete passing evidence.
- [ ] The public metadata-only tracer covers all five commands without auth.
- [ ] Explicit apply writes only below the ignored `.private/` root.
- [ ] Focused tests, affected Window-PPTX tests, formatter, workflow gates,
      private staged guard, and diff checks pass.
- [ ] Fresh independent specification, quality, verification, and Agnes phase
      audits have no unresolved Blocker or Important finding.

## Blocking Questions

- None.

Live commercial sync is a declared external precondition and remains
`NEEDS_AUTH`; it does not block the offline tracer.

## Ambiguity Report

- **Goal clarity:** 0.97
- **Boundary clarity:** 0.98
- **Constraint clarity:** 0.98
- **Acceptance clarity:** 0.96
- **Ambiguity:** 0.028

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | Architecture | Extend the generation CLI or isolate library management? | Use a dedicated manager and additive modules |
| 2 | Safety | May acquisition mutate by default? | No; every command is dry-run unless explicitly applied |
| 3 | Secrets | How is authorization supplied? | A path below ignored `.private/`; never a raw value |
| 4 | Packages | Extract first or inspect passively? | Inspect the ZIP package without extraction or execution |
| 5 | Storage | Database or JSON for the first tracer? | Deterministic JSON v3 behind a stable module interface |
| 6 | Compatibility | Rewrite existing registries? | No; adapt them and preserve their quarantine flags |
