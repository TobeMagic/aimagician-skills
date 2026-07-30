# Phase 43 Discussion Log

**Status:** Complete

## Decisions

| Topic | Options considered | Decision | Reason |
|---|---|---|---|
| Acquisition | all, first-N, preview-first | preview-first diversity | maximizes reuse and differentiation |
| Taxonomy | numeric ID, route plus ID | route plus ID | prevents cross-route collision |
| Source shortfall | duplicate fill, explicit | explicit | preserves truth |
| Private boundary | export, ignored local | ignored local | protects credentials and bytes |

- User authorized normal authenticated acquisition with a private request
  header, but credentials and commercial bytes must remain ignored and local.
- User required high differentiation within weakly named categories.
- The team rejected download-all and first-N selection.
- The accepted approach inventories previews first, selects by deterministic
  visual diversity, then downloads only validated direct packages.
- Real source insufficiency is reported as a shortfall rather than filled with
  duplicates or fabricated coverage.

## Assumptions

| Assumption | Status | Evidence or action |
|---|---|---|
| User account is entitled to exposed package links | Confirmed | authenticated normal-browser run |
| Pinned CDN needs no Cookie | Confirmed | cookie-free fixture and live behavior |

## Rejected Options

- Download-all, first-N, numeric-only taxonomy, and treating navigation pages
  as package files.

## Deferred Work

- Rendered-page semantic classification and art-direction certification move
  to Phase 44.
