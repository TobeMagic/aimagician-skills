# Phase 43 Engineering Design — Route-aware diverse acquisition

## Behavior contract

The adapter inventories the complete 32-category Gaojie template catalog,
selects a deterministic visually diverse private core from preview images, and
downloads only direct valid PowerPoint packages. It remains same-origin,
credential-redacted, resumable, bounded, and nonredistributable.

## Domain model

- `TemplateCategoryKey`: normalized route path plus numeric category ID.
- `CatalogItem`: detail URL digest, public title, category keys, preview
  evidence, and optional selected artifact evidence.
- `PreviewFingerprint`: content SHA-256, perceptual hash, color histogram,
  entropy, edge density, dimensions, and aspect ratio.
- `DiversitySelection`: deterministic ordered item IDs, first-N baseline
  metrics, selected-set metrics, rule version, and shortfall findings.
- `Artifact`: private relative path, byte digest, file kind, size, and category
  provenance.

## Invariants

1. Numeric IDs from different route paths never collide.
2. Credentials are read only from the validated private file and never enter
   state, logs, reports, prompts, filenames, or exceptions.
3. Navigation is exact-origin. Preview and artifact URLs are exact-origin or
   on the pinned HTTPS CDN; authentication cookies are never sent to the CDN.
   An observed legacy HTTP link is upgraded only when its hostname exactly
   matches the pinned CDN.
4. Exact preview bytes and exact PowerPoint bytes are stored once.
5. Selection is deterministic for the same inventory and rule version.
6. Bounded smoke work is proportional to its requested item limit.
7. HTML, redirects outside the origin, malformed images, and malformed
   PowerPoint packages are never promoted as templates.

## Options considered

### A. Download everything, deduplicate later

Simple but slow, wasteful, and produces a low-signal private library. Rejected
because the user explicitly requires high differentiation and reusability.

### B. First-N per category

Fast but site ordering can group near-identical styles. Rejected because it
does not inspect images and cannot demonstrate diversity.

### C. Preview-first deterministic selection, then package download

Chosen. It inventories the complete catalog cheaply, uses observable visual
features to select representatives, and defers expensive rendering and semantic
certification to Phase 44.

### D. Long-lived browser request context for every CDN byte

Rejected after live evidence showed that a long catalog run could leave that
request context returning transient failures while the same image succeeded in
a fresh request. Authenticated HTML remains in Playwright; pinned CDN bytes use
cookie-free, bounded short requests with 16-way concurrency, immediate retry,
and one post-inventory recovery pass.

## Test seams

- Pure Cookie/request-header parsing.
- Pure route-aware category-key normalization.
- Pure image fingerprinting from fixture bytes.
- Pure deterministic diverse selection against a known duplicate/variant set.
- Fixture Playwright inventory with pagination, lazy preview attributes,
  cross-route category-ID collisions, HTML navigation links, and direct PPTX.
- Live bounded smoke with secret-free state inspection.

## Migration and rollback

State schema advances from `gaojie-sync.v1` to `gaojie-sync.v2`. V1 state is
not trusted for taxonomy completeness because numeric-only category identity is
lossy; existing verified artifacts may be hash-reconciled but discovery is
rebuilt. Rollback is the previous commit plus ignored private state; no public
catalog or credential migration is required.
