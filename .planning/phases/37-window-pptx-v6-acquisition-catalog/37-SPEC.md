# Phase 37 Specification: Secure Acquisition and Catalog

**Status:** Locked
**Depends on:** Phase 36
**Requirements:** V6-ASSET-01, V6-LIB-01

## Goal

Build a resumable, entitlement-aware private template acquisition and catalog
pipeline without exposing credentials, executing active content, or committing
original assets.

## Acceptance

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
