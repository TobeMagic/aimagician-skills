# Phase 31 Specification: Trusted Visual Preservation and Golden Replay

**Status:** Locked
**Risk:** high
**User-facing:** yes
**Requirements:** V51-TPL-01, V51-TPL-02, V51-TPL-03, V51-DESIGN-04

## Goal

Close the portable TemplatePack contract with a reproducible golden-r10
generation path and a non-self-referential visual-preservation metric that
detects changes outside declared editable regions.

## Current

The adapter already preserves undeclared package parts, updates governed text
and chart/workbook slots atomically, renders r10 without COM, and passes
structural reference-grade checks. The remaining `0.98` non-slot similarity
requirement has no frozen executable definition, and r10 generation is not yet
one clean-clone command with a compact manifest.

## Target requirements

### P31-MASK-01 — trusted visual masks

**Current:** TemplatePack slots identify editable OOXML targets but do not
declare rendered mask geometry.

**Target:** The TemplatePack authoring path derives normalized visual masks
from the source PPTX shape tree, including nested group transforms and chart
frames. Masks are source-hash-bound, schema-validated, deterministic, and never
model-authored.

**Acceptance:** Repeated inventory produces identical masks; unknown shape
targets, invalid geometry, excessive mask coverage, unsupported transforms, or
source-hash drift fail before scoring.

### P31-SIM-01 — masked non-slot rendered similarity

**Current:** Structural preservation and PNG quality checks do not quantify
rendered pixels outside editable regions.

**Target:** A deterministic scorer compares source and candidate PNG pages from
the same renderer fingerprint, excludes only trusted mask pixels, and reports
per-slide/deck similarity and changed-pixel ratios.

**Acceptance:** Every accepted page has mean absolute similarity at least
`0.98` outside masks and changed-pixel ratio at most `0.02` using an 8/255
channel tolerance. Page count, dimensions, missing masks, renderer mismatch,
or mask coverage above `0.80` fail closed. A synthetic out-of-mask mutation
fails while a mutation fully inside a declared mask passes.

### P31-GOLD-01 — reproducible golden replay

**Current:** r10 exists as local evidence but requires multiple manual commands.

**Target:** One skill-owned command validates the source hash and bindings,
adapts the TemplatePack, renders source and candidate with the same portable
engine, runs structural/PNG/masked-similarity gates, and emits a compact
hash-bound manifest.

**Acceptance:** Two clean output directories produce byte-identical PPTX and
semantically identical compact manifests apart from explicitly excluded
absolute paths/timestamps. Candidate hashes remain stable before and after
proof rendering.

### P31-AUTHOR-01 — deterministic authoring support

**Current:** Building masks or reviewing slot coverage requires ad hoc
inspection.

**Target:** A read-only authoring command inventories nested shapes, chart
frames, slot capacity, and proposed masks into a reviewable JSON document. It
does not mutate the source or silently register new slots.

**Acceptance:** The institutional TemplatePack inventory covers all declared
text and chart targets, validates against the source hash, and can be
round-tripped through its schema.

## Boundaries

### In scope

- TemplatePack schema, loader, authoring inventory, and visual-mask contract.
- Portable source/candidate rendering with identical engine fingerprint.
- Masked PNG similarity report and hard gate.
- Golden-r10 replay CLI and compact evidence manifest.
- Tests for nested transforms, chart masks, overflow, tampering, and
  reproducibility.

### Out of scope

- Whole-slide screenshot delivery.
- Model-authored masks, coordinates, OOXML, HTML, or code.
- Closing human/vision-model blind review.
- Mandatory COM or automatic registry repair.
- The consulting-proposal composition grammar, which begins in Phase 32.
- The formal two-model benchmark.

## Invariants

1. The authorized source PPTX remains byte-identical.
2. Masks are derived only from the hash-bound source and declared targets.
3. Mask generation cannot inspect source/candidate pixel differences.
4. Candidate rendering cannot modify the candidate.
5. Automatic similarity is engineering evidence, never human visual approval.
6. Large proof artifacts remain local; committed evidence is compact.

## Acceptance checklist

- [ ] TemplatePack schema and loader accept trusted normalized masks.
- [ ] Nested group and chart target inventory is deterministic and complete.
- [ ] In-mask changes pass and out-of-mask changes fail the scorer.
- [ ] Excessive masks, page mismatch, renderer mismatch, and invalid geometry fail.
- [ ] Golden-r10 replay passes twice with stable candidate hash.
- [ ] Focused and full Window-PPTX regression pass.
- [ ] Skill documentation and Phase 31 validation record exact evidence.
- [ ] Independent specification, quality, and verification reviews have no unresolved Blocker or Important finding.

## Ambiguity report

Goal clarity: 0.99
Boundary clarity: 0.98
Constraint clarity: 0.96
Acceptance clarity: 0.96
Ambiguity: 0.02

## Decision log

- Use trusted geometry masks plus exact OOXML preservation; reject
  whole-slide-only similarity.
- Use mean absolute pixel similarity and changed-pixel ratio as complementary
  deterministic signals.
- Freeze `0.98`, `0.02`, 8/255, and `0.80` as Phase 31 defaults; later
  calibration requires a versioned profile change.
- Keep COM optional and keep human/vision review as a separate verdict.
