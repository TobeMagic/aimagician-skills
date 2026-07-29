# Phase 41: AI-Only Acceptance and Closure - Specification

**Created:** 2026-07-30
**Status:** Locked
**Risk:** high
**User-facing:** yes
**Depends on:** Phases 39 and 40
**Requirements:** 6

## Goal

Close v6 only after deterministic engineering evidence and three completely
independent fresh-context visual-capable AI reviewers accept every flagship at
the frozen reference-parity thresholds.

## Background

Earlier automatic scores obscured visible quality failures, and continued
review contexts could inherit implementation history. The user explicitly
requires AI-only blind acceptance in isolated contexts. Failed rounds remain
evidence and cannot be manually overridden.

## Requirements

### V6-PORT-02: Portable Completion Evidence

- **Source requests:** USR-V6-03, USR-V6-08
- **Current:** Mandatory PowerPoint/COM verification is blocked and unnecessary.
- **Target:** Portable evidence is sufficient for the release gate.
- **Acceptance:** Every physical page renders with stable hashes.

Every accepted PPTX must have isolated portable PDF/PNG evidence for every
physical page, stable hashes, source protection, and no COM dependency.

### V6-EVID-01: Anonymous Hash-Bound Packets

- **Source requests:** USR-V6-01, USR-V6-08, USR-V6-09
- **Current:** Full-deck thumbnails and visible provenance can bias review.
- **Target:** Anonymous segmented packets preserve physical slide identity.
- **Acceptance:** Packet files, page labels, and hashes validate.

Reviewer evidence contains a clearly labeled calibration reference and
anonymous candidate segments with real physical slide numbers. Generator
identity, model history, and other reviewer results remain hidden.

### V6-DOC-01: Executable Quality-First Workflow

- **Source requests:** USR-V6-01, USR-V6-02, USR-V6-04
- **Current:** Stale v5 workflow text does not describe the quality-first path.
- **Target:** Skill documentation makes the v6 process executable.
- **Acceptance:** Formatter, workflow, and behavior checks pass.

Skill and planning documentation must describe realistic brief discussion,
certified template intelligence, complete deck anatomy, native rendering,
bounded QA, evidence, and failure behavior without stale v5 defaults.

### V6-UAT-01: Three-Reviewer AI Blind Acceptance

- **Source requests:** USR-V6-08, USR-V6-09
- **Current:** Prior trials were rejected and human acceptance was not run.
- **Target:** Three isolated visual AIs decide reference parity.
- **Acceptance:** All frozen score, parity, and consensus gates pass.

Three fresh isolated visual reviewers cover art direction, narrative, and
production. At least two of three must vote reference parity for every deck;
overall mean is at least 4.3, every dimension at least 4.1, and every deck at
least 4.2.

### V6-AUDIT-01: Fresh Independent Completion Audit

- **Source requests:** USR-V6-01, USR-V6-08, USR-V6-09
- **Current:** No v6 request-to-evidence completion audit exists.
- **Target:** Fresh OpenCode independently maps every request and requirement.
- **Acceptance:** Every mapping passes with no serious unresolved finding.

A fresh OpenCode audit maps the original user requests to requirements,
implementation, tests, artifacts, and UAT. Every mapped requirement must pass
with no unresolved Blocker or Important finding.

### V6-REL-01: Fail-Closed Release

- **Source requests:** USR-V6-01, USR-V6-08, USR-V6-09
- **Current:** v6 remains open while any quality or evidence gate is unresolved.
- **Target:** Release occurs only after complete deterministic and AI closure.
- **Acceptance:** Any failure keeps the milestone open; all passes permit GO.

Any missing reviewer, invalid evidence, failed score floor, parity failure,
two-reviewer same-slide same-dimension Blocker/Important consensus, failing
test, or unmapped request keeps the milestone open.

## Boundaries

### In Scope

- anonymous segmented evidence, reviewer provenance, strict aggregation, and
  immutable failed rounds;
- deterministic regression, workflow, private-asset, formatter, and diff
  gates;
- final audit, phase documents, roadmap/state/requirement closure, commits,
  and push after GO.

### Out Of Scope

- human score substitution, manual override, reduced thresholds, missing
  reviewer imputation, continued contexts, or concealed failed rounds;
- COM as a mandatory gate;
- new v6.1 weak-model distillation after v6 acceptance.

## Constraints

- Reviewer contexts are fresh, isolated, and mutually independent.
- All three reviewers must complete the exact anonymous candidate set.
- The reference calibrates craft complexity, not palette or industry motifs.
- Segmented sheets preserve physical slide labels and prevent full-deck
  thumbnail scale from being mistaken for source typography.
- Aggregation is deterministic and fail closed.

## Acceptance Criteria

- [ ] Three unique fresh-context reports cover all anonymous candidates.
- [ ] Every candidate receives at least two reference-parity votes.
- [ ] Overall mean is at least 4.3, every dimension mean at least 4.1, and
      every candidate mean at least 4.2.
- [ ] No same-candidate, same-slide, same-dimension Blocker or Important is
      reported by two reviewers.
- [ ] All engineering, workflow, formatter, private-asset, and diff gates pass.
- [ ] Fresh OpenCode specification, quality, verification, and completion
      audits contain no unresolved Blocker or Important.
- [ ] Requirements, roadmap, state, summaries, validation, UAT, and audit
      records are updated before release.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 1.0
- **Boundary clarity:** 1.0
- **Constraint clarity:** 0.99
- **Acceptance clarity:** 1.0
- **Ambiguity:** 0.008

## Decision Log

| Round | Decision |
|---:|---|
| 1 | Use three fresh independent AI contexts with no human scoring |
| 2 | Keep failed visual rounds immutable and never average them away |
| 3 | Segment long candidates into physical-slide-labeled sheets |
| 4 | Require both numerical floors and zero consensus serious findings |
| 5 | Keep COM optional and portable rendering canonical |
