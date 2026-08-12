# Phase 51: Research

**Updated:** 2026-08-12

## Objective

Establish the smallest deterministic boundary between Phase 50 candidate
retrieval and later physical PPTX materialization, so agent creativity remains
in content/narrative selection rather than geometry or OOXML authoring.

## Local Evidence

| Evidence | Finding | Phase 51 consequence |
|---|---|---|
| `pptx_studio/query.py` | queries are deterministic and bounded but candidate selection is single-request and has no deck-wide compatibility state | compose from supplied bounded candidate IDs; do not rescan |
| `pptx_studio/catalog.py` / `regions.py` | pages have content-addressed IDs, source hashes, editable text shapes and safe regions | plan stores only these IDs and declared capacity |
| `pptx_studio/observations.py` | visual observations are hash-bound and egress-safe | derive style signature only from catalog + observation fields |
| v6.1 `physical_assembly.py` | a certified full-page materializer already exists | leave it unchanged; Phase 52 integrates through new plan |
| Phase 50 validation | active catalog contains 294 decks / 491 pages / 839 regions and complete observations | use a local smoke only after synthetic tests pass |

## Options

1. Let the agent emit free-form slide edits: rejected because it recreates the
   unstable visual-design dependency this project exists to remove.
2. Force every request through one source deck: rejected because real client
   decks need multiple page roles and controlled component reuse.
3. Compile bounded catalog candidates, a style lock and fact/asset ID bindings:
   selected because it preserves template fidelity while allowing governed
   flexibility.

## Recommendation

The composition request is an **intent envelope**, not a visual-authoring
language. It contains IDs that were previously returned by bounded retrieval;
the compiler independently resolves those IDs and rejects any mismatch. A
style signature is SHA-256 over a controlled taxonomy derived from observation
labels: visual archetype (`corporate`, `academic`, `technology`, `editorial`,
`minimal`, `infographic`, `festive`, or `general`) × tone (`dark`, `light`, or
`balanced`). The agent can select the anchor and named fallback signatures from
candidates but cannot author an arbitrary style. This deliberately avoids an
overfit signature per free-form Agnes prose string.

For each target slide, `exact_deck` validates a source deck/page position,
`page` validates a single source page, and `component` validates one or more
source regions. The compiler requires the source page to fit the locked style
signature and requested capacity. It never silently lowers mode.

The adaptation compiler accepts a value-bearing fact registry only at its
input boundary. Its output contains fact/asset IDs and safe target region IDs;
materializers receive values separately after revalidating the registry. This
keeps generated plans reviewable without copying client content into every
artifact.

## Failure-First Cases

- Candidate ID supplied in the intent does not resolve in the catalog.
- Caller marks `exact_deck` but uses page from a different deck or a source
  position twice.
- Candidate style signature is not anchor or explicitly allowlisted.
- Component request selects an image-only page, unknown region, or a region
  without capacity.
- Adaptation contains literal replacement text, a raw `x/y/color/font` field,
  an unknown fact/asset, or repeats an editable target.
- Materializer receives a plan whose source hash no longer matches catalog.

## Assumptions To Confirm

- The Phase 50 visual observation taxonomy can form useful coarse style groups
  despite individual free-form labels. Confirm with a local aggregate before
  using the compiler for a real deck.
- Existing physical assembly can consume source hashes/slide identities in
  Phase 52 without reopening the private source-catalog contract.

## Validation Strategy

1. Synthetic catalog/observation fixtures prove all branch and failure cases.
2. Schema validation proves public contract shape.
3. A local private smoke compiles a small multi-role plan from the Phase 50
   catalog, recording only candidate counts/digests.
4. Fresh independent review inspects public code/tests and sanitized evidence;
   it is not allowed private source content.
