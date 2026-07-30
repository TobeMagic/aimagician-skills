# Phase 43 Research

**Status:** Complete

## Objective

Determine the real taxonomy, authenticated navigation, preview, package, and
selection constraints required for a safe production adapter.

## Local Evidence

| Source | Fact | Relevance |
|---|---|---|
| Authenticated read-only probe | 32 nonzero template categories | Fixes the completion target. |
| First adapter run | Numeric IDs collide across routes | Requires route-aware category identity. |
| Product pages | Preview and package links may use a pinned CDN | Requires a cookie-free asset policy. |
| Category ordering | Visually similar items are adjacent | Rejects first-N selection. |

Authenticated read-only probing established the real source model before the
final adapter was locked:

- exactly 32 nonzero `products.aspx` template categories;
- numeric category IDs collide with unrelated routes and cannot be global IDs;
- product cards link through `products_show.aspx`;
- previews and packages may use one legacy pinned CDN;
- navigation labels containing “download” are not necessarily files;
- category ordering contains visually similar neighbors, so first-N is unsafe;
- long-lived CDN request state can become transiently stale and needs bounded
  cookie-free short requests plus retry.

These findings are implemented in `43-DESIGN.md` and `43-SPEC.md`.

## Options

| Option | Benefits | Costs and risks | Verification |
|---|---|---|---|
| Download all | Simple | Wasteful and duplicate-heavy | Rejected against user request |
| First-N per category | Fast | Visually homogeneous and ordering-dependent | Diversity fixture |
| Preview-first diversity | Complete inventory with bounded package work | Requires fingerprinting and retry | Fixture plus real UAT |

## Recommendation

Use route-aware complete preview inventory, deterministic farthest-first
selection, then validated direct-package acquisition and resumable
reconciliation.

## Assumptions To Confirm

- None.
