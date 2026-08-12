# Phase 50: Asset Curation and Visual Catalog - Research

**Updated:** 2026-08-11

## Objective

Establish a small, safe local library boundary that enables later semantic
retrieval without accidentally exposing private bytes, assuming category names
or letting visual-model prose control technical adaptation.

## Local Evidence

| Source | Fact | Relevance |
|---|---|---|
| `.../window-pptx/.private/sources/gaojie` | 29 category directories, 377 PPTX packages and about 1.4GB; the user supplied an exact allowlist of 22 active categories. | Curation must be manifest-first and recoverable. |
| `private_asset_intelligence.py` | Existing `mine_gaojie_private_assets` uses portable LibreOffice rendering, hashes each rendered page and stores relative local paths. | Reuse proof/render patterns, but do not mutate its historical output contract. |
| `page_template_library.py:resolve_private_root` | Explicit flag, then `WINDOW_PPTX_PRIVATE_ROOT`, then config controls private root and validates its asset index. | New catalog must retain explicit external-private-root policy, but migrate name only in Phase 52. |
| `page_template_library.py:compile_page_templates` | Current stable route compiles whole certified pages and slot graph metadata from the old private core. | Phase 50 adds a separate catalog rather than destabilizing v6.1 acceptance APIs. |
| `.planning/phases/49-*/49-SPEC.md` | Clean client roots must not be scanned for private templates and private bytes never enter Git/reviewer packets. | Continue this invariant for all new catalog/query operations. |
| `vision-analysis/SKILL.md` | Agnes requires explicit external-upload authorization, a rendered image path and a hash-bound sanitized response. | User supplied authorization for retained rendered page analysis; original files stay local. |

## External Evidence

| Source | Fact | Relevance |
|---|---|---|
| Agnes visual-analysis workflow (local skill) | Explicitly uploads only declared image inputs and emits hashes/sanitized text. | Provides the authorized visual-evidence boundary; no external visual source/repository is needed. |

## Options

| Option | Benefits | Costs and risks | Verification |
|---|---|---|---|
| Extend legacy page-template library directly | Minimum new code | Couples uncurated historical core, Phase 49 contract and future rename; regions would be implicit | Could pass unit tests but makes migration unsafe |
| New `pptx_studio` catalog beside legacy route | Isolates schemas, permits dry-run archive and a clean migration seam | Some temporary duplicated parsing until Phase 52 | Deterministic fixture/private smoke query and no legacy diff |
| Use vision descriptions as the only catalog | Rich semantic search | Cannot prove editable geometry/capacity or safe source relation | Rejected by synthetic OOXML fixtures |
| Combine OOXML/portable evidence with visual descriptions | Separates measurable source facts from design interpretation | More schemas and a batch observation job | Hash-bound catalog plus local visual spot-check |

## Recommendation

Choose a new `pptx_studio` module with five shallow public entry points:
`plan_curation`, `apply_curation`, `compile_catalog`, `validate_observation`,
and `query_catalog`. Keep private archive/catalog bytes outside the Git
worktree. The compiler owns hard provenance, geometry and editability; Agnes
owns only structured visual observations; query owns deterministic bounded
ranking. This creates a reversible tracer and leaves actual assembly to Phase
51.

## Assumptions To Confirm

- The active package/page count is deliberately measured at compile time,
  because duplicate filenames and multi-slide packages make planning estimates
  unreliable. This is not a blocking ambiguity.
