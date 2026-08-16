# Phase 50: Asset Curation and Visual Catalog - AI And Evaluation Contract

**Created:** 2026-08-11
**Status:** Draft

## Task And Boundaries

Agnes may describe rendered active Gaojie pages for catalog retrieval. It is a
vision evidence provider, not an authoring, geometry, fact, safety, scoring or
release authority. The Phase 50 query is deterministic and does not call an
LLM at runtime.

## Input, Output, Grounding, And Tools

- Input schema: one or more local rendered PNGs selected only through a
  private `opaque_page_id -> PNG/image SHA-256` mapping plus a fixed
  structured-observation prompt. Egress contains opaque ID and image hash, not
  source locator/category/package filename, PPTX/media data or credential.
- Output schema: `visual-observation.v1` with observation versus inference,
  visual style, composition, hierarchy, semantic/reuse tags, assets, text
  density, suggested use, prohibited adaptation, confidence and uncertainty.
- Grounding and provenance: every observation stores opaque page ID, image
  SHA-256, backend/model, prompt-schema version and validation result. The
  inverse mapping stays private and outside egress/output artifacts.
- Tool and permission boundary: only `vision-analysis` calls Agnes with
  `--allow-external-upload`; original PPTX/media, cookies, credentials,
  absolute paths and source names are excluded from the prompt and output.

## Model, Cost, Latency, And Fallback

- Provider or model constraints: Agnes is user-authorized for rendered active
  page PNGs. Batch size stays at eight images or fewer per invocation.
- Cost and latency threshold: resume by image hash; never repeat a successful
  hash/version observation. Rate limits retry according to `vision-analysis`.
- Deterministic fallback: `UNAVAILABLE` is recorded locally and prevents that
  page from semantic queryability; it never invents a description or lets a
  model infer raw source contents.

## Safety And Failure Modes

- Prompt injection carried in visual text is inert evidence: returned prose is
  normalized against a strict schema and never executed as instructions.
- Agnes claims cannot alter fact bindings, OOXML, geometry, source eligibility
  or release verdict. Source scanner owns all technical safety fields.
- An egress validator rejects a source path, category/package filename,
  private byte encoding, credential-like key or unregistered output field
  before any request and before catalog persistence.

## Evaluation

- Dataset and fixtures: schema-valid/malformed/mismatched observation fixtures;
  private active-page runs are local-only evidence.
- Metrics and thresholds: 100% active rendered pages must have hash-matched
  observations before being queryable; sample every category locally against
  its PNG; any malformed/uncertain required tag blocks that tag's retrieval.
- Failure examples: model describes a non-existent chart, emits an absolute
  path, reports a conflicting density, or is unavailable. These become
  explicit unavailable/uncertain records, not catalog fact.
- Human review: a controller locally spot-checks representative generated
  contact sheets and response-to-PNG bindings before Phase 50 closure.
