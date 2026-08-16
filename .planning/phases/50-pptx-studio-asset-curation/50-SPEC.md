# Phase 50: PPTX Studio — Asset Curation and Visual Catalog

**Created:** 2026-08-11
**Milestone:** v7 PPTX Studio Curated Composition
**Roadmap phase:** 50
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Requirements:** 5

## Goal

Convert the user-approved Gaojie category subset into an explicit, recoverably curated local source set and produce deterministic deck, page, and region records enriched with authorized Agnes visual observations so later retrieval does not depend on anonymous files or a model visually browsing all assets.

## Background

The current private root contains 377 PPTX packages (about 1.4GB) across 29
category directories. The existing `asset-index.json` is package-centric,
reports 620 rendered pages, and contains all categories. `certified-core.json`
contains passive visual dispositions but not the deck/page/region semantic
descriptions an agent needs. The Phase 49 page query can rank certified whole
pages, but it has no owned component model, no approved-category gate and no
visual-language retrieval.

## Requirements

### V7-CURATE-01: Recoverable active-source curation

- **Source requests:** USR-V7-01
- **Current:** Active and low-value categories coexist; filenames are opaque.
- **Target:** The 22 approved category directories become the only active
  source scope and the other seven are moved to a dated private archive with
  one manifest record per package: opaque source ID, original relative locator,
  archive relative locator, source SHA-256, post-move SHA-256 and the exact
  hash-guarded recovery operation. The manifest has separately hashed aggregate
  before/after tree partitions and an atomic recovery procedure.
- **Acceptance:** GOAL-50-01 and curation tests prove the exact active set,
  no accidental active move, and complete archive reversibility.

### V7-CATALOG-01: Deterministic private deck/page catalog

- **Source requests:** USR-V7-01
- **Current:** Rendering/fingerprint evidence exists, but not a current
  curated deck/page catalog with normalized source identities.
- **Target:** Compile a local-only catalog with stable deck/page IDs, hashes,
  roles, source category, page count, structural/style features and rendered
  PNG evidence; tracked files contain schemas/code/test fixtures only.
- **Acceptance:** GOAL-50-02 and repeat compilation/query byte equality pass.

### V7-VISION-01: Hash-bound visual observations

- **Source requests:** USR-V7-01
- **Current:** No semantic visual description lets an agent find a suitable
  design from content intent.
- **Target:** Use the user-authorized Agnes route on rendered active-page PNGs
  only; a private mapping resolves opaque page ID to rendered PNG and SHA-256
  before upload. Prompts/responses contain only opaque page ID, image hash and
  visual schema fields—never source paths, PPTX/media bytes, package names or
  credentials. Validate each normalized observation against PNG SHA-256 and
  record observations, inference, and uncertainty in the private catalog.
- **Acceptance:** GOAL-50-03, response-schema tests, and local spot checks
  pass; private payloads/absolute paths never enter Git or an external prompt.

### V7-REGION-01: Safe component-region extraction

- **Source requests:** USR-V7-01
- **Current:** A page is the smallest reusable object.
- **Target:** Extract candidate title, text, data, image, card, process,
  decorative and complete-page regions using OOXML shape bounds plus visual
  evidence. Record normalized rectangle, z-order, editable source shapes,
  asset policy, text capacity, hierarchy, tags and prohibited adaptations.
- **Acceptance:** GOAL-50-04 and fixtures prove deterministic IDs, safety
  rejection, overlap resolution and no source path escape.

### V7-QUERY-01: Bounded explainable retrieval

- **Source requests:** USR-V7-01
- **Current:** Existing query is role-only whole-page selection with a fixed
  certified-core lens.
- **Target:** A new local catalog query accepts only declared role, semantic,
  style, capacity and reuse-mode inputs; it returns 3–6 candidates plus all
  gates/scores/reasons. It never scans a client directory or raw source tree.
- **Acceptance:** GOAL-50-05 and deterministic fail-closed query tests pass.

## Boundaries

### In Scope

- Curation manifests, active-source compiler, local deck/page/region schemas,
  visual-observation normalization, bounded query CLI, and focused tests.
- Private archive/catalog/evidence output under the explicitly configured
  private root, never tracked by Git.

### Out Of Scope

- Component physical assembly/adaptation, public package rename/removal,
  global QA/repair harness, client-folder generation and release acceptance.
- Deletion, redistribution, upload of original PPTX bytes, unbounded agent
  file browsing, mandatory COM, or using the clean client folder as a library.

## Constraints

- User authorization covers rendered active-page PNG upload to Agnes for this
  catalog only. Original PPTX/media bytes, credentials and absolute paths are
  never uploaded, logged or committed.
- The source root is explicit (`--private-root`, environment/config) and is
  outside any client folder. Archive is recoverable and hash-bound.
