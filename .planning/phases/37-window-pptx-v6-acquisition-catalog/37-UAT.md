# Phase 37: Secure Acquisition and Catalog - UAT

**Updated:** 2026-07-29

## Scenarios

### UAT-01: Authenticated Source Without Credential

- **Action:** Run `sync` without a credential file.
- **Expected:** `NEEDS_AUTH`; no retry, secret, state, or private byte.
- **Result:** PASS
- **Evidence:** `test_sync_without_private_credential_is_needs_auth`.

### UAT-02: Unsafe Package

- **Action:** Pass synthetic traversal, macro, OLE, ActiveX, external,
  DTD/entity, encrypted, duplicate, symlink, and expansion-risk ZIPs through
  passive inspection.
- **Expected:** `QUARANTINED` or `REJECTED`; never extract or execute.
- **Result:** PASS
- **Evidence:** Phase 37 quarantine parameterization and symlink tests.

### UAT-03: Evidence-Bound Certification

- **Action:** Certify a package with a private accepted quarantine report and
  matching allowed RightsRecord.
- **Expected:** PASS only for matching non-metadata-only rights; unsafe package
  remains `QUARANTINED`; missing or mismatched rights remains `NEEDS_RIGHTS`.
- **Result:** PASS
- **Evidence:** certification API and CLI tests.

### UAT-04: Safe Catalog Retrieval

- **Action:** Query Catalog v3 and legacy entries.
- **Expected:** deterministic certified-only default; broken dependency
  closure, malformed certified metadata, and unverified legacy entries fail
  closed. Explicit inventory may include the unverified public seed.
- **Result:** PASS
- **Evidence:** stable-ID, dedupe, closure, schema-drift, legacy, and query
  tests.

### UAT-05: Public No-Auth Tracer

- **Action:** Run all five commands using the allowlisted public metadata
  source and synthetic safe package/evidence.
- **Expected:** five machine-readable dry-run PASS manifests with no auth or
  private/commercial bytes.
- **Result:** PASS
- **Evidence:** `test_public_metadata_seed_traces_all_five_commands_without_auth`.

## UAT Decision

**Status:** PASS
**Residual risk:** Live site adapters and commercial entitlements remain
external `NEEDS_AUTH`; Phase 38 still must certify real legally usable visual
spines before any flagship or milestone release claim.
