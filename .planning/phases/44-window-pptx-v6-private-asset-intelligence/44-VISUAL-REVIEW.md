# Phase 44 Private Contact-Sheet Visual Review

**Status:** complete; final direct-use blind review GO
**Private evidence:** 32 labeled category sheets plus one overview; images remain
under the ignored `.private/` tree.

## Invocation

- Objective: assess cross-category differentiation, within-category
  repetition, page-family coverage, reusable cores, weak categories, and
  visible loading/crop defects.
- Backend: Agnes `agnes-2.0-flash`
- Attempts: 1
- Rate-limit events: 0
- Transient retries: 0
- Input: the generated 32-category overview only; no Cookie, source URL, or
  request header was uploaded.

## Visible observations retained

- The selected set spans covers, contents, sections, title systems, closings,
  one-to-six/multi-block pages, people, awards, timelines, processes,
  business models, mockups, quotes, partners, image-text layouts, charts,
  complete works, maps, data/text components, and decorative shapes.
- `055 图文排版`, `056 表格图表`, `038 标题模板`, `104 数据基座`, and
  `105 文本组件` are high-reuse families.
- `040 素材图片` is an asset pool rather than a page-layout family and must be
  routed separately.
- `058 实用素材` and `062 风格配色` contain only three/four visually distinct
  collection-cover candidates. They are useful as meta/style-pack entry
  points, not certified slide-layout pages.
- `106 装饰形状` is visibly narrow and heavily blue/curve-oriented.
- `039 结尾模板` has repeated “THANKS” conventions and should receive lower
  selection weight unless a project explicitly requests that convention.
- No obvious blank image, corrupt raster, or gross crop failure is visible in
  the overview.

## Controller spot-check corrections

The full-resolution local overview does not support several claims in the
first Agnes narrative:

- `036 目录模板` visibly contains multiple directory/navigation layouts; it is
  not missing.
- `050 架构流程` visibly includes hierarchy, circular, matrix, and horizontal
  process structures; it is not limited to horizontal arrows.
- `082 地图排版` visibly contains China/world/regional map layouts.
- `058` and `062` are not failed image loads. Their previews are legible
  collection-cover slides, but they are the wrong abstraction level for a
  page-layout core.
- The overview contains 12 or fewer selected candidates per category, not 24.

## Decisions

1. Preserve the source taxonomy as provenance, but add a second semantic role
   taxonomy; source labels cannot directly own generation routing.
2. Route `素材图片`, `实用素材`, `风格配色`, `文本组件`, and `装饰形状` as
   support/style/component packs where appropriate rather than ordinary slide
   layouts.
3. Use the rendered PowerPoint pages, not catalog previews alone, for final
   certification and visual duplicate clustering.
4. Require category-specific selection weights and a per-deck repetition cap
   before Phase 45 materialization.

## Full rendered q0.75 review

The committed implementation generated 16 private contact sheets covering
312/312 preliminary pages. A fresh independent local pixel context classified
every ordinal exactly once:

| Decision | Count | Route |
|---|---:|---|
| keep | 136 | `complete-layout` |
| reroute | 103 | named component, asset, specialty, or case pool |
| deny | 73 | `excluded` |

The exact complete partition is machine-bound by ordered page-set digest in
`registries/gaojie-visual-disposition-v1.json`. It contains no private path,
source URL, or asset byte.

Serious deny evidence includes:

- one visible third-party watermark;
- fifteen portrait-poster pages;
- one visible duplicate;
- 56 Important pages with obsolete clip-art, unreadable density/contrast,
  broken formatting, or art direction below the reference bar.

The resulting v2 core contains 136 layout pages and 103 support pages. All 73
denied pages are absent from both pools. Cross-pool exact/near dedupe found no
additional alias among the remaining 239 pages.

## Supplement band

All 79 rendered pages in the half-open quality band `[0.65, 0.75)` were
collected; four private contact sheets cover 79/79 exactly.

The first direct Agnes four-sheet review is retained as invalid evidence:

- it treated the contact-sheet routing caption `supplement-review` as a slide
  watermark;
- its enumerated keep/reroute/deny ordinals did not cover 79 pages;
- its stated group counts contradicted its explicit lists.

No supplement decision is accepted from that response.

A second independent local pixel context then classified every supplement
ordinal exactly once:

| Decision | Count | Route |
|---|---:|---|
| keep | 32 | `complete-layout` |
| reroute | 42 | eleven named component/style/specialty pools |
| deny | 5 | `excluded` |

The five deny decisions are two portrait-poster Blockers and three Important
low-contrast, tiny-text, or visibly dated/dense pages. The exact full
partition is digest-bound in
`registries/gaojie-supplement-disposition-v1.json`.

The first merged core contained 313 usable pages:

- 168 complete layouts;
- 145 support/specialty pages;
- 78 denied pages isolated outside every certified pool;
- no additional exact or near duplicate after deterministic cross-pool
  canonicalization.

Sixteen regenerated private contact sheets covered 313/313 pages. The first
independent final-pool review found three Important defects:

- one same-package visible duplicate;
- one “THANKS” page with an unnatural `THANK` / `S` line break;
- one component retaining a non-generic “高阶 PPT” supplier mark.

All three pages were moved to explicit deny reasons. The corrected core had
310 pages: 166 complete layouts and 144 support/specialty pages, with 81 total
denied pages. Sixteen regenerated sheets covered 310/310 pages.

That fresh-context review found a second class of problems that the earlier
layout-quality review did not model:

- five supplier/contact identity Blockers;
- seven crop, clipping, broken-wrap, orphan-line, or low-contrast Important
  failures;
- 37 otherwise useful brand, product, IP, partner-wall, and case-study pages
  that are valuable as art-direction references but unsafe for direct
  materialization without content replacement.

The digest-bound
`registries/gaojie-final-visual-overrides-v1.json` now hard-denies the 12
defective/identity pages and routes the 37 branded examples to
`reference-only/brand-case` or `reference-only/partner-wall`. Every
reference-only record has `auto_materialize=false`, `direct_use=false`, and
`requires_content_replacement=true`.

The quality-first final core contains 288 pages:

- 129 direct-use pages;
- 159 isolated reference-only pages;
- 103 total denied pages;
- zero current exact/near aliases.

All 391 rendered candidates at or above the 0.65 quality floor were reviewed.
The 12-page shortfall against the nominal 300-page target is explicit and is
not backfilled from the 229 lower-quality rendered pages. Fifteen regenerated
private sheets cover 288/288 pages exactly once.

Repeated fresh-context reviews then operated on direct-use-only sheets so that
known branded and repair-required references could not mask remaining direct
defects. The final seven-sheet review covered 129/129 direct-use pages and
returned GO with zero Blocker, zero Important, and five recorded Nitpicks.
`44-FINAL-VISUAL-AUDIT.md` contains the full iteration and isolation record.