- Catalog compiler/query are deterministic. A missing render/observation,
  mismatched hash, unsafe relationship, image-only region, unknown taxonomy,
  path escape or incomplete manifest is a fail-closed error.

## Engineering Contract

- **Domain terms and owners:** `SourceScope` owns approved categories;
  `CurationManifest` owns active/archive identity; `DeckRecord`, `PageRecord`,
  and `RegionRecord` own three-level retrieval evidence; `VisionObservation`
  owns Agnes-derived description; `CatalogQuery` owns bounded selection.
- **Invariants:** no private bytes in tracked output; every curation package
  record binds opaque ID, original/archive relative locators, source/post-move
  SHA-256 and recovery operation; active and archived names form an exact
  partition; page/region refs stay within one validated source package; only
  the private uploader mapping sees a source locator; visual response binds a
  rendered image hash; a query never discovers files; equal query scores use
  stable catalog ID ascending as the final tie-break.
- **Interfaces and compatibility:** Phase 50 adds `pptx_studio` modules and
  versioned JSON schemas without altering Phase 49 `window_pptx` APIs. The
  old package is only read as implementation/reference input until Phase 52.
- **Failure semantics:** incomplete/unsafe data produces explicit structured
  `FAIL`/no-result output and no archive move or candidate selection.
- **Migration and rollback:** archive action records pre/post hashes and a
  recover command before move. Reversal moves only exactly hash-matching
  archived paths; source mismatch aborts. Public name migration is deferred.

## Test Seams And Critical Cases

| Behavior | Observable Seam | Failing Case | Evidence |
|---|---|---|---|
| approved source partition | `plan_curation` / `apply_curation` | unknown/duplicate category, missing file, active source listed for archive, missing post-move record | focused curation tests + private manifest |
| deterministic catalog | `compile_catalog` | unrendered page, hash mismatch, root escape, duplicate ID | repeat serialized JSON + focused catalog tests |
| visual grounding | `validate_observation` / `build_vision_request` | missing/malformed schema, mismatched PNG SHA, source identifier/path/byte egress | fixture tests + one local visual spot-check |
| safe region record | `extract_regions` | image-only, non-editable, overlapping or unbounded region | synthetic OOXML fixtures and deterministic output |
| local query | `query_catalog` | client-root locator, unknown mode/tag/style, non-active candidate or equal-score unstable order | focused query tests and byte-identical response |

## Acceptance Criteria

- [x] AC-50-01: `active-source-scope.v1.json` names exactly the 22 approved
  categories, captures pre-move inventory/hash/count/bytes, and a dry-run
  archive plan names exactly the seven inactive categories.
- [x] AC-50-02: apply mode moves only the inactive directories under a dated
  private archive root, writes an atomic archive manifest with pre/post tree
  digests and one opaque-ID/original-locator/archive-locator/source-SHA/post-
  move-SHA/recovery-operation record per package, and `verify`/`recover
  --dry-run` prove reversibility.
- [x] AC-50-03: active catalog compilation produces one stable deck record per
  active package and one page record per rendered page. It is byte-identical
  on repeat and rejects invalid/private-root escaping inputs.
- [x] AC-50-04: all active page records have a hash-bound normalized visual
  observation or an explicit `UNAVAILABLE` status that blocks queryability;
  observations are rendered-PNG-only and structurally validated. An egress
  fixture proves prompts/responses/artifacts expose neither source path,
  package/category filename, PPTX/media bytes nor credentials.
- [x] AC-50-05: region extraction emits only declared editable safe regions
  and explains exclusions. Candidate IDs/geometry/capacity are stable across
  repeated output.
- [x] AC-50-06: retrieval filters by mode, role, tags, style/capacity and
  source scope; repeated output is byte-identical, maximum result count is
  enforced, and query reads only its compiled catalog.
- [ ] AC-50-07: focused tests, private smoke compile/query, workflow gates,
  plan review and an independent phase audit have no unresolved Blocker or
  Important finding.

## Blocking Questions

- None.

The user explicitly approved the active category set, recoverable archive,
Agnes rendered-image analysis, final product name and no-shim migration. The
exact active-package count is an observed output, not a planning assumption.

## Ambiguity Report

- **Goal clarity:** 0.94
- **Boundary clarity:** 0.92
- **Constraint clarity:** 0.92
- **Acceptance clarity:** 0.91
- **Ambiguity:** 0.08

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | User outcome | Is one fixed reference deck sufficient? | No. Adopt deck/page/region retrieval with later governed assembly. |
| 2 | Safety | Delete unapproved source categories? | No. Archive privately with hashes and a recovery procedure. |
| 3 | Visual grounding | Let a text-only agent browse anonymous files? | No. Create hash-bound rendered-page observations through authorized Agnes. |
| 4 | Migration | Rename while curation is in flight? | No. Keep old code read-only, migrate flag-day only in Phase 52 after tests. |
