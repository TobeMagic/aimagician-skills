# Phase 49: Physical Template Assembly and Work-Report Acceptance - Research

**Updated:** 2026-08-08

## Objective

Identify why the v6.1 checkpoint can produce a visually faithful physical deck
yet fails correctness, selection safety, and package-efficiency release gates.

## Local Evidence

| Source | Fact | Relevance |
|---|---|---|
| `.private/intelligence/gaojie/certified-core.json` | 288 pages from 266 packages; 129 direct-use-capable and 159 reference-only | Compiler and query must preserve eligibility |
| `page_template_library.py` | Non-first records read `slide1.xml`; all pages receive one style cluster | GOAL-49-01 and GOAL-49-02 blockers |
| `physical_assembly.py` | Per-slide namespacing repeats shared dependencies and resolves nested targets from the slide owner | GOAL-49-03 blocker |
| Audited 15-slide output | 8 unresolved chart style/color targets; output/source ratio 4.02x | Recursive QA and dedup are mandatory |
| Existing focused tests | 6/6 pass while the defects remain | New tests must exercise public behavior and nested OPC graphs |

## External Evidence

| Source | Fact | Relevance |
|---|---|---|
| ECMA-376 OPC relationship model (implemented through existing package patterns) | Relationship targets are owner-relative and content types describe concrete parts | Confirms the local root-cause analysis; no new runtime dependency required |

## Options

| Option | Benefits | Costs and risks | Verification |
|---|---|---|---|
| Keep per-slide namespacing and add verifier exceptions | Small diff | Retains bloat and cannot safely represent nested graphs | Rejected by unresolved/size gates |
| Flatten charts/media or rasterize pages | Simple packaging | Breaks native editability and accepted product boundary | Rejected by V61-ASM-01/V61-ADAPT-01 |
| Assembly-wide graph importer with cached per-source closure | Correct owner-relative graph, safe sharing, deterministic metrics | Larger internal rewrite and focused regression burden | Synthetic recursive fixtures plus private replay |

## Recommendation

Use the assembly-wide graph importer. First correct page intelligence and
eligibility; then import owner-relative closure with same-source sharing and
conservative safe dedup; finally run recursive verification and the exact
clean-room acceptance chain.

## Assumptions To Confirm

- None.
