# Phase 41 Specification: AI-Only Acceptance and Closure

**Status:** Locked
**Depends on:** Phases 39–40
**Requirements:** V6-PORT-02, V6-EVID-01, V6-DOC-01, V6-UAT-01,
V6-AUDIT-01, V6-REL-01

## Goal

Close v6.0 only after deterministic engineering gates and three independent
fresh-context visual-capable AI reviewers accept all flagships.

## Acceptance

- All three reviewers pass image-load preflight and receive anonymous,
  hash-bound evidence without generator traces or other reviewer scores.
- At least two of three return reference parity; overall mean is at least
  `4.3`, every dimension aggregate at least `4.1`, and every flagship at least
  `4.2`.
- No two reviewers agree on a same-slide same-issue Blocker or Important
  finding.
- An unavailable reviewer makes the round `NOT_RUN`; there is no two-reviewer
  fallback or manual override.
- A fresh OpenCode Agnes completion audit maps every user request and v6
  requirement to exact implementation and passing evidence.
