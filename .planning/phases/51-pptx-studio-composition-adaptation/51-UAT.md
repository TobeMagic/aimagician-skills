# Phase 51: UAT

**Updated:** 2026-08-12

## Scenarios

### UAT-01: Coherent Page Assembly

- **Starting state:** complete Phase 50 catalog/observation index.
- **Action:** choose four role-compatible catalog pages sharing one derived
  style signature, then compile page assembly.
- **Expected visible result:** ordered source page provenance, capacity
  evidence, an anchor style match, and no physical source mutation.
- **Result:** PASS
- **Evidence:** local smoke compiled four targets/roles with one style
  signature and deterministic plan digest recorded in validation.

### UAT-02: Exact-Deck and Component Boundaries

- **Starting state:** synthetic catalog with ordered multi-page source deck
  and eligible component regions.
- **Action:** compile exact-deck and component strategies, then present an
  off-deck, role-incompatible and unknown-region selection.
- **Expected visible result:** valid strategies pass; invalid selection fails
  closed instead of falling back to an arbitrary page.
- **Result:** PASS
- **Evidence:** focused composition tests cover stable exact-deck, style,
  candidate, sequence, and component failure paths.

### UAT-03: Fact and Asset Binding Safety

- **Starting state:** validated page-assembly plan, registered text fact and
  asset hash.
- **Action:** bind a fact to a safe region and an asset to an existing image
  shape; then try literal text, unknown fact, overflow, duplicate target and
  source drift.
- **Expected visible result:** valid plan contains IDs only; every unsafe case
  is rejected before any package write.
- **Result:** PASS
- **Evidence:** focused adaptation/CLI tests and local smoke.

## UAT Decision

**Status:** PASS
**Residual risk:** later physical assembly and rendered QA must verify that
valid plan operations preserve visual quality in real PPTX files.
