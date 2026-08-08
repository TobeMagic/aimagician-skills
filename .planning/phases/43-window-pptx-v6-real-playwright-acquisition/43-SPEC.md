# Phase 43 Specification — Real Playwright acquisition

**Created:** 2026-07-30
**Status:** Locked
**Risk:** high
**User-facing:** no
**Requirements:** 1
**Original requests:** USR-V6-11, USR-V6-12

## Goal

Inventory the complete 32-category Gaojie template taxonomy and acquire a secure, resumable, preview-selected high-diversity private core through a same-origin Playwright adapter with a deterministic local fixture.

## Background

The retained Phase 37 contracts had no live source adapter. The first
authenticated probe proved 32 `products.aspx` categories but also exposed
numeric-ID collisions across routes, navigation links mistaken for files,
unbounded smoke traversal, unstable CDN preview access, and weak first-N
selection. Phase 43 replaces that path with route-aware inventory,
preview-first diversity, validated direct packages, and resumable private
evidence.

## Requirements

### V6R-ACQ-01: Authenticated, diverse, resumable private acquisition

- **Current:** The earlier foundation had no real authenticated adapter and
  could not prove complete taxonomy, diverse selection, or real package resume.
- **Target:** Discover all route-aware template categories, inventory and
  validate previews before deterministic diversity selection, acquire only
  verified editable package bytes, and preserve secret-free resumable state.
- **Acceptance:** GOAL-43-01 through GOAL-43-04 and the detailed acceptance
  checklist below all pass on current fixture and real private evidence.

## Boundaries

### In Scope

- Authenticated normal-browser discovery, preview inventory, deterministic
  diversity selection, validated package download, resume, and redaction.
- Exact-origin page navigation and one cookie-free pinned asset host.
- Ignored private state, previews, packages, and evidence.

### Out Of Scope

- Access-control bypass, redistribution, or exposing credentials/source URLs.
- Rendering, semantic page classification, visual art-direction certification,
  and materialization; Phase 44 and Phase 45 own those concerns.

## Constraints

- Credentials and commercial bytes must never cross the ignored `.private/`
  boundary.
- Site navigation is exact-origin; only the pinned asset host may serve
  cookie-free preview or direct-package bytes.
- Source shortfalls must remain explicit and cannot be converted into invented
  coverage.
- Browser work, downloads, memory, file size, disk use, and retries are bounded.

## Engineering Contract

The production entrypoint, fixture contract, security contract, acquisition
contract, output state, and exit gate below are normative. State schema v2 is
resumable but numeric-only v1 discovery is not trusted for taxonomy
completeness.

## Production entrypoint

```bash
python skills/owned/window-pptx/scripts/manage_window_pptx_library.py sync \
  --private-root skills/owned/window-pptx/.private \
  --source-id gaojie-entitled \
  --source-adapter gaojie \
  --origin http://www.gaojiewenhua.cn \
  --allow-host www.gaojiewenhua.cn \
  --allow-insecure-http \
  --credential-file skills/owned/window-pptx/.private/auth/gaojie.cookie \
  --apply
```

The HTTP exception is explicit because the observed site does not serve
working HTTPS. Authentication remains same-origin and the adapter rejects
other schemes/hosts.

## Browser fixture

The repository test server models login redirect, cookie acceptance, category
navigation, pagination, detail pages, downloads, duplicate bytes, and expired
sessions. Real adapter work may not start from untested selectors alone.

## Runtime behavior

- Cookie text is read only from the validated private file and injected into a
  fresh ephemeral browser context.
- Raw Cookie text, a `Cookie:` header, and browser-copied alternating
  header-name/header-value lines are accepted; conflicting Cookie candidates
  fail closed.
- Successful authentication must reach products without login controls.
- Exactly the 32 nonzero `products.aspx` template categories are required.
  Category identity is `(route_path, category_id)`, never the numeric ID alone;
  `case.aspx`, `example.aspx`, `honor.aspx`, `down.aspx`, and other site
  sections are recorded as observations but cannot overwrite template
  categories.
- Every category page and pagination page is inventoried before final
  selection. Product cards are recognized as same-origin
  `products_show.aspx?id=...` links and retain title, preview URL, route-aware
  category provenance, and secret-free URL digests.
- Preview images are downloaded under `.private/previews/gaojie/`, validated as
  images, content-hash deduplicated, and described by deterministic visual
  features: perceptual hash, coarse color histogram, entropy, edge density,
  dimensions, and aspect ratio.
