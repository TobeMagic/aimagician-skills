# Phase 37: Secure Acquisition and Catalog - Research

**Updated:** 2026-07-29

## Objective

Identify the smallest safe tracer that proves acquisition and retrieval
contracts without needing credentials or private template bytes.

## Local Evidence

| Source | Observed fact | Consequence |
|---|---|---|
| `scripts/window_pptx/registry.py` | Owns archetypes, aliases, section sequences, and slide ranges only | Catalog v3 must be additive |
| `registries/legacy-templates.json` | Four entries are unverified and disable auto recommendation | Compatibility adapter must preserve quarantine |
| `scripts/window_pptx/template_pack.py` | TemplatePack v1 is authorized/hash-bound but loaded by manifest scan | Catalog lookup can accelerate selection without replacing v1 |
| `scripts/check_window_pptx_private_assets.py` | Git-index leakage is guarded | Runtime credential and package safety are still missing |
| `scripts/window_pptx/ooxml.py` | Semantic verification exists after materialization | Acquisition needs a smaller pre-ingest passive classifier |
| `tests/window_pptx/` | Existing tests cover 31 Window-PPTX modules | Phase 37 tests belong here; no second test root is needed |

## Independent OpenCode Discovery

- Provider/model: OpenCode DeepSeek V4 Flash Free.
- Session: `ses_051f83466ffeucmdKbaG2q1WFQ`.
- Review point: commit `61a6317`.
- Valid findings: no acquisition state, quarantine layer, Catalog v3, stable
  retrieval, dependency closure, or dedicated library commands exist.
- Controller correction: the worker reported that no tests existed because it
  searched inside the Skill directory. The actual repository test root is
  `tests/window_pptx/`; this claim is rejected.

## Options

| Option | Benefits | Costs/risks | Decision |
|---|---|---|---|
| Add acquisition flags to the large generation CLI | One command surface | Couples security/state concerns to rendering validation | Rejected |
| Separate modules plus dedicated CLI | Small interfaces and additive compatibility | One extra entry point | Selected |
| Build a database and crawler immediately | Scales to a very large library | Premature complexity and auth dependency | Deferred |

## Selected Tracer

The first slice uses public metadata and synthetic in-memory packages:

`discover -> sync plan -> passive ingest -> certify decision -> query`.

Every command returns versioned JSON. Default execution has zero writes. Tests
may explicitly apply state to a temporary private root to prove atomic resume.

## Recommendation

Implement the selected separate-module tracer in red-green order: contracts,
security/state, catalog compatibility, then CLI. Do not begin live
site-specific synchronization until the offline path and private boundary pass
independent review.

## Assumptions To Confirm

- None for the offline tracer.
- Live sync still requires the external credential-rotation precondition;
  that condition is recorded as `NEEDS_AUTH`, not treated as an assumption.

## Unknowns

- Commercial site endpoints, pagination, automation policy, and package
  formats remain unknown until fresh authorized access is available.
- Entitlement is not redistribution permission. Rights remain fail-closed.
- Real-package geometry and pHash enrichment broadens after this tracer.