- Selection is per category, deterministic, and diversity-first. Exact preview
  duplicates are removed, near-duplicates are suppressed, and farthest-first
  traversal selects up to 12 candidates while preserving category coverage.
  A category with fewer than eight valid diverse candidates produces an
  explicit `DIVERSITY_SHORTFALL` finding instead of inventing coverage.
- `--maximum-items` is a real bounded smoke mode: it may stop inventory and
  detail traversal once enough downloadable candidates are proven and must
  never crawl the complete catalog before returning one item.
- Category, pagination, and product-detail navigation remain on the exact
  configured origin. Preview images and direct PowerPoint files may additionally
  use the pinned HTTPS asset host `wstx.web.vleader.net.cn`; no authentication
  Cookie is attached to that host, and requests carry only the same-site page
  Referer required by the CDN.
- Legacy catalog links that name that exact pinned CDN over HTTP are
  deterministically upgraded to HTTPS before fetching. No other foreign HTTP
  host is accepted. CDN bytes use bounded cookie-free short requests with
  controlled concurrency; authenticated page navigation remains sequential in
  the ephemeral browser context.
- Transient preview failures receive bounded immediate retry and one
  post-inventory page revisit before selection. A failed first fetch therefore
  cannot silently remove an otherwise valid candidate from a category.
- Only direct file links ending in `.pptx`, `.ppt`, `.potx`, `.pot`, or `.zip`
  are download candidates. Navigation pages such as `/down.aspx` are not
  treated as files even when their label contains “download”.
- Downloads are accepted only from successful non-HTML responses.
- `.pptx` and `.potx` bytes must have a ZIP signature and contain the expected
  OOXML presentation member before atomic promotion.
- Bytes are SHA-256 deduplicated and atomically promoted below
  `.private/sources/gaojie/`.
- Secret-free state below `.private/state/gaojie-sync.json` supports resume.
- Remaining disk below 40 GiB fails closed by default.
- Site drift, expired auth, incomplete taxonomy, missing download links, and
  HTTP errors produce explicit findings.

## Exit gate

Fixture tests, existing acquisition tests, secret guard, and independent
specification/quality review must pass. A real smoke must authenticate, discover
all 32 template categories, inventory preview-backed product cards, select a
diverse candidate, and atomically promote at least one valid editable
PowerPoint package. Phase 43 cannot claim complete merely from fixture success,
thumbnail access, or a login-page heuristic.

## Detailed Acceptance

- [ ] 32/32 `products.aspx` template categories are discovered with stable
      route-aware identities and nonempty public labels.
- [ ] Every discovered product has category provenance and either a validated
      preview or an explicit preview failure.
- [ ] For each sufficiently populated category, selection contains 12
      content-hash-unique candidates and beats deterministic first-N on median
      nearest-neighbor visual distance.
- [ ] A one-item smoke completes without full-catalog traversal and promotes a
      valid OOXML/PowerPoint file.
- [ ] Resume after interruption neither redownloads valid bytes nor skips
      missing/corrupt artifacts.
- [ ] State, stdout, stderr, tests, reports, and OpenCode review contain no
      credential values.

## Test Seams And Critical Cases

| Behavior | Observable Seam | Failing Case | Evidence |
|---|---|---|---|
| V6R-ACQ-01 | Fixture, focused tests, real sanitized manifest | taxonomy drift, secret leakage, invalid package, broken resume | `43-VALIDATION.md` |

## Acceptance Criteria

- [x] V6R-ACQ-01 has passing fixture, focused, private-guard, real UAT, and
  independent completion-audit evidence covering GOAL-43-01 through
  GOAL-43-04.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.96
- **Boundary clarity:** 0.95
- **Constraint clarity:** 0.94
- **Acceptance clarity:** 0.96
- **Ambiguity:** 0.05

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | Reality | What is a template category? | Only the 32 nonzero route-aware `products.aspx` categories. |
| 2 | Quality | How is weak naming handled? | Validate images and select deterministically by visual distance. |
| 3 | Security | May the CDN receive Cookie? | No; it receives only bounded cookie-free requests and same-site Referer. |
| 4 | Integrity | How are unavailable packages represented? | Explicit NO_LINK, UNAVAILABLE, or diversity shortfall; never invented coverage. |
